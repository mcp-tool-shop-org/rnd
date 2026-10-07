---
title: Command reference
description: Every rnd command, flag, exit code and error shape.
sidebar:
  order: 4
---

```
python -m rnd [--db PATH] [--debug] [--version] <command> [options]
```

| global flag | effect |
|---|---|
| `--db PATH` | index path. Default: `rnd.db` in the repo, or `$RND_DB` |
| `--debug` | print the full traceback on an unexpected error |
| `--version` | print the version and exit |

Listing commands take `--json` for machine-readable output.

## Reading

### `search <words…>`

Full-text search over entries and catalogue items (FTS5, Porter stemming).

| option | effect |
|---|---|
| `--limit N` | results (default 10) |
| `--kind KIND` | entries of one kind |
| `--field FIELD` | entries in one research field |
| `--entries-only` / `--catalog-only` | search one side |
| `--raw` | pass the query to FTS5 unquoted (`AND`, `OR`, `NEAR`, `prefix*`) |

### `show <id>`

One entry with its sources, claims and backlinks. `show <catalog>:<item>` shows a
catalogue item instead. An unknown id suggests near matches.

### `list`

Entries, newest first. Filters: `--kind`, `--relevance act|watch|reference`,
`--status active|draft|superseded`, `--field`, `--tag`.

### `tools`

The instrument registry: each studio tool's status, how to invoke it, when to use
it and where it lives. `--status shipped|planned|retired` filters.

### `stats`

Counts by kind, relevance, field, source tier and claim confidence, plus each
catalogue's pinned commit and sync time.

### `readouts [words…]`

Read-only search across the readouts knowledge bases, through each one's own
full-text table, with prefix matching (`listener` also finds `listeners`).

| option | effect |
|---|---|
| `--any` | match any word instead of all of them |
| `--kb NAME` | one knowledge base, e.g. `vocology-knowledge` |
| `--limit N` | results per knowledge base (default 5) |
| `--list` | list the knowledge bases |
| `--root PATH` | readouts checkout (overrides `$RND_READOUTS`) |

### `sql "<query>"`

A read-only SQL query against the index. Tables: `entries`, `entry_fields`,
`entry_tags`, `sources`, `claims`, `links`, `catalogs`, `catalog_items`, `meta`,
plus the FTS tables `entries_fts` and `catalog_fts`.

```bash
python -m rnd sql "SELECT confidence, count(*) FROM claims GROUP BY confidence"
python -m rnd sql "SELECT entry_id, text FROM claims WHERE confidence = 'disputed'"
```

## Writing

### `new "<title>"`

Scaffold `entries/<year>/<date>-<slug>.md` from the template and print its path.
Options: `--kind` (default `finding`), `--relevance` (default `reference`),
`--field` and `--tag` (repeatable), `--id`, `--date`. It refuses to overwrite an
existing file.

### `check`

Validate every entry, instrument and catalogue file without touching the index.
Exits 1 on any error. See [Filing research](../filing-research/) for the rules.

### `build`

Rebuild `rnd.db` from `entries/`, `instruments/` and `catalogs/`. If any file has
an error, the build halts and the previous index is kept. Searches rebuild
automatically when files change, so you rarely need this.

### `bump [level]`

Raise the version and add a CHANGELOG section. Versions have five segments,
`MAJOR.MINOR.PATCH.MICRO.NANO`:

| level | for |
|---|---|
| `major`, `minor`, `patch` | the `rnd` tool itself (semver meaning) |
| `micro` | a structural library change: a new experiment, catalogue or instrument family |
| `nano` (default) | an ordinary library update: entries filed or revised, results added |

A bump resets the segments after the one it raises (`1.0.0.0.9` → `micro` →
`1.0.0.1.0`). The CHANGELOG section lists the entries, instruments, experiments and
catalogues changed since the last `v*` tag, including uncommitted and untracked
files, plus any `--note` lines. `--dry-run` prints it without writing. The command
prints the commit, tag and push to run next.

```bash
python -m rnd bump --note "Kev measured against hosted Jev"
python -m rnd bump micro --dry-run
```

### `catalog list|lanes|families|sync [name]`

Work with a mirrored catalogue (default `nvidia-skills`).

| action | effect |
|---|---|
| `list` | items, filterable by `--fit direct\|adjacent\|general`, `--family`, `--lane` |
| `lanes` | items grouped by upstream lane, with studio fit |
| `families` | items grouped by family |
| `sync` | re-pin the snapshot from upstream through your `gh` CLI login (writes `catalog.json`) |

`catalog.json` is generated. Edit `review.json` to change fit or notes.

## Exit codes

| code | meaning |
|---|---|
| `0` | ok |
| `1` | invalid library files (`check`, `build`) |
| `2` | usage error, or the thing asked for was not found |
| `3` | runtime failure: an external tool failed, or an unexpected error |

## Error shape

Errors go to stderr as a stable code, a message and a hint:

```
error: NOT_FOUND: no entry 'cuda-graph'
  hint: did you mean: 2026-10-07-cuda-graphs
```

Codes include `NOT_FOUND`, `EXISTS`, `BAD_ID`, `INDEX_INVALID`, `SQL_ERROR`,
`READOUTS_MISSING`, `READOUTS_INDEX_INVALID`, `BAD_VERSION`, `BAD_LEVEL`, `BAD_CHANGELOG`,
`GIT_FAILED`, `INTERNAL` and `INTERRUPTED`, plus the catalogue sync codes.
