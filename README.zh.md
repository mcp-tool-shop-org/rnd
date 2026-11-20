<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.md">English</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/rnd/readme.png" alt="Research and Development" width="400">
</p>

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/rnd/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/rnd/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://codecov.io/gh/mcp-tool-shop-org/rnd"><img src="https://codecov.io/gh/mcp-tool-shop-org/rnd/branch/main/graph/badge.svg" alt="Coverage"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
  <a href="https://mcp-tool-shop-org.github.io/rnd/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page"></a>
</p>

工作室的研究工作台。来自任何领域的研究成果会以简短的 Markdown 条目形式快速呈现，每个来源都会被标记，并且每个声明都会被标记为已验证或未验证。实验与它们所测试的条目并列。外部目录会被镜像和评估，并且一个注册表会列出工作室可以使用的研究工具。一个命令可以搜索所有内容。

## 它所在的位置：位于 readouts 前面的工作台

两个存储空间保存着工作室的知识，并且它们执行不同的任务。

| | 研究与开发（此仓库） | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| 角色 | 工作台：接收、实验、开放性问题 | 书架：经过验证的知识库 |
| 速度 | 几分钟内完成一个条目，声明从 `unverified` 开始 | 由研究团队构建和验证 |
| 形式 | Markdown 条目，每个条目一个主题 | 每个领域一个 SQLite 知识库 |
| 混乱程度 | 有目的地混乱：有争议的声明、死胡同和临时结果会一直显示 | 完全不混乱：每一行都有来源并经过验证 |

知识的流动方向：

1. **工作台。** 一个研究成果以条目的形式呈现在这里。它的声明从 `[unverified]` 开始，并且只有在附带已验证它的内容的说明时，才会标记为 `[verified]`。
在我们的机器上进行的测量结果会以 `rig` 来源的形式呈现，其配置位于 `experiments/` 中。
2. **内部书架。** 一旦某个主题的关键声明得到证实，它就会被构建到 readouts 的私有工作仓库中的知识库中，或者添加到现有的知识库中。**推广是完成实验的一部分**（主管，2026-10-09）。当实验结果提交到这里时，其 readouts-internal 更新将在同一会话或下一个会话中进行，并附带其图表。没有任何内容会在工作台上停留超过一周的时间。定期的少量更新胜过一次大型更新。实验的 README 文件会记录其推广情况，并在其结果下方添加一行：“已推广：readouts-internal `<kb>` 波次 `<n>`，`<date>`”，或者说明为什么尚未推广。
3. **公共书架。** 当知识库被添加到导出允许列表中时，它就会发布到公共 readouts 仓库中。

`rnd readouts` 从这里搜索每个 readouts 知识库，因此一个席位可以访问这两个存储空间。首先搜索工作台，然后搜索书架，最后研究差距。

这里的研究不仅限于工作室自己的领域。每个条目都会分别记录两件事：知识是什么，以及它对工作室意味着什么（`relevance: act | watch | reference`）。`reference` 是一种很好的结论。

## 使用方法

需要 Python 3.10 或更高版本，并且不需要其他任何东西（仅使用标准库）。可在 Windows、macOS 和 Linux 上运行。从仓库根目录：

```bash
python -m rnd search cuda graphs            # full-text over entries + catalogues (stemmed: pair finds pairs)
python -m rnd search --exact PAIR           # whole words, same case: the product, not the word
python -m rnd probe https://github.com/NVIDIA/NeMo-Relay   # licence, release, telemetry hits, already in rnd?
python -m rnd show 2026-10-07-cuda-graphs   # one entry, with backlinks
python -m rnd list --relevance act          # what needs doing
python -m rnd tools                         # instruments this seat can use
python -m rnd readouts splice glitch --any  # search the readouts knowledge bases too
python -m rnd catalog lanes                 # NVIDIA skills by lane, with studio fit
python -m rnd catalog list --fit adjacent   # skills worth using when the need arises
python -m rnd new "Paper title" --kind paper --field audio --tag pitch
python -m rnd new-question "Why does X happen?" --field audio
python -m rnd sync --check                  # verify numbers bound to experiments/<id>/results.json
python -m rnd check                         # validate every file (exit 1 on errors)
python -m rnd similar 2026-10-07-cuda-graphs --limit 3  # closest claims in other entries (read-only)
python -m rnd digest --since v1.1.24.0.14   # entries, claims and questions changed since a tag or date
python -m rnd sql "SELECT tier, count(*) FROM sources GROUP BY tier"
python -m rnd change "what changed"         # add a changelog fragment under changes/ (nano by default)
python -m rnd bump --note "release note"    # release PR: apply changes/ fragments, bump version + CHANGELOG
```

