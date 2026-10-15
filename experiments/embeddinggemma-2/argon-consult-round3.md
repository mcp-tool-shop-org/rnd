# Argon consult, round 3: the EmbeddingGemma 2 harness, before the counted run

**For Argon, from R&D. 2026-10-15.** The Director approved design v3. Section 6 requires an outside review of the harness, with its code inline, before any counted run. This is that review. R&D built the harness. Everything below was run without counting anything. You have no repository access: the design (with amendment 1), the validation results and every harness file are inline. Your findings are advice. R&D decides and records why.

## What's been done

- **The corpus is frozen with offrig's own chunker, rebuilt once before any counted run so chunk headers carry project-relative paths, as offrig writes them (amendment 2).**
  - Each source was archived with `git archive` at a pinned commit: rnd, readouts-internal's `*-knowledge` pages, role-set `src/` and offrig `crates/*/src`, with this experiment's folder excluded.
  - offrig 1.1.1's `index` was then run with an embed URL that doesn't answer. offrig stores every chunk and its FTS5 row, then refuses at the embed step, so no model ran.
  - That gave 11,525 chunks (10,072 prose, 1,453 code). The longest is 2,191 characters.
  - The chunk text stays private, because readouts-internal is private. Only ids, hashes and counts are committed.
- **The queries are frozen:** 100, of which 19 come from session logs and 81 were written by a Sonnet agent with the corpus closed (amendment 1).
- **Arm A's server is genuinely CPU-only.** offrig's documented start line put it on the 5090 through Vulkan on Ollama 0.40.4. That was caught in the server log before any load, and offrig #64 fixes it.
- **The validation results** follow below.

## What to check

1. **Fidelity to offrig.** `common.py` copies offrig 1.1.1's `fts_query`, `quantize`, `cosine_q` and `rrf`, with k 60, depth 50 and keep 20. Its Rust sources are quoted in the docstrings. Does anything differ from offrig in a way that changes a ranking? Look in particular at Unicode handling in `fts_query`, tie order in `rrf`, and that `quantized()` dequantizes before the cosine, as offrig does.
2. **The arms.** Does `embed.py` give each arm exactly what design v3 says? That means the prefixes, batch 32, the 270M load guard, `num_gpu: 0`, the digest pin, the VRAM stop, the code-prefix diagnostic, and B256 cut in float, re-normalized and then quantized.
3. **Pooling and scoring.** `pool.py` pools the top 10 of every run, both readings and the diagnostics, then dedupes and shuffles with a seed. In `score.py`, check the nDCG gain `2^g − 1`, the treatment of unjudged chunks as 0, the bootstrap, both stages, the hybrid guard, and amendment 1's drop rule. Does any of it diverge from section 5?
4. **The validation results.** Is anything in them a reason to stop?
5. **Grading** now follows your rubric, adopted as the handbook template (`relevance-grading.md`, summarised in amendment 2). Is the harness ready to feed it? You review the intent lines in a separate private packet.
6. **Verdict:** ready to run, or named changes.

## The validation run (section 6.2), as recorded

- **Tokens:** every chunk, prefix included, through both tokenizers. The longest is 1,231 WordPiece tokens for nomic and 1,528 for EmbeddingGemma 2. The 99th percentile is 835 and 834. No chunk is over 2,048.
- **Dtype gate:** 50 chunks in float32 and in bfloat16 on the 285K's CPU. bf16 took 17.0 s and fp32 took 20.9 s, but the minimum cosine was 0.9967, below the 0.999 gate. So arm B is float32, as the gate requires.
- **Throughput behind HTTP,** 1,024 sampled chunks at batch 32:
  - nomic through the CPU-only Ollama: 5.10 chunks/s;
  - EmbeddingGemma 2 behind a loopback `/api/embed` wrapper: 2.02 chunks/s;
  - B over A is 0.395, above the design's one-third cost line.
- **Dry run on the first 512 chunks and all 100 queries:**
  - **Records:** each arm's manipulation record reads correctly. The prefixes are `search_document: ` and `title: none | text: `, the dimension is 768 with norms within 1e-6 of 1, and B256 is 256 dimensions with norms within 1e-6.
  - **Speed:** in-process, A does 4.93 chunks/s and B does 2.80.
  - **A dry-run artifact:** the hybrid reading takes BM25 from the full frozen index, so it reaches chunks outside the 512 slice. The counted run embeds every chunk, so it doesn't arise there.
  - **The pool, from the 8 decision runs** (A, B and B256 in dense-int8 and hybrid, plus the code-prefix dense diagnostic for B and B256): 26.8 chunks per query on average, 36 at most. That's larger than the 15–20 estimated earlier. It means about 2,500 grades for the full pool, and about 270 chunks for a 10-query audit.
  - **Excluded from the pool:** the float readings and the code-prefix hybrids, which are diagnostics only. A chunk that only they surface counts 0, and that is stated beside those diagnostics.

## Design v3 with amendments 1 and 2 (rnd `experiments/embeddinggemma-2/design.md`)

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

## `harness/common.py`

