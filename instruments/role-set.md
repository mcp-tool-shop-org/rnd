---
id: role-set
title: role-set — a generator for role-shaping training data (prototype, in the open)
date: 2026-10-10
kind: instrument
relevance: act
fields: [machine-learning, training, studio-tooling]
tags: [instrument, role-set, stage1, verifier, training-data, generator]
instrument_status: planned
invoke: "uv run role-set plan --lessons <T..> --seed <n> --out plan.json ; uv run role-set cost --plan plan.json --profile <p> ; role-set write (refused until aspire-si's gates package is pinned)"
when: "Building Stage 1 role-shaping training data at scale, with every item planned before it's written and passed through the same gates the humans use; later, a self-learning loop that steers new items toward questions the model gets stuck on."
where: "github.com/mcp-tool-shop-org/role-set (public since 2026-10-10, prototype)"
---

## Summary

role-set is a generator, not a judge.
- **It plans every slot of a batch first:** kind, side, verdict, pairs, two-turn items, escalate items,
  multi-line keys, puzzle structures and real-source slots. It does this from a seed with no model call, so the
  data floors hold by construction.
- **A large model writes only the parts a writer should write,** on a pod the human launches with offrig.
- **Every item passes the same gates the humans use** before a human sees it. The gates are aspire-si's
  stdlib `aspire-si-gates` package, imported at a pinned commit, never copied.
- **What a good verifier is lives in the role pack,** which people write.

It was made public by the maintainer's decision, so it can be tested and developed in the open. It's a
prototype, and its interfaces change without notice.

## Key points

- **Guards:**
  - loopback endpoints only;
  - licence-checked writers only;
  - never a cloud tag;
  - a 5090 step only inside a Publisher grant with a fresh watchdog heartbeat.

  It never launches, prices or shuts down a pod; offrig and the human hold the budget.
- **The firewall:** it never reads the sealed set, the DEV sets or the pre-interview. The training runner's
  store write path refuses any DEV, sealed or interview id or text, as does role-set's ingest. DEV aggregates
  can enter only between stages, by a dated amendment, through a command that refuses while a stage is open.
  The next stage then gets a fresh DEV. See `experiments/stage1-role-eval/` for why: with 30 DEV tasks, a
  lesson × kind × tier "aggregate" is effectively an item result.
- **The self-learning loop** (pre-registered in the Stage 1 eval plan):
  - From round 2, 20% of each round's new items are steering slots, drawn from a key-checked reserve pool,
    never written live.
  - The cell is (lesson, kind) for kinds C, D and E. A cell needs n ≥ 8 observations and a stuck rate of at
    least max(median, 0.10).
  - Caps: 25% of the budget per cell, 40% per lesson, with floors placed first.
  - The signal is pooled over the ROLE and NO-ROLE arms, with one stream per training seed.
- **"Stuck" means circling, not effort** (`stage1-stuck-rule.json`, sha256 `716dc251…`):
  - an 8-word span repeats 3 or more times; **or**
  - the 16,384-token cap is reached; **or**
  - the trace is long **and** either re-reads already-quoted lines at more than 8.09 per 1,000 tokens, or has
    a burst of 3 or more hedge phrases within 200 tokens.

  On the untrained baseline, bursts appear in 7 of 102 traces and in 0 of 68 taught targets (48 ROLE, 20
  NO-ROLE). That's why the burst replaced the overall hedge rate as the trigger. The hedge rate and every
  burst field are still recorded on every trace.

## Studio relevance

role-set is how Stage 1 data stops depending on hand-written batches. Grok's third batch was generated from
one template script, passed every mechanical gate anyway, and was rejected on a human read. role-set's
answer is to plan the structure itself and to gate diversity: no 8-word span shared by 3 or more items, no
reused framings, materials or puzzle shapes.

R&D reviews its design, its gates and its reserve pool through the same key-check lane as every batch.

## Sources

- github.com/mcp-tool-shop-org/role-set — README and docs/role-set-design.md [primary]
- rnd `experiments/stage1-role-eval/` — the Stage 1 statistics, the stuck rule and the DEV ruling [primary]
