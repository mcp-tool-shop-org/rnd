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

The studio's research bench. Findings from any field come in fast as short
Markdown entries, with every source tagged and every claim marked as checked or
not. Experiments sit next to the entries they test. External catalogues are
mirrored and rated, and a registry lists the studio tools research can call on.
One command searches all of it.

## Where it sits: the bench before readouts

Two stores hold the studio's knowledge, and they do different jobs.

| | Research and Development (this repo) | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| Role | the bench: intake, experiments, open questions | the shelf: verified knowledge bases |
| Pace | an entry in minutes, claims start `unverified` | built and checked by study swarms |
| Shape | Markdown entries, one topic each | one SQLite knowledge base per domain |
| How messy | messy on purpose: disputed claims, dead ends and interim results stay visible | not messy at all: every row is sourced and verified |

Knowledge moves one way:

1. **Bench.** A finding lands here as an entry. Its claims start `[unverified]`,
   and are marked `[verified]` only with a note of what checked them.
   Measurements made on our own machines go in as `rig` sources, with their
   harness under `experiments/`.
2. **Internal shelf.** Once a topic's load-bearing claims hold up, it is built
   into a knowledge base in readouts' private working repo, or added to one.
   **Promotion is part of closing an experiment** (the Director, 2026-10-09). When
   an experiment's result is committed here, its readouts-internal update follows
   in the same session or the next one, with its charts. Nothing sits on the bench
   for more than about a week. Regular small updates beat one big one. An
   experiment's README records its promotion as a line under its result:
   "Promoted: readouts-internal `<kb>` wave `<n>`, `<date>`", or why not yet.
3. **Public shelf.** A knowledge base is published to the public readouts repo
   when it is added to the export allow-list.

`rnd readouts` searches every readouts knowledge base from here, so one seat
reaches both stores. Search the bench first, the shelf second, then research the gap.

Research here is not limited to the studio's own fields. Each entry records two
things separately: what the knowledge is, and what it means for the studio
(`relevance: act | watch | reference`). `reference` is a fine verdict.

## Use it

Requires Python 3.10 or later and nothing else (standard library only). Runs on
Windows, macOS and Linux. From the repo root:

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

Every listing command takes `--json` for agents. `rnd.cmd` (Windows) and
`rnd.sh` (POSIX shells) are thin wrappers, so the command works from any directory.

To use the tool from other projects, install it from PyPI:

```bash
pip install mcptoolshop-rnd
```

That installs the `rnd` command, not the library: the entries live in this
repository. The command finds a library in this order: `--library DIR`, then
`$RND_ROOT`, then the nearest folder at or above the current one that holds
`entries/` and `instruments/`. Outside a library it stops with `NO_LIBRARY`;
only `rnd readouts` works without one.

In Python, import `mcptoolshop_rnd`: that name always works. `rnd` is kept as a
compatibility alias, but an unrelated PyPI package is also called `rnd`, and if
both are installed it can replace the alias. The `rnd` command and
`python -m mcptoolshop_rnd` keep working either way.

The library changes daily, so versions have five segments,
`MAJOR.MINOR.PATCH.MICRO.NANO`. The first three version the `rnd` tool; MICRO marks a
structural library change and NANO an ordinary update. Ordinary updates add a
changelog fragment under `changes/` via `rnd change`; at release time, `rnd bump`
consumes all fragments, moves the version once by the highest fragment level,
and writes one CHANGELOG section.

Exit codes: `0` ok · `1` invalid library files · `2` usage error or not found ·
`3` runtime failure (an external tool, or an unexpected error). Errors print a
code, a message and a hint; `--debug` adds the traceback.

## Layout

| Path | What | Who edits |
|------|------|-----------|
| `entries/YYYY/*.md` | Research entries: the source of truth | people and agents |
| `questions/*.md` | Open and answered research questions | people and agents |
| `changes/*.md` | Unreleased changelog fragments (`rnd change`) | people and agents (`rnd bump` consumes) |
| `experiments/<name>/` | Harnesses, pinned inputs, `results.json`, and result receipts | people and agents |
| `experiments/<name>/collect.json` | Records collected from a tool repository at pinned commits (`rnd collect`) | people |
| `instruments/*.md` | Studio tools and protocols the seat can call (`kind: instrument`) | R&D seat only (reviewed diff) |
| `catalogs/<name>/source.json` | Where a catalogue comes from | people |
| `catalogs/<name>/catalog.json` | Pinned snapshot from `rnd catalog sync` | generated; never hand-edit |
| `catalogs/<name>/review.json` | Studio fit and notes per family and item | people |
| `datapacks/<name>/spec.json` | What a data pack holds: include globs, licences, generators, host | people |
| `datapacks/<name>/datapack.json` | Manifest from `rnd datapack build`: every file's SHA-256, licences, pins | generated; never hand-edit |
| `datapacks/<name>/hosted.json` | Where the upload landed (repo revision) | after an upload |
| `mcptoolshop_rnd/` | The CLI | code |
| `rnd/` | Compatibility alias for `mcptoolshop_rnd` | code |
| `rnd.db` | SQLite FTS5 index, rebuilt automatically when files change | generated; not in git |
| `rnd.misses.jsonl` | Local zero-hit search log beside `rnd.db` (`RND_NO_USAGE=1` disables) | generated; not in git |

