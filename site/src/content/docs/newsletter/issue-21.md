---
title: "A critic that catches more, and refuses too much"
description: "Issue 14 left our training-data critic with one gap: it ignored a correct \"no flaw\" answer. The confirmation test proved the stricter rule catches what today's rules miss, but it refused too many good rows. So we tried a narrower rule and a fuller definition of \"no flaw\". The narrower rule caught 14 more broken rows, and still refused 9 of 22 sound ones. Here's why, and what we're testing next."
issue: 21
date: 2026-10-22
highlights:
  - "<strong>Proven, but too strict.</strong> Making the critic's flaw check count caught 22 broken rows that today's rules missed, and none the other way. But it also refused 12 of 32 good rows, against a limit of 10%."
  - "<strong>A narrower rule catches nearly as much.</strong> Refusing only when the critic says \"no flaw\" and the label says there is one (or the reverse) caught 77 of 90 broken rows, against 63 under today's rules."
  - "<strong>Sound reasoning read as a guess.</strong> It still refused 9 of 22 good rows with sound reasoning, almost all because the critic called the reasoning a \"guess\". A fuller definition of \"no flaw\" didn't change that."
  - "<strong>The same prompt, twice, gives different answers.</strong> Two runs with identical prompts disagreed on 7 of 102 verdicts. That noise floor now shapes the next test."
---

The studio builds training data with a pipeline of local models. A **writer** drafts each row, and a **critic** from
another model family checks it. [Issue 14](/rnd/newsletter/issue-14/) tested the critic by breaking good rows on
purpose. It found one gap. Some rows carry a checker's reasoning with a planted mistake, and a label naming it (such
as "guess", reasoning from outside the material). When the reasoning was in fact sound but the label still named a
flaw, the critic correctly answered "no flaw". Today's rules ignore that answer, so the wrong row is kept.

A stricter rule set, **P2**, makes the flaw check count. In issue 14 it won every disagreement, but there were too
few to clear the test we had set in advance. This issue follows the confirmation test, and what came after.

## The confirmation: proven, and too strict

The confirmation test used fresh rows, hand-checked blind, with one comparison fixed in advance. P2 settled the
question:
- it caught **22 broken rows that today's rules (P0) missed, against 0 the other way** (p ≈ 5 × 10⁻⁷);
- but it also refused **12 of 32 good rows**. The design's limit was 10%.

The good rows split two ways, and so do the refusals:
- **Rows with a planted flaw**, correctly labelled. The critic agreed a flaw was there on all 22, but sometimes named a
  different one, such as "guess" for a reasoning loop. P2 requires the exact label, so it refused those.
- **Rows with sound reasoning**, labelled "no flaw". The critic called 4 of these 10 flawed.

So we separated the two problems, and tested the narrower one first.

## The narrower rule

The new rule set, **Pc** (the coarse gate), ignores which flaw the critic names. It refuses only when the critic and
the label disagree on whether there is a flaw at all. A "loop" read as "guess" is still "a flaw", so it passes. On the
confirmation data, Pc refused none of the 22 planted-flaw rows. All its refusals were sound reasoning read as flawed.

