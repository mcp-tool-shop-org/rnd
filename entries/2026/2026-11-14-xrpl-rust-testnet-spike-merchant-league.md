---
id: 2026-11-14-xrpl-rust-testnet-spike-merchant-league
title: xrpl-rust 1.3.0 Testnet spike for Merchant League: works, not adopted
date: 2026-11-14
kind: finding
relevance: reference
fields: [blockchain]
tags: [xrpl, rust, merchant-league]
---

## Summary

Merchant League's M2 spike asked one question: can the Rust library `xrpl-rust` 1.3.0 build, sign and submit every
XRP Ledger transaction the game needs? It was tried on the public Testnet on 2026-11-14 and the answer was yes. Ten
transaction types validated, and the final ledger state matched the prediction exactly. The library was still not
adopted, because it fails the repository's security audit in a way it cannot fix. The spike's PR
(merchant-league #2) is closed unmerged. Its receipt, and the escrow-condition encoding it proved, are kept in
rnd-data.

## Key points

- **Every transaction type worked on Testnet:**
  - issuer flags (allow clawback, default ripple);
  - a trust line and a payment;
  - an offer and its cancel;
  - a check, written and cashed;
  - an escrow locked to a secret's PREIMAGE-SHA-256 crypto-condition;
  - a clawback.
- **A wrong reveal was rejected by the ledger, as designed.** Finishing the escrow with the wrong secret returned
  `tecCRYPTOCONDITION_ERROR` in a validated ledger. The right secret then finished it.
- **The final state was as predicted:** a merchant balance of 102 MRK (100 + 5 − 3), with no escrow, check or offer
  left.
- **It is not adopted.** With `xrpl-rust` in the lock, `cargo audit --deny warnings` fails on two advisories:
  - RUSTSEC-2026-0387, timing variability in `crypto-bigint` 0.5.5, in key arithmetic. The fix (0.7.6) is out of
    reach: both `xrpl-rust` 1.3.0 and its successor `xrpl-sdk` 2.0.0 require `^0.5.1`.
  - RUSTSEC-2023-0089: `atomic-polyfill` is unmaintained, and comes in through the library's own HTTP client.

  The repository fixes advisories by upgrading, never by ignoring them.
- **Other gaps in the library:**
  - A `tec` result comes back as an error without the transaction hash. In this game a failed reveal is a scoring
    event, so the hash is needed.
  - Its helper error type does not implement `std::error::Error`.
  - It grows the lock from 200 to 449 packages.
- **The alternative the receipt names:** a thin layer of our own.
  - ed25519 keys only, so key derivation needs SHA-512 and no big-integer maths.
  - Our own binary serialization for these transaction types, checked against published vectors.
  - Plain JSON-RPC submission, with each hash computed before submitting.
- **What was kept:** `league-dice` encodes the PREIMAGE-SHA-256 condition (for EscrowCreate) and fulfillment (for
  EscrowFinish), plus the finish fee. It was tested against xrpl.org's example and against an independent encoding,
  and the live escrow used it. That crate exists only on the closed branch, so a copy at 1d031a3e is in rnd-data.

## Studio relevance

`reference`. This is the evidence for Merchant League's ledger-layer decision: `xrpl-rust` works, but cannot pass
the security audit. If the game goes back to on-ledger play, start from the thin-layer alternative above and reuse
the kept `league-dice` encoding. XRPL work stays on Testnet.

## Claims

- [verified] The receipt and the encoding crate are in rnd-data as run `merchant-league--m2-xrpl-rust-spike-2026-11-14`, copied byte for byte from merchant-league PR #2's head 1d031a3e. (via: R&D's git archive of the PR head and rnd raw ingest, 2026-11-25)
- [unverified] All thirteen steps validated on Testnet ledgers 22,311,281 to 22,311,302, as the receipt records. The
  ledger history is in the receipt's `raw/02_merchant_account_tx.json`; not re-read from the network.
- [unverified] `crypto-bigint`'s fixed version is out of reach for both `xrpl-rust` 1.3.0 and `xrpl-sdk` 2.0.0, as
  the receipt's audit file and PR text state; not re-checked against crates.io today.

## Sources

- [primary] https://github.com/mcp-tool-shop-org/merchant-league/pull/2 — the spike PR (closed unmerged), head 1d031a3e
- [primary] https://github.com/mcp-tool-shop-org/rnd-data/tree/main/runs/merchant-league--m2-xrpl-rust-spike-2026-11-14 — rnd-data's run: the receipt (README, spike source, raw step output, validated account history, cargo audit) and `league-dice` at 1d031a3e
- [primary] https://rustsec.org/advisories/RUSTSEC-2026-0387.html — the crypto-bigint timing advisory
- [primary] https://rustsec.org/advisories/RUSTSEC-2023-0089.html — atomic-polyfill unmaintained
