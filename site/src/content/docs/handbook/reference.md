---
title: Command reference
description: Every rnd command, flag, exit code and error shape.
sidebar:
  order: 4
---

```
python -m rnd [--library DIR] [--db PATH] [--debug] [--version] <command> [options]
```

| global flag | effect |
|---|---|
| `--library DIR` | the library checkout. Default: `$RND_ROOT`, else the nearest folder at or above the current one holding `entries/` and `instruments/` |
| `--db PATH` | index path. Default: `rnd.db` in the library, or `$RND_DB` |
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
catalogue item instead. An unknown id suggests near matches. A `superseded` or
`disputed` claim is marked, with the id of the claim that replaced or contradicted
it. `search` marks them the same way, and both also return question files.

### `list`

Entries, newest first. Filters: `--kind`, `--relevance act|watch|reference`,
`--status active|draft|superseded`, `--field`, `--tag`.

### `tools`

The instrument registry: each studio tool's status, how to invoke it, when to use
it and where it lives. `--status shipped|planned|retired` filters.

### `stats`

Counts by kind, relevance, field, source tier and claim confidence, plus each
catalogue's pinned commit and sync time. `--usage` adds the count of searches
that found nothing and the most frequent missed queries, read from the local miss
log (see [Security and trust](../security/)).

### `claims [list|assign <entry>]`

`claims` (or `claims list`) lists indexed claims with their id, state and
relations; `--state verified|unverified|disputed|wrong|superseded` filters and
`--json` prints machine-readable output. `claims assign <entry>` adds a stable
`c-<hex>` id to each claim of one entry that has none, refusing
(`MULTIPLE_CLAIMS_HEADINGS`) without writing if the entry has more than one real
`## Claims` heading. Ids are never renumbered, and existing entries are not
rewritten in bulk.

### `questions`

Lists the question files under `questions/`. Filters: `--status
open|investigating|answered|parked`, `--field`. `--json` for machine-readable
output.

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
`entry_tags`, `sources`, `claims`, `claim_relations`, `links`, `questions`,
`question_fields`, `catalogs`, `catalog_items`, `meta`, plus the FTS tables
`entries_fts`, `questions_fts` and `catalog_fts`.

```bash
python -m rnd sql "SELECT confidence, count(*) FROM claims GROUP BY confidence"
python -m rnd sql "SELECT entry_id, text FROM claims WHERE confidence = 'disputed'"
```

### `abmine analyze <record>`

ab_dataminer: where and how much the arms of an A/B run of one model differ, from a JSON-lines record of greedy generations with top-K logprobs. No GPU, no server, and no library needed. See [Mining an A/B run](/rnd/handbook/ab-dataminer/).

| Flag | Meaning |
|---|---|
| `--arm A` | limit to these arms, in this order (repeatable); the first is the reference of each pair |
| `--reference R` | an arm to break ties at the other arms' forks, and the chosen-token MAE against it |
| `--log ARM=PATH` | an arm's `OLLAMA_DEBUG` server log (repeatable) |
| `--json` | machine-readable output |

Errors: `ABMINE_RECORD` (unreadable or not JSON lines), `ABMINE_EMPTY` (no result rows), `ABMINE_LOG`, `ABMINE_ARM` (an arm not in the record).

## Writing

### `new "<title>"`

Scaffold `entries/<year>/<date>-<slug>.md` from the template and print its path.
Options: `--kind` (default `finding`), `--relevance` (default `reference`),
`--field` and `--tag` (repeatable), `--id`, `--date`. It refuses to overwrite an
existing file.

### `new-question "<title>"`

Scaffold one file under `questions/` and print its path. Options: `--field` and
`--tag` (repeatable), `--id`, `--date`, `--status open|investigating|answered|parked`
(default `open`) and `--answered-by CLAIM_ID` (repeatable). `--status answered`
needs at least one `--answered-by` naming a claim id that exists; otherwise the
command refuses and writes nothing.

### `change "<text>"`

Record one update as a changelog fragment under `changes/`, without touching the
version or `CHANGELOG.md`. `--level major|minor|patch|micro|nano` (default
`nano`). Fragment file names carry a random part, so two branches never collide.

