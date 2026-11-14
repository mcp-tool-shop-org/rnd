---
id: 2026-11-13-xrpl-lab-expansion-seed-20
title: Expanding xrpl-lab: the Testnet reset deadline and a corrected module plan (seed 20)
date: 2026-11-13
kind: finding
relevance: act
fields: [xrpl, education]
tags: [xrpl-lab, testnet-reset, amendments, seed-20, harvest]
---

## Summary

The studio asked a Gemini Deep Research run for an evidence-based expansion plan for xrpl-lab, its 32-module XRP
Ledger teaching lab, with the lab's overview attached. The report is AI output (`[aggregator]` throughout), and
R&D checked the claims a decision rests on against xrpl.org and the lab's code. Two things stood out. First, a real
deadline: the XRPL Testnet and Devnet are wiped on 2026-11-25, which would make every learner certificate issued
before then fail a live check. Second, the report's top-ranked modules rest on amendment status it could not have
had right, so wave 1 was re-ranked.

## Key points

- **Testnet and Devnet reset, Wednesday 2026-11-25.** All accounts, transactions, balances, offers, AMMs and escrows
  are erased and Testnet amendments are restored to Mainnet's; the cause is the crash of the single full-history
  server. Mainnet is unaffected. The announcement page shows no publication date.
- **xrpl-lab today:** v2.7.9 (released 2026-10-22). It stamps no network or genesis identity into state, proof packs
  or certificates, and it does not use the `simulate` RPC (its "simulated" txids come from the offline dry-run). A
  faucet override exists (`XRPL_LAB_FAUCET_URL`, and `XRPL_LAB_RPC_URL`).
