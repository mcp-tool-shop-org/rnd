# Local builders, Wave 1: design

**Template:** rnd handbook, [model comparisons](https://mcp-tool-shop-org.github.io/rnd/handbook/model-comparisons/)
(rnd #116, `0464b50`). The A/B template's sections 3, 6 and 7 apply too.

**Status:** drafted by the Publisher, 2026-10-16; reviewed and filed by R&D the same day with the changes below.
**Nothing runs** until Argon has reviewed the design and the maintainer has approved it. The maintainer has read
section 1's first draft. Change 2 below alters its second sentence.

**R&D's review changes** (2026-10-16):
1. **The screen runs on Colab, on one pinned A100-40GB,** not the 5090 (section 6). This corrects R&D's earlier
   "one pinned L4": a 24 GB L4 can't hold these 27–36B models, and most would read "doesn't fit".
   - `OLLAMA_GPU_OVERHEAD` sets the usable budget to the 5090's 26 GB plan cap, so "doesn't fit" means the same
     as on the rig.
   - Colab isn't shared with ASPIRE, so the screen doesn't wait for the governor (section 8).
   - Wave 2's confirmatory runs stay on the 5090.
2. **J1's control is Argon's first-round items** (aspire-si #162 at `ff20f44`, the 30 T04, T09 and T10 slots), not
   the revised ones. The revised items went through R&D's non-blind feedback rounds, and the local models get one
   shot. R&D has seen those items, so **a fresh grader keys the shuffled pool:** an R&D subagent working from a
   written rubric, which hasn't seen any of the items. R&D audits its disagreements.
3. **`num_ctx` per job kind, from the validation run:** the largest prompt plus output seen, times 1.5, rounded up
   to a power of two. Not 65536 for both. An oversized context inflates the KV cache and makes "doesn't fit" a
   setting, not a property of the model.
4. **J2's recall guard:** record each candidate's release date and stated training cutoff. A task counts only if its
   fix merged after every candidate's cutoff, or after its release date where no cutoff is stated.
5. **Read the machine line from the serving process, not the install folder.** Two Ollama trees exist side by side:
   - the studio CUDA 13.4.3 build serves port 11434, activated 2026-10-16 13:18 under `ACTIVATION-PLAN.md`
     (`ggml-cuda.dll` `0ebc0e61…`; its start script pins all five hashes and refuses on drift);
   - the untouched install keeps the stock backend (`2f7f959a…`) as the `USE_STOCK=1` fallback.

   The run-time check reads the listening process's path and the hash of the module it loaded.
   (R&D's first filing hashed the install folder and called the studio build inactive. The Publisher corrected
   that, and R&D confirmed it on the rig.)
6. **The card sub-study uses real cards** (T4 16 GB, L4 24 GB, A100 40 GB on Colab). Only 8 and 12 GB stay
   simulated, and are labelled so.
7. **Run order:** each model runs as a block, in a seeded order recorded in the receipts, with the model unloaded
   between blocks. A local runtime has no service drift, so blocks are acceptable; the A/B template's
   interleaving rule is about hosted services.

**Sources:**
- the maintainer's goal (2026-10-16);
- Browser Argon rounds 1–2;
- R&D's rulings of 2026-10-16;
- model facts checked on the HF Hub and with `ollama show`.

## Standards compliance

| Standard | Score | Evidence |
|---|---|---|
| PIN_PER_STEP | 2 | Every run pins the model digest, harness version, prompt hash, sampling, context, effort and machine line (section 7). No pin changes inside a confirmatory run (section 2). |
| ANDON_AUTHORITY | 2 | The governor's tiers, the containment probe and the stop rules (section 8) halt the wave on a defect. A bad item never enters training on its own say-so. |
| NAMED_COMPENSATORS | n/a | No irreversible call. Builders never push, merge, tag or publish, and worktrees are local and kept. Model pulls are reversible by the model-archive procedure (its PURGE-NOTES; owner: the Publisher). |
| DECOMPOSE_BY_SECRETS | 2 | The governor and router (interlock), the study (rnd), the task banks and the receipts store are separate. Only one record schema is shared. |
| UNCERTAINTY_GATED_HUMANS | 2 | the maintainer gates the design and every GPU window. "No decision at this sample size" is a written outcome, not a judgement call. |
| EXTERNAL_VERIFIER | 2 | Argon reviews the design (a different family from the drafter). R&D reviews the governor code; a fresh grader keys the items blind and R&D audits it. |

## 1. The check in three sentences (for the maintainer first)

1. **Job kinds and decisions:**
   - **J1:** which local model, if any, can write Stage 1-style apply items (schema-bound data with honest flags) well enough to sit beside a cloud-built control.
   - **J2:** which local models can fix a small real bug in our repos (make a red test pass without breaking the suite).
   - Wave 1 is a **screen**. It decides which models go on to Wave 2, not which model wins.
2. **Candidates:**
   - six local models, each through Ollama in its own chat template and tool format;
   - J1 runs through a thin Python driver on Ollama's native chat API, J2 through Aider;
   - the bar for J1 is Antigravity Argon's first-round 30 items on the same slots (aspire-si #162 at `ff20f44`).
   - There is no local incumbent yet. Wave 1's top model becomes Wave 2's incumbent.
3. **Why the measure answers the decision:**
   - **J1's measure:** the share of items that pass the repo's own gates **and** the fresh grader's blind key-check (R&D audited), flags included. That's exactly what makes an item usable.
   - **J2's measure:** the share of tasks where the target test passes, the full suite stays green and only allowed paths changed. That's exactly what makes a fix mergeable before review.

## 2. Candidates and pins

**Licences** are checked on the Hugging Face card, in its metadata. The Ollama digest is pinned at the run.

| Model (Ollama tag) | Digest | Licence (HF card) | Params (card) | Why it's in |
|---|---|---|---|---|
| `qwen3.8:27b` | `aaee06c39dcf` | Apache-2.0 | 27.8B dense | Argon's top pick for agentic coding |
| `qwen3.6:35b-a3b` | `a7eb95c53bcf` | Apache-2.0 | 36.0B MoE, ~3B active | Fast MoE |
| `muse-glimmer:30b-q4_K_M-dflash` | `da643f4663ab` | Apache-2.0 (meta-models) | 29.8B with vision | Strongest agentic model on disk; a third family |
| `gemma4:31b` | `6316f0629137` | Apache-2.0 | 32.7B with vision | A second family, strong at following instructions |
| `nemotron-3.5-lightning:latest` | `e7a64ff15fb1` | NVIDIA Open Model License | ~30B hybrid MoE | A fourth family; built for agents |
| `granite4.2:30b` | (pulling) | Apache-2.0 | 29.3B dense | A fifth family; tool calling |

**Settings:** each model's **documented production values** (its card's sampling), not one shared sampler.
- **Shared across all models:**
  - `num_ctx` per job kind, set from the validation run (R&D change 3) and recorded;
  - the server's KV cache type (left at the Ollama default, recorded);
  - an output cap of 16,384 tokens per turn.
- **J2 caps:** 30 turns and 15 minutes wall per task. Capped runs are reported apart.
- **J1 caps:** at most 3 gate-feedback retries per slot.

**Effort:**
- `think` is on at each model's default.
- A graded level (low/medium/high) is sent only where the preflight shows the Ollama API accepts it for that model. Otherwise it's recorded as `graded: unsupported`.
- The raw parameter sent is recorded on every request.

**Doesn't fit:** a model that can't run at these pins within the plan cap is recorded as **doesn't fit at this card**, and leaves Wave 1. It's never stepped down. The plan cap is 26 GB on the 32 GB card, per the maintainer's GPU rule.
- The fit is decided in the preflight (section 8), not mid-run.
- `nemotron-3.5-lightning` (25 GB of weights) is the likely case.

## 3. Native runtimes, guest arms and containment

- **J1 driver:**
  - it calls Ollama `/api/chat` directly, so the model's own template, tool format and system prompt apply;
  - every candidate gets the same task prompt, a pinned hash;
  - each slot's output goes through `role_set.assemble.assemble` and the gates. A gate refusal goes back to the model, up to 3 times.
- **J2 harness:**
  - Aider, at one pinned version, `--model ollama_chat/<tag>`, with the same edit format for every model unless a model's documented format differs (recorded);
  - flags: `--yes-always --no-check-update --analytics-disable`, plus `--llm-history-file` and `--analytics-log` for the record.
- **Guest arms:** none in Wave 1. In Wave 2, Claude Code against Ollama may run as a labelled arm answering "how well does Claude Code drive local models". It never ranks them.
- **Containment.** Every builder process:
  - runs in a detached worktree with its remotes removed;
  - has `HTTP_PROXY` and `HTTPS_PROXY` set to `127.0.0.1:9` and `NO_PROXY` set to `127.0.0.1,localhost`;
  - has `LITELLM_LOCAL_MODEL_COST_MAP=True`, `PIP_NO_INDEX=1` and `NPM_CONFIG_OFFLINE=true`;
  - reaches only `127.0.0.1:11434`.
  - **The probe** (section 8) proves that a builder-issued `curl https://example.com`, `pip install` and `git push` all fail.

## 4. Tasks and keys

**J1: 30 slots** (lessons T04, T09, T10; 5 C and 5 D each).
- These are the same `role-set plan --apply` slots as Argon's build, so **J1 waits for Argon's apply-items branch.**
- **The key:**
  - the slot's planned verdict;
  - the repo's gates;
  - R&D's blind check of every authored flag (`silent_without_deciding`, `order_free`, `r10_twin`).
- **Blinding:** a fresh grader, an R&D subagent that has seen none of the items, keys all of them in a shuffled pool
  with the source labels removed: Argon's first-round 30 plus each model's 30. It works from a written rubric
  (the gates, the slot's verdict, and the handoff's rules for DECIDING, ESCALATE and the flags). R&D audits every
  disagreement and a 10% sample.
- **Leakage and training:**
  - the slots are never in any prompt as finished items, and the driver never shows Argon's items;
  - local-built items are study data only, kept in their own partition;
  - they never enter Stage 1 training and never feed the generator.

**J2: 20 tasks** from real merged fixes in aspire-si, role-set and interlock, merged **after every candidate's
stated training cutoff** (or its release date where none is stated; R&D change 4). That way a fix can't be
recalled from pretraining. 2026-09-01 is the provisional floor until the cutoffs are recorded.
- **Building each task:**
  1. Take the fix's parent commit as a `git archive` into a fresh `git init` repo, so the fix is in no history.
  2. Add the fix PR's test.
  3. Remove the PR's CHANGELOG line.
- **The key:** the PR's test passes, the full suite is green, and only allowed paths changed.
- **Mix:** count distinct templates, not tasks, with at most 2 tasks from any one module. Mix single-file and multi-file fixes.
- **Bank and keys** are built and audited by someone other than the builder of the harness (R&D audits) before any run.

**Deferred to Wave 2:** review jobs (scored against planted defects), test writing (mutant-killing), and a second rep.

## 5. The ranking and the decision rule

- **Ranking measure per job kind:** the J1 and J2 rates in section 1. Reported but not decided on:
  - first-try pass;
  - retries;
  - malformed tool calls;
  - wall time;
  - peak VRAM;
  - energy.
- **The unit is the slot or task.** One rep in Wave 1, so there's nothing to average yet.
- **Report:**
  - each model's rate with a 95% interval;
  - P(best) by bootstrap over slots and tasks;
  - for J1, each model's rate beside Argon's control rate from the same blind key-check.
- **Pairwise tests:** none in Wave 1, because it's a screen. Wave 2 pre-names each challenger against Wave 1's top model: exact McNemar, with Holm across job kinds and pairs.
- **Sizing,** stated now:
  - **J1, 30 slots:** a paired difference smaller than about 23 points can't be shown.
  - **J2, 20 tasks:** smaller than about 35 points can't be shown.
  - Smaller gaps read as "not shown".
- **Cost:** wall time, peak VRAM and energy (`nvidia-smi` power integrated over the run) on the 5090, reported per model.
- **Decision rule,** in full:
  - a model **leaves** after Wave 1 if:
    - it doesn't fit at its pins; or
    - its J1 rate is below 50%; or
    - it resolves 2 or fewer of the 20 J2 tasks; or
    - it crashes its harness on more than 20% of runs;
  - of the rest, **the top 3 by P(best) per job kind go to Wave 2.** Ties at a low P(best) are reported as ties, and both go on;
  - **if no model passes the J1 floor,** the decision is "no local model writes apply items yet", and J1 waits for the next model generation;
  - **Wave 1 crowns no winner.**

## 6. Hardware, the card sub-study and preemption

- **Wave 1, the screen, runs on Colab** (R&D change 1):
  - one pinned A100-40GB, under `instruments/colab.md`'s rules;
  - the three-layer teardown, and `--timeout` sized to each run;
  - the machine line, with `COLAB_RELEASE_TAG` and the CPU;
  - stock Linux Ollama 0.40.4 at a pinned version;
  - `OLLAMA_GPU_OVERHEAD` set so the usable budget is 26 GB, matching the 5090's plan cap.

  **Unit budget:** about 13 GPU-hours at 5.30 units an hour, roughly 70 units. Cap: 90 units, the maintainer's to
  approve. Its wall time, VRAM and energy are reported for the A100, and aren't the 5090's cost.
- **Wave 2's confirmatory runs: the 5090.** The machine line is the RTX 5090 32 GB, driver 617.42, Ollama 0.40.4
  with the studio CUDA 13.4.3 backend (`ggml-cuda.dll` `0ebc0e61…`, active since 2026-10-16), read from the serving
  process (R&D change 5) and recorded with every run. A run under the stock fallback (`USE_STOCK=1`) is a different
  machine line, recorded as such.
- **The card sub-study ("what works on your card")** is Wave 2. There the profile is the treatment.
  - **Real cards on Colab:** T4 16 GB (with `--high-mem`), L4 24 GB and A100 40 GB, each its own machine line.
  - **Simulated 8 and 12 GB** come from `OLLAMA_GPU_OVERHEAD`, labelled "simulated: fit only, not bandwidth,
    compute or spill".
  - The governor's tiers are measured against the real or simulated size.
- **Preemption:** ASPIRE-SI holds GPU priority.
  - The governor leaves through orange: checkpoint, cancel, unload, GPU free.
  - **A preempted run isn't scored** against the model. It's rerun.
  - A run that blows its own time or memory cap is scored as a failure.

## 7. Receipts

They go to **interlock's receipts store**, in the shared schema, in their own partition. They never go to ASPIRE's frozen store.

**Each run records:**
- the task or slot id;
- the model tag and digest;
- the harness and its version;
- the prompt hash;
- every pin;
- the effort's raw parameter, and whether graded levels are supported;
- thinking and output tokens;
- truncation;
- turns and tool calls, malformed and failed;
- retries;
- wall time, peak VRAM and the energy;
- the governor tier events;
- whether the run was preempted;
- the grade;
- the machine line.

**Shaped for the effort study:** thinking tokens, truncation, correctness and difficulty are recorded together for every model, so the queued thinking-effort study can reuse them.

## 8. Before the first counted run

The A/B template's section 6 applies. In addition, in order:

1. **For Wave 2's runs on the 5090:**
   - the governor exists and passes its fault-injection tests. Antigravity Argon builds it in interlock, and R&D
     reviews it. The tests trigger each tier (yellow, orange, red); the GPU really frees; and the journal resumes;
   - the watchdog heartbeat is fresh, or the governor's preflight refuses.

   **Wave 1 on Colab** needs neither, because the VM is disposable and not shared with ASPIRE. It does need the
   three-layer teardown and the unit cap.
3. **A fit preflight per model at its pins,** recorded. "Doesn't fit" is decided here.
4. **The containment probe** passes for both harnesses.
5. **One free validation run per harness,** on a task not in the bank. Its token counts match Ollama's `prompt_eval_count` and `eval_count`, its wall time covers only the task, and every receipt field fills.
6. **the maintainer's go for each GPU window,** told before it starts: what, how hard, how long.
   - **Estimate:** J1 is 30 slots × 6 models at about 1 minute a slot with retries, roughly 3 hours. J2 is 20 tasks × 6 models at about 5 minutes a task (15 minute cap), roughly 10 hours.
   - **Wave 1** runs on Colab (about 70 units, capped at 90), so it doesn't wait for gaps between ASPIRE grants.
     **Wave 2's** 5090 windows sit between ASPIRE grants.

**Stop rules:**
- any network reach from a builder;
- any write outside the task worktree;
- a run whose start doesn't match its pins;
- a red-tier kill;
- a receipt field missing on more than one run.

Each halts the wave until it's explained.

## Order of work

1. Antigravity Argon: the apply items (Stage 1 critical path; brief ready).
2. The J2 task bank, the J1 driver and the fresh grader's rubric: a builder brief, with R&D auditing the keys.
3. Section 8's preflight on Colab, then Wave 1 on Colab on the maintainer's go (the unit cap approved).
4. Antigravity Argon: the governor in interlock, plus its fault tests, with a Linux sampler path. R&D reviews.
   Needed before Wave 2.
5. R&D's blind key-check, the report, and the Wave 2 design.
