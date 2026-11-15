---
id: 2026-11-15-xrpl-test-network-reset-releases
title: "Releases for the XRPL Testnet and Devnet reset: xrpl-lab 2.8.0, xrpl-camp 1.6.0, sovereignty 2.4.0"
date: 2026-11-15
kind: release
relevance: watch
fields: [xrpl, education]
tags: [xrpl-lab, xrpl-camp, sovereignty, testnet-reset, proof-packs, engineering-note]
---

## Summary

An engineering note, not an experiment. XRPL Testnet and Devnet are wiped on Wednesday 2026-11-25
([[2026-11-13-xrpl-lab-expansion-seed-20]]). Three studio tools record test-network transactions as evidence: xrpl-lab and
xrpl-camp in proof packs, sovereignty in round-proof anchors. After the wipe, each of those transactions is missing
from the ledger. Before these releases, each tool reported that as a forgery or a mismatch.

All three tools shipped a fix on 2026-11-13 (sovereignty's GitHub release is dated 2026-11-14 UTC). They share one
design: a transaction lost to a reset reads as "can't be checked". It never reads as a pass, and never as a forgery.
The verdict also names what it rests on.

Facts here come only from the three repositories: their GitHub releases, CHANGELOGs at the tags, merged PRs and one
open issue, plus the PyPI and npm registries. They were read on 2026-11-15. Anything not read is marked "not checked".

## Key points

**The releases**

| Tool | Version | Tag commit | Released to | Feature PRs | Release PR |
|------|---------|------------|-------------|-------------|------------|
| xrpl-lab | 2.8.0 | `b0b0ffe` | GitHub (Linux and Windows binaries), PyPI `xrpl-lab`, npm `@mcptoolshop/xrpl-lab` | #54, #55, #56 | #57 |
| xrpl-camp | 1.6.0 | `3c4ad65` | GitHub (macOS arm64, Linux and Windows binaries), PyPI `xrpl-camp`, npm `@mcptoolshop/xrpl-camp` | #38, #39 | #40 |
| sovereignty | 2.4.0 | `ba7ffff` | GitHub (macOS arm64, Linux and Windows binaries), PyPI `sovereignty-game`, npm `@mcptoolshop/sovereignty` | #99, #100 | #101 |

- Each tag sits on the README translations commit that followed its release PR: lab #58, camp #43, sovereignty #102.
- Each repository has a live-check receipt folder at its tag:
  - lab: `docs/receipts/2.8.0-reset-live-check-61cbd9a`;
  - camp: `docs/receipts/1.6.0-live-check`;
  - sovereignty: `docs/receipts/2.4.0-reset-live-check-1016c26`.

  Their contents: not checked for this note.
- **sovereignty 2.4.1** (#103, 2026-11-14) followed 2.4.0. The v2.4.0 release built no desktop installers, because the
  `tauri` crate and `@tauri-apps/api` were on different minor versions. Its CHANGELOG says the CLI, PyPI, npm and
  container releases of 2.4.0 were not affected.

**The reset-verdict design, common to all three**

- **Never a pass.** A transaction missing after a reset can't be checked. It is never reported as verified, in human
  output, in `--json` or in a UI. Only the offline hash is left as evidence, and the output says so.
- **Never a forgery.** The tool no longer says "not found" or "mismatch" when an announced reset explains the gap.
  - In sovereignty, a reset is reported only when the transaction is really absent. A transaction that exists with a
    different hash is still a mismatch.
- **The verdict names its signal** (`reset_signal` in lab and sovereignty, `history_signal` in camp):
  - `announced`: a reset listed in the tool's code (`resets.py` in lab and camp) covers the recorded time.
  - `seen_by_this_lab` (lab only): the lab checking the pack saw the reset in its own state.
  - `pack_claim` (lab and camp): only the pack's own numbers say so. Anyone can write those numbers, so this verdict is
    **UNCONFIRMED**. It is never upgraded to a reset, and never to a pass.
  - In lab, the two independent signals give `RESET`, and a pack's own claim gives `UNCONFIRMED`. Before release, a
    pack's own marks gave `RESET`; this changed in #56.
- **Day, not hour.** The notice gives the reset's day, not its hour. So the reset covers anything recorded before
  the 25th has ended everywhere, at 2026-11-26 12:00 UTC.
  - camp also bounds the start: from 2026-11-24 10:00 UTC, when the 25th begins anywhere.
  - lab accepts the edge in its release notes. A transaction recorded after the wipe, but before that hour, and missing
    from the ledger reads `RESET` instead of `FAIL`. It is a pass in neither case.
- **The ledger going backwards.** lab and camp both use a 1,000-ledger margin, about an hour of closes, so a server
  that lags a few ledgers is not mistaken for a reset.
  - lab records the highest validated ledger index each Testnet or Devnet run sees (`ledger_marks`), and records a
    drop of more than 1,000 (`ledger_epochs`). New packs carry both inside their hash.
  - camp treats a recorded ledger index more than 1,000 past the endpoint's newest as history gone.
- **Exit codes:**
  - lab: new code **4** for `verify-artifact --live`, for both `RESET` and `UNCONFIRMED`.
  - camp: unchanged. A reset reads as history gone, code **3**, as discarded history already did. It is a minor
    release because the status strings and `history_signal` are new.
  - sovereignty: new code **3** for `sov verify --tx` (`NET_ANCHOR_RESET`).
  - In all three, `0` still means verified and `1` still means a failure or a mismatch.
- **Recovery:**
  - lab: `xrpl-lab doctor` has a Network reset check, and `xrpl-lab recovery` lists the steps: fund the wallet again,
    then re-run the affected modules with `--force`.
  - sovereignty: `sov anchor --reanchor` sends again only the rounds whose anchor transaction is gone, and only from a
    proof whose local hash still checks out.
  - camp: not covered by its release notes.
- **Mainnet:** sovereignty's notes say Mainnet is never reset and nothing changes there. For lab and camp: not checked.

**The `valid` field follow-up**

- In both packs' `--json` output, `valid` does not mean "verified". Two handbook-only PRs, merged after the tags, say
  what it means:
  - lab #59: `valid` is the offline hash check only. Read `live_passed` or the exit code.
  - camp #41: `valid` means "not contradicted". Read exit code `0` or `online.status == "confirmed"`.
- camp's meaning dates from 1.4.2 and is documented, so it was not changed in 1.6.0 (the Publisher's ruling,
  2026-11-13, as camp #41 and #42 record it).
- **camp issue #42 (open):** a non-breaking `verified` boolean for the next minor. It would be true only when the
  ledger confirmed every checkable lesson. Whether an offline run gives `false` or omits the field is still open.

## Studio relevance

`watch`. What is left:
- The releases were checked live before the wipe; a run against the network after it is still to come.
- camp #42 is still open.
- A test-network proof is only as durable as the network. Any future studio tool that anchors evidence on a test
  network needs the same three rules from the start: never a pass, never a forgery, and name the signal.

## Claims

- [verified] xrpl-lab v2.8.0's tag is commit b0b0ffe, published to GitHub on 2026-11-13 with Linux and Windows binaries, and 2.8.0 is on PyPI (`xrpl-lab`) and npm (`@mcptoolshop/xrpl-lab`). (via: gh release view, gh api commits, the PyPI JSON API and npm view, 2026-11-15)
- [verified] xrpl-camp v1.6.0's tag is commit 3c4ad65, published 2026-11-13, and 1.6.0 is on PyPI (`xrpl-camp`) and npm (`@mcptoolshop/xrpl-camp`). (via: gh release view, gh api commits, the PyPI JSON API and npm view, 2026-11-15)
- [verified] sovereignty v2.4.0's tag is commit ba7ffff, its GitHub release is dated 2026-11-14 UTC, and 2.4.0 is on PyPI (`sovereignty-game`) and npm (`@mcptoolshop/sovereignty`); 2.4.1 followed because 2.4.0 built no desktop installers. (via: gh release view, gh api commits, the PyPI JSON API, npm view and sovereignty's CHANGELOG on main, 2026-11-15)
- [verified] In all three tools a transaction missing after an announced reset is never reported as a pass, and lab and camp report a reset claimed only by the pack as UNCONFIRMED. (via: the three release notes and CHANGELOG sections at the tags, 2026-11-15)
- [verified] lab added exit code 4, sovereignty added exit code 3 for `sov verify --tx`, and camp kept its exit codes. (via: the three release notes, 2026-11-15)
- [verified] xrpl-lab #59 and xrpl-camp #41 are handbook-only PRs saying what `valid` means, merged on 2026-11-13 after the tags, and xrpl-camp #42 (a `verified` boolean) is open. (via: gh pr view and gh issue view, 2026-11-15)
- [unverified] The reset happens on 2026-11-25 as announced. The xrpl.org notice is cited by all three releases. (not checked against xrpl.org for this note)

## Sources

- [primary] https://github.com/mcp-tool-shop-org/xrpl-lab/releases/tag/v2.8.0 — xrpl-lab 2.8.0 release notes
- [primary] https://github.com/mcp-tool-shop-org/xrpl-lab/pull/59 — `valid` against `live_passed`, handbook
- [primary] https://github.com/mcp-tool-shop-org/xrpl-camp/releases/tag/v1.6.0 — xrpl-camp 1.6.0 release notes
- [primary] https://github.com/mcp-tool-shop-org/xrpl-camp/pull/41 — `valid` means not contradicted, handbook
- [primary] https://github.com/mcp-tool-shop-org/xrpl-camp/issues/42 — a `verified` boolean, next minor (open)
- [primary] https://github.com/mcp-tool-shop-org/sovereignty/releases/tag/v2.4.0 — sovereignty 2.4.0 release notes
- [primary] https://github.com/mcp-tool-shop-org/sovereignty/blob/main/CHANGELOG.md — sovereignty CHANGELOG, 2.4.1
- [primary] https://pypi.org/project/xrpl-lab/2.8.0/ — PyPI
- [primary] https://www.npmjs.com/package/@mcptoolshop/xrpl-lab/v/2.8.0 — npm