That pointed at the definitions. In the critic's instructions, "no flaw" was the one label with no description: just
"the check was right". "Guess" included "or a misreading", which could absorb any trace the critic doubted. So **Track
A** tested one prompt edit. It gave "no flaw" a full description (quoted the deciding lines, reasoned only from what
they state, reached the material's verdict), and said that such a check is not a guess.

The design ran the critic, Muse-Glimmer-30B, twice over the same 102 items at seed 0: once with the old instructions,
once with the new. 219 items were scored from those replies. An arm qualified only if it beat P0, at
an adjusted p under 0.05, and kept its false refusals at 10% or less on both kinds of good row. The outside reviewer,
Google's Gemini, checked the design, and set how to analyse it before any result was seen.

## What it found

On the 90 broken rows the test is built around:

| Rule set | Broken rows caught | Good rows refused: sound reasoning | Good rows refused: planted flaw | Qualifies? |
|---|---|---|---|---|
| P0, today's rules | 63 of 90 | 2 of 22 | 0 of 21 | (the baseline) |
| Pc, old instructions | **77 of 90** | **9 of 22** | 0 of 21 | no |
| Pc, new instructions | **76 of 90** | **10 of 22** | 1 of 21 | no |

The coarse gate works where it's meant to. Both arms caught 14 broken rows that P0 missed, and P0 caught at most one
they didn't (adjusted p = 0.0002 and 0.001).

But both failed the bar on sound reasoning, at 9 and 10 of 22, against at most 2. **The new instructions changed
nothing measurable.** Scored on the same set of verdicts, so that only the instructions differ, the two arms
disagreed on 2 broken rows, both caught by the old instructions and missed by the new (p = 0.5).

Why the critic still says "flaw" on sound reasoning shows up in what it named. On the good rows with sound reasoning
that it refused, it named "guess" 8 times of 9 in one run and 9 of 10 in the other. Read blind, none of that
reasoning hedges or leans on anything the material doesn't say. Yet the critic called about half of it a guess,
whatever its form: quoting the deciding lines didn't protect a trace, and a forced inference raised the rate only a
little. The one thing that separates real guesses from sound reasoning is an outside assumption, present in 6 of 7
planted guesses and in none of the 22 sound traces. Telling the critic what "no flaw" looks like didn't stop the
over-calling.

So nothing was adopted. The pipeline stays on P0, with the flaw check advisory, and every accepted row still goes
through R&D's blind hand check.

## The same prompt, twice

The design assumed something we could check: both runs send byte-identical verdict prompts at the same seed, so they
should give the same verdicts. They didn't. Of 102 matched calls:
- 22 replies differed in their text;
- 7 verdicts differed.

The most likely cause: the critic samples at temperature 1, so the seed doesn't make its output reproducible across
sessions. It changed little that mattered: under P0,
3 of the 90 broken rows changed outcome between runs. But a gap of 1 or 2 items between arms is within that noise, which
is part of why the two instruction sets can't be told apart.

When the premise failed, the reviewer ruled on how to analyse the result, without seeing any outcome figures. One
caveat: R&D's analysis script had already computed the figures in the same pass, before the ruling arrived, so R&D
had seen them. They were held unreported, and the reviewer chose the analysis without them. One analysis was the
pre-registered one; the other scored both arms from one shared set of verdicts. The two agree: neither arm
qualifies.

## Next: rewrite the labels

The failure points at the labels themselves, not at the rule. **Track B** tests that, in two stages:
- **Diagnosis, at no cost, now done:** on the items already scored, it found what's described above, and that the
  critic's flaw label flipped between runs on 5 of 12 such items. The label fixes are now frozen: "guess" is defined
  by an outside assumption alone.
- **Verification:** today's labels against the rewritten ones, on a fresh bank of items neither arm has seen, scored
  with the coarse gate. To handle the noise, the critic's flaw answer is sampled three times, and a row is refused
  only if 2 of the 3 name a flaw.

Its design has been reviewed and approved. T10, the next writer run, has priority for compute.

## Where the figures come from

- **The result:** [`data/track-a-result-2026-10-22.json`](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/stage1-regeneration/critic-signal/data/track-a-result-2026-10-22.json),
  with every comparison, the control rates, the flaw labels named and the noise floor.
- **The plan and its bar:** [`PLAN-ROUND4.md`](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/stage1-regeneration/critic-signal/PLAN-ROUND4.md)
  §1 to §4, which also holds the confirmation test's figures.
- **The diagnosis and the frozen labels:** `TRACK-B-STAGE1.md` and `TRACK-B-LABELS.md`, beside it.
- **Next:** [`TRACK-B-DESIGN.md`](https://github.com/mcp-tool-shop-org/rnd/blob/main/experiments/stage1-regeneration/critic-signal/TRACK-B-DESIGN.md).
- The text of the rows stays off the public repo. These files hold ids, codes and counts only.
