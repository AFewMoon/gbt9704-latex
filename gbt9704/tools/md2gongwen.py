#!/usr/bin/env python3
"""Convert a Markdown draft into a GB/T 9704-2012 公文 LaTeX source.

Supported Markdown subset (exactly what 公文草稿用到的部分):

    # 大标题       -> 由 \\title{...} + \\maketitle 输出
    ## 一级标题    -> \\section{...}（自动编号「一、二、三、」）
    ### 二级标题   -> \\subsection*{...}（不编号，保留原文手写的「（一）」）
    普通段落       -> 正文段落
    **加粗**       -> \\textbf{...}
    [文字](./a.md) -> 纯文字（公文不使用超链接，URL 一律丢弃）

文末最后两个「整段加粗、无其他文字」的段落会被消费为公文落款：倒数第二个
变为 \\signature{...}，最后一个变为 \\signdate{...}。可用 --signature /
--date 显式指定以覆盖自动识别。

不支持列表、表格、图片、引用块、代码块、HTML、YAML front matter：遇到即以
错误（带行号）中止，而不是静默丢弃内容。

Usage:
    python3 tools/md2gongwen.py input.md -o output.tex \\
        --title "关于……的决议" --org "xx委员会" --number "x发〔2026〕1 号" \\
        --signature "xx委员会" --date "2026 年 7 月 31 日"

产物为 UTF-8 无 BOM 的 LaTeX 源文件，用 LuaLaTeX 编译（类安装与字体要求
见本仓库 README.md / AGENTS.md）。
"""

import argparse
import re
import sys
from pathlib import Path

#: LaTeX 特殊字符 → 转义写法
ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}

#: 行内结构。嵌套内容交给 inline() 递归处理。
TOKEN = re.compile(
    r"\[(?P<ltext>[^\[\]]*)\]\((?P<lurl>[^)\s]*)\)"
    r"|`(?P<ctext>[^`]*)`"
    r"|\*\*(?P<stext>[^*]+)\*\*"
    r"|\*(?P<etext>[^*]+)\*"
)

HEADING_H1 = re.compile(r"^#\s+(?P<text>.+?)\s*$")
HEADING_H2 = re.compile(r"^##\s+(?P<text>.+?)\s*$")
HEADING_H3 = re.compile(r"^###\s+(?P<text>.+?)\s*$")
HEADING_H4 = re.compile(r"^#{4,}\s+(?P<text>.+?)\s*$")

BOLD_ONLY = re.compile(r"^\*\*(?P<text>[^*]+)\*\*$")

#: 不支持的结构（命中即报错，不静默丢内容）
UNSUPPORTED = [
    (re.compile(r"^\s*(?:[-*+]|\d+\.)\s+\S"), "列表（公文正文请写成段落文字）"),
    (re.compile(r"^\|"), "表格（请改用 financialtable 环境手工排版）"),
    (re.compile(r"^>"), "引用块"),
    (re.compile(r"^```|^~~~"), "代码块"),
    (re.compile(r"!\["), "图片"),
    (re.compile(r"<[a-zA-Z/]"), "HTML 标签"),
    (re.compile(r"^-{3,}$|^={3,}$"), "分隔线"),
]


class UnsupportedError(Exception):
    """Raised when the draft uses Markdown outside the supported subset."""


def escape_plain(text: str) -> str:
    """Escape LaTeX special characters in a plain-text segment."""
    return "".join(ESCAPES.get(ch, ch) for ch in text)


def inline(text: str) -> str:
    """Convert Markdown inline markup to LaTeX.

    链接降级为锚文本（URL 丢弃），`code` → \\texttt，**bold** → \\textbf，
    *em* → \\emph，其余文本原样转义。
    """
    out = []
    pos = 0
    for match in TOKEN.finditer(text):
        out.append(escape_plain(text[pos:match.start()]))
        if match.group("ltext") is not None:
            out.append(inline(match.group("ltext")))
        elif match.group("ctext") is not None:
            out.append(r"\texttt{%s}" % escape_plain(match.group("ctext")))
        elif match.group("stext") is not None:
            out.append(r"\textbf{%s}" % inline(match.group("stext")))
        else:
            out.append(r"\emph{%s}" % inline(match.group("etext")))
        pos = match.end()
    out.append(escape_plain(text[pos:]))
    # 链接被降级为锚文本后，中文两侧可能留出连续空格，收敛成一个
    return re.sub(r" {2,}", " ", "".join(out))


def _glue(prev: str, line: str) -> str:
    """Join a soft-wrapped continuation line onto the previous text."""
    if not prev:
        return line
    tail = prev[-1]
    head = line.lstrip()[:1]
    # 西文两侧都是 ASCII 时补空格，避免 "1985 年" 被粘连或 "a b" 被合并
    if tail.isascii() and head.isascii():
        return " " + line.lstrip()
    return line.lstrip()


def split_blocks(text: str):
    """Split into blocks of (kind, body, lineno).

    kind is one of "h1", "h2", "h3", "paragraph". Blank lines separate
    blocks; headings always start a new block.
    """
    blocks = []
    current = []  # [(lineno, line), ...]

    def flush():
        if not current:
            return
        joined = ""
        for idx, (_, line) in enumerate(current):
            joined = line if idx == 0 else _glue(joined, line)
        body = joined.strip()
        if body:
            blocks.append((_classify(body, current[0][0]), body, current[0][0]))
        current.clear()

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.replace("　", " ").rstrip()
        if not line.strip():
            flush()
            continue
        if current and not _is_heading(line):
            current.append((lineno, line))  # 软换行并段
        else:
            flush()
            current.append((lineno, line))
    flush()
    return blocks