```python
"""Shared pieces of the EmbeddingGemma 2 benchmark harness (design v3, experiments/embeddinggemma-2/design.md).

Everything that reproduces offrig's behaviour is copied from offrig 1.1.1's crates/offrig-core and named after its
source: fts_query (store.rs), quantize and cosine_q (index.rs), rrf with RRF_K, RANKER_DEPTH and FUSED_KEEP (index.rs).
Private text (chunks, queries' pooled passages, grades) lives under BENCH, outside the public repo. Only ids, hashes,
counts and scores are committed.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EXPERIMENT = HERE.parent
BENCH = Path(os.environ.get("EG2_BENCH", r"E:\AI\eg2-bench"))
PROJECT = BENCH / "index"          # the offrig project: corpus/ inside it, .offrig/offrig.db holds the frozen chunks
DB = PROJECT / ".offrig" / "offrig.db"
CHUNKS = BENCH / "chunks.jsonl"
QUERIES = BENCH / "queries.jsonl"
VECTORS = BENCH / "vectors"
RUNS = BENCH / "runs"
RESULTS = EXPERIMENT / "results"   # committed: ids, hashes, counts and scores only

# offrig 1.1.1, crates/offrig-core/src/index.rs
RANKER_DEPTH = 50
FUSED_KEEP = 20
RRF_K = 60.0
BATCH = 32

# The two arms' document and query strings (design v3, section 2).
A_DOC, A_QUERY = "search_document: ", "search_query: "
B_DOC = "title: none | text: "
B_QUERY = "task: search result | query: "
B_QUERY_CODE = "task: code retrieval | query: "
EG2_REVISION = "914f7f89142e33e77833254d9c9b90c3cef7303b"
NOMIC = "nomic-embed-text"
NOMIC_DIGEST = "0a109f422b47"
EMBED_URL = "http://127.0.0.1:11490"   # offrig's CPU-only Ollama


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def fts_query(text: str) -> str | None:
    """offrig store.rs fts_query: split on anything but alphanumerics and _ - . :, quote each word, join with OR."""

    words, cur = [], []
    for ch in text:
        if ch.isalnum() or ch in "_-.:":
            cur.append(ch)
        elif cur:
            words.append("".join(cur))
            cur = []
    if cur:
        words.append("".join(cur))
    words = ['"' + w.replace('"', "") + '"' for w in words if w]
    return " OR ".join(words) if words else None


def quantize(v: np.ndarray) -> tuple[np.ndarray, float]:
    """offrig index.rs quantize: per-vector absmax over 127, round, clamp to [-127, 127]."""

    m = float(np.max(np.abs(v)))
    if m == 0.0:
        return np.zeros(v.shape, dtype=np.int8), 0.0
    scale = np.float32(m / 127.0)
    q = np.clip(np.round(v.astype(np.float32) / scale), -127, 127).astype(np.int8)
    return q, float(scale)


def l2n(m: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(m, axis=-1, keepdims=True)
    return m / np.where(n == 0, 1, n)


def cosine_matrix(queries: np.ndarray, docs: np.ndarray) -> np.ndarray:
    """offrig cosine: dot over the product of norms (offrig never assumes unit length)."""

    return l2n(queries.astype(np.float32)) @ l2n(docs.astype(np.float32)).T


def rrf(lists: list[list[int]], k: float = RRF_K, keep: int = FUSED_KEEP) -> list[int]:
    """offrig index.rs rrf: 1/(k + rank) summed, highest first, ties keep first-seen order."""

    scores: dict[int, float] = {}
    order: list[int] = []
    for lst in lists:
        for rank, cid in enumerate(lst, start=1):
            if cid not in scores:
                scores[cid] = 0.0
                order.append(cid)
            scores[cid] += 1.0 / (k + rank)
    first = {cid: i for i, cid in enumerate(order)}
    return sorted(order, key=lambda c: (-scores[c], first[c]))[:keep]


def ndcg_at(ranked: list[int], grades: dict[int, int], k: int = 10) -> float:
    """nDCG@k with gain 2^g - 1 over the pooled grades; an unjudged chunk counts 0."""

    dcg = sum((2 ** grades.get(c, 0) - 1) / math.log2(i + 2) for i, c in enumerate(ranked[:k]))
    ideal = sorted(grades.values(), reverse=True)[:k]
    idcg = sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0
```

## `harness/build_corpus.py`

