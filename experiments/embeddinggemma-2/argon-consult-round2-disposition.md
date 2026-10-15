# Argon consult, round 2: the answer and the disposition | 2026-10-15

Argon's verdict on design v2: **ready for the Director,** with three one-line edits that need no further round. All three are taken in design v3.

| # | Finding | Disposition |
|---|---|---|
| 1 | The pool omitted B256 and the code-prefix diagnostic. B256's re-ranked hits at ranks 8–10 would go unjudged and score 0, which biases Stage 2 against B256. | **Taken.** B256 and the diagnostic join the blind pool. They add about one or two chunks per query. |
| 2 | Per-vector int8 at 256 dimensions carries about 1.6× the cosine noise of 768 dimensions. Stage 2 must read int8, as deployed, and the harness must cut and re-normalize in float before computing a fresh int8 scale. | **Taken.** Stage 2 reads int8, with float logged. The order of operations is written into section 3. |
| 3 | The hybrid guard is too loose. BM25 is identical in both arms, so a real dense gain should never leave hybrid negative. | **Taken.** Mean hybrid Δ ≥ 0.00 and a one-sided 95% lower bound above −0.015. |

Confirmed:
- Dense stays primary and hybrid a guard: RRF dilutes a dense gain to roughly half in hybrid.
- Pooling dense and hybrid together reduces bias.
- The power statement stands: about 33–44% at +0.03 and about 80% at +0.05–0.06, with the false-switch rate under 5%. Argon calls +0.03 the indifference boundary and +0.05–0.06 the effect worth switching for.

**Next:** design v3 goes to the Director for approval. Nothing runs before it.