### `sync [paths…]`

Rewrite every bound number in the given files or folders (default: entries,
questions, briefs and experiment notes) from the `experiments/<id>/results.json`
it names. `--check` changes nothing and exits 1 if any bound number differs.
See [Filing research](../filing-research/#binding-a-number-to-a-results-file).

### `reconcile <entry>`

For each `supersedes`, `contradicts` or `supports` relation in the entry's claims,
mark the older claim in its own file: `superseded-by` and state `superseded`,
`contradicted-by` and state `disputed` (unless already `superseded` or `wrong`,
keeping `[wrong]` as `[wrong]`), or `supported-by`, adding an id if the older
claim has none. It changes nothing else on that line and no other line, and
running it twice changes nothing. It refuses without writing if any file to read
or update has more than one real `## Claims` heading (`MULTIPLE_CLAIMS_HEADINGS`),
or if the line it is about to change is not the claim it read (`CLAIM_MISMATCH`).

### `check`

Validate every entry, question, changelog fragment, instrument and catalogue file
without touching the index. Exits 1 on any error. See
[Filing research](../filing-research/) for the rules.

### `build`

Rebuild `rnd.db` from `entries/`, `instruments/` and `catalogs/`. If any file has
an error, the build halts and the previous index is kept. Searches rebuild
automatically when files change, so you rarely need this.

### `bump [level]`

Raise the version and add a CHANGELOG section. With fragments under `changes/`
(written by `rnd change`), `bump` takes the highest level among them, moves the
version once, lists every fragment's text in one CHANGELOG section and deletes the
fragments: updates add a fragment, and the version moves once, in a release pull
request. With no fragments it works as described below. Versions have five
segments, `MAJOR.MINOR.PATCH.MICRO.NANO`:

| level | for |
|---|---|
| `major`, `minor`, `patch` | the `rnd` tool itself (semver meaning) |
| `micro` | a structural library change: a new experiment, catalogue or instrument family |
| `nano` (default) | an ordinary library update: entries filed or revised, results added |

A bump resets the segments after the one it raises (`1.0.0.0.9` → `micro` →
`1.0.0.1.0`). The CHANGELOG section lists the entries, instruments, experiments and
catalogues changed since the last `v*` tag, including uncommitted and untracked
files, plus any `--note` lines. `--dry-run` prints it without writing. Both
`mcptoolshop_rnd/__init__.py` and `CHANGELOG.md` are staged through temp files
in the same folder and swapped with `os.replace`, rolling back `__init__.py` if
the `CHANGELOG.md` swap fails; if a crash leaves `__init__.py` ahead of
`CHANGELOG.md`, re-running at the matching level completes it and re-running at
any other level refuses with `BAD_CHANGELOG` instead of bumping twice. The
command prints the commit, tag and push to run next.

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

Codes include `NO_LIBRARY`, `NOT_FOUND`, `EXISTS`, `BAD_ID`, `INDEX_INVALID`, `SQL_ERROR`,
`READOUTS_MISSING`, `READOUTS_INDEX_INVALID`, `BAD_VERSION`, `BAD_LEVEL`, `BAD_CHANGELOG`,
`GIT_FAILED`, `INTERNAL` and `INTERRUPTED`, plus the catalogue sync codes. The 1.2
commands add `BAD_CHANGE` and `BAD_FRAGMENT` (changelog fragments); `BAD_BINDING`,
`BAD_RESULTS`, `MISSING_KEY`, `BAD_FORMAT`, `BAD_VALUE` and `SYNC_MISMATCH` (bound
numbers); `CLAIM_NOT_FOUND`, `CLAIM_MISMATCH`, `DUPLICATE_CLAIM_ID`,
`MULTIPLE_CLAIMS_HEADINGS` and `SELF_RELATION` (claim ids and links);
`BAD_STATUS` and `BAD_ANSWERED_BY`
(questions); `INSTRUMENTS_PROTECTED` (a command that summarises outside content
was pointed at `instruments/`); and `MISSING_EXTRA` (a command needs an optional
package that is not installed).