## Entry format

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

- **Source tiers:** `primary` (vendor docs, papers, repos), `secondary`
  (reputable write-ups), `aggregator` (summary sites, AI search output),
  `user` (supplied by a person: slides, notes), `rig` (measured on our machines).
- **Claim confidence:** `unverified`, `verified`, `disputed`, `wrong`,
  `superseded`. A `verified` or `wrong` claim must say what checked it with
  `(via: …)`.
- `[[entry-id]]` links entries; `rnd show` lists backlinks.

## Changelog fragments

Updates do not edit `mcptoolshop_rnd/__init__.py` or `CHANGELOG.md` directly, so
parallel branches never collide on the version line:

```bash
python -m rnd change "Add study of XYZ"                # writes changes/YYYY-MM-DD-<hex>-<slug>.md (level: nano)
python -m rnd change "New tool feature" --level minor  # levels: nano | micro | patch | minor | major
python -m rnd bump --dry-run                           # preview version bump from changes/ fragments
python -m rnd bump                                     # release PR: bump once, update CHANGELOG.md, delete fragments
```

With no files under `changes/`, `rnd bump [nano|micro|…] [--note …]` keeps its
git-diff behaviour. Both `__init__.py` and `CHANGELOG.md` are staged through
temp files and swapped with `os.replace`, rolling back `__init__.py` if the
CHANGELOG swap fails and completing or refusing (`BAD_CHANGELOG`) an
interrupted bump on re-run without bumping twice. `rnd check` reports any
malformed fragment as an error.

## Bound numbers

An experiment can keep public-safe summary numbers in
`experiments/<id>/results.json` and bind numbers in entries, briefs or
experiment notes directly after the literal:

```markdown
The judge scored 84.2%<!-- rnd:experiments/e4b/results.json#accuracy:.1% --> on the held-out split.
```

- Raw Markdown, `grep` and the SQLite index keep the plain literal (`84.2%`);
  GitHub and Starlight render `84.2%` with no visible marker or link.
- `rnd sync [paths…]` rewrites bound literals from `results.json` using the
  Python format spec; `rnd sync --check` exits `1` without writing if any
  literal differs.
- `rnd check` treats any out-of-sync bound literal, missing file or missing key
  as an error, and warns on `[verified]` claims whose `(via: …)` names a repo
  experiment while still holding unbound numbers—ignoring plain integers (with
  no decimal point, percent sign, thousands separator or trailing unit) that
  pair with the preceding word in the entry's own title or tags or follow
  `RTX` or `GTX` (3–4 digits) or `CUDA`, `PTX`, `Gemma`, `Llama`, `Qwen`,
  `Claude`, `GPT` or `Phi` (1–2 digits).

## Claim ids and links

Claims can carry stable deterministic `c-<hex>` ids and explicit relations
(`supersedes`, `contradicts`, `supports`) to older claims by id:

```bash
python -m rnd claims                               # list indexed claims (--state superseded, --json)
python -m rnd claims assign <entry>                # add deterministic c-<hex> ids to one entry's claims
python -m rnd similar <entry> [--limit 5]          # closest older claims in other entries (read-only)
python -m rnd reconcile <entry>                    # mark older claims (superseded / disputed / supported-by)
```

`rnd similar <entry>` runs a read-only SQLite FTS5 BM25 query over `claims_fts`
for each claim of `<entry>` against other entries (`--limit` defaults to 5),
flags `superseded` or `disputed` hits with what replaced or contradicted them,
prints the exact `(supersedes: id)` / `(contradicts: id)` / `(supports: id)`
clauses and `rnd reconcile <entry>` command, and never writes `rnd.db` or any
entry. `rnd reconcile <entry>` writes only the id (if missing), updated state and
inverse relation (`superseded-by`, `contradicted-by`, `supported-by`) on the
older claim's line in its own file without touching its sentence or any other
line (leaving a `[wrong]` claim `[wrong]` when contradicted). Both
`rnd claims assign` and `rnd reconcile` refuse (`MULTIPLE_CLAIMS_HEADINGS`)
without writing if an entry holds more than one real `## Claims` heading.
`rnd check` errors on broken target ids, one-sided links (hinting to run
`rnd reconcile`, or remove the clause and reset a `superseded` or `disputed`
state) or an unclosed code fence,
and warns on a `[superseded]` claim with no `(superseded-by: …)` link.
`rnd search` and `rnd show` mark `superseded` and `disputed` claims and name the
claim that replaced or contradicted them.

