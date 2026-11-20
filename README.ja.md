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

スタジオの研究用ベンチ。あらゆる分野からの発見が、短いMarkdown形式のエントリーとして迅速に記録されます。すべての情報源がタグ付けされ、すべての主張が検証済みまたは未検証としてマークされます。実験は、その実験でテストされるエントリーの隣に配置されます。外部カタログはミラーリングされ、評価され、スタジオが利用できるツールを一覧にした登録簿があります。1つのコマンドでこれらすべてを検索できます。

## 配置場所：readoutsの前のベンチ

スタジオの知識を保存する2つのストレージがあり、それぞれ異なる役割を担っています。

| | 研究開発（このリポジトリ） | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| 役割 | ベンチ：情報の取り込み、実験、未解決の質問 | 棚：検証済みの知識ベース |
| ペース | エントリーは数分で作成され、主張は`unverified`から始まります。 | 研究チームによって作成および検証されます。 |
| 形式 | Markdown形式のエントリー、各エントリーはひとつのトピック | ドメインごとにひとつのSQLite知識ベース |
| どの程度整理されているか | 意図的に未整理：議論の余地のある主張、行き詰まり、および中間結果は表示されたままになります。 | 完全に整理済み（乱雑さゼロ）：すべての行に情報源があり、検証されています。 |

知識の流れは一方通行です。

1. **ベンチ。** 発見はエントリーとしてここに記録されます。その主張は`[unverified]`から始まり、何によって検証されたかのメモがある場合にのみ`[verified]`とマークされます。自社のマシンで測定されたデータは、`experiments/`の下にハーネスを添えて、`rig`の情報源として記録されます。
2. **内部の棚。** あるトピックの重要な主張が裏付けられた場合、それはreadoutsのプライベートな作業リポジトリに構築された知識ベースに追加されるか、既存の知識ベースに追加されます。**昇格（readoutsへの反映）は実験を完了する作業の一部です**（ディレクター、2026年10月9日）。実験の結果がここにコミットされると、そのチャートとともに、同じセッションまたは次のセッションでそのreadouts-internalの更新が行われます。ベンチにエントリーが残るのは約1週間までです。定期的な小さな更新は、大きな更新よりも効果的です。実験のREADMEには、その結果の下に昇格の記録が1行で記載されます：「昇格済み：readouts-internal `<kb>` ウェーブ `<n>`、`<date>`」、またはまだ昇格していない理由。
3. **公開の棚。** 知識ベースは、エクスポート許可リストに追加されると、公開リポジトリreadoutsに公開されます。

`rnd readouts`は、ここからすべてのreadouts知識ベースを検索するため、1つのシートから両方のストレージにアクセスできます。まずベンチを検索し、次に棚を検索し、最後にギャップを調査します。

