---
title: Security and trust
description: What rnd touches, what it never touches, and how the public repo stays clean.
sidebar:
  order: 6
---

## What it touches

- **Reads and writes:** files inside the repo (`entries/`, `questions/`,
  `changes/`, `instruments/`, `catalogs/`, `experiments/`), the generated index
  `rnd.db` and, beside it, the local miss log `rnd.misses.jsonl` (see below).
  `rnd new` writes one new entry file and refuses to overwrite. `rnd catalog sync`
  rewrites a generated `catalog.json`. `rnd sync` rewrites bound numbers,
  `rnd claims assign` adds claim ids in the named entry, and `rnd reconcile`
  updates only the cited claim lines in existing Markdown files.
- **Reads only:** the readouts knowledge bases, opened in SQLite's read-only
  mode. `rnd sql` also uses a read-only connection.

## What it never touches

- Nothing outside the repo and the readouts checkout.
- No credentials: it neither stores nor reads any.
- No network, except `rnd catalog sync`, `rnd probe` and `rnd watch`, which read
  public metadata or call the GitHub API through your own `gh` CLI login when you
  run them.
- No background service and no elevated permissions.

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
