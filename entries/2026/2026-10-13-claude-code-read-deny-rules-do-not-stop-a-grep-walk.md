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

In Claude Code 2.1.197, a deny rule such as `Read(X/**)` doesn't contain a recursive search started at or above `X`. A
Grep with `path` set to `X`, or to a directory above it, walked the tree and returned the names of files inside the
denied tree. A sandbox containment probe found this on 2026-10-13. Permission rules are not a containment boundary.
Operating-system file permissions are.

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

- [verified] On Claude Code 2.1.197, a Grep whose path is above a `Read(X/**)`-denied tree lists file names inside that tree. (via: the sandbox containment probe, 2026-10-13)
- [verified] Running the CLI as an unprivileged user, with root-only trees, stopped every route the probe tried. (via: the re-probe, 29 of 29 calls, 0 leaks, 2026-10-13)

## Sources

- [rig] Containment probes in the Docker sandbox `atlas-pilot`, 2026-10-13
