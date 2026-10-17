# Stage 1 data regeneration: plan

**Why.** The maintainer's ruling (2026-10-16): regenerate Stage 1's training data (`experiments/generated-content-terms`).
*Revised 2026-10-17:* the proof rule this plan was first written under is withdrawn; a use is barred only by a clause.
Grok's and Argon's rows still can't train (the xAI distillation and Google ML clauses). Kimi's rows may train: Kimi's
weights are open and permissive (K3 MIT-style, K2.6 modified MIT), and its seat ran through Ollama Cloud, not the
Kimi app (PROVENANCE.md). The frozen set
(aspire-si `FROZEN.md` `e7b69464`) has these writers:
- Kimi wrote the pilot;
- Grok wrote batches 2–8;
- Antigravity Argon wrote the 210 apply items;
- Claude sessions made fix rounds.

**The maintainer's direction:**
- use the biggest models whose licences allow it for the whole process, writer and critic alike;
- **Colab for everything it can do; RunPod only for the roles that need bigger, multi-card models;**
- the RunPod tier and any dollars are the maintainer's to approve.

**Status (2026-10-16):** revised after Argon's consult (`argon-answer.md`). R&D re-read every licence clause it
cites at the primary source (section 1). **Nothing runs** until the maintainer approves this plan, and each Colab
or RunPod window is told to him first.

## 1. Licence-cleared models, re-read by R&D at the primary source (2026-10-16)

Each licence was read for any clause on outputs (the proof column is the 2026-10-16 record; a grant isn't required). Biggest first:

| Model | Size (total / active) | Licence | Proof, as R&D read it | Verdict |
|---|---|---|---|---|
| meta-models/Muse-Spark-Open-816B-A42B | 816B / 42B MoE | **Muse Model License** (released 2026-10-15) | The card's intended uses include "Synthetic Data Generation - generating high-quality training data for downstream model development." **The licence attaches conditions:** a model "trained … distilled, or otherwise improved using the Software or any outputs or results thereof" is a **Derivative**. Copies of a Derivative must carry the copyright notice, the licence and the Usage Policy, and each product using it must display "Built with Muse Spark Open". The repo is gated (legal name, date of birth, organisation). | **allowed, with conditions** (the maintainer's call) |
| deepseek-ai/DeepSeek-R1 and R1-0528 | 671B / 37B MoE | MIT | R1: "DeepSeek-R1 series support commercial use, allow for any modifications and derivative works, including, but not limited to, distillation for training other LLMs." R1-0528 words it differently: "DeepSeek-R1 series (including Base and Chat) supports commercial use and distillation." | **allowed** |
| nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B | 550B / 55B hybrid MoE | OpenMDW-1.1 (card: "Governing Download Terms: Use of this model is governed by the OpenMDW License Agreement, version 1.1"; released 2026-06-04) | OpenMDW-1.1: "does not impose any restrictions or obligations with respect to any use, modification, or sharing of any outputs" | **allowed** |
| nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B | 120B / 12B hybrid MoE | OpenMDW-1.1 (same governing line; released 2026-10-15) | as above | **allowed** |
| deepseek-ai/DeepSeek-R1-Distill-Qwen-32B | 32.8B dense | MIT (tag), with the R1 card's clause repeated on its own card | DeepSeek's distillation grant. The card notes the model is "derived from Qwen-2.5 series, which are originally licensed under Apache 2.0 License". Qwen2.5-32B's own card is plain Apache-2.0, silent on outputs. | **allowed; its maker grants it** (see the note below) |
| meta-models/Muse-Glimmer-30B | 30B dense | Apache-2.0 | the card's intended uses include "Synthetic data generation: Generating high-quality training data for downstream model development." | **allowed** |
| nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B | 30B / 3B MoE | OpenMDW-1.1 (the card governs, not the licence the Ollama tag bundles) | as for the Nemotrons above | **allowed** |