ここでの研究は、スタジオ自身の分野に限定されません。各エントリーは、知識そのものと、それがスタジオにとって何を意味するかという2つのことを別々に記録します（`relevance: act | watch | reference`）。`reference`は、優れた評価です。

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
python -m rnd new-question "Why does X happen?" --field audio
python -m rnd sync --check                  # verify numbers bound to experiments/<id>/results.json
python -m rnd check                         # validate every file (exit 1 on errors)
python -m rnd sql "SELECT tier, count(*) FROM sources GROUP BY tier"
python -m rnd change "what changed"         # add a changelog fragment under changes/ (nano by default)
python -m rnd bump --note "release note"    # release PR: apply changes/ fragments, bump version + CHANGELOG
```

すべてのリストコマンドは、エージェント用に`--json`を受け取ります。`rnd.cmd`（Windows）と`rnd.sh`（POSIXシェル）は、薄いラッパーであるため、コマンドはどのディレクトリからでも実行できます。

他のプロジェクトからこのツールを使用するには、PyPIからインストールします。

```bash
pip install mcptoolshop-rnd
```

これにより、ライブラリではなく、`rnd`コマンドがインストールされます。エントリーは、このリポジトリに保存されます。コマンドは、次の順序でライブラリを検索します。`--library DIR`、次に`$RND_ROOT`、次に現在のディレクトリまたはそれより上位のディレクトリにある、`entries/`と`instruments/`を含む最も近いフォルダー。ライブラリの外では、`NO_LIBRARY`で停止します。`rnd readouts`のみが、ライブラリなしで機能します。

Pythonでは、`mcptoolshop_rnd`をインポートします。この名前は常に機能します。`rnd`は互換性のためのエイリアスとして保持されますが、関連性のないPyPIパッケージも`rnd`と呼ばれており、両方がインストールされている場合、エイリアスを置き換える可能性があります。`rnd`コマンドと`python -m mcptoolshop_rnd`は、どちらの場合でも引き続き機能します。

ライブラリは毎日変更されるため、バージョンには5つのセグメントがあります。`MAJOR.MINOR.PATCH.MICRO.NANO`。最初の3つのセグメントは、`rnd`ツールをバージョン管理します。MICROは、構造的なライブラリの変更を示し、NANOは通常の更新を示します。通常の更新では、`rnd change`を介して`changes/`の下に変更ログのフラグメントが追加されます。リリース時に、`rnd bump`はすべてのフラグメントを消費し、最も高いフラグメントレベルでバージョンを1回だけ進め、1つのCHANGELOGセクションを書き込みます。

終了コード：`0` OK · `1` 無効なライブラリファイル · `2` 使用方法エラーまたは見つからない · `3` 実行時のエラー（外部ツール、または予期しないエラー）。エラーは、コード、メッセージ、およびヒントを出力します。`--debug`は、トレースバックを追加します。

## レイアウト

| パス | 内容 | 編集者 |
|------|------|-----------|
| `entries/YYYY/*.md` | 研究エントリー：真実の情報源 | 人々とエージェント |
| `questions/*.md` | 未解決および解決済みの研究課題 | 人々とエージェント |
| `changes/*.md` | 未リリース時の変更ログフラグメント（`rnd change`） | 人々とエージェント（`rnd bump`が消費） |
| `experiments/<name>/` | ハーネス、固定された入力、`results.json`、および結果のレシート | 人々とエージェント |
| `experiments/<name>/collect.json` | 固定されたコミットでツールリポジトリから収集されたレコード（`rnd collect`） | 人々 |
| `instruments/*.md` | シートが利用できるスタジオツールとプロトコル（`kind: instrument`） | R&Dシートのみ（レビューされた差分） |
| `catalogs/<name>/source.json` | カタログの出所 | 人々 |
| `catalogs/<name>/catalog.json` | `rnd catalog sync`からの固定スナップショット | 自動生成。決して手動で編集しないでください |
| `catalogs/<name>/review.json` | スタジオへの適合性と、ファミリーおよびアイテムごとのメモ | 人々 |
| `datapacks/<name>/spec.json` | データパックに含まれるもの：含めるグロブ、ライセンス、ジェネレーター、ホスト | 人々 |
| `datapacks/<name>/datapack.json` | `rnd datapack build`からのマニフェスト：すべてのファイルのSHA-256、ライセンス、ピン | 自動生成。決して手動で編集しないでください |
| `datapacks/<name>/hosted.json` | アップロードが完了した場所（リポジトリの改訂版） | アップロード後 |
| `mcptoolshop_rnd/` | CLI | コード |
| `rnd/` | `mcptoolshop_rnd`の互換性エイリアス | コード |
| `rnd.db` | SQLite FTS5 インデックス。ファイルが変更されるたびに自動的に再構築されます。 | 生成されたもの。gitには含まれません。 |
| `rnd.misses.jsonl` | `rnd.db`の横にあるローカルのゼロヒット検索ログ（`RND_NO_USAGE=1`で無効化） | 生成されたもの。gitには含まれません。 |

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
- [verified] [c-a1b2c3d4] A checked statement. (via: what checked it, date)
## Sources
- [primary] https://… — publisher
```

- **情報源の階層：** `primary`（ベンダーのドキュメント、論文、リポジトリ）、`secondary`（信頼できる解説）、`aggregator`（概要サイト、AI検索出力）、`user`（個人が提供：スライド、メモ）、`rig`（自社マシンで測定）。
- **主張の信頼度：** `unverified`、`verified`、`disputed`、`wrong`、`superseded`。`verified`または`wrong`の主張は、検証に使用したものを`(via: …)`で示す必要があります。
- `[[entry-id]]`はエントリーをリンクし、`rnd show`はバックリンクをリストします。

## 変更ログフラグメント

更新では、`mcptoolshop_rnd/__init__.py`または`CHANGELOG.md`を直接編集しないため、並行ブランチはバージョンラインで衝突することはありません。

```bash
python -m rnd change "Add study of XYZ"                # writes changes/YYYY-MM-DD-<hex>-<slug>.md (level: nano)
python -m rnd change "New tool feature" --level minor  # levels: nano | micro | patch | minor | major
python -m rnd bump --dry-run                           # preview version bump from changes/ fragments
python -m rnd bump                                     # release PR: bump once, update CHANGELOG.md, delete fragments
```

ファイルが `changes/` に存在しない場合、`rnd bump [nano|micro|…] [--note …]` は
git-diff の動作を維持します。`rnd check` は、形式が正しくないフラグメントをすべてエラーとして報告します。

## バインドされた数値

実験では、公開しても安全な要約数値を `experiments/<id>/results.json` に保存し、エントリ、概要、または実験ノート内の数値を、リテラル直後に直接バインドできます。

```markdown
The judge scored 84.2%<!-- rnd:experiments/e4b/results.json#accuracy:.1% --> on the held-out split.
```

- 生の Markdown、`grep`、および SQLite インデックスは、プレーンなリテラル (`84.2%`) を保持します。
GitHub と Starlight は、目に見えるマーカーやリンクなしで `84.2%` をレンダリングします。
- `rnd sync [paths…]` は、Python の書式指定を使用して `results.json` からバインドされたリテラルを書き換えます。`rnd sync --check` は、いずれかのリテラルが異なる場合、書き込みを行わずに終了コード `1` で終了します。
- `rnd check` は、同期が取れていないバインドされたリテラル、ファイルが見つからない、またはキーが見つからない場合、エラーとして扱い、`[verified]` の主張について、その `(via: …)` がリポジトリの実験を参照しているにもかかわらず、バインドされていない数値が保持されている場合に警告します。

## 主張 ID とリンク

主張は、安定した決定的な `c-<hex>` ID と、ID による古い主張への明示的な関係 (`supersedes`、`contradicts`、`supports`) を持つことができます。

```bash
python -m rnd claims                               # list indexed claims (--state superseded, --json)
python -m rnd claims assign <entry>                # add deterministic c-<hex> ids to one entry's claims
python -m rnd reconcile <entry>                    # mark older claims (superseded / disputed / supported-by)
```

`rnd reconcile <entry>` は、古い主張自身のファイル内にあるその主張の行に対して、ID（未設定の場合）、更新された状態、および逆方向の関係（`superseded-by`、`contradicted-by`、`supported-by`）のみを書き込み、その文や他の行には一切手を加えません。`rnd check` は、壊れたターゲット ID または一方通行のリンクがある場合にエラーを発生させ、`rnd reconcile` の実行を促します。`rnd search` と `rnd show` は、`superseded` と `disputed` の主張にマークを付け、それらを置き換えた、または反論した主張を示します。

## 未解決の質問

未解決の質問は、ステータス `open`、`investigating`、`answered`、または `parked` を持つ個別の Markdown ファイルとして `questions/` に保存されます。

```bash
python -m rnd new-question "Does X hold on Y?" --field systems
python -m rnd questions --status open --json
```

質問の `status` が `answered` の場合、そのフロントマター `answered_by` リストには、少なくとも 1 つの既存の主張 ID が含まれている必要があります。`rnd check` は、既存の主張 ID がない `answered` の質問をエラーとして扱います。質問は `rnd.db` にインデックスが付けられ、`rnd search` と `rnd show` によって返されます。

## ローカル検索ミスログ

`rnd search` が一致するものを見つけられない場合、1 つの JSON 行 (`time` と `query`) をローカルの `.misses.jsonl` ファイルに、`rnd.db` の隣に追加します (`rnd.misses.jsonl` はリポジトリのルートにあり、git で無視されます。または、`<db>.misses.jsonl` は `--db` / `RND_DB` の隣に追加されます)。それ以外は何も記録されず、ネットワーク経由で送信されることもありません。`RND_NO_USAGE=1` はロギングをオフにし、ファイルを削除すると完全に削除されます。`rnd stats --usage` は、合計ミス数と最も頻繁にミスしたクエリを表示します。

## インストゥルメントファイルとオプションの追加機能

- **インストゥルメントファイル (`instruments/*.md`):** 変更された各インストゥルメントファイルが説明に列挙されたレビュー済みの差分において、R&Dシートのみが編集します。外部コンテンツを要約するステップやコマンド（`rnd watch`、`rnd probe`、`rnd collect`、`rnd catalog sync`）によって編集されることは決してありません。
- **コア依存関係と追加機能:** `rnd` のコアは、Python 標準ライブラリのみです。オプションの追加機能はすべて、オプトイングループに存在し、遅延ロードされます。必要な追加機能がないコマンドは、`MISSING_EXTRA` とインストールヒントとともに失敗します。

## データパック

クローンするには大きすぎる、またはかさばりすぎる処理済みデータは、**データパック**として提供されます。バイトは、Hugging Face のデータセットリポジトリ (公開されるまで非公開) に保存され、ライブラリは小さなマニフェストのみを保持します。整合性モデルは、[research-packs](https://github.com/mcp-tool-shop-org/research-packs) から取得されます。マニフェスト、各ファイルの SHA-256、1 つのコマンドによる検証、およびリストが含まれます。

```bash
rnd datapack build natural-errors --source experiments/natural-errors  # reads datapacks/natural-errors/spec.json
rnd datapack list
hf download mcp-tool-shop/rnd-natural-errors --repo-type dataset --local-dir ne
rnd datapack verify natural-errors --copy ne/files                      # PASS when every byte matches
```

- **すべてのファイルには、仕様にライセンスが必要です。** モデルの出力には、そのモデルの条項が含まれます (例: Llama 3.1 の出力の場合、「Llama で作成」)。`rnd datapack build` は、ファイルがカバーされていないデータパックを拒否します。
- **生成に使用されるすべてのモデルは固定されています (Ollama ダイジェスト、HF リビジョン、または API モデル ID)。** また、その役割も指定されます。
- **`rnd check` はすべてのマニフェストを検証し、手動で編集されたマニフェストがある場合は失敗します。**
- アップロードには、ファイルとともに `datapack.json` が含まれているため、誰でもこのリポジトリなしで検証できます: `pip install mcptoolshop-rnd`。

## 収集された実験記録

ツールリポジトリは、事前に登録された仕様と実行記録 (interlock のレシート) をコミットします。これは、すべてのリポジトリが Atlas マップをコミットする方法と同じです。ライブラリは、ツールリポジトリの固定されたコミットから `rnd collect` によって作成された、トリミングされた数値のコピーのみを公開します。

```bash
rnd collect                 # list the experiments that collect records
rnd collect e4b             # read each source with git show, trim it, write experiments/e4b/results/
rnd collect e4b --check     # recompute every output; exit 1 if any differs from the committed file
```

- **`experiments/<name>/collect.json`** は、リポジトリ、読み取り元の兄弟クローン (`--clone` でオーバーライド可能)、および各ソース (パス、コミット、そのバイトの SHA-256、出力、および実験の `extract.py` 内のトリミング関数) を指定します。
- **固定されたソースは変更されません。** ハッシュが固定値と一致しなくなったバイトは拒否されます。
- **すべてのレコードには、プロバナンス (リポジトリ、ソースパス、およびトリミングされたバイトの SHA-256) が含まれます。**
- **すべての出力は、書き込まれる前に公開しても安全です。** マシンパス、ホームディレクトリ、または環境フィールドは保持されず、実験のモジュールはより厳格なガードを追加できます。拒否された場合は何も書き込まれません。

## 試行前にツールをテストする

`rnd probe <url> …` は、各ソースの独自の API から、ツールまたはモデルに関する最初の質問に答えます。Web ページの要約から答えることはありません。

- **GitHub** (`gh api` を介して、そのため、自分の GitHub CLI ログインを使用します): ライセンス、アーカイブされているかどうか、最後のプッシュ、最新のリリース、および「テレメトリ」のコード検索。ヒットは、読むべき手がかりであり、決して証拠ではありません。ヒットがゼロであることも証拠ではありません。
- **Hugging Face:** ライセンスタグ、または「その他」の場合は、カードのライセンス名とリンク。ゲートキーピング。最後の変更。
- **PyPI と npm:** ライセンス、最新バージョン、および公開日。
- **rnd 自体:** 正確な単語検索で名前を検索します。これにより、ライブラリがすでにそれを持っているかどうかを確認できます。

アクセスできないソースは、理由とともに不明として報告されます。

## ソースの監視

`rnd watch` は、[docs/watchlist.json](docs/watchlist.json) 内のソースをチェックし、最後のチェック以降の変更点を報告します。

- NVIDIA の技術ブログ。
- CUDA ツールキットのバージョン。
- NVIDIA の新しい Hugging Face モデル。
- NVIDIA のスキルカタログ。
- スタジオが実行するエンジンとツールのリリース (例: Ollama、OpenVINO、PyTorch、ComfyUI、および Claude Code)。

```bash
python -m rnd watch                  # what's new; records what it saw
python -m rnd watch --no-save --json # look without recording
python -m rnd watch --only ollama    # one source
```

リポジトリの外にある状態ファイル（`$RND_WATCH_STATE`、または`~/.rnd/watch-state.json`）に、その結果が保存されます。
ソースの最初のチェックは、基準となるもので、現在の項目を記録し、新しい項目は存在しないと報告します。プレリリースがソースの最新バージョンとして報告されることは決してなく、最新バージョンより新しいプレリリースがある場合はその横に並べて表示されます。GitHubのリリースノートとコミットメッセージは、JSON形式で出力されるため、ユーザーは各ページを個別に取得する必要はありません。アクセスできないソースは、不明として報告され、その状態は変更されないため、何もサイレントにスキップされることはありません。

このコマンドは、毎週のルーチンの決定的な部分です（Director、2026-10-13）。スカウトは、新しい項目を読み込み、候補となるツールを`rnd probe`でテストし、ライブラリを`rnd search --exact`でチェックし、短い優先順位付けされたレポートを作成します。レポートには、記録すべき項目、試すべき項目、スキップすべき項目が記載されます。プルリクエストでソースを追加し、その重要性を説明します。

## 他のスタジオツールとの関係

- **readouts** は、このベンチが知識を送り込む検証済みの棚です（上記参照）。
- **research-os** は、特定のトピックに関する、アクセス制限付きの固定された証拠パックをビルドします。意思決定の基礎となるトピックは、エントリーからリンクされたresearch-osパックに昇格できます。
- **repo-knowledge** はスタジオ自身のリポジトリをインデックス化し、このライブラリはそれらの外部にある知識をカバーします。
- 何かを設計する際に収集された情報は、ここにも保存されるため、それを生成したセッションが終了した後も残ります。

完全なツールの登録については、`python -m rnd tools`を参照し、ワークフローがスタジオのワークフロールールにどのように適合するかについては、[docs/standards.md](docs/standards.md)を参照してください。

## セキュリティと信頼性

- **アクセスされるデータ:** このリポジトリ内のファイル（`entries/`、`questions/`、`changes/`、`instruments/`、`catalogs/`、`experiments/`）、インデックス`rnd.db`、およびその関連するローカルミスログ`rnd.misses.jsonl`。`rnd readouts`は、readoutsの知識ベースを**読み取り専用**で開きます。`rnd sql`は、読み取り専用の接続に対して実行されます。
- **アクセスされないデータ:** リポジトリとreadoutsのチェックアウトの外部にあるデータ。認証情報は保存されず、読み取られもしません。
- **ネットワーク:** `rnd catalog sync`、`rnd probe`、および`rnd watch`を除き、ネットワーク通信はありません。これらは実行時に公開メタデータを読み取るか、ユーザー自身の`gh` CLIログインを通じてGitHub APIを呼び出します。
- **権限:** 通常のファイルアクセスのみ。特別な権限やバックグラウンドサービスはありません。
- **ローカル専用の使用状況ログ:** 何のデータも収集されず、どこにも送信されません。`rnd search`が一致するものを見つけられない場合、`rnd.db`の隣にある`rnd.misses.jsonl`（リポジトリ内ではgitで無視されます。`--db`または`$RND_DB`指定時はその隣にある`<db>.misses.jsonl`）に1行（UTC時刻とクエリ）を追加します。`RND_NO_USAGE=1`を設定してログをオフにしたり、いつでも`.misses.jsonl`を削除してログをクリアしたりできます。他の使用状況データは記録されません。
- **パブリックリポジトリの衛生管理:** 各プッシュの前に、ツリー内にホームディレクトリパスやオペレーターの身元情報が含まれていないかスキャンされます。

脆弱性を報告する方法については、[SECURITY.md](SECURITY.md)を参照してください。

## テスト

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## ステータスとライセンス

スタジオによって維持され、毎日使用されています。コード: [MIT](LICENSE)。エントリー: CC BY 4.0。`catalogs/nvidia-skills/catalog.json`にあるNVIDIAのスキルミラーは、そのプロジェクトのライセンス（コードの場合はApache-2.0、スキルテキストの場合はCC-BY-4.0）に基づいて、[NVIDIA/skills](https://github.com/NVIDIA/skills)からスキル名と説明を再現します。

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
