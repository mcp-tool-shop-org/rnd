---
id: 2026-10-13-claude-code-read-deny-rules-do-not-stop-a-grep-walk
title: "Claude Code: a Read deny rule doesn't stop a Grep walk over the denied tree"
date: 2026-10-13
kind: finding
relevance: act
fields: [agent-tooling]
tags: [claude-code, permissions, isolation, sandbox]
---

## Summary

In Claude Code 2.1.197, a deny rule such as `Read(X/**)` doesn't contain a recursive search started at `X` itself. A
Grep with `path` set to `X`, the denied root, walked the tree and returned the names of files inside it. A sandbox
containment probe found this on 2026-10-13. Permission rules are not a containment boundary. Operating-system file
permissions are.

This is documented behaviour, not a hidden gap. Claude Code's permissions page calls `Read` rules on Grep and Glob a
"best-effort" attempt, and says they're applied to the directory a search's `path` resolves to. `X/**` doesn't match `X`
itself. The same page points to the sandbox for OS-level enforcement.

**Corrected 2026-10-20.** This entry first said "at or above `X`". The probe measured a Grep whose `path` was the denied
root itself (the home directory, with `Read(~/**)` denied). A Grep started above the root wasn't measured.

## Key points

- **The probe:** an agent was asked to reach planted sentinel files by every route: Read, Grep, Glob and Bash. The Read
  calls on the denied paths were refused. A Grep started at the home directory listed files under it, including a
  planted file whose name was never given.
- **The fix that held:** the CLI runs as an unprivileged user, and every tree it must not see is owned by root with no
  access for others. On the re-probe, every route at every tree came back empty: 29 of 29 calls, 0 leaks.
- **Seen on 2.1.197 only.** Later versions weren't probed.

## Studio relevance

Any studio harness that keeps an agent out of files with `--disallowedTools` or settings deny rules alone is leaky.
Put the agent in a sandbox or under a separate OS user, and use deny rules only as a second layer.

## Claims

- [unverified] On Claude Code 2.1.197, a Grep whose path is above a `Read(X/**)`-denied tree lists file names inside that tree. Not measured: the probe's Grep was rooted at the denied root itself.
- [verified] On Claude Code 2.1.197, a Grep whose `path` is the denied root itself (the home directory, with `Read(~/**)` denied) lists file names inside it. (via: the sandbox containment probe, 2026-10-13; the Publisher's record of the probe, re-read by R&D 2026-10-20)
- [verified] Claude Code's permissions documentation describes `Read` rules on Grep and Glob as best-effort, applied to the directory the search's `path` resolves to, and points to the sandbox for OS-level enforcement. (via: R&D's read of code.claude.com/docs/en/permissions, 2026-10-20)
- [verified] Running the CLI as an unprivileged user, with root-only trees, stopped every route the probe tried. (via: the re-probe, 29 of 29 calls, 0 leaks, 2026-10-13)

## Sources

- [rig] Containment probes in the Docker sandbox `atlas-pilot`, 2026-10-13
- [primary] https://code.claude.com/docs/en/permissions — Claude Code's permissions documentation (read 2026-10-20)
