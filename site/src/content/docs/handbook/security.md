---
title: Security and trust
description: What rnd touches, what it never touches, and how the public repo stays clean.
sidebar:
  order: 6
---

## What it touches

What `rnd` writes, by where it lands:

- **Inside the repo** (the library: `--library`, else `$RND_ROOT`, else the nearest folder at or above
    the working directory that holds `entries/` and `instruments/`, else the checkout the
    package runs from): `rnd new` (one new file under `entries/` or `instruments/`, never
  overwriting), `rnd new-question` (`questions/`), `rnd new-experiment`,
  `rnd runs record` and `rnd collect <name>` (`experiments/<name>/`),
  `rnd claims assign`, `rnd reconcile` and `rnd sync` (claim lines and bound
  numbers in existing Markdown files), `rnd change` (`changes/`), `rnd bump`
  (`mcptoolshop_rnd/__init__.py` and `CHANGELOG.md`, through temporary files
  beside each, and it deletes the `changes/` fragments it used),
  `rnd catalog sync` (`catalogs/<name>/catalog.json`), `rnd datapack build`
  (`datapacks/<name>/datapack.json`) and `rnd layout` (`docs/layout.json`).
- **The index:** `rnd.db`, or the path given by `--db` or `$RND_DB`, with a
  temporary `.db.tmp` file beside it while it is built. `rnd build` writes it,
  and every command that reads the index (`search`, `show`, `list`, `tools`,
  `stats`, `catalog`, `claims`, `questions`, `sql`, `runs`, `ledger`, `where`,
  `probe`) rebuilds it first when a source file has changed. The miss log
  `rnd.misses.jsonl` sits beside it (see below).
- **Your home folder:** `rnd watch` writes its seen-items file to `--state`, else
  `$RND_WATCH_STATE`, else `~/.rnd/watch-state.json` (built in code as
  `Path.home() / ".rnd" / "watch-state.json"`), where it stays across runs. It is written through a `.tmp` file beside it.
    `--no-save` skips the write.
- **The raw-data stores, outside the repo:** `rnd raw ingest`, `rnd raw private` and
  `rnd raw relicense` write to the public store (`--public`, else `$RND_DATA`,
  else `../rnd-data`) and the private store (`--private`, else `$RND_DATA_PRIVATE`, else `../rnd-data-private`
    beside the library; when `rnd raw` is run outside a library, `rnd-data-private`
    beside the public store). `rnd raw ingest` also puts
  every file over 256 KB into the blob store, under `blobs/` in the folder
  named by `$RND_DATA_STORE_D` or by the `"d"` entry of the public store's
  `store.local.json` (there is no default; without one, ingest refuses). Blobs are written through a `.tmp` file beside them and marked read-only. With `--link` a new blob is
    a hard link to the source file, so **that source file becomes read-only too** (a blob
    already in the store is left alone, and so is its source); without `--link` the
    source is not changed. `rnd raw ingest --update` deletes a run's earlier small files in
  the two stores before writing the new ones. `--dry-run` writes nothing.
- **Read, never written:** `rnd readouts` (SQLite read-only mode), `rnd collect` source
  clones (`git show`), `rnd raw verify`, `rnd datapack verify --copy`,
  `rnd runs record --from`, `rnd abmine`, and `rnd similar` and `rnd digest`,
  which work in memory and write nothing anywhere: no temporary file, no
  working-tree, git index or `rnd.db` change.
- **Code it runs:** `rnd collect <name>`, with or without `--check`, loads and runs
  `experiments/<name>/extract.py` (or the module that folder's `collect.json`
  names) from the library (`mcptoolshop_rnd/collect.py:142-149`). Python may
  cache that module's bytecode in `experiments/<name>/__pycache__/`. `rnd` limits
  what it writes itself to `experiments/<name>/`; it does not limit what that
  module's own code does, so run it only on a library you trust.
- **Outside the `rnd` command:** the package also ships
  `mcptoolshop_rnd.localbuilders`, the harness of the local-builders
  experiment. No `rnd` command runs it. Run directly (for example
  `python -m mcptoolshop_rnd.localbuilders.runner`), on the rented machine it
  was written for and partly as root, it creates, deletes and changes the owner and permissions of files under the paths
  its caller passes (work, home, history, virtual-environment, receipt, log,
  report, secret-directory and containment-probe paths), and its scorer uses a temporary folder in the operating
  system's temp folder, removed when it finishes.

## What it never touches

- No `rnd` command writes, deletes or changes a file anywhere other than the
  places listed above.
- No credentials: it neither stores nor reads any.
- No network, except `rnd catalog sync`, `rnd probe` and `rnd watch`, which read
  public metadata or call the GitHub API through your own `gh` CLI login when you
  run them.
- No background service, and no `rnd` command needs elevated permissions.

## The local-only usage log

Nothing is collected or sent anywhere. One thing is written on your own machine:
when `rnd search` returns no matches, it appends one line (the UTC time and the
query) to `rnd.misses.jsonl` beside `rnd.db` (git-ignored in the repo), or beside
the index named by `--db` or `$RND_DB` (with `--db foo.db` the file is
`foo.misses.jsonl` beside it, not `foo.db.misses.jsonl`).

- Set `RND_NO_USAGE=1` to turn it off.
- Delete the `.misses.jsonl` file at any time to clear it.
- `rnd stats --usage` prints the count and the most frequent missed queries.
- No other usage data is recorded.

## Public-repo hygiene

The repo is public and entries are written fast, so hygiene is a step, not a hope:

- Before every push, the tracked tree is scanned for home-directory paths and
  operator identity. A hit stops the push.
- Entries are written in the author's own words. Copyrighted text is not pasted in.
- Generated images are re-saved without their embedded generator metadata.
- Experiment receipts are checked before they are committed. Large inputs stay
  outside the repo, pinned by checksum.

## Reporting

See [SECURITY.md](https://github.com/mcp-tool-shop-org/rnd/blob/main/SECURITY.md).
Content that should not be public is in scope too: report it the same way.
