# Cross-family label check

Every gold label so far was written or relabelled by Claude models (Opus, Sonnet). This check has a model from
another family label a sample blind, so that errors Claude models share don't pass unseen. The gold labels
decide which verifier becomes offrig's default, so this is the targeted check Standing Rule 3 allows.

## Fixed before the run (2026-10-08)

**Sample** (`make_sample.py`, seed 20261008): 120 claims, 60 from each gold set.
- Every item a human ruling touched is in: the PR set's adjudicated items, and the reasoning set's split and
  flagged items.
- The rest are drawn at random by label, in proportion to each set.
- Result: grounded 27 supported, 28 unsupported, 5 cannot_tell; reasoning 27, 26 and 7.
- The blind file holds claim and evidence only. Ids are left out because their suffixes give the label away.

**Labeller:** `gemma4:31b` on the local Ollama (CUDA 13.4 backend), run with `run_labeller.py`.
- It gets the same instructions the Claude labellers had, one claim per call.
- Thinking on, temperature 0, reply constrained to a JSON schema.

**What counts:**
- Every disagreement between Gemma and the gold label is ruled on by R&D against the code.
- The result is the number of **gold labels found wrong**, not Gemma's agreement rate. Gemma is a labeller
  here, and a disagreement can be Gemma's error.
- **Pass:** at most 3 gold errors in 120 (2.5%). Each error found is fixed in its set.
- **Fail (4 or more):** both gold sets are held back from calibration. The stratum the errors fall in gets a
  full relabel by a non-Claude model before any default is named.
- A call that fails or returns no label is reported, and it counts as neither agreement nor error.

**Disclosure:** gemma4:31b is also a verifier candidate. Its calibration report will show these 120 claims
separately, since it has seen them.

## Result, 2026-10-08: PASS, 2 gold labels wrong in 120

Gemma answered 120/120 (26 min, median 8.7 s per claim, CUDA 13.4 system Ollama) and agreed with the gold
on **109/120**. R&D ruled on the 11 disagreements against the code (`disagreements.json`):

| n | id | gold | Gemma | ruling |
|---|---|---|---|---|
| 2 | diffhard-aspire-si-52-1u | unsupported | supported | gold stands: `"big"+"er"` is `"biger"`, so the guard returns None |
| 6 | prs-aspire-si-63-5s | supported | cannot_tell | gold stands (stated in the evidence's comment; see below) |
| 10 | docs-killswitch-t | supported | cannot_tell | gold stands (the doc comment says it restores pure keyword routing) |
| 14 | diff-offrig-8-4s | supported | cannot_tell | **gold wrong:** neither hunk shows the enclosing function is `launch` → cannot_tell |
| 59 | prs-offrig-31-5u | unsupported | cannot_tell | gold stands: the arm calls `job_pod_env(j)`, not `job_env` |
| 70 | prs-offrig-39-2s | supported | cannot_tell | gold stands (the constants and their comments state it) |
| 86 | prs-aspire-si-59-2s | supported | unsupported | **gold wrong (ambiguous):** "requires reasoning first" reads as a property order; reworded |
| 95 | prs-aspire-si-59-3u | cannot_tell | supported | gold stands: whether judges carry `False` or `None` is in `JUDGES`, not shown |
| 101 | prs-aspire-si-61-13s | supported | unsupported | gold stands, borderline: an empty sample shows no misses only vacuously |
| 116 | shuffle-floor-f | unsupported | cannot_tell | gold stands: the code pushes an error, not a note |
| 118 | prs-aspire-si-53-1s | unsupported | supported | gold stands: `uni` isn't a listed prefix (already ruled) |

**Two gold errors, against a limit of three: the gold sets stand.** Both are fixed:
- `diff-offrig-8-4s` is now cannot_tell, in the adjudicated reasoning file `../diffs/reasoning-diffs.jsonl`;
- `prs-aspire-si-59-2s` is reworded in `../prs/grounded-prs.jsonl`.
Each fix's note gives the reason.

**Disclosure: the labeller's instructions were stricter than the gold's definition.**
- Gemma was told "comments and docstrings are not proof of behaviour". The gold, and offrig's own verifier
  prompt, define supported as "the evidence states the claim, or it follows directly from the evidence"; a
  comment in the evidence is evidence.
- That mismatch explains four of Gemma's six cannot_tells (6, 10, 70, 116). Ruled against the product's
  definition, those gold labels stand.
- The `has_doc_comment` stratum in calibration shows how much each model leans on comments.

**Not a label finding but a preview:** Gemma said cannot_tell on 6 claims whose gold is decided. Under the
product prompt that would count toward its abstain rate in calibration.