**Revised 2026-10-16 under the reworded rule** (allowed unless a contract or licence restricts it):
- **Plain Apache-2.0 models** (Qwen3.8 and 3.6, Gemma 4, Granite 4.2) **are eligible.** Their licence makes no claim
  on outputs, and no contract binds a local run. Gemma 4 is checked against Gemma's own use policy before it's used.
  (The earlier "not proven" counted silence as a bar.)
- **Nemotron-4-340B and Nemotron-3-Super (Dec 2025)** (NVIDIA Open Model License) are likewise unrestricted on
  outputs. They're out on size and placement, not licence.

**Out:**
- **Llama-based distills** (R1-Distill-Llama-70B, Llama-3.1-Nemotron-Ultra-253B): out, but **Argon's reason was
  wrong.** The Llama 3.3 licence (2024-12-06) doesn't bar training non-Llama models. Its Section 1.b.i permits using
  outputs "to create, train, fine tune, or otherwise improve an AI model", on condition that the model's name begins
  with "Llama". That naming condition on the studio's student is reason enough to leave them out. The 253B model is
  also under NVIDIA's own licence.

**Notes for the maintainer:**
- **Muse-Spark's conditions** would attach to the student verifier and to any product using it: carry the licence
  and Usage Policy, and display "Built with Muse Spark Open". It also needs a gated-access request in the
  maintainer's legal name, and only the frontier tier can run it (section 5). Out of reach at today's balance either
  way.
- **R1-Distill-Qwen-32B** stands on its maker's explicit grant, and its Apache-2.0 base adds no restriction, so
  it's eligible under the reworded rule. The Publisher's earlier "not used" rested on the base's silence.

## 2. Writer and critic

- **The writer is the role that needs the biggest model.** Writer text becomes the rows. The critic's words never
  enter a row: its verdict only gates and returns feedback, and the deterministic gates and the blind key check
  stand behind it.
- **Colab tier, the default:**
  - **writer:** Muse-Glimmer-30B, Q8_0;
  - **critic:** Nemotron-3.5-Lightning, Q8_0.
  - They're different families.
- **RunPod tier, only if the pilot earns it:**
  - **writer:** Nemotron-3.5-Super-VL-120B, Q8_0, on a pod;
  - **critic:** stays on Colab, a non-Nemotron model (Muse-Glimmer or R1-Distill-Qwen-32B).
  - Only the writer's hours are paid.
- **The critic differs from every writer it judges** (local-builders amendment A).
- Every row passes `role_set.assemble` and the aspire-si gates, unchanged.

## 3. The provenance inventory (step 0, before any generation)

Every field of every Stage 1 row is traced to its writer. Only these sources may reach the new rows:
- models whose licences allow the use;
- deterministic code: gates, assemble, slot plans, puzzle generators;
- the maintainer's own writing.

