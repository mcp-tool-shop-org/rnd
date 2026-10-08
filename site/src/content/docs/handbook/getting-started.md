---
title: Getting started
description: Clone and run, or install the command from PyPI; first searches and the wrappers.
sidebar:
  order: 1
---

## Requirements

Python 3.10 or later. Nothing else: `rnd` uses the standard library only, so
there is no install step and no virtual environment. It runs on Windows, macOS
and Linux.

```bash
git clone https://github.com/mcp-tool-shop-org/rnd.git
cd rnd
python -m rnd --version
```

### The command from PyPI

To call `rnd` from other projects, install the command:

```bash
pip install mcptoolshop-rnd
rnd --library path/to/rnd search cuda
```

The package holds the tool, not the library; the entries live in the clone.
`rnd` finds a library from `--library`, then `$RND_ROOT`, then the nearest folder
at or above the current one with `entries/` and `instruments/`. Outside a
library every command except `rnd readouts` stops with `NO_LIBRARY`. The package
imports as `rnd`, as does an unrelated PyPI package of that name, so keep them
in separate environments.

## First searches

The index (`rnd.db`) builds itself the first time you search, and rebuilds when
any entry or catalogue file changes.

```bash
python -m rnd search cuda graphs          # entries and catalogue items
python -m rnd search pitch --entries-only # entries only
python -m rnd list --relevance act        # what needs doing, newest first
python -m rnd show 2026-10-07-cuda-graphs # one entry, with its backlinks
python -m rnd stats                       # counts by kind, field, tier, confidence
```

Words are matched as words, so punctuation in a query is safe. For FTS5 syntax
(`AND`, `OR`, `NEAR`, `prefix*`) pass `--raw`.

## The order to look in

Before researching anything, look in this order:

1. `rnd search <words>`: the bench may already hold it.
2. `rnd readouts <words>`: the verified knowledge bases may cover it. Add `--any`
   to match any word rather than all of them.
3. `rnd tools`: the instruments that can research the gap (study swarms,
   evidence packs, local models, rented GPUs).

## Pointing at readouts

`rnd readouts` needs a readouts checkout. It looks at `$RND_READOUTS` first, then
the studio rig's default location. Point it anywhere with `--root`:

```bash
export RND_READOUTS=~/src/readouts
python -m rnd readouts --list
python -m rnd readouts splice glitch --any --limit 3
```

## Run it from any directory

`rnd.cmd` (Windows) and `rnd.sh` (POSIX shells) are thin wrappers. Put the repo
on your `PATH`, or alias them:

```bash
alias rnd="$HOME/src/rnd/rnd.sh"
rnd search intelligibility
```

## For agents

Every listing command takes `--json`. Errors go to stderr as
`error: CODE: message` with a `hint:` line, and the exit code says what kind of
failure it was (see the [command reference](../reference/)).