```python
"""Freeze the corpus with offrig's own chunker (design v3, sections 3 and 4).

1. `git archive` each source at a pinned commit into BENCH/corpus/<repo>/ (this experiment's folder excluded).
2. `offrig index` the corpus into BENCH/index with an embedder that doesn't answer: offrig stores every chunk and its
   FTS row first, then refuses at the embed step, so no model is touched.
3. Export the chunks to BENCH/chunks.jsonl (private: it carries text) and write results/corpus-manifest.json
   (public: commits, counts, hashes; no text).

Run: E:/AI/envs/embedgemma/Scripts/python.exe -I build_corpus.py
"""

from __future__ import annotations

import io
import json
import os
import shutil
import sqlite3
import subprocess
import tarfile
from collections import Counter

from common import BENCH, CHUNKS, DB, PROJECT, RESULTS, sha256_file, write_jsonl

# The corpus lives inside the offrig project and is indexed by a relative path, so chunk headers read
# `[corpus/<repo>/<path> · kind · title]` the way offrig writes them in production (project-relative).
CORPUS = PROJECT / "corpus"

SOURCES = [
    # (name, repo dir, ref, include prefixes, exclude prefixes, suffixes)
    ("rnd", r"E:\AI\Research and Development", "origin/main",
     ["entries/", "instruments/", "experiments/"], ["experiments/embeddinggemma-2/"], None),
    ("readouts", r"E:\AI\readouts", "origin/main", None, [], (".md",)),
    ("role-set", r"E:\AI\role-set", "origin/main", ["src/"], [], (".py",)),
    ("offrig", r"E:\AI\offrig", "origin/main", ["crates/"], [], (".rs",)),
]
OFFRIG = shutil.which("offrig")
DEAD_EMBED = "http://127.0.0.1:11499"


def git(repo: str, *args: str) -> str:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, check=True, text=True).stdout.strip()


def keep(name: str, path: str, include, exclude, suffixes) -> bool:
    if name == "readouts":
        top = path.split("/", 1)[0]
        return top.endswith("-knowledge") and path.endswith(".md")
    if name == "rnd" and path.startswith("experiments/") and not path.endswith(".md"):
        return False
    if name == "offrig" and "/src/" not in path:
        return False
    if include and not any(path.startswith(p) for p in include):
        return False
    if any(path.startswith(p) for p in exclude):
        return False
    return suffixes is None or path.endswith(suffixes)


def archive(name: str, repo: str, ref: str, include, exclude, suffixes) -> dict:
    commit = git(repo, "rev-parse", ref)
    blob = subprocess.run(["git", "-C", repo, "archive", "--format=tar", commit], capture_output=True, check=True).stdout
    dest = CORPUS / name
    files = 0
    with tarfile.open(fileobj=io.BytesIO(blob)) as tar:
        for member in tar.getmembers():
            if member.isfile() and keep(name, member.name, include, exclude, suffixes):
                target = dest / member.name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(tar.extractfile(member).read())
                files += 1
    return {"name": name, "ref": ref, "commit": commit, "files": files}


def main() -> None:
    if PROJECT.exists():
        raise SystemExit(f"REFUSED: {PROJECT} exists; the corpus is frozen once. Move it aside to rebuild.")
    PROJECT.mkdir(parents=True)
    pins = [archive(*s) for s in SOURCES]
    subprocess.run(["git", "init", "-q", str(PROJECT)], check=True)
    env = dict(os.environ, OFFRIG_EMBED_URL=DEAD_EMBED)
    version = subprocess.run([OFFRIG, "--version"], capture_output=True, text=True, check=True).stdout.strip()
    run = subprocess.run([OFFRIG, "index", "corpus", "--project", str(PROJECT)], capture_output=True, text=True, env=env, cwd=PROJECT)
    if "no embedding server answers" not in (run.stdout + run.stderr):
        raise SystemExit(f"REFUSED: offrig index did not stop at the embed step as expected:\n{run.stdout}\n{run.stderr}")
    con = sqlite3.connect(DB)
    if con.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0] != 0:
        raise SystemExit("REFUSED: the index holds vectors; it must hold none")
    rows = [
        {"id": i, "source": s, "kind": k, "title": t, "ordinal": o, "body": b}
        for i, s, k, t, o, b in con.execute("SELECT id, source, kind, title, ordinal, body FROM chunks ORDER BY id")
    ]
    write_jsonl(CHUNKS, rows)
    root = lambda src: src.replace("\\", "/").split("corpus/", 1)[-1].split("/", 1)[0]
    manifest = {
        "offrig": version,
        "offrig_exe_sha256": sha256_file(__import__("pathlib").Path(OFFRIG)),
        "pins": pins,
        "chunks": len(rows),
        "by_kind": dict(Counter(r["kind"] for r in rows)),
        "by_source": dict(Counter(root(r["source"]) for r in rows)),
        "max_body_chars": max(len(r["body"]) for r in rows),
        "chunks_sha256": sha256_file(CHUNKS),
        "db_sha256": sha256_file(DB),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "corpus-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "pins"}, indent=1))
    for p in pins:
        print(p)


if __name__ == "__main__":
    main()
```

## `harness/collect_queries.py`

```python
"""Mine candidate queries from Claude Code session logs (design v3, section 4).

Reads every session transcript under ~/.claude/projects and keeps the search strings agents actually issued:
`rnd search <words>` and `rnd readouts <words>` in Bash calls, and the `query` of offrig_memory_search calls.
Only tool-call arguments are read; no user message is copied. For each session the first query of a run of
searches is kept and later reformulations within five minutes are marked, so a pick can take the first query
per information need. Output: BENCH/query-candidates.jsonl (private; R&D picks from it by hand).

Run: E:/AI/envs/embedgemma/Scripts/python.exe collect_queries.py
"""

from __future__ import annotations

import json
import re
import shlex
from datetime import datetime
from pathlib import Path

from common import BENCH, write_jsonl

LOGS = Path.home() / ".claude" / "projects"
RND = re.compile(r"(?:python(?:\.exe)?\s+-m\s+rnd|rnd)\s+(search|readouts)\s+(.+?)(?:\s*(?:\||&&|;|2>|>|$))")


def when(stamp: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00")) if stamp else None
    except ValueError:
        return None


def from_bash(cmd: str) -> list[tuple[str, str]]:
    out = []
    for m in RND.finditer(cmd):
        try:
            words = [w for w in shlex.split(m.group(2)) if not w.startswith("-")]
        except ValueError:
            continue
        if words:
            out.append((f"rnd {m.group(1)}", " ".join(words)))
    return out


def main() -> None:
    rows = []
    for path in sorted(LOGS.rglob("*.jsonl")):
        session = path.stem
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = ev.get("message") or {}
            if msg.get("role") != "assistant" or not isinstance(msg.get("content"), list):
                continue
            for part in msg["content"]:
                if part.get("type") != "tool_use":
                    continue
                name, args = part.get("name", ""), part.get("input") or {}
                hits = []
                if name in ("Bash", "PowerShell") and isinstance(args.get("command"), str):
                    hits = from_bash(args["command"])
                elif name.endswith("offrig_memory_search") and isinstance(args.get("query"), str):
                    hits = [("offrig_memory_search", args["query"].strip())]
                for tool, q in hits:
                    rows.append({"session": session, "project": path.parent.name, "at": ev.get("timestamp"),
                                 "tool": tool, "query": q})
    rows.sort(key=lambda r: (r["session"], r["at"] or ""))
    prev: dict[str, dict] = {}
    for r in rows:
        last = prev.get(r["session"])
        t, lt = when(r["at"]), when(last["at"]) if last else None
        r["reformulation"] = bool(last and t and lt and (t - lt).total_seconds() < 300)
        prev[r["session"]] = r
    seen, firsts = set(), []
    for r in rows:
        key = r["query"].lower()
        if not r["reformulation"] and key not in seen:
            seen.add(key)
            firsts.append(r)
    write_jsonl(BENCH / "query-candidates.jsonl", rows)
    write_jsonl(BENCH / "query-firsts.jsonl", firsts)
    print(f"{len(rows)} search calls; {len(firsts)} distinct first queries")


if __name__ == "__main__":
    main()
```

