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
only `rnd readouts` works without one. The package imports as `rnd`, as does an
unrelated PyPI package called `rnd`, so don't install both in one environment.

The library changes daily, so versions have five segments,
`MAJOR.MINOR.PATCH.MICRO.NANO`. The first three version the `rnd` tool; MICRO marks a
structural library change and NANO an ordinary update. `rnd bump` raises the
last segment by default and writes a CHANGELOG section from the files changed
since the last tag, so each update gets its own small tagged version.

Exit codes: `0` ok · `1` invalid library files · `2` usage error or not found ·
`3` runtime failure (an external tool, or an unexpected error). Errors print a
code, a message and a hint; `--debug` adds the traceback.

## Layout

| Path | What | Who edits |
|------|------|-----------|
| `entries/YYYY/*.md` | Research entries: the source of truth | people and agents |
| `experiments/<name>/` | Harnesses, pinned inputs and result receipts for rig measurements | people and agents |
| `instruments/*.md` | Studio tools and protocols the seat can call (`kind: instrument`) | people and agents |
| `catalogs/<name>/source.json` | Where a catalogue comes from | people |
| `catalogs/<name>/catalog.json` | Pinned snapshot from `rnd catalog sync` | generated; never hand-edit |
| `catalogs/<name>/review.json` | Studio fit and notes per family and item | people |
| `rnd/` | The CLI | code |
| `rnd.db` | SQLite FTS5 index, rebuilt automatically when files change | generated; not in git |

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
- [verified] A checked statement. (via: what checked it, date)
## Sources
- [primary] https://… — publisher
```

- **Source tiers:** `primary` (vendor docs, papers, repos), `secondary`
  (reputable write-ups), `aggregator` (summary sites, AI search output),
  `user` (supplied by a person: slides, notes), `rig` (measured on our machines).
- **Claim confidence:** `unverified`, `verified`, `disputed`, `wrong`. A
  `verified` or `wrong` claim must say what checked it with `(via: …)`.
- `[[entry-id]]` links entries; `rnd show` lists backlinks.

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

- **Data touched:** files inside this repo (`entries/`, `instruments/`,
  `catalogs/`, `experiments/`) and the index `rnd.db`, which it rebuilds. `rnd
  readouts` opens the readouts knowledge bases **read-only**. `rnd sql` runs
  against a read-only connection.
- **Data not touched:** nothing outside the repo and the readouts checkout. It
  stores no credentials and reads none.
- **Network:** none, except `rnd catalog sync`, which calls the GitHub API
  through your own `gh` CLI login when you run it.
- **Permissions:** ordinary file access. No elevated rights, no background service.
- **No telemetry.** Nothing is collected or sent.
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
