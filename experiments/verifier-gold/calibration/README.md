# Calibrating offrig's default verifier

Which local model becomes offrig's default verifier, chosen by `offrig verify calibrate` (offrig#44, oracle
mode: each claim's own context is the evidence) against the gold sets in `..`. This file fixes the protocol
before any candidate runs.

## Fixed before the runs (2026-10-08)

**Gold** (cross-family check passed, `../crossfamily/`):
- grounded: `grounded.jsonl` + `prs/grounded-prs.jsonl`;
- reasoning: `diffs/reasoning-diffs.jsonl`.

**Rule:** offrig's default rule, as merged in #44.
- Per check type: the false-accept upper bound below 0.10 (the primary rate counts gold unsupported and gold
  cannot_tell together), abstain at most 0.20, decided balanced accuracy at least 0.80, and at least 100
  unsupported claims.
- Any model-caused unusable outcome fails the rule.
- The default is **the cheapest model that passes both grounded and reasoning.**

**Selection and confirmation:**
1. **Smoke** (`smoke.sh`): 4 tune claims per check type per model, to settle `--think` (a model without
   thinking refuses `think`) and `--structured`, and to measure seconds per claim. Smoke results choose
   settings only, never a model.
2. **Selection on `--split tune`,** smallest model first, every model with its smoke-settled settings.
3. **Confirmation:** the chosen model runs once on `--split heldout`. **The held-out numbers are the
   headline,** so the choice isn't scored on the data it was picked on. If it fails on held-out, no default is
   named: that is reported, and the next model is not quietly promoted.

**Candidates** (local, on disk, families other than the generator's): qwen3:8b, llama3.1:8b, qwen3:14b,
mistral-small:24b, granite4.1:30b, gemma4:31b.
- **gemma4:31b has seen the 120 cross-family sample claims.** Its report also shows its result without them.

**Where:** the local 5090 on the CUDA 13.4 system Ollama, overnight, in blocks the Publisher grants. Not the
cloud: a stock RunPod Ollama runs CUDA 13.0, against the 13.4 rule. Runs use a scratch `--project`, so the
schema-v6 store never meets an older offrig MCP server.

**Reported per model:**
- every metric row, including the cannot_tell row and the false-accept rate on unsupported only;
- the strata `has_doc_comment`, `self_referential` and `origin`;
- unusable counts and seconds per claim.