## What changed (digest)

`rnd digest --since <git ref or YYYY-MM-DD> [--json]` compares the library at an
earlier commit (read from git objects into a temporary directory without touching
the working tree, index or `rnd.db`) against the current tree:

```bash
python -m rnd digest --since v1.1.24.0.14
python -m rnd digest --since 2026-11-19 --json
```

It reports entries added, claims added, claim state changes (`old_state -> new_state`
with what replaced or contradicted them), and questions opened, answered (with
answering claim ids) and parked, along with counts. Dates resolve to the last
commit on the current branch at or before the end of that day; claims match by
`id` when both sides have one, otherwise by `(entry, exact text)` so a reworded
claim without an id appears as added rather than a state change.

## Open questions

Open questions live as individual Markdown files under `questions/` with status
`open`, `investigating`, `answered` or `parked`:

```bash
python -m rnd new-question "Does X hold on Y?" --field systems
python -m rnd questions --status open --json
```

When a question's `status` is `answered`, its frontmatter `answered_by` list
must name at least one existing claim id; `rnd check` treats an `answered`
question without an existing claim id as an error. Questions are indexed in
`rnd.db` and returned by `rnd search` and `rnd show`.

## Local search-miss log

When `rnd search` returns no matches, it appends one JSON line (`time` and
`query`) to a local `.misses.jsonl` file beside `rnd.db` (`rnd.misses.jsonl` in
the repo root, git-ignored; or `<stem>.misses.jsonl` beside `--db` / `RND_DB`,
so `--db foo.db` writes `foo.misses.jsonl` beside it, not `foo.db.misses.jsonl`).
Nothing else is recorded, nothing is ever sent over the network, `RND_NO_USAGE=1`
switches logging off, and deleting the file removes it completely.
`rnd stats --usage` prints the total miss count and the most frequent missed
queries.

## Instrument files and optional extras

- **Instrument files (`instruments/*.md`):** edited only by the R&D seat in a
  reviewed diff whose description lists each instrument file changed, never by a
  step or command that summarises outside content (`rnd watch`, `rnd probe`,
  `rnd collect`, `rnd catalog sync`).
- **Core dependencies and extras:** `rnd`'s core stays Python standard library
  only. Any optional extra lives in an opt-in group and is imported lazily; a
  command that needs a missing extra fails with `MISSING_EXTRA` and an install
  hint.

## Data packs

Processed data too big or too bulky for the clone is offered as a **data pack**: the bytes live
on a Hugging Face dataset repo (private until published), and the library keeps only a small
manifest. The integrity model comes from
[research-packs](https://github.com/mcp-tool-shop-org/research-packs): a manifest, a SHA-256 for
every file, a one-command verify, and a listing.

```bash
rnd datapack build natural-errors --source experiments/natural-errors  # reads datapacks/natural-errors/spec.json
rnd datapack list
hf download mcp-tool-shop/rnd-natural-errors --repo-type dataset --local-dir ne
rnd datapack verify natural-errors --copy ne/files                      # PASS when every byte matches
```

- **Every file needs a licence** in the spec. Model outputs carry their model's terms (for
  example "Built with Llama" for Llama 3.1 outputs). `rnd datapack build` refuses a pack that
  leaves a file uncovered.
- **Every generating model is pinned** (Ollama digest, HF revision or API model id), with its role.
- **`rnd check` validates every manifest** and fails on one edited by hand.
- The upload carries `datapack.json` beside the files, so anyone can verify without this repo:
  `pip install mcptoolshop-rnd`.

## Collected experiment records

