# BUILD BRIEF | Seat C | role-set: the Advocate, the second writer swap before the pilot | mcp-tool-shop-org/role-set | from R&D, with the Publisher | 2026-10-15

**Status:** fix-up 3 passed (R&D verdict on #56, settled with Argon's round 8). One change comes before the pilot, on the Director's decision.
- **The licence:** `llama3.1:8b`'s licence (Llama 3.1 Community License, clause 1.b.i, verified by R&D from Meta's `llama-models` repository) requires any distributed model trained on its outputs to have a name beginning with "Llama".
- **The Director's decision:** the second writer is swapped now, so the pilot measures the writers the training batch will use.
- **The new writer:** `granite3.3:8b`. Its family is granite, and its licence is Apache-2.0, checked by R&D in two places: the licence bundled in the Ollama build, and the `ibm-granite/granite-3.3-8b-instruct` model card. It's a standard GGUF build, already pulled on the rig. Its digest is `fd429f23b90980ed1bef53b990894e7b0199331f6ae90c5650240a7d5b70f1f7`, Q4_K_M, 8.2B parameters, 4.9 GB.

Small turn. Load no model.

## The change

1. **`writers.json`:**
   - Add `granite3.3:8b` with its digest, `"quant": "Q4_K_M"`, `"licence": "Apache-2.0"` and `"checked_by": "R&D, 2026-10-15: the Ollama build's bundled licence and the HF model card"`.
   - Keep the `llama3.1:8b` row, and add a `"note"`: `"Not for training items: Llama 3.1 Community License 1.b.i requires a distributed model trained on its outputs to be named 'Llama…' and to display 'Built with Llama'. Verified by R&D from meta-llama/llama-models models/llama3_1/LICENSE, 2026-10-15."`
2. **`pilot.py`:** `WRITERS = {"writer-a": "qwen3:8b", "writer-b": "granite3.3:8b"}`.
3. **Tests:**
   - Update any test that names `llama3.1:8b` as writer B.
   - Add one assertion that the three pilot models are three different families (qwen3, granite, gemma4), read from `writers.json` or a fixed map, so a later swap can't put two writers in the same family.
4. The CHANGELOG line under Unreleased.

## Hand-back on #56, then stop

- The head SHA, the suite count and time, coverage, and CI inside 10 minutes. `pack verify` unchanged.
- **The grant request, restated:**
  - writer 1 `qwen3:8b` (500a1f06…, 5.2 GB, thinking off);
  - writer 2 `granite3.3:8b` (fd429f23…, 4.9 GB);
  - critic `gemma4:31b` (6316f062…, 19 GB);
  - one model at a time, peak 19 GB, about 60 minutes, caps 90 minutes and 24 GB, Ollama 0.40.4.
- The `--mock` table again. The families changed, so the attempts per family change in name only.

**Stop.** R&D checks the diff, which is a small turn with no consult, and then the Publisher posts the grant.

## Gates

- Suite green at the coverage floor. CI inside 10 minutes. `atlas check`. The identity scan CLEAN.
- Run the suite with `uv run pytest -m "not sweep" -n auto`.
- Touch only the files named here.
