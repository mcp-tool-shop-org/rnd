# Verifier gold sets: grounded and reasoning claims

These are the gold claims that pick and calibrate offrig's default verifier model. The design is offrig#38,
`docs/verifier-design.md`. The split agreed with the Publisher, 2026-10-08: R&D owns model selection and the
grounded set, and the Publisher owns the PR-based reasoning set.

## Format

JSONL, one claim per line, in the shape the verifier's calibration runner consumes:

```
{"id", "check_type": "grounded", "claim", "context": [{"source", "text"}],
 "label": "supported" | "unsupported" | "cannot_tell", "subtle", "split": "tune" | "heldout", "origin", "notes"}
```

## How a claim is made

- **Facts:** each comes from real code at a pinned commit (`facts_roleos.py`).
- **Evidence:** the exact source lines around a unique anchor, read with `git show <sha>:<path>`. Nothing is
  paraphrased. `must` strings fail the build if the code changes underneath a fact.
- **Three claims per fact:**
  - `supported`: the evidence states it;
  - `unsupported`: a **near-miss** the evidence contradicts, marked `subtle`. The kinds: a changed number,
    strict vs non-strict bound, swapped term, flipped or dropped condition, changed severity, different outcome
    or behaviour, invented threshold;
  - optionally `cannot_tell`: a plausible claim the evidence neither states nor contradicts.
- **Splits:** by fact, never by claim, so a fact's true and false forms never straddle tune and held-out. The
  side is a stable hash of the fact id (salt 20261008), so adding a batch never moves an existing fact.

## Labels

