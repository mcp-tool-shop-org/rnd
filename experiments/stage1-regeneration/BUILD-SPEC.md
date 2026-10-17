# role-set build for the Stage 1 regeneration: spec

**Template:** rnd handbook, [dataset builds](https://mcp-tool-shop-org.github.io/rnd/handbook/dataset-builds/).
**For:** whoever the maintainer names as the builder (the code-authorship question is open; see "Builder").
**Reviewed by:** R&D, against role-set's code at `d4e4d18`. **Plan:** [PLAN.md](PLAN.md).
**Status (2026-10-16):** draft, with the provenance inventory in ([PROVENANCE.md](PROVENANCE.md)).

## Standards compliance

| Standard | Score | Evidence |
|---|---|---|
| PIN_PER_STEP | 2 | Every wave records the writer and critic GGUF sha256, the llama.cpp commit and binary sha256, the pack hash, the gates version and hash, the plan seed and the CUDA machine line (B6). A drift refuses the wave before any call. |
| ANDON_AUTHORITY | 2 | The existing cell, kind and systemic andons are kept across waves. The inline freeze checks (B5) halt a batch, with no re-roll. |
| NAMED_COMPENSATORS | 2 | See the table below. |
| DECOMPOSE_BY_SECRETS | 2 | The waves split along what changes together: the model on each host, the drafts file between them, and the gates unchanged. |
| UNCERTAINTY_GATED_HUMANS | 2 | The maintainer is told before each Colab or RunPod window. A floor miss or freeze-check failure goes to R&D and the Publisher, not to a retry. |
| EXTERNAL_VERIFIER | n/a | No specialised claims. The licence checks were done in PLAN.md §1. |

**Compensators** (irreversible calls in this build's runs):

| Action | Undo | State after | Owner |
|---|---|---|---|
| A RunPod pod launched (offrig_launch) | `offrig_shutdown`. The watchdog deadline terminates it regardless. | No pod, spend stops | the Publisher |
| A Colab VM assigned | `runtime.unassign()` in `finally`, the outer timeout, `colab stop`, then confirm the sessions list is empty | No VM, units stop | the Publisher |
| The role-set PR merged | `git revert` by PR | The previous generator | the Publisher |
| Regenerated rows committed to aspire-si | `git revert`; the receipts stay in the store, marked superseded | The previous freeze | the Publisher |

## 1. The check in three sentences

1. **What it teaches:** the same Stage 1 verifier lessons as the frozen set (the role pack is unchanged except where
   provenance forces a change), written now by models whose licences allow training on their outputs (no clause bars it).
2. **How an item is known to be right:**
   - by construction: the slot fixes the verdict, deciding line, escalation and flaw;
   - kind B's constraint model and solution are made in code before the writer sees the slot (B3);
   - real-source material comes from pinned repo lines.
   - The critic and R&D's blind key check then confirm, and never decide alone.
3. **How we'd know it taught the role and not a writer's fingerprint:**
   - the variety floors are gates, including across batches (B4);
   - a generator-identity probe across the writers runs in J1 (local-builders amendment A);
   - the frozen exam and the sealed set are untouched.

## 2. Builder

Anthropic's Help Center (article 12326764, dated 2026-03-16) allows Claude's outputs to train non-competing
"specialized classifiers and tools". It bars general chatbots, open-ended text generation models, and outputs as
training targets. Claude Code may build this. **Revised 2026-10-17:** Argon may build it too, because code the
studio owns is ordinary software under the generated-content rule, and Google's clause is read by its purpose
(training data and distillation into a rival model). Claude text may fill target fields too: the maintainer ruled
2026-10-17 that Anthropic's list bars competitive training only, and the verifier doesn't compete.

## 3. The build items

### B1. Wave mode in `role-set write`

**Today:** `Runner.run_slot` calls the critic inline after the mechanical gates, for each slot. The writer and
critic must therefore be loaded at the same moment, and both behind `127.0.0.1` on the same host.

**New:** `role-set write --wave {write,critique,rewrite}`, with a drafts file between waves.

1. **write:**
   - for each slot, the writer, then every check up to and including `ROLE_WORDS` (parse, shape, puzzle, stuck,
     assemble, truth, lesson copy, spent, `check_item`, role words);
   - a mechanical refusal is retried at once while the writer is loaded, inside the slot's attempt budget;
   - a candidate that passes is written to `drafts.jsonl` with state `awaiting_critique`.
2. **critique:**
   - for each `awaiting_critique` draft, `_critic_pass` unchanged, then the acceptance step under the lock, unchanged
     (`check_against` against the cumulative state of B4, `reply_opening_reused`, the lookup cap);
   - a pass goes to `accepted.jsonl` and `receipts.jsonl`, as today;
   - a critic or acceptance refusal becomes state `needs_rewrite`, carrying the refusal and its suggestion.
3. **rewrite:** the write wave over `needs_rewrite` drafts. It continues each draft's own conversation (the writer
   messages, the draft, then "Refused: <suggestion> …", as `run_slot` builds it today).

**Rules:**
- **One attempt budget per slot across all waves** (`MAX_ATTEMPTS = 3`). A slot that exhausts it is dropped, and
  the andon counts it as today.
- **The drafts file is the only hand-off.**
  - Each line carries the slot, the attempt count, the full writer conversation, the fields, the assembled row,
    the refusals so far, the state, and the writer pins.
  - Each wave records its input file's sha256 in its own output, so waves chain.
  - A draft whose pins don't match the run's pins is refused.
- **Each wave runs where its model is.** The loopback-only guard (`require_local_endpoint`) stays. Files move by
  `colab upload/download` and `offrig_put/get`.
- **`--mock` covers all three waves.** CI runs a mock write → critique → rewrite → critique cycle and checks the
  output is byte-identical to a mock inline run with the same seed, apart from the timing fields.
- **The inline path stays** for runs where both models fit one host.

### B2. A pre-assigned domain and frame per slot

*Amended 2026-10-16 by R&D's rulings on the Publisher's design questions.*

**Domains:**
- `role-set plan` assigns a **domain** by seed, with no model call. It goes to every slot that carries material or
  a passage: kinds A, C and D, every E type with material, and the C and D apply slots. Kind B takes its domains
  from the packs (B3).
- **No two slots in a lesson share a domain.** Ordinary slots use NAICS 2022 subsectors (3-digit).
- **The source is a public taxonomy, not a model:** the US Census NAICS 2022 titles (registry
  `census-naics-2022`). The source file is pinned by sha256 and URL, with titles verbatim.
- **ESCALATE slots draw only from mapped codes:**
  - medical: 621–623;
  - legal: 5411;
  - money: 52 and 5412;
  - safety: 23, 2211, 325, 481, 482, 5413 and 9221.

  A mapped code may also appear in a non-ESCALATE slot. Whether a slot is ESCALATE is set by the plan, not by its
  domain.
- **Each receipt records** the slot's NAICS code and title.

**Frames:**
- **A frame shapes the framing only;** the layout stays (framing, `Material:`, material, `Statement:`), as the
  student meets it at evaluation.
- **Frames go to** C, D, verdict E, and the C and D apply slots. Kind A has no frame.
- **The four frames,** each checked structurally (sentence count, final punctuation, one keyword), never by taste:
  - `ask`: one sentence, not a question;
  - `question`: ends in "?";
  - `situation_then_ask`: two or more sentences, the first setting the scene;
  - `line_question`: asks which line decides. It may not cite a line number, or share a 4-gram with the material,
    so it can't point at the answer.
- **Rotation:** within a lesson, frame counts differ by at most 1. Across the batch, each frame stays within ±10% of
  its share.
- **The framing still passes the existing gates** (`framing_repeats`, the opener share). A frame fixes structure,
  not wording.
- **The frame instruction lines are prompt text,** recorded under B9 provenance.

### B3. Solve-first kind B

- **Today:** the writer writes the puzzle and its constraint model (`fields["model"]`), and `check_puzzle` solves
  and checks it. The 8 structures in `plan.PUZZLE_STRUCTURES` already rotate (each at most once a lesson).
- **New:**
  - a generator per structure builds the `Model` in code from the slot's seed (entities, attributes, rules, the
    question), and `solve` confirms a unique answer, or the intended underdetermined set;
  - **the writer gets the locked model and renders the prose and the trace only;**
  - `check_text` then checks the prose states exactly the model's facts and order, as it does today;
  - a draft whose stated facts differ from the locked model is refused (`PUZZLE`).
