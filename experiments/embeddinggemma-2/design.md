# EmbeddingGemma 2 against nomic-embed-text, for the studio's retrieval

**Status:** design v3, 2026-10-15, after Argon's rounds 1 and 2 (`argon-consult-round1.md`, `argon-consult-round2.md`, with dispositions). Round 2 found it ready, with three line edits, all taken. Template: [A/B experiments](https://mcp-tool-shop-org.github.io/rnd/handbook/ab-experiments/). Nothing is counted until the Director approves this design. Every run is on the CPU, with no card grant. The model and its env are installed (`entries/2026/embeddinggemma-2.md`).

## 1. The check in three sentences

1. **The question:** should the studio's retrieval embed with EmbeddingGemma 2 instead of nomic-embed-text? offrig's project index comes first, then R&D's library and readouts search.
2. **What each arm gets:**
   - **Arm A (production):** nomic-embed-text through a CPU-only Ollama, with offrig's `search_document: ` and `search_query: ` prefixes.
   - **Arm B:** EmbeddingGemma 2, text-only, on the CPU through sentence-transformers 6.1.0, with its card's prefixes, at 768 dimensions. The dtype is float32 or bfloat16, fixed by the validation run in section 6.
   - **Arm B256:** B's vectors cut to 256 dimensions and re-normalized.
   - Same frozen chunks, same queries, same scoring.
3. **Why the difference answers it:** only the embedder and its documented prefixes change. So the gap on the studio's own questions is what a switch would buy, and the CPU timing is what it would cost.

## 2. The treatment is actually taken

- **Arm B's load is pinned:** `SentenceTransformer("google/embeddinggemma-2", revision="914f7f8…", device="cpu", config_kwargs={"vision_config": None, "audio_config": None})`. The run record shows 271M parameters. A run that loads the 740M graph stops.
- **Document strings carry the same text in both arms.** offrig opens every chunk with a header line, `[source · kind · title]`, which it embeds with the chunk. So the title context is already inside the chunk text, and neither arm gets a separate title:
  - Arm A embeds `search_document: {chunk}`.
  - Arm B embeds `title: none | text: {chunk}`.
  - A titled form, `title: {source} | text: {chunk}`, is logged as a diagnostic only.
- **Query prefixes:**
  - Arm A uses `search_query: {q}`.
  - Arm B uses `task: search result | query: {q}` for every query. offrig emits one prefix per search today.
  - On the code group, `task: code retrieval | query: {q}` is scored as a zero-re-index diagnostic. If it helps, kind-routed prefixes are part of the adoption change.
- **Manipulation check:** for the first query and the first chunk of each arm, the record stores the exact string the model received, the vector's dimension, and its L2 norm. That's 768 and 1.0 ± 1e-4 for B, and 256 and 1.0 ± 1e-4 for B256. A run missing these is untreated and isn't counted.
- **Task groups, fixed before any run:** **prose** (answered by a passage of studio prose) and **code** (answered by a source file or function). They are scored apart.

## 3. The arms differ only by the treatment

- **Leakage:** none. Keys are chunk ids, and no arm sees them. `experiments/embeddinggemma-2/` is excluded from the corpus.
- **Chunks:** offrig's own chunker (`MAX_CHARS` 2000, about 500 tokens), run once, with the chunks frozen as a file.
- **Context:** Ollama's nomic build reports a context length of 2048 (`ollama show`, 2026-10-15), and EmbeddingGemma 2 takes 8,192. The validation run tokenizes every frozen chunk with both tokenizers (WordPiece and Gemma's) and records the longest. It stops if any chunk exceeds 2,048 in either. At 2,000 characters none is expected to.
- **Batching:** both arms embed in batches of 32, offrig's `BATCH`.
- **Storage:** offrig stores int8-quantized vectors, each with its own scale, and scores `cosine_q`. Both arms are scored after the same int8 quantization, as deployed. Float scoring is a diagnostic. B256 works in float first: cut the 768-dimension float vector to 256, re-normalize it, then compute its own int8 scale. It never cuts an already-quantized 768-dimension vector. Stage 2 reads int8, with float logged to separate the Matryoshka loss from the rounding loss.
- **Ranking, two readings:**
  - **dense:** cosine top-k alone. This isolates the embedder, and it's what the decision rule reads.
  - **hybrid:** offrig's ranker as shipped (BM25 top 50 and cosine top 50 fused by RRF, top 20). This is what users get, and it's a guard in the rule.