- **The report was stale on one point:** the AppleDouble `._` filter it calls deferred had already landed (#52).
- **Amendment status, from xrpl.org's Known Amendments page** (data snapshot 2026-09-16, read 2026-11-13): Batch and
  fixBatchInnerSigs are obsolete (removed in 3.1.1 for a severe bug); a revised Batch was "expected 2026-09-29" and
  its fix is inactive; PermissionDelegation is obsolete (removed in 2.6.1) and its revised version was open for
  voting at 62.86%; PriceOracle, TicketBatch, DeepFreeze and AMMClawback are enabled. The report's claim that both
  revised amendments were enabled in October 2026 is unchecked, and the page snapshot predates it.
- **Not checked:** vote counts and enable dates beyond the snapshot, a reported exchange drain, CVE numbers, and
  whether 11 of 32 modules lack prerequisites. Each must be checked at source before any module text states it.
- **The teaching research it cites** (worked examples, predict-then-run, backward fading, goal-state checks) is real
  and well known, but its effect sizes are the report's numbers and were not checked.

## Studio relevance

### What it contradicts in our design (read first)

| Finding | xrpl-lab today (checked) | Decision | Owner |
|---|---|---|---|
| Testnet wipe on 2026-11-25 | No network or genesis stamp; a live verify would read a wiped ledger as missing transactions | Ship reset resilience before 11-25 as the first change | Book Keeper |
| Use `simulate` to predict failures | Not used; the dry-run is a local mock | Wave 2 adds it; wave 0 does not need it | Book Keeper |
| AppleDouble filter deferred | Already landed (#52) | Drop from the plan; the report is stale | Book Keeper |
| Repeated faucet calls per module | Not checked which modules call twice | Check, then fund helper wallets from the learner's own wallet | Book Keeper |
| Testnet mirrors Mainnet amendments | n/a | Any pre-Mainnet module stays dry-run or local-node only | Book Keeper |

### Decisions taken (the Publisher and R&D, 2026-11-13)

1. **Wave 0, before 2026-11-25:** stamp network id, the earliest complete or genesis ledger hash and the validated
   ledger index into state, the proof pack and the certificate; make the live verify commands report "ledger reset
   after issuance; offline hash intact" rather than a failure that looks like forgery; have `doctor` and `recovery`
   detect a reset and re-fund and rebuild. The same applies to the sister lab repo and any game ledger-proof
   receipts (the game's backpack has no network transport today, so nothing there breaks yet).
2. **Fund helper wallets from the learner's wallet** rather than repeated faucet calls.
3. **Wave 1 modules are re-ranked:** long-enabled features first (regular keys and blackholing, Tickets, Price
   Oracles, cross-currency paths, issuer architecture with DefaultRipple, DisallowIncoming, Deep Freeze and
   AMMClawback); Batch and Permission Delegation only if the `feature` RPC on Testnet shows them enabled, checked
   again after the reset. Each module is checked against xrpl.org when written.
4. **Later waves:** runner upgrade (predict, worked run, read metadata, faded template, goal-state grading), a local
   stand-alone node mode with recorded RPC cassettes for CI, and security hardening (a secret check on exported
   bundles, token auth when the server leaves loopback, hash-pinned builds).
5. **Mainnet regulatory notes** (pooled player wallets as possible money transmission) are legal text that will be
   relied on, so they need one targeted check before shipping (Standing Rule 3).
6. **Out of scope or held:** pre-Mainnet features (local-node previews only, later), the cross-chain bridge (skip),
   an MCP server, on-ledger certificates and grants (backlog ideas), and README translations (on hold).

All work stays on Testnet, dry-run or local. relevance: `act` (the reset deadline is 2026-11-25).

## Claims

- [verified] The XRPL Testnet and Devnet are wiped on Wednesday 2026-11-25; all accounts, transactions, balances, offers, AMMs and escrows are erased, Testnet amendments are restored to Mainnet's, and Mainnet is unaffected (via: xrpl.org's testnet-devnet-reset blog post read with WebFetch, R&D, 2026-11-13)
- [verified] xrpl-lab's latest release is v2.7.9, dated 2026-10-22 (via: gh release list, R&D, 2026-11-13)
- [verified] The AppleDouble glob filter landed in xrpl-lab #52, so the report's "deferred" is stale (via: xrpl-lab main, `modules.py`, R&D, 2026-11-13)
- [verified] xrpl-lab does not use the `simulate` RPC and stamps no network or genesis identity into state, proof packs or certificates (via: grep of main, R&D, 2026-11-13)
- [verified] xrpl-lab has a faucet override, `XRPL_LAB_FAUCET_URL`, and an RPC override, `XRPL_LAB_RPC_URL` (via: `cli.py` and `doctor.py` read, R&D, 2026-11-13)
- [verified] xrpl.org's Known Amendments page (snapshot 2026-09-16) lists Batch and fixBatchInnerSigs obsolete, PermissionDelegation obsolete and its revised version at 62.86% in voting, and PriceOracle, TicketBatch, DeepFreeze and AMMClawback enabled (via: the page read, Publisher and R&D, 2026-11-13)
- [unverified] Both revised amendments (Batch V1.1, PermissionDelegation V1.1) were enabled in October 2026 (the report; the page snapshot is older than the claimed dates, so only the `feature` RPC on Testnet can settle it)
- [unverified] 11 of xrpl-lab's 32 modules have no prerequisites (not checked; the frontmatter field name differed from the grep)
- [unverified] Amendment vote counts and enable dates, an exchange drain and CVE numbers in the report (not checked)
- [unverified] The effect sizes for worked examples, predict-then-run and backward fading cited from the teaching research (the report's numbers)

## Sources

- [aggregator] https://gemini.google.com/app/3ec4bd9fe7c8dfb8 — Gemini Deep Research report "Evidence-Based XRPL Lab Expansion" (seed 20, 2026-11-13; account-private chat)
- [primary] https://xrpl.org/blog/2026/testnet-devnet-reset — xrpl.org (Testnet and Devnet reset notice)
- [primary] https://xrpl.org/resources/known-amendments — xrpl.org (Known Amendments, data snapshot 2026-09-16)
- [primary] https://github.com/mcp-tool-shop-org/xrpl-lab — the studio's xrpl-lab repo (releases, code)