- **Structures with no generator yet keep today's path,** marked in the receipt. The build reports how many of the 8
  are solve-first. The target is all 8. At least the 5 Argon named must be done before the pilot: order and
  interval, resource allocation, dependency DAG, set cover, parity and grid. Map them onto the existing structures,
  or add them as new ones.

### B4. Cumulative exclusion state across batches

- A state file, `exclusion-state.json`, holding:
  - every accepted row's prompt shingles, opener and framing line, skeleton, B structure, domain and frame;
  - the ids of the batches it includes;
  - a sha256 over its contents.
- **Every write and critique wave loads it.** `check_against` and `reply_opening_reused` run against the rows of
  all earlier batches plus this run's (today: this run's rows only), and the writer's `avoid` list is seeded from
  it.
- **It's updated only at acceptance, under the lock.** The batch's final state is committed with its rows.
- **Apply plans** check against the whole regenerated training set (the existing `--training` path), never the
  frozen provider set.

### B5. Freeze checks inline, per batch

- At `_finish`, after `check_batch`, run the aspire-si freeze checks on the batch's rows:
  - `no_role.build()`;
  - `no_role.composition()` (within ±1 item of the target);
  - `quiz.variant_checked_spans()` (0 unspent);
  - for apply items, `apply_rules.make_twin()` and `set_rule()`.
