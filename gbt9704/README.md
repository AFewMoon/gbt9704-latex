Package: gbt9704
Version: 0.1.4
Date: 2026-07-29
License: LPPL-1.3c

========================================
LaTeX Class for GB/T 9704-2012
Chinese Official Document Format
========================================

This package provides a LaTeX document class for typesetting
documents according to the Chinese national standard
GB/T 9704-2012 (Format of official documents of party and
government organs).

REQUIREMENTS
------------
* TeX Live 2020 or later（推荐 XeLaTeX；LuaLaTeX 在部分机器上无法嵌入系统 CJK 字体）
* CTEX package (included in TeX Live) — 基类是 ctexart
* geometry + fancyhdr（included in TeX Live）——版面与页脚由这两个包实现
  （v0.2.0 起不再依赖 memoir：memoir 与 geometry/fancyhdr/titlesec 互斥，
   且 ctex 需要把它当"非标准文档类"打补丁）
* Required LaTeX packages (all in TeX Live):
  - iftex, fontspec, xcolor, graphicx, array, booktabs, longtable,
    caption, subcaption, ulem, alltt, indentfirst, fcolumn
* Emoji：
  - XeLaTeX（默认引擎）：用 TeX Live `noto-emoji` 包自带的 `NotoEmoji-Regular.ttf`，
    输出黑白 emoji，不依赖系统 emoji 字体（不做存在性探测，避免缺失字体触发 METAFONT）。
  - LuaLaTeX（可选，彩色 emoji）：`tlmgr install bxcoloremoji twemojis`，
    emoji 以 PDF 彩色矢量图形输出。
* Fonts:
  - 默认分支：FangSong, SimHei, KaiTi, SimSun（Windows/WPS 自带）
  - `fandol` 选项：只用 TeX Live 自带的 Fandol + Latin Modern，
    供没有中文系统字体的机器（CI、容器）使用
  - FZDaBiaoSong-B06 (FangZheng DaBiaoSong) for red headers.
    If not installed, the class will automatically fall back
    to SimHei with fake bold, with a warning message.
  - Sarasa Mono SC (CJK monospace) + DejaVu Sans Mono (box-drawing)
* Optional: zhlineskip (2026/06/30+) for CJK-aware line spacing
  control. Install via: tlmgr install zhlineskip

OPTIONS
-------
* redline / noredline : Enable/disable red separator line under
  the red header. (Default: noredline)
* titleindent / notitleindent : Enable/disable first-line indentation
  for section titles. (Default: titleindent, complying with standard)
* zhlineskip : Enable zhlineskip package for CJK-aware proportional
  line spacing. Sets bodytextleadingratio=1.75 (28pt/16pt) and
  restores Western math leading. (Default: off)
* emoji / noemoji : Enable/disable emoji support. (Default: emoji)
  - LuaLaTeX: colored PDF vector graphics via bxcoloremoji→twemojis.
  - XeLaTeX: black-and-white via Segoe UI Emoji / NotoEmoji font fallback.

USAGE EXAMPLE
-------------
\documentclass[redline,zhlineskip]{gbt9704}
\title{文件标题}
\begin{document}
\maketitle
\section{一、总体要求}
\subsection{（一）指导思想}
正文内容...
\end{document}

MAIN COMMANDS
-------------
* \gongwentitle{...}     - Main title (No.2 DaBiaoSong, centered)
* \gongwensubtitle{...}  - Subtitle (No.3 FangSong, centered)
* \makeheader{Org}{Num}{Sig} - Red header with issuing organ,
                           document number, and signatory
* \mainreceiver{...}     - Main receiver (left-aligned, no indent)
* \attachmentHZ{...}     - Single attachment (with "附件：" prefix,
                           2-character indent)
* \attachmentNOHZ{...}   - Single attachment (without prefix,
                           5-character indent, aligned with first)
* attachments environment - Multiple attachments with \attachmentitem
* \signature{...}        - Signature (right-aligned, 2-char indent)
* \signdate{...}         - Date (right-aligned, 2-char indent)
* \notes{...}            - Notes in parentheses (no indent)
* \copyto{...}           - CC list (no indent, "抄送：" prefix)
* \issueinfo{Org}{Date}  - Issuing organ and date (left+right)
* \seprule               - Separator line for page footer area
* \emoji{...}            - Insert a colored emoji (LuaLaTeX only). Uses
                           bxcoloremoji → twemojis pipeline: each emoji
                           is a colored PDF vector graphic. Example:
                           \emoji{👍} renders as 👍. No system emoji
                           font required. Use 'noemoji' option to disable.

