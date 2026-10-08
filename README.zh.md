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

工作室的研究工作台。来自任何领域的研究成果会以简短的 Markdown 格式快速呈现，每个来源都会被标记，并且每个声明都会被标记为已验证或未验证。实验结果与它们所测试的条目并列。外部目录会被镜像并进行评估，并且一个注册表会列出工作室可以使用的研究工具。一个命令可以搜索所有内容。

## 它所处的位置：在查看结果之前的工作台

工作室的知识存储在两个地方，并且它们执行不同的任务。

| | 研究与开发（此仓库） | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| 角色 | 工作台：接收、实验、开放性问题 | 书架：经过验证的知识库 |
| 速度 | 一个条目几分钟内完成，声明从 `unverified` 开始 | 由研究团队构建和验证 |
| 形式 | Markdown 条目，每个条目一个主题 | 每个领域一个 SQLite 知识库 |
| 有多乱？ | 故意弄得乱：有争议的说法、无法解决的问题和临时结果都保留着，以便查看。 | 一点也不乱：每一行数据都有来源，并且经过验证。 |

知识的流动方向：

1. **工作台。** 研究成果以条目的形式在此处呈现。其声明从 `[unverified]` 开始，并且只有在记录了验证内容后，才会标记为 `[verified]`。
在我们的机器上进行的测量结果会以 `rig` 来源的形式记录，其配置在 `experiments/` 中。
2. **内部书架。** 一旦某个主题的关键声明得到证实，它就会被构建到查看结果的私有工作仓库中的知识库中，或者添加到现有的知识库中。
3. **公共书架。** 当知识库被添加到导出允许列表中时，它将被发布到公共查看结果仓库中。

`rnd readouts` 从此处搜索每个查看结果知识库，因此一个席位可以访问两个存储。首先搜索工作台，然后搜索书架，最后研究差距。

这里的研究不仅限于工作室自己的领域。每个条目都会分别记录两件事：知识是什么，以及它对工作室意味着什么（`relevance: act | watch | reference`）。`reference` 是一个明确的结论。

## 使用方法

需要 Python 3.10 或更高版本，并且不需要其他任何东西（仅使用标准库）。可在 Windows、macOS 和 Linux 上运行。从仓库根目录：

```bash
python -m rnd search cuda graphs            # full-text over entries + catalogues
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

要从其他项目中调用该工具，请从 PyPI 安装它：

```bash
pip install mcptoolshop-rnd
```

这会安装 `rnd` 命令，而不是库：这些条目位于此仓库中。该命令按以下顺序查找库：`--library DIR`，然后是 `$RND_ROOT`，然后是当前目录或其上方目录中包含 `entries/` 和 `instruments/` 的最近文件夹。在库外部，它会停止并显示 `NO_LIBRARY`；只有 `rnd readouts` 才能在没有库的情况下工作。

在 Python 中，导入 `mcptoolshop_rnd`：该名称始终有效。`rnd` 被保留为一个兼容性别名，但还有一个名为 `rnd` 的无关 PyPI 包，如果同时安装了这两个包，它可能会替换该别名。无论如何，`rnd` 命令和 `python -m mcptoolshop_rnd` 都能正常工作。

库每天都在更新，因此版本包含五个部分：`MAJOR.MINOR.PATCH.MICRO.NANO`。前三个部分是 `rnd` 工具的版本；MICRO 表示库结构发生了变化，而 NANO 表示普通更新。`rnd bump` 默认情况下会增加最后一个部分，并从上次标记以来发生更改的文件中生成一个 CHANGELOG 部分，因此每次更新都会获得自己的小型标记版本。

退出代码：`0` 正常 · `1` 无效的库文件 · `2` 用法错误或未找到 · `3` 运行时错误（外部工具或意外错误）。错误会打印代码、消息和提示；`--debug` 会添加堆栈跟踪。

## 布局

| 路径 | 内容 | 谁编辑 |
|------|------|-----------|
| `entries/YYYY/*.md` | 研究条目：事实的来源 | 人员和代理 |
| `experiments/<name>/` | 用于设备测量 Harness、固定输入和结果收据 | 人员和代理 |
| `instruments/*.md` | 工作室可以使用的工具和协议（`kind: instrument`） | 人员和代理 |
| `catalogs/<name>/source.json` | 目录的来源 | 人员 |
| `catalogs/<name>/catalog.json` | 从 `rnd catalog sync` 提取的快照 | 生成；切勿手动编辑 |
| `catalogs/<name>/review.json` | 工作室的适配性和每个系列和项目的说明 | 人员 |
| `mcptoolshop_rnd/` | 命令行界面 (CLI) | 代码 |
| `rnd/` | `mcptoolshop_rnd` 的兼容性别名。 | 代码 |
| `rnd.db` | SQLite FTS5 索引，当文件发生更改时会自动重建 | 生成；不在 git 中 |

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
- **声明置信度：** `unverified`、`verified`、`disputed`、`wrong`。 `verified` 或 `wrong` 声明必须说明使用 `(via: …)` 进行了验证。
- `[[entry-id]]` 链接条目；`rnd show` 列出反向链接。

## 与其他工作室工具的关系

- **readouts** 是经过验证的书架，此工作台会向其提供数据（参见上文）。
- **research-os** 构建一个受控的、冻结的证据包，用于一个主题。可以根据某个主题，将其升级为 research-os 包，并从该条目中进行链接，因为该主题是决策所依赖的。
- **repo-knowledge** 索引工作室自己的仓库；此库涵盖来自外部的知识。
- 在设计过程中收集到的研究成果也应该放在这里，以便它们能够超越产生它们的会话。

有关完整的仪器注册表的详细信息，请参见 `python -m rnd tools`，有关工作流程如何符合工作室的工作流程标准，请参见 [docs/standards.md](docs/standards.md)。

## 安全与信任

- **涉及的数据：** 此仓库中的文件（`entries/`、`instruments/`、`catalogs/`、`experiments/`）以及索引 `rnd.db`，它会重建索引。`rnd readouts` opens the readouts knowledge bases **read-only**. `rnd sql` 命令针对只读连接运行。
- **不涉及的数据：** 仓库和查看结果检出之外的任何内容。它不存储任何凭据，也不读取任何凭据。
- **网络：** 除了 `rnd catalog sync` 之外，没有网络连接，它会在您运行该命令时，通过您自己的 `gh` CLI 登录来调用 GitHub API。
- **权限：** 普通的文件访问权限。没有更高的权限，也没有后台服务。
- **没有遥测数据。** 不会收集或发送任何数据。
- **公共仓库卫生：** 在每次推送之前，都会扫描树，以查找主目录路径和操作员身份。

如 [SECURITY.md](SECURITY.md) 中所述，请报告漏洞。

## 测试

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## 状态和许可证

由工作室维护，并每天使用。代码：[MIT](LICENSE)。条目：CC BY 4.0。`catalogs/nvidia-skills/catalog.json` 中的 NVIDIA 技能镜像，会根据该项目的许可证（代码为 Apache-2.0，技能文本为 CC-BY-4.0）复制技能名称和描述，该项目为 [NVIDIA/skills](https://github.com/NVIDIA/skills)。

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
