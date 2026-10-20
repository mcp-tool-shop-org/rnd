---
id: 2026-10-20-live-testnet-runs-surface-defects-in-layers-each-fix-exposed
title: Live testnet runs surface defects in layers: each fix exposed the next
date: 2026-10-20
kind: finding
relevance: act
fields: [testing, payments]
tags: [xrpl, xrpl-lab, live-fire, testnet, acceptance-test]
---

## Summary

xrpl-lab 2.6.0's new AMM module (#30, `amm_liquidity_101`) passed 1,985 offline tests against mocks. It then took
three live runs on XRPL Testnet to pass once. Each run failed on a defect that the previous defect had hidden:
- a funding race and a dropped hash hid an over-sized pool;
- the false "not funded" answer that caused extra funding hid the sizing bug;
- the module's own status hid all of it, by reporting success.

Mocks couldn't have shown any of the three, because each depends on what the live network does: held results, a
faucet's grant, ledger reserves.

## Key points

- **Run 1 (on 7acc67c): FAIL, no AMM created.**
  - The faucet reply carried no usable balance, so the code read three successful fundings as failures. It funded
    the wallet three times, 300 XRP.
  - The issuer's AccountSet (DefaultRipple) went out before the issuer was on a validated ledger, and never
    validated. AMMCreate, the deposit and the withdraw were then held as `ter` results: `terNO_RIPPLE`, then
    `terNO_AMM`.
  - xrpl-py's `submit_and_wait` waits on a held result until the 20-ledger window closes, about 80 s. The 60 s
    client timeout fired first and discarded both the hash and the result.
  - The report said "Transactions: 2 successful, 0 failed".
- **Run 2 (on f803a49, with run 1's fixes): FAIL, one layer deeper.**
  - The fixes: wait for the validated balance, sign before submitting so the hash survives, and a 150 s timeout.
  - All of them held on the ledger. But AMMCreate validated `tecUNFUNDED_AMM`.
  - The module pools 100 XRP. One faucet grant is 100 XRP, and after the 1 XRP base reserve, the trust-line
    reserve and the 0.2 XRP create fee, only about 98.6 XRP can be spent.
  - Run 1's 300 XRP of accidental funding had hidden this.
  - The AMM steps never reported their result, so the report said "Steps: 16 passed, 2 failed" and
    "Transactions: 3 successful, 0 failed". The process exited 0.
- **Run 3 (on 453d361, with run 2's fixes): PASS.**
  - The fixes: 25/25 create and 5/5 deposit, a reserve preflight, failure counted from the transaction record, and
    exit 3 on an unverified run.
  - All 9 transactions validated `tesSUCCESS`. The AMMCreate fee equalled `reserve_inc` (200,000 drops).
  - AMMDeposit (`tfTwoAsset`) and AMMWithdraw (`tfWithdrawAll`) were accepted.
  - The pool went 25/25 → 30/30 → deleted. `amm_info` then returned `actNotFound`.
  - The run exited 0, with "18 passed, 0 failed" and `verified: true`.

## Studio relevance

- **For any studio tool that writes to a ledger or an external service,** budget for several live acceptance runs,
  not one. Write each run's receipt even when it fails, because run N's failure is often what makes run N+1's defect
  readable.
- **Two habits paid off here:**
  - keeping every hash, and re-checking with read-only `simulate` calls after a failed run;
  - making the product's own status honest before trusting a green.
- **Two silent-failure patterns to look for in other XRPL code:**
  - a client timeout shorter than the transaction's ledger window;
  - a faucet response treated as proof of funding.

  xrpl-lab#20 lists 11 more handlers with the same funding race.
- **The release:** a fourth run, on the code Argon passed in its second review, also passed (9 of 9 tesSUCCESS, pool
  deleted, exit 0). xrpl-lab 2.6.0 was released from #19's merge commit (036c187) on 2026-10-20, to PyPI, npm and GitHub with binaries.

## Claims

- [verified] Module #30's first live run on XRPL Testnet (xrpl-lab 7acc67c) created no AMM: the wallet was funded three times (300 XRP) while each funding was reported as failed, the issuer's AccountSet never validated, and AMMCreate, AMMDeposit and AMMWithdraw hit the 60 s client timeout with no hash recorded (terNO_RIPPLE / terNO_AMM by simulate afterwards); the report said "2 successful, 0 failed". (via: xrpl-lab main docs/receipts/2.6.0-amm-live-fire/run-1-f9-20261020T2056Z and its README, read by R&D, 2026-10-20)
- [verified] The second run (f803a49), with funding and hash handling fixed, validated AMMCreate as tecUNFUNDED_AMM (1C14C1C3…08A1F5, ledger 21692864, fee 200000 = reserve_inc) because the module pooled 100 XRP from a single 100 XRP faucet grant; the report said "16 passed, 2 failed" and "3 successful, 0 failed", and the process exited 0. (via: the run-2 receipt folder and README, read by R&D, 2026-10-20)
- [verified] The third run (453d361) passed: 9 of 9 transactions tesSUCCESS, AMMCreate 25/25 at a fee of reserve_inc, AMMDeposit with tfTwoAsset and AMMWithdraw with tfWithdrawAll accepted, and after the sole LP's full withdraw the AMM was deleted and amm_info returned actNotFound. (via: the run-3 receipt folder and README, read by R&D, 2026-10-20)
- [verified] A fourth run (9630389, code identical to the 35de678 Argon passed) also passed: 9 of 9 transactions tesSUCCESS, the pool deleted after the full withdraw with amm_info actNotFound after, exit 0, 18 of 18 steps passed. (via: the run-4 receipt folder and README on xrpl-lab main, read by R&D, 2026-10-20)
- [verified] xrpl-py's submit_and_wait waits on a held (ter) result until the transaction's LastLedgerSequence passes, about 20 ledgers; a shorter client timeout loses the hash and the preliminary result. (via: the run-1 receipt and xrpl-lab's fix in f803a49, reviewed by R&D, 2026-10-20)

## Sources

- [primary] https://github.com/mcp-tool-shop-org/xrpl-lab/tree/main/docs/receipts/2.6.0-amm-live-fire — the four run receipts and their README, on xrpl-lab main (merged in #19, released as 2.6.0)
- [primary] https://github.com/mcp-tool-shop-org/xrpl-lab/pull/19 — xrpl-lab PR #19 (2.6.0), the fixes between runs
- [rig] The four live runs, executed by the Book Keeper seat on the Robot rig against XRPL Testnet, 2026-10-20
- [primary] https://github.com/mcp-tool-shop-org/xrpl-lab/issues/20 — the remaining handlers with the same funding race
