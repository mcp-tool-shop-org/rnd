# Retrieval benchmark: does offrig's index get worse if its embedder moves to the NPU?

Pre-registered 2026-10-09, before any query runs. offrig's default embedder stays nomic-embed-text, on the
CPU-only Ollama at 11490, until this reports and the Publisher reviews a design note.

## The options compared

| Option | Model | Device | Vector space | Index migration |
|---|---|---|---|---|
| **A (today)** | nomic-embed-text v1.5 (Ollama), with offrig's `search_document:`/`search_query:` prefixes | CPU (Ollama 11490) | — | — |
| **B** | bge-base-en-v1.5 | NPU (npu-serve) | new | every index re-embedded (`--rebuild`) |
| **C** | nomic-embed-text v1.5 itself, exported to OpenVINO | NPU | **same as A, if outputs match** | none, if the C-vs-A check passes |
| B-small (reported only) | bge-small-en-v1.5 (384-d) | NPU | new | re-embed |

**C goes first if it's feasible:** same model, faster device, no change of vector space. Its Hugging Face
version needs `trust_remote_code` (the custom NomicBert class). So pin the revision, read that code, then
export. C counts as "the same model" only if its vectors match Ollama's GGUF nomic with cosine ≥ 0.995 on the
benchmark's chunks. That bound applies to the **minimum** over every chunk and query, not the mean, and both
are reported. If not, C is a different model (say, 0.98 because of GGUF quantization) and is scored
like B.

**Prefixes, so the models are compared fairly:**
- nomic always gets its task prefixes, as offrig sends them.
- **bge is scored twice:** without its query instruction (what offrig sends today, since it adds prefixes
  only for nomic), and with "Represent this sentence for searching relevant passages: " on queries.
- **The no-instruction score is the one that counts,** because that's what offrig would do unchanged. The
  with-instruction score is reported, and it shows what an offrig change would buy.

## Corpus and queries

- **Corpus:** role-os at `ce91be8` and offrig at `a45fe53`, the two pinned sources of the grounded gold
  (`facts_roleos.py`, `facts_offrig.py`, `facts_roleos_docs.py`), exported with `git archive`. Each is indexed
  by `offrig index` in a scratch project, so the chunking and int8 vector storage are offrig's own.
- **Queries:** the grounded facts' claims, true and near-miss forms both (60 facts, 120 queries). Each
  query's target is the set of files its evidence spans cite.
- **Retrieval:**
  - **The primary score is embedding-only:** cosine top-k over the stored vectors, scored by the same
    query path. It isolates the embedder.
  - offrig's hybrid ranking (with BM25) is reported too when offrig exposes a search entry point. It isn't
    a CLI command today.

## Metric and decision rule

- **recall@5 by file:** a hit when any of the top 5 chunks comes from a target file. Also reported:
  recall@1 and @10, and MRR.
- **Truncated share, reported per option, descriptive only:** the share of the corpus's chunks whose
  token count, under that option's own tokenizer, exceeds its model window (bge-base: 512; nomic: its
  ladder top of 2048, so 0 by construction). A weak B then reads as "it was cut off", not "it's a worse
  model". Not part of the decision rule.
- **CI:** a 95% bootstrap over facts (the two forms of a fact resampled together), 2000 resamples,
  seed 20261009. It's reported for each option's recall@5 and for each difference from A.
- **B (or C, if it fails its match) may replace A only if both hold:**
  1. **Not worse:** the lower end of the 95% CI on (option − A) recall@5 is at or above **−0.05**, a
     non-inferiority margin of 5 points, with bge's no-instruction score.
  2. **The speed holds at scale:** a full `offrig index` of a larger project is at least **2× faster**
     end to end on the NPU than on 11490. The larger project is offrig at `a45fe53`, all of it, not the
     46-entry library.
- **C replaces A's device, not A's model,** if its vectors match (cosine ≥ 0.995) and the speed holds. No
  index changes.
- Anything else, or a CI too wide to decide: **A stays.** That's reported, not argued around.
- 60 facts is small. If the CI is wider than ±0.10, I'll widen the query set from the PR gold's grounded
  items before deciding, and record that here before those queries run.

**When it runs:** the bge and NPU legs run on the Intel side at any time. The nomic leg (options A and C's
match check) loads the CPU through Ollama 11490, so it runs after the overnight calibration chain, or only after
telling the Publisher, so the calibration's timings stay honest.

## What the design note must answer, whatever the result (the Publisher's points)

- **Index migration.** offrig already stamps each index with `embed_model` and `embed_dim`, and refuses on a
  mismatch with "run `offrig index --rebuild`" (`check_model` and `check_dim` in `index.rs`), so vectors
  can't mix silently. The note must say whether a default change re-embeds automatically or keeps refusing
  until a human rebuilds.
- **A second service.** Who starts npu-serve after a reboot (a scheduled task at logon, or offrig starting
  it), and what offrig does when it's down. The proposal: fail loudly with the start line, as it does today
  for 11490. Never fall back silently to a different model, since that's exactly the mixed-vector case.
- **Pinning.** The model revision and the OpenVINO version, recorded in the index's settings beside the model
  name.

## Amendments

- 2026-10-09, before any query has run (this remains pre-registration, not a post-hoc edit): report the
  per-option truncated share, so a model-window cut reads as such. The decision rule is unchanged.
- Same date: option C's match check (`nomic_parity.py`) guards the reference by measurement, not by
  the advertised window. `/api/show`'s num_ctx / context_length is recorded as context only; every
  A-fresh request carries `truncate: false` (a too-long input is a server error, never a silent cut);
  the five longest chunks (longest is 1619 nomic tokens, per
  `results/2026-10-09-nomic-chunk-lengths.json`) are embedded singly so the served `prompt_eval_count`
  is asserted against this tokenizer (BOS/EOS allowance 2), and once more exactly as offrig sends
  them (no truncate flag, no num_ctx) — which shows whether today's reference index itself truncates
  those chunks, a finding for the Publisher either way.
