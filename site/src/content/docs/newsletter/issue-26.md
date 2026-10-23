---
title: "Release night: two near misses, both caught"
description: "Escape the Valley 1.3.1 and XRPL Camp 1.5.1 shipped overnight. Before they did, the release checks caught a landing page edit that never reached the live page, and a release workflow that GitHub refused to start. A local translation model also filled a 32 GB graphics card on a 10 KB README. This issue covers what went wrong, how each was caught, and what changed so it can't happen quietly again."
issue: 26
date: 2026-10-23
highlights:
  - "<strong>Two releases out.</strong> Escape the Valley 1.3.1 and XRPL Camp 1.5.1 shipped with clean release programs, each checked on Windows and Linux after publishing."
  - "<strong>An edit the live page never saw.</strong> A landing page update went into a file the page doesn't use. It was caught while collecting the evidence for the release, and the release gate now checks the live page for the text a release promises."
  - "<strong>A release that wouldn't start.</strong> GitHub refused to run Escape the Valley's release workflow because of a permission mismatch added weeks earlier. Nothing was published. The fix was one line, and the tag was moved to the fixed commit."
  - "<strong>A README that filled the card.</strong> With no limit set, the translation model reserved room for 131,072 tokens and used 31,165 MiB of the card's 32,607 for a 10 KB file. Capped at 16,384 tokens, the same job peaked at 21,846 MiB."
---

Two releases went out overnight: **Escape the Valley 1.3.1** and **XRPL Camp 1.5.1**. Both carry the clean-build fixes
from [issue 25](/rnd/newsletter/issue-25/). Their packaged programs hold no build-machine folder paths, and Escape the
Valley's carry exact licence texts for everything inside them. Getting there, the checks caught three things that would
otherwise have gone out wrong or not at all.

## An edit the live page never saw

Every release goes through a full checklist, the **treatment**, before it ships. One step updates the tool's landing
page. For Escape the Valley, a new feature card was added to the site's configuration file, the site built cleanly, and
the deploy succeeded.

The card never appeared. Escape the Valley's landing page is a hand-built page that doesn't read that configuration
file. The live page still said "v1.1 — the highlights" and quoted a test count from June.

**How it was caught:** the release record has to quote evidence for each step, and the landing page evidence meant
fetching the live page and finding the new text in it. It wasn't there. "The page returns 200" would have passed.

**What changed:**
- A follow-up edited the page that's actually served. It now reads "v1.3 — the highlights", with the current test count
  (1,068). A claim nobody had re-measured since June was dropped.
- **The release gate now checks the live page.** Each release record lists text the live landing page must show. The
  gate fetches the page and refuses the release if any of it is missing.

## A release that GitHub wouldn't start

Pushing the version tag starts Escape the Valley's release workflow. That workflow first re-runs the test suite as a
gate, then publishes to npm, PyPI and GitHub. This time GitHub refused to start it at all: "startup failure", with no
logs.

**The cause** was added four weeks earlier (2026-09-26), in a change that wasn't about releases. The test workflow gained a coverage
upload that needs permission to request a short-lived identity token (`id-token: write`). The release workflow calls the
test workflow as its gate, but granted it only permission to read the code. On GitHub, a workflow called by another
can't hold more permissions than its caller grants, and when it asks for more, GitHub won't start the run.

So every Escape the Valley release since that change would have failed the same way. This was simply the first one
tried.

**What happened next:**
- **Nothing was published.** The other release steps (npm, PyPI, the program builds) all wait for this workflow to
  succeed, so none of them ran. That was checked before anything else: no GitHub release, and no 1.3.1 on npm or PyPI.
- **The fix was one line:** the gate grants the token permission too.
- **The tag was moved.** The first tag pointed at a commit with the broken workflow. Since it had published nothing, it
  was deleted and re-made on the fixed commit, after a fresh release record and approval for that exact commit. The
  only difference between the two commits was the workflow file.
- **The rule carries forward:** the next Escape the Valley work adds a Rust test job to the same workflow, and its brief
  says it must ask for no more than the gate grants.

## A README that filled the card

Release READMEs are translated into seven languages by TranslateGemma 27B, running locally on the studio's RTX 5090
(32 GB). Each run needs the GPU, and is granted for an expected size and time.

The first attempt was asked for about 20 GB. It peaked at **31,165 MiB**, just under the card's limit. The translation
script sends no context size, so the model server loaded the model with its full default of 131,072 tokens and
reserved memory for all of it. The Escape the Valley README is 10.8 KB, about 3,000 tokens.

That attempt had a second problem, of the studio's own making. A command meant for the Escape the Valley folder ran in
another repository's folder and rewrote that repository's translations. Nothing was committed, and the files were
restored at once.

The second run used a copy of the model capped at **16,384 tokens** of context:

| Run | Context | Peak card memory | Result |
|---|---|---|---|
| First (default) | 131,072 tokens | 31,165 MiB | wrong folder, reverted |
| Second (capped) | 16,384 tokens | 21,846 MiB | 7 of 7 languages |

The second run also had a hard stop: a separate monitor would end it if the card passed 26,000 MiB. It never fired.

**A clean exit code isn't taken as proof.** Every run is now checked three ways: all seven files are newer than the run's start,
the language bar lists all seven, and each keeps all 25 bold labels from the English.

**Product names still need protecting.** Hindi translated "XRPL" and the game's name, and Chinese turned the game's name
into a translated title. Both were fixed by hand. A protected-terms file, already in use on rnd, comes to each tool's next release, so the
translator leaves those names untouched.

**For anyone using the tool:** an issue is filed on [polyglot-mcp](https://github.com/mcp-tool-shop-org/polyglot-mcp/issues/55)
to size the context to the input. On a 24 GB card, the default would not fit on the card.

## Where things stand

- **Escape the Valley 1.3.1** ([release](https://github.com/mcp-tool-shop-org/escape-the-valley/releases/tag/v1.3.1)):
  live, and checked through npm on Windows and Linux. On Windows, `trail licenses` prints some extra blank lines, because
  a few licence texts kept their own line endings. Every licence is there in full, and the fix is queued for 1.3.2.
- **XRPL Camp 1.5.1** ([release](https://github.com/mcp-tool-shop-org/xrpl-camp/releases/tag/v1.5.1)): live, and checked
  through npm on Windows and Linux.
- **Escape the Valley 2.0:** the first Rust phase, the game's core data and world generation proven against the Python
  game, is being built.
- **macOS:** neither program's macOS build runs on the studio's machines. The macOS downloads were scanned unpacked once
  published, but haven't been run.
