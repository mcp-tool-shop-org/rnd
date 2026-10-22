---
title: "The course, end to end"
description: Five more xrpl-lab releases, 2.7.1 to 2.7.5. The check that proves a learner's work had been failing honest work. A lesson that passed on its own broke the next one. And the first run of all 32 lessons in a row, the way a workshop runs them, found five more lessons that broke others or failed outright. Here's what each looked like, and how the course got to a clean run end to end.
issue: 20
date: 2026-10-22
highlights:
  - "<strong>The proof that couldn't prove.</strong> The check that verifies a learner's evidence against the live ledger failed every honest lesson that teaches a rejection, and 17 of 25 real evidence files on a second, older rule."
  - "<strong>A lesson that passes alone can break the next one.</strong> One lesson left a setting on the learner's wallet, and the next lesson in the course couldn't pay them."
  - "<strong>All 32 lessons in a row.</strong> The first live run of the whole course in one wallet found 10 lessons failing. Eight passed when run alone: an earlier lesson had broken them."
  - "<strong>Clean end to end.</strong> After two more releases, all 32 lessons pass in one run on the live test network, and the evidence file verifies against the ledger with no failures."
---

[xrpl-lab](https://github.com/mcp-tool-shop-org/xrpl-lab) is the studio's hands-on course in the XRP Ledger. Its
lessons run real transactions on the public test network, XRPL Testnet, and can also run offline against a built-in
simulator. [Issue 19](/rnd/newsletter/issue-19/) followed 2.6.2 and 2.7.0, where several checks passed that shouldn't
have. This issue follows the next five releases. Most of it is about what happens between lessons.

## The proof that couldn't prove

Each lesson leaves evidence. At the end, a learner can export a proof pack, a file listing every transaction they
made. The command `proof verify --live` then looks each one up on the public ledger and confirms it is there as
claimed. That check is the reason the pack is worth anything.

2.7.1 began as two small follow-ups. While reviewing them, our outside reviewer, Google's Gemini, pointed out that
the dashboard's verify route ignored a new field. Following that path led to a bigger problem. Live verification
expected every transaction in a pack to have succeeded. So since 2.6.2, which began recording the rejections a lesson
teaches, it had failed every honest pack from a lesson that teaches one:
- a rejection that reached the ledger failed as "not a success";
- a rejection that never reaches a ledger, by design, failed as "not found".

Fixing that, the studio's live-testing seat found a second, older rule. Live verification also required every
successful transaction to be signed by the learner. But many lessons create helper wallets of their own: an issuer,
a buyer, a second player. Their transactions could never pass. Of 25 real packs from earlier live runs, 17 failed on
this alone, across 32 helper-signed transactions. Helper-signed *rejections* had been passing all along, because the
rejection path skipped the check. The rule wasn't only strict, it was inconsistent.

Now each run records the accounts it used, learner and helpers, and the pack carries them. A transaction signed by
any of them verifies.

One design choice is worth telling. An earlier proposal would have had a rerun of a lesson silently delete the
learner's earlier records. We kept them instead. Every attempt records its accounts, and the course's existing reset
command handles records from before the change. A rerun shouldn't destroy history.

## A lesson that passes alone

The same live check turned up something new. A lesson on deposit authorization turns on a wallet setting that
refuses payments from anyone not approved. The lesson passed. But it left the setting on, so the next lesson in the
same wallet, which needs to receive a token, was refused, and its trading pool had nothing to pool. The lesson also
couldn't be run twice, because its own leftover approval was still on the ledger.

2.7.2 makes it clean up after itself: it removes the approval, turns the setting off, and reads the wallet back to
check. Run live in one wallet, the next lesson then created its pool, the rerun was clean, and live verification
passed.

2.7.3 was a small fix: a rejection that reached the ledger now keeps its link to the ledger explorer in the saved
record, as the proof pack already did.

## All 32 lessons in a row

That raised an obvious question. If one lesson could break the next, what about the rest? A workshop runs the course
in order, in one wallet. Until now, live checks had run each lesson in a fresh one.

So we ran all 32 lessons in curriculum order, in one wallet, on testnet, and verified the whole pack at the end:
- 22 of 32 lessons finished cleanly;
- live verification found 104 transactions as claimed, failed 14, and skipped 11 from the one lesson that runs
  offline by design;
- no transaction failed because a helper signed it, so 2.7.1's fix held across the whole course.

Run alone in a fresh wallet, 8 of the 10 failing lessons passed. An earlier lesson had broken them:
- **A setting left on.** A lesson on crediting players' deposits makes the learner's wallet refuse any payment
  without a routing tag, and left it that way. Five later lessons that pay the learner were refused.
- **A shared issuer.** The lesson on recalling tokens needs an issuer that owns nothing yet. The course reuses one
  issuer across lessons, and by then it owned plenty, so the ledger refused.
- **An empty wallet.** A wallet gets one grant from the test faucet. By the cheque lesson, the learner held
  49.99967 XRP, just short of the 50 XRP cheque.

Two lessons failed alone too:
- **The wrong signer.** A token-distribution lesson created its currency from the learner's wallet instead of the
  issuer's. An issuer can't hold its own token, so the learner couldn't opt in, and the payment had nowhere to go.
- **An invalid name.** A lesson named its currency `HYGIENE`. A currency code must be 3 characters or 40 hex
  digits, so the library refused it before signing. It had never worked live.

Why didn't the offline tests catch any of this? Each offline run starts a brand-new simulated ledger, so no lesson
ever saw what an earlier one left behind. The simulator was also more lenient than the ledger in places: it accepted
`HYGIENE`, and it let token payments through to a wallet that refuses untagged ones.

## Clean end to end

2.7.4 fixed all five. The deposit-crediting lesson now turns its setting off. The token-recall lesson makes an issuer of its
own. The cheque lesson asks the faucet for a top-up when the learner is low. The distribution lesson signs as the
issuer. And the currency is now `HYG`.

It also gave the course a new offline test that runs all 32 lessons in one simulated ledger, in order. On 2.7.3 it
fails the two lessons the live run broke for lack of money and the routing tag. We then made the simulator stricter
in the places the live run had shown it was too lenient. With the deposit-crediting lesson's cleanup removed, the
test now fails exactly the lessons the live run did.

The first live run of 2.7.4 still found two more:
- **A retry that couldn't fix the record.** Redoing a lesson with `--force` had never updated its record. A
  passing retry after a failure still read as failed. This dates from before 2.7.
- **A trust line that wouldn't go.** The cleanup lesson removes a token trust line, but the line stayed on the
  ledger, still holding its reserve. Deleting a line needs one of its flags back at its default value, and the
  course left it at the other. This had been hidden all along, because the lesson used to fail earlier on
  `HYGIENE`.

Each fix exposed the next layer. Fixed, the full course ran clean live: all 32 lessons finished, live verification
confirmed 123 transactions with none failed, and no setting was left on the learner's wallet.

## A learner's recovery should verify

One gap was left. If a lesson fails and the learner fixes it with `--force`, the pack still carries the failed
attempt's records. Live verification failed on them, so a learner who had recovered couldn't get a clean result.

2.7.5 treats a failure older than the module's passing latest run as history. If it never reached a ledger, it is
skipped. If it did, it must be on the ledger as recorded. A module whose latest run failed still fails. No new field
was needed, so packs made by earlier versions verify the same way.

Our reviewer spelled out why one detail matters. Never-submitted records all share the placeholder `failed` instead of a hash. If
they were grouped by module alone, a later interrupted run's failure could hide behind an earlier, superseded one.
So they are grouped by module and by whether they're superseded.

## Smaller moments

- **A release that failed safely.** 2.7.1's first release run stopped at npm's signing step, with "an equivalent
  entry already exists". Nothing had been published. We asked before rerunning, the rerun passed, and we checked
  every registry directly.
- **Coverage held a merge.** The test-coverage gate held 2.7.2 at 87% of the changed lines covered, against a 90%
  bar. Three tests brought it to 98%. The bar doesn't move; the coverage does.
- **Paths in the receipts.** Six lines of run output carried a folder path from our rig. They were redacted
  before merging.

## Where it landed

All five releases are out on PyPI and npm, each after outside review and a live check on the reviewed code. The
course's tests went from 3,447 to 3,556, with coverage at 97%. Two more fixes found along the way are on their way
out. One adds `--live` to `verify-artifact`, the command the old verify commands now point learners to. The other
stops the setup check from reporting a failure that a `--force` retry has already fixed.

## Method and limits

One course, one network (XRPL Testnet), runs over two days by one studio seat on the studio's rig. Each run used a
fresh, isolated home folder; no wallet secret appears in any receipt. Full-course runs used one wallet, in
curriculum order. The faucet's rate limit set the pace. We checked sample transactions from every run on the ledger
ourselves. Figures come from the receipts, the ledger and the course's tests.

Sources: xrpl-lab's pull requests [#24](https://github.com/mcp-tool-shop-org/xrpl-lab/pull/24) to
[#33](https://github.com/mcp-tool-shop-org/xrpl-lab/pull/33), the follow-up lists in
[#20](https://github.com/mcp-tool-shop-org/xrpl-lab/issues/20) and
[#28](https://github.com/mcp-tool-shop-org/xrpl-lab/issues/28), and the run receipts in xrpl-lab's
[`docs/receipts/`](https://github.com/mcp-tool-shop-org/xrpl-lab/tree/main/docs/receipts).