**What it covers** (widened per Argon's finding 3):
- **role-set's prompt templates and few-shot exemplars** (`prompts.py`, `exemplars.py`, `generate/`): any string
  written by Kimi, Grok, Argon or Claude that reaches a prompt.
- **The lesson drafts** (L1–L3 and the trait lessons) that seed the prompts: they're either written by the
  maintainer or reduced to structural specs.
- **The puzzle generators and their catalogues** (`puzzle.py`, `t10_*`, `t11_*`, `t12_*` JSON).
- **DEV (review-10 and pilot-20), sealed (130) and interview.QUESTIONS (12):** their writers are recorded next to
  `FROZEN.md`. Evaluation use is allowed wherever no clause bars it (revised 2026-10-17; it was "not proven").
- **The real-source quotes** (pinned open-source repo lines): human-written, under their own licences, recorded
  per row. Reusable.

Owner: R&D, from the repos' handoffs, briefs, PR threads and `.models.jsonl` sidecars. Output: one table in this
folder.

## 4. The generation path

**Serving: one stack, CUDA 13.4 everywhere** (the maintainer's 13.4 rule, inference included; Argon's finding 1).
- **llama.cpp `llama-server`, built with the CUDA 13.4 toolkit,** on every host, Colab and RunPod alike.
  - It's compiled to SASS for each card it meets (sm_75, 80, 89, 90, 100 and 120), so nothing relies on PTX
    just-in-time compilation. Minor-version compatibility doesn't cover that.
  - It's pinned by commit and binary hash. Models are Q8_0 GGUF, pinned by file hash:
    - Muse-Glimmer from `meta-models/Muse-Glimmer-30B-GGUF`, the maker's own;
    - the Nemotrons from `ggml-org` (llama.cpp's own conversions);
    - R1-Distill-Qwen-32B from a conversion recorded at the pilot.
  - The licence follows the original weights; a conversion adds none.
  - It's OpenAI-compatible, with `--parallel` and continuous batching.
- **The A100 has no FP8** (sm_80), and Q8_0 needs none, so FP8 drops out of the plan.
- **The driver API:**
  - **On RunPod:** `cuda-compat-13-4` with `LD_LIBRARY_PATH=/usr/local/cuda-13.4/compat` gives a real 13.4 driver
    API. It's proven on the A100 and B200 (`experiments/cloud-cu134`).
  - **On Colab** (a driver 580 host, CUDA 13.0): the cu134 build runs under minor-version compatibility, which
    passed on the T4, L4 and A100. The pilot also tries the compat package there. If it loads, the machine line
    says 13.4 driver API; if not, it says "13.4 runtime on a 13.0 driver".
- **vLLM and SGLang are a known gap.** Their wheels are built against their own CUDA (12.x or 13.0), and there's
  no cu134 build of either. They aren't used unless one is built against the cu134 torch and probed first.

**Waves, not inline critique** (Argon's finding 2, reframed by R&D after reading role-set):
- role-set already runs slots concurrently: `--concurrency` exists, and pilot 2 ran at 8.
- **The real blocker:** `Runner.run_slot` calls the critic inline for each slot, so the writer and critic must be
  loaded at the same time. Two 30B models at Q8 (about 63 GB) can't share one 40 GB card, and a pod writer can't
  call a Colab critic.
- **The fix is a wave mode in `role-set write`:**
  1. the write wave: writer plus mechanical gates, with immediate retries, writing a drafts file;
  2. the critique wave over the drafts file;
  3. a rewrite wave, with critic feedback, for the rejected slots;
  4. repeat up to the retry cap.
- The writer and critic then never share a card or a host. That's also what lets the writer sit on a pod while
  the critic stays on Colab.

**Deterministic guards before the pilot** (Argon's finding 4, accepted):
- a pre-assigned domain and frame table per slot;
- solve-first kind-B puzzles across rotating families, checked by `puzzle_check`;
- cumulative cross-batch exclusion state, covering shingles, openers and frames;
- inline freeze checks per batch: `no_role.build`, composition, `variant_checked_spans`, `make_twin` and `set_rule`.
- role-set already has some of this (`plan.py`'s puzzle families, `puzzle_check.py`, `generate/t10_variety.py`).
  The step-0 inventory records which guards exist, and only the gaps get built.

**Jobs:**
- **Each Colab job is a `colab run` script,** under `instruments/colab.md`:
  - the machine line, with `COLAB_RELEASE_TAG`;
  - the card asserted;
  - `runtime.unassign()` in `finally`, plus a watchdog;
  - an outer timeout and the sessions-empty check;
  - results back by `colab download`.
- **Each RunPod job goes through offrig,** under the pod rules:
  - full specs first;
  - writes that auto-start and relaunch once the lane serves;
  - no manual steps on a billing pod;
  - offrig's watchdog deadline;
  - shutdown the moment the wave is done.
- **Every row records** its writer, critic, model revisions, quant hashes and seeds, plus its `partition`
  (`production`).
- **Variety and the key check** use the bar from aspire-si #155 and #162, on every kind: side-by-side reading, the
  opener-frame share against training, and keyed fields against their rules.

## 5. Hosting and money

**Colab** (Pro+, about 1,207 units left):
- all critique;
- the Colab-tier writer;
- the pilot.
- **The Colab-tier full run:** Argon estimates 20–28 units. R&D's earlier 10–20 assumed batching that the wave mode
  now provides. Proposed cap: **30 units**, confirmed after the pilot measures the rate.

**RunPod, writer waves only.** Live offers (offrig, 2026-10-16, all "LOW" stock):

| Card | VRAM | $/hr | Super-VL-120B at Q8_0 (~127 GB) | CUDA 13.4 forward compatibility |
|---|---|---|---|---|
| 1× H200 NVL (Hopper) | 143 GB | 3.79 | fits, about 16 GB for KV (the hybrid Mamba design keeps KV small) | **not yet probed:** Hopper isn't covered (`cloud-cu134`) |
| 1× B200 (Blackwell) | 180 GB | 7.99 | fits with room | **allowed** |
| 2× RTX PRO 6000 Blackwell Server Edition | 192 GB | 4.98 | fits, split across two cards | **not proven.** NVIDIA's forward-compatibility page (updated 2026-09-09) covers "NVIDIA Data Center GPUs", "Select NGC Server Ready SKUs of RTX cards" and Jetson, and names no models |
| 2× H100 80GB (Hopper) | 160 GB | 7.98 | fits, split | not yet probed |

**The 13.4 rule decides the card:**
- **First, the cu134 probe plus compat on one H200 NVL** (`experiments/cloud-cu134`'s script, about 10 minutes,
  **about $0.60**). If it passes, the H200 NVL is the card.
- **If it fails, the B200,** which is proven, at about twice the hourly rate.
- **The RTX PRO 6000 isn't relied on** until it has a probe of its own.

**Sizing** (estimates, not measurements; llama.cpp is slower than vLLM's batching, and the estimates allow for
that):
- **A RunPod writer pilot** on the same 20 slots: about 1 hour with the download and load, **about $4–5** on the
  H200 NVL (about $8 on a B200), plus the $0.60 probe.
- **The full writer run:** about 1.6M writer tokens at an assumed 80–100 tok/s aggregate, about 5 hours, plus load
  and one rewrite wave in a second session. **About $22–28 on the H200 NVL; about $45–55 on a B200.**
- **Against the balance:**
  - the RunPod balance is **$29.55**, and offrig's project cap is $30;
  - the account's caps across projects already promise more than the balance holds;
  - **so the pilot fits now, but the full big-writer run needs a top-up** for any margin. The maintainer decides
    the top-up after the pilot, at measured rates.
- **Frontier tier** (Muse-Spark-816B or R1-0528 writing, Ultra-550B critiquing, 8× H100/H200, about $110–190):
  **out of reach at today's balance.**

## 6. The local-builders study (J1 = the writer selection)

- **The control is role-set itself** (local-builders `DESIGN.md`, amendment A, rnd #124).
  - **Incumbent:** the Colab pair.
  - **Challengers:** the same pipeline, prompts, gates and critic, with only the writer swapped.
- **Challengers today:**
  - **R1-Distill-Qwen-32B** (Colab): a different family from the critic, so it's ranked on everything.
  - **Nemotron-3.5-Lightning as writer** and **Super-VL-120B** (the RunPod pilot): both share the critic's
    Nemotron family, so they're **ranked on first drafts only**: the gates and the blind key check before any
    critic feedback. First drafts are the writer's own signal anyway.
- **Measures:**
  - gate pass, on the first try and after retries;
  - the blind key-check rate;
  - variety against the #155 and #162 bars;
  - cost per accepted item.
- **Partitions:** J1 runs go to `trial:j1-wave1`. No trial text reaches prompts, lessons or rows.
- **The incumbent meets the 50% floor.** Below it, the regeneration halts.
- Argon suggested a 16-item set written by the maintainer as an anchor. It's advisory, kept as an option if the
  maintainer wants a human reference point.

## 7. Order and device time

1. **The provenance inventory:** R&D, CPU only.
2. **role-set changes** (a builder brief, with R&D reviewing): the wave mode and the missing guards.
3. **The Colab pilot,** one A100 session:
   - **20 slots spanning kinds A–E plus apply twins** (Argon's finding 5);
   - the incumbent and R1-Distill-Qwen-32B on the same slots, and Lightning as a writer on first drafts;
   - it measures tok/s, gate pass, retries and units;
   - **about 1 hour, about 5–6 units.**
4. **The RunPod writer pilot:**
   - the 13.4 probe on the H200 NVL first;
   - then Super-VL-120B on the same 20 slots, about $4–5;
   - critiqued on Colab. **The maintainer
   is told first.**
5. **The writer choice** from the J1 measures. Then the maintainer decides between the Colab tier and the RunPod
   tier with a top-up.
6. **The full run:**
   - batches 1–8 (810 rows) and the 210 apply items, in Colab sessions of about 1–2 hours;
   - plus pod writer waves if the RunPod tier is chosen.
7. **R&D's key check and variety check,** then the freeze rerun (`freeze.py`) and the composition check.
8. **Retire the provider-written data** when the regeneration lands. The maintainer decides the public-history
   question separately.

## Decisions (2026-10-16)

The maintainer's own rulings, plus those he delegated to the Publisher or R&D:
- **Regenerate everything:** all 810 training rows and the 210 apply items (*revised 2026-10-17:* Kimi's rows may
  be kept). The maintainer
  made no exception for the Grok-written batches: xAI's AUP lists "distilling model data or Outputs" among the
  uses you agree not to make, and his rule doesn't read it narrowly.
- **The student verifier is a specialized tool** in the sense of Anthropic's Help Center article 12326764. So
  Claude-written code, prompts, lessons, evaluation sets and row inputs may be used. **No Claude text is a training
  target.** Claude Code builds role-set's changes from BUILD-SPEC.md.
- **Argon- and Grok-written generator code is rewritten** (R&D, delegated): aspire-si #144 and #145 (gates 1.7.3),
  role-set #55, and role-set #49, #53 and #54, with #49's clue templates and packs replaced.
- **Code is read plainly (the maintainer, 2026-10-17):** studio code that no model trains on is allowed whoever wrote it, Antigravity included. The clean-room re-implementations of aspire-si #144 and #145 and role-set #55 stay as they are (no churn back). Training data from consumer services stays out.
- **Grok's generator logic stays; only its text is replaced** (the maintainer, 2026-10-16). role-set #49, #53 and #54 keep their logic and tests, credited "Written with Grok". Their clue templates and packs, which reach rows, are replaced. Argon's #55 is still re-implemented under Google's ML clause.
- **Interlock keeps its Grok and Kimi code** (R&D, delegated). Kimi ran through Ollama Cloud. Grok's work is
  credited "Written with Grok" in CONTRIBUTORS.md (interlock#130, role-set#69).
- **R1-Distill-Qwen-32B is not used** (the Publisher, delegated). **The Colab critic is Muse-Glimmer** for
  Nemotron writers, and Lightning critiques Glimmer writers.
- **The Colab cap is 30 units** for the full Colab share (the Publisher, delegated). **The RunPod probe and writer
  pilot are approved** (about $5–6). **A top-up for a full big-writer run stays the maintainer's call.**

## Still open

- **Muse-Spark's conditions:** moot unless the frontier tier is ever funded.
- **The Kimi pilot's 40 T04 rows:** usable under the reworded rule if they were written through Ollama Cloud (the
  route needs the maintainer's confirmation). They're regenerated anyway unless he says otherwise, for a uniform
  set.
- **Apache-2.0:** ruled 2026-10-16 under the reworded rule: eligible.
