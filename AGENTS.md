# CODEBUDDY.md This file provides guidance to CodeBuddy when working with code in this repository.

## 项目概览

`gbt9704` 是一个 LaTeX 文档类（LPPL-1.3c），按 **GB/T 9704—2012**《党政机关公文格式》排版红头文件、标题层级、附件、版记与页码。基类是 `ctexart`（`fontset=none`），主引擎 **LuaLaTeX**，XeLaTeX 可用但彩色 Emoji 降级。源码全部集中在 `gbt9704/`，用户可把该目录内容与自己的 `.tex` 放在一起，或安装到 `$TEXMF/tex/latex/gbt9704/`。

## 常用命令

编译说明文档（唯一的编译验证入口；无测试套件）。在 `gbt9704/` 目录下执行；`run.sh` 就是第一条命令。出错时先看 `gbt9704-doc.log` 里的 `Class Warning`（字体回退会以 warning 形式出现而非报错）。

```bash
cd gbt9704
latexmk -lualatex gbt9704-doc.tex
latexmk -c gbt9704-doc.tex          # 清理中间产物，保留 PDF
```

重新生成布局参数（改完 `gbt9704-layout.json` 后必须执行，两条产物都要重新生成）。在仓库根目录执行：

```bash
python3 gbt9704/tools/json2def.py gbt9704/gbt9704-layout.json > gbt9704/gbt9704-layout.def
python3 gbt9704/tools/json2def.py gbt9704/gbt9704-layout.json --lua > gbt9704/gbt9704-layout.lua
```

在 `gbt9704/` 目录下则用 `python tools/json2def.py gbt9704-layout.json > gbt9704-layout.def`（根 `README.md` 里的写法混用了两个工作目录，直接粘贴会找不到路径）。**Windows PowerShell 5.1 的 `>` 会把输出写成 UTF-16LE，生成的 `.def` 无法编译**：请改用 cmd / Git Bash 重定向，或在 PowerShell 7 下用 `| Set-Content -Encoding utf8NoBOM`。

无系统字体环境（CI、容器）验证：给测试文档加 `fandol` 选项编译，字体全部来自 TeX Live，不依赖 fontconfig 与系统 CJK 字体。

```latex
\documentclass[fandol,redline]{gbt9704}
```

## 架构

### 1. 布局参数管线（单一规范源 → 两件生成物 → 宏覆盖）

`gbt9704/gbt9704-layout.json` 是红头字号、紧缩比例、红线、标题/落款/页码等参数的唯一规范源；`tools/json2def.py` 把同一份 JSON 生成两种产物：`.def`（LaTeX `\def`，供 `.cls` 加载）与 `.lua`（Lua table，供外部工具/预览器读取，目前没有任何代码 `require` 它）。两者都标了 `DO NOT EDIT`，改参数只改 JSON 再重新生成。

命名规则由生成器决定：JSON 的 `section.key`（snake_case）→ `\gbt@layout@sectionKey@keyName`（camelCase，因为 LaTeX 宏名不能含下划线）；颜色走单独的 `\gbt@layout@color@chineseRed@model|@value`；JSON 里的嵌套 dict（如 `headings.h1.font_family`）会展开成 `@h1@fontFamily` 后缀。

`.cls` 的加载顺序是这个设计的核心：先给同名宏写一份**内置回退 `\def`**（保证 `.def` 缺失也能编译，只会报一条 warning），再用 `\InputIfFileExists{gbt9704-layout.def}` 覆盖，然后重新 `\makeatletter`，最后才 `\definecolor{chinese-red}`——颜色定义必须晚于 `.def` 加载，否则拿不到 JSON 里的色值。因此**新增一个布局参数要同时改四处**：JSON、`json2def.py` 的 `sections` 列表（仅当新增顶层节）、`.cls` 的回退 `\def`、真正使用该宏的代码。

已知缺口：`json2def.py` 的 `sections` 不含 `headings`，所以 `headings.h1/h2/h3` 只进了 `.lua`，不进 `.def`；正文标题字体实际硬编码在 `.cls` 的 `\ctexset` 里，改 JSON 的 headings 不会生效。

### 2. 引擎、字体与 Emoji 分支

`.cls` 用 `iftex` 检测引擎。三套字体方案互斥，由类选项选择：`fzfonts`（方正商用字体：红头 FZXiaoBiaoSong-B05S → B05 → FZDaBiaoSong-B06 → SimHei 逐级回退）、`fandol`（只用 TeX Live 自带 Fandol + Latin Modern）、默认（系统 FangSong/SimHei/KaiTi/SimSun + Sarasa Mono SC + DejaVu Sans Mono）。三条路径都导出同名切换命令 `\heiti \kaishu \fangsong \songti \dabiaosong`，`.cls` 其余部分只依赖这些名字，新增字体方案照此模式补一套即可。