- **First pass:** R&D (Claude Opus 5.5), written against the code.
- **Corrected before the second pass:** `jury-dup-s` was first written as `cannot_tell` ("the 0.9 cutoff comes
  from Geirhos et al."). The evidence's own comment calls it a "Studio rule", which points against a
  literature source, so it was replaced with a claim the evidence is really silent on.
- **Second pass:** blind, by a different model (Claude Sonnet 5.5, labels hidden, evidence only).
  - **role-os 64/64, offrig 47/47 and docs 16/16 agree: 127/127.**
  - The second labeller flagged 4 items as ambiguous and kept the same label on each, so all four held.
  - One wording was tightened after its flag: `or-fa-upper-t` said "under 0.10", but the evidence gives the
    constant, not the comparison. It now reads "the limit … is 0.10".
  - `docs-boost-t` was flagged because its evidence only implied the 5-outcome gate. A span from
    `summarizePack` now shows it (boost 0 and status "insufficient data" below `minRuns`). The label is
    unchanged.
  - **Caveat:** both passes are Claude models, so the agreement is not cross-family. A third, different-family
    pass (a local judge, after the CUDA 13.4 Ollama switch) on a sample is planned before the default model is
    named. The gold labels decide which verifier becomes the default, so this is the targeted check Standing
    Rule 3 allows.

## Coverage, and what's still needed

| Batch | Source | Facts | supported | unsupported | cannot_tell |
|---|---|---|---|---|---|
| 1 | role-os @ ce91be8 (JS): calibration, packs, jury, recipe card, abandon | 30 | 30 | 30 | 4 |
| 2 | offrig @ a45fe53 (Rust): verifier default rule, index, lanes, job runs, v2 create loop | 22 | 22 | 22 | 3 |
| 3 | role-os README sentences vs the code they describe (docs vs code; one natural error) | 8 | 8 | 8 | 0 |
| 4 | the Publisher's PR set (17 PRs, offrig/aspire-si/role-os/rnd), re-typed grounded: `prs/grounded-prs.jsonl` | 182 behaviours | 179 | 181 | 13 |
| **total** | | | **239** | **241** | **20** |

**Batch 4 (`prs/`):**
- **Written and labelled by** the Publisher's Sonnet author (Publisher commit 5894788).
- **Re-typed** `reasoning` → `grounded`: these are claim vs code at a merge SHA, not "what this change does". A
  diff-based reasoning set is being built separately.
- **Blind relabel** by R&D's Sonnet labellers (4 batches, strict "every part must hold"): **368/374 agreed**.
- **R&D adjudicated** the 6 disagreements plus one flagged item (rulings in each item's `notes`):
  - 1 supported → unsupported (`53-1s`, over-general "such as uni");
  - 3 → cannot_tell (the deciding code isn't in the evidence);
  - 1 dropped as ambiguous (`61-7u`);
  - 1 evidence span added (`61-9s`).
- **Spot-check:** R&D read 15 random agreements; all 15 correct.
- **Tags:** `has_doc_comment` (185, the context's comments restate the claim) and `self_referential` (44
  offrig#41 items about the verifier's own code), so calibration can report those strata separately.

The default rule needs **at least 100 unsupported claims per check type**, about 200+ claims in all. Next
batches widen beyond one codebase and one language, so a verifier isn't tuned to role-os's style:

- **offrig (Rust), more:** budget and plan arithmetic, the CUDA floor;
- **rnd (Python):** datapack manifests, the check rules, the version bump;
- **aspire-si (Python):** critic-head training and selection;
- **docs vs code:** README and handbook sentences checked against the code they describe. This is the
  verifier's real job.

## Reasoning set: claims about what a change did (`diffs/`)

The Publisher's diff-based set (Publisher commit f3f3f66), copied unchanged as
`diffs/source-publisher-f3f3f66.jsonl`.

| Split | supported | unsupported | cannot_tell |
|---|---|---|---|
| tune | 41 | 41 | 9 |
| heldout | 55 | 55 | 7 |
| **total** | **96** | **96** | **16** |

- **Source:** 19 PRs (offrig, aspire-si, role-os) plus 5 rnd commits. The evidence is the before and after
  hunks at the base and merge SHAs. 72 items are tagged `has_doc_comment`.
- **Near-misses specific to changes:**
  - direction reversed (9);
  - a false "no behaviour change", or old behaviour credited to the change (12);
  - the wrong scope (11);
  - plus the usual kinds.
- **Blind relabel** by R&D's Sonnet labellers (2 batches of 104, shuffled, labels and notes hidden, strict):
  **208/208 agreed.** They flagged 4 items as ambiguous wording, and kept the author's label on each.
- **Spot-check:** R&D read 10 random items and the 4 flagged ones against both hunks. All 14 were correct.
- **What 208/208 means:** the labels are sound. But a strong model found every item easy, so the set may not
  tell strong verifiers apart. The calibration run shows whether it does: if the local candidates also score
  near 100% here, the next batch needs harder near-misses (for example behaviour that depends on code
  outside the hunk, or a change whose doc comment says something the code doesn't do).
- **Caveats** (the Publisher's): one author; chained PRs share hunks, so items aren't independent; pure
  additions have only surrounding code as their "before".
- **Short of the rule:** 96 unsupported, against 100. The Publisher's hard batch below closes it.

### Hard batch (`diffs/source-publisher-hard.jsonl`, origin `diffs-2026-10-hard`)

- **Size:** 38 claims from 15 new behaviours: 15 supported, 15 unsupported, 8 cannot_tell. Mostly role-os
  direct commits, plus aspire-si#52 and one rnd commit.
- **Patterns** (named in each item's notes):
  - a subtle change in near-identical code (6);
  - a multi-part claim where one part fails (4);
  - an indirect effect (3);
  - a doc comment that overclaims (2);
  - an outside-the-hunk cannot_tell (8).
- **Blind relabel:** two Sonnet labellers each did all 38 independently.
  - Labeller A agreed with the author on 38/38, labeller B on 37/38.
  - The split is `diffhard-aspire-si-52-1u`: does `lexical_guard` call big → bigger a comparative? B said
    yes, reading `"big" + "er"` as `"bigger"`. **R&D ruled against the code: unsupported, the author's
    label.** The `g` is doubled, no suffix rule matches, neither word is in a vocabulary set, and the
    guard returns None. This is the kind of miss the batch was built to catch.
- **Spot-check:** R&D read the split and both flagged cannot_tell items (`6a9bade-1c`, `4342dff-1c`). Both
  rest on code not in the hunks, so cannot_tell is right.
- **Reasoning totals:** 111 supported, **111 unsupported**, 24 cannot_tell. That's past the 100 rule.

## Cross-family check, and the files to calibrate on

A blind label pass by `gemma4:31b` on a 120-claim sample (pre-registered in `crossfamily/README.md`) found
**2 gold labels wrong, under the limit of 3, so the sets stand.** Both are fixed:
- `diff-offrig-8-4s` → cannot_tell;
- `prs-aspire-si-59-2s` reworded.

**Calibrate on these** (`offrig verify calibrate`, one run per file and model):

| check type | files | supported | unsupported | cannot_tell |
|---|---|---|---|---|
| grounded | `grounded.jsonl` + `prs/grounded-prs.jsonl` | 239 | 241 | 20 |
| reasoning | `diffs/reasoning-diffs.jsonl` (all three Publisher sources, adjudicated) | 209 | 210 | 40 |

The `diffs/source-publisher-*.jsonl` files stay as the Publisher wrote them; `reasoning-diffs.jsonl` carries
the rulings. Reasoning splits: tune 102 supported, 102 unsupported, 19 cannot_tell; held-out 107, 108 and 21.

**Reasoning batch 2** (`diffs/source-publisher-b2.jsonl`, origin `diffs-2026-10-b2`):
- **Size:** 213 claims from 100 behaviours plus 13 cannot_tell, from role-os 41, rnd 24, aspire-si 21 and
  offrig 14. 31 use the hard patterns.
- **Blind relabel:** two Sonnet labellers, given offrig's own definition of supported (a comment in the
  evidence counts, but the code wins where they conflict): **208/213 agreed.**
- **R&D's rulings on the 5:**
  - `081e92f-4s` supported → cannot_tell: `NO_FORMAT`'s members aren't in the evidence;
  - `80c532c-4u` unsupported → cannot_tell: `earned` moves to `created_at`, but the evidence doesn't settle
    whether that is the certification time;
  - `b7bccc8-11s`/`-11u`: labels kept, and the after-hunk widened to L515 so it shows the `--redo` skip the
    claims turn on;
  - `4d45a08-7c` stays cannot_tell: the pod script's next step isn't shown.
- **Spot-check:** R&D read 6 random agreements against the hunks; all 6 correct.

## Pre-registration, 2026-10-10 ~01:00: is the gold coherent? (the Director's question; nothing runs until he agrees)

The Director doubts the labels ("There's places to get this sort of stuff, no need to make it up"). His point
holds:
- every claim here is a synthetic near-miss written by Claude about our own repos;
- the cross-family label check used gemma4:31b, which is also the leading candidate;
- nothing is anchored to an outside, human-labelled set.

The Publisher's first check on the committed receipts found the decided labels coherent: 729 tune claims, 21 runs,
and only 7 claims where 80% or more of the runs decided against gold. **All 7 are cannot_tell gold.** cannot_tell
is the soft spot, and it is small: **60 items** (grounded 15 tune and 5 held-out, reasoning 19 tune and 21
held-out). A handful of shaky ones moves the abstain and teacher-bar numbers.

**Part 1: re-rule every cannot_tell item (60) against a written definition, fixed now.**
- **The definition:** the evidence shown neither states nor contradicts the claim, and a careful reader couldn't
  settle it from what is shown. Evidence the claim needs but that isn't shown doesn't count, even if the repo has
  it.
- **Raters, chosen so the generator's family isn't the only judge:**
  - (a) R&D, blind to every model verdict;
  - (b) one different-family model, run **by hand by the Director** on Grok or Gemini (Standing Rule 1: no
    Ollama Cloud), with the same definition and evidence. **Not gemma**, because gemma is a candidate.
  - Where (a) and (b) disagree, the Director rules.
- **Outcomes:** every change is recorded, with old label, new label, rater and reason. Anything already scored is
  re-scored only as a **labelled correction**, beside the original, never in place of it. Held-out items are
  re-ruled blind to any held-out verdict. One held-out score already exists (gemma reasoning v2), and its
  correction is shown beside it.

**Part 2: an external anchor.** Run the leading configurations on public, human-labelled claim-verification sets.
If they **rank** the same way on the public sets as on our gold, that's evidence our gold measures the same
thing. If they don't, our gold is suspect, and the calibration numbers are reported as suspect until it's fixed.

| set | licence (HF card, read 2026-10-10) | labels → ours | use |
|---|---|---|---|
| VitaminC (`tals/vitaminc`) | CC BY-SA 3.0 | SUPPORTS / REFUTES / NOT ENOUGH INFO → supported / unsupported / cannot_tell | contrastive near-miss pairs from real Wikipedia edits, the closest match to our near-miss design; the only 3-way set |
| LLM-AggreFact (`lytang/LLM-AggreFact`) | **CC BY-ND 4.0, evaluation only:** the card says it "should not be used in pretraining or fine-tuning" | 1 / 0 → supported / unsupported | grounded-document fact checking; **anchor only, never ASPIRE training data** |
| HoVer (`hover-nlp/hover`) | CC BY-SA 4.0 | SUPPORTED / NOT_SUPPORTED; test labels hidden | multi-hop / conjunctive claims; evidence is only Wikipedia sentence ids, so it needs a fetch step. **Deferred** |

- **Sample (fixed now, seeded 0):**
  - VitaminC test: 300 claims, 100 per label;
  - LLM-AggreFact test: 300 claims, label-balanced and stratified across its source datasets.

  Each is converted to offrig's gold shape (claim, context = the evidence text, label, split `anchor`).
- **Configurations,** a minimal set:
  - gemma4:31b think on;
  - gemma4:31b think off;
  - qwen3:14b think on;
  - the think-before-accepting policy, once offrig serves it natively;
  - Nemotron's best level from tonight.

  At about 3–10 s per claim, that's about 1–1.5 h per configuration across both sets. **One grant, serial.**
- **Coherence test (fixed now):**
  - On each set, rank the configurations by decided balanced accuracy and, separately, by false-accept rate.
  - **Coherent:** our gold's top configuration is in the top 2 on both public sets, and our gold's FA ordering
    has no pair inverted by more than its Wilson intervals allow.
  - **Suspect:** otherwise.
  - With 4–5 configurations this is a weak test. It catches a gold that's badly off, not a subtle bias, and the
    report says so.
- **Caveats, stated before the run:**
  - Public sets from 2020–2021 may be in the models' training data. LLM-AggreFact carries a contamination
    identifier for this, and the report notes it.
  - Neither set is about code. They anchor the *labelling and the verdict behaviour*, not the domain.
  - Our code-domain gold stays the measure of the studio's task.
- **Licence use:**
  - Evaluation only for all three.
  - Results are reported as numbers, and no dataset text is republished in rnd, which is public.
  - LLM-AggreFact is never used for training.
  - VitaminC's and HoVer's share-alike licences matter only if a derived dataset is ever shared, which this plan
    doesn't do.
