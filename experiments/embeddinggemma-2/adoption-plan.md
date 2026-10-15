# EmbeddingGemma 2 in offrig: the adoption plan

**For:** the Publisher, before the offrig change is written. **From:** R&D, 2026-10-15.

The benchmark decided "adopt B at 768" (`results.md`). This plan covers four things:
- what the change touches;
- how stores are re-embedded;
- what happens to a store indexed with the old model;
- the one placement decision the Publisher makes before any code.

Every figure is labelled **measured** or **inferred**. The code facts were read at offrig `9b11ba1`, release 1.1.3.

## The models

| | Old | New |
|---|---|---|
| Name offrig stores in `embed_model` | `nomic-embed-text` | `embeddinggemma-2:f32` |
| Weights | Ollama digest `0a109f422b47`, F16 GGUF | `google/embeddinggemma-2`, revision `914f7f89142e33e77833254d9c9b90c3cef7303b`, text only (271M parameters) |
| Runtime | CPU-only Ollama on 11490 | sentence-transformers 6.1.0 on a CPU-only torch build (2.14.1+cpu), float32 |
| Dimension | 768 | 768 |
| Document prefix | `search_document: ` | `title: none \| text: ` |
| Query prefix | `search_query: ` | `task: search result \| query: `, for code queries too (the code prefix measured −0.008) |

**Why a new name, not `embeddinggemma-2`.** Ollama's library uses `embeddinggemma-2:*` for MLX builds, which have different weights and a different dtype. Those would make 768-dimension vectors that pass `check_dim`, so a store could silently mix runtimes under one name. The `:f32` tag names the treatment that was measured, and no Ollama tag uses it.

## Why it needs a server of its own

Ollama 0.40.4 on Windows refuses every EmbeddingGemma 2 tag with "requires MLX support" (measured). offrig embeds only through Ollama's `/api/embed`. So the change adds a small loopback server that answers what offrig calls:
- `/api/embed`;
- `/api/ps`, reporting `size_vram: 0`, so `check_cpu_only` gets positive evidence;
- `/api/tags` and `/api/version`.

It has the same shape as the `npu-serve` probe. It runs the model exactly as arm B did:
- `normalize_embeddings=True`;
- the model's `default_prompt_name` is null (measured from the pinned config), so offrig's prefix is the only prefix;
- it refuses to start if torch sees CUDA;
- it refuses any model name it doesn't serve, with a 404.

That last refusal is load-bearing. A server that embedded `nomic-embed-text` requests with EmbeddingGemma 2 would return vectors that pass every check offrig has.

## What changes in offrig

1. `DEFAULT_EMBED_MODEL` becomes `embeddinggemma-2:f32`.
2. `task_prefix()` gains the EmbeddingGemma 2 prefixes, with no kind routing.
3. `start_line()` and the 404 message in `Ollama::embed` stop saying `ollama pull`. They name the new server's start command. A 404 on a store built with another model says what to do: the index was built with X, the server serves Y, so run `offrig index --rebuild`, or search with `mode=keyword`.
4. `DEFAULT_EMBED_URL` stays `http://127.0.0.1:11490`. The new server takes 11490, and the CPU Ollama that serves nomic there stops.
5. The pins in `verify.rs` (`embed_model`) and the tests that name `nomic-embed-text` as the default move with it.

## What a store indexed with the old model does after the upgrade

Read from the code at `9b11ba1`:
- **`offrig index <paths>`** is refused by `check_model`: "the project index was built with nomic-embed-text, not embeddinggemma-2:f32; run `offrig index --rebuild`". Nothing is written.
- **Memory and project search** pick hybrid by default when the store has vectors (`plan_mode`). They embed the query with the store's own model (`index_model`), so the request asks the new server for `nomic-embed-text`. It gets a 404, and the search is **refused, not degraded**. Keyword search still works with `mode=keyword`.
- **The MCP side-car's background embed** (`embed_new_records`) is best effort. New records stay unembedded, and searchable by keyword, until the rebuild.
- **Nothing is ever mixed.** `check_model` and `check_dim` stop every write, and the 404 stops every query.

**Which stores that touches on this rig** (measured, read-only, every `E:/AI/*/.offrig/offrig.db`):

| Store | Chunks with vectors | Model |
|---|---|---|
| rnd-cpu-index | 201 | nomic-embed-text |
| rnd-npu-index-nomic | 201 | nomic-embed-text |
| rnd-npu-index | 201 | bge-base-en-v1.5 |
| every other store (Publisher, Research and Development, switchyard, …) | 0 | none |

The three with vectors are R&D's own test stores. No production store on this rig holds vectors, so the first `offrig index` in each embeds with the new model and needs no rebuild. **Not measured:** stores on another machine. Any there that were built with nomic need `offrig index --rebuild` after the upgrade.

## How the re-embed runs

The same command as today, against the new server on 11490:

```
offrig index --rebuild --project <dir>
```

- **CPU only.** The server runs on a torch build with no CUDA and refuses to start if CUDA is visible. No GPU grant is needed.
- **Time** (measured during the benchmark, which ran 11,525 chunks):
  - 2.6 chunks a second in process, and 2.02 over HTTP;
  - about 8 minutes per 1,000 chunks over HTTP (inferred from that rate);
  - about 1.7 minutes for a 201-chunk test store;
  - about 95 minutes for an 11,525-chunk store.

  A rebuild today would be slower. The CPU is 80% loaded by other processes (measured just now), and a batch of the 32 longest chunks took 164 s. A rebuild of any size should run when the CPU is quiet.
- **RAM** (measured just now, 63.4 GB on the rig, 44–46% used):
  - 1.7 GiB resident once the model is loaded, with a 12.9 s load;
  - at batch 32, the 32 longest chunks (about 1,500 tokens) peak at 6.8 GiB working set and 8.5 GiB commit.

  The server will encode in sub-batches of 8 to lower that peak. That's an inference, measured before release.
- **Before any rebuild:** system RAM under 80%, and the server's `/api/ps` reports `size_vram: 0`.

## The decision for the Publisher: where the server lives

**Ruled by the Publisher (2026-10-15): in offrig as `tools/embed-serve/`, released as offrig 1.2.0.**

- **Recommended: in offrig, as `tools/embed-serve/`.** It ships in the same offrig release, under one review, and its version moves with the client it serves. offrig gains a Python sidecar, documented in the README with its own `requirements.txt` that pins the CPU torch build.
- **Alternative: its own repository.** That's a cleaner split, but the repo-first rule means creating and scaffolding it first, plus a second release to coordinate.
- **Not rnd.** rnd is the research library, not a home for a running service.

Once you rule on this, R&D writes the change and exercises it end to end on 11490:
- rebuild the 201-chunk test store;
- confirm `embed_model` and `embed_dim`;
- confirm `/api/ps` reports `size_vram: 0`;
- confirm that searching a nomic store gets the new refusal text.

Then R&D sends it to you with the measured rebuild time and peak RAM.

## Compensators

| Action | Undo | Owner |
|---|---|---|
| offrig release with the new default | Install the previous offrig. Restart the CPU Ollama on 11490 with nomic. A store already rebuilt with the new model needs `offrig index --rebuild --model nomic-embed-text` | Publisher |
| `offrig index --rebuild` of a store | Rebuild again with the old model (the chunks are kept, and only vectors are replaced) | whoever ran it |
