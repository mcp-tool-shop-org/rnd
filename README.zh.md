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

工作室的研究工作台。来自任何领域的研究成果会以简短的 Markdown 条目的形式快速呈现，每个来源都会被标记，并且每个声明都会被标记为已验证或未验证。实验与它们所测试的条目并列。外部目录会被镜像和评估，并且一个注册表会列出工作室可以使用的研究工具。一个命令可以搜索所有内容。

## 它所在的位置：位于 readouts 前面的工作台

两个存储空间保存着工作室的知识，并且它们执行不同的任务。

| | 研究与开发（此仓库） | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| 角色 | 工作台：接收、实验、开放性问题 | 书架：经过验证的知识库 |
| 速度 | 几分钟内完成一个条目，声明从 `unverified` 开始 | 由研究团队构建和验证 |
| 形式 | Markdown 条目，每个条目一个主题 | 每个领域一个 SQLite 知识库 |
| 混乱程度 | 有目的地混乱：有争议的声明、死胡同和临时结果会一直显示 | 完全不混乱：每一行都有来源并经过验证 |

知识单向流动：

1. **工作台。** 一个研究成果以条目的形式呈现在这里。它的声明从 `[unverified]` 开始，并且只有在附带了验证它的内容的说明时，才会标记为 `[verified]`。
在我们的机器上进行的测量结果会以 `rig` 来源的形式呈现，其配置位于 `experiments/` 中。
2. **内部书架。** 一旦某个主题的关键声明得到证实，它就会被构建到 readouts 的私有工作仓库中的知识库中，或者添加到其中。**推广是完成实验的一部分**（主管，2026-10-09）。当一个实验的结果被提交到这里时，它的 readouts-internal 更新会在同一会话或下一个会话中进行，并附带其图表。没有任何内容会在工作台上停留超过一周的时间。定期的少量更新胜过一次大型更新。一个实验的 README 会记录其推广情况，并在其结果下方以如下形式呈现：“已推广：readouts-internal `<kb>` 波次 `<n>`，`<date>`”，或者说明为什么尚未推广。
3. **公共书架。** 当一个知识库被添加到导出允许列表中时，它就会被发布到公共 readouts 仓库中。

`rnd readouts` 从这里搜索每个 readouts 知识库，因此一个席位可以访问这两个存储空间。首先搜索工作台，然后搜索书架，最后研究差距。

这里的研究不仅限于工作室自己的领域。每个条目都会分别记录两件事：知识是什么，以及它对工作室意味着什么（`relevance: act | watch | reference`）。`reference` 是一个好的结论。

## 使用方法