每个列表命令都支持供代理（agent）使用的 `--json` 参数。`rnd.cmd`（Windows）和 `rnd.sh`（POSIX shell）是简单的包装器，因此该命令可以从任何目录运行。

要从其他项目中使用该工具，请从 PyPI 安装它：

```bash
pip install mcptoolshop-rnd
```

这会安装 `rnd` 命令，而不是库：条目存储在这个仓库中。该命令会按照以下顺序查找库：`--library DIR`，然后 `$RND_ROOT`，然后是当前目录或其上方目录中包含 `entries/` 和 `instruments/` 的最近文件夹。在库外部，它会停止并显示 `NO_LIBRARY`；只有 `rnd readouts` 可以在没有库的情况下工作。

在 Python 中，导入 `mcptoolshop_rnd`：这个名称始终有效。`rnd` 作为兼容性别名保留，但一个不相关的 PyPI 包也称为 `rnd`，如果同时安装了这两个包，它可能会取代该别名。`rnd` 命令和 `python -m mcptoolshop_rnd` 无论如何都会继续工作。

该库每天都会发生变化，因此版本有五个部分，格式为 `MAJOR.MINOR.PATCH.MICRO.NANO`。前三段用于标识 `rnd` 工具的版本；MICRO 表示库的结构性更改，而 NANO 表示普通更新。普通更新会在 `changes/` 下添加一个变更日志片段，通过 `rnd change`；在发布时，`rnd bump` 会使用所有片段，通过最高的片段级别将版本提升一次，并编写一个 CHANGELOG 部分。

退出代码：`0` 正常 · `1` 无效的库文件 · `2` 用法错误或未找到 · `3` 运行时失败（外部工具或意外错误）。错误会打印一个代码、一条消息和一个提示；`--debug` 会添加堆栈跟踪。

## 布局

| 路径 | 内容 | 谁编辑 |
|------|------|-----------|
| `entries/YYYY/*.md` | 研究条目：事实的来源 | 人和代理 |
| `questions/*.md` | 开放的和已解答的研究问题 | 人和代理 |
| `changes/*.md` | 未发布的变更日志片段（`rnd change`） | 人和代理（`rnd bump` 使用） |
| `experiments/<name>/` | 配置、固定的输入、`results.json` 和结果收据 | 人和代理 |
| `experiments/<name>/collect.json` | 从工具仓库中收集的记录，记录在固定的提交点（`rnd collect`） | 人 |
| `instruments/*.md` | 工作室工具和协议，席位可以调用（`kind: instrument`） | 仅供研发席位使用（已审核的差异） |
| `catalogs/<name>/source.json` | 目录的来源 | 人 |
| `catalogs/<name>/catalog.json` | 从 `rnd catalog sync` 固定的快照 | 生成；绝不手动编辑 |
| `catalogs/<name>/review.json` | 工作室适配和每个系列和项目的说明 | 人 |
| `datapacks/<name>/spec.json` | 数据包包含的内容：包含 glob、许可证、生成器、主机 | 人 |
| `datapacks/<name>/datapack.json` | 来自 `rnd datapack build` 的清单：每个文件的 SHA-256、许可证、固定版本 | 生成；绝不手动编辑 |
| `datapacks/<name>/hosted.json` | 上传的位置（仓库修订版） | 上传后 |
| `mcptoolshop_rnd/` | 命令行界面 | 代码 |
| `rnd/` | `mcptoolshop_rnd` 的兼容性别名 | 代码 |
| `rnd.db` | SQLite FTS5 索引，文件更改时自动重建 | 生成；不在 git 中 |
| `rnd.misses.jsonl` | 本地零命中搜索日志，位于 `rnd.db` 旁边（`RND_NO_USAGE=1` 禁用） | 生成；不在 git 中 |

## 条目格式

