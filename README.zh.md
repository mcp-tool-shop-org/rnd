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

## 它所处的位置：位于 readouts 前方的实验台

两个存储空间保存着工作室的知识，并且它们执行不同的任务。

| | 研究与开发（此仓库） | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| 角色 | 工作台：接收、实验、开放性问题 | 书架：经过验证的知识库 |
| 速度 | 一个条目几分钟完成，声明从 `unverified` 开始 | 由研究团队构建和验证 |
| 形式 | Markdown 条目，每个条目一个主题 | 每个领域一个 SQLite 知识库 |
| 混乱程度 | 有目的地混乱：有争议的声明、死胡同和临时结果会一直显示 | 完全不混乱：每一行都有来源并经过验证 |

知识单向流动：

1. **基准测试。** 某个结果会以条目的形式出现在这里。它的声明从 `[unverified]` 开始，并且仅通过一个注释来标记 `[verified]`，说明是谁对其进行了验证。
在我们的机器上进行的测量结果会以 `rig` 来源的形式记录，其测试框架位于 `experiments/` 下。
2. **内部存储区。** 一旦某个主题的关键声明得到证实，它就会被构建到 readouts 的私有工作仓库中的知识库中，或者添加到其中。
**推广是完成实验的一部分**（主管，2026-10-09）。当某个实验的结果在此处提交时，其 readouts-internal 更新将在同一会话或下一个会话中进行，并附带其图表。没有任何内容会在基准测试区停留超过一周。定期的少量更新胜过一次大型更新。某个实验的 README 文件会将其推广记录在其结果下方的行中：
“已推广：readouts-internal `<kb>` 波次 `<n>`，`<date>`”，或者说明为什么尚未推广。
3. **公共存储区。** 当知识库被添加到导出允许列表中时，它将被发布到公共 readouts 仓库。

`rnd readouts` 会从这里搜索每个 readouts 知识库，因此一个位置可以访问两个存储区。首先搜索实验台，然后搜索存储区，最后研究差距。

这里的研究不仅限于工作室自己的领域。每个条目都会分别记录两件事：知识是什么，以及它对工作室意味着什么（`relevance: act | watch | reference`）。`reference` 是一个明确的结论。

## 使用方法

