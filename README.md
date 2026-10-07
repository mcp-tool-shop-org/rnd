# Research and Development

The studio's research library. Findings from any field go in as short Markdown
entries with tagged sources and claims. External catalogues are mirrored and
rated. A registry lists the studio instruments that research can call on. One
command searches all of it.

Research here is not limited to the studio's own fields. Each entry records two
separate things: what the knowledge is, and what it means for the studio
(`relevance: act | watch | reference`).

## Use it

Requires Python 3.10+ (standard library only). Run from the repo root:

```bash
python -m rnd search cuda graphs          # full-text over entries + catalogues
python -m rnd show 2026-10-07-cuda-graphs # one entry, with backlinks
python -m rnd list --relevance act        # what needs doing
python -m rnd tools                       # instruments this seat can use
python -m rnd catalog lanes               # NVIDIA skills by lane, with studio fit
python -m rnd catalog list --fit adjacent # skills worth using when the need arises
python -m rnd new "Paper title" --kind paper --field audio --tag pitch
python -m rnd check                       # validate every file (exit 1 on errors)
python -m rnd sql "SELECT tier, count(*) FROM sources GROUP BY tier"
```

Every listing command takes `--json` for agents. `rnd.cmd` (Windows) and
`rnd.sh` (POSIX shells) are thin wrappers so the command works from any directory.

## Layout

| Path | What | Who edits |
|------|------|-----------|
| `entries/YYYY/*.md` | Research entries: the source of truth | people and agents |
| `instruments/*.md` | Studio tools/protocols the seat can call (`kind: instrument`) | people and agents |
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

- **research-os** builds a gated, frozen evidence pack for one topic. This
  library is the broad intake. A topic a decision depends on can graduate into a
  research-os pack, with the pack linked from the entry.
- **repo-knowledge** (`rk`) indexes the studio's own repos; this library covers
  knowledge from outside them.
- Findings gathered while designing something belong here too, so they outlive
  the design session that produced them.

See `python -m rnd tools` for the full instrument registry and
[docs/standards.md](docs/standards.md) for the workflow-standards scoring.

## Tests

```bash
python -m unittest discover -s tests -t .
```

## Licence

Code: MIT. Entries: CC BY 4.0. The NVIDIA skills mirror in
`catalogs/nvidia-skills/catalog.json` reproduces skill names and descriptions
from [NVIDIA/skills](https://github.com/NVIDIA/skills) under that project's
licences (Apache-2.0 for code, CC-BY-4.0 for skill text).