```markdown
---
id: 2026-10-07-cuda-graphs        # defaults to the file name
title: CUDA Graphs
date: 2026-10-07
kind: concept                     # finding concept release paper tool catalog rig-fact event question decision instrument
relevance: reference              # act | watch | reference
fields: [gpu-computing]           # any research field, open vocabulary
tags: [cuda-graphs, pytorch]
---

## Summary
## Key points
## Studio relevance
## Claims
- [unverified] A checkable statement.
- [verified] [c-a1b2c3d4] A checked statement. (via: what checked it, date)
## Sources
- [primary] https://… — publisher
```

- **来源层级：** `primary`（供应商文档、论文、仓库）、`secondary`（信誉良好的文章）、`aggregator`（摘要网站、AI 搜索输出）、`user`（由人提供：幻灯片、笔记）、`rig`（在我们的机器上测量）。
- **声明置信度：** `unverified`、`verified`、`disputed`、`wrong`、`superseded`。`verified` 或 `wrong` 声明必须通过 `(via: …)` 注明是什么验证了该声明。
- `[[entry-id]]` 链接条目；`rnd show` 列出反向链接。

## 变更日志片段

更新不会直接编辑 `mcptoolshop_rnd/__init__.py` 或 `CHANGELOG.md`，因此，
并行分支在版本线上不会发生冲突：

```bash
python -m rnd change "Add study of XYZ"                # writes changes/YYYY-MM-DD-<hex>-<slug>.md (level: nano)
python -m rnd change "New tool feature" --level minor  # levels: nano | micro | patch | minor | major
python -m rnd bump --dry-run                           # preview version bump from changes/ fragments
python -m rnd bump                                     # release PR: bump once, update CHANGELOG.md, delete fragments
```

如果 `changes/` 下没有文件，则 `rnd bump [nano|micro|…] [--note …]` 将保留其
git-diff 行为。 `__init__.py` 和 `CHANGELOG.md` 均通过临时文件暂存并通过 `os.replace` 原子替换；如果
CHANGELOG 替换失败，则会回滚 `__init__.py`。如果崩溃导致 `__init__.py` 的版本超前于 `CHANGELOG.md`，
以匹配的级别重新运行即可完成版本提升，而其他任何级别都会拒绝执行并返回 `BAD_CHANGELOG`。仍然存在一个差距：在两个文件都交换后，但在删除 `changes/` 下的片段之前发生崩溃，这会导致这些片段保留在原位，并且重新运行会导致第二次更新，因此首先手动删除这些片段。 `rnd check` 会将任何
格式不正确的片段报告为错误。

## 绑定数字

一个实验可以将公共安全摘要数字保存在 `experiments/<id>/results.json` 中，并将条目、摘要或实验注释中的数字直接绑定在文字之后：

```markdown
The judge scored 84.2%<!-- rnd:experiments/e4b/results.json#accuracy:.1% --> on the held-out split.
```

- 原始 Markdown、`grep` 和 SQLite 索引保留纯文本（`84.2%`）；
GitHub 和 Starlight 渲染 `84.2%`，不显示任何可见标记或链接。
- `rnd sync [paths…]` 使用 Python 格式规范重写来自 `results.json` 的绑定文本；如果任何文本不同，则 `rnd sync --check` 会退出 `1`，而不进行写入。
- `rnd check` 将任何不同步的绑定字面量、缺失的文件或缺失的键视为错误，并对 `(via: …)` 指向仓库内实验但仍包含未绑定数字的 `[verified]` 声明发出警告——但会忽略满足以下命名规则的纯整数（不含小数点、百分号、千位分隔符或尾随单位）：在条目自身的标题或标签中与前一个词配对出现的整数，或紧跟在 `RTX`、`GTX` 后的 3–4 位数字，或紧跟在 `CUDA`、`PTX`、`Gemma`、`Llama`、`Qwen`、`Claude`、`GPT`、`Phi` 后的 1–2 位数字。

## 声明 ID 和链接

声明可以携带稳定的确定性 `c-<hex>` ID 和与旧声明的显式关系（`supersedes`、`contradicts`、`supports`），通过 ID 进行关联：

