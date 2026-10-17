# Argon design review: local builders, Wave 1 (J2), with amendments A and B (2026-10-17)

**From:** R&D, for Browser Argon, through the maintainer. **Kind:** a design review before any counted run (the
model-comparisons template requires one). **Bundle:** `local-builders-DESIGN-<commit>.txt`, the design line-numbered
(`===== FILE: experiments/local-builders/DESIGN.md =====`). Template: the rnd handbook's "model comparisons" (section 0,
licences first, is new as of 2026-10-17).

**Answer format:** start with `## 2026-10-17 · rnd · local-builders design · <commit>`, then numbered findings, each
with a line reference and a severity: `blocking` (fix before Wave 1), `before Wave 2`, or `not blocking`. Quote the
design's line rather than paraphrasing it. Mark any factual claim about a tool or a model (Aider flags, llama-server
behaviour, licence text) `checked` (you read the primary source) or `unsure`.

## What changed since your last look

- **Amendment A:** J1 (writing Stage 1 items) now runs inside role-set, against role-set's own incumbent writer and
  critic pair, and has become the Stage 1 regeneration pilot. It's not in this review's scope.
- **Amendment B:** J2 (fixing real bugs through Aider) moves:
  - **onto the pinned stack:** `llama-server` at one binary, built with CUDA 13.4 and SASS for sm_80/90/100, with
    the 13.4.2 toolkit's cudart and cuBLAS pinned by hash;
  - **onto GGUFs we convert ourselves** from the makers' weights;
  - **onto a loopback logging proxy** that records top-5 log-probabilities for every call (`generations.jsonl`,
    `rnd abmine` format), as provenance evidence;
  - **onto Colab, with an open unit budget.**
- **Candidates now include** Apache-2.0 models, under the reworded licence rule (allowed unless a contract or
  licence restricts the use), plus Nemotron-3.5-Bolt-74B (NVIDIA's 24 GB quantisation-aware build) and
  R1-Distill-Qwen-32B.

## Questions

1. **The comparison holds the harness fixed and varies only the model?** Check:
   - Aider at one version, the same edit format (and when a documented exception is fair);
   - the same task prompt, the same caps (30 turns, 15 minutes);
   - one serving stack for all.

   Does serving Aider through an OpenAI-compatible endpoint, with each model's own embedded chat template, keep each
   model "in its native runtime" fairly? Compare it with Ollama's `ollama_chat` route.
2. **The logging proxy.** Can a proxy that adds `logprobs: true, top_logprobs: 5` change what the model generates,
   or how Aider parses it, under llama-server's OpenAI-compatible API? Name any interaction, for example streaming,
   tool calls, or slower sampling. If so, what's the cleanest way to record the log-probabilities without touching
   the run?
3. **Mixed quantisation.** Most candidates run Q8_0 that we convert ourselves. Bolt runs NVIDIA's 2-bit
   quantisation-aware build. Is ranking them together fair, or should Bolt's arm be labelled separately in the
   report?
4. **The task bank and the recall guard:**
   - tasks from fixes merged after every candidate's stated training cutoff;
   - the parent commit exported with `git archive` into a fresh repo;
   - the PR's test added and the CHANGELOG line removed;
   - at most 2 tasks per module.

   Is that enough to stop recall? What else leaks the fix (issue text, docstrings, nearby tests)?
5. **The decision rule:**
   - a screen, not a winner;
   - a model leaves if it fixes 2 or fewer of 20, or crashes on more than 20% of runs;
   - the top 3 by P(best) go to Wave 2.

   With 20 tasks, a difference smaller than about 35 points can't be shown. Is 20 too few for a useful screen?
   What would you change for the cost, given the units are now open?
6. **Containment.** Each builder:
   - runs in a detached worktree with no remotes;
   - has its proxy variables pointed at a dead port;
   - has pip and npm offline;
   - reaches only the logging proxy on loopback.

   Is that complete for an Aider process on a Colab VM? Name any route out, such as git hooks, Aider's own update
   check, or model-requested shell commands.
7. **Anything that makes the J2 measure** (the target test passes, the full suite stays green, and only allowed paths
   changed) **not mean "mergeable before review"**, for example tests that pass by deleting assertions, or skipped
   tests.

The maintainer approves the design after your review and R&D's disposition.
