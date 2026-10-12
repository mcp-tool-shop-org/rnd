---
id: 2026-10-12-device-runs-from-clean-worktree
title: Device runs go from a clean worktree
date: 2026-10-12
kind: decision
relevance: act
fields: [developer-tools]
tags: [switchyard, process]
---

## Summary

switchyard's live device runs now start from a dedicated, clean worktree (`switchyard-run`, with its own environment)
checked out at the commit under test. They no longer start from the main clone. The change followed the discovery
that a Grok seat had uncommitted harness edits in the main clone, which is where a run could have picked them up. A
receipt names a spec blob and a commit, so it is only true if the code that ran is exactly that commit.

## Key points

- **Failure:** a working copy shared by build seats and device runs can carry edits that no commit records. A run from
  it measures code that nobody reviewed.
- **Decision (Publisher, 2026-10-12):** device runs use only the `switchyard-run` worktree and its environment, reset
  to the reviewed commit before each run. Build seats keep working in the main clone.
- **Prevention:** the harness already refuses a modified spec blob (`require_unmodified`). The clean worktree extends
  that guarantee to the harness code itself.

## Studio relevance

The same rule fits any repo where an agent builds and a device measures: run from a checkout nobody edits. A
follow-up worth considering is a harness check that refuses to start when `git status` in its own tree is not clean.

## Claims

- [verified] Uncommitted harness edits by a Grok seat were found in switchyard's main clone (via: the Publisher's report, 2026-10-12)

## Sources

- [primary] https://github.com/mcp-tool-shop-org/switchyard — the repository
