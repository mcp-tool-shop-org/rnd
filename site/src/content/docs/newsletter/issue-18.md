---
title: "Testing the course we'd already shipped"
description: xrpl-lab's new AMM lesson passed nearly two thousand offline tests, then took four live runs to pass on the real XRPL Testnet. Once 2.6.0 was released, we kept running it live, and found more than all the offline testing had, including that the course's first lesson couldn't run on the real ledger at all. Here's what each round found, why every honest fix uncovered the next defect, and what 2.6.1 changed.
issue: 18
date: 2026-10-21
highlights:
  - "<strong>Two thousand offline tests, then four live runs.</strong> xrpl-lab 2.6.0's AMM lesson passed every simulated test, and needed four runs on XRPL Testnet to pass on its final code. Each failure had hidden the next."
  - "<strong>The released course was tested again, live.</strong> Ten lessons that create a second wallet were run on testnet after 2.6.0 shipped. Eight finished with failed steps, and one of the two that passed was passing for the wrong reason."
  - "<strong>The first lesson couldn't run on the real ledger.</strong> It paid \"self\", a word nothing turned into an address, and XRPL rejects a payment to yourself anyway. The offline simulator accepted it."
  - "<strong>Honest status kept exposing old faults.</strong> Each time the course reported its results more truthfully, an older defect became visible. 2.6.1 passed 14 of 14 lessons live, with test coverage up from 78% to 96%."
---


[xrpl-lab](https://github.com/mcp-tool-shop-org/xrpl-lab) is the studio's hands-on course in the XRP Ledger. Each
lesson walks a learner through real transactions on the public test network, XRPL Testnet, and can also run offline
against a built-in simulator. This issue follows one release and the one after it.

## 2.6.0: four live runs for one lesson

Version 2.6.0 made module #30 live for the first time. In it the learner creates an **automated market maker** (AMM),
a pool of two assets that trades against itself, deposits into it, and withdraws again. The new code passed 1,985
offline tests. Before releasing it, we ran the lesson on the real Testnet.

- **Run 1 created nothing.** The faucet's reply carried no balance the code could read, so it decided each funding had
  failed and asked again: the wallet was funded three times, 300 XRP. The token issuer's first transaction went out
  before its account was confirmed and never landed. Every later step was then held by the network, and the client
  gave up at 60 seconds, about 20 seconds before the network would have answered, throwing away the hash and the
  result code. The report said "0 failed".
- **Run 2 found what the extra money had hidden.** With funding fixed, the pool's creation failed outright: the lesson
  tried to pool 100 XRP, and a fresh wallet gets 100 XRP once, of which it must keep some in reserve. The report
  counted the pool steps as passed and exited 0.
- **Runs 3 and 4 passed,** run 4 on the code an outside reviewer had passed: 9 of 9 transactions succeeded, and the
  pool was created, used and deleted.

Mocks couldn't have shown any of it. A simulated network answers however the test was written; the real one holds
transactions, grants a fixed amount, and enforces its own reserves.

## After the release: testing what we'd shipped

2.6.0 shipped, and we kept running the released course live. Ten other lessons create
a second wallet, such as a payment receiver, a buyer or a second token issuer, and had the same funding pattern that
broke run 1. We ran all ten on testnet.

**Eight of the ten finished with failed steps.** The run found four kinds of defect:
- **The same race, in four lessons.** The second wallet was used before the network had confirmed its funding.
- **Correct lessons marked as failed.** Some lessons exist to show a rejection, such as a duplicate credential or a
  refused permission. 2.6.0's new honest status counted their expected rejection as a failure.
- **A pass that wasn't.** The checks lesson reported its expected rejection, but that transaction had never reached the
  ledger. Only the way the result was read made it look like the lesson's outcome.
- **Plain bugs, invisible offline.** Payment-channel claims always failed, because the code read the channel's key in
  the wrong format. Credential-gated payments couldn't be signed, because of a field-name bug in the XRPL library we
  use. And two lessons with an NFT sale priced the item at a buyer's entire faucet grant.

A second sweep, after the fixes, passed nine of ten. The tenth, the credentials lesson, finished unverified in both
sweeps, and the second showed why: one of its steps had been passing for the wrong reason all along. Its "unfunded"
account was a well-known example address that is funded on testnet. Only the stricter status from the first round's
fixes caught it.

## The offline simulator had its own blind spots

Running every lesson offline turned up two more problems:
- **Five lessons failed their own checks in the simulator,** also on 2.6.0. The simulator filed most of a learner's
  actions under a stand-in address the faucet never funded, so its balance went negative and its object counts were
  wrong.
- **The course's first lesson couldn't run on the real ledger.** It, and two others, sent their practice payment to
  "self". Nothing turned that word into an address, so the real network couldn't even sign the payment. Sending it to
  the learner's own address wouldn't have worked either: XRPL rejects a payment to yourself. The simulator accepted it.

The lessons now pay a fresh practice address made for each run; the first payment creates that account.

## Coverage, and the reviewers

We also brought the course's test coverage from 78% to 96%, with four AI agents writing 1,135 tests. Each test checks
behaviour, not just that code runs, and none touches the network. Writing them found four more bugs, including a
`send` command that reported success after a failed payment.

Two review passes caught what we'd missed:
- **An internal review** found seven lesson steps, across six lessons, that would accept any rejection as their
  lesson, so an unrelated failure could pass. Each now accepts only the code it teaches.
- **An outside model's review** (Google's Gemini, over two rounds) found that one kind of expected failure could still
  hide a real one, and that the "validated" flag was set by default where it should have been earned.

One defect came from a fix of our own. Our first fix for run 1 decided a step had failed by looking at a field that
only 2 of the 66 handlers that submit transactions set. It passed its own test, because the test was built to match it, and it marked the failure lesson's
deliberate rejection as a failure.

## Where 2.6.1 landed

The final release run passed **14 of 14 lessons live** on the reviewed code: the ten two-wallet lessons, the AMM lesson
and the three first lessons. Every rejection on the ledger was the one its lesson teaches. All 32 lessons also pass
offline, and coverage is held at 90% or more from now on.

What made each failure readable in time to fix it:
- **Receipts for every run, failures included.** Each run kept every transaction hash, and failed runs were checked
  afterwards with read-only queries.
- **Making the course's own status honest before trusting a green result.** Each time we did, an older defect showed.

## Method and limits

One course, one network (XRPL Testnet), runs on two days, by one studio seat on the studio's rig. Each run used a
fresh, isolated home folder, and no wallet secrets appear in any receipt. The figures are from the receipts and the
ledger.

Sources: the studio's research note,
[`2026-10-20-live-testnet-runs-surface-defects-in-layers-each-fix-exposed`](https://github.com/mcp-tool-shop-org/rnd/blob/main/entries/2026/2026-10-20-live-testnet-runs-surface-defects-in-layers-each-fix-exposed.md),
and the run receipts in xrpl-lab's
[`docs/receipts/`](https://github.com/mcp-tool-shop-org/xrpl-lab/tree/main/docs/receipts) (2.6.0 in
[#19](https://github.com/mcp-tool-shop-org/xrpl-lab/pull/19), 2.6.1 in
[#21](https://github.com/mcp-tool-shop-org/xrpl-lab/pull/21)).
