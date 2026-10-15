# Argon consult, round 3: the harness review and the intent review | 2026-10-15

**Harness verdict:** named changes, then run with no round 4. **Intent review:** 23 of 100 lines changed.

## The harness

| # | Finding | Disposition |
|---|---|---|
| Fidelity | `fts_query`, `quantize`, the dequantize-then-cosine order and `rrf`'s tie order match offrig. The rounding mode differs (half-to-even against half-away-from-zero), and so does Unicode `isalnum`, but neither can move a ranking on this corpus. | Recorded. No change. |
| Stage 2 bound | `score.py` used the 2.5th percentile, while every other gate is the one-sided 95% (5th percentile). | **Taken** as a clarification, settled before any run (amendment 3). The design's text came from round 1's "95% CI", so it could be read either way. The 5th percentile matches the rest of the design. |
| "KeyError" on code-prefix runs | Claimed as a crash. | **Not a crash:** the means filter already excludes the code-only runs, as Argon's own trace concludes. Both code-prefix diagnostics are now reported explicitly, so a later edit can't trip on it. |
| Key completeness, key hash | The key check passed if a query had any grade at all, and the scores weren't bound to the key. | **Taken.** `score.py` refuses a key that misses any pooled chunk, and writes `keys_sha256`. |
| Norm stop rule | `embed.py` recorded norms but didn't stop on them. | **Taken.** It stops on a wrong dimension or a norm off by more than 1e-3. |
| Intent in the pool | Pooled rows didn't carry the locked intent. | **Taken.** `pool.py` adds the intent and any grading note, and refuses an intent table that doesn't match the queries. |
| Tokenizer pin | The validation tokenizer wasn't pinned to the revision. | **Taken.** |
| Titled diagnostic | Promised by the design but not run. | **Dropped, and recorded** (amendment 3): offrig's header already puts the source and title in every chunk, and it would cost a second full embedding. |
| Header in body | Check whether offrig stores the header in `body`. | **Checked:** it does. The rebuild's first chunk begins `[corpus/offrig/... · code · ...]`. |
| Pool size | 26.8 per query is fine. Diverse pools give the benchmark leverage. | Recorded. |

## The intents

All 23 of Argon's changes were taken. Most narrow a two-part line to one question, or keep the query's form (where, how, why). The keyword queries get a single most-plausible reading. w055, w060 and w078 carry a split-answer note that graders see beside the intent. The frozen table is private with the queries; its sha256 is `67e4936d…6e186`.
