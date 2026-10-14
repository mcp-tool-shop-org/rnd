---
title: A red check that says how to fix itself
description: Atlas and testing-os, what they are, and how the research library is learning to collect from the fleet the way housekeeping collects from Atlas. Plus interlock's first release, and a proof that changed how a puzzle generator builds its items.
issue: 6
date: 2026-10-14
highlights:
  - "<strong>Atlas's red check now says how to fix itself, and says it where people look:</strong> the failure lands on the line in the pull request, with the lines to paste."
  - "<strong>Two live failing runs found what tests alone couldn't:</strong> annotations that never reached the diff, and each message repeated four times."
  - "<strong>The library now collects experiment records the way housekeeping collects maps:</strong> at a pinned commit, with a checked hash, through a public guard."
  - "<strong>interlock 0.1.0 is out,</strong> and a short proof settled what a T10 claim puzzle can and can't test."
---

Every claim below links to the record it came from.

## Atlas and testing-os, and how the library connects to them

**What they are.**
- **[testing-os](https://github.com/dogfood-lab/testing-os)** is the studio's testing workbench: protocols, evidence stores and learning loops for AI-assisted software.
- **Atlas** is its mapping engine. `atlas map` records how one repository is built: which parts it has, what each part does, which files belong to which part, and the "doors" where it meets the outside, such as workflows, entry points and the packages it publishes. The map is committed in the repository it describes.
- **`atlas check` runs in CI.** It fails when the code and the map disagree, so a new folder or a moved file can't pass unnoticed.
- **Every repository in the fleet that runs workflows keeps a map, made by one pinned engine version.** That's what lets a question be asked across the whole organisation.

**How [housekeeping](https://github.com/mcp-tool-shop-org/housekeeping) uses it.** The two tools split the work:
- **Atlas works offline,** one repository at a time, and records how that repository is built.
- **Housekeeping works online,** across the organisation. It records what GitHub says now: CI, pull requests, releases, Actions cost.
- **Housekeeping collects each repository's committed map by its blob id,** checks the map's health against the organisation's rule (no map, no check in CI, an engine behind the fleet), and ties a red run's failed step to the door it came through. Its findings stay private.

**How this library copies that pattern.**
- Each tool repository already commits its own pre-registered experiment specs and run records, the way it commits its map. interlock's receipts are the main example.
- The library should collect them the way housekeeping collects maps, rather than by hand. That's the build-up program R&D set out on 2026-10-13. → [The build-up program](https://github.com/mcp-tool-shop-org/rnd/blob/main/entries/2026/2026-10-13-atlas-testing-os-rnd-buildup.md)

## A red check that says how to fix itself

**The problem.** The fleet's commonest `atlas check` failure was a folder that no part of the map covers, such as interlock's `receipts/`.
- Each new file there failed the check, and regenerating the map pardoned only that one file.
- In CI the failure showed only as "exit code 1".

**What Atlas slice AM changed.** It's merged in testing-os, and ships in the next Atlas release with the multi-repository slices.
- **The check prints the lines to fix it,** ready to paste into `boundaries.yaml`. A folder no part reaches gets a part of its own, and a folder a part already reaches gets a glob. Every test applies the printed lines and requires the check to pass afterwards.
- **`atlas map` warns about an uncovered folder before CI fails** on the next file.
- **In GitHub Actions, the check annotates.** A failure is an error on the file, and a door notice is a warning on the line it was read from. The finding and the fix go into the job summary. Outside Actions, the output is unchanged byte for byte.

→ [testing-os #159](https://github.com/dogfood-lab/testing-os/pull/159)

**What the live runs showed.** The spec required one real failing Actions run before release, and recorded what GitHub actually displays. The first run found two defects that the tests had passed:
- **Paths:** a job that checked out into a subdirectory annotated `repo/.github/...`, and GitHub never placed that on the pull request's diff. Paths are now relative to the repository's top level.
- **Line numbers:** file-level failures carried line 0, and GitHub shows those only as a dead link, never on the diff. They now point at line 1.

A second live run showed every annotation landing on the diff, the subdirectory job included. The same run showed each message repeated four times, once per test leg and once per trigger. The organisation's Atlas rule now says to run the check on one leg only. → [the live run](https://github.com/dogfood-lab/testing-os/pull/160)

**The lesson:** a CI message is only fixed when someone has looked at where GitHub puts it. Tests of the emitted text couldn't see either defect.

**Next for Atlas:**
- **Slice AN is merged:** one `atlas mcp` server can now answer for several repositories, fixed when it starts. → [testing-os #169](https://github.com/dogfood-lab/testing-os/pull/169)
- **Slices AO to AQ follow,** before one pinned release for the whole set. AQ, the inferred-consumer check, turns on only after it clears a pre-set recall and precision bar on a labelled seed. → [the rulings](https://github.com/dogfood-lab/testing-os/pull/168)

## The library collects

`python -m rnd collect` reads an experiment's records from its tool repository at a pinned commit.
- **The pin:** each source is named with its path, its commit and the SHA-256 of its bytes. The bytes are read with `git show`, so the clone's own state doesn't matter, and a source whose hash no longer matches is refused rather than re-trimmed.
- **The trim:** each experiment's own module decides what its published record keeps. Every output then passes a public guard, which refuses a machine path, a home directory or an environment dump.
- **The drift check:** `--check` rebuilds every output and compares it byte for byte with the committed copy, so any drift between a source and its published copy is found.

E5's card, in [issue 5](/rnd/newsletter/issue-05/), was the first experiment collected this way. → [rnd #4](https://github.com/mcp-tool-shop-org/rnd/pull/4) · [E5's collect.json](https://github.com/mcp-tool-shop-org/rnd/tree/main/experiments/e5)

**Still to come in the program:**
- one run-record format in testing-os, for interlock, the library and later experiments;
- defect classes shared across the fleet, so the library can count them over time;
- an instrument-health check;
- the same failure-output style for the library's own `check`.

These will be reported as they land.

## Also this week

**[interlock 0.1.0](https://github.com/mcp-tool-shop-org/interlock/releases/tag/v0.1.0) is released,** the first on PyPI as `mcptoolshop-interlock`. It's a prototype advisory router: it suggests a model, an engine and a device from measured receipts, and never serves traffic. Its release assets carry SLSA provenance, and CI now fuzzes its receipt and spec readers.
- **A fuzz-target bug caught in review:** the first version of the fuzz target excused the very crashes it should report. A receipt that isn't UTF-8 crashed `interlock check` with a traceback.
- **Now:** both readers refuse cleanly, with tests. → [interlock #121](https://github.com/mcp-tool-shop-org/interlock/pull/121)

**What a T10 claim can test.** [role-set](https://github.com/mcp-tool-shop-org/role-set) builds small logic puzzles that teach a model to read size words literally ("exactly", "at least", "at most" two of them).
- **The defect:** a variety fix passed its floors, but review found that some "at least" puzzles were passing their shortcut check on a second "exactly" clue. They tested "exactly" again.
- **The proof:** every assignment that fits "exactly k" also fits "at least k". So if every assignment that fits "at least k" gives the same verdict about one entity, every assignment that fits "exactly k" does too, and misreading the word can't change a claim's verdict.
- **The fix:** claim puzzles now test "exactly", set puzzles test all three words, and each puzzle must change its answer on its own clue's misreading. On fresh locked seeds, the defect went from 8 items to 0. → [role-set #53](https://github.com/mcp-tool-shop-org/role-set/pull/53) · [role-set #54](https://github.com/mcp-tool-shop-org/role-set/pull/54) · [the briefs](https://github.com/mcp-tool-shop-org/rnd/tree/main/experiments/t10-variety)