## `harness/embed.py`

```python
"""Embed the frozen corpus and queries for arms A and B (design v3, sections 2, 3 and 6).

Arm A: nomic-embed-text on offrig's CPU-only Ollama (EMBED_URL, CUDA and Vulkan hidden), batch 32, offrig's prefixes.
Arm B: EmbeddingGemma 2 text-only on the CPU through sentence-transformers, batch 32, the card's prefixes, dtype from
the validation gate. B256 is derived at ranking time (rank.py), never stored separately.

Writes BENCH/vectors/<arm>-docs.npy and <arm>-queries.npy (float32), and results/embed-<arm>.json (public: the
manipulation records without chunk text, pins, timings).

Run: E:/AI/envs/embedgemma/Scripts/python.exe embed.py --arm A|B [--dtype float32|bfloat16] [--limit N]
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.request

import numpy as np

from common import (A_DOC, A_QUERY, B_DOC, B_QUERY, B_QUERY_CODE, BATCH, CHUNKS, EG2_REVISION, EMBED_URL, NOMIC,
                    NOMIC_DIGEST, QUERIES, RESULTS, VECTORS, read_jsonl)


def post(path: str, body: dict) -> dict:
    req = urllib.request.Request(EMBED_URL + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


def get(path: str) -> dict:
    with urllib.request.urlopen(EMBED_URL + path, timeout=30) as r:
        return json.loads(r.read())


def ollama_cpu_only() -> None:
    loaded = get("/api/ps").get("models", [])
    for m in loaded:
        if m.get("size_vram", 0) > 0:
            raise SystemExit(f"STOP: {m['name']} holds {m['size_vram']} bytes of VRAM on the embed server")


def nomic_pinned() -> None:
    tags = {m["name"]: m["digest"] for m in get("/api/tags")["models"]}
    if not tags.get(NOMIC + ":latest", "").startswith(NOMIC_DIGEST):
        raise SystemExit(f"STOP: {NOMIC} digest is {tags.get(NOMIC + ':latest')}, pinned {NOMIC_DIGEST}")


def embed_a(texts: list[str]) -> np.ndarray:
    nomic_pinned()
    out = []
    for i in range(0, len(texts), BATCH):
        r = post("/api/embed", {"model": NOMIC, "input": texts[i:i + BATCH], "truncate": False,
                                "options": {"num_gpu": 0}, "keep_alive": "10m"})
        out.extend(r["embeddings"])
        if i == 0:
            ollama_cpu_only()
    return np.asarray(out, dtype=np.float32)


def load_b(dtype: str):
    import torch
    from sentence_transformers import SentenceTransformer

    if torch.cuda.is_available():
        raise SystemExit("STOP: this torch build sees CUDA; arm B runs on the CPU only")
    model = SentenceTransformer("google/embeddinggemma-2", revision=EG2_REVISION, device="cpu",
                                model_kwargs={"torch_dtype": getattr(torch, dtype)},
                                config_kwargs={"vision_config": None, "audio_config": None})
    params = sum(p.numel() for p in model.parameters())
    if params > 300e6:
        raise SystemExit(f"STOP: {params / 1e6:.0f}M parameters loaded; the text-only model is 271M")
    return model, params


def embed_b(model, texts: list[str]) -> np.ndarray:
    v = model.encode(texts, batch_size=BATCH, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
    return np.asarray(v, dtype=np.float32)


def check(name: str, m: np.ndarray, dim: int) -> dict:
    if np.isnan(m).any():
        raise SystemExit(f"STOP: NaN in {name}")
    norms = np.linalg.norm(m, axis=1)
    return {"rows": int(m.shape[0]), "dim": int(m.shape[1]), "dim_ok": m.shape[1] == dim,
            "norm_min": float(norms.min()), "norm_max": float(norms.max())}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["A", "B"], required=True)
    ap.add_argument("--dtype", default="float32", choices=["float32", "bfloat16"])
    ap.add_argument("--limit", type=int, default=0, help="first N chunks only (validation)")
    args = ap.parse_args()
    chunks = read_jsonl(CHUNKS)
    queries = read_jsonl(QUERIES)
    if args.limit:
        chunks = chunks[: args.limit]
    tag = args.arm + (f"-limit{args.limit}" if args.limit else "")
    if args.arm == "A":
        docs = [A_DOC + c["body"] for c in chunks]
        qs = [A_QUERY + q["query"] for q in queries]
        qcode = None
        t0 = time.perf_counter(); dv = embed_a(docs); t_docs = time.perf_counter() - t0
        qv = embed_a(qs)
        params, dtype = 137_000_000, "F16 GGUF (Ollama)"
    else:
        model, params = load_b(args.dtype)
        dtype = args.dtype
        docs = [B_DOC + c["body"] for c in chunks]
        qs = [B_QUERY + q["query"] for q in queries]
        t0 = time.perf_counter(); dv = embed_b(model, docs); t_docs = time.perf_counter() - t0
        qv = embed_b(model, qs)
        code = [q for q in queries if q["group"] == "code"]
        qcode = embed_b(model, [B_QUERY_CODE + q["query"] for q in code]) if code else None
    VECTORS.mkdir(parents=True, exist_ok=True)
    np.save(VECTORS / f"{tag}-docs.npy", dv)
    np.save(VECTORS / f"{tag}-queries.npy", qv)
    if qcode is not None:
        np.save(VECTORS / f"{tag}-queries-codeprefix.npy", qcode)
    record = {
        "arm": args.arm, "dtype": dtype, "params": int(params), "batch": BATCH,
        "model": NOMIC + "@" + NOMIC_DIGEST if args.arm == "A" else "google/embeddinggemma-2@" + EG2_REVISION,
        "manipulation": {
            "first_doc_prefix": docs[0][: len(A_DOC if args.arm == "A" else B_DOC)],
            "first_query_prefix": qs[0][: len(A_QUERY if args.arm == "A" else B_QUERY)],
            "first_query_sha256": __import__("hashlib").sha256(qs[0].encode()).hexdigest(),  # query text stays private
            "docs": check("docs", dv, 768), "queries": check("queries", qv, 768),
        },
        "chunks": len(chunks), "seconds_docs_in_process": round(t_docs, 2),
        "chunks_per_second": round(len(chunks) / t_docs, 2),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"embed-{tag}.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=1))


if __name__ == "__main__":
    main()
```

