---
title: "27 October: a spotlight on AI Jam Sessions, interlock and XRPL Camp"
description: "A spotlight issue on three tools the studio ships in the open: AI Jam Sessions, which teaches an AI to play, sing and listen; interlock, which went from 1.0.8 to 1.0.10 while it measured its first rented card; and XRPL Camp, which teaches the XRP Ledger in one sitting. Plus one short note from today's runs."
issue: 32
date: 2026-10-27
highlights:
  - "<strong>AI Jam Sessions.</strong> An MCP server that teaches an AI to play piano and guitar, sing and listen: 109 annotated songs, 56 tools, and three hymns sung whole by a synthetic voice."
  - "<strong>interlock 1.0.8 to 1.0.10.</strong> Three releases made from what the first rented-card runs showed: a time limit on every cell, a restart when one hangs, and noise recorded instead of thrown away."
  - "<strong>XRPL Camp 1.5.</strong> Learn the XRP Ledger in about ten minutes on the test network, and keep a proof of what you did that anyone can check."
---

Today's Colab work produced little to report, so this issue is a spotlight: three of the studio's tools that are
public and shipping, what each one does, and what changed in it lately.

**In this issue:**

1. [AI Jam Sessions: an AI that plays, sings and listens](#ai-jam-sessions-an-ai-that-plays-sings-and-listens)
2. [interlock 1.0.8 to 1.0.10](#interlock-108-to-1010)
3. [XRPL Camp: the XRP Ledger in one sitting](#xrpl-camp-the-xrp-ledger-in-one-sitting)
4. [A short note from today's runs](#a-short-note-from-todays-runs)

## AI Jam Sessions: an AI that plays, sings and listens

[AI Jam Sessions](https://github.com/mcp-tool-shop-org/ai-jam-sessions) is an MCP server that teaches a language model
to play piano and guitar, and to sing. A model can read text, but it has no ears and no fingers, so the server gives
it senses it can use:

- **Reading:** 109 songs across 12 genres, every one annotated with its history, its structure bar by bar, and what
  it teaches.
- **Hearing:** six sound engines, from a sampled piano to a modelled guitar and a vocal tract, playing through real
  speakers.
- **Seeing:** a piano roll the model can read back, a guitar tablature editor, and a browser cockpit.
- **Remembering:** a practice journal that carries over from one session to the next.
- **Listening:** point it at a recording and it measures what is there, with the same kind of tools it uses on the
  score.

It has 56 MCP tools in all, and installs from npm as `@mcptoolshop/ai-jam-sessions`; the current release is 2.8.0.

### Three hymns, sung whole

Version 2.8.0 added whole songs sung by a synthetic voice on the piano's clock: Amazing Grace and America the
Beautiful, every verse. The Battle Hymn of the Republic followed on the [landing
page](https://mcp-tool-shop-org.github.io/ai-jam-sessions/#listen). Each performance is built from sixteen takes of a
singer conditioned on the score, with one take chosen for each phrase and checked for timing and pitch by two
instruments each, then passed by ear.

| | Amazing Grace | America the Beautiful | Battle Hymn |
|---|---|---|---|
| syllables within 40 ms of the score | 107 of 112 | 217 of 224 | 285 of 414 |
| notes within 50 cents | 135 of 140 | 218 of 224 | 368 of 424 |

The Battle Hymn's quick dotted notes are left on the singer's own timing, which is where most of its timing misses
come from. The voice is [SoulX-Singer](https://github.com/Soul-AILab/SoulX-Singer) (Apache-2.0) with its own example
timbre, imitating no real singer, and all three hymns are in the public domain.

### Data others can use

Two datasets from the same work are public on Hugging Face:

- [jam-actions-v0](https://huggingface.co/datasets/mcp-tool-shop/jam-actions-v0): 57 multi-turn MCP tool-use traces
  over four classical piano works, for teaching a model to answer questions about music by calling tools rather than
  guessing.
- [jam-actions-acoustic-v0](https://huggingface.co/datasets/mcp-tool-shop/jam-actions-acoustic-v0): 72 records over
  audio rather than notation, each label checked against what the analysis tools actually return. It ships no audio:
  each record carries a recipe and the hash of the waveform it produces.

Both carry their licences and sources in their cards. Each was corrected on 25 September when an audit found files
whose arrangement licence couldn't be established, and the records built from them were withdrawn.

## interlock 1.0.8 to 1.0.10

[interlock](https://github.com/mcp-tool-shop-org/interlock) picks a model, an engine and a device for a job from
speeds it has measured. [Issue 31](/rnd/newsletter/issue-31/) told how its first runs on a rented T4 card exposed
defects in how it measured, fixed in 1.0.5 to 1.0.7. The next three releases came from the same runs:

- **1.0.8: nothing waits for ever.** Every cell has a wall-time cap, and a call that reads the card's memory now has
  a deadline: one run had gone silent for 56 minutes waiting on it. The harness prints a line at each step, so the
  next hang names its own call. Rig checks get their own identity instead of borrowing a Colab card's name. And
  `interlock route --concurrency N` ranks results for the number of requests you'll actually send.
- **1.0.9: a hung cell is cleaned up.** When a cell's deadline fires, the server is restarted and any late answer
  from the abandoned cell is refused. The fallback reading of the card's memory is checked strictly, and an answer it
  can't trust is recorded as unmeasured.
- **1.0.10: noise is recorded, not used to discard.** A check meant to catch a cached prompt was also discarding real
  cells, because the time to read the prompt varies from pass to pass. Each measured row now records that spread
  instead, and the cells are kept.

interlock 1.0.10 is on PyPI as `mcptoolshop-interlock` and needs Python 3.13 or newer.

## XRPL Camp: the XRP Ledger in one sitting

[XRPL Camp](https://github.com/mcp-tool-shop-org/xrpl-camp) teaches the XRP Ledger by doing it: real transactions on
the ledger's test network, in about ten minutes, ending with a proof of what you did that anyone can check against
the ledger. It's on PyPI as `xrpl-camp` and npm as `@mcptoolshop/xrpl-camp`, both at 1.5.2.

- **1.5.0** wired in the last parts of the course: a walkthrough of the reserve an account owes for the things it
  owns, a plain-text certificate you can keep and share, and dated receipts each time a proof is verified.
- **1.5.1 and 1.5.2** tightened the edges. A submission whose result comes back missing is no longer taken as a
  success: the camp looks the transaction up on the ledger and reports what it finds. The reserve step says plainly
  when a change couldn't be measured yet. And the standalone downloads no longer bundle a leftover install record from
  their build.

## A short note from today's runs

On today's T4 runs, the Colab machine's memory limit stopped some of the largest cells: when a model's working cache
spilled out of the card into the machine's memory, the limit killed the model server at about 11.6 GB in use. Once,
the process running our harness was killed too, and the run was lost without a record. The run launcher now notices
a dead run and stops it within about two minutes, instead of waiting out its full time. How interlock should refuse
such cells before loading them is still being designed.
