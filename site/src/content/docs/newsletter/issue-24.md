---
title: "One fix for nine tools, and the check that comes before shipping"
description: "Nine of the studio's command-line tools reach npm through one small launcher. A bug in it meant `--version` printed the launcher's version instead of the tool's. Fixing it once fixed it for all nine. This issue covers that fix, what the translation model got wrong in the release READMEs, and the check every release now has to pass before it ships."
issue: 24
date: 2026-10-22
highlights:
  - "<strong>One launcher, nine tools.</strong> `npx @mcptoolshop/&lt;tool&gt; --version` printed the launcher's own version. Version 1.2.0 passes every argument to the tool, and nine tools pick it up on their next install, with no release of their own."
  - "<strong>The tool's own name.</strong> Once `--help` reached the tool, it printed a cached file's name in its usage line. Setting the program name when the tool starts fixed that on Windows and Linux."
  - "<strong>Translation slips we fix by hand.</strong> In the release READMEs, the local translation model dropped some bold text and translated product names. Each run is now checked for both."
  - "<strong>No release without its full check.</strong> Three releases went out without the studio's full release checklist. Now the release gate refuses any version that has no checklist record for the exact commit being shipped."
---

Several studio tools are written in Python, but people install them with `npx`, Node's package runner. That works
through one small npm package, [npm-launcher](https://github.com/mcp-tool-shop-org/npm-launcher). Each tool ships a
tiny wrapper that tells the launcher which GitHub release to fetch. The launcher downloads the right binary for the
machine, checks its SHA-256 checksum, caches it, and runs it.

## The bug: the wrong `--version`

The launcher answered `--version` and `--help` itself, before it looked at which tool it was running. So
`npx @mcptoolshop/xrpl-lab --version` printed `mcptoolshop-launch 1.1.1`, the launcher's version, not the tool's.
Learners and scripts asking "which version do I have?" got the wrong answer.

Launcher **1.2.0** answers those flags itself only when it's run on its own. Through a tool's wrapper, every argument
reaches the tool. The launcher's own version now has a flag of its own, `--launcher-version`.

**One fix, nine tools.** Nine wrappers ask for "any 1.x" of the launcher, so a fresh `npx` picks up 1.2.0 with no
release of their own. One wrapper, XRPL Camp, pinned the exact version 1.1.1, and moves to 1.2.0 in its own release.

## The second bug the first one revealed

With `--help` now reaching the tool, the tool's usage line read `Usage: xrpl-lab-2.7.9-win-x64.exe …`. Python
command-line libraries take the program's name from how it was started, and here that was the cached download's file
name. Nobody had seen it before, because `--help` had never got through.

The fix tells the operating system to start the tool under its own name. Measured with the real tool:

| Platform | How it was checked | Usage line |
|---|---|---|
| Windows | the packed launcher with the published xrpl-lab wrapper | `Usage: xrpl-lab …` |
| Linux | WSL Ubuntu, with the real Linux binary downloaded and checksum-verified | `Usage: xrpl-lab …` |

A command that reads the tool's bundled lesson files still worked, so the bundled tool finds its own files under the
new name.

## What the translation model got wrong

Release READMEs are translated into seven languages by a local model, TranslateGemma 27B, running on the studio's own
GPU. It's reliable on prose. Today's runs showed two kinds of slip, the same kinds the readouts newsletter recorded
on 2026-10-20:
- **Bold text dropped.** Japanese lost one bold label in the xrpl-lab README. In XRPL Camp's, Italian lost two and
  Portuguese one. The Japanese camp README has been missing 5 of its 25 bold spans since an earlier run.
- **Product names translated.** Japanese, Chinese and Hindi turned "XRPL Lab" into a translated name, and Hindi did the
  same to "XRPL Camp".

All of these were fixed by hand. Every translation run is now checked for both: bold spans are counted against the
English, and product names must survive unchanged.

## The check before shipping

The studio has a full release checklist for every tool, called the **treatment**. It checks the ship gate and scans for
personal details, then brings the README, translations, handbook, landing page and repository metadata up to date, and
records the tool in the studio's knowledge base.

Three releases this week (XRPL Camp 1.4.2 and xrpl-lab 2.7.8 and 2.7.9) shipped after code review and live testing, but
without it. Nobody had decided to skip it; the step had fallen out of the routine. A published version can't be
changed, so running the checklist afterwards doesn't fix what went out.

Two changes followed:
- **The release gate now refuses** any version without a treatment record for the exact commit being tagged. The record
  covers each part of the checklist, with evidence, and live checks that the landing page and handbook are up. The
  gate refused the first version it checked, for README translations months out of date. They were fixed before the
  release.
- **Treatments ran for all three tools.** npm-launcher shipped 1.2.0 only after its own, and xrpl-lab and XRPL Camp were
  treated so their next releases go out complete.

*Records:*
- npm-launcher 1.2.0 ([release](https://github.com/mcp-tool-shop-org/npm-launcher/releases/tag/v1.2.0)), with its live
  checks on Windows and Linux;
- the treatment pull requests for npm-launcher (#10), xrpl-lab (#48) and XRPL Camp (#18).
