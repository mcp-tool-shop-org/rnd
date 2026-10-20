---
id: 2026-10-20-xrpl-agentic-payments-x402-the-ai-starter-kit-and-mpp
title: XRPL agentic payments: x402, the AI Starter Kit and MPP
date: 2026-10-20
kind: concept
relevance: watch
fields: [payments, agent-tooling]
tags: [xrpl, x402, agentic-payments, mpp, rlusd]
---

## Summary

An XRPL marketing guide says AI agents already pay each other and pay for services on the XRP Ledger, through three
things: x402, an "XRPL AI Starter Kit", and Stripe and Tempo's Machine Payments Protocol (MPP). All three exist, and
the two payment protocols both work over HTTP's 402 "Payment Required" status:
- **x402** is an open standard, now under the Linux Foundation. Its official repository has an XRPL payment scheme.
- **The AI Starter Kit** is a bundle from Ripple and the XRP Ledger Foundation: a docs MCP server, two Claude skills,
  two xrpl.org pages and x402 support. It isn't a standalone product.
- **MPP** is Stripe and Tempo's protocol. XRPL support comes from Ripple's own beta SDK, not from Stripe or Tempo.

The guide's headline figure, millions of agentic transactions, rests on one company's dashboard, with no published
definition of an agentic transaction.

## Key points

- **x402 on XRPL is in the standard itself, not an add-on.**
  - The x402 Foundation's repository (Apache-2.0) has `specs/schemes/exact/scheme_exact_xrpl.md`, added 2026-07-03,
    beside 16 other chains' `exact` schemes.
  - The payer signs an ordinary XRPL `Payment` for an exact amount of XRP or an issued currency, and a facilitator
    submits it. The payer pays the network fee, so the XRPL scheme can't offer fee sponsorship.
  - Ripple credits t54 with the contribution, and t54 runs a hosted facilitator.
- **The Starter Kit, as Ripple's post of 2026-06-09 lists it:**
  - an XRPL docs MCP server (hosted at context7.com/websites/xrpl);
  - two Claude skills in XRPLF/xrpl-dev-portal (`.claude/skills/xrpl-skills/`): an agent wallet skill (wallets,
    balances, tracking) and a payments skill;
  - a getting-started tutorial and an "Agentic Transactions" hub on xrpl.org;
  - x402 support, paying in XRP or RLUSD.

  The post gives no transaction counts.
- **The kit has grown since launch.** xrpl.org's AI-tools page now lists the docs MCP server at `mcp.xrpledger.ai`
  (Ripple's post links context7.com/websites/xrpl), a second server at `xrpl.org/mcp`, and a third skill for trading,
  beside the wallet and payments skills.
- **MPP:**
  - Stripe announced it on 2026-03-18, co-authored with Tempo. The post names Tempo as the chain in its example and
    doesn't mention XRPL or Ripple.
  - It works with any payment method, and its specs (tempoxyz/mpp-specs) are CC0.
  - XRPL is one of its payment methods through Ripple's `xrpl-mpp-sdk` (Apache-2.0, created 2026-08-14, latest tag
    `0.1.0-beta.4`). No usage figures were found.
- **The counts:**
  - The XRP Ledger Foundation reported more than one million agentic payments over x402 when t54 launched its XRPL AI
    Hub dashboard (2026-07-08).
  - RippleX's head of engineering gave 1M on 2026-07-21 (The Block). The article names no counter and no method.
  - Secondary crypto news puts the October figure near 13.9M, from the same hub.
  - No source defines an agentic transaction, or says whether test and demo payments are excluded. On a near-free
    chain, a count of micropayments says little about the money that moved.

## Studio relevance

- **The studio builds the tools this is aimed at.** MCP servers, Claude skills and agents are the studio's own field,
  and Ripple's kit is the same shape: an MCP docs server plus skills. It's a reference design to read, not to adopt.
- **xrpl-lab:** an agent paying for an API with x402 on testnet would be a natural module beside the payments track.
  That's an idea to weigh, not a plan.
- **readouts xrpl-knowledge** has no row for x402 or MPP. Once the claims a row would need are verified, this entry is
  a candidate for promotion.
