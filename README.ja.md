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

スタジオの研究用ベンチ。あらゆる分野からの発見が、短いMarkdown形式のエントリーとして迅速に記録され、すべての情報源がタグ付けされ、すべての主張が検証済みまたは未検証としてマークされます。実験は、その実験でテストされるエントリーの隣に配置されます。外部カタログはミラーリングされ、評価され、スタジオが利用できるツールを一覧表示したレジストリが用意されています。1つのコマンドでこれらすべてを検索できます。

## どこに置かれるか：readoutsの前のベンチ

スタジオの知識を保存する2つのストレージがあり、それぞれ異なる役割を担っています。

| | 研究開発（このリポジトリ） | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| 役割 | ベンチ：情報の入力、実験、未解決の質問 | 棚：検証済みの知識ベース |
| ペース | エントリーの作成時間：数分、主張は`unverified`から開始 | 研究チームによって作成および検証 |
| 形式 | Markdown形式のエントリー、各エントリーはひとつのトピック | ドメインごとにひとつのSQLite知識ベース |
| 整理整頓度 | 意図的に整理されていない：議論の余地がある主張、行き詰まり、および中間結果は表示されたまま | まったく整理されていないわけではない：すべての行には情報源と検証結果が記載されている |

知識の流れは一方通行

1. **ベンチ。** 調査結果がエントリとしてここに記録されます。その主張は`[unverified]`から始まり、どの機関が検証したかを示すメモが`[verified]`として付記されます。
自社で実施した測定は、`rig`のソースとして記録され、そのテスト環境は`experiments/`に記載されます。
2. **内部の棚。** あるテーマの主要な主張が妥当であると確認されると、その内容はreadoutsのプライベートな作業リポジトリに組み込まれるか、既存のリポジトリに追加されます。
**プロモーションは、実験を完了させるプロセスの一部です**（ディレクター、2026年10月9日）。実験の結果がここにコミットされると、そのreadouts-internalの更新が、同じセッションまたは次のセッションで、グラフとともに追跡されます。ベンチに置かれたままになる期間は、通常1週間を超えません。定期的な小さな更新の方が、大きな更新よりも効果的です。
実験のREADMEファイルには、その結果の下にプロモーションに関する情報が1行で記録されます。「プロモーション：readouts-internal `<kb>` ウェーブ `<n>`、`<date>`」、または、まだプロモーションされていない理由。
3. **公開の棚。** ナレッジベースは、エクスポート許可リストに追加されると、公開リポジトリreadoutsに公開されます。

`rnd readouts`はここからすべてのreadouts知識ベースを検索するため、1つの席から両方のストアにアクセスできます。まずベンチを検索し、次に棚を検索し、最後にギャップを調査します。

ここでの研究は、スタジオ自身の分野に限定されません。各エントリーは、知識そのものと、それがスタジオにとって何を意味するかという2つのことを別々に記録します（`relevance: act | watch | reference`）。`reference`は、信頼できる検証結果です。

## 使用方法

Python 3.10以降が必要です。それ以外に必要なものはありません（標準ライブラリのみ）。Windows、macOS、およびLinuxで実行できます。リポジトリのルートから：

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

すべてのリスト表示コマンドは、`--json`をエージェントとして受け取ります。`rnd.cmd`（Windows）と`rnd.sh`（POSIXシェル）は、薄いラッパーであるため、コマンドはどのディレクトリからでも実行できます。

他のプロジェクトからこのツールを使用するには、PyPIからインストールします。

```bash
pip install mcptoolshop-rnd
```

これにより、ライブラリではなく、`rnd`コマンドがインストールされます。エントリーは、このリポジトリに保存されます。コマンドは、次の順序でライブラリを検索します。`--library DIR`、次に`$RND_ROOT`、次に現在のディレクトリまたはそれより上位のディレクトリにある、`entries/`と`instruments/`を含む最も近いフォルダー。ライブラリの外では、`NO_LIBRARY`で停止します。`rnd readouts`のみが、ライブラリなしで機能します。

Pythonでは、`mcptoolshop_rnd`をインポートします。この名前は常に機能します。`rnd`は、互換性のためのエイリアスとして保持されますが、関連性のないPyPIパッケージも`rnd`と呼ばれており、両方がインストールされている場合、エイリアスを置き換える可能性があります。`rnd`コマンドと`python -m mcptoolshop_rnd`は、どちらの場合でも機能します。

ライブラリは毎日変更されるため、バージョンには5つのセグメントがあります。`MAJOR.MINOR.PATCH.MICRO.NANO`。最初の3つのセグメントは、`rnd`ツールをバージョン管理します。MICROは、構造的なライブラリの変更を示し、NANOは、通常の更新を示します。`rnd bump`は、デフォルトで最後のセグメントをインクリメントし、最後のタグ以降に変更されたファイルからCHANGELOGセクションを作成するため、各更新には、独自の小さなタグ付きバージョンが割り当てられます。

