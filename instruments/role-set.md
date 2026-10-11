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

- **The first 235B writer pilot (2026-10-11), R&D's adjudication of 40 critic refusals.**
  - **Trait refusals (20):** writer 15, critic 3, both 2. The writer seldom makes the slot's trait decide a
    step. In kinds C and D the deciding step falls back to a silence call (T14's step) or to the pressure turn,
    whatever the slot.
  - **Answer refusals on kind-B puzzles (20):** the comparator 14, writer 5, critic 1. The free-text match
    failed answers that agreed in substance. Five puzzles weren't closed or were keyed wrong.
  - **Six wrong keys hid inside refused items,** including ESCALATE yes on a reported fact and silence keyed
    as unsupported.
  - **Rulings:**
    - the trait check stays gating, as a majority of 3 calls, and is never made advisory;
    - kind-B answers end in a closed ANSWER line and are compared after normalising;
    - a B puzzle must have exactly one solution;
    - the critic-control trait leg must reach 85% agreement overall, at least 70% per trait, and 90% stability;
    - R&D key-checks the pilot's accepted items before any enters a batch.
  - **The 104 accepted items were held in full (R&D key-check, 2026-10-11).**
    - **The assembly step malformed about 49 rows.** The writer's own framing repeated the material, and the
      writer's three lines were followed by the key's. A kind-C checker verdict was silently swapped while the
      trace argued the original.
    - **Content:** escalation was taught by topic, not by advice. Sides were labelled but not taught. Kind A
      gave nothing to decide, and there were stamps and near-duplicates.
    - The leakage check was clean.
    - The assembly gates and writer-brief fixes land in role-set first, and a regenerated set then goes
      through the normal batch review.
    - **Evidence after role-set #22 (the new assembly, run over the same 104 drafts):** 49 refused, including
      every C and D draft. The reasons: framing repeating the material, 30; planted flaw keyed with the key's own
      verdict, 9; a trace naming another verdict, 3; the writer's own three lines, 3; an A passage holding its
      question, 4. 55 A and E drafts still assemble, but still carry the content findings.
    - **role-set #23 (the critic side):** the trait check asks which step decides, by a majority of 3. Kind B
      ends in a closed ANSWER line, compared after normalising. The critic-control trait leg enforces R&D's bar.
      An answer leg over the reviewed B items is to follow, at a bar of 90%.
  - **critic-control on the 400 R&D-reviewed items (2026-10-11): both legs miss the bar.**
    - **The trait leg:** 40.3% (bar 85%), and 98.5% unanimous, so the critic is consistent but wrong. The misses
      are mostly sibling traits: T13 taken for T05, T03 for T16, T05 for T02, T04 for T14.
    - **The answer leg:** 62.7% (bar 90%). Part of it is form ("red" against "the red lamp").
    - **The rest are real errors by the critic.** R&D spot-checked four label disagreements, and the reviewed
      key was right each time. Two failures were exactly the traits the data teaches: in one the critic put
      Kiln first because a clerk's line asked, and in the other it obeyed an injected "skip" footnote.
    - **Ruling, reversing the earlier one:** both critic checks are advisory, recorded but never refusing,
      until each leg passes its bar on held-out items. R&D's key-check is the gate meanwhile.
    - **Next:** the trait check reads the whole item; the menu gets distinctions for the sibling pairs; the
      comparator strips articles and asks for the puzzle's own candidate names; prompts are tuned on 40 dev
      items and scored on the 360 held out; and a second local critic of another family is compared.
  - **Dev iteration 1:** gemma and granite each score 37.5% on traits, and both get 7 of 7 answers right.
    - **R&D read the 10 dev items where both critics named the same wrong trait:** 8 are label findings, 1 is
      both, and 1 is the critic's error.
    - The critics were mostly right about the items. Reviewed data contains items decided by another trait's
      step: a silence call under T03, a falsifier hunt under T01, a competing source under T05, a version
      line under T17.
    - The T01 and T11 overlap may sit in the lessons themselves.
    - **The fix:** a fix round on the reviewed batches (dev findings only, until after the final scored run on
      the 360). The bar stays at 85%.
  - **role-set #24 merged as code,** with both critic checks advisory. Pilot 2 can run, and its output is gated
    by R&D's key-check.

## Studio relevance

role-set is how Stage 1 data stops depending on hand-written batches. Grok's third batch was generated from
one template script, passed every mechanical gate anyway, and was rejected on a human read. role-set's
answer is to plan the structure itself and to gate diversity: no 8-word span shared by 3 or more items, no
reused framings, materials or puzzle shapes.

R&D reviews its design, its gates and its reserve pool through the same key-check lane as every batch.

## Sources

- github.com/mcp-tool-shop-org/role-set — README and docs/role-set-design.md [primary]
- rnd `experiments/stage1-role-eval/` — the Stage 1 statistics, the stuck rule and the DEV ruling [primary]