- **Timing:**
  - Throughput is measured in each arm's own runtime, at batch 32: Ollama over loopback HTTP for A, in-process `encode()` for B.
  - B is also timed behind a minimal local HTTP wrapper of the npu-serve shape, so the production cost isn't flattered by in-process calls.
  - Both readings are reported, and the rule's cost line reads the wrapped one.
- **Order:** each arm embeds the corpus once. Queries run interleaved, in a seeded order. No cache persists between arms. One process at a time.

## 4. The tasks represent the decision

- **Corpus,** at pinned commits:
  - rnd's `entries/`, `instruments/` and `experiments/**/*.md`, minus this experiment's folder;
  - readouts-internal's KB pages;
  - role-set's `src/` and offrig's `crates/*/src`.
  
  The chunk count and the pins go in the run record.
- **Queries: 100, 50 prose and 50 code.**
  - **From session logs:** the first query issued for each information need in `rnd search` and `offrig_memory_search` calls. A reformulation made after seeing a result is dropped, because it would favour the embedder that produced that result.
  - **Written:** the rest come from commit messages, PR descriptions and review hand-backs. Their author doesn't open the corpus while writing them, so they don't echo a target chunk's wording.
  - Deduplicated by stem. No two queries share a template. Frozen before any arm runs.
- **Keys, by blinded pooling:**
  1. Freeze the queries.
  2. Run A, B and B256 to get each query's top 10 chunk ids, plus the code-prefix diagnostic on the 50 code queries. Dense and hybrid are pooled together, so Stage 2 and the diagnostic never score an unjudged chunk as 0.
  3. Merge and deduplicate them into one pool per query. Strip model identities and ranks, and shuffle the order.
  4. R&D grades every pooled chunk 0, 1 or 2: no, on topic, answers it.
  5. A second reviewer, who didn't grade, audits the grades.
  6. Freeze the key file before any metric is computed.

## 5. Measures, sample size and the decision rule

- **Primary measure:** dense nDCG@10 per query, averaged. Comparisons are paired by query, with a 10,000-resample bootstrap.
- **Secondary measures,** each reported by group:
  - recall@5 and MRR;
  - hybrid nDCG@10;
  - throughput, in-process and HTTP-wrapped;
  - index size;
  - the code-prefix and titled-document diagnostics.