## `harness/rank.py`

```python
"""Rank the corpus for every query, the way offrig would (design v3, sections 3 and 5).

For each arm (A, B, B256, and the code-prefix diagnostics on the code group) and each reading:
- dense-int8: documents quantized per vector with offrig's quantizer; the query stays float; cosine; top 20.
  This is what the decision rule reads.
- dense-float: the same, without quantization (diagnostic).
- hybrid: offrig's FTS5 BM25 top 50 from the frozen index plus dense-int8 top 50, fused by RRF (k 60), top 20 kept.
B256 is cut from B's float vectors to 256 dimensions and re-normalized in float, then quantized with its own scale.

Writes BENCH/runs/<arm>-<reading>.json as {query id: [chunk ids, best first]}.

Run: E:/AI/envs/embedgemma/Scripts/python.exe rank.py [--tag-suffix -limit512]
"""

from __future__ import annotations

import argparse
import json
import sqlite3

import numpy as np

from common import CHUNKS, DB, FUSED_KEEP, QUERIES, RANKER_DEPTH, RESULTS, RUNS, VECTORS, cosine_matrix, fts_query, l2n, quantize, read_jsonl, rrf


def quantized(docs: np.ndarray) -> np.ndarray:
    """Dequantized int8 documents, exactly as offrig scores them (dequantize then cosine)."""

    out = np.empty_like(docs)
    for i, v in enumerate(docs):
        q, scale = quantize(v)
        out[i] = q.astype(np.float32) * scale
    return out


def top(scores: np.ndarray, ids: np.ndarray, k: int) -> list[list[int]]:
    idx = np.argsort(-scores, axis=1, kind="stable")[:, :k]
    return [[int(ids[j]) for j in row] for row in idx]


def bm25(con: sqlite3.Connection, text: str) -> list[int]:
    q = fts_query(text)
    if q is None:
        return []
    rows = con.execute(
        "SELECT c.id FROM chunks_fts f JOIN chunks c ON c.id = f.rowid WHERE chunks_fts MATCH ?1 "
        "ORDER BY bm25(chunks_fts) LIMIT ?2", (q, RANKER_DEPTH)).fetchall()
    return [r[0] for r in rows]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag-suffix", default="")
    args = ap.parse_args()
    sfx = args.tag_suffix
    chunks = read_jsonl(CHUNKS)
    queries = read_jsonl(QUERIES)
    ids = np.array([c["id"] for c in chunks], dtype=np.int64)
    a_docs = np.load(VECTORS / f"A{sfx}-docs.npy")
    ids = ids[: a_docs.shape[0]]
    b_docs = np.load(VECTORS / f"B{sfx}-docs.npy")
    a_q = np.load(VECTORS / f"A{sfx}-queries.npy")
    b_q = np.load(VECTORS / f"B{sfx}-queries.npy")
    code_idx = [i for i, q in enumerate(queries) if q["group"] == "code"]
    b_qc_path = VECTORS / f"B{sfx}-queries-codeprefix.npy"
    b_qc = np.load(b_qc_path) if b_qc_path.exists() else None

    arms = {
        "A": (a_docs, a_q, list(range(len(queries)))),
        "B": (b_docs, b_q, list(range(len(queries)))),
        "B256": (l2n(b_docs[:, :256]), l2n(b_q[:, :256]), list(range(len(queries)))),
    }
    if b_qc is not None:
        arms["Bcode"] = (b_docs, b_qc, code_idx)
        arms["B256code"] = (l2n(b_docs[:, :256]), l2n(b_qc[:, :256]), code_idx)

    b256_docs, b256_q = arms["B256"][0], arms["B256"][1]
    n_d, n_q = np.linalg.norm(b256_docs, axis=1), np.linalg.norm(b256_q, axis=1)
    record = {"dim_docs": int(b256_docs.shape[1]), "dim_queries": int(b256_q.shape[1]),
              "norm_min": float(min(n_d.min(), n_q.min())), "norm_max": float(max(n_d.max(), n_q.max()))}
    if record["dim_docs"] != 256 or abs(record["norm_min"] - 1) > 1e-3 or abs(record["norm_max"] - 1) > 1e-3:
        raise SystemExit(f"STOP: B256 manipulation check failed: {record}")
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"embed-B256{sfx}.json").write_text(json.dumps({"arm": "B256", "manipulation": record}, indent=2) + "\n", encoding="utf-8")

    con = sqlite3.connect(DB)
    lex = {q["id"]: bm25(con, q["query"]) for q in queries}
    RUNS.mkdir(parents=True, exist_ok=True)
    for name, (docs, qv, which) in arms.items():
        qids = [queries[i]["id"] for i in which]
        dense_f = top(cosine_matrix(qv, docs), ids, max(FUSED_KEEP, RANKER_DEPTH))
        dense_q_all = top(cosine_matrix(qv, quantized(docs)), ids, RANKER_DEPTH)
        runs = {
            "dense-int8": {q: r[:FUSED_KEEP] for q, r in zip(qids, dense_q_all)},
            "dense-float": {q: r[:FUSED_KEEP] for q, r in zip(qids, dense_f)},
            "hybrid": {q: rrf([lex[q], r]) for q, r in zip(qids, dense_q_all)},
        }
        for reading, run in runs.items():
            (RUNS / f"{name}{sfx}-{reading}.json").write_text(json.dumps(run) + "\n", encoding="utf-8")
        print(name, {k: len(v) for k, v in runs.items()})


if __name__ == "__main__":
    main()
```

