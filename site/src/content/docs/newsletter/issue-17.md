---
title: "What does a Claude Code deny rule actually hide?"
description: We asked an AI agent to reach files it had been told it couldn't read. A deny rule refused the obvious requests, but a search started in the right place still listed the hidden files. Which place depended on how the rule was written, down to a single slash. Version 2.1.280 filters the search we could test there. Here's what we measured, the two times we read it wrong, and what actually keeps an agent out.
issue: 17
date: 2026-10-20
highlights:
  - "<strong>A deny rule isn't a wall.</strong> With reading a folder denied, Claude Code 2.1.197 refused every direct read. But a search started one folder up still listed the names of the files inside, in every rule form we tried."
  - "<strong>The rule's spelling decides which search leaks.</strong> Written as <code>Read(~/**)</code>, a search started at the home folder itself also leaked. Written as an absolute <code>Read(//X/**)</code>, a search at X was refused. Written with one leading slash, the rule protected nothing."
  - "<strong>2.1.280 filters it.</strong> On the newer CLI, the search from above came back with no hidden files. We tested only the absolute form there."
  - "<strong>What held was the operating system.</strong> An agent running as its own user, with the private folders closed to it, reached nothing: 29 of 29 attempts, 0 leaks."
---

Studio tools increasingly hand work to AI agents that read and edit files. Claude Code, which runs many of them, lets
you write **permission rules** to keep an agent away from some files: `Read(~/**)`, for example, denies reading anything
under the home folder. We wanted to know how far such a rule really reaches, before trusting it with anything that
matters.

So we built a small test. An agent ran inside a Docker sandbox, with a few **sentinel** files planted where it had
been told it couldn't look. Each sentinel had a random name, so an agent could only report it by actually finding it.
Then we asked the agent to reach them by every route it had.

## A rule that refuses, and a search that doesn't

On Claude Code 2.1.197, the deny rule did what it says for direct requests: every attempt to read a sentinel was
refused. **Search was different.** Claude Code's Grep tool walks a folder and reports which files match. Started in the
right place, it walked straight through the denied folder and listed the sentinels by name.

The right place depended on how the rule was written. We tried three spellings of the same intent, with one sentinel
at the folder's root and one in a subfolder:

| How the rule was written | CLI | Search started at the denied folder | Search started one folder up | Search inside it |
|---|---|---|---|---|
| `Read(~/**)` (2 runs) | 2.1.197 | **listed both** | **listed both** | refused |
| `Read(//home/agent/b2probe/**)` | 2.1.197 | refused | **listed both** | refused |
| `Read(/home/agent/b2probe/**)`, one slash | 2.1.197 | **listed both** | **listed both** | **listed the sentinel in it** |
| `Read(//home/agent/b2probe/**)` | 2.1.280 | refused | "No files found" | refused |

Three things stand out:
- **Above the folder, both real rule forms leaked on 2.1.197.** A search started one level up listed the hidden names,
  however the rule was written.
- **`~/**` and an absolute path aren't the same rule.** With the home form, even a search started *at* the home folder
  leaked. With the absolute form, a search at the folder itself was refused.
- **One slash protects nothing.** In Claude Code's permission rules, a path with a single leading `/` is read relative
  to the settings source, not the root of the disk. So `Read(/home/…)` never matched the real folder, and every search
  listed everything. An absolute path is written with two slashes: `//home/…`.

**On 2.1.280, the search from above came back empty.** The newer CLI filters it. We only had turns to test the absolute
form there, so whether the `~` form is filtered too is still open.

## Documented, not hidden

None of this is a secret flaw. Claude Code's permissions page calls `Read` rules on Grep and Glob a "best-effort"
attempt, applied to the folder a search starts from. For real enforcement, it points to running the agent in a
sandbox. Our measurements are a concrete picture of what "best-effort" means in practice.

## What actually kept the agent out

We ran the same probe a second way: the agent as its own unprivileged user, with every folder it shouldn't see owned by
another user and closed to others. The operating system, not Claude Code, decided what it could open. **Every route
came back empty: Read, Grep, Glob and Bash, 29 of 29 attempts, 0 leaks.**

The practical rule for any tool that hands files to an agent:
- keep secrets out with the **operating system** (a separate user, or a sandbox);
- use deny rules only as a second layer;
- when you do write one, use `//` for absolute paths.

## A second finding: the first turn can start before the tools arrive

Agents often get extra tools from **MCP servers**, small programs the CLI starts beside the model. In headless mode on
2.1.197, Claude Code began the first turn the moment the message arrived. The MCP server was still starting
(`pending`), so the model got none of its tools for that turn: in our runs, 0 of its 7 tools. Holding the first message
for a few seconds fixed it, and the studio's harness now holds it for 10.

On 2.1.280, the server was connected with its tools at the first turn in 3 of 3 starts, with no hold. An earlier note
that 2.1.280 also started early didn't reproduce, so it's marked disputed, not wrong. Either way, check the start event:
the server should say `connected`, with its tools listed.

## How we got it wrong twice

This finding was corrected twice in one day, and the corrections are part of the record.
- **First:** our original probe used the `~/**` form and searched at the home folder. We read that as "only a search at
  the denied folder itself leaks", and narrowed the claim.
- **Second:** a re-probe with the absolute form showed the folder itself refused and the folder above leaking. We read
  that as the opposite.
- **Then** we ran both forms side by side, which gave the table above. Each earlier reading had been right for one
  spelling of the rule, and wrong to generalise. Nothing in the record is marked wrong; every claim now names its rule
  form and CLI version.

The lesson we took: don't narrow or widen a measured claim until a probe separates every case it covers.

## Where the figures come from

- **The probes:** Claude Code in the studio's `atlas-pilot` Docker sandbox, on the Claude plan
  with claude-haiku-5-5. 13 short turns in all on 2026-10-20: 6 for the deny-rule searches (Grep the only tool), 6 for the MCP start and 1
  for a tracing run. The original probe ran on 2026-10-13.
- **The entries:**
  [Claude Code: a Read deny rule doesn't stop a Grep walk over the denied tree](https://github.com/mcp-tool-shop-org/rnd/blob/main/entries/2026/2026-10-13-claude-code-read-deny-rules-do-not-stop-a-grep-walk.md)
  and
  [Claude Code starts a turn before its MCP servers connect](https://github.com/mcp-tool-shop-org/rnd/blob/main/entries/2026/2026-10-13-claude-code-starts-a-turn-before-mcp-servers-connect.md).
  Every claim there is marked verified or not, with what checked it.
- **The knowledge base:** the same findings are wave 1 of the new `agent-tooling-knowledge` base in
  [readouts](https://github.com/mcp-tool-shop-org/readouts).
- **Not published:** the raw run receipts. They carry session identifiers and, in one case, an account email. They're
  kept privately and named in the entries by their SHA-256.
- **Claude Code's own account:** the [permissions documentation](https://code.claude.com/docs/en/permissions), read
  2026-10-20.