- **Size and power, stated plainly.** Take σΔ, the per-query SD of the paired difference, as 0.20–0.25 (Argon's derivation from cross-model correlation). Then at 100 queries:
  - The SE is 0.020–0.025.
  - A one-sided 95% bound needs an observed gain of 0.033–0.041.
  - The design has 80% power to detect a true gain of about 0.05–0.06. A true gain of +0.03 passes only about a third of the time.
  
  That's accepted. Switching has a cost (an endpoint, a re-index, prefix routing), so a small true gain reading as "keep nomic" is the cheaper error. Group results are read descriptively: at 50 queries a group's 95% half-width is about ±0.07.
- **The decision rule,** written before any run:
  - **Stage 1, superiority (B against A).** Switch to EmbeddingGemma 2 when all of these hold:
    - mean dense ΔnDCG@10 (B − A) is at least +0.03;
    - its one-sided 95% bootstrap lower bound is above 0;
    - neither group's point estimate is below −0.015;
    - the mean hybrid ΔnDCG@10 (B − A) is at least 0.00, and its one-sided 95% bootstrap lower bound is above −0.015.
    
    Otherwise keep nomic-embed-text.
  - **Stage 2, compression (B256 against B, run only if Stage 1 passes).** Adopt B256 when both hold:
    - the paired 95% bootstrap lower bound on (B256 − B) is above −0.015;
    - mean (B256 − A) is at least +0.02.
    
    Otherwise adopt B at 768.
  - **The cost line:** if B's HTTP-wrapped throughput is below a third of A's, the switch also needs the Publisher's view on rebuild time.
  - A null result is a result. It's recorded either way.
- **What adoption changes, as a separate change the Publisher reviews:**
  - a CPU embedding endpoint for EmbeddingGemma 2 in npu-serve's Ollama-compatible shape;
  - offrig's `embed_url` pointed at it;
  - offrig's `task_prefix()` taught EmbeddingGemma 2's prefixes, kind-routed if the code diagnostic earns it;
  - `offrig index --rebuild`.
- **bge-base on the NPU is not an arm.** Its 512-token limit would clip chunks the other arms read whole. It may be scored against the frozen pool as a footnote, with the share of chunks over 512 tokens.

## 6. Before the first counted run

1. **The harness** is a script in this folder. An outside model reviews it with its code inline, and every finding is checked against the code.
2. **A free validation run, 5 queries,** that checks:
   - the manipulation records in all three arms;
   - the tokenizer pre-check, where any chunk over 2,048 tokens stops the run;
   - **the dtype gate:** encode 50 chunks in float32 and in bfloat16, require pairwise cosine ≥ 0.999, and fix the faster as Arm B's dtype, recorded;
   - both throughput readings.
3. **The Director approves the design.** No card and no paid service is used: Ollama's calls carry `num_gpu: 0`, and B's torch build has no CUDA.

## Amendment 1, 2026-10-15, before any counted run

- **The queries as frozen.** The log mining found 29 distinct first queries. Discarding shell placeholders, generic or self-referential ones (`experiment`, `embeddinggemma`), and one near-duplicate (`npu` beside `openvino npu`) left 19, all short keyword searches and all prose. The other 81 were written by a Sonnet agent from commit messages, PR text and review threads, with the corpus closed: it ran no reads, greps or file shows on the four repos. That was done because R&D had read parts of offrig's and role-set's code during reviews. The split is 50 code and 50 prose (31 written, 19 logged). The frozen file's sha256 is `8430973c…7ce87`.
- **A query whose pool holds no chunk graded 1 or 2 is dropped** and reported by id. It carries no information about either arm, since every arm scores 0. The rule's thresholds stay as written. If the drop takes either group below 40 queries, that is reported beside the result, because the power statement assumed 50 per group.
- **Arm A's server:** offrig's documented start line hides CUDA only. On Ollama 0.40.4, Vulkan then exposes the RTX 5090, and the log shows it as inference compute. So arm A's server runs with `GGML_VK_VISIBLE_DEVICES=-1 OLLAMA_VULKAN=0 OLLAMA_IGPU_ENABLE=0` as well. Its log reports CPU-only compute, and `embed.py` stops if `/api/ps` shows any VRAM. offrig #64 fixes the documented line.

## Amendment 2, 2026-10-15, before any counted run

- **Grading follows the [relevance grading](https://mcp-tool-shop-org.github.io/rnd/handbook/relevance-grading/) template.** Argon drafted it at the Director's request, and R&D adapted it for the studio.
  - R&D writes a locked intent line for each query, without opening the corpus, and Argon reviews the 100 lines before grading starts.
  - Sonnet agents grade on the Claude Code plan: a fresh agent per query, at most five chunks at a time, `reason` before `grade`.
  - Argon audits blind.
- **The audit:** 16 queries (8 code, 8 prose), chosen for a high share of chunks found by only one or two arms. Measured on the dry run, the pool averages about 27 chunks per query, so that's about 430 chunks in five pastes.
  - **Gates:** quadratic weighted κ ≥ 0.75, binary κ (0 against 1–2) ≥ 0.80, raw disagreement ≤ 10% and two-step ≤ 2%.
  - A pass freezes the Sonnet grades for the whole pool. A fail means revising and regrading the whole pool.
- **The corpus was rebuilt before any counted run, with project-relative paths.** The first build indexed it by absolute path, so every chunk header read `E:/AI/eg2-bench/corpus/…` where offrig writes a project-relative path in production. The rebuild indexes `corpus/` from inside the project. The count is unchanged at 11,525. The first build is kept aside, not deleted. The pins are in `results/corpus-manifest.json`; offrig's `main` had moved to `0600904` by the rebuild.
- **The pool is the 8 decision runs:** A, B and B256 in dense-int8 and hybrid, plus the code-prefix dense reading for B and B256. The float readings and the code-prefix hybrids are diagnostics. A chunk that only they surface counts 0, and that is stated beside them.

## Amendment 3, 2026-10-15, before any counted run

Argon's round 3 harness review (`argon-consult-round3.md`, disposition in `argon-consult-round3-disposition.md`) and his intent review are both answered. Changes:

- **Stage 2's bound is the one-sided 95% lower bound, the 5th bootstrap percentile.** The text said "the paired 95% bootstrap lower bound", which came from round 1's "95% CI" and could be read as the 2.5th percentile. Every other gate in this design is one-sided 95%, so the 5th percentile is the reading. This is settled before any run.
- **Harness fixes:**
  - `embed.py` stops on a wrong dimension or a norm off by more than 1e-3, as section 7 says.
  - `score.py` refuses a key that misses any pooled chunk, writes `keys_sha256` into the scores, and reports both code-prefix diagnostics explicitly.
  - `pool.py` carries each query's locked intent, and any grading note, into every pooled row.
  - `validate.py` pins the tokenizer to the model revision.
- **The titled-document diagnostic is dropped.** offrig's header already puts the source and title inside every chunk's text, so a `title: {source}` prefix would only repeat it. It would also have cost a second full embedding, about 70 minutes on the CPU. It isn't run, and its absence from the scores is intended.
- **Intents locked:** 100 lines. The auditor changed 23: 21 were narrowed to one question, or re-read for keyword queries, and three carry a split-answer note for graders. The frozen table's sha256 is `67e4936d…6e186`, kept private with the queries.

## Amendment 4, 2026-10-15, after grading, before any score

- **Queries with no relevant chunk are dropped** (Argon's ruling, `argon-consult-audit.md` Part B):
  - from every mean, paired difference, bootstrap and group floor;
  - they are reported with their count, ids and why the corpus can't answer each;
  - the excluded ids are locked after the audit's adjudication and any regrade, before the arms are unsealed;
  - the stage 1 thresholds stand at the N that remains.

  The reason: nDCG is undefined when no chunk is relevant, and scoring it 0.0 adds a synthetic tie that pulls the mean difference toward 0. In round 1 the four were l006, w059, w060 and w068. A term search over all 11,525 chunks found no answer to any of them.
- **The round 1 audit failed two bars:**

  | Measure | Result | Bar | |
  |---|---|---|---|
  | Quadratic weighted κ | 0.821 | ≥ 0.75 | pass |
  | Binary κ | 0.747 | ≥ 0.80 | miss |
  | Raw disagreement | 12.6% (63 of 501) | ≤ 10% | miss |
  | Two-step (0 against 2) | 0% | ≤ 2% | pass |

  All 63 disagreements have the auditor one step higher. As amendment 2 requires, the brief is revised and the whole pool is regraded. The 63 go to Argon first to adjudicate (`argon-consult-audit-round2.md`). The round 1 key (sha256 `c4c35891…`) and the audit are kept as the record, never overwritten.

## 7. While running and after

- **Stop rules:**
  - a NaN vector;
  - a norm off by more than 1e-3;
  - a missing manipulation record;
  - the 740M graph loaded;
  - a chunk over 2,048 tokens;
  - a key changed after freezing.
- A design change after any run is a dated amendment, and never touches the rule.
- **Results go in this folder:** per-query scores, intervals by group, both readings, throughput, and every dropped run. The site article follows the run and a short hands-on look (multimodal canon search, a quick fine-tune).

## Standards compliance

| Standard | Score | Evidence |
|---|---|---|
| PIN_PER_STEP | 2 | Model revision `914f7f8…`, the nomic digest `0a109f42…`, Ollama 0.40.4, library versions, corpus commits, the dtype and seeds are all in the run record. |
| ANDON_AUTHORITY | 2 | The stop rules in section 7 halt the run. |
| NAMED_COMPENSATORS | n/a | Nothing irreversible. Adoption is a separate, reviewed change. |
| DECOMPOSE_BY_SECRETS | 2 | Corpus, queries, pooled keys, arms and scoring are separate steps, with frozen files between them. |
| UNCERTAINTY_GATED_HUMANS | 2 | Gated on the outside review, the key audit and the Director's approval, before any counted run. |
| EXTERNAL_VERIFIER | n/a | No specialised claims. The key audit is a second reader. |
