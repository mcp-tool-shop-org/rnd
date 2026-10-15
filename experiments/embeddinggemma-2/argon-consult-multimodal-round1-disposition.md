# Argon, multimodal round 1: the disposition

**Argon's verdict (2026-10-15):** hold for five named changes. R&D's rulings follow, in Argon's order. "Measured" means R&D read it on the rig on 2026-10-15. The revised design is `design-multimodal.md`, revision 2.

## Two facts in R&D's round 1 were wrong

- **"About 2,900 images on disk."** Measured now, the four query projects hold 2,104 image files. 1,451 of them are generation outputs in `outputs/<folder>/`, and 1,246 remain after removing byte-identical copies. Of the 2,085 records across all projects, only 868 point at a file that exists. star-freight's 1,182 records have no images on disk.
- **"Where the record names its lineage."** None of the 385 query records does. `iteration` is null in every record. The 60 records with a `lineage` object are all star-freight's, and their fields are null.

## The five changes

| # | Argon's change | Ruling | Why |
|---|---|---|---|
| 1 | Restrict the pool to recorded images; use filtered strict MRR that masks same-lineage siblings | **Amended** | Recorded images alone would leave 369 distractors, and rustline would have none except its own other queries (all 172 of its records on disk are queries). The pool becomes generation outputs, with byte-identical copies merged (172 targets had one) and dHash near-duplicates masked. That covers Argon's real concern: unverifiable copies of a target. Contact sheets, `training/`, `exports/`, `inbox/` and `inputs/` are left out. With no lineage data the filtered key can't be computed, so the strict key stays primary and same-subject siblings stay as distractors. That noise is equal for both arms. |
| 2a | In T2, embed descriptions with the document prefix | **Accepted, locked** | The card is clear. Comparing both prefixes in validation would add a forking path. |
| 2b | Token-count all 385 descriptions; fixed padding at 64 | **Accepted** | |
| 3a | Replace the −0.05 per-project floor | **Accepted: the upper-bound form** | A project vetoes only when it is significantly worse (its one-sided 95% upper bound on G − S is below 0). Argon's arithmetic checks: at n = 41 the −0.05 floor falsely vetoes a tie 14.3% of the time. |
| 3b | Drop G256 from the rule | **Accepted** | Text adopted 768, so images match it. 512 and 256 are reported as a descriptive curve. |

**Recorded for the Director:** +0.05 is a bar on the sample mean. A true gain of +0.05 clears it half the time, and 80% power needs a true gain of about +0.063 (Argon's arithmetic, checked).

## Audio, for later

Argon's sizing is recorded for when ai-jam-sessions or vocology build a labelled library:
- 120–150 text-to-audio queries;
- a pool of 500–1,000 clips;
- two baselines: Whisper transcripts into EmbeddingGemma 2's text model for speech, and CLAP for music and effects.

**Unverified:** the licences of the public sets Argon named (Clotho v2.1, FSD50K, ESC-50) and the MIEB and MMEB dimension figures it quoted from a library page. A licence that will be relied on gets checked before any use.

## Round 2 (2026-10-15): approved as written

Argon approved revision 2 with no change to the design:
- the pool, byte-deduplicated;
- the near-duplicate mask at dHash ≤ 10 of 256;
- the strict key, with same-subject siblings left in as distractors. The approved-only pool and recall@5 and @10 give the sibling-free readings.

It asked for two guards in the harness, now in step 6 of the design:
- mid-rank reciprocal rank, so file order never breaks a tie;
- a token gate that logs the offending ids and halts before any embedding.

Next: the Director's approval of the design. Then the harness, its outside review, and the free validation run.
