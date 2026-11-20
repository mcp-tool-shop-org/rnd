<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

スタジオの研究用ベンチ。あらゆる分野からの発見が、短いMarkdown形式のエントリーとして迅速に記録されます。すべての情報源にはタグが付けられ、すべての主張は検証済みまたは未検証としてマークされます。実験は、それらを検証するエントリーの隣に配置されます。外部カタログはミラーリングされ、評価され、スタジオが利用できるツールを一覧にしたレジストリがあります。1つのコマンドでこれらすべてを検索できます。

## 配置場所：readoutsの前のベンチ

スタジオの知識を保存する2つのストレージがあり、それぞれ異なる役割を担っています。

| | 研究開発（このリポジトリ） | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| 役割 | ベンチ：情報の取り込み、実験、未解決の質問 | 棚：検証済みの知識ベース |
| ペース | エントリーは数分で作成され、主張は`unverified`から始まります。 | 研究チームによって作成および検証されます。 |
| 形式 | Markdown形式のエントリー、各エントリーはひとつのトピック | ドメインごとにひとつのSQLite知識ベース |
| どの程度雑然としているか | 意図的に雑然としている：議論の余地のある主張、行き詰まり、および中間結果がそのまま可視化されます。 | まったく雑然としていない：すべての行に情報源が明記され、検証されています。 |

知識の流れは一方通行です。

1. **ベンチ。** 発見はエントリーとしてここに記録されます。その主張は`[unverified]`から始まり、何を根拠に検証されたかを示すメモがある場合にのみ`[verified]`とマークされます。自社で作成したマシンで測定されたデータは、そのハーネスが`experiments/`の下に配置された状態で、`rig`の情報源として記録されます。
2. **内部の棚。** あるトピックの重要な主張が裏付けられた場合、それはreadoutsのプライベートな作業リポジトリに構築された知識ベースに追加されるか、既存の知識ベースに追加されます。**実験の完了の一部として、情報の整理が行われます**（ディレクター、2026年10月9日）。実験の結果がここにコミットされると、そのチャートとともに、同じセッションまたは次のセッションでそのreadouts-internalの更新が行われます。ベンチにエントリーが残るのは約1週間までです。定期的な小さな更新は、大きな更新よりも効果的です。実験のREADMEには、その結果の下に、その整理がどのように行われたかが1行で記録されます。「整理済み：readouts-internal `<kb>` ウェーブ `<n>`、`<date>`」、またはまだ整理されていない理由。
3. **公開の棚。** 知識ベースは、エクスポート許可リストに追加されると、公開リポジトリreadoutsに公開されます。

`rnd readouts`はここからすべてのreadouts知識ベースを検索するため、1つのインターフェースで両方のストレージにアクセスできます。まずベンチを検索し、次に棚を検索し、最後にギャップを調査します。