需要 Python 3.10 或更高版本，并且不需要其他任何东西（仅使用标准库）。可以在 Windows、macOS 和 Linux 上运行。从仓库根目录：

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
python -m rnd check                         # validate every file (exit 1 on errors)
python -m rnd sql "SELECT tier, count(*) FROM sources GROUP BY tier"
python -m rnd bump --note "what changed"  # micro version bump + CHANGELOG section
```

每个列表命令都接受 `--json` 作为参数。`rnd.cmd`（Windows）和 `rnd.sh`（POSIX shell）是简单的包装器，因此该命令可以从任何目录运行。

要从其他项目中使用该工具，请从 PyPI 安装它：

```bash
pip install mcptoolshop-rnd
```

这会安装 `rnd` 命令，而不是库：条目都存储在这个仓库中。该命令会按照以下顺序查找库：`--library DIR`，然后 `$RND_ROOT`，然后是当前目录或其上方最近的包含 `entries/` 和 `instruments/` 的文件夹。在库外部，它会以 `NO_LIBRARY` 停止；只有 `rnd readouts` 可以在没有库的情况下工作。

在 Python 中，导入 `mcptoolshop_rnd`：这个名称始终有效。`rnd` 会作为兼容性别名保留，但一个不相关的 PyPI 包也称为 `rnd`，如果两者都已安装，它可能会取代该别名。`rnd` 命令和 `python -m mcptoolshop_rnd` 无论如何都会继续工作。

该库每天都会更新，因此版本有五个部分，`MAJOR.MINOR.PATCH.MICRO.NANO`。前三个版本用于 `rnd` 工具；MICRO 表示结构性库的更改，而 NANO 表示普通更新。`rnd bump` 默认情况下会增加最后一个部分，并从上次标记以来的更改文件中编写一个 CHANGELOG 部分，因此每次更新都会获得自己的小型标记版本。

退出代码：`0` 正常 · `1` 无效的库文件 · `2` 用法错误或未找到 · `3` 运行时失败（外部工具或意外错误）。错误会打印一个代码、一条消息和一个提示；`--debug` 会添加堆栈跟踪。

## 布局

| 路径 | 内容 | 谁编辑 |
|------|------|-----------|
| `entries/YYYY/*.md` | 研究条目：事实的来源 | 人员和代理 |
| `experiments/<name>/` | 用于设备测量的配置、固定输入和结果收据 | 人员和代理 |
| `experiments/<name>/collect.json` | 从工具仓库中收集的记录，记录在固定的提交点（`rnd collect`） | 人员 |
| `instruments/*.md` | 工作室工具和协议，席位可以调用（`kind: instrument`） | 人员和代理 |
| `catalogs/<name>/source.json` | 目录的来源 | 人员 |
| `catalogs/<name>/catalog.json` | 从 `rnd catalog sync` 提取的快照 | 生成；绝不手动编辑 |
| `catalogs/<name>/review.json` | 工作室的适配和每个系列和项目的注释 | 人员 |
| `datapacks/<name>/spec.json` | 数据包包含的内容：包含 glob、许可证、生成器、主机 | 人员 |
| `datapacks/<name>/datapack.json` | 来自 `rnd datapack build` 的清单：每个文件的 SHA-256、许可证、固定版本 | 生成；绝不手动编辑 |
| `datapacks/<name>/hosted.json` | 上传的位置（仓库版本） | 上传后 |
| `mcptoolshop_rnd/` | 命令行界面 | 代码 |
| `rnd/` | `mcptoolshop_rnd` 的兼容性别名 | 代码 |
| `rnd.db` | SQLite FTS5 索引，文件更改时自动重建 | 生成；不在 git 中 |

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
- [verified] A checked statement. (via: what checked it, date)
## Sources
- [primary] https://… — publisher
```

- **来源层级：** `primary`（供应商文档、论文、仓库）、`secondary`（信誉良好的文章）、`aggregator`（摘要网站、AI 搜索结果）、`user`（由人员提供：幻灯片、笔记）、`rig`（在我们的机器上测量）。
- **声明置信度：** `unverified`、`verified`、`disputed`、`wrong`。一个 `verified` 或 `wrong` 声明必须说明使用 `(via: …)` 验证了什么。
- `[[entry-id]]` 链接条目；`rnd show` 列出反向链接。

## 数据包

对于克隆来说太大或太多的已处理数据，会提供为 **数据包**：字节存储在 Hugging Face 数据集仓库中（在发布之前是私有的），并且库仅保留一个小的清单。完整性模型来自 [research-packs](https://github.com/mcp-tool-shop-org/research-packs)：一个清单、每个文件一个 SHA-256、一个单命令验证和一个列表。

```bash
rnd datapack build natural-errors --source experiments/natural-errors  # reads datapacks/natural-errors/spec.json
rnd datapack list
hf download mcp-tool-shop/rnd-natural-errors --repo-type dataset --local-dir ne
rnd datapack verify natural-errors --copy ne/files                      # PASS when every byte matches
```

- **每个文件都需要一个许可证**，如规范中所述。模型输出会包含其模型的条款（例如，对于 Llama 3.1 输出，为“基于 Llama 构建”）。`rnd datapack build` 会拒绝包含未包含许可证的文件。
- **每个生成模型都会被固定**（Ollama 摘要、HF 版本或 API 模型 ID），并附带其角色。
- **`rnd check` 会验证每个清单**，并且如果清单被手动编辑，则会失败。
- 上传会包含 `datapack.json`，以便任何人都可以无需访问此仓库进行验证：`pip install mcptoolshop-rnd`。

## 收集的实验记录

一个工具仓库会提交其自身预先注册的规范和运行记录（interlock 的收据），就像每个仓库提交其 Atlas 地图一样。该库仅发布经过精简的数字副本，这些副本由 `rnd collect` 从工具仓库的固定提交中生成：

```bash
rnd collect                 # list the experiments that collect records
rnd collect e4b             # read each source with git show, trim it, write experiments/e4b/results/
rnd collect e4b --check     # recompute every output; exit 1 if any differs from the committed file
```

- **`experiments/<name>/collect.json`** 命名仓库，以及从中读取的子仓库（`--clone` 覆盖），以及每个来源：其路径、提交记录、其字节的 SHA-256、输出以及实验的 `extract.py` 中的精简函数。
- **固定的来源永远不会更改。**不再与固定版本哈希值匹配的字节将被拒绝。
- **每个记录都包含来源信息：**仓库、来源路径和精简字节的 SHA-256。
- **在写入之前，每个输出都是安全的。**不会保留任何机器路径、主目录或环境变量，并且实验的模块可以添加更严格的保护措施。不会在任何拒绝的情况下写入任何内容。

## 在试用之前测试工具

`rnd probe <url> …` 从每个来源的 API 获取有关工具或模型的第一个问题，而不是从网页摘要中获取：

- **GitHub**（通过 `gh api`，因此它使用您的 GitHub CLI 登录）：许可证，是否已存档，上次提交，最新发布版本，以及对“遥测”的代码搜索。找到的结果是一个阅读的线索，而不是确凿的证据；没有找到结果也不是证据。
- **Hugging Face：**许可证标签，或者对于“其他”，是卡片的许可证名称和链接；访问控制；上次更改。
- **PyPI 和 npm：**许可证，最新版本以及发布时间。
- **rnd 本身：**对名称进行精确的词语搜索，以便您知道该库是否已经包含它。

无法访问的来源将被报告为未知，并附带原因。

## 监控来源

`rnd watch` 检查 [docs/watchlist.json](docs/watchlist.json) 中的来源，并报告自上次检查以来有哪些新内容：

- NVIDIA 的技术博客；
- CUDA 工具包版本；
- NVIDIA 的新 Hugging Face 模型；
- NVIDIA 技能目录；
- 引擎和工具的发布版本，工作室使用这些引擎和工具，例如 Ollama、OpenVINO、PyTorch、ComfyUI 和 Claude Code。

```bash
python -m rnd watch                  # what's new; records what it saw
python -m rnd watch --no-save --json # look without recording
python -m rnd watch --only ollama    # one source
```

What it saw is kept in a state file outside the repository (`$RND_WATCH_STATE`, else `~/.rnd/watch-state.json`).
A source's first check is a baseline: it records the current items and reports none as new. A pre-release is never reported as a source's latest version; a newer one is shown beside it. GitHub release notes and commit messages are kept in the JSON output, so a reader doesn't have to fetch each page. A source that
can't be reached is reported as unknown, and its state is left alone so nothing is skipped silently.

该命令是每周例行程序中的确定性部分（Director，2026-10-13）。一个侦察员读取新项目，使用 `rnd probe` 探测任何候选工具，使用 `rnd search --exact` 检查库，并编写一份简短的排序报告：哪些需要归档，哪些需要尝试，哪些需要跳过。通过拉取请求添加来源，并说明其重要性。

## 与其他工作室工具的关系

- **readouts** 是经过验证的存储区，此实验台从中获取数据（参见上文）。
- **research-os** 为某个主题构建一个受限的、冻结的证据包。可以从条目中链接到某个主题，该主题是决策所依据的主题，并且可以升级为 research-os 包。
- **repo-knowledge** 索引工作室自己的仓库；此库涵盖来自外部的知识。
- 在设计过程中收集的发现也应该记录在这里，以便它们能够超越产生它们的会话。

有关完整工具注册表的详细信息，请参见 `python -m rnd tools`，有关工作流程如何符合工作室的工作流程标准，请参见 [docs/standards.md](docs/standards.md)。

## 安全与信任

- **涉及的数据：**此仓库中的文件（`entries/`、`instruments/`、`catalogs/`、`experiments/`）以及索引 `rnd.db`，它会重新构建索引。`rnd readouts` opens the readouts knowledge bases **read-only**. `rnd sql` 会在只读连接上运行。
- **未涉及的数据：**仓库外部和 readouts 检出中的任何内容。它不存储任何凭据，也不读取任何凭据。
- **网络：**没有，除了 `rnd catalog sync`，它会在您运行它时通过您自己的 `gh` CLI 登录调用 GitHub API。
- **权限：**普通的文件访问权限。没有更高的权限，也没有后台服务。
- **没有遥测。** 不会收集或发送任何数据。
- **公共仓库卫生：**在每次推送之前，都会扫描树，以查找主目录路径和操作员身份。

如 [SECURITY.md](SECURITY.md) 中所述，报告漏洞。

## 测试

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## 状态和许可证

由工作室维护，并每天使用。代码：[MIT](LICENSE)。条目：CC BY 4.0。`catalogs/nvidia-skills/catalog.json` 中的 NVIDIA 技能镜像，会根据该项目的许可证（代码为 Apache-2.0，技能文本为 CC-BY-4.0）复制技能名称和描述，来自 [NVIDIA/skills](https://github.com/NVIDIA/skills)。

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