- They're imported from the pinned aspire-si checkout, as the stuck rule is (`stuck_repo` and `stuck_commit`), with
  their sha recorded in the pins.
- **A failure halts the batch** (andon). It's reported to R&D and the Publisher and isn't re-rolled.

### B6. Pins, provenance and partition on every record

**Each receipt adds:**
- `partition` (`production` or `trial:j1-wave1`);
- the writer's and critic's `family`, `repo`, `revision`, GGUF file and sha256;
- the llama.cpp commit and `llama-server` sha256;
- the CUDA machine line: driver, compat loaded or not, runtime, card and `COLAB_RELEASE_TAG` or the pod id;
- the wave and the drafts file's sha256.

**`writers.json` records each writer's licence (revised 2026-10-17):**
- each entry names `family`, `licence` and its `registry_id`;
- the guard refuses an entry only when the registry marks training on that writer's outputs `barred`, citing the
  clause. A licence that is silent on outputs, such as Apache-2.0 or MIT, is allowed.
- *Superseded:* the 2026-10-16 version required a quoted proof clause for every entry and removed the Apache-only
  entries (Qwen3-235B, qwen3:8b, gemma4:31b, granite4.1:30b) as "not proven". They're eligible again.

**Llama-server pinning:**
- the wave script hashes the GGUF and the binary before launch and passes them in;
- the guard compares them to `writers.json` and refuses on drift. This replaces `require_ollama_digest` on this
  path.

**A new guard refuses a critic whose `family` equals the writer's.**

### B7. Exemplars and other provider text in prompts

- **Today:** `run_slot` shows up to 3 exemplars from other lessons, loaded from the aspire-si training files at a
  commit. That's the frozen set: Kimi and Grok rows. **They must not reach a writer prompt.**
- **New:**
  - the exemplar loader accepts only rows whose receipts name a writer that `writers.json` allows, with partition
    `production`;
  - **batch 1 runs with no exemplars;**
  - later batches may use earlier regenerated batches' rows;
  - the guard refuses an exemplar file without receipts.
- Anything else the inventory finds is fixed the same way: provider text that reaches a prompt or a row is removed,
  replaced from an allowed source, or rewritten by the maintainer.

### B9. Provenance on every text-bearing source

- **Every human-language constant, template, pack, catalogue entry and role-pack file** that reaches a prompt or a
  row gets a `provenance` record: the writer's family (maintainer, a named model, Claude, or a code
  derivation) and the PR that added it. That covers render.py's TEMPLATES and CLAUSES, recipes.py's PACKS, the
  prompts.py constants, trait_steps, critic.py, and the pack's lessons and amendments. The record sits beside the
  text, or in a manifest keyed by name and hash.
