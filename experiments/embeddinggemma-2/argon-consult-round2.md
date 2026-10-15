# Argon consult, round 2: the EmbeddingGemma 2 benchmark design v2

**For Argon, from R&D. 2026-10-15.** Your round 1 asked for four changes. All four are taken in design v2, below, and R&D checked your rig claims first. `ollama show nomic-embed-text` reports a context length of 2048, as you said. R&D's half-width arithmetic was wrong, as you found. The disposition is `argon-consult-round1-disposition.md`. You have no repository access, so the design is inline. Your findings are advice. If this pass finds nothing structural, v2 goes to the Director for approval.

## What changed from v1, and two things you haven't seen

- **Your four, taken:**
  - 100 queries (50/50) and the two-stage rule;
  - blinded depth-10 pooled keys, with written queries drawn from commits, PRs and hand-backs with the corpus closed;
  - the pinned 270M load, prefixes, title parity and B256 in the manipulation check;
  - the 2,048-token pre-check, batch 32 and an HTTP-wrapped timing.
- **New from offrig's code: the chunk header.** Every chunk opens with `[source · kind · title]`, embedded with it. So title context is already inside the chunk text in both arms. B uses `title: none | text: {chunk}`, and the titled form is a diagnostic.
- **New from offrig's code: hybrid search.** offrig's search isn't dense-only: BM25 top 50 and cosine top 50 are fused by RRF, keeping the top 20. v2 decides on dense nDCG@10 and adds a guard: B mustn't lose more than 0.015 in hybrid.
- **New from offrig's code: int8 vectors.** offrig stores int8-quantized vectors, so both arms are scored after the same int8 quantization.
- **Power, stated plainly:** about 80% at a true +0.05–0.06, about a third at +0.03. That's accepted, because switching has a cost.

## What to check

1. Do your four changes land as you meant them, with nothing weakened?
2. **The hybrid guard:** is a dense decision with a hybrid non-inferiority guard right? Or should hybrid be the primary measure, since it's what users get? And does pooling dense and hybrid top 10s together bias the keys toward either arm?
3. **int8 scoring:** offrig quantizes each vector with its own scale (`cosine_q`). Does int8 at 256 dimensions lose more than at 768? Should Stage 2 read float, int8 or both?
4. **The power statement:** is accepting about a third power at +0.03 defensible, or should the margin or the size move?
5. **Verdict:** ready for the Director, or named changes.

## Design v2 (rnd `experiments/embeddinggemma-2/design.md`)

# EmbeddingGemma 2 against nomic-embed-text, for the studio's retrieval

**Status:** design v2, 2026-10-15, after Argon's round 1 (`argon-consult-round1.md`, disposition in `argon-consult-round1-disposition.md`). Template: [A/B experiments](https://mcp-tool-shop-org.github.io/rnd/handbook/ab-experiments/). Nothing is counted until the Director approves this design. Every run is on the CPU, with no card grant. The model and its env are installed (`entries/2026/embeddinggemma-2.md`).

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
- **Storage:** offrig stores int8-quantized vectors and scores `cosine_q`. Both arms are scored after the same int8 quantization, as deployed. Float scoring is a diagnostic.
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
  2. Run A and B to get each query's top 10 chunk ids. Dense and hybrid are pooled together.
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
    - mean hybrid nDCG@10 for B is not below A's by more than 0.015.
    
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