def _is_heading(line: str) -> bool:
    return bool(HEADING_H1.match(line) or HEADING_H2.match(line)
               or HEADING_H3.match(line) or HEADING_H4.match(line))


def _classify(body: str, lineno: int) -> str:
    if HEADING_H1.match(body):
        return "h1"
    if HEADING_H2.match(body):
        return "h2"
    if HEADING_H3.match(body):
        return "h3"
    if HEADING_H4.match(body):
        raise UnsupportedError("第 %d 行：四级及更深标题不在公文层级内" % lineno)
    for pattern, what in UNSUPPORTED:
        if pattern.search(body):
            raise UnsupportedError("第 %d 行：不支持%s" % (lineno, what))
    return "paragraph"


def bold_text(body: str) -> str:
    """Return the inner text of a bold-only paragraph, else None."""
    match = BOLD_ONLY.match(body.strip())
    return match.group("text") if match else None


def build(source: Path, args) -> str:
    text = source.read_text(encoding="utf-8")

    title_from_h1 = None
    blocks = []
    for kind, body, lineno in split_blocks(text):
        if kind == "h1":
            if title_from_h1 is not None:
                raise UnsupportedError("第 %d 行：出现多个一级标题" % lineno)
            title_from_h1 = HEADING_H1.match(body).group("text")
        else:
            blocks.append((kind, body, lineno))

    title = args.title or title_from_h1 or source.stem

    # 文末「整段加粗」段落段对 → 落款 / 成文日期（被消费，正文中不再重复输出）
    bold_indices = [i for i, (k, b, _) in enumerate(blocks)
                    if k == "paragraph" and bold_text(b) is not None]
    date_index = bold_indices[-1] if bold_indices else None
    sig_index = bold_indices[-2] if len(bold_indices) > 1 else None
    date = args.date or (bold_text(blocks[date_index][1]) if date_index is not None else None)
    signature = args.signature or (bold_text(blocks[sig_index][1]) if sig_index is not None else None)
    skip_indices = {i for i in (sig_index, date_index) if i is not None}

    out = [
        "% !TeX program = lualatex",
        "% 本文件由 tools/md2gongwen.py 生成，请勿手工编辑正文：",
        "% 请修改 Markdown 源文件后重新生成。",
        "\\documentclass[%s]{gbt9704}" % (args.options or "redline,titleindent,zhlineskip"),
        "",
        "% 一级标题中文编号「一、」；二级标题不编号（原文已手写「（一）」）",
        r"\setcounter{secnumdepth}{1}",
        r"\renewcommand{\thesection}{\chinese{section}、}",
        "",
        r"\begin{document}",
        "",
    ]

    if not args.no_header:
        if not args.org:
            raise SystemExit("缺发文机关：用 --org 指定红头机关，或用 --no-header 跳过红头")
        out += [
            r"\makeheader{%s}{%s}{%s}" % (
                inline(args.org), inline(args.number or ""), inline(args.signatory or "")),
            "",
        ]

    out += [r"\title{%s}" % inline(title), r"\maketitle", ""]

    for index, (kind, body, _lineno) in enumerate(blocks):
        if index in skip_indices:
            continue
        if kind == "h2":
            out.append(r"\section{%s}" % inline(HEADING_H2.match(body).group("text")))
        elif kind == "h3":
            out.append(r"\subsection*{%s}" % inline(HEADING_H3.match(body).group("text")))
        else:
            out.append(inline(body))
        out.append("")

    if signature or date:
        out.append("")
        if signature:
            out.append(r"\signature{%s}" % inline(signature))
        if date:
            out.append(r"\signdate{%s}" % inline(date))

    out += ["", r"\end{document}", ""]
    return "\n".join(out)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="把 Markdown 公文草稿转换为 gbt9704 文档类可编译的 LaTeX 源文件"
    )
    parser.add_argument("input", help="Markdown 源文件（UTF-8）")
    parser.add_argument("-o", "--output", help="输出的 .tex 路径，默认为与输入同名")
    parser.add_argument("--options", help="\\documentclass 选项，默认 redline,titleindent,zhlineskip")
    parser.add_argument("--title", help="公文标题（大标题）；缺省取 Markdown 一级标题或文件名")
    parser.add_argument("--org", help="发文机关，红头 \\makeheader 第一参数")
    parser.add_argument("--number", help="发文字号，\\makeheader 第二参数，如「x发〔2026〕1 号」")
    parser.add_argument("--signatory", help="签发人，\\makeheader 第三参数，通常留空")
    parser.add_argument("--signature", help="落款机关，缺省取文末倒数第二段整段加粗")
    parser.add_argument("--date", help="成文日期，缺省取文末最后一段整段加粗")
    parser.add_argument("--no-header", action="store_true", help="不输出红头版头")
    args = parser.parse_args(argv)

    source = Path(args.input)
    if not source.is_file():
        raise SystemExit("找不到输入文件：%s" % source)

    try:
        tex = build(source, args)
    except UnsupportedError as exc:
        raise SystemExit("转换中止：%s" % exc)

    target = Path(args.output) if args.output else source.with_suffix(".tex")
    target.write_text(tex, encoding="utf-8")  # UTF-8 无 BOM
    print("已生成 %s" % target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