```bash
python -m rnd claims                               # list indexed claims (--state superseded, --json)
python -m rnd claims assign <entry>                # add deterministic c-<hex> ids to one entry's claims
python -m rnd similar <entry> [--limit 5]          # closest claims in other entries (read-only)
python -m rnd reconcile <entry>                    # mark older claims (superseded / disputed / supported-by)
```

`rnd similar <entry>` 会将 `<entry>` 中的每条声明与其他条目进行比对，在 `claims_fts` 上执行只读的 SQLite FTS5 BM25 查询（`--limit` 默认为 5），标记 `superseded` 或 `disputed` 匹配项并注明替换或反驳它们的声明，打印确切的 `(supersedes: id)` / `(contradicts: id)` / `(supports: id)` 子句和 `rnd reconcile <entry>` 命令，并且绝不会写入 `rnd.db` 或任何条目。`rnd reconcile <entry>` 仅在旧声明所在文件的对应行上写入 ID（如果缺失）、更新后的状态和反向关系（`superseded-by`、`contradicted-by`、`supported-by`），而不会触及该行的正文句子或其他任何行（当 `[wrong]` 声明被反驳时，仍保持其 `[wrong]` 状态不变）。
如果某个条目包含多个实际的 `## Claims` 标题，`rnd claims assign` 和 `rnd reconcile` 都会拒绝执行（`MULTIPLE_CLAIMS_HEADINGS`）且不进行任何写入。
`rnd check` 会在目标 ID 损坏、单向链接（提示运行 `rnd reconcile`，或删除该子句并重置 `superseded` 或 `disputed` 状态）或未关闭的代码块时报错，
并在没有 `(superseded-by: …)` 链接的 `[superseded]` 声明时发出警告。
`rnd search` 和 `rnd show` 会标记 `superseded` 和 `disputed` 声明，并命名替换或否定它们的声明。

## 更改内容（摘要）

`rnd digest --since <git ref or YYYY-MM-DD> [--json]` 将早期提交时的库状态（从内存中的 git 对象解析，不触及工作树、git 索引、`rnd.db` 或临时文件）与当前目录树进行比较：

```bash
python -m rnd digest --since v1.1.24.0.14
python -m rnd digest --since 2026-11-19 --json
```

它会报告添加的条目、添加的声明、删除的声明、声明状态更改（`old_state -> new_state` 以及替换或反驳它们的项），以及打开、回答（带有回答声明 ID）和搁置的问题，以及计数。 `YYYY-MM-DD` 日期会解析为当前分支（`HEAD`）的第一个父系行中，提交者日期在该日期或之前，最新的提交。当双方都有 `id` 时，声明通过 `id` 匹配，否则通过 `(entry, exact text)` 匹配；因此，没有 ID 的声明在改写后会显示为删除一条声明并新增一条声明，绝不会显示为状态更改。

## 待解决的问题

待解决的问题以单独的 Markdown 文件形式存储在 `questions/` 下，状态为 `open`、`investigating`、`answered` 或 `parked`：

```bash
python -m rnd new-question "Does X hold on Y?" --field systems
python -m rnd questions --status open --json
```

当问题的 `status` 为 `answered` 时，其前置元数据（frontmatter）中的 `answered_by` 列表必须包含至少一个现有的声明 ID；`rnd check` 会将没有现有声明 ID 的 `answered` 问题视为错误。问题在 `rnd.db` 中被索引，并由 `rnd search` 和 `rnd show` 返回。

## 本地搜索失败日志

当 `rnd search` 没有返回任何匹配项时，它会将一个 JSON 行（`time` 和 `query`）附加到 `rnd.db` 旁边的本地 `.misses.jsonl` 文件中（`rnd.misses.jsonl` 在仓库根目录中，git 忽略；或者 `<stem>.misses.jsonl` 位于 `--db` / `RND_DB` 旁边，因此 `--db foo.db` 会在其旁边写入 `foo.misses.jsonl`，而不是 `foo.db.misses.jsonl`）。
不会记录其他任何内容，也不会通过网络发送任何内容，`RND_NO_USAGE=1` 会关闭日志记录，并且删除该文件会完全删除它。
`rnd stats --usage` 会打印总的未命中计数和最频繁的未命中查询。

## 工具文件和可选附加组件