終了コード：`0` OK · `1` 無効なライブラリファイル · `2` 使用方法エラーまたは見つからない · `3` 実行時のエラー（外部ツール、または予期しないエラー）。エラーは、コード、メッセージ、およびヒントを出力します。`--debug`は、トレースバックを追加します。

## レイアウト

| パス | 内容 | 編集者 |
|------|------|-----------|
| `entries/YYYY/*.md` | 研究エントリー：信頼できる情報源 | 人およびエージェント |
| `experiments/<name>/` | リグ測定用のハーネス、固定された入力、および結果レシート | 人およびエージェント |
| `experiments/<name>/collect.json` | ツールリポジトリの固定されたコミットから収集されたレコード（`rnd collect`） | 人 |
| `instruments/*.md` | スタジオが使用できるツールとプロトコル（`kind: instrument`） | 人およびエージェント |
| `catalogs/<name>/source.json` | カタログの入手先 | 人 |
| `catalogs/<name>/catalog.json` | `rnd catalog sync`からの固定されたスナップショット | 生成される。手動で編集することは決してない |
| `catalogs/<name>/review.json` | スタジオの適合性および、ファミリーおよびアイテムごとの注釈 | 人 |
| `datapacks/<name>/spec.json` | データパックに含まれるもの：含めるグロブ、ライセンス、ジェネレーター、ホスト | 人 |
| `datapacks/<name>/datapack.json` | `rnd datapack build`からのマニフェスト：すべてのファイルのSHA-256、ライセンス、ピン | 生成される。手動で編集することは決してない |
| `datapacks/<name>/hosted.json` | アップロードの場所（リポジトリの改訂版） | アップロード後 |
| `mcptoolshop_rnd/` | CLI | コード |
| `rnd/` | `mcptoolshop_rnd`の互換性エイリアス | コード |
| `rnd.db` | SQLite FTS5インデックス。ファイルが変更されるたびに自動的に再構築されます。 | 生成される。gitには含まれない |

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
- **主張の信頼度：** `unverified`、`verified`、`disputed`、`wrong`。`verified`または`wrong`の主張は、検証に使用されたものを`(via: …)`で示す必要があります。
- `[[entry-id]]`はエントリーをリンクし、`rnd show`はバックリンクを一覧表示します。

## データパック

