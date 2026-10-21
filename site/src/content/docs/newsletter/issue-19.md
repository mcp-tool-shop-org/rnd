---
title: "Passes that weren't"
description: Two more xrpl-lab releases, 2.6.2 and 2.7.0, and the same lesson from five directions. A correct lesson left its own result out of the record. The offline simulator handed out ten times testnet's money. A library upgrade changed which account a key signs as. A clock ran ahead of the ledger. And our own test sweep "passed" every lesson after one step. Here's what each one looked like, and what caught it.
issue: 19
date: 2026-10-21
highlights:
  - "<strong>A correct lesson, missing from its own record.</strong> Twelve lesson steps that teach a rejected transaction got the rejection right on the ledger, but left it out of the course's record. A receipt couldn't show that the failure was the expected one."
  - "<strong>The simulator gave out ten times the money.</strong> Offline wallets started with 1,000 XRP; testnet gives 100. One lesson's pool needed all of a real wallet's 100, and only the live network could say so."
  - "<strong>An upgrade that changes who signs.</strong> The XRPL library's new major version reads some keys differently. The course's own wallets were unaffected, but an imported one would have signed as a different account. 2.7.0 keeps it on its account, or refuses."
  - "<strong>Our own sweep passed after one step.</strong> Our offline check of all 32 lessons ran with no keyboard attached. Every lesson stopped at its first \"Press Enter\" and still reported success. A fix in 2.7.0 is what exposed it."
---