ここでの研究は、スタジオ自身の分野に限定されません。各エントリーは、知識そのものと、それがスタジオにとって何を意味するかという2つのことを別々に記録します（`relevance: act | watch | reference`）。`reference`という判定でもまったく問題ありません。

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
python -m rnd similar 2026-10-07-cuda-graphs --limit 3  # closest claims in other entries (read-only)
python -m rnd digest --since v1.1.24.0.14   # entries, claims and questions changed since a tag or date
python -m rnd sql "SELECT tier, count(*) FROM sources GROUP BY tier"
python -m rnd change "what changed"         # add a changelog fragment under changes/ (nano by default)
python -m rnd bump --note "release note"    # release PR: apply changes/ fragments, bump version + CHANGELOG
```

すべてのリスト表示コマンドは、エージェント向けに`--json`を受け取ります。`rnd.cmd`（Windows）と`rnd.sh`（POSIXシェル）は、薄いラッパーであるため、コマンドはどのディレクトリからでも実行できます。

他のプロジェクトからこのツールを使用するには、PyPIからインストールします。

```bash
pip install mcptoolshop-rnd
```

これにより、ライブラリではなく、`rnd`コマンドがインストールされます。エントリーは、このリポジトリに保存されます。コマンドは、次の順序でライブラリを検索します。`--library DIR`、次に`$RND_ROOT`、次に現在のディレクトリまたはそれより上位のディレクトリにある、`entries/`と`instruments/`を含む最も近いフォルダー。ライブラリの外では、`NO_LIBRARY`で停止します。`rnd readouts`のみが、ライブラリなしで動作します。

Pythonでは、`mcptoolshop_rnd`をインポートします。この名前は常に機能します。`rnd`は互換性のためのエイリアスとして保持されますが、関連性のないPyPIパッケージも`rnd`と呼ばれており、両方がインストールされている場合、エイリアスを置き換える可能性があります。`rnd`コマンドと`python -m mcptoolshop_rnd`は、どちらの場合でも引き続き機能します。

ライブラリは毎日変更されるため、バージョンには5つのセグメントがあります。`MAJOR.MINOR.PATCH.MICRO.NANO`。最初の3つのセグメントは、`rnd`ツールをバージョン管理します。MICROは、構造的なライブラリの変更を示し、NANOは通常の更新を示します。通常の更新では、変更ログのフラグメントが`rnd change`を介して`changes/`の下に追加されます。リリース時に、`rnd bump`はすべてのフラグメントを消費し、最も高いフラグメントレベルでバージョンを1つ進め、1つのCHANGELOGセクションを書き込みます。

終了コード：`0` OK · `1` 無効なライブラリファイル · `2` 使用方法エラーまたは見つからない · `3` 実行時のエラー（外部ツール、または予期しないエラー）。エラーは、コード、メッセージ、およびヒントを出力します。`--debug`は、トレースバックを追加します。

## レイアウト

| パス | 内容 | 編集者 |
|------|------|-----------|
| `entries/YYYY/*.md` | 研究エントリー：真実の情報源 | 人々とエージェント |
| `questions/*.md` | 未解決および解決済みの研究課題 | 人々とエージェント |
| `changes/*.md` | 未リリース変更ログフラグメント（`rnd change`） | 人々とエージェント（`rnd bump`が消費） |
| `experiments/<name>/` | ハーネス、固定された入力、`results.json`、および結果のレシート | 人々とエージェント |
| `experiments/<name>/collect.json` | 固定されたコミットでツールリポジトリから収集されたレコード（`rnd collect`） | 人々 |
| `instruments/*.md` | シートが使用できるスタジオツールとプロトコル（`kind: instrument`） | R&Dシートのみ（レビューされた差分） |
| `catalogs/<name>/source.json` | カタログの出所 | 人々 |
| `catalogs/<name>/catalog.json` | `rnd catalog sync`からの固定スナップショット | 生成されたもの。手動で編集することはできません。 |
| `catalogs/<name>/review.json` | スタジオへの適合性と、ファミリーおよびアイテムごとのメモ | 人々 |
| `datapacks/<name>/spec.json` | データパックに含まれるもの：含めるグロブ、ライセンス、ジェネレーター、ホスト | 人々 |
| `datapacks/<name>/datapack.json` | `rnd datapack build`からのマニフェスト：すべてのファイルのSHA-256、ライセンス、ピン | 生成されたもの。手動で編集することはできません。 |
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
- `[[entry-id]]`はエントリーをリンクし、`rnd show`はバックリンクを一覧表示します。

## 変更ログフラグメント

更新では、`mcptoolshop_rnd/__init__.py`または`CHANGELOG.md`を直接編集しないため、並行ブランチはバージョンラインで衝突することはありません。

```bash
python -m rnd change "Add study of XYZ"                # writes changes/YYYY-MM-DD-<hex>-<slug>.md (level: nano)
python -m rnd change "New tool feature" --level minor  # levels: nano | micro | patch | minor | major
python -m rnd bump --dry-run                           # preview version bump from changes/ fragments
python -m rnd bump                                     # release PR: bump once, update CHANGELOG.md, delete fragments
```

`changes/`の下にファイルがない場合、`rnd bump [nano|micro|…] [--note …]`は
git-diffの動作を維持します。`__init__.py`と`CHANGELOG.md`はいずれも一時ファイルを通じてステージングされ、`os.replace`で入れ替えられます。CHANGELOGの入れ替えが失敗した場合は、`__init__.py`をロールバックします。クラッシュが発生し、`__init__.py`が`CHANGELOG.md`よりも進んでいる場合、対応するレベルで再実行することで、更新が完了し、他のすべてのレベルは`BAD_CHANGELOG`で拒否されます。残っている問題は1つだけです。両方のファイルが入れ替えられた後、しかし、`changes/`の下にあるフラグメントが削除される前にクラッシュが発生した場合、それらはそのまま残され、再実行すると2回目の更新が行われるため、最初にそれらのフラグメントを手動で削除します。`rnd check`は、形式が正しくないフラグメントをエラーとして報告します。

## バインドされた数値

実験では、公開されている安全な要約数値を`experiments/<id>/results.json`に保存し、エントリ、概要、または実験ノート内の数値を、リテラル直後にバインドできます。

```markdown
The judge scored 84.2%<!-- rnd:experiments/e4b/results.json#accuracy:.1% --> on the held-out split.
```

- 生のMarkdown、`grep`、およびSQLiteインデックスは、プレーンなリテラル（`84.2%`）を保持します。
GitHubとStarlightは、目に見えるマーカーやリンクなしで`84.2%`をレンダリングします。
- `rnd sync [paths…]`は、Pythonのフォーマット仕様を使用して、`results.json`からバインドされたリテラルを書き換えます。`rnd sync --check`は、異なるリテラルがある場合、書き込みを行わずに終了コード`1`で終了します。
- `rnd check`は、同期されていないバインドされたリテラル、欠落しているファイル、または欠落しているキーをエラーとして扱い、`(via: …)`がリポジトリの実験を指定しているにもかかわらずバインドされていない数値を含む`[verified]`の主張に対して警告を出します。ただし、エントリ自身のタイトルやタグ内で直前の単語とペアになっているプレーンな整数（小数点、パーセント記号、桁区切り文字、末尾の単位がないもの）、または`RTX`や`GTX`に続く3〜4桁の整数、あるいは`CUDA`、`PTX`、`Gemma`、`Llama`、`Qwen`、`Claude`、`GPT`、`Phi`に続く1〜2桁の整数は無視されます。

## 主張IDとリンク

主張は、安定した決定的な`c-<hex>` IDと、IDによる古い主張への明示的な関係（`supersedes`、`contradicts`、`supports`）を持つことができます。

```bash
python -m rnd claims                               # list indexed claims (--state superseded, --json)
python -m rnd claims assign <entry>                # add deterministic c-<hex> ids to one entry's claims
python -m rnd similar <entry> [--limit 5]          # closest claims in other entries (read-only)
python -m rnd reconcile <entry>                    # mark older claims (superseded / disputed / supported-by)
```

`rnd similar <entry>`は、`<entry>`の各主張について他のエントリを対象に`claims_fts`上で読み取り専用のSQLite FTS5 BM25クエリを実行し（`--limit`の既定値は5）、`superseded`または`disputed`の一致項目にそれらを置き換えたり反論したりした主張を示して印を付け、正確な`(supersedes: id)`／`(contradicts: id)`／`(supports: id)`節と`rnd reconcile <entry>`コマンドを出力し、`rnd.db`やどのエントリにも決して書き込みません。
`rnd reconcile <entry>`は、ID（存在しない場合）、更新された状態、および逆の関係（`superseded-by`、`contradicted-by`、`supported-by`）のみを、自身のファイル内の古い主張の行に書き込みます。ただし、その文や他の行には一切触れません（反論された場合は、`[wrong]`の主張を`[wrong]`として残します）。
`rnd claims assign`と`rnd reconcile`は、いずれも、エントリに複数の実際の`## Claims`見出し（2つ以上）が含まれている場合、書き込みを行わずに拒否します（`MULTIPLE_CLAIMS_HEADINGS`）。
`rnd check`は、無効なターゲットID、一方通行のリンク（`rnd reconcile`を実行するか、節を削除して`superseded`または`disputed`の状態をリセットするように促します）、または閉じられていないコードフェンスがある場合にエラーを発生させ、`(superseded-by: …)`のリンクがない`[superseded]`の主張がある場合は警告を表示します。
`rnd search`と`rnd show`は、`superseded`と`disputed`の主張にマークを付け、それらを置き換えたり、反論したりした主張の名前を記録します。

## 変更点（ダイジェスト）

`rnd digest --since <git ref or YYYY-MM-DD> [--json]`は、以前のコミット（メモリ内のgitオブジェクトから解析され、ワーキングツリー、gitインデックス、`rnd.db`、または一時ファイルには触れません）にあるライブラリと、現在のツリーを比較します。

```bash
python -m rnd digest --since v1.1.24.0.14
python -m rnd digest --since 2026-11-19 --json
```

追加されたエントリ、追加された主張、削除された主張、主張の状態の変化（`old_state -> new_state`、それらを置き換えたものまたは矛盾したもの）、および開かれた質問、回答された質問（回答した主張のID付き）、保留中の質問とともに、その数を報告します。`YYYY-MM-DD`の日付は、現在のブランチ（`HEAD`）の最初の親ラインに沿って、コミッターの日付がその日以前である最新のコミットに解決されます。主張は両方に`id`がある場合は`id`で一致し、それ以外の場合は`(entry, exact text)`で一致するため、IDのない主張が言い換えられた場合は1件の主張の削除と1件の主張の追加として表示され、状態の変化としては決して表示されません。

## 未解決の質問

未解決の質問は、ステータスが`open`、`investigating`、`answered`、または`parked`である個別のMarkdownファイルとして、`questions/`の下に保存されます。

```bash
python -m rnd new-question "Does X hold on Y?" --field systems
python -m rnd questions --status open --json
```

質問の`status`が`answered`の場合、そのフロントマターの`answered_by`リストには、少なくとも1つの既存の主張IDが含まれている必要があります。`rnd check`は、既存の主張IDのない`answered`の質問をエラーとして扱います。質問は`rnd.db`にインデックスが付けられ、`rnd search`と`rnd show`によって返されます。

## ローカル検索ミスログ

`rnd search`が一致するものを見つけられない場合、1つのJSON行（`time`と`query`）を、ローカルの`.misses.jsonl`ファイルに、`rnd.db`の隣に追加します（`rnd.misses.jsonl`はリポジトリのルートにあり、gitによって無視されます。または、`<stem>.misses.jsonl`は`--db` / `RND_DB`の隣にあり、そのため、`--db foo.db`はその隣に`foo.misses.jsonl`を書き込み、`foo.db.misses.jsonl`には書き込みません）。
それ以外は何も記録されず、ネットワーク経由で送信されることもなく、`RND_NO_USAGE=1`はロギングをオフにし、ファイルを削除すると完全に削除されます。`rnd stats --usage`は、合計ミス数と最も頻繁にミスしたクエリを出力します。

## 計測ファイルとオプションの追加機能

- **計測ファイル（`instruments/*.md`）：** 変更された各計測ファイルが説明に明記されたレビュー済みの差分において、R&Dシートによってのみ編集され、外部コンテンツを要約するステップやコマンド（`rnd watch`、`rnd probe`、`rnd collect`、`rnd catalog sync`）によって編集されることは決してありません。
- **コア依存関係と追加機能：** `rnd`のコアは、Python標準ライブラリのみです。オプションの追加機能はすべて、オプトイングループに存在し、遅延ロードでインポートされます。必要な追加機能がないコマンドは、`MISSING_EXTRA`とインストールヒントで失敗します。

## データパック

クローンするには大きすぎる、またはかさばりすぎる処理済みのデータは、**データパック**として提供されます。バイトは、Hugging Faceのデータセットリポジトリ（公開されるまでは非公開）に保存され、ライブラリには小さなマニフェストのみが保存されます。整合性モデルは、[research-packs](https://github.com/mcp-tool-shop-org/research-packs)から取得されます。マニフェスト、各ファイルのSHA-256、1つのコマンドによる検証、およびリストが含まれます。

```bash
rnd datapack build natural-errors --source experiments/natural-errors  # reads datapacks/natural-errors/spec.json
rnd datapack list
hf download mcp-tool-shop/rnd-natural-errors --repo-type dataset --local-dir ne
rnd datapack verify natural-errors --copy ne/files                      # PASS when every byte matches
```

- **すべてのファイルには、仕様にライセンスが必要です。** モデルの出力には、そのモデルの利用条件が伴います（例：Llama 3.1の出力に対する「Built with Llama」）。`rnd datapack build`は、ファイルがカバーされていないデータパックを拒否します。
- **生成するすべてのモデルは、ピン留めされます**（Ollamaダイジェスト、HFリビジョン、またはAPIモデルID）、およびその役割。
- **`rnd check`は、すべてのマニフェストを検証し、手動で編集されたマニフェストで失敗します。**
- アップロードには、ファイルとともに`datapack.json`が含まれているため、誰でもこのリポジトリなしで検証できます：`pip install mcptoolshop-rnd`。

## 収集された実験記録

ツールリポジトリは、事前に登録された仕様と実行記録（interlockのレシート）をコミットします。これは、各リポジトリがアトラスマップをコミットする方法と同じです。ライブラリは、固定されたコミットでツールリポジトリから`rnd collect`によって作成された、数値の簡略化されたコピーのみを公開します。

```bash
rnd collect                 # list the experiments that collect records
rnd collect e4b             # read each source with git show, trim it, write experiments/e4b/results/
rnd collect e4b --check     # recompute every output; exit 1 if any differs from the committed file
```

- **`experiments/<name>/collect.json`** は、対象リポジトリ、読み込み元となる隣接クローン（`--clone` で上書き可能）、および各ソース（パス、コミット、バイト列の SHA-256、出力先、実験の `extract.py` 内のトリミング関数）を指定します。
- **固定されたソースは決して変更されません。** ハッシュ値が指定された値と一致しなくなったバイトは拒否されます。
- **すべてのレコードには、その由来（プロベナンス）が記録されます。** 具体的には、リポジトリ、ソースパス、およびトリミングされたバイトの SHA-256 です。
- **すべての出力は、書き込まれる前に安全性が確認されます。** マシンパス、ホームディレクトリ、または環境フィールドは保持されません。また、実験モジュールは、より厳格なセキュリティ対策を追加できます。拒否された場合は、何も書き込まれません。

## 試行前にツールをテストする

`rnd probe <url> …` は、各ソースの独自の API から、ツールまたはモデルに関する最初の質問に答えます。ウェブページの概要からではありません。

- **GitHub**（`gh api` を介して、そのためには GitHub CLI のログインを使用します）：ライセンス、アーカイブされているかどうか、最後のプッシュ、最新のリリース、および「テレメトリ」のコード検索。ヒットした場合、それは読むべき手がかりであり、決して証拠ではありません。ヒットがゼロの場合も、証拠にはなりません。
- **Hugging Face:** ライセンスタグ、または「その他」の場合は、カードのライセンス名とリンク。アクセス制限、最後の変更。
- **PyPI および npm:** ライセンス、最新バージョン、および公開日。
- **rnd 自体:** 正確な単語検索で名前を検索し、ライブラリがすでにそれを持っているかどうかを確認します。

アクセスできないソースは、理由とともに「不明」として報告されます。

## ソースの監視

`rnd watch` は、[docs/watchlist.json](docs/watchlist.json) 内のソースをチェックし、前回のチェック以降の変更点を報告します。

- NVIDIA の技術ブログ。
- CUDA ツールキットのバージョン。
- NVIDIA の新しい Hugging Face モデル。
- NVIDIA のスキルカタログ。
- スタジオで使用されているエンジンとツールのリリース（例：Ollama、OpenVINO、PyTorch、ComfyUI、Claude Code）。

```bash
python -m rnd watch                  # what's new; records what it saw
python -m rnd watch --no-save --json # look without recording
python -m rnd watch --only ollama    # one source
```

確認された内容は、リポジトリ外のステートファイル（`--state`、それ以外の場合は `$RND_WATCH_STATE`、それ以外の場合は `Path.home() / ".rnd" / "watch-state.json"`、`~/.rnd/watch-state.json`）に保存されます（ただし、`--no-save` が渡された場合は除く）。ソースの最初のチェックは、ベースラインとして機能します。現在の項目を記録し、新しい項目は何も報告しません。プレリリースがソースの最新バージョンとして報告されることは決してありません。最新バージョンより新しいプレリリースがある場合は、その横に並べて表示されます。GitHub リリースノートとコミットメッセージは JSON 出力に保存されるため、各ページを個別に取得する必要はありません。アクセスできないソースは「不明」として報告され、その状態は変更されないため、何もサイレントにスキップされることはありません。

このコマンドは、毎週行われる一連の作業のうち、決定的な部分を担います（Director、2026-10-13）。スカウトは、新しい項目を読み取り、候補となるツールを `rnd probe` でテストし、ライブラリを `rnd search --exact` でチェックし、短いランク付けされたレポートを作成します。レポートには、記録すべき項目、試すべき項目、およびスキップすべき項目が記載されます。プルリクエストでソースを追加し、その重要性を説明します。

## 他のスタジオツールとの関係

- **readouts** は、このベンチが検証済みの知見を送り込む先の「棚」です（上記参照）。
- **research-os** は、特定のトピックに関する、アクセス制限付きの固定された証拠パックを構築します。意思決定の根拠となるトピックは、エントリからリンクされた research-os パックに昇格できます。
- **repo-knowledge** は、スタジオ自身のリポジトリをインデックス化します。このライブラリは、それらの外部にある知識をカバーします。
- 何かを設計する際に収集された情報は、ここにも保存されるため、その情報を生成したセッションが終了した後も利用できます。

完全なツールのレジストリについては、`python -m rnd tools` を参照してください。また、ワークフローがスタジオのワークフロー標準にどのように適合するかについては、[docs/standards.md](docs/standards.md) を参照してください。

## セキュリティと信頼

- **書き込まれるデータ**（書き込み先ごと）：
  - **このリポジトリの内部**（ライブラリ：`--library`、なければ `$RND_ROOT`、なければ作業ディレクトリまたは
    その上位で `entries/` と `instruments/` を持つ最も近いフォルダー、なければパッケージが実行されている
    チェックアウト）：`rnd new`（`entries/` または `instruments/` の下に新しいファイルを1つ作成し、上書きは
    決してしません）、`rnd new-question`（`questions/`）、`rnd new-experiment`、
    `rnd runs record` と `rnd collect <name>`（`experiments/<name>/`）、
    `rnd claims assign`、`rnd reconcile` と `rnd sync`（既存の Markdown ファイル内の主張の行とバインドされた
    数値）、`rnd change`（`changes/`）、`rnd bump`
    （`mcptoolshop_rnd/__init__.py` と `CHANGELOG.md`。それぞれの隣の一時ファイルを経由して書き込み、
    使用した `changes/` のフラグメントを削除します）、
    `rnd catalog sync`（`catalogs/<name>/catalog.json`）、`rnd datapack build`
    （`datapacks/<name>/datapack.json`）、`rnd layout`（`docs/layout.json`）。
  - **インデックス：** `rnd.db`、または `--db` か `$RND_DB` で指定されたパス。構築中は、その隣に一時的な
    `.db.tmp` ファイルが置かれます。`rnd build` がこれを書き込み、
    インデックスを読み取るすべてのコマンド（`search`、`show`、`list`、`tools`、
    `stats`、`catalog`、`claims`、`questions`、`sql`、`runs`、`ledger`、`where`、
    `probe`）は、ソースファイルが変更されている場合、まずインデックスを再構築します。ミスログ
    `rnd.misses.jsonl` はその隣に置かれます（下記参照）。
  - **ホームフォルダー：** `rnd watch` は、確認済み項目のファイルを `--state`、なければ
    `$RND_WATCH_STATE`、なければ `~/.rnd/watch-state.json`（コード上は
    `Path.home() / ".rnd" / "watch-state.json"`）に書き込み、このファイルは実行をまたいで残ります。書き込みは隣の `.tmp` ファイルを経由します。
    `--no-save` を指定すると書き込みを行いません。
  - **このリポジトリの外部にある生データストア：** `rnd raw ingest`、`rnd raw private`、
    `rnd raw relicense` は、公開ストア（`--public`、なければ `$RND_DATA`、
    なければ `../rnd-data`）と非公開ストア（`--private`、なければ `$RND_DATA_PRIVATE`、なければライブラリの隣の
    `../rnd-data-private`。`rnd raw` をライブラリの外で実行した場合は、公開ストアの隣の
    `rnd-data-private`）に書き込みます。`rnd raw ingest` はさらに、
    256 KB を超えるすべてのファイルを blob ストアに入れます。場所は、
    `$RND_DATA_STORE_D`、または公開ストアの `store.local.json` の `"d"` エントリで指定された
    フォルダーの `blobs/` の下です（既定値はありません。指定がなければ ingest は拒否します）。blob は隣の `.tmp` ファイルを経由して書き込まれ、読み取り専用に設定されます。`--link` を指定すると、新しい blob は
    ソースファイルへのハードリンクになるため、**そのソースファイルも読み取り専用になります**（すでに
    ストアにある blob はそのまま残り、そのソースも変更されません）。`--link` を指定しなければ、
    ソースは変更されません。`rnd raw ingest --update` は、新しいファイルを書き込む前に、2つのストアにある
    その実行の以前の小さなファイルを削除します。`--dry-run` は何も書き込みません。
- **読み取るだけで、決して書き込まないもの：** `rnd readouts`（SQLite の読み取り専用モード）、`rnd collect` のソース
  クローン（`git show`）、`rnd raw verify`、`rnd datapack verify --copy`、
  `rnd runs record --from`、`rnd abmine`、そして `rnd similar` と `rnd digest`。
  後の2つはメモリ内で動作し、どこにも何も書き込みません。一時ファイルも作らず、
  作業ツリー、git インデックス、`rnd.db` も変更しません。
- **実行するコード：** `rnd collect <name>` は、`--check` の有無にかかわらず、ライブラリにある
  `experiments/<name>/extract.py`（またはそのフォルダーの `collect.json` が
  指定するモジュール）を読み込んで実行します（`mcptoolshop_rnd/collect.py:142-149`）。Python は
  そのモジュールのバイトコードを `experiments/<name>/__pycache__/` にキャッシュすることがあります。`rnd` は
  自身が書き込む範囲を `experiments/<name>/` に限定しますが、その
  モジュール自体のコードが行うことは制限しません。信頼できるライブラリでのみ実行してください。
- **`rnd` コマンドの外部：** このパッケージには
  `mcptoolshop_rnd.localbuilders`（local-builders 実験のハーネス）も
  含まれています。これを実行する `rnd` コマンドはありません。直接実行した場合（たとえば
  `python -m mcptoolshop_rnd.localbuilders.runner`）、このハーネスは、想定されたレンタルマシン上で
  一部を root として動作し、呼び出し元が渡すパス（作業、ホーム、履歴、仮想環境、レシート、ログ、
  レポート、シークレットディレクトリ、封じ込めプローブの各パス）の下でファイルを作成、削除し、
  その所有者と権限を変更します。また、スコアラーはオペレーティング
  システムの一時フォルダーに一時フォルダーを作成し、終了時に削除します。
- **触れないデータ：** これら以外の場所では、どの `rnd` コマンドもファイルの書き込み、削除、変更を
  行いません。認証情報を保存することも、読み取ることもありません。
- **ネットワーク：** なし。例外は `rnd catalog sync`、`rnd probe`、`rnd watch` で、
  これらは実行したときに、公開メタデータを読み取るか、利用者自身の `gh` CLI の
  ログインを通じて GitHub API を呼び出します。
- **権限：** 通常のファイルアクセスのみ。昇格した権限を必要とする `rnd` コマンドはなく、バックグラウンドサービスもありません。
- **ローカルのみの使用ログ：** 何も収集されず、どこにも送信されません。`rnd search` で
  一致するものがなかった場合、`rnd.db` の隣の `rnd.misses.jsonl` に1行（UTC 時刻とクエリ）を
  追記します（リポジトリでは git の無視対象。`--db foo.db` の場合はその隣の `foo.misses.jsonl` で、
  `foo.db.misses.jsonl` ではありません。`$RND_DB` の場合も同様です）。
  `RND_NO_USAGE=1` を設定すると無効になり、`.misses.jsonl` ファイルはいつでも削除して
  消去できます。それ以外の使用データは記録されません。
- **公開リポジトリの衛生管理：** プッシュのたびに、その前にツリーをスキャンして、
  ホームディレクトリのパスと運用者の身元情報がないか確認します。

[SECURITY.md](SECURITY.md) に記載されているように、脆弱性を報告してください。

## テスト

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## ステータスとライセンス

スタジオによって維持され、毎日使用されています。コード: [MIT](LICENSE)。エントリ: CC BY
4.0。`catalogs/nvidia-skills/catalog.json` の NVIDIA スキルミラーは、
そのプロジェクトのライセンス (コードは Apache-2.0、スキルテキストは CC-BY-4.0) の下で、[NVIDIA/skills](https://github.com/NVIDIA/skills) からスキル名と説明を再現します。

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