## `harness/pool.py`

```python
"""Build the blind grading pool (design v3, section 4, keys steps 2 and 3).

Union of each query's top 10 across every run in BENCH/runs (A, B, B256, both readings and the code-prefix
diagnostics), deduplicated, with model identities and ranks dropped and the order shuffled by a fixed seed.

Writes BENCH/pool.jsonl (private: chunk text for the graders) and results/pool-manifest.json (public: sizes).
Grades go in BENCH/keys.jsonl as {"qid", "chunk_id", "grade": 0|1|2, "grader"}.

Run: E:/AI/envs/embedgemma/Scripts/python.exe pool.py [--tag-suffix S]
"""

from __future__ import annotations

import argparse
import json
import random
from statistics import mean

from common import BENCH, CHUNKS, QUERIES, RESULTS, RUNS, read_jsonl, write_jsonl

SEED = 20261015
DEPTH = 10


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag-suffix", default="")
    args = ap.parse_args()
    body = {c["id"]: c for c in read_jsonl(CHUNKS)}
    queries = read_jsonl(QUERIES)
    # The decision readings of A, B and B256, plus the code-prefix diagnostic's dense reading (design v3, keys
    # step 2). The float readings and the code-prefix hybrids are diagnostics read against these grades; a chunk
    # only they surface counts 0, which is stated beside those diagnostics.
    names = [f"{arm}{args.tag_suffix}-{reading}" for arm in ("A", "B", "B256") for reading in ("dense-int8", "hybrid")]
    names += [f"Bcode{args.tag_suffix}-dense-int8", f"B256code{args.tag_suffix}-dense-int8"]
    runs = [json.loads((RUNS / f"{n}.json").read_text(encoding="utf-8")) for n in names]
    rng = random.Random(SEED)
    rows, sizes = [], []
    for q in queries:
        pool: list[int] = []
        for run in runs:
            for cid in run.get(q["id"], [])[:DEPTH]:
                if cid not in pool:
                    pool.append(cid)
        rng.shuffle(pool)
        sizes.append(len(pool))
        for n, cid in enumerate(pool, start=1):
            c = body[cid]
            rows.append({"qid": q["id"], "group": q["group"], "query": q["query"], "n": n, "chunk_id": cid,
                         "source": c["source"], "text": c["body"]})
    write_jsonl(BENCH / f"pool{args.tag_suffix}.jsonl", rows)
    manifest = {"seed": SEED, "depth": DEPTH, "runs": len(runs), "queries": len(queries), "pooled": len(rows),
                "per_query_mean": round(mean(sizes), 2), "per_query_max": max(sizes)}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"pool-manifest{args.tag_suffix}.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(manifest)


if __name__ == "__main__":
    main()
```

## `harness/score.py`

