# Argon consult, round 1: the EmbeddingGemma 2 retrieval benchmark design

**For Argon, from R&D. 2026-10-15.** Your last answer on EmbeddingGemma 2 was taken in full. The model is installed from Hugging Face. The NPU probe was skipped on precision. The benchmark runs on the CPU with explicit prefixes, and with re-normalization after truncation. One correction to that answer: the NPU sits on the CPU die and shares its memory, so there is no PCIe boundary. And the "vocabulary table pinned on the host" finding came from gemma4 on the 5090 under Ollama, not from the NPU. The skip stands on precision alone.

You have no repository access, so everything you need is below: what's installed, what offrig does today, and the design in full. Your findings are advice. R&D decides and records why. Nothing is counted until you've reviewed the design and the Director has approved it.

## What's installed, and what was learned on the way

- **Ollama can't serve it here.** The rig's Ollama was upgraded from 0.35.1 to 0.40.4. Every `embeddinggemma-2` tag in Ollama's library is an MLX tensor build. Ollama on Windows refuses them with "this model requires MLX support". Ollama's own notes put MLX on Apple Silicon by default. MLX kernels for CUDA are in a release candidate, and Windows support isn't stated.
- **So it runs through Hugging Face:** sentence-transformers 6.1.0, transformers 5.19.0, torch 2.14.1+cpu, in its own env. The 1.49 GB checkpoint at revision `914f7f8…` was hash-checked. The `[image]` extra is needed even for text-only, because the processor class imports Pillow.
- **Smoke run, not counted:** text-only, float32 on the CPU, 271M parameters. It loads in 2.5 s, encodes 4 short texts in 0.21 s, and returns 768 dimensions with no NaN. The right document ranked first at both 768 and 256 dimensions.
- **offrig today:** `offrig index` embeds with `nomic-embed-text` on a dedicated CPU-only Ollama (`embed_url`, default `http://127.0.0.1:11490`), never the shared server and never a GPU. Its `task_prefix()` adds `search_document: ` and `search_query: `. Changing the model or the dimension needs `offrig index --rebuild`.

## What to check

1. **Section 1:** does the difference between the arms answer the question? Is "nomic-embed-text in Ollama" against "EmbeddingGemma 2 in sentence-transformers" a fair runtime comparison, given section 3's "runtime fit" note?
2. **Section 4, the tasks:** is the query source sound, and are 80 queries (50 prose, 30 code) with graded keys enough? Is anything in the corpus or keys a leakage or bias risk? One example: R&D writes 40 of the queries and also writes the keys.
3. **Section 5, sample size and the rule:** check the arithmetic of the ±0.05 half-width and the 0.03 margin. Can the adopt-B256 rule be met at this size? If not, what should change: more queries, a different margin, or a non-inferiority framing for B256 against B?
4. **Missing arms:** should bge-base (already served on the NPU by npu-serve) be a third arm, or a reported reference only? And should EmbeddingGemma 2 in bfloat16 on the CPU be measured, given that the card recommends bf16 where supported and the 285K's CPU supports it?
5. **Anything in the model's own guidance the design gets wrong:** the prefixes, the `title:` field for chunks without a title, truncation, the 8K limit against the chunker.
6. **Verdict:** ready for the Director, or named changes.

## The design (rnd `experiments/embeddinggemma-2/design.md`)

# EmbeddingGemma 2 against nomic-embed-text, for the studio's retrieval