需要 Python 3.10 或更高版本，并且不需要其他任何东西（仅使用标准库）。可以在 Windows、macOS 和 Linux 上运行。从仓库的根目录开始：

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
python -m rnd sql "SELECT tier, count(*) FROM sources GROUP BY tier"
python -m rnd change "what changed"         # add a changelog fragment under changes/ (nano by default)
python -m rnd bump --note "release note"    # release PR: apply changes/ fragments, bump version + CHANGELOG
```

每个列表命令都接受供代理使用的 `--json` 参数。`rnd.cmd`（Windows）和 `rnd.sh`（POSIX shell）是简单的包装器，因此该命令可以从任何目录运行。

要从其他项目中使用该工具，请从 PyPI 安装它：

```bash
pip install mcptoolshop-rnd
```

这会安装 `rnd` 命令，而不是库：条目都存储在这个仓库中。该命令会按照以下顺序查找库：`--library DIR`，然后 `$RND_ROOT`，然后是当前目录或其上方目录中包含 `entries/` 和 `instruments/` 的最近文件夹。在库外部，它会停止并显示 `NO_LIBRARY`；只有 `rnd readouts` 可以在没有库的情况下工作。

在 Python 中，导入 `mcptoolshop_rnd`：这个名称始终有效。`rnd` 会作为兼容性别名保留，但一个不相关的 PyPI 包也称为 `rnd`，如果同时安装了这两个包，它可能会取代该别名。`rnd` 命令和 `python -m mcptoolshop_rnd` 无论如何都会继续工作。

该库每天都会发生变化，因此版本有五个部分，格式为 `MAJOR.MINOR.PATCH.MICRO.NANO`。前三个部分用于标识 `rnd` 工具的版本；MICRO 表示库的结构性更改，而 NANO 表示普通更新。普通更新会在 `changes/` 下添加一个变更日志片段，通过 `rnd change`；在发布时，`rnd bump` 会使用所有片段，通过最高的片段级别将版本提升一次，并编写一个 CHANGELOG 部分。

退出代码：`0` 正常 · `1` 无效的库文件 · `2` 用法错误或未找到 · `3` 运行时失败（外部工具或意外错误）。错误会打印一个代码、一条消息和一个提示；`--debug` 会添加堆栈跟踪。

## 布局

| 路径 | 内容 | 谁编辑 |
|------|------|-----------|
| `entries/YYYY/*.md` | 研究条目：事实的来源 | 人和代理 |
| `questions/*.md` | 开放的和已解决的研究问题 | 人和代理 |
| `changes/*.md` | 未发布的变更日志片段（`rnd change`） | 人和代理（`rnd bump` 使用） |
| `experiments/<name>/` | 配置、固定的输入、`results.json` 和结果收据 | 人和代理 |
| `experiments/<name>/collect.json` | 从工具仓库中收集的记录，记录在固定的提交点（`rnd collect`） | 人 |
| `instruments/*.md` | 工作室工具和协议，席位可以调用（`kind: instrument`） | 仅限研发席位编辑（经过审核的差异） |
| `catalogs/<name>/source.json` | 目录的来源 | 人 |
| `catalogs/<name>/catalog.json` | 从 `rnd catalog sync` 固定的快照 | 生成；绝不手动编辑 |
| `catalogs/<name>/review.json` | 工作室适配和每个系列和项目的说明 | 人 |
| `datapacks/<name>/spec.json` | 数据包包含的内容：包含 glob、许可证、生成器、主机 | 人 |
| `datapacks/<name>/datapack.json` | 来自 `rnd datapack build` 的清单：每个文件的 SHA-256、许可证、固定版本 | 生成；绝不手动编辑 |
| `datapacks/<name>/hosted.json` | 上传的位置（仓库版本） | 上传后 |
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

- **来源层级：** `primary`（供应商文档、论文、仓库）、`secondary`（信誉良好的文章）、`aggregator`（摘要网站、AI 搜索结果）、`user`（由人提供：幻灯片、笔记）、`rig`（在我们的机器上测量）。
- **声明置信度：** `unverified`、`verified`、`disputed`、`wrong`、`superseded`。一个 `verified` 或 `wrong` 声明必须说明什么验证了它，使用 `(via: …)`。
- `[[entry-id]]` 链接条目；`rnd show` 列出反向链接。

## 变更日志片段

更新不会直接编辑 `mcptoolshop_rnd/__init__.py` 或 `CHANGELOG.md`，因此，
并行分支在版本线上永远不会发生冲突：

```bash
python -m rnd change "Add study of XYZ"                # writes changes/YYYY-MM-DD-<hex>-<slug>.md (level: nano)
python -m rnd change "New tool feature" --level minor  # levels: nano | micro | patch | minor | major
python -m rnd bump --dry-run                           # preview version bump from changes/ fragments
python -m rnd bump                                     # release PR: bump once, update CHANGELOG.md, delete fragments
```

如果 `changes/` 下没有任何文件，则 `rnd bump [nano|micro|…] [--note …]` 将保留其
git-diff 行为。`rnd check` 会将任何格式不正确的片段报告为错误。

## 绑定数字

实验可以将可公开的安全摘要数字保存在 `experiments/<id>/results.json` 中，并在条目、简报或实验笔记中紧跟在数字字面量之后直接绑定：

```markdown
The judge scored 84.2%<!-- rnd:experiments/e4b/results.json#accuracy:.1% --> on the held-out split.
```

- 原始 Markdown、`grep` 和 SQLite 索引保留纯文本（`84.2%`）；
GitHub 和 Starlight 会渲染 `84.2%`，没有任何可见标记或链接。
- `rnd sync [paths…]` 会使用 Python 格式规范根据 `results.json` 重写绑定的字面量；如果任何字面量不一致，则 `rnd sync --check` 会以退出代码 `1` 退出，而不进行写入。
- `rnd check` 将任何不同步的绑定文字、缺失的文件或缺失的键视为错误，并在 `[verified]` 声明上发出警告，该声明的 `(via: …)` 名称是指一个仓库
实验，但仍然包含未绑定的数字。

## 声明 ID 和链接

声明可以携带稳定的确定性 `c-<hex>` ID 和明确的关系
（`supersedes`、`contradicts`、`supports`）到较早的声明，通过 ID 进行关联：

```bash
python -m rnd claims                               # list indexed claims (--state superseded, --json)
python -m rnd claims assign <entry>                # add deterministic c-<hex> ids to one entry's claims
python -m rnd reconcile <entry>                    # mark older claims (superseded / disputed / supported-by)
```

`rnd reconcile <entry>` 仅写入 ID（如果缺失）、更新后的状态和
反向关系（`superseded-by`、`contradicted-by`、`supported-by`）到
较早声明的行中，位于它自己的文件中，而不会触及其句子或任何其他
行。如果目标 ID 损坏或链接是单向的，则 `rnd check` 会报错，并提示运行 `rnd reconcile`。`rnd search` 和 `rnd show` 会标记 `superseded` 和 `disputed` 声明，并指出替换它们或与之矛盾的声明。

## 待解决的问题

待解决的问题以单独的 Markdown 文件形式存储在 `questions/` 下，状态为
`open`、`investigating`、`answered` 或 `parked`：

```bash
python -m rnd new-question "Does X hold on Y?" --field systems
python -m rnd questions --status open --json
```

当问题的 `status` 为 `answered` 时，其 frontmatter `answered_by` 列表
必须命名至少一个现有的声明 ID；`rnd check` 将没有现有声明 ID 的 `answered`
问题视为错误。问题在
`rnd.db` 中进行索引，并由 `rnd search` 和 `rnd show` 返回。

## 本地搜索失败日志

当 `rnd search` 没有返回任何匹配项时，它会将一行 JSON 数据（`time` 和
`query`）附加到本地 `.misses.jsonl` 文件中，该文件位于 `rnd.db` 旁边（`rnd.misses.jsonl` 在
仓库根目录中，git 忽略；或者 `<db>.misses.jsonl` 位于 `--db` / `RND_DB` 旁边）。
不会记录任何其他内容，也不会通过网络发送任何内容，`RND_NO_USAGE=1`
会关闭日志记录，并且删除该文件会完全删除它。
`rnd stats --usage` 会打印总的失败计数和最频繁的失败查询。

## 工具文件和可选附加组件

- **工具文件（`instruments/*.md`）：** 仅由研发席位在经过审核的差异中进行编辑（该差异的描述须列出每个更改的工具文件），绝不由任何汇总外部内容的步骤或命令进行编辑（`rnd watch`、`rnd probe`、`rnd collect`、`rnd catalog sync`）。
- **核心依赖项和附加组件：** `rnd` 的核心仅保留 Python 标准库。任何可选附加组件都位于可选组中，并且是延迟导入的；如果需要一个缺失的附加组件，则命令将使用 `MISSING_EXTRA` 失败，并提供安装提示。

## 数据包

对于克隆来说太大或太多的已处理数据，会提供为 **数据包**：字节存储在 Hugging Face 数据集仓库（在发布之前是私有的），库仅保留一个小的清单。完整性模型来自
[research-packs](https://github.com/mcp-tool-shop-org/research-packs)：一个清单、每个文件一个 SHA-256、一个单命令验证和一个列表。

```bash
rnd datapack build natural-errors --source experiments/natural-errors  # reads datapacks/natural-errors/spec.json
rnd datapack list
hf download mcp-tool-shop/rnd-natural-errors --repo-type dataset --local-dir ne
rnd datapack verify natural-errors --copy ne/files                      # PASS when every byte matches
```

- **每个文件都需要一个许可证**，如规范中所述。模型输出携带其模型的条款（例如，对于 Llama 3.1 输出，为“基于 Llama 构建”）。`rnd datapack build` 会拒绝一个数据包，该数据包会使某个文件未被覆盖。
- **每个生成模型都会被固定**（Ollama 摘要、HF 版本或 API 模型 ID），并带有其角色。
- **`rnd check` 验证每个清单**，如果手动编辑了清单，则会报错。
- 上传会携带 `datapack.json`，与文件一起，因此任何人都可以进行验证，而无需使用此仓库：
`pip install mcptoolshop-rnd`。

## 收集的实验记录

一个工具仓库会提交其自身的预注册规范和运行记录（interlock 的收据），就像每个仓库提交其 Atlas 地图一样。库仅发布数字的精简副本，该副本由 `rnd collect` 从工具仓库的固定提交中生成：

```bash
rnd collect                 # list the experiments that collect records
rnd collect e4b             # read each source with git show, trim it, write experiments/e4b/results/
rnd collect e4b --check     # recompute every output; exit 1 if any differs from the committed file
```

- **`experiments/<name>/collect.json`** 命名仓库、它读取的同级克隆（`--clone` 会覆盖），以及每个来源：其路径、提交、其字节的 SHA-256、
输出以及实验的 `extract.py` 中的修剪函数。
- **固定的来源永远不会更改。** 如果字节不再与固定值匹配，则会被拒绝。
- **每个记录都包含来源：** 仓库、来源路径和修剪后的字节的 SHA-256。
- **在写入之前，每个输出都是公共安全的。** 没有机器路径、主目录或环境字段会保留，并且实验的模块可以添加更严格的保护。如果发生任何拒绝，则不会写入任何内容。

## 在试验之前测试工具

`rnd probe <url> …` 直接通过每个来源自身的 API（而不是网页摘要）回答有关工具或模型的第一批问题：

- **GitHub**（通过 `gh api`，因此它使用您的 GitHub CLI 登录）：许可证、是否已存档、
上次推送、最新版本以及代码中是否存在“遥测”的搜索。找到匹配项是一个需要阅读的线索，而不是证明；
没有找到匹配项也不是证明。
- **Hugging Face：** 许可证标签，或者对于“其他”，是卡片的许可证名称和链接；门禁；上次更改。
- **PyPI 和 npm：** 许可证、最新版本以及发布时间。
- **rnd 本身：** 对名称进行精确的单词搜索，以便您知道库是否已经包含它。

如果无法访问某个来源，则会将其报告为未知，并提供原因。

## 监视来源

`rnd watch` 会检查 [docs/watchlist.json](docs/watchlist.json) 中的来源，并报告自上次检查以来有哪些内容是新的：

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

它所看到的内容会保存在仓库外部的状态文件中（`$RND_WATCH_STATE`，否则是`~/.rnd/watch-state.json`）。
一个源的首次检查是一个基准：它会记录当前的项目，并报告没有新的项目。预发布版本绝不会被报告为某个源的最新版本；如果有更新的预发布版本，则会显示在最新版本旁边。GitHub发布说明和提交消息会保存在 JSON 输出中，因此读者不必逐个获取每个页面。如果无法访问某个源，则会将其报告为“未知”，并且其状态保持不变，以防止任何内容被静默跳过。

该命令是每周例行程序中确定性的一半（Director，2026-10-13）。一个侦察员会读取新的项目，使用`rnd probe`探测任何候选工具，使用`rnd search --exact`检查库，并编写一份简短的排序报告：哪些需要归档，哪些需要尝试，哪些需要跳过。通过拉取请求（Pull Request）添加一个源，并说明其重要性。

## 与其他工作室工具的关系

- **readouts** 是由这个工作台输送内容的、经过验证的书架（参见上文）。
- **research-os** 为某个主题构建一个受控的、固定的证据包。一个决策所依赖的主题可以升级为 research-os 包，并由该条目链接过去。
- **repo-knowledge** 索引工作室自己的仓库；这个库涵盖了来自外部的知识。
- 在设计过程中收集的发现也应该放在这里，这样它们就可以超越产生它们的会话。

请参阅`python -m rnd tools`以获取完整的工具注册表，并参阅[docs/standards.md](docs/standards.md)以了解工作流程如何符合工作室的工作流程标准。

## 安全与信任

- **涉及的数据：** 此仓库内的文件（`entries/`、`questions/`、`changes/`、`instruments/`、`catalogs/`、`experiments/`）、索引`rnd.db`及其关联的本地缺失日志`rnd.misses.jsonl`。`rnd readouts`以只读方式打开readouts知识库。`rnd sql`在只读连接上运行。
- **未涉及的数据：** 仓库和readouts检出之外的任何内容。它不存储任何凭据，也不读取任何凭据。
- **网络：** 除了`rnd catalog sync`、`rnd probe`和`rnd watch`之外，没有网络连接，它们读取公共元数据或通过您自己的`gh` CLI 登录调用GitHub API（在您运行它们时）。
- **权限：** 普通的文件访问权限。没有更高的权限，也没有后台服务。
- **仅本地的使用日志：** 不会收集或发送任何内容。当 `rnd search` 没有返回任何匹配项时，它会将一行（UTC 时间和查询）附加到 `rnd.db` 旁边的 `rnd.misses.jsonl` 中（在仓库中被 git 忽略；若指定了 `--db` / `$RND_DB`，则为位于其旁边的 `<db>.misses.jsonl`）。设置`RND_NO_USAGE=1`以将其关闭，并且可以随时删除`.misses.jsonl`以清除它。不会记录任何其他使用数据。
- **公共仓库的卫生：** 在每次推送之前，都会扫描树，以查找主目录路径和操作员身份。

如[SECURITY.md](SECURITY.md)中所述，请报告漏洞。

## 测试

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## 状态和许可证

由工作室维护，并每天使用。代码：[MIT](LICENSE)。条目：CC BY 4.0。`catalogs/nvidia-skills/catalog.json`中的 NVIDIA 技能镜像会重现来自[NVIDIA/skills](https://github.com/NVIDIA/skills)的技能名称和描述，并遵循该项目的许可证（代码为 Apache-2.0，技能文本为CC-BY-4.0）。

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