```python
"""Score the frozen keys and apply the pre-registered rule (design v3, section 5).

Per query: nDCG@10 (gain 2^g - 1), recall@5 (grade >= 1 counts relevant), MRR (first grade >= 1).
Comparisons are paired by query with 10,000 bootstrap resamples (seed fixed).

Stage 1 (B against A, dense-int8): mean delta >= +0.03, one-sided 95% lower bound > 0, neither group's mean
delta below -0.015, hybrid mean delta >= 0.00 with its one-sided 95% lower bound > -0.015.
Stage 2 (only if Stage 1 passes; B256 against B, dense-int8): two-sided 95% lower bound > -0.015 and mean
(B256 - A) >= +0.02. Otherwise B at 768.

Writes results/scores.json and results/per-query.jsonl (ids and numbers only).

Run: E:/AI/envs/embedgemma/Scripts/python.exe score.py
"""

from __future__ import annotations

import json
from collections import defaultdict

import numpy as np

from common import BENCH, QUERIES, RESULTS, RUNS, ndcg_at, read_jsonl, write_jsonl

SEED = 7
RESAMPLES = 10_000


def load_run(name: str) -> dict:
    return json.loads((RUNS / f"{name}.json").read_text(encoding="utf-8"))


def metrics(ranked: list[int], grades: dict[int, int]) -> dict:
    rel = {c for c, g in grades.items() if g >= 1}
    rr = next((1.0 / (i + 1) for i, c in enumerate(ranked) if c in rel), 0.0)
    return {"ndcg10": ndcg_at(ranked, grades, 10),
            "recall5": len(rel & set(ranked[:5])) / len(rel) if rel else 0.0, "mrr": rr}


def boot(delta: np.ndarray, rng: np.random.Generator) -> dict:
    n = len(delta)
    means = delta[rng.integers(0, n, size=(RESAMPLES, n))].mean(axis=1)
    return {"mean": float(delta.mean()), "lo_one_sided_95": float(np.quantile(means, 0.05)),
            "lo_95": float(np.quantile(means, 0.025)), "hi_95": float(np.quantile(means, 0.975)), "n": int(n)}


def main() -> None:
    queries = read_jsonl(QUERIES)
    group = {q["id"]: q["group"] for q in queries}
    grades: dict[str, dict[int, int]] = defaultdict(dict)
    for k in read_jsonl(BENCH / "keys.jsonl"):
        grades[k["qid"]][int(k["chunk_id"])] = int(k["grade"])
    missing = [q["id"] for q in queries if not grades.get(q["id"])]
    if missing:
        raise SystemExit(f"STOP: no grades for {missing[:5]}")
    # Amendment 1: a query whose pool holds nothing graded 1 or 2 carries no information about either arm.
    dropped = [q["id"] for q in queries if max(grades[q["id"]].values()) < 1]
    queries = [q for q in queries if q["id"] not in dropped]
    kept_groups = {g: sum(1 for q in queries if q["group"] == g) for g in ("prose", "code")}
    names = {p.stem for p in RUNS.glob("*.json") if "-limit" not in p.stem}
    per = defaultdict(dict)
    for name in sorted(names):
        run = load_run(name)
        for qid, ranked in run.items():
            if qid not in dropped:
                per[qid][name] = metrics(ranked, grades[qid])
    rows = [{"qid": q, "group": group[q], **{f"{n}.{m}": round(v, 5) for n, d in per[q].items() for m, v in d.items()}}
            for q in sorted(per)]
    write_jsonl(RESULTS / "per-query.jsonl", rows)

    rng = np.random.default_rng(SEED)
    qids = [q["id"] for q in queries]

    def delta(x: str, y: str, metric: str = "ndcg10", only: str | None = None) -> np.ndarray:
        return np.array([per[q][x][metric] - per[q][y][metric] for q in qids if (only is None or group[q] == only)])

    def mean_of(name: str, only: str | None = None) -> float:
        return float(np.mean([per[q][name]["ndcg10"] for q in qids if (only is None or group[q] == only)]))

    s1 = boot(delta("B-dense-int8", "A-dense-int8"), rng)
    s1_groups = {g: float(delta("B-dense-int8", "A-dense-int8", only=g).mean()) for g in ("prose", "code")}
    s1_hybrid = boot(delta("B-hybrid", "A-hybrid"), rng)
    stage1 = (s1["mean"] >= 0.03 and s1["lo_one_sided_95"] > 0 and min(s1_groups.values()) >= -0.015
              and s1_hybrid["mean"] >= 0.0 and s1_hybrid["lo_one_sided_95"] > -0.015)
    s2 = boot(delta("B256-dense-int8", "B-dense-int8"), rng)
    s2_vs_a = float(delta("B256-dense-int8", "A-dense-int8").mean())
    stage2 = stage1 and s2["lo_95"] > -0.015 and s2_vs_a >= 0.02
    decision = "adopt B256" if stage2 else ("adopt B at 768" if stage1 else "keep nomic-embed-text")
    out = {
        "decision": decision,
        "queries": {"kept": len(queries), "by_group": kept_groups, "dropped": dropped,
                    "below_40_in_a_group": any(n < 40 for n in kept_groups.values())},
        "stage1": {"dense": s1, "groups": s1_groups, "hybrid": s1_hybrid, "passed": stage1},
        "stage2": {"b256_vs_b": s2, "b256_minus_a_mean": s2_vs_a, "passed": stage2},
        "means_ndcg10": {n: {"all": mean_of(n), "prose": mean_of(n, "prose"), "code": mean_of(n, "code")}
                         for n in sorted(names) if not n.endswith("code-dense-int8") and "code-" not in n},
        "diagnostics": {
            "code_prefix_B_minus_B_on_code": float(np.mean([per[q]["Bcode-dense-int8"]["ndcg10"] - per[q]["B-dense-int8"]["ndcg10"]
                                                            for q in qids if group[q] == "code"])) if "Bcode-dense-int8" in names else None,
            "int8_minus_float_B256": float(delta("B256-dense-int8", "B256-dense-float").mean()),
            "int8_minus_float_B": float(delta("B-dense-int8", "B-dense-float").mean()),
            "recall5_B_minus_A": float(delta("B-dense-int8", "A-dense-int8", "recall5").mean()),
            "mrr_B_minus_A": float(delta("B-dense-int8", "A-dense-int8", "mrr").mean()),
        },
        "bootstrap": {"seed": SEED, "resamples": RESAMPLES},
    }
    (RESULTS / "scores.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
```

## `harness/validate.py`

