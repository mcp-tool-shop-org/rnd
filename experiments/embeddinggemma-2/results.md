# EmbeddingGemma 2 text benchmark: results

**Decision, by the rule written before any run (design §5): adopt B at 768.** Stage 1 passed. Stage 2 failed, so the 256-dimension cut is not adopted. Every figure here is measured, from `results/scores.json` and `results/per-query.jsonl`, scored on 2026-10-15 by `harness/score.py` against the round 2 key (sha256 `5747ac59…`).

- **Arm A:** nomic-embed-text, offrig's current embedder, on a CPU-only Ollama.
- **Arm B:** EmbeddingGemma 2, text only (271M parameters), float32, 768 dimensions, sentence-transformers on the CPU.
- **Arm B256:** B's vectors cut to 256 dimensions and re-normalised.

## Queries scored

93 of 100. Seven have no relevant chunk in the pool and are dropped from every mean, difference, bootstrap and group floor, as amendment 4 requires. Their ids and reasons were locked in `results/zero-relevance-lock.json` and pushed before any score was computed, and `score.py` stops if the queries it drops differ from the lock.

| Group | Scored |
|---|---|
| prose | 43 |
| code | 50 |

Dropped: l006, l008, l016, w059, w060, w061, w068. Neither group falls below 40.

## Stage 1: B against A

Paired by query, 10,000 bootstrap resamples, seed 7.

| Test | Result | Bar | |
|---|---|---|---|
| Mean dense ΔnDCG@10 (B − A), int8 | **+0.112** | ≥ +0.03 | pass |
| Its one-sided 95% lower bound | **+0.065** | > 0 | pass |
| Prose group, point estimate | +0.041 | ≥ −0.015 | pass |
| Code group, point estimate | +0.174 | ≥ −0.015 | pass |
| Mean hybrid ΔnDCG@10 (B − A) | +0.065 | ≥ 0.00 | pass |
| Its one-sided 95% lower bound | +0.029 | > −0.015 | pass |

The two-sided 95% interval on the dense difference is +0.056 to +0.172.

## Stage 2: B256 against B

| Test | Result | Bar | |
|---|---|---|---|
| Paired 95% lower bound on (B256 − B), one-sided as the harness tests it | **−0.062** | > −0.015 | **fail** |
| Mean (B256 − B) | −0.043 | | |
| Mean (B256 − A) | +0.070 | ≥ +0.02 | pass |

The two-sided 95% interval on (B256 − B) is −0.066 to −0.020, so it fails on either reading of "95% lower bound".

The cut keeps most of B's lead over nomic, but it costs B about 0.04 of nDCG@10, and the rule doesn't accept a loss that size. So B stays at 768 dimensions.

## nDCG@10 by run

| Run | All | Prose | Code |
|---|---|---|---|
| A dense, int8 | 0.549 | 0.536 | 0.560 |
| B dense, int8 | 0.661 | 0.577 | 0.734 |
| B256 dense, int8 | 0.619 | 0.543 | 0.684 |
| A hybrid | 0.634 | 0.565 | 0.694 |
| B hybrid | 0.699 | 0.613 | 0.773 |
| B256 hybrid | 0.697 | 0.635 | 0.751 |

Group figures are descriptive: at about 50 queries a group's 95% half-width is about ±0.07 (design §5).

## Secondary measures and diagnostics

- **Recall@5 (B − A):** +0.090. **MRR (B − A):** +0.015.
- **The code prefix doesn't earn its routing.** Embedding code queries with `task: code retrieval` instead of `task: search result` changes B's code-group nDCG@10 by −0.008 (B256: −0.003). Adoption can use the one search prefix for every query.
- **int8 is free.** int8 minus float32 nDCG@10 is +0.003 for B and +0.001 for B256.
- **The cost line doesn't trigger.** Wrapped in HTTP, B embeds 2.02 chunks a second against A's 5.10 (a 1,024-chunk sample), which is 0.395 of A. The rule asks for the Publisher's view on rebuild time only below a third.
- **Rebuild time.** In process, B embedded the 11,525 chunks in 4,425 s (2.6 a second, about 74 minutes). A took 2,046 s.
- **Index size.** B at 768 dimensions is the same size as A's index, since both are 768-dimension vectors.

## How the key was made

- The pool is 2,470 chunks: each run's top results, merged, stripped of arm and rank, and shuffled.
- Fresh Sonnet graders graded one query each.
- Round 1's blind audit failed two of four bars: binary κ 0.747 and raw disagreement 12.6%. Every disagreement had the auditor one step higher. Argon adjudicated the 63 disagreements, and its rulings became grader brief v2 (`harness/grader-brief-v2.md`).
- The whole pool was then regraded under brief v2. A fresh blind audit passed all four bars: Argon graded 16 queries the first audit hadn't seen, 481 chunks.

  | Measure | Result | Bar |
  |---|---|---|
  | Quadratic κ | 0.897 | ≥ 0.75 |
  | Binary κ | 0.869 | ≥ 0.80 |
  | Raw disagreement | 8.7% | ≤ 10% |
  | Two-step | 0% | ≤ 2% |

- The round 1 key and audit are kept as the record. The queries, intents, chunk text and grade reasons stay private. Only ids and numbers are published.

## What follows

Adoption is a separate change the Publisher reviews (design §5):
1. a CPU embedding endpoint for EmbeddingGemma 2 in npu-serve's Ollama-compatible shape;
2. offrig's `embed_url` pointed at it;
3. offrig's `task_prefix()` taught the EmbeddingGemma 2 prefixes, with no kind routing, since the code diagnostic didn't earn it;
4. `offrig index --rebuild`.

The site article follows after hands-on time, including the multimodal look (`design-multimodal.md`).
