---
id: 2026-11-22-measuring-a-preview-tool-s-effect-at-frozen-game-states-what
title: Measuring a preview tool's effect at frozen game states: what a Deep Research audit found (seed 53)
date: 2026-11-22
kind: finding
relevance: act
fields: [evaluation]
tags: [merchant-league, agent-evaluation, seed-53, harvest]
---

## Summary

This follows the seed 42 entry (2026-11-20), which moved Merchant League's first evaluation to frozen game states. That
design is now built. `league-eval` saves a checkpoint after the talk phase and before the act phase. It replays one
decision three ways from that checkpoint: tool `off`, a `control` arm with the same rules text and a tool that gives a
fixed reply, and tool `on`. The first run is planned at 20 seeds × 6 states × 3 arms. We asked a second Gemini Deep
Research run to audit that design and its statistics before any GPU time is spent.

The report is `[aggregator]` AI output with 246 citations. We compared its findings with our code and docs, and none
of its papers were read for this entry. Its main message: the design is sound, but five parts of the plan would make
the result hard to read. Those five are below.

## Key points

- **One run per arm per state is not enough.** With reasoning on and sampling at the model makers' settings, one run
  per arm cannot separate sampling noise from the tool's effect at that state. A small pilot with three replicates per
  arm and state should measure the noise first, and that measurement sets the main run's replicate count.
- **The control is not a clean placebo for the preview.** The real tool also checks whether the orders are legal. The
  control checks nothing. So `on` against `control` measures a legality check and a preview together.
- **The scorer must look further ahead than the tool does.** The preview shows the immediate outcome of a turn. A
  scorer that grades one-turn net worth would reward exactly what the tool shows, which makes the test circular. The
  scorer should value a decision to the season's close and average over plausible orders from the other seats and
  hidden-objective guesses. It should be built and frozen on a pilot, blind to arm, before the main run is scored.
- **Many saved states may not be sensitive to the preview** (routine or already-decided turns). The report's own
  estimate is that this can roughly double the effect needed to see anything. It suggests an arm-blind pre-screen of
  states before branching.
- **What the preview assumes about the other seats matters.** If the preview treats the other seats as submitting
  nothing, a trade agreed in talk can look like a loss. A literal-minded model might then cancel it. The report
  suggests measuring how often each arm keeps talk-phase deals.
- **Analysis plan:**
  - a linear mixed model with small-sample (Kenward-Roger) degrees of freedom;
  - a cluster-level sign-flip test over the per-seed means as a distribution-free check;
  - a fixed test order (`on` vs `control`, then `on` vs `off`, then `control` vs `off`);
  - false-discovery-rate control across the secondary measures;
  - an equal-compute baseline (a majority vote of several `off` runs against one `on` run);
  - truncation inside the thinking block recorded separately, never scored as a tool failure.
- **It confirms the rest:** branching at the pre-act boundary, fresh replays of all three arms, reasoning kept within
  a turn, and determinism checks before paid runs.

## Studio relevance

### What it contradicts in our design (read first)

| Finding | Merchant League today | Decision |
|---|---|---|
| One run per arm per state confounds noise with the effect | First run planned at one run per arm per state | A pilot at 4 seeds × 6 states × 3 replicates first. The main run's replicate count comes from the pilot, minimum 2, written into the pre-registration |
| The control lacks the legality check | `on` returns `INVALID_ORDER` for illegal drafts; `control` returns a fixed string | Changing the control's reply changes model-facing words and needs the Director. Until then the contrast is reported as "legality check + preview vs. nothing" |
| A one-turn scorer is circular | `league-eval` records the scorer's inputs; no scorer exists | A scorer is being designed: candidate set, horizon to season close, sampled other seats, CPU-only and deterministic, arm-blind, hash-frozen on the pilot |
| Preview-insensitive states dilute the effect | States are chosen by early/mid/late phase only | An arm-blind pre-screen, with thresholds fixed on the pilot and pre-registered |
| The preview assumes the other seats submit nothing | True, and disclosed in general terms in the tool's description | Keep the tool as designed; add per-arm talk-phase deal-keeping to the measures |

### Decisions and actionables

1. All five rows above go into the first run's pre-registration before any main-run GPU time.
2. The scorer design comes before the pilot is scored. The pilot itself needs its own compute grant.
3. The detection limit is stated up front: small effects will not be distinguishable at this size.

## Claims

- [verified] The engine's preview assumes empty peer bundles (via: `crates/league-core/src/engine.rs:935` and `:948` in mcp-tool-shop-org/merchant-league at 55fd92a2, read by R&D, 2026-11-22)
- [verified] The model-facing preview tool takes the seat's own orders only, with no assumption parameters (via: `crates/league-relay/src/wording.rs:2176` at 55fd92a2, read by R&D, 2026-11-22)
- [verified] The tool description says projected marks may differ after the other seats reveal (via: `crates/league-relay/src/wording.rs:944` at 55fd92a2, read by R&D, 2026-11-22)
- [verified] The `on` arm's preview has an `INVALID_ORDER` code, while the control returns a fixed reply with no rule validation (via: `crates/league-relay/src/wording.rs:1255` and `docs/eval-harness.md` decision D3 at 55fd92a2, read by R&D, 2026-11-22)
- [unverified] Agents react to loud tool errors but often not to quiet, incomplete returns. Reasoning models caught quiet faults less often than instruct models (the report's reading of Kraishan 2026; paper not read)
- [unverified] With 120 states, the smallest detectable effect at 80% power is about 0.30 to 0.43 paired standard deviations (the report's own arithmetic; not recomputed)
- [unverified] Twenty base games are about 88% of all model calls, so a second replicate adds about 12% (the report's estimate; it assumes 28 turns and 8 calls a turn, which differs from our game; re-measure from the pilot)
- [unverified] Several figures in the report come from secondary digests, not primary papers (Bellam 2026, JudgeBench numbers, τ-bench pass^8). Not load-bearing for the decisions above.

## Sources

- [aggregator] https://gemini.google.com/ — Gemini Deep Research (Gemini 4 Carbon, High), 2026-11-22: "Experimental Design Audit and Statistical Protocol for Evaluating Outcome-Preview Tools in Multi-Player Language-Model Agents"
- [primary] https://github.com/mcp-tool-shop-org/merchant-league — the game and its evaluation harness (`docs/eval-harness.md`), read at 55fd92a2
- [primary] https://doi.org/10.2307/2533558 — Kenward and Roger (1997), Small sample inference for fixed effects from restricted maximum likelihood, Biometrics 53 (cited by the report; not read)
- [primary] https://doi.org/10.1016/j.jeconom.2022.04.001 — MacKinnon, Nielsen and Webb (2023), Cluster-robust inference, Journal of Econometrics (cited by the report for cluster resampling; not read)
- [primary] https://arxiv.org/abs/2411.00640 — Miller (2024), Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations (cited by the report; not read)
- [primary] https://arxiv.org/abs/2610.10062 — Kraishan (2026), Loud Failures, Quiet Failures (cited by the report; not read)
- [primary] https://arxiv.org/abs/2203.11171 — Wang et al. (2023), Self-Consistency Improves Chain of Thought Reasoning in Language Models (the majority-vote baseline; cited by the report; not read)
- [primary] https://arxiv.org/abs/2407.01502 — Kapoor et al. (2025), AI Agents That Matter (cost-controlled comparison; cited by the report; not read)