- **Watch for:** a published definition and method behind the hub's counts, MPP's XRPL SDK leaving beta, and x402's
  XRPL scheme gaining fee sponsorship.

## Claims

- [verified] The x402 Foundation's repository (x402-foundation/x402, Apache-2.0) holds an `exact` payment scheme for XRPL, added 2026-07-03, in which the payer signs an XRPL Payment and a facilitator submits it; the scheme can't sponsor fees (via: GitHub API and the spec file read at source, Editor, 2026-10-20)
- [verified] Ripple's post of 2026-06-09 lists the Starter Kit as a docs MCP server, two Claude skills in XRPLF/xrpl-dev-portal, two xrpl.org pages and x402 support in XRP or RLUSD, credits t54 for the x402 contribution, and gives no transaction counts (via: the post read at source, Editor, 2026-10-20)
- [verified] xrpl.org's AI-tools page lists the XRPL Docs MCP server at mcp.xrpledger.ai, an xrpl.org MCP server at xrpl.org/mcp, and wallet, payments and trading skills (via: the page read at source, Editor, 2026-10-20)
- [verified] Stripe announced MPP on 2026-03-18, co-authored with Tempo, without mentioning XRPL or Ripple (via: Stripe's post read at source, Editor, 2026-10-20)
- [verified] MPP's specs in tempoxyz/mpp-specs are CC0 1.0 (via: its LICENSE.md, Editor, 2026-10-20)
- [verified] Ripple's xrpl-mpp-sdk is Apache-2.0, created 2026-08-14, latest tag 0.1.0-beta.4 (via: GitHub API, Editor, 2026-10-20)
- [verified] The Block (2026-07-21) quotes RippleX's head of engineering on passing 1 million agentic transactions and names no counter or method (via: the article read at source, Editor, 2026-10-20)
- [unverified] The XRP Ledger Foundation reported more than one million agentic x402 payments at the XRPL AI Hub's launch on 2026-07-08 (via: crypto.news; the Foundation's own post not read)
- [unverified] The XRPL AI Hub counted about 13.9 million agentic transactions by 2026-10-12 (via: Coin-Turk; the hub itself not reached)
- [unverified] The x402 Foundation was announced on 2026-04-02 and became operational on 2026-07-14 under the Linux Foundation (via: a research agent's reading of search summaries; the press pages not read directly)
- [unverified] XRPL agents have made millions of agentic transactions, through the AI Starter Kit, x402 and MPP support (via: an XRPL marketing guide supplied by the Director, 2026-10-20)

## Sources

- [primary] https://github.com/x402-foundation/x402 — x402 Foundation (Apache-2.0; `specs/schemes/exact/scheme_exact_xrpl.md`)
- [primary] https://ripple.com/insights/xrpl-ai-starter-kit/ — Ripple, 2026-06-09
- [primary] https://github.com/XRPLF/xrpl-dev-portal — XRP Ledger Foundation (`.claude/skills/xrpl-skills/`)
- [primary] https://xrpl.org/resources/dev-tools/ai-tools — xrpl.org (the current list of MCP servers and skills)
- [primary] https://xrpl.org/docs/agents/agentic-payments-x402 — xrpl.org (via the research agent; not re-read)
- [primary] https://stripe.com/blog/machine-payments-protocol — Stripe, 2026-03-18
- [primary] https://github.com/tempoxyz/mpp-specs — Tempo and Stripe (specs CC0)
- [primary] https://github.com/ripple/xrpl-mpp-sdk — Ripple (Apache-2.0, beta)
- [aggregator] https://theblock.co/post/408987/ripplex-sees-xrp-ledger-agentic-transactions-hitting-10-million-mark-soon — The Block, 2026-07-21
- [aggregator] https://crypto.news/xrp-ledger-hits-1m-ai-payments-as-t54-ai-launches-hub/ — crypto.news
- [aggregator] https://en.coin-turk.com/xrpl-ai-agents-process-13-9-million-transactions-in-october-as-value-stays-modest/ — Coin-Turk, 2026-10-12
- [user] An XRPL marketing guide's "Agentic commerce on XRPL" section, supplied by the Director, 2026-10-20
