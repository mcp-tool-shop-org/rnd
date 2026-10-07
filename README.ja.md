<p align="center">
  <a href="README.md">English</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

スタジオの研究用ベンチ。あらゆる分野からの発見が、短いMarkdown形式のエントリーとして迅速に記録され、すべての情報源がタグ付けされ、すべての主張が検証済みまたは未検証としてマークされます。実験は、それらによってテストされるエントリーの隣に配置されます。外部カタログはミラーリングされ、評価され、スタジオが研究に利用できるツールを一覧にした登録簿があります。1つのコマンドでこれらすべてを検索できます。

## 配置場所：測定結果が表示される前のベンチ

スタジオの知識を保存する2つのストレージがあり、それぞれ異なる役割を担っています。

| | 研究開発（このリポジトリ） | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| 役割 | ベンチ：情報の収集、実験、未解決の質問 | 棚：検証済みの知識ベース |
| ペース | エントリーの作成時間：数分、主張は`unverified`から開始 | 研究チームによって作成および検証 |
| 形式 | Markdown形式のエントリー、各エントリーは1つのトピック | ドメインごとに1つのSQLite知識ベース |
| 雑然さ | 想定内：議論のある主張、行き詰まり、中間結果もそのまま残る | なし：各行は出典付きで検証済み |

知識の流れは一方通行です。

1. **ベンチ。** 発見はエントリーとしてここに記録されます。その主張は`[unverified]`から始まり、何がそれを検証したかを示すメモとともに`[verified]`とマークされます。自社のマシンで測定されたデータは、そのハーネスが`experiments/`の下に配置された状態で、`rig`の情報源として記録されます。
2. **内部の棚。** あるトピックの重要な主張が裏付けられた場合、測定結果のプライベートな作業リポジトリに知識ベースとして構築されるか、既存の知識ベースに追加されます。
3. **公開の棚。** 知識ベースは、エクスポート許可リストに追加されると、公開リポジトリに公開されます。

`rnd readouts`は、ここからすべての測定結果の知識ベースを検索するため、1つのインターフェースで両方のストレージにアクセスできます。まずベンチを検索し、次に棚を検索し、最後にギャップを調査します。

ここでの研究は、スタジオ自身の分野に限定されません。各エントリーは、知識そのものと、それがスタジオにとって何を意味するかという2つのことを別々に記録します（`relevance: act | watch | reference`）。`reference`は、十分な根拠のある結論です。

## 使用方法

Python 3.10以降が必要です。その他の依存関係はありません（標準ライブラリのみ）。Windows、macOS、およびLinuxで実行できます。リポジトリのルートから：

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
```

すべてのリスト表示コマンドは、エージェントに対して`--json`を受け取ります。`rnd.cmd`（Windows）と`rnd.sh`（POSIXシェル）は、薄いラッパーであるため、コマンドはどのディレクトリからでも実行できます。

終了コード：`0`（正常）、`1`（無効なライブラリファイル）、`2`（使用方法エラーまたは見つからない）、`3`（実行時エラー）（外部ツール、または予期しないエラー）。エラーが発生した場合、コード、メッセージ、およびヒントが出力されます。`--debug`は、トレースバックを追加します。

## レイアウト

| パス | 内容 | 編集者 |
|------|------|-----------|
| `entries/YYYY/*.md` | 研究エントリー：信頼できる情報源 | 人およびエージェント |
| `experiments/<name>/` | リグ測定用のハーネス、固定された入力、および結果レシート | 人およびエージェント |
| `instruments/*.md` | スタジオが使用できるツールとプロトコル（`kind: instrument`） | 人およびエージェント |
| `catalogs/<name>/source.json` | カタログの出所 | 人 |
| `catalogs/<name>/catalog.json` | `rnd catalog sync`からの固定スナップショット | 生成されるため、手動で編集することはできません |
| `catalogs/<name>/review.json` | スタジオの適合性およびファミリーとアイテムごとの注釈 | 人 |
| `rnd/` | CLI | コード |
| `rnd.db` | SQLite FTS5インデックス。ファイルが変更されるたびに自動的に再構築されます。 | 生成されるため、Gitには含まれません |

## エントリー形式

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

- **情報源の階層：** `primary`（ベンダーのドキュメント、論文、リポジトリ）、`secondary`（信頼できる解説）、`aggregator`（概要サイト、AI検索結果）、`user`（個人が提供：スライド、メモ）、`rig`（自社のマシンで測定）。
- **主張の信頼度：** `unverified`、`verified`、`disputed`、`wrong`。`verified`または`wrong`の主張は、何がそれを検証したかを`(via: …)`で示す必要があります。
- `[[entry-id]]`はエントリーをリンクし、`rnd show`はバックリンクをリストします。

## 他のスタジオツールとの関係

- **readouts**は、このベンチから情報を供給される、検証済みの棚です（上記参照）。
- **research-os**は、1つのトピックに対するゲートされた、固定された証拠パックを構築します。意思決定の根拠となるトピックは、research-osパックに昇格し、エントリーからリンクできます。
- **repo-knowledge**は、スタジオ自身のリポジトリをインデックス化します。このライブラリは、それらの外部の知識を扱います。
- 何かを設計する際に収集された情報は、ここにも保存されるため、それを生成したセッションを超えて残ります。

完全な機器登録については、`python -m rnd tools`を参照し、ワークフローがスタジオのワークフロールールにどのように適合するかについては、[docs/standards.md](docs/standards.md)を参照してください。

## セキュリティと信頼

- **アクセスされるデータ：** このリポジトリ内のファイル（`entries/`、`instruments/`、`catalogs/`、`experiments/`）と、再構築されるインデックス`rnd.db`。`rnd readouts` opens the readouts knowledge bases **read-only**. `rnd sql`は、読み取り専用の接続に対して実行されます。
- **アクセスされないデータ：** リポジトリとreadoutsチェックアウトの外部のデータ。認証情報は保存されず、読み取られません。
- **ネットワーク：** `rnd catalog sync`を除く。これは、実行時に独自の`gh`CLIログインを通じてGitHub APIを呼び出します。
- **権限：** 通常のファイルアクセス。特別な権限やバックグラウンドサービスはありません。
- **テレメトリーはありません。** 何も収集または送信されません。
- **公開リポジトリの衛生管理：** 各プッシュの前に、ツリーはホームディレクトリのパスとオペレーターのIDについてスキャンされます。

脆弱性を[SECURITY.md](SECURITY.md)に記載されている方法で報告してください。

## テスト

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## ステータスとライセンス

スタジオによって維持され、毎日使用されています。コード：[MIT](LICENSE)。エントリー：CC BY 4.0。`catalogs/nvidia-skills/catalog.json`のNVIDIAスキルミラーは、そのプロジェクトのライセンス（コードの場合はApache-2.0、スキルテキストの場合はCC-BY-4.0）に基づいて、[NVIDIA/skills](https://github.com/NVIDIA/skills)からスキルの名前と説明を再現します。

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