クローンするには大きすぎる、またはかさばりすぎる処理済みデータは、**データパック**として提供されます。データは、Hugging Faceのデータセットリポジトリ（公開されるまで非公開）に保存され、ライブラリには小さなマニフェストのみが保存されます。整合性モデルは、[research-packs](https://github.com/mcp-tool-shop-org/research-packs)から取得されます。マニフェスト、すべてのファイルのSHA-256、1つのコマンドによる検証、およびリスト表示が含まれます。

```bash
rnd datapack build natural-errors --source experiments/natural-errors  # reads datapacks/natural-errors/spec.json
rnd datapack list
hf download mcp-tool-shop/rnd-natural-errors --repo-type dataset --local-dir ne
rnd datapack verify natural-errors --copy ne/files                      # PASS when every byte matches
```

- **すべてのファイルには、仕様でライセンスが必要です。** モデルの出力には、そのモデルの規約が含まれます（例：Llama 3.1の出力の場合、「Llamaでビルド」）。`rnd datapack build`は、ファイルがカバーされていないパッケージを拒否します。
- **生成に使用するすべてのモデルは、固定されています**（Ollamaダイジェスト、HFリビジョン、またはAPIモデルID）、およびその役割とともに。
- **`rnd check`はすべてのマニフェストを検証し、手動で編集された場合はエラーを返します。**
- アップロードには、ファイルとともに`datapack.json`が含まれているため、誰でもこのリポジトリなしで検証できます：`pip install mcptoolshop-rnd`。

## 収集された実験記録

A tool repository commits its own pre-registered specs and run records (interlock's receipts),
the way every repository commits its Atlas map. The library publishes only a trimmed copy of the
numbers, made by `rnd collect` from the tool repository at pinned commits:

```bash
rnd collect                 # list the experiments that collect records
rnd collect e4b             # read each source with git show, trim it, write experiments/e4b/results/
rnd collect e4b --check     # recompute every output; exit 1 if any differs from the committed file
```

- **`experiments/<name>/collect.json`**は、リポジトリの名前、読み取り元の兄弟クローン（`--clone`でオーバーライド）、および各ソース（そのパス、コミット、SHA-256のバイト数、出力、および実験の`extract.py`内のトリミング関数）を指定します。
- **固定されたソースは決して変更されません。** ハッシュ値が固定された値と一致しなくなったバイトは拒否されます。
- **すべての記録には、その起源が記録されています。** リポジトリ、ソースパス、およびトリミングされたバイトのSHA-256が含まれます。
- **すべての出力は、書き込まれる前に安全性が確認されます。** マシンパス、ホームディレクトリ、または環境フィールドは残らず、実験のモジュールはより厳格なガードを追加できます。拒否された場合は、何も書き込まれません。

## 試行前にツールをテストする

`rnd probe <url> …`は、各ソースの独自のAPIから、ツールまたはモデルに関する最初の質問に答えます。ウェブページの概要からではありません。

- **GitHub**（`gh api`を通じて、したがって、あなたのGitHub CLIのログインを使用します）：ライセンス、アーカイブされているかどうか、最後のプッシュ、最新のリリース、および「テレメトリ」のコード検索。検索結果は、読むべき情報への手がかりであり、決して証拠ではありません。検索結果がゼロであることも、証拠にはなりません。
- **Hugging Face：** ライセンスタグ、または「その他」の場合は、カードのライセンス名とリンク、アクセス制限、最後の変更。
- **PyPIおよびnpm：** ライセンス、最新バージョン、および公開日。
- **rnd自体：** 正確な単語による名前の検索。これにより、そのライブラリがすでにその名前を持っているかどうかを確認できます。

アクセスできないソースは、理由とともに「不明」として報告されます。

## ソースの監視

`rnd watch`は、[docs/watchlist.json](docs/watchlist.json)内のソースをチェックし、最後のチェック以降の変更を報告します。

- NVIDIAの技術ブログ。
- CUDAツールキットのバージョン。
- NVIDIAの新しいHugging Faceモデル。
- NVIDIAのスキルカタログ。
- スタジオが使用するエンジンとツールのリリース（例：Ollama、OpenVINO、PyTorch、ComfyUI、Claude Code）。

```bash
python -m rnd watch                  # what's new; records what it saw
python -m rnd watch --no-save --json # look without recording
python -m rnd watch --only ollama    # one source
```

確認された内容は、リポジトリ外のステートファイル（`$RND_WATCH_STATE`、それ以外の場合は`~/.rnd/watch-state.json`）に保存されます。ソースの最初のチェックはベースラインです。現在の項目を記録し、新しい項目は何も報告しません。プレリリースは、ソースの最新バージョンとして報告されることはありません。新しいバージョンは、その横に表示されます。GitHubのリリースノートとコミットメッセージはJSON出力に保存されるため、読者は各ページをフェッチする必要はありません。アクセスできないソースは「不明」として報告され、その状態は変更されないため、何もサイレントにスキップされることはありません。

このコマンドは、週ごとの儀式の決定的な部分です（Director、2026-10-13）。スカウトは、新しい項目を読み取り、候補となるツールを`rnd probe`でテストし、ライブラリを`rnd search --exact`でチェックし、短いランク付けされたレポートを作成します。レポートには、ファイルに保存するもの、試すもの、スキップするものなどが記載されます。プルリクエストでソースを追加し、その理由を説明します。

## 他のスタジオツールとの関係

- **readouts**は、このベンチに供給される検証済みの棚です（上記参照）。
- **research-os**は、あるトピックに対して、ゲートされた、固定された証拠パックをビルドします。意思決定の基礎となるトピックは、エントリからリンクされたresearch-osパックに昇格できます。
- **repo-knowledge**は、スタジオ自身のリポジトリをインデックス化します。このライブラリは、それらの外部の知識をカバーします。
- 何かを設計中に収集された情報は、ここにも属します。そのため、それらは生成されたセッションを超えて残ります。

完全なインストルメントレジストリについては、`python -m rnd tools`を参照し、ワークフローがスタジオのワークフロールーの標準にどのように適合するかについては、[docs/standards.md](docs/standards.md)を参照してください。

## セキュリティと信頼

- **アクセスされたデータ：**このリポジトリ（`entries/`、`instruments/`、`catalogs/`、`experiments/`）内のファイルと、再構築されるインデックス`rnd.db`。`rnd readouts` opens the readouts knowledge bases **read-only**. `rnd sql`は、読み取り専用接続に対して実行されます。
- **アクセスされていないデータ：**リポジトリとreadoutsチェックアウトの外部のデータ。認証情報は保存されず、読み取られません。
- **ネットワーク：**なし。ただし、`rnd catalog sync`は、実行時に、独自の`gh`CLIログインを通じて、GitHub APIを呼び出します。
- **権限：**通常のファイルアクセス。特別な権限やバックグラウンドサービスはありません。
- **テレメトリなし。** 何も収集または送信されません。
- **公開リポジトリの衛生管理：**すべてのプッシュの前に、ツリーはホームディレクトリパスとオペレーターのIDについてスキャンされます。

脆弱性を[SECURITY.md](SECURITY.md)に記載されている方法で報告してください。

## テスト

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## ステータスとライセンス

スタジオによって維持され、毎日使用されています。コード：[MIT](LICENSE)。エントリ：CC BY 4.0。`catalogs/nvidia-skills/catalog.json`のNVIDIAスキルミラーは、そのプロジェクトのライセンス（コードの場合はApache-2.0、スキルテキストの場合はCC-BY-4.0）の下で、[NVIDIA/skills](https://github.com/NVIDIA/skills)からスキル名と説明を再現します。

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