Emoji 也按引擎分叉：LuaLaTeX 走 `bxcoloremoji` → `twemojis`，用 `\directlua` 把十进制码点转十六进制查表，输出彩色 PDF 矢量图形（多码点序列只取首字符）；XeLaTeX 用 TeX Live `noto-emoji` 的 `NotoEmoji-Regular.ttf` 黑白渲染；`noemoji` 时 `\emoji` 只告警并输出 `[字符]`。verbatim 内不渲染 Emoji，需要保留空白时用 `alltt`。

### 3. 版式与页码（国标数值的直接映射）

版面由 geometry 精确指定：`top=37mm, bottom=35mm, left=28mm, right=26mm`，即 156mm×225mm 版心；`\baselineskip=28pt`（三号 16pt × 1.75，保证每面 22 行）、`\parindent=2em`、`parskip=0`、`secnumdepth=0`（编号交由用户重定义 `\thesection` 等，见 `gbt9704-doc.tex` 的 一、/（一）/1.）。`zhlineskip` 选项是可选增强，用 `bodytextleadingratio=1.75` 让 CJK 行距按字号比例生效，未装该宏包不能启用。

页码要求"单页码居右空一字、双页码居左空一字"，但类文档是单面（oneside）排布，所以 `.cls` 在 `\gbt@pagefoot` 内部用 `\ifodd\value{page}` 自行判断左右，再交给 `fancyhdr` 的 `gongwen` 页脚样式；`\footskip` 取 `space_above(7mm) + 11.2pt`，这 11.2pt 是 geometry+fancyhdr 组合下实测的"基线到一字线上缘"偏移（换版面底层必须重测）。

标题层级不使用 titlesec，而走 ctex 的 `\ctexset`（配合 `heading=true`）；每个层级的 `format` 里都把 `\baselineskip` 重置为正文的 28pt，否则标题会按自身字号算行节距，出现"标题紧贴上一段"。

### 4. 公文组件 API

所有组件都是就地排版命令，内部用 `\begingroup...\endgroup` 或局部 `\setlength` 包裹，不污染文档状态（唯一例外是 `\makeheader` 会 `\thispagestyle{gongwen}`）。按版面顺序分四组：

- **版头与标题**：`\makeheader{机关}{字号}{签发人}`（红头用 `\scalebox` 横向压缩，`redline` 选项控制红线）、`\gongwentitle`（或 `\title` + `\maketitle`，pandoc 兼容）、`\gongwensubtitle`。
- **正文要素**：`\mainreceiver`、`gongwenbody` 环境、`attachments` 环境 + `\attachmentitem[缩进]{}`、`\attachmentHZ`（带"附件："前缀）/`\attachmentNOHZ`。
- **落款与版记**：`\signature`/`\signdate`（右对齐 + 2 字符右缩进）、`\notes`、`\seprule` + `\copyto` + `\issueinfo`。
- **表格**：`fcolumn` 提供 `C`（千分位 + 小数点对齐）与 `N` 列类型，`financialtable` 环境会 `\resetsumline` 并锁定三号仿宋 28pt。

## 约定与坑

- **不要手改 `.def` / `.lua`**，它们每次都会整份重新生成。
- **`.def` 里绝不能出现 `\makeatletter/\makeatother`**：文件在 `.cls` 的 `\makeatletter` 组内加载，`\makeatother` 会把后续类代码中的 `@` 变成非字母，`\@ifundefined` 等立即失效。生成器已修正；`.cls` 在加载后重新断言 `\makeatletter` 以兼容旧副本。
- **不要用 `\IfFontExistsTF` 探测 TeX 树内字体**（Fandol / NotoEmoji / Latin Modern）：检测不到，且缺失时会退化成 METAFONT 查找并以 `I can't find file` 中断编译。TeX 树字体必须写成"文件名 + 扩展名"（如 `FandolSong-Regular.otf`）。`\IfFontExistsTF` 只用于系统字体（FangSong、SimHei、方正系），失败时 `\ClassWarning` 后继续编译。
- **版本号以 `\ProvidesClass` 为准（v0.2.0, 2026-10-14）**，文件头注释仍写 v0.1.14，属未同步。改功能时同步更新 `gbt9704/README.md` 的 CHANGELOG 与 `gbt9704-doc.tex`。
- **文档漂移**：`README.md`、`gbt9704/README.md`、`gbt9704-doc.tex` 仍描述"基于 memoir"，而 `gbt9704.cls` 早已改为 `ctexart` + geometry + fancyhdr（memoir 与三者互斥，且 ctex 需把它当非标准文档类打补丁）。读文档时以此文件的描述为准，改动时顺手修正。
- `issue`、`roadmap` 是本地笔记文件，已被 `.gitignore` 忽略；`gbt9704-doc.pdf` 是入库的编译产物。
