# Local agent, diagnosed with NeMo Relay: design v0 (prototype)

**Status:** prototype v0. The Director approved it on 2026-10-13 as a prototype to build on, the same status as the templates. It follows the [diagnose-then-fix](https://mcp-tool-shop-org.github.io/rnd/handbook/diagnose-then-fix/) and [A/B experiments](https://mcp-tool-shop-org.github.io/rnd/handbook/ab-experiments/) templates, and it comes from Argon's consult on the local-first brief. Every change after v0 is a dated entry in the amendment log at the end.

**Order of work:**
1. Step 0, on the local model only; it publishes nothing.
2. The Step 0 results, including the speed figure, go to the Publisher before stage 1 is scheduled.
3. The plan-cost estimate for writing the new tasks goes to the Publisher before anyone writes them.

Every GPU run needs the Publisher's grant, and the Publisher tells the Director before granting.

## The check in three sentences

1. **Stage 1:** with nemotron-3.5-lightning running as a coding agent in Hermes Agent, do Relay's traces show the mechanical causes of its wasted work, more clearly than Hermes's own transcripts? The causes include impossible or malformed tool calls, attempts at forbidden actions, oversized tool output, loops, and runs that stop early or hit the cap.
2. **Stage 2:**
   - On 20 locked, unseen tasks, the baseline arm runs nemotron in Hermes with default settings.
   - The tuned arm runs the same model in the same runtime, changed only by the fixes that stage 1's traces called for, from a table fixed in advance.
3. **Why that answers it:** the tasks are unseen while fixes are made, the model and runtime are the same in both arms, and each fix must lower the symptom it targets. So a gain in correct answers per GPU minute shows that the fixes made the local agent better. Whether Relay saw more than Hermes's own transcripts is a separate result, from stage 1, not from stage 2.

## Why local, and why Hermes

- The aim is to make local models work well for the studio's read-only repository work. A local model runs in an agent built for local models, not as a guest in Claude Code.
- Argon recommends Hermes Agent. It's reported to have Relay built in, and to read the tool-call format the model emits.
- Each claim Argon made about the runtime and the model is checked in step 0 before it's relied on.

## Step 0: checks before any counted run (harness debugging, local, publishes nothing)

| # | Claim from the consult | How it's checked |
|---|---|---|
| 1 | Hermes has Relay built in and writes ATOF and ATIF to local files | Install the Hermes sandbox kit, run one trivial task, and look for the files |
| 2 | Hermes drives nemotron through Ollama's OpenAI-compatible `/v1` with working tool calls | The same run: a tool call is parsed and executed |
| 3 | The model loads at its pinned 131k context through `/v1` on every turn | Ollama's `/api/ps` `context_length`, read during a multi-turn run; the derived `nemotron-3.5-lightning-131k` model sets it in its Modelfile |
| 4 | The prompt prefix is reused between turns (no full re-prefill each turn) | Prompt-evaluation times per turn, from Relay or Ollama |
| 5 | The model's speed. The consult says 28–38 tokens/s; the studio's own record says about 312 tokens/s | One timed run. The figure sets the GPU budget below |
| 6 | The sampling the model card recommends (the consult says temperature 1.0, top_p 0.95 with thinking on) | Read the model card. Pin whatever it says |
| 7 | Relay can gate a tool call before it runs, not only mark it | Relay's documentation and one test. If it can't, that fix row uses the agent's own tool list instead |
| 8 | Containment holds for the Hermes kit as it does for Claude Code | The sentinel probe, adapted to Hermes |
| 9 | Nothing leaves the sandbox except Ollama traffic | `sbx policy log`, before and after |

If a check fails, the design is amended in writing and resubmitted before any counted run.

## Tasks

- **Bank hygiene:**
  - The repositories are rebuilt as single fresh commits, so no `atlas/` map or other answer survives in git history.
  - A check confirms that searching history for each key's answer finds nothing.
- **Mechanical tasks:** the 42-task bank is collapsed to one task per distinct question template, about 16.
- **New multi-step tasks:** 16 are added, written to the studio's real read-only work:
  - tracing a value through calls (6);
  - failure and retry conditions (5);
  - configuration that's defined but unused (5).

  Each key is written by one session and audited blind by another before any run.
- **The split, by repository:**
  - Diagnostic bank D: 12 tasks (6 mechanical and 6 multi-step) from 6 repositories.
  - Locked verification bank V: 20 tasks (10 and 10) from the other 11.

  V isn't opened or run until the fixes are frozen in git.
- **Strata, fixed before any run:** mechanical, and multi-step.

## Stage 1: diagnose (on D)

- **Runs:**
  - the 12 D tasks once each;
  - 4 planted faults: a 16k context cap on a large-file task, a tool output of about 25,000 tokens, a forced search error, and temperature 0 on an ambiguous prompt.

  That's 16 runs, recorded by Relay and by Hermes's own transcripts at once.
- **Waste, defined in a script before the runs:**
  1. a call to a tool that wasn't offered;
  2. malformed tool arguments;
  3. a forbidden action attempted;
  4. the same call repeated with nothing changed in between;
  5. three or more failed calls in a row on variations of the same thing;
  6. thinking that uses up the output budget before any call;
  7. a single tool output over 16,000 tokens, or a full re-prefill;
  8. hitting the turn cap, or giving up within two turns when the answer exists.
- **The comparison:** the same detection script, written once for each format, runs over Hermes's transcripts and Relay's trimmed traces. Anything the scripts can't decide is normalised into one table and read blind.
- **Stage 1's measures:**
  - for the planted faults, which records catch each one and place it at the right step;
  - for the natural runs, waste found in one format and missed in the other;
  - trace size after trimming;
  - setup time.

## The symptom-to-fix table (fixed now, before stage 1)

| Symptom found in stage 1 | Fixes allowed |
|---|---|
| Calls to tools not offered, or forbidden actions | Offer only read-only tools; remove editing and building language from the system prompt; a pre-call policy gate with a one-line refusal (if check 7 holds) |
| Oversized tool output | A cap on tool output with a hint to page through the rest |
| Repeated failures on paths | A short file list of the repository in the first turn |
| Loops, or thinking that uses up the budget | Sampling settings within the model card's range; a cap on thinking |
| Context blowout or re-prefill | Fix the context or prefix setting |

General fixes only, never hints for particular tasks. Anything else needs a dated amendment before V runs.

## Stage 2: verify (on V)

- **Arms:** B0 (Hermes and nemotron at defaults, 131k context) and B1 (the frozen stage 1 fixes). Each V task gets 3 reps per arm, interleaved in a seeded order. That's 120 runs.
- **The unit is the task:** its reps are averaged.
- **Primary measure:** correctness per task, by the audited key, with partial credit on sets.
- **Co-primary measures:** wasted turns per task, and GPU seconds per correct answer.
- **Attribution:** each fix's targeted symptom must fall in B1.
- **Size:** 20 tasks can show a gain of about 20 points or more in correctness. Smaller gains look like no difference. This is said up front.

## Decision rule (provisional: the thresholds are the consult's, and the Director may change them before V runs)

- **Local takes over read-only repository work** if B1 scores at least 85% on both strata, cuts wasted turns by at least half against B0, and averages under 0.2 forbidden or impossible calls a run.
- **Local takes the mechanical lookups only** if B1 scores at least 90% on mechanical tasks but under 75% on multi-step tasks, with its traces showing little waste. The limit is then the model's reasoning, not the harness, and a larger local model is the next study.
- **Hold** if B1 is under 80% even on mechanical tasks. The traces say whether the cause is the model or the context.

## Cost

- **Plan and API: none.**
- **GPU:** the consult estimates about 3 hours on the RTX 5090. Check 5 corrects that estimate before anything is scheduled.
- **GPU grants:** runs need a grant from the Publisher, outside measurement windows.
- **People and sessions:**
  - writing and auditing 16 new task keys is the largest piece of work;
  - then the waste script, the trimmer, and the Hermes containment check.

## Deferred, by the consult's advice

- **The NPU and the integrated GPU:** not in this study. A later one could use them for an always-on task router, trained on this study's labels.
- **Local against Claude, each in its own best runtime, on cost per correct answer:** a separate study, after this one.

## Amendment log

- **v0, 2026-10-13:** approved by the Director as a prototype. Stage 2 is credited with the fixes' effect, and Relay's added visibility is a stage-1 result. The thresholds are provisional until V runs.
