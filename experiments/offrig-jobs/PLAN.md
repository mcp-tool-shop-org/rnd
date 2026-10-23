# offrig `--jobs`: the 30-item measurement on the 5090

R&D, 2026-10-22. Draft, for the Publisher's grant once the `--jobs` PR has merged (Antigravity build, Argon code
round). Free: the local card only, no paid step.

## The question

Does running several claims at once through one local Ollama raise throughput on the 5090? Does it change what the
model answers? Both matter: a study pins its teacher's outputs, so a faster run that answers differently is a
different teacher.

## Setup

- **Model:** gemma4:31b, Q4_K_M, the digest distill-ladder pins. Settings are the teacher's own: think on, structured
  on, `num_predict` 4096, offrig's auto `num_ctx` (8192 on this card), temperature 0, seed 0.
- **Items:** `bench30.jsonl` (kept local: built from distill-ladder training items), sha256 `0c88ec0f915c911a99d3fcf2d2e91104c0c65b0f279656f27afa2244099ce547`.
  - 30 items from distill-ladder's training file, picked with seed 20261022 and half of each label where the count
    allows: L1–L4 2 each, L5 4, L6 4, L7 5, L8 5, sweep `steps=3` 2, sweep `precedence=3` 2. The weight sits on the
    heavy cells, where the card spends its time and where truncation happens.
  - 24 of the 30 were already answered in teacher window 1 (3 of them truncated there). That's a third reference at
    N = 1.
- **Each arm** gets its own scratch project and output directory, never the teacher's. Each starts from an empty card
  with a fresh Ollama server started with that arm's environment. The studio's CUDA build stays the backend: check
  `ollama --version` and the loaded runner against the GPU-stack note before the first arm.

| Arm | `--jobs` | `OLLAMA_NUM_PARALLEL` | KV cache | Flash attention |
|---|---|---|---|---|
| A1 | 1 | 1 | f16 | auto |
| A2 | 1 | 1 | f16 | auto (A1 repeated: the run-to-run control) |
| B | 2 | 2 | f16 | auto |
| C | 4 | 4 | f16 | auto; skipped and recorded if the model offloads |
| D | 4 | 4 | q8_0 | forced on (`OLLAMA_FLASH_ATTENTION=1`) |

## What each arm records

- **Throughput:** items per hour from elapsed wall time (the report's new elapsed figure), and each claim's own latency.
- **Memory:** `/api/ps` after load (`size_vram == size`, so offloaded is false). Peak VRAM from `nvidia-smi`, sampled
  every 2 s through the arm.
- **Answers, against A1:** for each claim, whether these are byte-identical:
  - `model_verdict` and `final_verdict`;
  - `reasoning` and `evidence_quote`;
  - the unusable code.

  Also the count with `final_verdict == label`, and the truncation count.
- **The control:** A2 against A1 says how much a single stream varies by itself. An arm "changes answers" only beyond
  that.

## Decision rule (fixed before the run)

- **Adopt `--jobs N` for new runs** if:
  - its items per hour are at least 1.5× A1's;
  - it doesn't offload;
  - its answers differ from A1 on no more claims than A2 does.
- **If answers move beyond the control:**
  - `jobs` goes into offrig's resume identity (a follow-up PR);
  - concurrency is allowed only in a fresh run whose plan names it;
  - never mid-study.
- **D only counts if it passes on its own.** It changes the KV cache's precision, which is a second variable. If C
  fits, D's result is reported but not adopted.
- **distill-ladder:** whatever this shows, its teacher keeps its pinned single stream unless the truncation consult and
  a plan change say otherwise.
- **The Publisher's condition (2026-10-22):** until this shows outputs hold, `--jobs` above 1 is used on no pinned study
  run, distill-ladder's teacher legs included. The report gives each arm's agreement with A1 next to A2's, as a table
  per claim (verdict, reasoning, quote, unusable code), not only items per hour.

## How this relates to study 1 (batching drift)

Study 1, in the R&D queue, asks the same question at scale: it replays Track B and T10 prompts through llama-server on
Colab at batch 1 twice, then at 2, 4 and 8. It measures token divergence, verdict flips and throughput. This plan is
the local, verdict-level slice of that question for offrig against Ollama on the 5090, with the same control: the
batch-1 repeat is the noise floor.
- Its results go into study 1's design as a prior. They don't replace it.
- If answers move here, study 1 is where the size and cause of the drift are measured.

## Cost and the grant

- **Card time:** about 15 minutes each for A1 and A2. Window 1's times for 24 of the items sum to 625 s, and the other
  6 are estimated at about 48 s (L8) and 35 s (sweep). B, C and D are shorter if concurrency helps. Add about 1 minute
  per model load and server restart.
- **Ask:** 75 minutes of the 5090, peak about 24–31 GB depending on the arm, then "card free". The 15-minute rest
  before the next heavy holder is owed, as usual.
- **Restarts:** the Ollama server restarts between arms with different environments. The Publisher's grant has to
  cover that, because every other user of the local server waits.

## Standards (short form)

- **Pinned per step:**
  - the item file's sha;
  - the model digest;
  - the offrig commit, and each arm's environment written to its output directory.
- **Halt rule:** any arm that offloads, or whose server falls back off the studio CUDA build, stops and is recorded.
- **Undo:** none needed. Scratch directories only, and the server returns to its normal environment at the end.
- **The human check** is the Publisher's grant. The result is written up as an rnd finding, whichever way it falls.