- **`role-set check` refuses** any such source with no provenance record, or whose writer's use there is barred by a
  clause: Grok or Argon text that would enter a training row (the xAI distillation and Google ML clauses), and Kimi
  text only if it came through the Kimi app. Text that reaches only a prompt is allowed. Claude-written text is allowed
  anywhere, target fields included (ruled 2026-10-17; the earlier deny list barred Kimi outright and anything "not
  proven").
- **Seat commits carry a `Seat:` trailer** (for example `Seat: Grok`), so authorship can be read from git, not
  inferred from PR tags.
- *Source: the role-set inventory agent's debrief, 2026-10-16.*

### B8. Tests and coverage

- **A unit test for each item above,** including the refusals: a same-family critic, a writer whose training use is barred, a
  pin drift between waves, an exemplar without receipts, a frame mismatch, and a locked-model mismatch.
- **The mock three-wave equivalence test** (B1).
- **Coverage:** measure role-set's current coverage first and ratchet the floor to it (the coverage-bar rule). New
  code is covered.
- **The Atlas map** is regenerated in the same PR if `atlas check` goes red.

## 4. Provenance fixes (from the inventory)

See [PROVENANCE.md](PROVENANCE.md) for the sources. The build fixes these:

| Source | Writer | Fix |
|---|---|---|
| Kind-B clue templates (`generate/render.py` TEMPLATES, CLAUSES), 31 of 48 | Grok | Rewrite the 31 Grok-written ones (they enter training rows: xAI's distillation clause). The 17 Claude-written ones stay as inputs |
| Puzzle packs (`generate/recipes.py` PACKS: pans, machines, trains, beds, clinics) | Grok | Replace (they enter rows) |
| T10 cell table and tiered deletion (`generate/t10_variety.py`, `t10_*.json`; role-set #53, #54) | Grok | Keep: generator logic is code (revised 2026-10-17); only text that enters rows is replaced |
| T10 if-shape axis (role-set #55) | Argon | Code: allowed (revised 2026-10-17). Already rewritten; it stays as it is |
| aspire-si gates 1.7.3 and det_run NF1–NF3 (#144, #145), pinned by role-set | Argon | Code: allowed (revised 2026-10-17). Already rewritten; it stays as it is |
| Exemplars (finished Kimi and Grok rows in the writer prompt) | Kimi, Grok | Prompt text, not training rows. B7 keeps regenerated rows only, for variety; batch 1 runs without exemplars |
| Lessons, house rules, trait steps, flaw definitions, critic prompts | Claude | Keep (prompts and inputs are allowed) |
| Real-source excerpts from studio repos | mostly Claude | Keep, as inputs or targets (ruled 2026-10-17) |
| Claude fix rounds in batch files | Claude | Moot: the rows are regenerated |
| Writer-claimed twin and order flags (`assemble._apply_fields`) | the writer | Compute them in code (B5) |

**The guards that already exist** narrow B2–B5:
- B2 exists for kind B only (pack and cell per seed);
- B3's solve-first generator exists for T10–T12 (`generate/build.py`, six question families) but **isn't wired**
  into `role-set write`;
- B4 exists only for apply plans;
- B5's checks live in aspire-si `docs/runs/stage1-train` on `verifier-distill-prereg-draft` and run at freeze only.

## 5. Variety floors (unchanged, now cumulative)

- The floors in role-set's gates and the aspire-si freeze stay as they are, measured per batch **and** against the
  cumulative state (B4).
- **R&D's variety review** reads every kind (A–E and the puzzles) side by side with an earlier batch, as in
  aspire-si #155 and #162.

## 6. Fingerprint controls

- **The generator-identity probe** (template item 5) runs on the J1 pool: can a cheap classifier tell the writers
  apart? It's a report, not a gate.
- **The others,** shuffled labels and partial input, belong to Stage 1's training readout, unchanged.

## 7. Splits

Unchanged: the frozen exam and the sealed set are untouched. **The sealed set is never opened by this build.**

## 8. The recipe card

The regenerated set's card gives:
- the writers and critics, with family, revision and GGUF sha256;
- each model's licence and registry id (PLAN.md §1);
- the pack hash, the plan seed, the NAICS table hash, the code hash, and the counts per kind, trait and writer.

## 9. Before the first counted batch

1. **The mock three-wave cycle is green in CI,** and R&D has reviewed the PR.
2. **The Colab pilot** (PLAN.md §7): 20 slots across kinds A–E plus apply twins. Its rows are `trial:j1-wave1`.
   **The maintainer is told first.**
3. **The critic's own controls:** its gates stay advisory where they were (`trait_gate`, `answer_gate`,
   `flaw_gate`) until critic-control passes for the new critic models. The Lightning and Glimmer critics are new, so
   critic-control runs on them in the pilot.
4. **Argon reviews this spec and the harness diff** before any counted batch.

## 10. Verdicts and what changes

- **A floor miss, a freeze-check failure or a failed control stops the batch.** The fix is a dated amendment, with
  a rerun on fresh seeds. The missed run stays in the record.
- **Dropped slots are reported,** never padded.
