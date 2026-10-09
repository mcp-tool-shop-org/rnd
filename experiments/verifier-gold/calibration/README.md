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

**Amendment, 2026-10-08, before any candidate ran:** the reasoning set can't be split. The rule needs at
least 100 unsupported claims per run, and reasoning has 50 in tune and 61 in held-out (grounded has 128 and
113). Split, no model could pass on reasoning, so the protocol as first written could never name a default.
- **grounded:** unchanged. Select on tune; held-out confirms and is the headline.
- **reasoning:** runs on `--split all` (246 claims, 111 unsupported), for selection and for the rule.
- **The cost:** reasoning has no held-out check, so the chosen model's reasoning numbers are in-sample.
  Selection bias stays small, because the rule takes the cheapest model that passes, not the best score. The
  report says so next to the numbers.
- **The fix:** about 90 more reasoning behaviours, so each split reaches 100 unsupported; then reasoning gets
  a held-out confirmation too. That's asked of the Publisher, who owns the reasoning set.
- R&D missed this when the protocol was first committed; it was caught while writing the run script, before
  any model ran.

**Candidates** (local, on disk, families other than the generator's): qwen3:8b, llama3.1:8b, qwen3:14b,
mistral-small:24b, granite4.1:30b, gemma4:31b.
- **gemma4:31b has seen the 120 cross-family sample claims.** Its report also shows its result without them.

**Where:** the local 5090 on the CUDA 13.4 system Ollama, overnight, in blocks the Publisher grants. Not the
cloud: a stock RunPod Ollama runs CUDA 13.0, against the 13.4 rule. Runs use a scratch `--project`, so the
schema-v6 store never meets an older offrig MCP server.
- **Rest (Director's standing rule, 2026-10-08):** the card rests 15 minutes with nothing loaded between runs.
  `chain_step.sh` rests before it loads each model after the first, and refuses to load if anything is
  still on the card. Six models add about 75 minutes of rest.
- **Pauses:** a health monitor may pause the chain mid-model. A step whose runs are incomplete exits 3 and
  the chain stops there. Rerunning the same step resumes it, and no completed claim is asked again.

**Reported per model:**
- every metric row, including the cannot_tell row and the false-accept rate on unsupported only;
- the strata `has_doc_comment`, `self_referential` and `origin`;
- unusable counts and seconds per claim.