- **工具文件（`instruments/*.md`）：** 仅由研发人员在经过审查的差异中进行编辑，其描述列出了每个更改的工具文件，而不是由汇总外部内容的步骤或命令进行编辑（`rnd watch`、`rnd probe`、`rnd collect`、`rnd catalog sync`）。
- **核心依赖项和附加组件：** `rnd` 的核心仅保留 Python 标准库。任何可选附加组件都位于可选组中，并且是延迟导入的；如果需要一个缺失的附加组件，则命令将失败，并显示 `MISSING_EXTRA` 和安装提示。

## 数据包

对于克隆来说太大或太多的处理数据，会提供一个 **数据包**：字节存储在 Hugging Face 数据集仓库中（在发布之前是私有的），库仅保留一个小的清单。完整性模型来自 [research-packs](https://github.com/mcp-tool-shop-org/research-packs)：一个清单、每个文件一个 SHA-256、一个单命令验证和一个列表。

```bash
rnd datapack build natural-errors --source experiments/natural-errors  # reads datapacks/natural-errors/spec.json
rnd datapack list
hf download mcp-tool-shop/rnd-natural-errors --repo-type dataset --local-dir ne
rnd datapack verify natural-errors --copy ne/files                      # PASS when every byte matches
```

- **每个文件都需要许可证**，在规范中。模型输出携带其模型的条款（例如，对于 Llama 3.1 输出，“基于 Llama 构建”）。 `rnd datapack build` 会拒绝缺少文件许可证的数据包。
- **每个生成模型都会被固定**（Ollama 摘要、HF 版本或 API 模型 ID），并带有其角色。
- `rnd check` 会验证每个清单，并在手动编辑的清单中失败。
- 上传会携带 `datapack.json`，与文件一起，因此任何人都可以进行验证，而无需使用此仓库：`pip install mcptoolshop-rnd`。

## 收集的实验记录

一个工具仓库会提交其自身的预注册规范和运行记录（interlock 的收据），就像每个仓库提交其 Atlas 地图一样。库仅发布库中数字的精简副本，由 `rnd collect` 从工具仓库中的固定提交中创建：

```bash
rnd collect                 # list the experiments that collect records
rnd collect e4b             # read each source with git show, trim it, write experiments/e4b/results/
rnd collect e4b --check     # recompute every output; exit 1 if any differs from the committed file
```

- **`experiments/<name>/collect.json`** 指的是仓库，以及从中读取数据的克隆仓库（`--clone` 可以覆盖）。它还包括每个源：其路径、提交记录、字节的 SHA-256 值、输出以及实验中的 `extract.py` 中的修剪函数。
- **固定的源永远不会更改。** 如果字节不再与固定的值匹配，则会拒绝该字节。
- **每个记录都包含来源信息：** 仓库、源路径以及修剪后的字节的 SHA-256 值。
- **在写入之前，每个输出都必须是安全的。** 不会保留任何机器路径、主目录或环境变量。实验的模块可以添加更严格的保护措施。一旦发生任何拒绝，将不会写入任何内容。

## 在试用之前测试工具

`rnd probe <url> …` 通过每个源的 API 回答关于工具或模型的第一批问题，而不是从网页摘要中获取：

- **GitHub**（通过 `gh api`，因此它使用您的 GitHub CLI 登录）：许可证、是否已存档、上次推送、最新发布以及代码中是否存在“遥测”字样的搜索。找到匹配项表示可以进一步研究，但绝不是确凿的证据；没有找到匹配项也不是确凿的证据。
- **Hugging Face：** 许可证标签，或者对于“其他”，是卡片中的许可证名称和链接；访问控制；上次更改。
- **PyPI 和 npm：** 许可证、最新版本以及发布时间。
- **rnd 本身：** 对名称进行精确匹配的搜索，以便您知道库是否已经包含它。

无法访问的源将被报告为未知，并附带原因。

## 监控源

`rnd watch` 检查 [docs/watchlist.json](docs/watchlist.json) 中的源，并报告自上次检查以来有哪些新内容：

- NVIDIA 的技术博客；
- CUDA 工具包版本；
- NVIDIA 的新 Hugging Face 模型；
- NVIDIA 技能目录；
- 工作室运行的引擎和工具的发布版本，例如 Ollama、OpenVINO、PyTorch、ComfyUI 和 Claude Code。

```bash
python -m rnd watch                  # what's new; records what it saw
python -m rnd watch --no-save --json # look without recording
python -m rnd watch --only ollama    # one source
```

它所看到的内容将保存在仓库外部的状态文件中（`--state`，否则 `$RND_WATCH_STATE`，否则 `Path.home() / ".rnd" / "watch-state.json"`，`~/.rnd/watch-state.json`），除非传递了 `--no-save`。
源的首次检查是基准：它会记录当前的项目，并且不报告任何新项目。预发布版本绝不会作为源的最新版本报告；如果有更新的预发布版本，会在最新版本旁边一并显示。GitHub 发布说明和提交消息将保存在 JSON 输出中，因此读者不必逐个获取每个页面。无法访问的源将被报告为未知，并且其状态保持不变，因此不会静默地跳过任何内容。

该命令是每周例行程序中确定性的一半（Director，2026-10-13）。侦察员会读取新项目，使用 `rnd probe` 探测任何候选工具，使用 `rnd search --exact` 检查库，并编写一份简短的排序报告：哪些需要归档，哪些需要尝试，哪些需要跳过。通过提交拉取请求来添加源，并说明其重要性。

## 与其他工作室工具的关系

- **readouts** 是此工作台向其输送经验证成果的“书架”（见上文）。
- **research-os** 构建一个受控的、冻结的证据包，用于一个主题。一个决策所依赖的主题可以升级为 research-os 包，并链接到该条目。
- **repo-knowledge** 索引工作室自己的仓库；此库涵盖来自外部的知识。
- 在设计过程中收集的发现也应该包含在其中，以便它们能够超越产生它们的会话。

请参阅 `python -m rnd tools` 以获取完整的工具注册表，并参阅 [docs/standards.md](docs/standards.md) 以了解工作流程如何符合工作室的工作流程标准。

## 安全性和信任

- **写入的数据**（按落盘位置划分）：
  - **在此仓库内**（即库：`--library`，否则为 `$RND_ROOT`，否则为工作目录或其上级目录中包含 `entries/` 和 `instruments/` 的最近文件夹，否则为运行该软件包所在的检出仓库）：`rnd new`（在 `entries/` 或 `instruments/` 下创建一个新文件，绝不覆盖现有文件）、`rnd new-question`（`questions/`）、`rnd new-experiment`、`rnd runs record` 和 `rnd collect <name>`（`experiments/<name>/`）、`rnd claims assign`、`rnd reconcile` 和 `rnd sync`（现有 Markdown 文件中的声明行和绑定数字）、`rnd change`（`changes/`）、`rnd bump`（通过各自旁边的临时文件写入 `mcptoolshop_rnd/__init__.py` 和 `CHANGELOG.md`，并删除其使用过的 `changes/` 片段）、`rnd catalog sync`（`catalogs/<name>/catalog.json`）、`rnd datapack build`（`datapacks/<name>/datapack.json`）以及 `rnd layout`（`docs/layout.json`）。
- **索引：** `rnd.db`，或由 `--db` 或 `$RND_DB` 指定的路径；构建期间其旁边会有一个临时的 `.db.tmp` 文件。`rnd build` 会写入该索引，且所有读取索引的命令（`search`、`show`、`list`、`tools`、`stats`、`catalog`、`claims`、`questions`、`sql`、`runs`、`ledger`、`where`、`probe`）在源文件发生更改时都会先重建索引。未命中搜索日志 `rnd.misses.jsonl` 位于其旁边（见下文）。
- **您的主文件夹：** `rnd watch` 将其“已查看项目”文件写入 `--state`，否则写入 `$RND_WATCH_STATE`，否则写入 `~/.rnd/watch-state.json`（代码中构造为 `Path.home() / ".rnd" / "watch-state.json"`），并在多次运行之间保留。该文件通过其旁边的 `.tmp` 临时文件写入。`--no-save` 会跳过写入操作。
- **此仓库之外的原始数据存储：** `rnd raw ingest`、`rnd raw private` 和 `rnd raw relicense` 会写入公共存储（`--public`，否则为 `$RND_DATA`，否则为 `../rnd-data`）和私有存储（`--private`，否则为 `$RND_DATA_PRIVATE`，否则为库旁边的 `../rnd-data-private`；当在库外部运行 `rnd raw` 时，为公共存储旁边的 `rnd-data-private`）。`rnd raw ingest` 还会将每个超过 256 KB 的文件放入 Blob 存储，位于由 `$RND_DATA_STORE_D` 或公共存储的 `store.local.json` 中 `"d"` 条目所指定文件夹下的 `blobs/` 中（无默认值；若未指定，摄取操作会拒绝执行）。Blob 通过其旁边的 `.tmp` 文件写入并标记为只读。使用 `--link` 时，新创建的 Blob 是指向源文件的硬链接，因此**该源文件也会变为只读**（存储中已存在的 Blob 保持不变，其源文件也保持不变）；不使用 `--link` 时，源文件不会被更改。`rnd raw ingest --update` 在写入新文件之前，会先删除这两个存储中某次运行先前的较小文件。`--dry-run` 不写入任何内容。
- **只读，绝不写入：** `rnd readouts`（SQLite 只读模式）、`rnd collect` 的源克隆仓库（`git show`）、`rnd raw verify`、`rnd datapack verify --copy`、`rnd runs record --from`、`rnd abmine`，以及在内存中运行且不在任何地方写入任何内容的 `rnd similar` 和 `rnd digest`：不创建临时文件，也不更改工作树、Git 索引或 `rnd.db`。
- **其运行的代码：** `rnd collect <name>`（无论是否带有 `--check`）都会从库中加载并运行 `experiments/<name>/extract.py`（或该文件夹的 `collect.json` 所指定的模块）（`mcptoolshop_rnd/collect.py:142-149`）。Python 可能会将该模块的字节码缓存在 `experiments/<name>/__pycache__/` 中。`rnd` 将其自身写入的内容限制在 `experiments/<name>/` 内；但它不限制该模块自身代码的行为，因此请仅在您信任的库上运行它。
- **在 `rnd` 命令之外：** 该软件包还附带了 `mcptoolshop_rnd.localbuilders`，即 local-builders 实验的测试框架。没有任何 `rnd` 命令会运行它。如果直接运行（例如 `python -m mcptoolshop_rnd.localbuilders.runner`），在为其编写的目标租用机器上并以部分 root 权限运行时，它会在调用方传入的路径（工作目录、主目录、历史记录、虚拟环境、收据、日志、报告、机密目录和隔离探测路径）下创建、删除文件并修改文件的所有者和权限；其评分器会在操作系统的临时文件夹中使用一个临时文件夹，并在结束时将其删除。
- **未触及的数据：** 没有任何 `rnd` 命令会在其他任何地方写入、删除或修改文件。它不存储任何凭据，也不读取任何凭据。
- **网络：** 无，但 `rnd catalog sync`、`rnd probe` 和 `rnd watch` 除外；它们在您运行时会读取公开元数据，或通过您自己的 `gh` CLI 登录会话调用 GitHub API。
- **权限：** 普通文件访问权限。无需提升权限即可执行任何 `rnd` 命令，并且没有后台服务。
- **仅限本地的使用日志：** 不会收集任何数据，也不会发送到任何地方。当 `rnd search` 没有返回匹配项时，它会向 `rnd.db` 旁边的 `rnd.misses.jsonl` 追加一行（UTC 时间和查询内容）（在仓库中被 Git 忽略；使用 `--db foo.db` 时，会在其旁边写入 `foo.misses.jsonl` 而不是 `foo.db.misses.jsonl`，`$RND_DB` 同理）。设置 `RND_NO_USAGE=1` 可将其关闭，且随时删除 `.misses.jsonl` 文件即可清空记录。不记录任何其他使用数据。
- **公共仓库卫生检查：** 每次推送（push）之前，都会扫描目录树以检查是否存在主目录路径和操作员身份信息。

如 [SECURITY.md](SECURITY.md) 中所述，报告漏洞。

## 测试

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## 状态和许可

由工作室维护，并每天使用。代码：[MIT](LICENSE)。条目：CC BY 4.0。位于 `catalogs/nvidia-skills/catalog.json` 中的 NVIDIA 技能镜像
以该项目的许可（代码为 Apache-2.0，技能文本为 CC-BY-4.0）的方式，重现了 [NVIDIA/skills](https://github.com/NVIDIA/skills) 中的技能名称和描述。

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