```python
"""The free validation run (design v3, section 6.2). Nothing it produces is counted.

1. Tokenizer pre-check: every frozen chunk, with its arm's prefix, tokenized with nomic's WordPiece tokenizer and
   EmbeddingGemma 2's tokenizer. Stops if any exceeds 2,048 tokens.
2. Dtype gate: 50 chunks through arm B in float32 and in bfloat16. The pairwise cosine must be >= 0.999. The faster
   dtype is recorded as arm B's.
3. Throughput behind HTTP: 1,024 chunks through arm A's Ollama (as deployed), and through arm B behind a minimal
   loopback server in npu-serve's shape (/api/embed), both at batch 32.

Writes results/validation.json. The 5-query end-to-end check is embed.py and rank.py with --limit 512 on the
first five queries, run by hand after this.

Run: E:/AI/envs/embedgemma/Scripts/python.exe validate.py
"""

from __future__ import annotations

import json
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np

from common import A_DOC, B_DOC, BATCH, CHUNKS, RESULTS, read_jsonl
from embed import embed_a, embed_b, load_b

LIMIT_TOKENS = 2048
SAMPLE = 1024


def tokenizer_check(chunks: list[dict]) -> dict:
    from huggingface_hub import hf_hub_download
    from tokenizers import Tokenizer
    from transformers import AutoTokenizer

    nomic = Tokenizer.from_file(hf_hub_download("nomic-ai/nomic-embed-text-v1.5", "tokenizer.json"))
    eg2 = AutoTokenizer.from_pretrained("google/embeddinggemma-2")
    a = [len(nomic.encode(A_DOC + c["body"]).ids) for c in chunks]
    b = [len(eg2(B_DOC + c["body"])["input_ids"]) for c in chunks]
    out = {"nomic_max": max(a), "eg2_max": max(b), "nomic_p99": int(np.percentile(a, 99)), "eg2_p99": int(np.percentile(b, 99)),
           "over_limit": sum(1 for x, y in zip(a, b) if x > LIMIT_TOKENS or y > LIMIT_TOKENS)}
    if out["over_limit"]:
        raise SystemExit(f"STOP: {out['over_limit']} chunks exceed {LIMIT_TOKENS} tokens: {out}")
    return out


def dtype_gate(chunks: list[dict]) -> dict:
    texts = [B_DOC + c["body"] for c in chunks[:50]]
    res = {}
    vecs = {}
    for dtype in ("float32", "bfloat16"):
        model, _ = load_b(dtype)
        embed_b(model, texts[:4])  # warm
        t0 = time.perf_counter()
        vecs[dtype] = embed_b(model, texts)
        res[f"{dtype}_seconds"] = round(time.perf_counter() - t0, 3)
        del model
    cos = np.sum(vecs["float32"] * vecs["bfloat16"], axis=1)
    res["cosine_min"] = float(cos.min())
    res["cosine_mean"] = float(cos.mean())
    res["parity_ok"] = bool(cos.min() >= 0.999)
    res["chosen"] = ("bfloat16" if res["parity_ok"] and res["bfloat16_seconds"] < res["float32_seconds"] else "float32")
    return res


class _Handler(BaseHTTPRequestHandler):
    model = None

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        vecs = embed_b(self.model, body["input"]).tolist()
        data = json.dumps({"model": "embeddinggemma-2", "embeddings": vecs}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


def wrapped_b(chunks: list[dict], dtype: str) -> float:
    _Handler.model, _ = load_b(dtype)
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}/api/embed"
    texts = [B_DOC + c["body"] for c in chunks]
    t0 = time.perf_counter()
    for i in range(0, len(texts), BATCH):
        req = urllib.request.Request(url, data=json.dumps({"input": texts[i:i + BATCH]}).encode(),
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=600).read()
    secs = time.perf_counter() - t0
    server.shutdown()
    return secs


def main() -> None:
    chunks = read_jsonl(CHUNKS)
    out = {"tokens": tokenizer_check(chunks)}
    print("tokens", out["tokens"])
    out["dtype_gate"] = dtype_gate(chunks)
    print("dtype", out["dtype_gate"])
    rng = np.random.default_rng(3)
    sample = [chunks[i] for i in sorted(rng.choice(len(chunks), SAMPLE, replace=False))]
    embed_a([A_DOC + c["body"] for c in sample[:BATCH]])  # load and warm
    t0 = time.perf_counter()
    embed_a([A_DOC + c["body"] for c in sample])
    a_secs = time.perf_counter() - t0
    b_secs = wrapped_b(sample, out["dtype_gate"]["chosen"])
    out["http_throughput"] = {"sample": SAMPLE, "A_chunks_per_second": round(SAMPLE / a_secs, 2),
                              "B_chunks_per_second": round(SAMPLE / b_secs, 2),
                              "B_over_A": round(a_secs / b_secs, 3)}
    print("http", out["http_throughput"])
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "validation.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
```

## `results/corpus-manifest.json` (the rebuild)

```json
{
  "offrig": "offrig 1.1.1",
  "offrig_exe_sha256": "491602715e185b8601ec4d9b8ae1695e070e1fe1cc895efefb537ae613ee2ba4",
  "pins": [
    {
      "name": "rnd",
      "ref": "origin/main",
      "commit": "59180754260ac0bacf54a6bfd62fa8c70a085688",
      "files": 154
    },
    {
      "name": "readouts",
      "ref": "origin/main",
      "commit": "75b222527ff624fcff0deba571295bfc688bbfa7",
      "files": 659
    },
    {
      "name": "role-set",
      "ref": "origin/main",
      "commit": "e38feef85a67196f5dbc837f20a1a25ff98058dc",
      "files": 34
    },
    {
      "name": "offrig",
      "ref": "origin/main",
      "commit": "060090461adcc8efd3b5e675770338b6423f1c05",
      "files": 47
    }
  ],
  "chunks": 11525,
  "by_kind": {
    "code": 1453,
    "doc": 10072
  },
  "by_source": {
    "offrig": 1125,
    "readouts": 8695,
    "rnd": 1377,
    "role-set": 328
  },
  "max_body_chars": 2175,
  "chunks_sha256": "95dad37608db3f5f81f6a8ce78b8ff757f650f199af673fa8f4b369867a36e0c",
  "db_sha256": "9aabed70942f62787a624b3986649a2525a5bf4a991c000f7ef522a0193df1b3"
}
```