[xrpl-lab](https://github.com/mcp-tool-shop-org/xrpl-lab) is the studio's hands-on course in the XRP Ledger. Its lessons
run real transactions on the public test network, XRPL Testnet, and can also run offline against a built-in simulator.
[Issue 18](/rnd/newsletter/issue-18/) followed 2.6.0 and 2.6.1, where live runs kept finding defects that offline tests
had passed. This issue follows the next two releases. Almost everything here was a pass that wasn't one.

## A correct lesson, missing from its own record

Some lessons exist to show a rejection: a duplicate credential, a payment to an account that requires a tag, an
escrow that isn't allowed yet. 2.6.1 taught the course to tell an expected rejection from a real failure. Each of
those steps now checks for the one code it teaches.

2.6.1's live run turned up a gap. In 12 of the 19 steps that teach a rejection, the transaction was rejected exactly
as taught, but the step never wrote it into the course's record of transactions. So:
- the lesson passed;
- the run's summary didn't count the rejection;
- the proof pack, the file a learner keeps as evidence, didn't list it.

A receipt couldn't show by itself that the failure was the one the lesson wanted.

2.6.2 records every one of them and marks it `expected`. Its release run passed all 14 lessons: 13 live on testnet
and one offline. In every lesson the summary's "N failed" was exactly its expected rejections. Of those 19
rejections, 17 were confirmed on the ledger with the codes the lessons teach. The other two, a malformed
transaction and a multisig quorum failure, never reach a ledger by design.

## The simulator gave out ten times the money

Offline, a new wallet got 1,000 XRP. On testnet the faucet gives 100. We set the simulator to 100, and one lesson
stopped working offline. Its trading pool asked for 100 XRP, all of a fresh testnet wallet's money, before the
balance a wallet must keep in reserve. On testnet that pool could never have been created. The pool is now 25 XRP
each side, as in issue 18's AMM lesson.

The same pass turned up three more simulator gaps:
- **A stand-in address.** Second wallets, such as a buyer or a sender, had their transactions filed under one
  stand-in address the faucet never funded. A test now runs all 32 lessons and checks nothing lands there; two failed
  it before the fix.
- **The wrong unit.** An escrow of 10 XRP was reported as "10 drops", a millionth of the amount.
- **A crash.** On Windows, one lesson crashed when its output went to a file, because of an arrow character.

## An upgrade that changes who signs

2.7.0 moves to version 5 of xrpl-py, the Python library the course uses for the ledger. Version 5 fixed a
long-standing bug. Version 4 turned every secret key into the same kind of keypair, so a key of the other kind, such
as one imported from another tool, signed as the wrong account. Version 5 reads the kind from the key itself.

For the course, that fix is a hazard. We measured both versions on one test key:
- every wallet the course creates turns into the same account on both versions;
- a key of the other kind turns into two different accounts.

A learner who imported such a key under version 4 has their funds and history on the old account. Under version 5,
with no change in the course, they would sign as an empty stranger.

We asked an outside reviewer, Google's Gemini, to choose between two designs:
- keep version 4's behaviour, the wrong account included;
- read the key the new way, and fall back to the old account only when that's the one on record.

It chose the second, and added a rule: if neither account matches the record, refuse, and sign nothing.

Its first review of the build found two gaps. One wallet path never recorded the address to check against, and 13
signing methods dropped the address they were given. Both are fixed.

## The clock and the ledger

A live run of 2.7.0 on one lesson per kind of transaction passed 10 of 11. The eleventh was an escrow that can be
released only after a set time. The release was rejected with `tecNO_PERMISSION`, "not yet".

The receipts show why. The ledger releases an escrow only once the previous ledger's close time is strictly after
the release time. When the release went out, that close time was exactly equal to it. The lesson had checked the
computer's clock instead, which runs 1 to 2 seconds ahead of the ledger on our rig. So it decided the time had passed
and didn't wait.

The lesson now waits until a validated ledger has closed after the release time. On the rerun the release succeeded,
in a ledger whose previous close was 10 seconds after the release time. That timing code dates from 2.4.0, and
this lesson had no earlier live run on record.

The same run found three more:
- **A refusal reported as success.** The course correctly refused to sign with a mismatched key, and the wallet file
  was left byte-identical, but the program exited with code 0, which tells a script "success".
- **`--force` did nothing.** The option to redo a finished lesson did nothing on testnet, and had done nothing since
  the course's first version.
- **An undercount.** One lesson's summary said 4 transactions where the ledger recorded 6.

## Our own sweep passed after one step

The early-exit fix is what exposed our own mistake. Before each review we ran all 32 lessons offline from the command
line and counted the exits: all 0. But that sweep ran with no keyboard attached. Every lesson stopped at its first
"Press Enter to continue", printed "Module interrupted", and exited 0. It looked like 32 passes, and it checked
almost nothing.

We had cited that sweep in two releases' notes and in our reviewer's briefs. The claim itself held: a separate
automated test runs every lesson to the end and confirms it finished. But the evidence we named was wrong. Once 2.7.0
made an interrupted run exit 130 instead of 0, the sweep failed all 32 at once.

Run again with Enter fed to every prompt, the sweep completed and verified all 32. We've corrected the record on both
releases. We now check that each run reached its end, not just its exit code.

## Where it landed

2.6.2 is released, and 2.7.0 has passed four rounds of outside review and a live rerun of every fix. The course's
tests stand at 3,440, with coverage at 97%. The course now treats a refusal, an interruption or a missing record as
the failure it is, not a quiet pass.

## Method and limits

One course, one network (XRPL Testnet), runs over one day by one studio seat on the studio's rig. Each live run used
a fresh, isolated home folder, and no wallet secret appears in any receipt. The test key for the upgrade was
generated for the measurement and never funded. Figures are from the receipts, the ledger and the course's tests.

Sources: the pull requests [xrpl-lab #22](https://github.com/mcp-tool-shop-org/xrpl-lab/pull/22) (2.6.2) and
[#23](https://github.com/mcp-tool-shop-org/xrpl-lab/pull/23) (2.7.0), the follow-up list in
[#20](https://github.com/mcp-tool-shop-org/xrpl-lab/issues/20), and the run receipts in xrpl-lab's
[`docs/receipts/`](https://github.com/mcp-tool-shop-org/xrpl-lab/tree/main/docs/receipts).
