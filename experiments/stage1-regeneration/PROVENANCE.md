# Stage 1 provenance inventory (step 0)

**Date:** 2026-10-16. **By:** R&D, with two read-only Sonnet inventories (role-set at `d4e4d18`; aspire-si
records and PRs). Authorship comes from PR bodies, seat tags and commit trailers. Every commit is under the
maintainer's account, so the account name is no evidence. "Co-Authored-By: Claude" trailers and "Generated with
Claude Code" footers mark Claude sessions (the Publisher, R&D, the Dataset Specialist, ASPIRE). Seat tags name Grok,
Argon and Kimi. In aspire-si #96, #97 and #106, "Seat A" is Grok.

**Sealed set:** no sealed task file or sitting was opened. One slip: an exploratory search's glob matched the
freeze *record* `docs/runs/2026-10-10-stage1-sealed-freeze.md` (a document about the freeze, not the tasks) and
printed one line of it. It was disclosed to the Publisher the same day.

## What reaches the training rows

| Source | Writer | Notes |
|---|---|---|
| Pilot (T04, 40 rows) | Kimi | #81, #83 |
| Batch 2 (T01, T14, T16) | **Kimi, then Grok's fix rounds** | An exception to "Grok wrote 2–8" |
| Batches 3–8 | Grok | #84, #87, #92, #106, #112, #155 |
| Fix rounds in the batch files | Claude (Dataset Specialist) | #93 to #140. Rows touched not counted |
| 210 apply items | Argon, plus one Claude fix | #162. STaR rows are built from them |
| Kind-B clue templates (`generate/render.py` TEMPLATES, CLAUSES) | 31 of 48 by Grok (#49); 17 by Claude (#48) | Enter the B user turn |
| Puzzle packs (`generate/recipes.py` PACKS) | Grok (#49); 3 packs by Claude (#48) | Names and values enter the puzzle text |
| T12 packs and templates, setting and question lines | Claude (#48, #50) | Enter rows |
| **Real-source excerpts** (103 of 810 rows; repos roll, site-theme, polyglot-mcp, style-dataset-lab, rig-bridge, repo-knowledge) | **Mostly Claude.** Claude co-authored most of those repos' commits (for example roll 29 of 32, style-dataset-lab 173 of 181). repo-knowledge has 6 Cursor Agent commits | The plan called these "human-written". They aren't. The licences are fine; the text is mostly Claude's |
| Row format lines (`assemble.py`) | Deterministic code (Claude-written) | Labels such as "Material:" and "Statement:" |

## What reaches the writer's prompt only

| Source | Writer |
|---|---|
| The role pack: lessons T01–T18, kinds, amendments 1–5 (aspire-si lesson drafts L1–L3, the trait and qualities lessons) | Claude, written to the maintainer's method and ratified by him. Amendment 4 quotes two Grok phrases |
| `prompts.py` house rules, B model rule and worked example, structure notes, slot brief, warm-up | Claude |
| `trait_steps.py`, `critic.py` FLAW_DEFINITIONS | Claude |
| **Exemplars:** up to 3 finished rows from other lessons | **Kimi and Grok rows**, with Claude fixes. No span gate exists against them (`exemplars.spans_of` has no caller) |
| Writer-drafted material (`material_messages`) | The run's own writer: clean with a proven writer |

## What reaches the critic only

`critic.py` CRITIC_SYSTEM, TRAIT_SYSTEM and PAIR_DISTINCTIONS: Claude.

## Evaluation

| Set | Writer |
|---|---|
| DEV: review-10 and pilot-20 | Claude (hand-written claims and keys over studio-repo text) |
| Interview, 12 questions | Claude (the Publisher's draft) |
| Sealed, 130 items | Claude, by inference: the records say "written, keyed, and checked by the R&D session"; no record names a provider |

## Guards that exist (for BUILD-SPEC)

- **Domain and frame per slot:** only for kind B (pack and cell per seed). A, C, D and E get a rotated content kind;
  openings are refused after the fact.
- **Solve-first puzzles:** built (`generate/build.py`, `recipes.py`, six question families) for T10–T12 only, and
  **not wired** into `role-set write`. Other lessons' B items are writer-freehand, checked afterwards.
- **Cross-batch exclusion:** only for apply plans (`--training`). Training batches start empty.
- **Freeze checks:** in aspire-si `docs/runs/stage1-train` (`no_role.py`, `freeze.py`, `apply_rules.py`) on branch
  `verifier-distill-prereg-draft`. They run at freeze, not in the generator.
  `assemble._apply_fields` takes the twin and order flags as writer claims, not computed values.

## Not attributed

- Per-row shares inside the mixed batch files (Grok, Kimi, Claude).
- How far team-review input from other seats shaped the lessons.
- The harvested pool's exact lines (`pool.jsonl` isn't committed).
- The Cursor Agent commits' model.

## Code written by Argon, Grok or Kimi (for the code question, U4)

Read from branch names, seat tags and commit trailers (2026-10-16). "Implemented by Claude from Argon's review"
means Argon's findings were design input and Claude wrote the code. That's not Argon's code.

| Repo | PRs | Writer | What |
|---|---|---|---|
| aspire-si | #144 `argon-nf1-nf2-fallback`, #145 `argon-nf3-gates` | **Argon** (no Claude trailer) | det_run's SDPA table and fallback; gates 1.7.3 (leakage reads the statement field; a STaR row refuses think tags). role-set pins gates 1.7.3 (role-set #68) |
| aspire-si | #133–#138 (`argon-a`…`argon-f`) | Claude, from Argon's review findings | det_run, training seed, batched path, NO-ROLE, apply, gates 1.7.2 |
| aspire-si | #162 `argon/apply-items` | Argon | The 210 apply items (data, already being regenerated) |
| role-set | #55 `argon/t10-if-shape` | **Argon** (6 commits, no Claude trailer) | T10's if-shape claim axis, capacity weights |
| role-set | #53 `grok/t10-variety`, #54 `grok/t10-trait-tested`, #49 | **Grok** (with one Claude commit in #53) | T10 cell table and tiered deletion; the clue templates and puzzle packs (also text that enters rows) |
| role-set | #35 | Grok | The README and release surface (not pipeline code) |
| interlock | about 30 `grok/*` PRs (#8–#124) and about 20 `kimi/*` PRs (#9–#38) | **Grok and Kimi** | The harness, supervisor, E1–E5 measurement, router v0, release prep. Inference and measurement tooling, not the training pipeline |

## What the terms make of it (R&D's re-read, 2026-10-16)

- **Anthropic.** The Help Center article "Can I use my Outputs to train an AI model?" (support.claude.com article
  12326764, dated 2026-03-16) is live and reads as Argon quoted it. "You can use Claude's Outputs to train models
  that don't compete with Anthropic's own models. This includes creating specialized classifiers and tools". The
  examples given are sentiment analysis, content categorization, summarization, information extraction, semantic
  search and anomaly detection. Prohibited: general-purpose chatbots, "Models designed for open-ended text
  generation", and "Using Outputs as training targets for models". It also says "you own the Outputs".
  - The Commercial Terms D.4 (effective 2025-06-17) bar "to train competing AI models".
  - The 2026 Usage Policy bars "Use outputs to train an AI model … without prior authorization", and this article
    is Anthropic's published statement of what is authorized.
  - **So, if the student verifier is a specialized tool, Claude-written text is proven for:**
    - pipeline code;
    - writer and critic prompts, including the lessons;
    - evaluation sets (owned outputs, a lesser use than training);
    - the *inputs* of training rows.
  - **It is never proven as a training target.**
- **Google.** The consumer ToS's "using AI-generated content from our services to develop machine learning models or
  related AI technology" has no competition qualifier. Antigravity's terms incorporate it. Argon-written pipeline
  code is barred on the literal text.
- **xAI.** The AUP bars distilling Outputs outright. Its "develop … machine learning models or any products or
  services that compete" turns on whether "that compete" reaches "machine learning models". **Not proven.**
- **Kimi** (consumer app): "non-commercial, personal research, and study" only. **Not proven** for studio tooling.