A tool repository commits its own pre-registered specs and run records (interlock's receipts),
the way every repository commits its Atlas map. The library publishes only a trimmed copy of the
numbers, made by `rnd collect` from the tool repository at pinned commits:

```bash
rnd collect                 # list the experiments that collect records
rnd collect e4b             # read each source with git show, trim it, write experiments/e4b/results/
rnd collect e4b --check     # recompute every output; exit 1 if any differs from the committed file
```

- **`experiments/<name>/collect.json`** names the repository, the sibling clone it's read from
  (`--clone` overrides), and each source: its path, the commit, the SHA-256 of its bytes, the
  output and the trim function in the experiment's `extract.py`.
- **A pinned source never changes.** Bytes that no longer hash to the pin are refused.
- **Every record carries provenance:** the repository, the source path and the SHA-256 of the
  bytes trimmed.
- **Every output is public-safe before it is written.** No machine path, home directory or
  environment field survives, and an experiment's module can add a stricter guard. Nothing is
  written on any refusal.

## Probing a tool before a trial

`rnd probe <url> …` answers the first questions about a tool or model from each source's own API,
not from a summary of a web page:

- **GitHub** (through `gh api`, so it uses your GitHub CLI login): the licence, whether it's archived, the
  last push, the latest release, and a code search for "telemetry". A hit is a lead to read, never proof;
  zero hits isn't proof either.
- **Hugging Face:** the licence tag, or for "other" the card's licence name and link; gating; the last change.
- **PyPI and npm:** the licence, the latest version and when it was published.
- **rnd itself:** an exact-word search for the name, so you know whether the library already holds it.

A source that can't be reached is reported as unknown, with the reason.

## Watching sources

`rnd watch` checks the sources in [docs/watchlist.json](docs/watchlist.json) and reports what's new since
the last check:

- NVIDIA's technical blog;
- the CUDA toolkit version;
- NVIDIA's new Hugging Face models;
- the NVIDIA skills catalogue;
- the releases of the engines and tools the studio runs, such as Ollama, OpenVINO, PyTorch, ComfyUI and Claude Code.

```bash
python -m rnd watch                  # what's new; records what it saw
python -m rnd watch --no-save --json # look without recording
python -m rnd watch --only ollama    # one source
```

What it saw is kept in a state file outside the repository (`$RND_WATCH_STATE`, else `~/.rnd/watch-state.json`).
A source's first check is a baseline: it records the current items and reports none as new. A pre-release is never reported as a source's latest version; a newer one is shown beside it. GitHub release notes and commit messages are kept in the JSON output, so a reader doesn't have to fetch each page. A source that
can't be reached is reported as unknown, and its state is left alone so nothing is skipped silently.

The command is the deterministic half of a weekly ritual (Director, 2026-10-13). A scout reads the new items,
probes any candidate tool with `rnd probe`, checks the library with `rnd search --exact`, and writes a short
ranked report: what to file, what to try, and what to skip. Add a source by pull request, and say why it
matters.

## Relation to other studio tools

- **readouts** is the verified shelf this bench feeds (see above).
- **research-os** builds a gated, frozen evidence pack for one topic. A topic a
  decision depends on can graduate into a research-os pack, linked from the entry.
- **repo-knowledge** indexes the studio's own repos; this library covers
  knowledge from outside them.
- Findings gathered while designing something belong here too, so they outlive
  the session that produced them.

See `python -m rnd tools` for the full instrument registry, and
[docs/standards.md](docs/standards.md) for how the workflow scores against the
studio's workflow standards.

## Security and trust

- **Data touched:** files inside this repo (`entries/`, `questions/`, `changes/`,
  `instruments/`, `catalogs/`, `experiments/`), the index `rnd.db` and its
  sibling local miss log `rnd.misses.jsonl`. `rnd readouts` opens the readouts
  knowledge bases **read-only**. `rnd sql` runs against a read-only connection,
  and `rnd similar` / `rnd digest` are read-only and never modify the working
  tree, index or `rnd.db`.
- **Data not touched:** nothing outside the repo and the readouts checkout. It
  stores no credentials and reads none.
- **Network:** none, except `rnd catalog sync`, `rnd probe` and `rnd watch`,
  which read public metadata or call the GitHub API through your own `gh` CLI
  login when you run them.
- **Permissions:** ordinary file access. No elevated rights, no background service.
- **Local-only usage log:** nothing is collected or sent anywhere. When `rnd search`
  returns no matches, it appends one line (UTC time and query) to `rnd.misses.jsonl`
  beside `rnd.db` (git-ignored in the repo; with `--db foo.db`, `foo.misses.jsonl`
  beside it, not `foo.db.misses.jsonl`, and likewise for `$RND_DB`). Set
  `RND_NO_USAGE=1` to turn it off, and delete the `.misses.jsonl` file at any
  time to clear it. No other usage data is recorded.
- **Public repo hygiene:** before every push, the tree is scanned for
  home-directory paths and operator identity.

Report vulnerabilities as described in [SECURITY.md](SECURITY.md).

## Tests

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## Status and licence

Maintained by the studio and in daily use. Code: [MIT](LICENSE). Entries: CC BY
4.0. The NVIDIA skills mirror in `catalogs/nvidia-skills/catalog.json`
reproduces skill names and descriptions from
[NVIDIA/skills](https://github.com/NVIDIA/skills) under that project's licences
(Apache-2.0 for code, CC-BY-4.0 for skill text).

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
