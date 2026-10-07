---
title: Security and trust
description: What rnd touches, what it never touches, and how the public repo stays clean.
sidebar:
  order: 6
---

## What it touches

- **Reads and writes:** files inside the repo (`entries/`, `instruments/`,
  `catalogs/`, `experiments/`) and the generated index `rnd.db`. `rnd new` writes
  one new entry file and refuses to overwrite. `rnd catalog sync` rewrites a
  generated `catalog.json`.
- **Reads only:** the readouts knowledge bases, opened in SQLite's read-only
  mode. `rnd sql` also uses a read-only connection.

## What it never touches

- Nothing outside the repo and the readouts checkout.
- No credentials: it neither stores nor reads any.
- No network, except `rnd catalog sync`, which calls the GitHub API through your
  own `gh` login when you run it.
- No telemetry. Nothing is collected or sent.
- No background service and no elevated permissions.

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
