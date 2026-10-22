---
title: "Watching 0.2 XRP lock and come back"
description: "XRPL Camp 1.5.0 adds a lesson you can run after the course: mint an NFT and burn it, and watch your spendable XRP fall by the owner reserve and come back. On the live test network it does exactly that. Getting there meant answering two quieter questions: what a zero means when you measure money, and when a tool should write a receipt into your proof."
issue: 23
date: 2026-10-22
highlights:
  - "<strong>Held, not spent.</strong> Minting an NFT left the balance down by the 10-drop fee and the spendable XRP down by 200,010 drops. Burning it brought back 199,990. Over the round trip, only the two fees were gone."
  - "<strong>A zero has two meanings.</strong> If an account already holds an NFT, a new one can join an existing page and lock nothing new. A slow server can also show no change. The tool now tells these apart from the numbers it already reads, rather than calling both 'locked'."
  - "<strong>Receipts only for what was confirmed.</strong> A proof file can now carry dated receipts of past checks, but only when the ledger confirmed it. The first build would have written a receipt saying a contradicted file 'passed'."
---

[XRPL Camp](https://github.com/mcp-tool-shop-org/xrpl-camp) teaches the XRP Ledger in one sitting. It runs six lessons on
the public test network, and ends with a certificate and a proof file anyone can check against the ledger. Version
1.5.0 adds three things the camp had built but never switched on. The most visible is a command that shows one of the
ledger's less intuitive rules happening to your own account.

## The rule: owning things locks XRP

Every account on the XRP Ledger must keep a minimum balance, its **reserve**. There are two parts:
- a base reserve for existing at all, 1 XRP on the test network when we measured;
- an **owner reserve** of 0.2 XRP (200,000 drops) for each object the account owns, such as a trust line or a page of
  NFTs.

The reserve isn't a fee. It isn't spent. It's held while you own the object, and released when you give it up. Your
**balance** stays the same, but your **spendable** XRP doesn't.

## The demo, measured

`xrpl-camp reserve` mints one NFT from the learner's wallet, then burns it, and shows both numbers side by side. Here's
the run that checked the release, read back from the ledger afterwards:

| Step | Objects owned | Balance (drops) | Spendable (drops) |
|---|---|---|---|
| Mint an NFT | 0 → 1 | −10 | −200,010 |
| Burn it | 1 → 0 | −10 | +199,990 |

The balance only moved by the fee: 10 drops for each transaction. The spendable XRP moved by the fee *plus* 200,000
drops on the way in, and got the 200,000 back on the way out. Over the round trip, 20 drops are gone, and the reserve
returned in full. The transaction records on the ledger agree with every number in the table.

## What a zero means

While the release was being reviewed, a question came up about the case where the demo shows **no reserve change at
all**. There are two ways that happens, and they mean different things.

1. **The NFT joined an existing page.** The ledger doesn't charge the owner reserve per NFT. It charges it per **NFT
   page**, a container holding up to 32 tokens. An account that already holds an NFT with room on its page mints the new
   one into that page, and locks nothing new. That's a true zero.
2. **The server hadn't caught up.** If the read after the mint reaches a server that hasn't yet seen the validated
   ledger with the mint in it, the numbers come back unchanged. That reads as a zero too, but it's a stale read, not a
   fact about reserves.

The first build called every zero "the token went into an existing page". The fix uses numbers the demo already has:
- **a shared page** needs the account to have owned something before, the object count to stay the same, *and* the fee
  to have been paid, which proves the read came after the transaction;
- **anything else that reads zero** is reported plainly: the ledger read after the mint didn't show the transaction
  yet, so the change couldn't be measured, and here is the transaction link.

## Receipts, and when not to write one

The camp's proof file is sealed with a hash, so any edit shows. `proof verify --online` also asks the ledger whether
the transactions in the file really happened. Version 1.5.0 can record each such check as a dated **receipt** inside
the file, outside the seal. A file then gathers a short history of being checked over the years. That matters on a
test network, which is reset from time to time, so old transactions eventually stop resolving.

Every receipt carries a disclaimer. It's self-reported: a copy of the tool said this passed on this date, and it proves
nothing on its own.

Review caught a problem with the first build: it wrote a receipt whatever the ledger answered. A file the ledger had
*contradicted* would have gained a receipt saying it passed. So did a file whose check couldn't reach the network.

Now a receipt is written only when the ledger **confirmed** the file. Any other answer leaves the file byte-for-byte
unchanged and says why. The release check tried a forged file, re-sealed with a fresh hash: it was contradicted,
refused a receipt, and left unchanged.

## Also in 1.5.0

- `certificate --format text` writes a plain-text keepsake beside the machine-readable certificate.
- Every sealed certificate prints a short block you can copy and paste. It names the proof command, so a reader can
  check the claim rather than take it on trust.

*How it was checked:*
- **Four review rounds** on the code by a second model, Gemini, and a review by the studio's R&D seat.
- **A live check on the test network** by a separate seat, with the receipts committed in the repository
  (`docs/receipts/1.5.0-live-check/`).
- **The XRPL's rules on reserves and NFT pages:** xrpl.org, "Reserves" and "NFTokenPage".
