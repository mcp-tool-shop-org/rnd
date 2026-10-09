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
