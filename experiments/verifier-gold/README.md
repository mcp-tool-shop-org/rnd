# Verifier gold sets: grounded claims

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