HEADING FORMATS (GB/T 9704-2012)
---------------------------------
* Heading 1 (一、): SimHei (黑体), No.3, 2-char indent
* Heading 2 (（一）): KaiTi bold (楷体加粗), No.3, 2-char indent
* Heading 3 (1.): FangSong bold (仿宋加粗), No.3, 2-char indent

RECOMMENDED COMPANION PACKAGES
------------------------------
* zhlineskip (2026/06/30+) — CJK-aware proportional line spacing
  with independent bodytext/footnote/math leading control.
  Built-in support via the zhlineskip class option.
  Install via: tlmgr install zhlineskip

KNOWN ISSUES / LIMITATIONS
--------------------------
* The class requires LuaLaTeX (recommended) or XeLaTeX; pdflatex is not
  supported due to font encoding requirements.
* Colored emoji (\emoji{}) requires LuaLaTeX. Uses bxcoloremoji→twemojis
  pipeline (PDF vector graphics), not system emoji fonts. Emoji inside
  verbatim environments will not render — use \emoji{} outside verbatim.

INSTALLATION
------------
Copy gbt9704.cls to:
$TEXMF/tex/latex/gbt9704/
or simply place it in the same folder as your .tex file.

Compile with LuaLaTeX:
lualatex document.tex

CONTRIBUTION & FEEDBACK
-----------------------
Bugs, feature requests, and contributions are welcome.
Please submit via https://codeberg.org/songwupei/latex-gbt9704
or email: songwupei@163.com

CHANGELOG
---------
v0.2.0 (unreleased) - Monospace font fallback and Markdown converter.
- Monospace fonts now degrade gracefully: Sarasa Mono SC →
  SimHei (CJK) and DejaVu Sans Mono → Consolas → lmmono10
  (TeX Live). Previously a missing mono font aborted the compile
  at \documentclass time, even though the class never quotes
  monospaced text.
- zhlineskip is loaded without the `quiet` option: v1.0e (and any
  release that lacks it) treats unknown options as fatal
  PackageError.
- \makeheader's third argument (签发人) is no longer typeset when
  empty, matching its documentation.
- New tool: tools/md2gongwen.py converts a Markdown draft into
  gbt9704-class LaTeX (pure standard library, no pandoc needed).

v0.1.4 (2026-07-29) - Section numbering and ctex heading integration.
- Section numbering: Chinese numerals (一、（一）、1.) per GB/T 9704-2012.
- Switched heading styles from memoir \setsecheadstyle to ctex \ctexset for
  correct font rendering with heading=true.
- Fixed attachment spacing: removed extra \vspace between attachment items.
- Various documentation fixes and cleanup.

v0.1.3 (2026-07-28) - Dual-engine emoji and financial tables.
- Unified cls supports both LuaLaTeX (colored vectors) and XeLaTeX (font fallback).
- Dual-engine emoji: bxcoloremoji→twemojis (LuaLaTeX) or Segoe UI Emoji/NotoEmoji (XeLaTeX).
- Built-in financial table support via fcolumn package (C and N column types).
- Added gongwenbody environment and \setgongwenlinespread command.
- New dependencies: fcolumn, alltt, Sarasa Mono SC, DejaVu Sans Mono.
- Font fallback for FZDaBiaoSong (graceful degradation to SimHei).
- Memoir-native title indent via \setsecindent (cleaner, hyperref-compatible).
- Soul/ulem CJK compatibility fix in \AtBeginDocument.

v0.1.2 (2026-07-28) - Engine upgrade and colored emoji support.
- Switch primary engine from XeLaTeX to LuaLaTeX.
- Add colored emoji support via bxcoloremoji → twemojis pipeline:
  each emoji renders as a colored PDF vector graphic (no system
  emoji fonts required). Uses TeX \number + Lua dec-to-hex
  conversion to bridge Unicode input to twemojis name lookup.
- Add \emoji{<character>} command and noemoji class option.
- Update documentation: two-column code/render layout for all
  emoji examples (verbatim+emoji incompatibility resolved).

v0.1.1 (2026-07-06) - Feature update.
- Add zhlineskip class option for CJK-aware proportional line spacing
  (bodytextleadingratio=1.75, footnoteleadingratio=1.75,
   restoremathleading).
- H2 (subsection): 楷体加粗 (\kaishu\bfseries).
- H3 (subsubsection): 仿宋加粗 (\normalfont\bfseries).
- \signature and \signdate: add 2-character right indent.

v0.1 (2026-06-22) - Initial Beta release.
- Core functionality for GB/T 9704-2012 compliance.
- Font fallback mechanism for FZDaBiaoSong.
- Options: redline, titleindent.
- Commands: title, section/subsection, attachments, signature, etc.