**Status:** design, 2026-10-15. Template: [A/B experiments](https://mcp-tool-shop-org.github.io/rnd/handbook/ab-experiments/). Nothing is counted until the design has had an outside review and the Director has approved it. Every run is on the CPU, with no card grant. The model and its env are installed (`entries/2026/embeddinggemma-2.md`).

## 1. The check in three sentences

1. **The question:** should the studio's retrieval embed with EmbeddingGemma 2 instead of nomic-embed-text? This covers offrig's memory index first, then R&D's library and readouts search.
2. **What each arm gets:**
   - **Arm A (production):** nomic-embed-text through a CPU-only Ollama, with offrig's own `search_document:` and `search_query:` prefixes.
   - **Arm B:** EmbeddingGemma 2, text-only, float32 on the CPU through sentence-transformers 6.1.0, with its card's prefixes, at 768 dimensions.
   - **Arm B256:** the same vectors cut to 256 dimensions and re-normalized.
   - Same corpus, same chunks, same queries, cosine top-k, no reranker.
3. **Why the difference answers it:** only the embedder (and its documented prefixes) changes. So a gap in ranking quality on the studio's own questions is the gap the switch would buy, and the CPU timing is what it would cost.

## 2. The treatment is actually taken

- Each arm uses its model's documented prefixes, because that is how it would be deployed. An arm without its prefixes would measure a misuse.
- **Manipulation check.** Each run's record stores, for the first query and the first document, the exact string the model received (prefix included), the vector's dimension, and its L2 norm (1.0 ± 1e-4 after normalization). A run without these is untreated and isn't counted.
- **Task groups, fixed before any run:**
  - **prose:** questions answered by a passage of studio prose (rnd entries, readouts pages, design docs);
  - **code:** questions answered by a source file or function (role-set and offrig source).
  
  EmbeddingGemma 2 claims its largest gain on code, so the groups are scored apart.

## 3. The arms differ only by the treatment

- **Leakage:** none possible. The keys are file and chunk ids, and no arm sees them.
- **Settings parity:**
  - the same chunker as offrig's index, run once, with the chunks frozen as a file;
  - the same truncation length for both models, the smaller of their limits (nomic 8,192, EmbeddingGemma 2 8,192), checked against the chunker's longest chunk.
- **Runtime fit:** each model runs in its real deployment runtime. nomic runs in Ollama. EmbeddingGemma 2 runs in sentence-transformers, since Ollama can't serve it on Windows. Throughput is reported per runtime and says so.
- **Order:** embed the corpus once per arm, then score the queries interleaved, in a seeded order. No caches persist between arms.
- **Concurrency:** one process at a time, matching offrig's indexer.

## 4. The tasks represent the decision

- **Corpus:**
  - rnd's `entries/`, `instruments/` and `experiments/**/*.md` at a pinned commit;
  - readouts-internal's KB pages at a pinned commit;
  - role-set's `src/` and offrig's `crates/*/src` at pinned commits.
  
  The chunk count and the pins go in the run record.
- **Queries: 80, drawn from real work.**
  - 40 from questions this studio actually asked: `rnd search` calls and `offrig_memory_search` calls in session logs. These are deduplicated by stem, and no two queries share a template.
  - 40 written from the work: the "why" and "where" questions the last two weeks' reviews and hand-backs turned on, each answerable from the corpus.
  
  The split is 50 prose and 30 code.
- **Keys:** each query lists its relevant chunks, graded 2 (answers it) or 1 (on topic). The keys are written by R&D, then audited by a reviewer who didn't write them, and frozen before any arm runs.

## 5. Measures, sample size and the decision rule

- **Primary measure:** nDCG@10 per query, averaged across queries. Comparisons are paired by query, with a 10,000-resample bootstrap 95% interval on the difference.
- **Secondary measures:**
  - recall@5;
  - MRR;
  - CPU embedding throughput (chunks per second) and index size;
  - each reported by group.
- **Size:** 80 queries. From published MTEB spreads, a per-query nDCG standard deviation of about 0.25 is plausible. That gives a paired half-width of roughly ±0.05 overall and ±0.08 for the 30 code queries. A 0.03 margin is therefore not resolvable on code alone. The overall rule below is what the size supports. The per-group reading is descriptive.
- **The decision rule,** written before any run:
  - **Adopt B256** when its overall nDCG@10 is at least 0.03 above A and the interval's lower bound is above 0. Neither group may fall more than 0.03 below A. Index size drops threefold against B, and it beats A at the same size or better.
  - **Adopt B at 768** instead, if B256 fails only the margin and B passes it.
  - **Otherwise keep nomic-embed-text,** and record the result. A null result is a result.
  - **Either way, report the CPU cost:** if B's throughput is below a third of A's, adoption also needs the Publisher's view on index rebuild time.
- **What adoption changes:** an Ollama-compatible CPU endpoint for EmbeddingGemma 2 (npu-serve's shape), offrig's `embed_url` pointed at it, `offrig index --rebuild`, and offrig's `task_prefix` taught EmbeddingGemma 2's prefixes. That is a separate change, reviewed by the Publisher.

## 6. Before the first counted run

1. The harness, a script under this folder, is reviewed by an outside model with its code inline.
2. A free validation run on 5 queries shows the manipulation check reading correctly in both arms, and the run record's pins and counts.
3. The design is reviewed by an outside model, and the Director approves it.
4. No card and no paid service is used. The CPU only, so no grant is needed. The run must not load anything onto the 5090: Ollama's call carries `num_gpu: 0`, and the sentence-transformers process has no CUDA build.

## 7. While running and after

- **Stop rules:** a NaN vector, a norm off by more than 1e-3, a missing manipulation record, or a key changed after freezing.
- A design change after any run is a dated amendment, and never touches the rule.
- **Results go in this folder:** per-query scores, the intervals by group, throughput, and every dropped run. The article on the site follows once the run and a short hands-on look (multimodal canon search, a quick fine-tune) have been done.

## Standards compliance

| Standard | Score | Evidence |
|---|---|---|
| PIN_PER_STEP | 2 | Model revisions (`914f7f8…`, nomic digest), library versions, corpus commits and seeds are pinned in the run record. |
| ANDON_AUTHORITY | 2 | The stop rules in section 7 halt the run. |
| NAMED_COMPENSATORS | n/a | Nothing irreversible: no publish, no pod, no index switch. Adoption is a separate change with its own review. |
| DECOMPOSE_BY_SECRETS | 2 | Corpus build, keys, arms and scoring are separate steps with frozen files between them. |
| UNCERTAINTY_GATED_HUMANS | 2 | Gates on design review, key audit and the Director's approval, before any counted run. |
| EXTERNAL_VERIFIER | n/a | No specialised claims. The key audit is a second reader, not a verifier pass. |
