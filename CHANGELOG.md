# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
Versions have five segments, `MAJOR.MINOR.PATCH.MICRO.NANO`. The first three
follow [Semantic Versioning](https://semver.org/) for the `rnd` tool. MICRO marks a
structural library change (a new experiment, catalogue or instrument family), and
NANO an ordinary library update (entries filed or revised, results added).
`python -m rnd bump` writes each section; `1.0.0` reads as `1.0.0.0.0`.

## [Unreleased]

## [1.1.23.1.0] - 2026-10-19

- New experiment cuda-python-5090-rung and rig-fact entry 2026-10-20-cuda-python-on-5090: six CUDA Python libraries (cuda.core, CuPy, numba-cuda, cuda.compute, nvmath-python, cuTile) run a checked kernel on the RTX 5090 at compute capability 12.0, pinned, once NumPy is held below 2.5; the cuTile-on-sm_120 question is answered
- Updated `2026-10-07-cutile-on-sm120`: Does cuTile run on compute capability 12.0 (RTX 5090)?
- Added `2026-10-20-cuda-python-on-5090`: CUDA Python libraries on the RTX 5090 (smoke rung)
- Added experiment `cuda-python-5090-rung`

## [1.1.23.0.0] - 2026-10-19

- rnd raw verify --json: counts (manifests, public git files, declared blobs checked), the sorted list of public git files re-hashed, what was skipped, and problems as {rule, where} with stable rule codes and redacted places (never a hash, the matched text or a content-private name). The shape rnd-data's own verifier defines, so the two can be compared file for file until rnd imports it (tooling plan R2, R4)

## [1.1.22.0.0] - 2026-10-19

- rnd raw verify --public-only, Argon's rnd-data protection round 1 (F1-F4): CALL_CHECKPOINT and the other content markers, packaged in mcptoolshop_rnd, under runs/; a git file over 256 KB under runs/; the private tag anywhere except the four pages that explain it; a home-directory path in any OS's form anywhere (the identity scan's Windows-only patterns missed four WSL /home/<account> paths on 2026-10-19); drive paths in manifests, store.json, docs and workflows; a public manifest's copies naming the companion, a non-public hash or a private entry's path. Problems print file and line, never the match. MACHINE_PATH_RE's share name is tightened so escaped backslashes in code aren't taken for one

## [1.1.21.0.0] - 2026-10-19

- rnd raw runs without an rnd library when the store is named (--public or $RND_DATA), as in rnd-data's CI; the companion's default is then beside the store. Found by running rnd-data's verify.sh against the 1.1.20.0.0 pin from a clean install, where it stopped with NO_LIBRARY

## [1.1.20.0.0] - 2026-10-19

- rnd raw verify --public-only: what a public clone can check (rnd-data's CI): git copies re-hashed, the blob store and the companion skipped and counted, plus a file under runs/ no manifest names or carrying the private tag, a private-looking name anywhere, and a machine path in a manifest
- rnd raw relicense: reapplies a rules file's licences to written manifests, changing only the licence field; receipts.json gains the licence rules from the Director's ruling (data CC BY 4.0, scripts MIT, llama.cpp MIT) and the Publisher's verifier-gold rule

## [1.1.19.0.1] - 2026-10-19

- The site's header logo and favicon become the rnd badge's centre mark (brand repo logos/rnd, polished in brand#107, sha256 335c2947); the accent moves from teal to the badge's navy blue

## [1.1.19.0.0] - 2026-10-19

- rnd raw ingest copies blobs by default; --link (hard-link) only for a read-only snapshot; every blob is read-only (the Publisher's P3 follow-up: an append to a linked live file would change the blob)

## [1.1.18.0.0] - 2026-10-19

- rnd raw ingest/private/verify: rnd-data (public) and rnd-data-private (only the named exceptions), files over 256 KB once by content in a blob store, --update for a changed source
- docs/raw-data-rules/receipts.json: deny by default for content, co-owned with the Publisher; a public manifest never carries a private file's hash
- rnd check and the index read the companion; the exact private match skips files under 16 bytes; scripts/hooks/pre-push runs rnd check
- stage1-regeneration: all 74 runs carry raw_manifest_id; docs/: the approved scale plan, its review history, the Argon system instructions
- Updated experiment `stage1-regeneration`

## [1.1.17.0.0] - 2026-10-19

- rnd.db: six record tables (experiments, runs, budgets, files, manifest_files, copies) rebuilt from experiment records, data-pack manifests and rnd-data's manifests; the schema's hash joins the index fingerprint
- rnd runs record --from outcome.json (a run object as written, or an older file mapped), rnd runs, rnd ledger, rnd where
- budgets: excludes (runs outside the cap) and reconciled (overlapping runs counted at their measured total)
- stage1-regeneration: its experiment record, 74 runs backfilled from the Publisher's records; the ledger matches theirs (196.93 of 300 units, $8.05 of $22)
- Added experiment `stage1-regeneration`

## [1.1.16.0.0] - 2026-10-19

- rnd check: the layout rules: a 256 KB file and 2 MB experiment limit under experiments/ with a no-growth baseline (docs/layout.json), the private-file rule (tag, names, rnd-data's private manifest), and experiment.json (rnd-experiment/v1)
- rnd new-experiment and rnd layout baseline; a gitignored staging/ for data-pack builds
- run_vocabulary.json: the run outcomes, cost bases, units, venues and id rule shared with the Publisher's outcome.json
- handbook: Where data lives

## [1.1.15.2.16] - 2026-10-19

- critic-signal PLAN-ROUND4.md: the plan after phase 4, passed by Argon (round 4b); SYNTHESIS.md's last recommendation corrected (the coarse gate's errors are at the none boundary)
- Updated experiment `stage1-regeneration`

## [1.1.15.2.15] - 2026-10-19

- critic-signal SYNTHESIS.md: what phases 0–4 and the parked step 1 have shown, the cost, the method lessons, and the options for T10
- Added experiment `stage1-regeneration`

## [1.1.15.2.14] - 2026-10-19

- handbook: briefing an outside model (template), with the critic-signal AI Studio brief as the worked example
- Added experiment `stage1-regeneration`

## [1.1.15.2.13] - 2026-10-19

- weekly watch 2026-10-19: NeMo Relay 0.10.1/0.10.2 notes (primary-read), Claude Code idle compaction vs the harness pin
- Updated `nemo-relay`: nemo-relay — tracing what an agent actually did (NVIDIA NeMo Relay)
- Updated experiment `agent-ab-harness`

## [1.1.15.2.12] - 2026-10-19

- offrig instrument: measured pod choice for conversions
- Updated `offrig`: offrig — big models on rented RunPod GPUs

## [1.1.15.2.11] - 2026-10-19

- offrig instrument: operating facts read from its source
- Updated `offrig`: offrig — big models on rented RunPod GPUs

## [1.1.15.2.10] - 2026-10-19

- card-values: Nemotron-3.5-Super-VL-120B critic card (critic-signal §10)
- Updated experiment `local-builders`

## [1.1.15.2.9] - 2026-10-19

- critic-signal §10: the larger-critic test, pre-registered
- Updated experiment `stage1-regeneration`

## [1.1.15.2.8] - 2026-10-19

- critic-signal phase 4: the confirmation test's result
- Updated experiment `stage1-regeneration`

## [1.1.15.2.7] - 2026-10-19

- critic-signal confirmation: gold set, items sha and hand-check drops frozen before the critic run
- Added experiment `stage1-regeneration`

## [1.1.15.2.6] - 2026-10-19

- newsletter issue 14: testing the tester (critic-signal)
- Updated experiment `charts`
- Added experiment `stage1-regeneration`

## [1.1.15.2.5] - 2026-10-19

- critic-signal phases 2-3 results and the confirmation design (§9, Argon PASS r3b)
- Updated experiment `stage1-regeneration`

## [1.1.15.2.4] - 2026-10-18

- critic-signal phases 0 and 1: the critic's per-check record and a blind gold check of 51 accepted rows
- Updated experiment `stage1-regeneration`

## [1.1.15.2.3] - 2026-10-18

- Stage 1 part 2 design: a critic that can tell writers apart (passed by Argon, two rounds)
- Added experiment `stage1-regeneration`

## [1.1.15.2.2] - 2026-10-18

- the golden path: deadline stops with measured margins, no implicit Hub token, the token-clean check, Colab can't see a dead kernel

## [1.1.15.2.1] - 2026-10-18

- the golden path and issue 13 after Argon's consult: what a cap stop returns, the vault fallback, image drift, OOM, stand-in checklist, template fields

## [1.1.15.2.0] - 2026-10-18

- newsletter issue 13: Claude + Colab, the path we'd use again; the window data through W-A
- Updated experiment `colab-golden-path`

## [1.1.15.1.1] - 2026-10-18

- the golden path: gate floors on the gate's own metric, the converter's environment as part of the pin, mocks with real failure modes

## [1.1.15.1.0] - 2026-10-18

- the Claude + Colab golden path: the rented-GPU-windows handbook page and the pilot's raw window data
- Added experiment `colab-golden-path`

## [1.1.15.0.4] - 2026-10-17

- newsletter issue 10 and a brief: what the terms let you do with AI output

## [1.1.15.0.3] - 2026-10-17

- The dataminer counts Gemma 4's thinking: its template closes <|channel>thought with <channel|>, now one of the channel ends (counted only with tokens after it, as before). Window 12f's Gemma calls recount from 17 nulls to 80.9% thinking.

## [1.1.15.0.2] - 2026-10-17

- newsletter issue 11: picking a writer model on rented GPUs (critic test, thinking cost, the window method), with Qwen3.8's per-call counts and a chart
- Updated experiment `charts`
- Updated experiment `stage1-regeneration`

## [1.1.15.0.1] - 2026-10-17

- The dataminer counts thinking on every reply: a reply cut off at the length limit with no answer counts all its output as thinking, and a harmony-style template's thinking ends at <|eom|> or <|end|> (Muse-Glimmer). Each call records thinking_tokens_source (usage, timings, marker, length, none). Before this, both cases were null and summaries summed them as 0. New: python -m mcptoolshop_rnd.localbuilders.recount re-measures a generations file into a new one.

## [1.1.15.0.0] - 2026-10-17

- J2 pre-run round 5: skip pre-creating venv when install names {venv}, enforce Python 3.12 interpreter check, and refuse empty or non-{venv} install commands.

## [1.1.14.0.0] - 2026-10-17

- J2 pre-run round 4: companion_tests (`file` key), per-task venv setup (`{venv}`/`{bank}` placeholders, `suite_cmd` scorer contract, `venv_python_version`), strict history chown, and 0600 proxy files.

## [1.1.13.0.0] - 2026-10-17

- packaging: mcptoolshop_rnd.localbuilders (and setup_vm.sh) now ship in the wheel; a test checks every subpackage is included

## [1.1.12.0.2] - 2026-10-17

- critic-control known-answer v2: two faulty keys replaced (D-04, D-11), found by both critics in window 7b
- Updated experiment `stage1-regeneration`

## [1.1.12.0.1] - 2026-10-17

- critic-control's bar, set before the first result
- Updated experiment `stage1-regeneration`

## [1.1.12.0.0] - 2026-10-17

- mcptoolshop_rnd.localbuilders: verify installed Aider 0.86.1 version gate and synthetic assistant strings against real CoderPrompts and EditBlockPrompts in preflight and runner; record aider_version and synthetic_strings_verified on receipts
- mcptoolshop_rnd.localbuilders: create per-task chat-history.md and input-history owned by builder (0600) in an unlistable directory (0711) before launching Aider, and allow only those two outside-workspace writes in probe
- mcptoolshop_rnd.localbuilders: set CUDA_VISIBLE_DEVICES='' in builder_env for Aider --auto-test runs and scoring pytest so builder tests see no GPU

## [1.1.11.0.0] - 2026-10-17

- mcptoolshop_rnd.localbuilders: J2 logging proxy, task runner, clean git-archive workspace, JUnit XML and twin scorer, VM containment and probe, and fit/template/thinking-split preflight (amendments C, D, E: NB1, NB2, F1-F7, F9, F10, F13, D1, D2, D-F1 to D-F3)
- tests: unittest suite and 2-task fixture bank for mcptoolshop_rnd.localbuilders

## [1.1.10.2.11] - 2026-10-17

- local-builders amendment E: R&D's disposition of Argon's review of amendment D (D-F1 to D-F4)
- Updated experiment `generated-content-terms`
- Updated experiment `local-builders`
- Updated experiment `stage1-regeneration`

## [1.1.10.2.10] - 2026-10-17

- The maintainer's ruling: Claude text may be training targets for the non-competing verifier (Anthropic's list bars competitive training)
- Updated experiment `generated-content-terms`
- Updated experiment `local-builders`
- Updated experiment `stage1-regeneration`

- The licence-rule cleanup (2026-10-17): a use is barred only by a quoted clause. Registry verdicts `proven`/`not_proven` become `allowed`/`barred`, and the test now requires a clause for every bar, not for every grant. BUILD-SPEC, PLAN, the generated-content README and DESIGN drop the proof rule and the strict tier; Argon's 2026-10-16 answers are marked superseded; amendment D3 drops the authorship filter.


## [1.1.10.2.9] - 2026-10-17

- local-builders: amendment D (card values, the fold_system and reattach_thinking transforms, the bank's 2026-09-04 floor and Claude-only authorship) and card-values.json
- Updated experiment `local-builders`

## [1.1.10.2.8] - 2026-10-17

- local-builders: amendment C, the disposition of Argon's J2 design review (F1-F14); registry adds Gemma's prohibited-use policy
- Updated experiment `local-builders`

## [1.1.10.2.7] - 2026-10-17

- generated-content rule split: strict for what shapes weights or scores, code read plainly (Antigravity may build studio code, AI tooling included)
- Updated experiment `generated-content-terms`
- Updated experiment `local-builders`
- Updated experiment `stage1-regeneration`

## [1.1.10.2.6] - 2026-10-17

- local-builders: amendment B (J2 on the pinned CUDA 13.4 stack, licences first, generation records, open units) and the Argon design-review brief
- Updated experiment `local-builders`

## [1.1.10.2.5] - 2026-10-16

- stage1-regeneration: DATAMINER-USES.md, using the generation records in role-set (uncertain-first key check, host agreement, and four later uses)
- handbook: the dataminer's generation record as provenance evidence in every experiment template

## [1.1.10.2.4] - 2026-10-16

- stage1-regeneration: the critic's known-answer set v1 (40 Claude-written keyed items for critic-control)
- Added experiment `stage1-regeneration`

## [1.1.10.2.3] - 2026-10-16

- stage1-regeneration: DATASET-RELEASE.md, a design note for releases with verifiable provenance through npm-launcher, OIDC trusted publishing and the maintainer's approval
- handbook: 'Licences first' (section 0) in the dataset-builds, model-comparisons and A/B templates
- The generated-content rule reworded (the maintainer, 2026-10-16): allowed unless a contract or licence restricts it, with the search documented; silence-based verdicts revised (Apache/MIT outputs, Kimi via Ollama Cloud, Google non-AI output, R1-Distill-Qwen-32B)
- generated-content-terms: Argon's answer on pipeline code (barred on the literal consumer text); registry adds the Gemini API and Google Cloud terms
- Added experiment `generated-content-terms`

## [1.1.10.2.2] - 2026-10-16

- stage1-regeneration: BUILD-SPEC B2 amended with R&D's domain, ESCALATE-mapping and frame rulings
- Updated experiment `stage1-regeneration`

## [1.1.10.2.1] - 2026-10-16

- licences: the Census NAICS 2022 entry for role-set's domain table; PDF policies read; archive links kept

## [1.1.10.2.0] - 2026-10-16

- licences/: the registry of every licence and terms page the studio relies on, with clauses, verdicts per use and snapshot hashes
- Updated experiment `generated-content-terms`

## [1.1.10.1.3] - 2026-10-16

- stage1-regeneration: decisions recorded; regenerate all rows under the proof rule
- Updated experiment `stage1-regeneration`

## [1.1.10.1.2] - 2026-10-16

- stage1-regeneration: the Kimi seat ran through Ollama Cloud, not the Kimi app
- Updated experiment `stage1-regeneration`

## [1.1.10.1.1] - 2026-10-16

- stage1-regeneration: provenance inventory, role-set build spec, Anthropic Help Center re-read
- Updated experiment `stage1-regeneration`

## [1.1.10.1.0] - 2026-10-16

- stage1-regeneration: plan, revised after Argon's consult; every licence clause re-read
- Added experiment `stage1-regeneration`

## [1.1.10.0.21] - 2026-10-16

- local-builders amendment A: J1's control is role-set itself; Antigravity Section 6 note
- Updated experiment `generated-content-terms`
- Updated experiment `local-builders`

## [1.1.10.0.20] - 2026-10-16

- experiment generated-content-terms: provider terms for generated content, checked under the proof rule
- Added experiment `generated-content-terms`

## [1.1.10.0.19] - 2026-10-16

- stage1-role-eval note: the freeze (e7b69464) and the composition rerun (0 of 909 cells differ; ratio 0.656)
- Updated experiment `stage1-role-eval`

## [1.1.10.0.18] - 2026-10-16

- instrument colab: second probe session (timeout measured, in-VM unassign unproven, T4 high-mem, H100 unavailable); cloud-cu134: Colab T4 and L4
- Updated `colab`: Colab Pro+ — prepaid cloud GPUs for experiments
- Updated experiment `cloud-cu134`

## [1.1.10.0.17] - 2026-10-16

- experiment local-builders: Wave 1 design filed with R&D's review changes
- Added experiment `local-builders`

## [1.1.10.0.16] - 2026-10-16

- experiment colab-bottlenecks: Argon's consult, checked against the CLI source; instrument colab rules updated
- Updated `colab`: Colab Pro+ — prepaid cloud GPUs for experiments
- Added experiment `colab-bottlenecks`

## [1.1.10.0.15] - 2026-10-16

- scripts/colab: the Colab rate probe and runner (probe.py, rates.sh), linked from instrument colab
- Updated `colab`: Colab Pro+ — prepaid cloud GPUs for experiments

## [1.1.10.0.14] - 2026-10-16

- instrument colab: installed (0.7.4), measured unit rates, rules of use
- Updated `colab`: Colab Pro+ — prepaid cloud GPUs for experiments

## [1.1.10.0.13] - 2026-10-16

- handbook: the model-comparisons design template

## [1.1.10.0.12] - 2026-10-16

- ollama-cuda-backend: fix the flaky diag breach test (record writes serialised in the fixture); the harness's concurrent-append defect noted
- Updated experiment `ollama-cuda-backend`

## [1.1.10.0.11] - 2026-10-16

- stage1-role-eval amendment E: no twin for cannot_tell items in T01, T03, T04 (as D for T14)
- Updated experiment `stage1-role-eval`

## [1.1.10.0.10] - 2026-10-16

- instrument: colab (Colab Pro+ units approved for experiments)
- Added `colab`: Colab Pro+ — prepaid cloud GPUs for experiments

## [1.1.10.0.9] - 2026-10-16

- stage1-role-eval note: amendment B disclosure corrected (5.0 / 6.4), per-seed hold (aspire-si#150)
- Updated experiment `stage1-role-eval`

## [1.1.10.0.8] - 2026-10-15

- stage1-role-eval: note on the NO-ROLE token gap (0.624) and exposure, pre-freeze
- Updated experiment `stage1-role-eval`

## [1.1.10.0.7] - 2026-10-15

- stage1-role-eval: note on NO-ROLE's closed-form E quiz (Argon's finding 5a)
- Updated experiment `stage1-role-eval`

## [1.1.10.0.6] - 2026-10-15

- stage1-role-eval amendment D: wording fix (A_0 from all of DEV's decided items; T14 cannot_tell items need no twin)
- Updated experiment `stage1-role-eval`

## [1.1.10.0.5] - 2026-10-15

- stage1-role-eval: amendment D, the keep rule's lesson clause for T14 and T16 (the maintainer's decision after Argon's review)
- Updated experiment `stage1-role-eval`

## [1.1.10.0.4] - 2026-10-15

- dataset-desk: the design record filed (design, Argon passes 2-3 and the follow-up); the code moved to mcp-tool-shop-org/dataset-desk v0.1.0; instrument file
- Added `dataset-desk`: dataset-desk — review a visual dataset before it trains or tests anything
- Added experiment `dataset-desk`

## [1.1.10.0.3] - 2026-10-15

- embeddinggemma-2: the multimodal design, revision 3, approved (desk-checked queries, Path A, the acceptance tests)
- Added experiment `dataset-desk`
- Updated experiment `embeddinggemma-2`

## [1.1.10.0.2] - 2026-10-15

- stage1-role-eval: the maintainer's amendments of 2026-10-15, recorded. A: STaR matched across the arms (each
  arm keeps its own right apply answers, downsampled to equal counts per lesson and kind, with identical steps, a
  near-duplicate filter and a cap of 8). B: the panel stops a round on a drop of more than 2.0 points that is also
  significant (p <= 0.05, paired McNemar). C: the panel keeps the card's sampling settings, not greedy decoding.

## [1.1.10.0.1] - 2026-10-15

- stage1-role-eval: R&D's ruling raises the closed-form `distractor_margin` from 0.15 to 0.20. The batch 5 and 6
  re-measure (24 items, at aspire-si 0c181e4) put the minimum gap at 0.214 and the median at 0.437. The gap is
  re-measured at the batch 8 freeze.

## [1.1.10.0.0] - 2026-10-15

- Fixed `rnd abmine` (`parse_log`): a forced FlashAttention setting is now its own resolution. With
  `--flash-attn off` (or `on`), llama.cpp logs `flash_attn = disabled` (or `enabled`) and prints no
  `resolve_fused_ops` line, so 1.1.9.0.0 left the resolution empty for FA-off arms.
- Updated experiment `ollama-cuda-backend` with the diagnosis of the CUDA 13.4 Update 2 backend:
  - the frozen harness v6 (byte for byte), its diffs, the run record, and the analysis;
  - the result: the difference from stock is cuBLAS, and the build is ELIGIBLE;
  - the record of v5's aborted run.
- Added `tests/test_diag_harness.py`. It runs the diagnosis harness's tests in the suite, including an offline dry run
  of the harness's `main()` through all eight arms to the verdict.
- Site: the brief "Can Ollama run the studio's CUDA 13.4 backend?", an update to newsletter issue 9, and the
  ab_dataminer handbook page.
- Tests: abmine stays at 100% coverage. The package floor stays at 90.

## [1.1.9.0.1] - 2026-10-15

### Fixed

- **The release workflow installs `hypothesis` before `verify.sh`,** with the same pin as ci.yml (6.131.9). Without it, the property tests failed to import, Verify failed, and nothing reached PyPI from v1.1.4.0.0 to v1.1.9.0.0. PyPI's latest stayed 1.1.3.0.0.
- **`release.yml` gains a `workflow_dispatch` trigger** with a required `tag` input, so the fixed workflow on main can publish an existing released tag (v1.1.9.0.0) without a new version.
  - The tag reaches shell steps only through env, never interpolated into a script.
  - It must match vMAJOR.MINOR.PATCH.MICRO.NANO, and have a published, non-draft GitHub release.
  - The version-equals-tag check reads it.
  - Trusted publishing is unchanged: the same file name and `pypi` environment.
- This is a workflow-only change, so this nano version isn't itself released.

## [1.1.9.0.0] - 2026-10-15

### Added

- **`rnd abmine analyze`** (ab_dataminer), the analysis half of the A/B template for runs that compare backends, builds or settings of one model. It reads a JSON-lines record of greedy generations with top-K logprobs and reports, with no GPU and no server:
  - per pair of arms and prompt: the fork, Δz = (ℓR(t1) − ℓR(t2)) − (ℓT(t1) − ℓT(t2)) at every matched-prefix step (censored and flagged when a reference candidate is outside the test arm's top-K), the step-0 Δz, the mean, p95 and max |Δz|, a drift slope, pre-fork spikes, fork detail and the chosen-token MAE;
  - a pairwise matrix and, with `--reference`, tie-breaks at the other arms' forks and each arm's MAE against the reference;
  - from `OLLAMA_DEBUG` logs: the backend DLLs loaded, the device, the FlashAttention resolution, KV types and graph reuse.
- `abmine.probe` (a library function for GPU grants, not a command): prefill-replay of a generation in raw mode with the model's exact template, ending inside the assistant turn. It must reproduce the recorded prompt token count and step-0 candidates before any later position is trusted. The qwen3 rendering is pinned to its template's sha256.
- 39 tests at 100% line coverage of the module, including the 2026-10-15 cu1343 sandbox record as a fixture. It reproduces the outside reviewer's hand figures: Δz 0.770 and 1.345 at the forks, and a step-14 runner-up shift of 1.294 (the hand figure, 1.30, was rounded).
- The handbook page "Mining an A/B run", linked from the A/B template, and the command reference.

### Library

- `experiments/ollama-cuda-backend/abmine-cu1343.txt` and `.json`: the analysis of the cu1343 sandbox record. The two builds disagree at step 0 on every prompt (Δz −0.163, 0.117 and −0.373), so the shift starts at prefill and isn't accumulated decode drift. The prompt that matched token for token still shows |Δz| up to 1.67.
- `diag_test-v4-draft.py` and `diag_test-v3-to-v4.diff`: the N-arm diagnosis harness for the outside review, not run. Its arms are S0, S1, S2, S0_cb1343, S0_nofa, S2_nofa, a reference arm and S0′. It has 15 prompts with task checks, and the pre-registered activation rule written into its verdict block. It refuses to run until the reference arm is chosen and its hash is frozen

## [1.1.8.3.23] - 2026-10-15

- The Ollama CUDA backend's sandbox test failed criterion 2, so nothing is activated. The 13.4 Update 2 build loaded (the log names its path, compute 12.0) and kept pace with stock (mean rate ratio 1.194 against stock A). But its outputs diverged from stock on 2 of 3 prompts, at token 15 and token 6, where stock's top two were 0.70 and 0.81 apart, not the near-tie the rule allows. Stock matched itself exactly. `experiments/ollama-cuda-backend/sandbox-result-cu1343.md` holds the verdict, with the run's record minus one log line's PATH values. Newsletter issue 9 gains the update, and both build records now explain the `0x0` affinity reading (an elevated process a non-elevated shell can't open)

## [1.1.8.3.22] - 2026-10-15

- Newsletter issue 9, "The backend that changed under us": an Ollama update replaced the studio's CUDA 13.4 backend, and the backend was rebuilt from Ollama 0.40.4's llama.cpp pin. It covers the CPU rules set after an uncapped job (efficiency-core affinity, below-normal priority, every thread pool capped), three rounds of outside review of the sandbox test, CUDA 13.4's version numbering, and a new weekly check
- `experiments/ollama-cuda-backend/`: the build records. 0.35.1 on CUDA 13.4.1; 0.40.4 on 13.4.1 (343.8 s); 0.40.4 to the studio standard on 13.4 Update 2 (nvcc V13.4.92, sm_120a SASS only, 374.0 s, ggml-cuda.dll 0ebc0e61…); the capped launcher; the sandbox plan; and the sandbox test v3 with its diff from v2. Nothing is activated, and the sandbox test waits for review and a GPU grant

## [1.1.8.3.21] - 2026-10-15

- EmbeddingGemma 2: Argon's resource review of offrig's embed-serve, and its disposition. Argon held it for seven changes, and all were applied in offrig: every thread pool capped before torch loads, below-normal priority, request bounds and HTTP hardening. The capped rerun's figures: 201 chunks in 162.6 s on 6 E-cores at about 20% of the machine, peaking at 2.8 GiB. The brief records that Argon read its first version
- EmbeddingGemma 2, multimodal: the Director approved design revision 2

## [1.1.8.3.20] - 2026-10-15

- EmbeddingGemma 2, multimodal: design revision 2 after Argon's round 1 (pool = generation outputs, byte-deduplicated, near-duplicates masked; strict key; T2 document prefix; per-project upper-bound rule; G256 out of the rule), approved by Argon as written in round 2. Two round 1 facts corrected: 2,104 image files in the query projects, not about 2,900, and no record names a lineage. Waits on the Director's approval
- EmbeddingGemma 2: the offrig adoption plan (models, server, re-index, rollback); the Publisher placed the server in offrig as tools/embed-serve, release 1.2.0

## [1.1.8.3.19] - 2026-10-15

- EmbeddingGemma 2: the round 2 regrade (all 100 queries, grader brief v2) passed its fresh blind audit on all four bars (quadratic kappa 0.897, binary kappa 0.869, raw disagreement 8.7%, two-step 0%). The seven queries with no relevant chunk are locked before any score, as amendment 4 requires; 93 queries are scored. The pre-registered score: adopt EmbeddingGemma 2 at 768 dimensions. Stage 1 passed (dense nDCG@10 +0.112 over nomic-embed-text, one-sided lower bound +0.065; prose +0.041, code +0.174; hybrid +0.065, lower bound +0.029). Stage 2 failed (256 dimensions cost 0.043, lower bound -0.062), so the cut isn't adopted. Results in `experiments/embeddinggemma-2/results.md`, ids and numbers only

## [1.1.8.3.18] - 2026-10-15

- Atlas slice AP (testing-os #179): the security consult for the by-hand, different-family review before merge, with the code from 4904cf90 inline and seven questions on what an attacker who controls one root can reach
- EmbeddingGemma 2 grader brief v2: the format example's chunk id is now 99999, which no chunk has (1234 was a real chunk, though in no pool)

## [1.1.8.3.17] - 2026-10-15

- EmbeddingGemma 2: Argon adjudicated the 63 audit disagreements (56 resolved to the Sonnet grade, 7 to the auditor's). Grader brief version 2 carries the adjudicated boundary rules, with no example ids, so nothing leaks into the regrade. The grading tool gains a round 2 that never overwrites round 1, and the fresh 16-query audit is drawn before any regrading. The round 3 consult asks Argon to approve the brief and grade the fresh audit

## [1.1.8.3.16] - 2026-10-15

- EmbeddingGemma 2: the round 1 grading audit failed two of its four bars (binary kappa 0.747, raw disagreement 12.6%); every disagreement has the auditor one step higher. Design amendment 4 records the result and Argon's ruling to drop queries with no relevant chunk. The adjudication consult (round 2) is filed, and the whole pool is regraded under a revised brief, as amendment 2 requires. No score was computed

## [1.1.8.3.15] - 2026-10-15

- EmbeddingGemma 2 text benchmark: all 100 queries graded (2,470 chunks, one fresh Sonnet grader each, 100 of 100 complete); the merged key is frozen; four queries have no relevant chunk in the corpus. Scores stay sealed. The audit consult to Argon (blind regrade of 16 queries, and a scoring rule for queries with no relevant chunk) is filed, with the grading record, the run records and the grading harness's completeness check

## [1.1.8.3.14] - 2026-10-15

- Advocate fix-up 5 amended after Argon's read: the preflight reads the card while the model is loaded, the card-clear wait compares against the run's starting baseline, the shutdown path never waits or raises twice, and the preflight keeps its prompt check

## [1.1.8.3.13] - 2026-10-15

- Advocate fix-up 5: a preflight that can finish. A one-token call ends with done_reason "length" (measured on a CPU-only Ollama 0.40.4), so the preflight accepts that; keep_alive 60s re-sent; the preflight counts the card baseline; the run waits for the card to clear between models

## [1.1.8.3.12] - 2026-10-15

- Advocate fix-up 4: a short keep_alive (60s) on every live and preflight call, so a hard-killed pilot can't pin the critic in VRAM for 30 minutes (Argon's second read)

## [1.1.8.3.11] - 2026-10-15

- Advocate fix-up 4 amended after Argon's read: num_predict caps (512 writer, 256 critic); truncation checked before and after each call; the record flushed before the critic loads, with every attempt's prose and failing checks; Argon's family-fallback inference corrected (the writer is per slot, no fallback)

## [1.1.8.3.10] - 2026-10-15

- Advocate: the live pilot stopped at the 24 GiB cap when the critic loaded (the pilot sent no num_ctx, so the 16K default doubled the writers and pushed gemma4:31b over; R&D sized the grant on weights and missed it); fix-up 4 brief filed: a sized context, truncation detection, an incremental record, a measuring preflight, the granite checked_by

## [1.1.8.3.9] - 2026-10-15

- Advocate: the writer swap passed; the grant posted (publisher-5090-advocate-pilot-2026-10-15); the pilot run brief filed for Seat C, pointing at the grant note for the run line, heartbeat, run directory, caps and the grant hand-back

## [1.1.8.3.8] - 2026-10-15

- EmbeddingGemma 2 multimodal design drafted (the Director: don't stop at text): description-to-image and image-to-description search over style-dataset-lab's art against SigLIP2 (ai-eyes), keys by construction from 385 human-described approved images among ~2,900; audio deferred for lack of a labelled clip library; Argon consult filed

## [1.1.8.3.7] - 2026-10-15

- Advocate: Argon round 8 settled, fix-up 3 passed to the pilot grant; the Llama 3.1 licence clause 1.b.i verified by R&D from Meta's llama-models repo; the Director chose to swap writer 2 before the pilot; granite3.3:8b (Apache-2.0, GGUF, pulled) chosen; the swap brief filed

## [1.1.8.3.6] - 2026-10-15

- Advocate fix-up 3 reviewed by R&D: the guards, think/format/fence handling, Note labels, category wording and one table all landed; three items for Argon (the Llama 3.1 licence condition for the training batch, verified from source; no positive pin test; two rules moved from the table into the record); round 8 consult filed

## [1.1.8.3.5] - 2026-10-15

- EmbeddingGemma 2: Argon's harness review and intent review answered (amendment 3: Stage 2 reads the one-sided bound; stop rules, key completeness and key hash, intents in the pool, tokenizer pin; the titled diagnostic dropped; 23 intents revised and frozen); grading.py and the grader brief; the counted embedding run started

## [1.1.8.3.4] - 2026-10-14

- Handbook: the relevance-grading template (drafted by Argon at the Director's request, adapted by R&D): the 0/1/2 scale with query-form rules and boundary cases, blindness, locked intents, reason-before-grade, weighted and binary kappa gates, freezing and publication
- EmbeddingGemma 2: the harness (corpus frozen with offrig's own chunker, 11,525 chunks; 100 queries; embed, rank, pool, score, validate); validation (tokens under 2,048, bf16 fails parity so float32, B at 0.395 of A behind HTTP); dry run on 512 chunks; amendments 1 and 2; Argon harness consult round 3; rubric disposition

## [1.1.8.3.3] - 2026-10-14

- EmbeddingGemma 2 design v3: Argon round 2 found it ready; three line edits taken (B256 and the code-prefix diagnostic in the blind pool; float slice and re-normalize before int8; a tighter hybrid guard). Awaiting the Director's approval
- Advocate: Argon round 7 settled; the third fix-up brief filed (model guards and pins, the critic's think, format and fence handling, Note labels, relay acts as categories, one shared table, the read packet); R&D verdict on role-set #56

## [1.1.8.3.2] - 2026-10-14

- Advocate fix-up 2 reviewed by R&D: the live pilot skips the writers.json and digest guards (no cloud-tag refusal), procedures name Note lines the records no longer mark, the relay acts list hands over the slots' exact strings, the critic's think flag is implicit, the critic's table is the old abstract one; Argon consult round 7 filed with code inline; role-set #59 reviewed (pass, one handbook sentence)

## [1.1.8.3.1] - 2026-10-14

- EmbeddingGemma 2 design v2 after Argon round 1 (100 queries, two-stage rule, blinded pooled keys, prefix and title parity, 2,048-token pre-check, bf16 gate; R&D adds the hybrid guard and int8 scoring from offrig's code); round 2 consult filed

## [1.1.8.3.0] - 2026-10-14

- EmbeddingGemma 2: installed from Hugging Face (CPU env, hash-checked), entry filed, A/B benchmark design against offrig's nomic-embed-text, Argon consult round 1; Ollama 0.40.4 can't serve it on Windows (MLX-only builds)
- Advocate fix-up 2 amended: the critic's live call passes think=False explicitly and the test asserts it for gemma4:31b (the Publisher's Ollama 0.40.4 smoke); the grant request records the Ollama version
- Added `embeddinggemma-2`: EmbeddingGemma 2 — a multimodal embedder for studio retrieval

## [1.1.8.2.26] - 2026-10-14

- Advocate fix-up 2 brief: Argon's read folded in (check-line numbers allowed; out-of-scope relay points phrased as the notes the drop rule names)

## [1.1.8.2.25] - 2026-10-14

- Argon round 6 answered: hold for a second fix-up; fix-up 2 brief filed (relay messages rendered, the live path returns text, a prompt-completeness gate, the flag sheet dropped, the 0.2.0 follow-ups in CI's idle minutes); R&D verdict on role-set #56

## [1.1.8.2.24] - 2026-10-14

- Advocate fix-up reviewed by R&D: the relay messages never reach the writer or critic, no prompt-sufficiency test, the headline ignores tripwires, the B critic gets A's rules, three slot contradictions, the fake probe still in; Argon consult round 6 filed with the code inline; the grant held

## [1.1.8.2.23] - 2026-10-14

- Advocate fix-up brief: Argon's read folded in (unit-suffixed numbers; threshold-crossing figure plants flip the hidden flags; the turn 3 negative allocation fixed)

## [1.1.8.2.22] - 2026-10-14

- Argon round 5 answered: hold the grant; phase 1 fix-up brief filed (ten defects, the C1 ruling, Q1–Q5 answers, the pilot planner and mock runner); turn 3 amended; R&D verdict on role-set #56

## [1.1.8.2.21] - 2026-10-14

- Advocate phase 1 reviewed by R&D: six required findings, one turn-3 conflict, five questions; Argon consult round 5 filed with the code inline; the pilot grant held
- Newsletter issue 8: the role-set scorecard reads 37 of 50, as measured after the translations (role-set #58)

## [1.1.8.2.20] - 2026-10-14

- role-set v0.2.0 released: outcome recorded on the treatment brief; issue 8 and the T10 brief link the release

## [1.1.8.2.19] - 2026-10-14

- role-set 0.2.0 treatment reviewed: pass with one required change (the Advocate's approval state on three surfaces); five code follow-ups filed

## [1.1.8.2.18] - 2026-10-14

- Argon round 4 answered: green light; the slot 3 ledger tag and the 9/10 critic rule folded into the pilot brief; disposition filed

## [1.1.8.2.17] - 2026-10-14

- Argon consult round 4 filed: the pilot brief after the three fixes, inline, with the 5% reconciliation as the question

## [1.1.8.2.16] - 2026-10-14

- Advocate pilot brief: Argon's three alignment fixes applied (registered negative classes only, 26 texts, the fourth row, the critic's two counts); review and disposition filed

## [1.1.8.2.15] - 2026-10-14

- Advocate: Seat C turn 2 (pack fix-up, phase 1) and turn 3 (the free pilot, 16 slots) briefs filed; the pilot brief goes to Argon before Seat C

## [1.1.8.2.14] - 2026-10-14

- issue 8 and the T10 brief: the floors are checked in seconds inside a CI job of about seven minutes, not 'four minutes'

## [1.1.8.2.13] - 2026-10-14

- T10 Phase 1 (if_shape) landed in role-set #55: brief 3 outcome, the T10 brief page, newsletter issue 8; the seat brief for role-set's full treatment and 0.2.0

## [1.1.8.2.12] - 2026-10-14

- Advocate lean brief: one verdict vocabulary (the table's hold/cannot_tell/pilot_first/proceed; supported retired), and paid model API (always hold) told apart from a paid offrig pod run (green-light conditions). Argon's resolution of the seat's Phase 0 question.

## [1.1.8.2.11] - 2026-10-14

- Advocate lean brief: Argon's five structural fixes (pilot kinds match traits; checks scoped to kind A, trace on positives, section numbers exempt; cannot_tell ordered in the table, verdict before the alternative; relay points tagged in or out of scope).

## [1.1.8.2.10] - 2026-10-14

- Advocate: lean batch-1 brief (Director-approved after Argon's shape check); the hardened design kept as brief-v1-hardened.md, its machinery deferred with triggers.

## [1.1.8.2.9] - 2026-10-14

- advocate-dataset: section 1's three sentences carry the round-2 and round-3 fixes (the verifier, the precedence table, lexical anchors, the relational probe, immaterial figures, the writer split, the natural exam)

## [1.1.8.2.8] - 2026-10-14

- advocate-dataset: Argon round 3 folded in (the ceiling, quota collisions, the scope matrix, the precedence order, the negation rule, the 16-slot pilot); ready for the Director's section 1

## [1.1.8.2.7] - 2026-10-14

- advocate-dataset: Argon consult round 3 (the revised brief checked for the six changes, quota-skeleton consistency, the role scope table, the pilot's 16 items)

## [1.1.8.2.6] - 2026-10-14

- advocate-dataset: Argon round 2 folded in (prose-to-block verifier, counterfactual negatives with parity, affine ceiling, two rule tiers, precedence table, recombinatorial harvesting, natural exam, critic legs); disposition record

## [1.1.8.2.5] - 2026-10-14

- advocate-dataset: Argon consult round 2 (adversarial pass on the folded design, brief inline), on the Director's ask for several passes before a seat

## [1.1.8.2.4] - 2026-10-14

- T10 brief 3 amendment 4: if_shape stop; capacity weights split by stratum; fresh locked 101-120

## [1.1.8.2.3] - 2026-10-14

- advocate-dataset: Argon round 1 folded in (fact ledger, canonical block, independent negatives, isomorphic synthesis, local writers), R&D's three additions, the disposition record

## [1.1.8.2.2] - 2026-10-14

- Advocate brief: the studio shape (section 0a): the brief's fixed order (asks, headline, figures, tripwires, recommendation), the studio record kinds, tripwires as a constructed and keyable list (a relayed approval included), relay in the studio's directions, role titles only. The Publisher, on the Director's authority to align the build.

## [1.1.8.2.1] - 2026-10-14

- advocate-dataset brief revised to the Director's definition and sequenced (batch 1 first)

## [1.1.8.2.0] - 2026-10-14

- advocate-dataset: role-set's second role (the Advocate) brief for the Grok seat; handbook template Dataset builds

## [1.1.8.1.14] - 2026-10-14

- T10 brief 3 amendment 3: if_shape goes ahead; one-if shape is consequent polarity + touches; guard on touches

## [1.1.8.1.13] - 2026-10-14

- T10 variety landed in role-set #49: outcome in briefs 2 and 3; public brief page

## [1.1.8.1.12] - 2026-10-14

- interlock-relay stage 1 raw records archived (receipts, traces, call tables, driver records), needles redacted
- Added experiment `interlock-relay`

## [1.1.8.1.11] - 2026-10-14

- NeMo Relay brief measured; newsletter issue 7: the interlock-relay experiment end to end

## [1.1.8.1.10] - 2026-10-14

- interlock-relay v3.2 build round: Argon's build applied, reviewed, approved; closed by the Director
- Updated experiment `interlock-relay`

## [1.1.8.1.9] - 2026-10-14

- interlock-relay stage 1 result: frozen verdict, diagnosis, Argon consult, amendment v3.2 (debug-only)
- Updated experiment `interlock-relay`

## [1.1.8.1.8] - 2026-10-14

- interlock-relay stage 1: post-Argon preflight corrections recorded, with the CPU-quiet check
- Updated experiment `interlock-relay`

## [1.1.8.1.7] - 2026-10-14

- interlock-relay stage 1: Argon round 2 folded in, the grant cap, the preflight corrected on the live rig; ready for the grant
- Updated experiment `interlock-relay`

## [1.1.8.1.6] - 2026-10-14

- interlock-relay stage 1: Argon round 1 folded in, analysis re-frozen (cbaed82), round 2 brief
- Updated experiment `interlock-relay`

## [1.1.8.1.5] - 2026-10-14

- interlock-relay stage 1: the harness analysis frozen (43643bc) and the Argon review brief
- Added experiment `interlock-relay`

## [1.1.8.1.4] - 2026-10-14

- interlock-relay: Argon round 2 folded in, stage 0 complete; the stage 1 plan
- Updated experiment `interlock-relay`

## [1.1.8.1.3] - 2026-10-14

- interlock-relay stage 0: Argon round 1 folded in (runs 3-5, three further defects fixed), round 1 and round 2 code-review briefs; T10 brief 3 amendments 1 and 2
- Updated experiment `interlock-relay`

## [1.1.8.1.2] - 2026-10-14

- interlock-relay stage 0 on fakes: H4a and H4b hold; amendments A1-A7. T10 brief 3 (multi-pack variety)
- Updated experiment `interlock-relay`

## [1.1.8.1.1] - 2026-10-14

- newsletter issue 6: Atlas and testing-os, the library's collector, interlock 0.1.0, and what a T10 claim can test

## [1.1.8.1.0] - 2026-10-14

- t10-variety: two seat briefs and an Argon consult on what a claim item can test (role-set #53, #54); interlock-relay audit briefs, rounds 1-4; interlock-relay design marked approved and on hold
- Updated experiment `interlock-relay`

## [1.1.8.0.31] - 2026-10-13

- interlock-relay design v3.1 (Director-approved after four Argon audits)
- Added experiment `interlock-relay`
- Added experiment `local-agent-relay`

## [1.1.8.0.30] - 2026-10-13

- local-agent-relay design v0 (prototype, Director-approved); diagnose-then-fix page marked prototype
- Added experiment `local-agent-relay`

## [1.1.8.0.29] - 2026-10-13

- handbook: diagnose-then-fix study template (Director-approved)
- Updated `2026-10-13-atlas-testing-os-rnd-buildup`: Atlas, testing-os, housekeeping and rnd — the build-up program
- Updated `2026-10-13-docker-sandboxes-on-the-rig-from-signup-to-a-pinned-pilot-wo`: Docker Sandboxes on the rig: from signup to a pinned pilot workspace
- Updated `2026-10-13-multi-repository-atlas-research-grounding-for-the-build-up`: Multi-repository Atlas: research grounding for the build-up
- Added `2026-10-13-nemo-relay-first-trial-in-the-sandbox`: NeMo Relay's first trial: it traces Claude Code in the sandbox at no measurable cost, and sends nothing of its own
- Updated `2026-10-13-nvidia-nemo-relay-tracing-agent-harnesses-claude-code-includ`: NVIDIA NeMo Relay: tracing agent harnesses, Claude Code included
- Added `agent-ab-harness`: agent-ab-harness — paired A/B runs of a coding agent in a sandbox
- Updated `atlas`: atlas — a repository's map, checked in CI and served to agents
- Updated `nemo-relay`: nemo-relay — tracing what an agent actually did (NVIDIA NeMo Relay)
- Updated experiment `atlas-mcp-utility`
- Added experiment `local-agent-relay`

## [1.1.8.0.28] - 2026-10-13

- nemo-relay first trial in the sandbox; instrument installed
- Updated `2026-10-13-atlas-testing-os-rnd-buildup`: Atlas, testing-os, housekeeping and rnd — the build-up program
- Updated `2026-10-13-docker-sandboxes-on-the-rig-from-signup-to-a-pinned-pilot-wo`: Docker Sandboxes on the rig: from signup to a pinned pilot workspace
- Updated `2026-10-13-multi-repository-atlas-research-grounding-for-the-build-up`: Multi-repository Atlas: research grounding for the build-up
- Added `2026-10-13-nemo-relay-first-trial-in-the-sandbox`: NeMo Relay's first trial: it traces Claude Code in the sandbox at no measurable cost, and sends nothing of its own
- Updated `2026-10-13-nvidia-nemo-relay-tracing-agent-harnesses-claude-code-includ`: NVIDIA NeMo Relay: tracing agent harnesses, Claude Code included
- Added `agent-ab-harness`: agent-ab-harness — paired A/B runs of a coding agent in a sandbox
- Updated `atlas`: atlas — a repository's map, checked in CI and served to agents
- Updated `nemo-relay`: nemo-relay — tracing what an agent actually did (NVIDIA NeMo Relay)
- Updated experiment `atlas-mcp-utility`

## [1.1.8.0.27] - 2026-10-13

- agent-ab-harness: the harness becomes a reusable instrument; A/B experiment design template in the handbook
- Updated `2026-10-13-atlas-testing-os-rnd-buildup`: Atlas, testing-os, housekeeping and rnd — the build-up program
- Updated `2026-10-13-docker-sandboxes-on-the-rig-from-signup-to-a-pinned-pilot-wo`: Docker Sandboxes on the rig: from signup to a pinned pilot workspace
- Updated `2026-10-13-multi-repository-atlas-research-grounding-for-the-build-up`: Multi-repository Atlas: research grounding for the build-up
- Updated `2026-10-13-nvidia-nemo-relay-tracing-agent-harnesses-claude-code-includ`: NVIDIA NeMo Relay: tracing agent harnesses, Claude Code included
- Added `agent-ab-harness`: agent-ab-harness — paired A/B runs of a coding agent in a sandbox
- Updated `atlas`: atlas — a repository's map, checked in CI and served to agents
- Updated experiment `atlas-mcp-utility`

## [1.1.8.0.26] - 2026-10-13

- atlas-mcp-utility harness fixes: token totals, task wall time, write detection, process cleanup, grading
- Updated `2026-10-13-atlas-testing-os-rnd-buildup`: Atlas, testing-os, housekeeping and rnd — the build-up program
- Added `2026-10-13-claude-code-read-deny-rules-do-not-stop-a-grep-walk`: Claude Code: a Read deny rule doesn't stop a Grep walk over the denied tree
- Added `2026-10-13-claude-code-starts-a-turn-before-mcp-servers-connect`: Claude Code starts a print-mode turn before its MCP servers connect, on Anthropic's endpoint
- Updated `2026-10-13-docker-sandboxes-on-the-rig-from-signup-to-a-pinned-pilot-wo`: Docker Sandboxes on the rig: from signup to a pinned pilot workspace
- Updated `2026-10-13-multi-repository-atlas-research-grounding-for-the-build-up`: Multi-repository Atlas: research grounding for the build-up
- Added `2026-10-13-nemotron-lightning-needs-its-context-set-for-claude-code`: nemotron-3.5-lightning under Claude Code needs a 131k context; Ollama's default 32k cripples it
- Updated `2026-10-13-nvidia-nemo-relay-tracing-agent-harnesses-claude-code-includ`: NVIDIA NeMo Relay: tracing agent harnesses, Claude Code included
- Updated `atlas`: atlas — a repository's map, checked in CI and served to agents
- Updated experiment `atlas-mcp-utility`

## [1.1.8.0.25] - 2026-10-13

- atlas-mcp-utility withdrawn as badly designed; write-ups removed, harness kept and marked unvalidated
- Updated `2026-10-13-atlas-testing-os-rnd-buildup`: Atlas, testing-os, housekeeping and rnd — the build-up program
- Updated `2026-10-13-docker-sandboxes-on-the-rig-from-signup-to-a-pinned-pilot-wo`: Docker Sandboxes on the rig: from signup to a pinned pilot workspace
- Updated `2026-10-13-multi-repository-atlas-research-grounding-for-the-build-up`: Multi-repository Atlas: research grounding for the build-up
- Updated `2026-10-13-nvidia-nemo-relay-tracing-agent-harnesses-claude-code-includ`: NVIDIA NeMo Relay: tracing agent harnesses, Claude Code included
- Updated `atlas`: atlas — a repository's map, checked in CI and served to agents
- Updated experiment `atlas-mcp-utility`

## [1.1.8.0.24] - 2026-10-13

- atlas-mcp-utility amendment 13 rewritten: arm B is told to use Atlas; speed primary
- Updated experiment `atlas-mcp-utility`

## [1.1.8.0.23] - 2026-10-13

- atlas-mcp-utility amendment 13: arm B's prompt names the Atlas tools
- Updated experiment `atlas-mcp-utility`

## [1.1.8.0.22] - 2026-10-13

- atlas-mcp-utility amendment 12: arm B holds its task until Atlas connects
- Updated experiment `atlas-mcp-utility`

## [1.1.8.0.21] - 2026-10-13

- atlas-mcp-utility: arm B correction, Atlas pending only on the plan route
- Updated experiment `atlas-mcp-utility`

## [1.1.8.0.20] - 2026-10-13

- atlas-mcp-utility shakedown results: Haiku 12/12, nemotron-131k 11/12; arm B never had Atlas in its task turn
- Updated experiment `atlas-mcp-utility`

## [1.1.8.0.19] - 2026-10-13

- atlas-mcp-utility amendment 11: Haiku partners the local model, nemotron at a pinned 131k context, refused out-of-set calls stop nothing
- Updated experiment `atlas-mcp-utility`

## [1.1.8.0.18] - 2026-10-13

- atlas-mcp-utility amendment 10: a local route first, refused calls stop nothing, recorded streams replay
- Updated experiment `atlas-mcp-utility`

## [1.1.8.0.17] - 2026-10-13

- atlas-mcp-utility amendment 9: read-only shell in the checkout is part of the measured surface; the detector stops only writes, background commands and substitution; temp files cleared between attempts
- Updated experiment `atlas-mcp-utility`

## [1.1.8.0.16] - 2026-10-13

- atlas-mcp-utility: the probe and pilot summaries carry each run's start (effort, permission mode, on the plan, Atlas at init)
- Updated experiment `atlas-mcp-utility`

## [1.1.8.0.15] - 2026-10-13

- atlas-mcp-utility amendment 8: the CLI gets the sandbox proxy; the placeholder sign-in file is installed fresh before every attempt
- Updated experiment `atlas-mcp-utility`

## [1.1.8.0.14] - 2026-10-13

- atlas-mcp-utility amendment 8: the shakedown (Sonnet and local legs) and containment by permission (harness as root, the CLI as an unprivileged user)
- Updated experiment `atlas-mcp-utility`

## [1.1.8.0.13] - 2026-10-13

- atlas-mcp-utility amendment 7 (medium effort; the runs move into the local sandbox atlas-pilot; permission-mode and key-source checks); Docker Sandboxes entry and brief
- Added `2026-10-13-docker-sandboxes-on-the-rig-from-signup-to-a-pinned-pilot-wo`: Docker Sandboxes on the rig: from signup to a pinned pilot workspace
- Updated `docker-sandboxes`: docker-sandboxes — isolated machines for agent experiments (Docker Sandboxes, sbx)
- Updated experiment `atlas-mcp-utility`

## [1.1.8.0.12] - 2026-10-13

- docker-sandboxes: the Director's ruling, no paid model API; models local or RunPod only
- Updated `docker-sandboxes`: docker-sandboxes — isolated machines for agent experiments (Docker Sandboxes, sbx)

## [1.1.8.0.11] - 2026-10-13

- docker-sandboxes: which model a sandboxed agent uses (rig and plan for Claude; RunPod or local for open models)
- Updated `docker-sandboxes`: docker-sandboxes — isolated machines for agent experiments (Docker Sandboxes, sbx)

## [1.1.8.0.10] - 2026-10-13

- docker-sandboxes: what the console showed at signup (API-key claude kit, $0.28/hr medium, 1-hour stop)
- Updated `docker-sandboxes`: docker-sandboxes — isolated machines for agent experiments (Docker Sandboxes, sbx)

## [1.1.8.0.9] - 2026-10-13

- Docker on the weekly watch (blog, Sandboxes, Desktop, Engine, Model Runner); instrument docker-sandboxes (planned)
- Added `docker-sandboxes`: docker-sandboxes — isolated machines for agent experiments (Docker Sandboxes, sbx)

## [1.1.8.0.8] - 2026-10-13

- corrected from the #107 live check: the sampler window caught the old runner's teardown; the card was idle at the call
- Updated `2026-10-12-test-fakes-hide-the-platform`: Test fakes that hide the platform, a recurring defect class
- Updated `2026-10-13-e5-fill-card`: E5 — how much context each local model holds on the 5090

## [1.1.8.0.7] - 2026-10-13

- consult verdicts: Grok Build and Kimi K3 on Atlas slice AN, with R&D's rulings
- Added experiment `atlas-mcp-utility`

## [1.1.8.0.6] - 2026-10-13

- consult brief: the outside-family security review of Atlas slice AN (testing-os #169)
- Added experiment `atlas-mcp-utility`

## [1.1.8.0.5] - 2026-10-13

- multi-repo Atlas entry: slices AN-AQ as ruled; probe entry: interlock #109
- Updated `2026-10-13-multi-repository-atlas-research-grounding-for-the-build-up`: Multi-repository Atlas: research grounding for the build-up
- Updated `2026-10-13-the-probe-was-the-contention-a-process-walk-inside-the-measu`: The probe was the contention: a process walk inside the measured window

## [1.1.8.0.4] - 2026-10-13

- entry: instrument_perturbs_measurement, the interlock slot probe's process walk
- Added `2026-10-13-the-probe-was-the-contention-a-process-walk-inside-the-measu`: The probe was the contention: a process walk inside the measured window

## [1.1.8.0.3] - 2026-10-13

- test-fakes entry: the second #107 instance (a fake with no unload lag)
- Updated `2026-10-12-test-fakes-hide-the-platform`: Test fakes that hide the platform, a recurring defect class

## [1.1.8.0.2] - 2026-10-13

- piano-arrangement entry: two corrections from the receipts; promoted to vocology-knowledge wave 14
- Updated `2026-10-08-llm-piano-arrangement-from-a-generated-brief`: Piano arrangements by an LLM from a brief generated from the score

## [1.1.8.0.1] - 2026-10-13

- entry: test_fake_hides_platform, the E5 settle-wait instance (interlock #107 review)
- Updated `2026-10-12-test-fakes-hide-the-platform`: Test fakes that hide the platform, a recurring defect class

## [1.1.8.0.0] - 2026-10-13

- rnd watch: latest is the newest stable release (a newer pre-release is shown apart); release notes and commit messages kept in the JSON (first watch run, 2026-10-13)
- rnd search --exact: terms split on spaces and keep inner punctuation, so Run:ai and NeMo-Relay match whole

## [1.1.7.1.5] - 2026-10-13

- site: the watch, a weekly page linked from the landing page and the newsletter; first edition, week of 13 October

## [1.1.7.1.4] - 2026-10-13

- catalog: nvidia-skills synced (7 added: codonfm x4, nvidia-ontology x3), flagged by the first weekly watch
- brief and entry: PAIR 1.0.0's release notes (launch options incl. context size, Claude Code routing)
- instrument: nemo-relay, 0.10.0's local trace files, OTLP auto-export condition, permission marks
- Updated `2026-10-13-multi-repository-atlas-research-grounding-for-the-build-up`: Multi-repository Atlas: research grounding for the build-up
- Updated `2026-10-13-nvidia-pair-a-lan-inference-router-and-how-it-compares-with-`: NVIDIA PAIR: a LAN inference router, and how it compares with interlock
- Updated `nemo-relay`: nemo-relay — tracing what an agent actually did (NVIDIA NeMo Relay)
- Updated catalog `nvidia-skills`
- Updated experiment `atlas-mcp-utility`

## [1.1.7.1.3] - 2026-10-13

- atlas-mcp-utility amendment 6: Kimi K3's consult (ladder decides on cross-repo tasks; blind tasks; release-commit pins; CF09-CF13 out of rung 1's decision set)
- entry: Kimi K3's consult and R&D's rulings on the multi-repository Atlas design
- Updated `2026-10-13-multi-repository-atlas-research-grounding-for-the-build-up`: Multi-repository Atlas: research grounding for the build-up
- Updated experiment `atlas-mcp-utility`

## [1.1.7.1.2] - 2026-10-13

- entry: multi-repository Atlas, research grounding for the build-up (study-swarm, four questions)
- Added `2026-10-13-multi-repository-atlas-research-grounding-for-the-build-up`: Multi-repository Atlas: research grounding for the build-up

## [1.1.7.1.1] - 2026-10-13

- atlas-mcp-utility amendment 5: the full run becomes a repository ladder (ladder.md)
- Updated experiment `atlas-mcp-utility`

## [1.1.7.1.0] - 2026-10-13

- experiment: e5, collected from interlock (run-b at 6e8cab6, run-c at cc91aed)
- entry: E5 card complete (gemma4:31b 86016, granite4.1:30b 43008, llama3.1:8b 131072)
- newsletter issue 5: The card is full
- brief: PAIR and interlock, E5 row updated
- Updated `2026-10-13-e5-fill-card`: E5 — how much context each local model holds on the 5090
- Added experiment `e5`

## [1.1.7.0.0] - 2026-10-13

- rnd watch: what's new on the watchlist's sources since the last check (releases, commits, Hugging Face models, Atom/RSS feeds, release-notes pages)
- docs/watchlist.json: twelve sources for the weekly watch ritual

## [1.1.6.0.0] - 2026-10-13

- rnd probe: licence, latest release, gating, telemetry hits and library hits for GitHub, Hugging Face, PyPI and npm sources, from each API
- rnd search --exact: whole words in the same case, no stemming (PAIR the product, not pair)

## [1.1.5.0.6] - 2026-10-13

- brief: Where should this request run? NVIDIA PAIR and interlock
- entry: NVIDIA PAIR (LAN inference router)
- Added `2026-10-13-nvidia-pair-a-lan-inference-router-and-how-it-compares-with-`: NVIDIA PAIR: a LAN inference router, and how it compares with interlock

## [1.1.5.0.5] - 2026-10-13

- instrument: nemo-relay (planned; the Director added it to the toolset)
- brief: How do we see what an agent actually did? (NeMo Relay)
- Updated `2026-10-13-nvidia-nemo-relay-tracing-agent-harnesses-claude-code-includ`: NVIDIA NeMo Relay: tracing agent harnesses, Claude Code included
- Added `nemo-relay`: nemo-relay — tracing what an agent actually did (NVIDIA NeMo Relay)

## [1.1.5.0.4] - 2026-10-13

- entry: NVIDIA NeMo Relay (tracing agent harnesses, Claude Code included)
- atlas-mcp-utility amendments merged:
  - amendment 2: run isolation, the harness and the probes (#6);
  - the Bash escape detector (#7);
  - amendment 3: the six-question debrief and two stated conventions (#8).
- Added `2026-10-13-nvidia-nemo-relay-tracing-agent-harnesses-claude-code-includ`: NVIDIA NeMo Relay: tracing agent harnesses, Claude Code included

## [1.1.5.0.3] - 2026-10-13

- atlas-mcp-utility pre-registered (#5); the Director's go on the pilot, after the GPU grant ends

## [1.1.5.0.2] - 2026-10-13

- atlas-mcp-utility pre-registered (#5); the Director's go on the pilot only
- Updated `atlas`: atlas — a repository's map, checked in CI and served to agents
- Added experiment `atlas-mcp-utility`

## [1.1.5.0.1] - 2026-10-13

- E5 smoke 3 under the new gates; rnd collect tagged
- Updated `switchyard`: interlock (formerly switchyard) — the local AI device router (in build)

## [1.1.5.0.0] - 2026-10-13

- rnd collect: copy an experiment's trimmed records from a tool repository at pinned commits, with a byte-for-byte --check (build-up item 3)
- E4b's results now come from experiments/e4b/collect.json; rnd collect e4b --check reproduces them byte for byte
- Updated experiment `e4b`

## [1.1.4.6.60] - 2026-10-13

- charts write LF and the chart test draws into a temporary directory (a test run leaves the tree clean)
- Added `atlas`: atlas — a repository's map, checked in CI and served to agents
- Added `testing-os`: testing-os — dogfood records, findings and the swarm control plane
- Updated experiment `charts`

- Atlas: a `datapacks` part in `atlas/boundaries.yaml`, so a new datapack no longer fails `atlas check`
- New instruments: `atlas` and `testing-os` (the testing-os session, for R&D's review)

## [1.1.4.6.59] - 2026-10-13

- decision: Atlas, testing-os, housekeeping and rnd build-up program
- Added `2026-10-13-atlas-testing-os-rnd-buildup`: Atlas, testing-os, housekeeping and rnd — the build-up program

## [1.1.4.6.58] - 2026-10-13

- interlock #103 review; Atlas build-up rulings
- Updated `switchyard`: interlock (formerly switchyard) — the local AI device router (in build)

## [1.1.4.6.57] - 2026-10-13

- E5 first full run ruling
- Added `2026-10-13-e5-fill-card`: E5 — how much context each local model holds on the 5090
- Updated `switchyard`: interlock (formerly switchyard) — the local AI device router (in build)

## [1.1.4.6.56] - 2026-10-13

- E5 smoke 2 passed
- Updated `switchyard`: interlock (formerly switchyard) — the local AI device router (in build)

## [1.1.4.6.55] - 2026-10-13

- interlock #101 pass
- Updated `switchyard`: interlock (formerly switchyard) — the local AI device router (in build)

## [1.1.4.6.54] - 2026-10-13

- interlock #101 review (floor reference)
- Updated `switchyard`: interlock (formerly switchyard) — the local AI device router (in build)

## [1.1.4.6.53] - 2026-10-13

- interlock #100 pass
- Updated `switchyard`: interlock (formerly switchyard) — the local AI device router (in build)

## [1.1.4.6.52] - 2026-10-13

- E5 spill-baseline ruling
- Updated `switchyard`: interlock (formerly switchyard) — the local AI device router (in build)

## [1.1.4.6.51] - 2026-10-13

- interlock #99 pass (live-read)
- Updated `switchyard`: interlock (formerly switchyard) — the local AI device router (in build)

## [1.1.4.6.50] - 2026-10-13

- test-fakes entry: E5 instances
- Updated `2026-10-12-test-fakes-hide-the-platform`: Test fakes that hide the platform, a recurring defect class

## [1.1.4.6.49] - 2026-10-13

- interlock #99 rulings; E4b flash-attention correction
- Updated `switchyard`: interlock (formerly switchyard) — the local AI device router (in build)

## [1.1.4.6.48] - 2026-10-12

- E5 live-read audit; R&D review practice
- Updated `switchyard`: interlock (formerly switchyard) — the local AI device router (in build)

## [1.1.4.6.47] - 2026-10-12

- E5 run c diagnosis (adapter exact match)
- Updated `switchyard`: interlock (formerly switchyard) — the local AI device router (in build)

## [1.1.4.6.46] - 2026-10-12

- interlock #96 content review
- Updated `switchyard`: interlock (formerly switchyard) — the local AI device router (in build)

## [1.1.4.6.45] - 2026-10-12

- interlock #95 pass; E5 readiness
- Updated `switchyard`: interlock (formerly switchyard) — the local AI device router (in build)

## [1.1.4.6.44] - 2026-10-12

- newsletter issue 4 (E4b: three devices, no contention)
- Updated experiment `charts`
- Added experiment `e4b`

- E4b charts: the pre-registered verdict, per-triplet effects and pilot clock check, plus a post hoc view of the iGPU latencies
- Chart manifest: the E4b results are pinned, and four input hashes that had drifted from their files are refreshed

## [1.1.4.6.43] - 2026-10-12

- E4b complete: all four pairs free
- Updated `2026-10-12-e4b-block-2`: E4b — the 5090, NPU and iGPU run free together
- Updated `switchyard`: interlock (formerly switchyard) — the local AI device router (in build)

## [1.1.4.6.42] - 2026-10-12

- interlock #92 pass
- Updated `switchyard`: interlock (formerly switchyard) — the local AI device router (in build)

## [1.1.4.6.41] - 2026-10-12

- interlock #92 review
- Updated `switchyard`: interlock (formerly switchyard) — the local AI device router (in build)

## [1.1.4.6.40] - 2026-10-12

- interlock rename (#90) reviewed; instrument renamed
- Updated `switchyard`: interlock (formerly switchyard) — the local AI device router (in build)

## [1.1.4.6.39] - 2026-10-12

- E4b block 2 ruling
- Added `2026-10-12-e4b-block-2`: E4b block 2 — the 5090 runs free beside the NPU and iGPU
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.38] - 2026-10-12

- interlock #89 pass
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.37] - 2026-10-12

- switchyard #89 re-check
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.36] - 2026-10-12

- E4b block 1 aborted; switchyard #89 review
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.35] - 2026-10-12

- switchyard #88 pass
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.34] - 2026-10-12

- switchyard #87 opened (E4b tolerances)
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.33] - 2026-10-12

- E4b pilot accepted; tolerance and steady band 22.5 MHz
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.32] - 2026-10-12

- switchyard #86 pass
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.31] - 2026-10-12

- E4b pilot try 4: rate gap withdrawn
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.30] - 2026-10-12

- E4b pilot try 4: correction
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.29] - 2026-10-12

- E4b pilot try 4 ruling
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.28] - 2026-10-12

- switchyard #85 re-check pass
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.27] - 2026-10-12

- entries: Windows 26340 listener state; test fakes defect class
- Added `2026-10-12-test-fakes-hide-the-platform`: Test fakes that hide the platform, a recurring defect class
- Added `2026-10-12-windows-26340-listener-state-closed`: Windows build 26340 reports a listening socket as Closed

## [1.1.4.6.26] - 2026-10-12

- switchyard #85 review: live-only gaps
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.25] - 2026-10-12

- switchyard #84 re-check pass
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.24] - 2026-10-12

- switchyard #84 review
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.23] - 2026-10-12

- switchyard #83 pass
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.22] - 2026-10-12

- switchyard #80 re-check pass
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.21] - 2026-10-12

- switchyard #82 pass
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.20] - 2026-10-12

- switchyard #72 re-check pass
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.19] - 2026-10-12

- role-set #48 re-check pass
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.6.18] - 2026-10-12

- role-set #48 review
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.6.17] - 2026-10-12

- role-set #47 re-check pass
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.6.16] - 2026-10-12

- role-set #47 review
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.6.15] - 2026-10-12

- role-set: span-valued contains representation ruled
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.6.14] - 2026-10-12

- batch 6 residue cleared (aspire-si #112)
- Updated experiment `stage1-role-eval`

## [1.1.4.6.13] - 2026-10-12

- 2026-10-13 reviews: #106 r5, switchyard #80/#79/#81
- Updated `switchyard`: switchyard — the device-aware model router (in build)
- Updated experiment `stage1-role-eval`

## [1.1.4.6.12] - 2026-10-12

- switchyard E4b pass
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.11] - 2026-10-12

- switchyard E4b draft review
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.10] - 2026-10-12

- instruments/offrig: release 1.1.1
- Updated `offrig`: offrig — big models on rented RunPod GPUs

## [1.1.4.6.9] - 2026-10-12

- newsletter issue 3: the outside review of the first live runs

## [1.1.4.6.8] - 2026-10-12

- switchyard: rulings on Kimi's live-run consult
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.7] - 2026-10-12

- switchyard #71 fixtures pass
- Updated `2026-10-12-ollama-num-predict-zero-is-no-limit`: Ollama 0.35.1 reads num_predict 0 as no limit
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.6] - 2026-10-12

- E4 run 7 readout
- Added `2026-10-12-e4-co-scheduling-inconclusive`: E4: 5090 and Intel co-scheduling is inconclusive on run 7
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.5] - 2026-10-12

- switchyard #72 re-check
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.4] - 2026-10-12

- switchyard #75 pass
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.3] - 2026-10-12

- switchyard #74 pass
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.2] - 2026-10-12

- switchyard E5 run 2 diagnosis
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.1] - 2026-10-12

- switchyard #72 review
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.6.0] - 2026-10-12

- four switchyard live-run records (2026-10-12)
- Added `2026-10-12-device-runs-from-clean-worktree`: Device runs go from a clean worktree
- Added `2026-10-12-e4-npu-static-shape`: E4 NPU arms needed a static shape
- Added `2026-10-12-ollama-num-predict-zero-is-no-limit`: Ollama 0.35.1 reads num_predict 0 as no limit
- Added `2026-10-12-prefix-fit-count-cost`: Prefix fitting cost one count per seed repeat

## [1.1.4.5.115] - 2026-10-12

- switchyard #71 review
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.114] - 2026-10-12

- switchyard #70 pass
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.113] - 2026-10-12

- switchyard #66 pass
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.112] - 2026-10-12

- switchyard #65 pass
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.111] - 2026-10-11

- switchyard #65 review
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.110] - 2026-10-11

- role-set #46 pass
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.109] - 2026-10-11

- role-set #46 review
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.108] - 2026-10-11

- switchyard #62 pass
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.107] - 2026-10-11

- stage1-role-eval batch 6 round 4
- Updated experiment `stage1-role-eval`

## [1.1.4.5.106] - 2026-10-11

- role-set #45 merged
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.105] - 2026-10-11

- switchyard #62 early read
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.104] - 2026-10-11

- role-set generator: contains predicate ruling
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.103] - 2026-10-11

- role-set generator: Kimi-consult decisions confirmed
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.102] - 2026-10-11

- role-set: puzzle generator design ruling; brief updated
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.101] - 2026-10-11

- stage1-role-eval batch 6 round 3; role-set #45; switchyard #62 re-check
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)
- Updated `switchyard`: switchyard — the device-aware model router (in build)
- Updated experiment `stage1-role-eval`

## [1.1.4.5.100] - 2026-10-11

- stage1-role-eval, #109 and #110
- Updated experiment `stage1-role-eval`

## [1.1.4.5.99] - 2026-10-11

- stage1-role-eval, gates 1.5.0 #108
- Updated experiment `stage1-role-eval`

## [1.1.4.5.98] - 2026-10-11

- stage1-role-eval, signature fold ruling; role-set #44
- Updated experiment `stage1-role-eval`

## [1.1.4.5.97] - 2026-10-11

- stage1-role-eval, gates 1.5.0 rulings
- Updated experiment `stage1-role-eval`

## [1.1.4.5.96] - 2026-10-11

- instruments/role-set #43
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.95] - 2026-10-11

- stage1-role-eval, batch 6 rework Part 1 re-check
- Updated experiment `stage1-role-eval`

## [1.1.4.5.94] - 2026-10-11

- instruments/switchyard, #63 disk key pass
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.93] - 2026-10-11

- instruments/role-set, #42 re-check
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.92] - 2026-10-11

- instruments/role-set #42; stage1-role-eval combined brief calls
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)
- Updated experiment `stage1-role-eval`

## [1.1.4.5.91] - 2026-10-11

- stage1-role-eval, batch 6 key-check; instruments/role-set #41
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)
- Updated experiment `stage1-role-eval`

## [1.1.4.5.90] - 2026-10-11

- instruments/switchyard, #63 re-check
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.89] - 2026-10-11

- instruments/switchyard, #60 pass
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.88] - 2026-10-11

- stage1-role-eval, batch 5 round 2b review
- Updated experiment `stage1-role-eval`

## [1.1.4.5.87] - 2026-10-11

- stage1-role-eval: distractor margin set to 0.15 from batch 5's paraphrased round
- Updated experiment `stage1-role-eval`

## [1.1.4.5.86] - 2026-10-11

- stage1-role-eval, #105 gate review
- Updated experiment `stage1-role-eval`

## [1.1.4.5.85] - 2026-10-11

- stage1-role-eval, batch 5 trims; T08 puzzle shapes
- Updated experiment `stage1-role-eval`

## [1.1.4.5.84] - 2026-10-11

- stage1-role-eval, batch 5 round re-check
- Updated experiment `stage1-role-eval`

## [1.1.4.5.83] - 2026-10-11

- stage1-role-eval: distractor margin ruling
- Updated experiment `stage1-role-eval`

## [1.1.4.5.82] - 2026-10-11

- stage1-role-eval: configurable keyed-carry decision; batch 5 re-check
- Updated experiment `stage1-role-eval`

## [1.1.4.5.81] - 2026-10-11

- stage1-role-eval: ruling on Amendment 5 closed-form keyed options
- Updated experiment `stage1-role-eval`

## [1.1.4.5.80] - 2026-10-11

- stage1-role-eval, #104
- Updated experiment `stage1-role-eval`

## [1.1.4.5.79] - 2026-10-11

- stage1-role-eval #103; instruments/role-set #39 defect catalog
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)
- Updated experiment `stage1-role-eval`

## [1.1.4.5.78] - 2026-10-11

- stage1-role-eval: quiz-loop rulings recorded; #102 review
- Updated experiment `stage1-role-eval`

## [1.1.4.5.77] - 2026-10-11

- instruments/switchyard, #63 review
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.76] - 2026-10-11

- instruments/role-set #38; instruments/switchyard #60 #62; site brief: skeleton check in the tool
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.75] - 2026-10-11

- stage1-role-eval, #101 trainer blockers
- Updated experiment `stage1-role-eval`

## [1.1.4.5.74] - 2026-10-11

- instruments/role-set, #37 and #100 re-checks
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.73] - 2026-10-11

- instruments/role-set #37; stage1-role-eval #100
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)
- Updated experiment `stage1-role-eval`

## [1.1.4.5.72] - 2026-10-11

- stage1-role-eval #99 re-check; instruments/role-set #36
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)
- Updated experiment `stage1-role-eval`

## [1.1.4.5.71] - 2026-10-11

- stage1-role-eval, #99 review
- Updated experiment `stage1-role-eval`

## [1.1.4.5.70] - 2026-10-11

- stage1-role-eval, fix round 2b closed
- Updated experiment `stage1-role-eval`

## [1.1.4.5.69] - 2026-10-11

- site: newsletter issue 2 and a brief on checking the verifier's training data

## [1.1.4.5.68] - 2026-10-11

- experiments/cuda-graphs, aspire-si#62 seeding review
- Updated experiment `cuda-graphs`

## [1.1.4.5.67] - 2026-10-11

- stage1-role-eval, fix round 2b addendum
- Updated experiment `stage1-role-eval`

## [1.1.4.5.66] - 2026-10-11

- stage1-role-eval, fix round 2b final pass
- Updated experiment `stage1-role-eval`

## [1.1.4.5.65] - 2026-10-11

- stage1-role-eval, batch 6 brief review
- Updated experiment `stage1-role-eval`

## [1.1.4.5.64] - 2026-10-11

- stage1-role-eval round 2b re-check; instruments/role-set 0.1.0 surface review
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)
- Updated experiment `stage1-role-eval`

## [1.1.4.5.63] - 2026-10-11

- instruments/switchyard, #59 review
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.62] - 2026-10-11

- instruments/offrig, #37 cuda_runtime review
- Updated `offrig`: offrig — big models on rented RunPod GPUs

## [1.1.4.5.61] - 2026-10-11

- stage1-role-eval fix round 2b review; instruments/offrig 1.1.0 treatment review
- Updated `offrig`: offrig — big models on rented RunPod GPUs
- Updated experiment `stage1-role-eval`

## [1.1.4.5.60] - 2026-10-11

- instruments/role-set: fix round 2b brief
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.59] - 2026-10-11

- instruments/role-set: #33 review
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.58] - 2026-10-11

- stage1-role-eval: fix round 2 review
- Updated experiment `stage1-role-eval`

## [1.1.4.5.57] - 2026-10-11

- instruments/offrig: #56 readiness and CUDA pin review
- Updated `offrig`: offrig — big models on rented RunPod GPUs

## [1.1.4.5.56] - 2026-10-11

- instruments/role-set: fix-round-2 brief review
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.55] - 2026-10-11

- instruments/role-set: #32 review
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.54] - 2026-10-11

- stage1-role-eval: fix round 1 merge commit
- Updated experiment `stage1-role-eval`

## [1.1.4.5.53] - 2026-10-11

- stage1-role-eval: fix round 1 cleared; fix round 2 design
- Updated experiment `stage1-role-eval`

## [1.1.4.5.52] - 2026-10-11

- stage1-role-eval: guess vs reject_by_default boundary
- Updated experiment `stage1-role-eval`

## [1.1.4.5.51] - 2026-10-11

- stage1-role-eval: fix round 1 cleared
- Updated experiment `stage1-role-eval`

## [1.1.4.5.50] - 2026-10-11

- stage1-role-eval: T03 floor ruling
- Updated experiment `stage1-role-eval`

## [1.1.4.5.49] - 2026-10-11

- stage1-role-eval: fix round 1 review
- Updated experiment `stage1-role-eval`

## [1.1.4.5.48] - 2026-10-11

- instruments/role-set: #30 cleared
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.47] - 2026-10-11

- instruments/role-set: #30 review
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.46] - 2026-10-11

- instruments/role-set: 8B solver rehearsal
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.45] - 2026-10-11

- stage1-role-eval: batch 5 key-check
- Updated experiment `stage1-role-eval`

## [1.1.4.5.44] - 2026-10-11

- instruments/role-set: #29 cleared; round order
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.43] - 2026-10-11

- instruments/role-set: #29 review; fix-round 1 ruling
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.42] - 2026-10-11

- instruments: role-set #28 merged; switchyard #57 README review
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.41] - 2026-10-11

- instruments/role-set: PR H solver design ruling
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.40] - 2026-10-11

- instruments/role-set: #28 review
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.39] - 2026-10-11

- instruments/role-set: correct the critic-notes finding
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.38] - 2026-10-11

- instruments/role-set: pilot 2 key-check
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.37] - 2026-10-11

- instruments: offrig #55 GPU-count review; role-set #25 review
- Updated `offrig`: offrig — big models on rented RunPod GPUs
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.36] - 2026-10-11

- role-set: dev iteration 2; trait check to verification
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.35] - 2026-10-11

- role-set: dev shared misses are mostly label findings
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.34] - 2026-10-11

- role-set: critic-control legs miss; checks advisory
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.33] - 2026-10-11

- role-set: assembly drop-outs, critic-side review
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.32] - 2026-10-11

- role-set: pilot accepted-104 held
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.31] - 2026-10-11

- role-set: 235B pilot adjudication
- Updated `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)

## [1.1.4.5.30] - 2026-10-11

- stage1: batch 4 passes; conventions adopted
- Updated experiment `stage1-role-eval`

## [1.1.4.5.29] - 2026-10-11

- switchyard: e3-ref reads, 5090 qwen3:8b 208 tok/s
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.28] - 2026-10-11

- switchyard: rest out of the harness; e3-ref empty-prompt defect
- Updated `switchyard`: switchyard — the device-aware model router (in build)
- Updated experiment `verifier-gold`

## [1.1.4.5.27] - 2026-10-11

- switchyard: E3 reads VIABLE, the tail closed
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.26] - 2026-10-10

- stage1: batch 4 key-check, fix round sent
- Updated experiment `stage1-role-eval`

## [1.1.4.5.25] - 2026-10-10

- switchyard: E2 GO, the tail, conditional rest, E3 parked on memory; stage1 batch 3 done
- Updated `switchyard`: switchyard — the device-aware model router (in build)
- Updated experiment `stage1-role-eval`

## [1.1.4.5.24] - 2026-10-10

- stage1-role-eval: batch 3 round-3 key check
- Updated experiment `stage1-role-eval`

## [1.1.4.5.23] - 2026-10-10

- instruments/switchyard: the E2 l512 NPU rejection confirmed as replicated on the -10b receipts (#37)
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.22] - 2026-10-10

- instruments/switchyard: E2 rerun findings (l512 rejection replicated; CPU 8x2048 slow, not stuck) and the per-arm call-bound ruling (#36)
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.21] - 2026-10-10

- stage1-role-eval: batch 3 fix-round key check
- Updated experiment `stage1-role-eval`

## [1.1.4.5.20] - 2026-10-10

- instruments/role-set: the role-shaping data generator (public prototype), its guards and firewall, the self-learning loop and the stuck rule; linked from stage1-role-eval
- Added `role-set`: role-set — a generator for role-shaping training data (prototype, in the open)
- Updated experiment `stage1-role-eval`

## [1.1.4.5.19] - 2026-10-10

- instruments/switchyard: #34 and #35 (native_binary_rejected and the abort flush; E2 amendment, blob bd88da4b) reviewed and passed
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.18] - 2026-10-10

- stage1-role-eval: the stuck rule frozen at 716dc251 (burst clause), and the baseline hedge profile
- Updated experiment `stage1-role-eval`

## [1.1.4.5.17] - 2026-10-10

- stage1-role-eval: hedge bursts (3 within 200 tokens) replace the hedge rate as the (C) trigger, per the pre-registered rule; all hedge and burst fields recorded everywhere
- Updated experiment `stage1-role-eval`

## [1.1.4.5.16] - 2026-10-10

- stage1-role-eval: hedge phrases measured, adopted as a stuck trigger inside (C), and recorded at every sitting
- Updated experiment `stage1-role-eval`

## [1.1.4.5.15] - 2026-10-10

- stage1-role-eval: the frozen stuck rule (re-read baseline 8.09; the late-quote marker dropped as uninformative) and the (lesson, kind) steering cell
- Updated experiment `stage1-role-eval`

## [1.1.4.5.14] - 2026-10-10

- stage1-role-eval: the stuck definition (loop markers gated by length), steering minimum evidence, and the pre-checked reserve pool
- Updated experiment `stage1-role-eval`

## [1.1.4.5.13] - 2026-10-10

- stage1-role-eval: the self-learning generator ruling (no DEV in the store during a stage; between stages only, with a fresh DEV after)
- Updated experiment `stage1-role-eval`

## [1.1.4.5.12] - 2026-10-10

- stage1-role-eval: the rebuilt batch 3 key-check result
- Updated experiment `stage1-role-eval`

## [1.1.4.5.11] - 2026-10-10

- instruments/switchyard: the E2 INVALID_NATIVE_BINARY ruling (#33): a scoped capability outcome, a replication rule, and the abort flush
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.10] - 2026-10-10

- instruments/switchyard: #32, the OpenVINO IR .bin fetched with its .xml at the pinned revision
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.9] - 2026-10-10

- stage1-role-eval: batch 2 passed; batch 3 rejected as template-generated, and the diversity gates proposed
- Updated experiment `stage1-role-eval`

## [1.1.4.5.8] - 2026-10-10

- instruments/switchyard: the #31 run path, and the card-empty gap that blocks E4 (Ollama-only probe, fails open; VRAM ceiling and rest polling asked for)
- Updated `switchyard`: switchyard — the device-aware model router (in build)

## [1.1.4.5.7] - 2026-10-10

- stage1-role-eval: NO-ROLE builder frozen (63162cf4), token ratio 0.644
- Updated experiment `stage1-role-eval`

## [1.1.4.5.6] - 2026-10-10

- stage1-role-eval: the NO-ROLE arm's design (derived one for one, mechanical targets, always-true closings, role-neutral prompts) and its token-ratio limitation
- Updated experiment `stage1-role-eval`

## [1.1.4.5.5] - 2026-10-10

- stage1-role-eval: the composition amendment (training mix shaped by sealed-baseline aggregates; targeted behaviours disclosed; NO-ROLE arm must match composition)
- Updated experiment `stage1-role-eval`

## [1.1.4.5.4] - 2026-10-10

- stage1-role-eval: the complete sealed baseline (aggregates) and Phase A power re-run from the measured per-task baseline (power_empirical.py + receipt; 80% at about +7 to +8 points)
- Updated experiment `stage1-role-eval`

## [1.1.4.5.3] - 2026-10-10

- stage1-role-eval: the three frozen scorers by sha256 and the sealed baseline under them
- Updated experiment `stage1-role-eval`

## [1.1.4.5.2] - 2026-10-10

- stage1-role-eval: the secondary 'found the evidence' score, ruled before any trained model is scored (sealed baseline miss breakdown; lenient formatting, half-coverage, version headings kept)
- Updated experiment `stage1-role-eval`

## [1.1.4.5.1] - 2026-10-10

- stage1-role-eval: batch 2 re-check result and two more failure patterns (thinking that misdescribes the claim; conflicting stop rules)
- Updated experiment `stage1-role-eval`

## [1.1.4.5.0] - 2026-10-10

- experiments/stage1-role-eval: R&D's part of the Stage 1 role evaluation (statistics, power.py + receipt, the rounds stop rule, the pre-interview measures, the frozen scoring rule, key-check record and the patterns that fail instant agreement, the leakage tool); no sealed content
- Added experiment `stage1-role-eval`

## [1.1.4.4.10] - 2026-10-10

- verifier-gold leakage_check.py reads training items: with no claim field, the user turns are the text, compared sentence by sentence (a verbatim interview question planted in a long prompt is flagged)
- Updated experiment `verifier-gold`

## [1.1.4.4.9] - 2026-10-10

- verifier-gold leakage_check.py --against: held-out mode for training data (same or near-duplicate claim fails, Jaccard >= 0.5 warns for paraphrase, 2+ shared material lines fail); reads the pre-interview's numbered questions from .md
- Updated experiment `verifier-gold`

## [1.1.4.4.8] - 2026-10-10

- verifier-gold: leakage_check.py for new task sets (claim copies fail; evidence overlap warns)
- Added experiment `verifier-gold`

## [1.1.4.4.7] - 2026-10-10

- verifier calibration marked provisional (synthetic, unverified gold) in rnd, site and charts; Director quotes rewritten as decisions
- Updated experiment `charts`
- Updated experiment `verifier-gold`

## [1.1.4.4.6] - 2026-10-10

- calibration: Nemotron think-off result (FAIL); think-on stopped by the Director, medium not run
- Updated experiment `verifier-gold`

## [1.1.4.4.5] - 2026-10-10

- verifier-gold: coherence pre-registration (re-rule 60 cannot_tell items; VitaminC + LLM-AggreFact anchor), awaiting the Director
- Updated experiment `verifier-gold`

## [1.1.4.4.4] - 2026-10-10

- calibration: Nemotron path run note; native-serving fidelity check of 'think before accepting' (offrig #54) pre-registered
- Updated experiment `verifier-gold`

## [1.1.4.4.3] - 2026-10-10

- calibration: thinking-control design (Director); replay on existing receipts: 'think before accepting' passes both check types with one policy
- Updated experiment `verifier-gold`

## [1.1.4.4.2] - 2026-10-10

- calibration: nemotron-3.5-lightning pre-registered on tune (off/on/medium) before the grounded held-out is spent; gemma grounded held-out on hold
- Updated experiment `verifier-gold`

## [1.1.4.4.1] - 2026-10-09

- intel-npu: E1 answered (reload-tolerant, max B_reuse 78.5); nomic NPU batch-8 losses are driver-level (3/3 with correct inputs); health check #3
- Updated `intel-npu`: The Intel side of the rig — NPU embeddings and iGPU cross-encoders (npu-serve)
- Added experiment `npu-probe`

## [1.1.4.4.0] - 2026-10-09

- thinking-off results (gemma think-off grounded passes tune, post hoc) + grounded held-out pre-registration; charts built from receipts (13); site: newsletter issue 1 and a research brief directory (9 briefs); study-swarm entry on making thinking cheaper; NPU health check #2 and the E1 root cause
- Added `2026-10-09-making-thinking-cheaper-study-swarm`: Making thinking cheaper — cascades, budgets, distillation, specialists and offload (study-swarm)
- Updated `intel-npu`: The Intel side of the rig — NPU embeddings and iGPU cross-encoders (npu-serve)
- Added experiment `charts`
- Added experiment `npu-probe`
- Updated experiment `verifier-gold`

## [1.1.4.3.37] - 2026-10-09

- calibration: thinking-off chain_step completeness reads metrics.json status (false INCOMPLETE from offrig 9b6527f's report note); check fix only
- Added experiment `charts`
- Updated experiment `verifier-gold`

## [1.1.4.3.36] - 2026-10-09

- intel-npu: NPU health check passed after the E1 device loss (receipt committed)
- Updated `intel-npu`: The Intel side of the rig — NPU embeddings and iGPU cross-encoders (npu-serve)
- Added experiment `npu-probe`

## [1.1.4.3.35] - 2026-10-09

- calibration: thinking-off pre-registration (qwen3:8b, qwen3:14b, gemma4:31b at off, tune; model-verdict primary; offrig 9b6527f sha256 pinned; run lines fixed)
- Updated experiment `verifier-gold`

## [1.1.4.3.34] - 2026-10-09

- intel-npu: correct the hang note (bge ran batch 8 cleanly; hangs were DeBERTa 8x512 and nomic 8x1024); NPU health check defined
- Updated `intel-npu`: The Intel side of the rig — NPU embeddings and iGPU cross-encoders (npu-serve)

## [1.1.4.3.33] - 2026-10-09

- intel-npu: second batch-8 NPU hang (switchyard E1, nomic 8x1024, device lost); batch > 1 on the NPU is a hang risk
- Updated `intel-npu`: The Intel side of the rig — NPU embeddings and iGPU cross-encoders (npu-serve)

## [1.1.4.3.32] - 2026-10-09

- headline: gemma4:31b passes held-out reasoning, offrig's first default verifier (reasoning only)
- Updated `offrig`: offrig — big models on rented RunPod GPUs
- Updated experiment `verifier-gold`

## [1.1.4.3.31] - 2026-10-09

- gemma4:31b rerun result: reasoning PASS on tune, grounded FAIL (one thinking loop); loop-repeat receipt; held-out run line
- Updated experiment `verifier-gold`

## [1.1.4.3.30] - 2026-10-09

- pre-registration note before the reasoning result: v2 held-out is reasoning's one look; v3 needs a fresh sealed split
- Updated experiment `verifier-gold`

## [1.1.4.3.29] - 2026-10-09

- instruments: offrig calibrate changes, switchyard (planned), intel-npu device facts; calibration error-lean post-hoc
- Updated `intel-npu`: The Intel side of the rig — NPU embeddings and iGPU cross-encoders (npu-serve)
- Updated `offrig`: offrig — big models on rented RunPod GPUs
- Added `switchyard`: switchyard — the device-aware model router (in build)
- Updated experiment `verifier-gold`

## [1.1.4.3.28] - 2026-10-09

- gemma rerun pre-registration: context check, num_ctx unchanged
- Updated experiment `verifier-gold`

## [1.1.4.3.27] - 2026-10-09

- gemma rerun pre-registration: binary sha256s, run line, CAL_EXTRA pass-through
- Updated experiment `verifier-gold`

## [1.1.4.3.26] - 2026-10-09

- math ladder v1 results (six models), arithmetic-floor post-hoc, gemma rerun pre-registration amendments
- Updated experiment `verifier-gold`

## [1.1.4.3.25] - 2026-10-09

- quote-match post-hoc finding; ladder report model-verdict view
- Updated experiment `verifier-gold`

## [1.1.4.3.24] - 2026-10-09

- calibration chain result (no default named) and the gemma post-hoc pre-registration
- Updated experiment `verifier-gold`

## [1.1.4.3.23] - 2026-10-09

- calibration: thinking-level table per model
- Updated experiment `verifier-gold`

## [1.1.4.3.22] - 2026-10-09

- calibration: gemma4 back to think on (on/off only); per-model thinking levels
- Updated experiment `verifier-gold`

## [1.1.4.3.21] - 2026-10-09

- calibration README: thinking level is a per-task variable, not a default
- Updated experiment `verifier-gold`

## [1.1.4.3.20] - 2026-10-09

- calibration: thinking-level amendment before gemma; Ollama 500 finding; resume fix
- Updated experiment `verifier-gold`

## [1.1.4.3.19] - 2026-10-09

- difficulty report splits false accepts from false rejects; teacher T3 note
- Updated experiment `distill-ladder`
- Updated experiment `verifier-gold`

## [1.1.4.3.18] - 2026-10-09

- distill plan: Step 0 complete
- Updated experiment `distill-ladder`

## [1.1.4.3.17] - 2026-10-09

- distill plan: Step 0 status
- Updated experiment `distill-ladder`

## [1.1.4.3.16] - 2026-10-09

- Step 0 complete in rnd: dedupe and sealing, scoring properties, Wilson edge fix (ASPIRE, PR #1)
- Added experiment `distill-ladder`
- Updated experiment `verifier-gold`

## [1.1.4.3.15] - 2026-10-09

- atlas map regenerated (red since fd2aca3)

## [1.1.4.3.14] - 2026-10-09

- Step 0: ladder generator property tests (Hypothesis), CI wired
- Updated experiment `distill-ladder`
- Updated experiment `verifier-gold`

## [1.1.4.3.13] - 2026-10-09

- distill plan: student pinned (Qwen3-1.7B @ 70d244cc), aspire-si#72 approved
- Updated experiment `distill-ladder`

## [1.1.4.3.12] - 2026-10-09

- distill plan: teacher pool, itemised card plan, 13.4 sandbox, cleanup; post-hoc candidates marked
- Added experiment `data-designer`
- Updated experiment `distill-ladder`
- Updated experiment `verifier-gold`

## [1.1.4.3.11] - 2026-10-09

- distillation exercise plan v2: ASPIRE's training section, B-matched arm
- Added experiment `data-designer`
- Updated experiment `distill-ladder`

## [1.1.4.3.10] - 2026-10-09

- distillation exercise plan, draft v1 (1.7b student on the math ladder)
- Added experiment `data-designer`
- Added experiment `distill-ladder`

## [1.1.4.3.9] - 2026-10-09

- math ladder: its own scratch store, run step with rest and gates
- Added experiment `data-designer`
- Added experiment `verifier-gold`

## [1.1.4.3.8] - 2026-10-09

- math ladder v1 pre-registered: 780 generated claims, 26 cells
- Added experiment `data-designer`
- Added experiment `verifier-gold`

## [1.1.4.3.7] - 2026-10-09

- calibration: generated math ladder noted for the next round
- Added experiment `data-designer`
- Updated experiment `verifier-gold`

## [1.1.4.3.6] - 2026-10-09

- difficulty table: Wilson CI per cell, under-30 cells tentative
- Added experiment `data-designer`
- Updated experiment `verifier-gold`

## [1.1.4.3.5] - 2026-10-09

- calibration difficulty tiers fixed before the chain
- Added experiment `data-designer`
- Updated experiment `verifier-gold`

## [1.1.4.3.4] - 2026-10-09

- calibration smoke: 6 candidates, 48/48 usable, settings and timings
- Added experiment `data-designer`
- Updated experiment `verifier-gold`

## [1.1.4.3.3] - 2026-10-09

- NPU raw engine rates; nomic on the NPU; Kimi K3 review folded in
- Added experiment `data-designer`
- Updated experiment `npu-probe`

## [1.1.4.3.2] - 2026-10-09

- NPU retrieval benchmark pre-registered (nomic vs bge vs nomic-on-NPU)
- Added experiment `data-designer`
- Added experiment `npu-probe`

## [1.1.4.3.1] - 2026-10-09

- intel-npu instrument points at its skill
- Updated `intel-npu`: The Intel side of the rig — NPU embeddings and iGPU cross-encoders (npu-serve)
- Added experiment `data-designer`

## [1.1.4.3.0] - 2026-10-09

- Intel NPU/iGPU probe and the npu-serve instrument
- Added `intel-npu`: The Intel side of the rig — NPU embeddings and iGPU cross-encoders (npu-serve)
- Added experiment `data-designer`
- Added experiment `npu-probe`

## [1.1.4.2.16] - 2026-10-09

- calibration scripts gate on the watchdog heartbeat (mtime only)
- Added experiment `data-designer`
- Updated experiment `verifier-gold`

## [1.1.4.2.15] - 2026-10-09

- calibration: per-model think from Ollama capabilities; smoke driver
- Added experiment `data-designer`
- Added experiment `verifier-gold`

## [1.1.4.2.14] - 2026-10-08

- reasoning batch 2 blind-relabelled 208/213 and merged; reasoning back to tune/heldout
- Added experiment `data-designer`
- Updated experiment `verifier-gold`

## [1.1.4.2.13] - 2026-10-08

- calibration chain: 15-min rest between models, incomplete stops the chain
- Added experiment `data-designer`
- Updated experiment `verifier-gold`

## [1.1.4.2.12] - 2026-10-08

- calibration protocol amended before any run: reasoning runs on all (under 100 unsupported per split)
- Added experiment `data-designer`
- Updated experiment `verifier-gold`

## [1.1.4.2.11] - 2026-10-08

- calibration protocol pre-registered: tune selects, heldout headline, local 13.4
- Added experiment `data-designer`
- Added experiment `verifier-gold`

## [1.1.4.2.10] - 2026-10-08

- cross-family label check PASS (2 gold errors in 120, fixed); calibration files named
- Added experiment `data-designer`
- Updated experiment `verifier-gold`

## [1.1.4.2.9] - 2026-10-08

- cross-family label check pre-registered: 120-claim sample, gemma4:31b, pass at most 3 gold errors
- Added experiment `data-designer`
- Added experiment `verifier-gold`

## [1.1.4.2.8] - 2026-10-08

- Kev env README: bf16 criterion change disclosed in the gate section
- Added experiment `data-designer`
- Updated experiment `kev-judge-finetune`

## [1.1.4.2.7] - 2026-10-08

- Kev cu134 + causal-conv1d passes, 4.80 s median step; Windows torch.compile probe works
- Updated experiment `cuda-graphs`
- Added experiment `data-designer`
- Updated experiment `kev-judge-finetune`

## [1.1.4.2.6] - 2026-10-08

- atlas map regenerated (CI red since 1.1.4.1.5)
- Added experiment `data-designer`
- Added experiment `kev-judge-finetune`

## [1.1.4.2.5] - 2026-10-08

- site: override postcss-selector-parser to 7.1.6 (Dependabot alert 1)
- Added experiment `data-designer`
- Added experiment `kev-judge-finetune`

## [1.1.4.2.4] - 2026-10-08

- verifier gold, hard reasoning batch blind-relabelled, reasoning at 111 unsupported
- Added experiment `data-designer`
- Added experiment `kev-judge-finetune`
- Updated experiment `verifier-gold`

## [1.1.4.2.3] - 2026-10-08

- verifier gold, Publisher diff-based reasoning set blind-relabelled 208/208
- Added experiment `data-designer`
- Added experiment `kev-judge-finetune`
- Updated experiment `verifier-gold`

## [1.1.4.2.2] - 2026-10-08

- verifier gold: PR set adjudicated (373), grounded unsupported 241
- Added experiment `data-designer`
- Added experiment `kev-judge-finetune`
- Updated experiment `verifier-gold`

## [1.1.4.2.1] - 2026-10-08

- verifier gold batch 3: docs vs code
- Added experiment `data-designer`
- Added experiment `kev-judge-finetune`
- Updated experiment `verifier-gold`

## [1.1.4.2.0] - 2026-10-08

- verifier grounded gold set, batches 1-2 (111 claims)
- Updated experiment `cuda-graphs`
- Added experiment `data-designer`
- Added experiment `kev-judge-finetune`
- Added experiment `verifier-gold`

## [1.1.4.1.6] - 2026-10-08

- causal-conv1d built for cu134 via pip nvcc 13.4
- Added experiment `data-designer`
- Updated experiment `kev-judge-finetune`

## [1.1.4.1.5] - 2026-10-08

- CUDA graphs measured: 7.2-25x on aspire critic heads
- Updated `2026-10-07-cuda-graphs`: CUDA Graphs
- Updated experiment `cuda-graphs`
- Added experiment `data-designer`

## [1.1.4.1.4] - 2026-10-08

- kev cu134 passes full band; graphed_heads seeds CUDA RNG
- Updated experiment `cuda-graphs`
- Added experiment `data-designer`
- Updated experiment `kev-judge-finetune`

## [1.1.4.1.3] - 2026-10-08

- kev cu134 rerun prep: fla/fastapi restored, fla #1330 patch, speed gate
- Added experiment `data-designer`
- Updated experiment `kev-judge-finetune`

## [1.1.4.1.2] - 2026-10-08

- B200 probe: CUDA 13.4 under cuda-compat passes 9 of 9; 2 locality domains
- Updated experiment `cloud-cu134`

## [1.1.4.1.1] - 2026-10-08

- cuda-compat-13-4 gives a real 13.4 driver API on RunPod 13.0 hosts
- Updated experiment `cloud-cu134`

## [1.1.4.1.0] - 2026-10-08

- cloud cu134 probe on a RunPod CUDA 13.0 host; kev cu132 fallback env
- Added experiment `cloud-cu134`
- Updated experiment `kev-judge-finetune`

## [1.1.4.0.13] - 2026-10-08

- cuda-graphs probe venv moved to E:/AI/envs/triton-probe (watchdog-guarded)
- Updated experiment `cuda-graphs`

## [1.1.4.0.12] - 2026-10-08

- CUDA graphs build-out for aspire-si critic heads (code, CPU tests, gates; GPU run pending)
- Updated `2026-10-07-cuda-graphs`: CUDA Graphs
- Added experiment `cuda-graphs`

## [1.1.4.0.11] - 2026-10-08

- kev env: fallback is stable cu132 (to be built), not cu128 (Director)
- Updated experiment `kev-judge-finetune`

## [1.1.4.0.10] - 2026-10-08

- kev-judge-finetune: new-env runs write their own output names, never over a reference run
- Updated experiment `kev-judge-finetune`

## [1.1.4.0.9] - 2026-10-08

- kev-judge-finetune: CUDA 13.4 env (torch 2.16 nightly cu134) pinned with a lock file and a fixed pass band; KEV_VENV selects the env
- Updated experiment `kev-judge-finetune`

## [1.1.4.0.8] - 2026-10-08

- nvidia-skills review: training-lane skills read (tao-finetune-huggingface-model, nemo-rl-auto-research, data-designer, nemotron-customize)
- Updated catalog `nvidia-skills`

## [1.1.4.0.7] - 2026-10-08

- natural-errors build.py p2: numbered sentences, one verdict per sentence, tune half only, resumable, run tags for the noise floor and the thinking dial
- Updated experiment `natural-errors`

## [1.1.4.0.6] - 2026-10-08

- hymn-arrangements uploaded (private), round-trip verified 21/21

## [1.1.4.0.5] - 2026-10-08

- natural-errors: pre-registered tuning grid, frozen 53/42 split, P1 baselines on the tune half; R&D pre-run amendments (per-sentence schema, cross-family verifier); full-95 screen plan withdrawn
- Updated experiment `natural-errors`

## [1.1.4.0.4] - 2026-10-08

- natural-errors: screen2 full-run plan and the 40% bar, committed before the run; --sample
- Updated experiment `natural-errors`

## [1.1.4.0.3] - 2026-10-08

- Data pack hymn-arrangements (v1, spec and manifest; not uploaded): three Kimi-K3 piano arrangements of public-domain hymns, CC0, with briefs, prompts, raw answers and generation records. The arrangement entry's CC0 and public-domain claims are verified at source.
- Updated `2026-10-08-llm-piano-arrangement-from-a-generated-brief`: Piano arrangements by an LLM from a brief generated from the score

## [1.1.4.0.2] - 2026-10-08

- natural-errors: context-rich screen pilot (5 judges x 3 answers); capability-aware thinking, reasoning-first replies, --num-predict
- Added experiment `natural-errors`

## [1.1.4.0.1] - 2026-10-08

- Six findings and one instrument from the ai-jam-sessions sung-exemplar work: the pyannote one-voice gate, aligner misdates, the phrase-end hold, LLM piano arrangement from a generated brief, Pages cache stitching of replaced media, TranslateGemma fraction and name slips; instrument sung-exemplar-method.
- Added `2026-10-08-aligner-misdates-cause-sung-dropouts`: Misdated syllable onsets cause dropouts in phrase-picked singing
- Added `2026-10-08-llm-piano-arrangement-from-a-generated-brief`: Piano arrangements by an LLM from a brief generated from the score
- Added `2026-10-08-pages-cache-stitches-replaced-media`: Replacing a media file under the same URL on GitHub Pages can break playback
- Added `2026-10-08-phrase-end-hold-removes-the-stutter`: Holding the phrase-final note removes the "stutter" in placed singing
- Added `2026-10-08-translategemma-failure-modes-on-readme-tables`: TranslateGemma 27B mistranslates fractions and transliterates model names
- Added `2026-10-08-voice-gate-pyannote-segmentation-on-sung-vocals`: A one-voice gate for synthesised singing with pyannote segmentation
- Added `sung-exemplar-method`: Sung-exemplar method — a hymn to a published sung recording
- Updated experiment `natural-errors`

## [1.1.4.0.0] - 2026-10-08

- rnd datapack build|list|verify: data packs hosted outside the clone, with per-file SHA-256, licences and model pins (integrity model from research-packs)
- first pack: natural-errors v1, private on Hugging Face (mcp-tool-shop/rnd-natural-errors)
- natural-errors build.py: screen2, a context-rich re-screen (thinking where supported, reasoning-first otherwise, failure reasons logged)
- Updated experiment `natural-errors`

## [1.1.3.3.2] - 2026-10-08

- muse-glimmer as a natural-error screen judge
- Updated `2026-10-08-three-follow-up-studies-for-critic-recipes-hard-pairs-two-pl`: Three follow-up studies for critic recipes — hard pairs, two planter families, natural errors
- Updated experiment `natural-errors`

## [1.1.3.3.1] - 2026-10-08

- SAM3 and sam-3d-objects access accepted
- Updated `2026-10-08-gated-model-scouting-what-to-request-for-the-critic-audio-an`: Gated model scouting — what to request for the critic, audio and visual research

## [1.1.3.3.0] - 2026-10-08

- Study A natural-error set labelled (two blind Claude passes, adjudicated); screen readout; 31 correction pairs
- Updated `2026-10-08-three-follow-up-studies-for-critic-recipes-hard-pairs-two-pl`: Three follow-up studies for critic recipes — hard pairs, two planter families, natural errors
- Updated experiment `natural-errors`

## [1.1.3.2.7] - 2026-10-08

- Scouting: Llama 4 access accepted
- Updated `2026-10-08-gated-model-scouting-what-to-request-for-the-critic-audio-an`: Gated model scouting — what to request for the critic, audio and visual research

## [1.1.3.2.6] - 2026-10-08

- Gemma licensing checked at the source: Gemma 4 is Apache-2.0, outside the Gemma Terms
- Updated `2026-10-08-gated-model-scouting-what-to-request-for-the-critic-audio-an`: Gated model scouting — what to request for the critic, audio and visual research

## [1.1.3.2.5] - 2026-10-08

- Kev judge fine-tune transfers to gemma-planted errors; scouting gating corrections
- Updated `2026-10-07-open-jev-style-decision-models`: Open Jev-style decision models — the landscape, checked against primary sources
- Updated `2026-10-08-gated-model-scouting-what-to-request-for-the-critic-audio-an`: Gated model scouting — what to request for the critic, audio and visual research
- Updated experiment `kev-judge-finetune`

## [1.1.3.2.4] - 2026-10-08

- Scouting: access status and a reading of the Gemma Terms of Use
- Updated `2026-10-08-gated-model-scouting-what-to-request-for-the-critic-audio-an`: Gated model scouting — what to request for the critic, audio and visual research

## [1.1.3.2.3] - 2026-10-08

- Fix: aggregator source URL in the scouting entry
- Updated `2026-10-08-gated-model-scouting-what-to-request-for-the-critic-audio-an`: Gated model scouting — what to request for the critic, audio and visual research

## [1.1.3.2.2] - 2026-10-08

- Gated model scouting: what to request for the critic, audio and visual research
- Added `2026-10-08-gated-model-scouting-what-to-request-for-the-critic-audio-an`: Gated model scouting — what to request for the critic, audio and visual research
- Added experiment `kev-judge-finetune`

## [1.1.3.2.1] - 2026-10-08

- ASPIRE: the found Auditor holds on fresh pairs (0.678)
- Updated `2026-10-08-more-prompts-raise-the-aspire-critic-s-accuracy-but-not-its-`: More prompts raise the ASPIRE critic's accuracy but not its spread between seeds; critic init and run seed both carry the spread

## [1.1.3.2.0] - 2026-10-08

- Experiment natural-errors: in-domain natural-error yardstick built (95 answers, 3-judge screen, 85 for review)
- Added experiment `natural-errors`

## [1.1.3.1.1] - 2026-10-08

- Three follow-up studies for critic recipes: designs for natural errors, two planter families, hard pairs
- Added `2026-10-08-three-follow-up-studies-for-critic-recipes-hard-pairs-two-pl`: Three follow-up studies for critic recipes — hard pairs, two planter families, natural errors

## [1.1.3.1.0] - 2026-10-08

- Dataset recipes for critic jury roles: evidence, recipe card, controls, panel selection, role-os connection
- Added `2026-10-08-dataset-recipes-for-critic-jury-roles-designing-roles-by-dat`: Dataset recipes for critic jury roles — designing roles by data and choosing the panel

## [1.1.3.0.8] - 2026-10-08

- ASPIRE critic-init: report PR #44; seed-44 composite critic may have been an inverted draw
- Updated `2026-10-07-sft-before-aspire-weakens-critic`: SFT before ASPIRE has no reliable effect on the critic; run-to-run critic variance dominates (3 seeds)
- Updated `2026-10-08-more-prompts-raise-the-aspire-critic-s-accuracy-but-not-its-`: More prompts raise the ASPIRE critic's accuracy but not its spread between seeds; critic init and run seed both carry the spread

## [1.1.3.0.7] - 2026-10-08

- ASPIRE critic-init test: init and run seed both carry the spread; one init inverted the critic
- Updated `2026-10-08-more-prompts-raise-the-aspire-critic-s-accuracy-but-not-its-`: More prompts raise the ASPIRE critic's accuracy but not its spread between seeds; critic init and run seed both carry the spread

## [1.1.3.0.6] - 2026-10-08

- ASPIRE step 2: report PR #42 as primary source
- Updated `2026-10-08-more-prompts-raise-the-aspire-critic-s-accuracy-but-not-its-`: More prompts raise the ASPIRE critic's accuracy but not its spread between seeds

## [1.1.3.0.5] - 2026-10-08

- ASPIRE step 2: more prompts raise the critic's level, not its seed spread
- Updated `2026-10-07-sft-before-aspire-weakens-critic`: SFT before ASPIRE has no reliable effect on the critic; run-to-run critic variance dominates (3 seeds)
- Added `2026-10-08-more-prompts-raise-the-aspire-critic-s-accuracy-but-not-its-`: More prompts raise the ASPIRE critic's accuracy but not its spread between seeds

## [1.1.3.0.4] - 2026-10-08

- America the Beautiful is written at 92 BPM: relative verse build and coda
- Updated `2026-10-07-expressive-timing-and-emphasis-for-a-sung-hymn-performance-r`: Expressive timing and emphasis for a sung hymn — performance rules applied to synthetic singing

## [1.1.3.0.3] - 2026-10-08

- Hymn timing: Battle Hymn outcome; per-hymn values for Amazing Grace and America the Beautiful
- Updated `2026-10-07-expressive-timing-and-emphasis-for-a-sung-hymn-performance-r`: Expressive timing and emphasis for a sung hymn — performance rules applied to synthetic singing

## [1.1.3.0.2] - 2026-10-08

- Battle Hymn: SoulX's measured dotted ratio at 76–80 BPM (0.57) replaces the assumption; A/B contrast 1 reframed
- Updated `2026-10-07-expressive-timing-and-emphasis-for-a-sung-hymn-performance-r`: Expressive timing and emphasis for a sung hymn — performance rules applied to synthetic singing

## [1.1.3.0.1] - 2026-10-08

- Experiment scripts point at E:/AI/rnd, the local folder's new name
- Updated experiment `kev-judge-finetune`
- Updated experiment `openjev-vs-jev`

## [1.1.3.0.0] - 2026-10-08

- Name-clash fix: the code moves to `mcptoolshop_rnd` (the import name that always works); `rnd` stays as a compatibility shim that aliases every submodule, and the `rnd` command runs `mcptoolshop_rnd.cli:main`, so an unrelated PyPI `rnd` replacing the shim breaks neither the command nor `python -m mcptoolshop_rnd`
- tests/test_packaging.py and a CI clash check (a raising rnd/ stub after a clean install) prove it

## [1.1.2.0.0] - 2026-10-08

- Packaged for PyPI as `mcptoolshop-rnd` (pyproject.toml, uv.lock); the `rnd` command finds its library via `--library`, `$RND_ROOT` or the nearest folder with entries/ and instruments/, else stops with NO_LIBRARY
- release.yml: publishes to PyPI by trusted publishing when a GitHub release is published; refuses a tag that differs from the package version
- CI: build, twine check, clean-install smoke and pip-audit; README and handbook document the install

## [1.1.1.2.3] - 2026-10-07

- Battle Hymn expressive timing and emphasis research
- Added `2026-10-07-expressive-timing-and-emphasis-for-a-sung-hymn-performance-r`: Expressive timing and emphasis for a sung hymn — performance rules applied to synthetic singing

## [1.1.1.2.2] - 2026-10-07

- Kev judge: scorer identity with the reference confirmed
- Updated experiment `kev-judge-finetune`

## [1.1.1.2.1] - 2026-10-07

- Kev judge weights in the private HF repo
- Updated `2026-10-07-open-jev-style-decision-models`: Open Jev-style decision models — the landscape, checked against primary sources
- Updated experiment `kev-judge-finetune`

## [1.1.1.2.0] - 2026-10-07

- Kev-4B judge fine-tune: three seeds pass the pre-registered rule; aspire-si confirmation filed
- Updated `2026-10-07-open-jev-style-decision-models`: Open Jev-style decision models — the landscape, checked against primary sources
- Updated `2026-10-07-qwen32b-judge-position-bias`: Qwen2.5-32B as a judge of planted errors — ties, total position bias, and how to plant errors
- Updated experiment `kev-judge-finetune`

## [1.1.1.1.0] - 2026-10-07

- New experiment kev-judge-finetune: Kev-4B LoRA fine-tune as a planted-error judge on aspire-si's fresh pairs (1,086 rows, both orders, 0 leaks), success rule written before the run
- Added experiment `kev-judge-finetune`

## [1.1.1.0.19] - 2026-10-07

- Planted-defects program: event spans merged (#96); detector heads fit their operating point on validation mixes; a third song (Battle Hymn) makes the song split 3-fold
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.18] - 2026-10-07

- Planted-defects program: event spans (#96) and detector heads (#98) as CPU-tested code; the operating point must include shams
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.17] - 2026-10-07

- Planted-defects program: planter PR 2 merged (#95); Step B split between ai-jam-sessions (clips, evidence) and the R&D seat (MERT/Dasheng heads); MERT is CC BY-NC, so a shipped detector needs Dasheng
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.16] - 2026-10-07

- Planted-defects program: planter PR 2 opened as ai-jam-sessions #95; alternate picks (#94) merged
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.15] - 2026-10-07

- Kev as a judge: 9B trails 4B because its order gap is noisier (sd 0.205 vs 0.144; 25 vs 3 pairs on the wrong side), not because it is less biased; the confirmation run is specified
- Updated `2026-10-07-open-jev-style-decision-models`: Open Jev-style decision models — the landscape, checked against primary sources

## [1.1.1.0.14] - 2026-10-07

- Kev as a judge (exploratory): averaging over both answer orders took Kev-4B from 0.547 to 0.976 on aspire-si's 127 planted-error pairs; to be confirmed on fresh pairs. Cross-linked from the Qwen-32B judge entry
- Updated `2026-10-07-open-jev-style-decision-models`: Open Jev-style decision models — the landscape, checked against primary sources
- Updated `2026-10-07-qwen32b-judge-position-bias`: Qwen2.5-32B as a judge of planted errors — ties, total position bias, and how to plant errors

## [1.1.1.0.13] - 2026-10-07

- Kev: training is adapter-only for 0.8B/4B/9B, so a local WSL run on the 5090 is plausible; smoke-test before renting
- Updated `2026-10-07-open-jev-style-decision-models`: Open Jev-style decision models — the landscape, checked against primary sources

## [1.1.1.0.12] - 2026-10-07

- Kev: how to fine-tune it (--init_from, JSONL with labels), its server switches (/permute against option-order bias, KEV_DATE_FACTS), and that kev.train fails on native Windows
- Updated `2026-10-07-open-jev-style-decision-models`: Open Jev-style decision models — the landscape, checked against primary sources

## [1.1.1.0.11] - 2026-10-07

- Planted-defects program: PR 2 built (stretch, pitch slip, vocoded sham, compound kinds); compounds are 3–4× more available than clean replays, and replay+early-vowel has no eligible join in the shipped warp mixes
- Kev as a planted-error judge: 0.547 (4B) and 0.598 (9B) with heavy first-option bias; not a useful judge for that task
- Updated `2026-10-07-open-jev-style-decision-models`: Open Jev-style decision models — the landscape, checked against primary sources
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.10] - 2026-10-07

- Planted-defects program: planter #91 ready; warp clicks verified at either hard edge of a seam and graded by crossfade length; final warp trial kept 83/100 and 86/100
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.9] - 2026-10-07

- Planted-defects program: only 13–15% of shipped warp joins can carry a clean replay/skip once vowel-move and pause compounds are refused; replays now verify 17–18 of 20
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.8] - 2026-10-07

- SFT-before-ASPIRE correction: aspire-si PR #30 and the run 1 report added as primary sources
- Updated `2026-10-07-sft-before-aspire-weakens-critic`: SFT before ASPIRE has no reliable effect on the critic; run-to-run critic variance dominates (3 seeds)

## [1.1.1.0.7] - 2026-10-07

- Correction: SFT before ASPIRE has no reliable effect on the critic (3 seeds, pre-registered rule); the earlier claim is marked wrong. Critic run-to-run variance (0.425–0.866) and a replicating ASPIRE drift direction against SFT are the findings that hold
- Pod host checks: container disk with HF_HOME on it wrote at ~1.3 GB/s; one draw stalled pulling its image
- Updated `2026-10-07-pod-host-checks-driver-and-download`: Rented GPU pods — the driver and download speed vary per host, so check both first
- Updated `2026-10-07-sft-before-aspire-weakens-critic`: SFT before ASPIRE has no reliable effect on the critic; run-to-run critic variance dominates (3 seeds)

## [1.1.1.0.6] - 2026-10-07

- Planted-defects program: #91 review fixes; warp replay/skip plants displace the cut's vowel (0.1 s replays moved it 0.18–0.21 s), now recorded per label
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.5] - 2026-10-07

- New logo (brand repo logos/rnd), teal accent and favicon to match
- Planted-defects program: planter engine rebased on the placer overrides; warp trial on the shipped mixes kept 75/100 and 77/100; finding that the pad16 warp mixes have no mid-phrase splices
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.4] - 2026-10-07

- Planted-defects program: planter engine drafted as ai-jam-sessions #91 (plan mutation, replay/skip measured from where the take had reached; 39/40 plants kept on a real mix)
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.3] - 2026-10-07

- Planted-defects program: RunPod cost estimate from live offrig prices (Step B $2.50–14.50; first full program $5–30) against about $2–3 of electricity on the local 5090
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.2] - 2026-10-07

- Planted-defects program: adopted by ai-jam-sessions; calibrated review tracked as ai-jam-sessions #89
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.1] - 2026-10-07

- Planted-defects program for sung mixes: an automated planter-versus-detector loop with a regret reward, a MERT frame-level detector, and the Director's catch trials setting the audibility line (seven research agents' findings)
- Added `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.0] - 2026-10-07

- Coverage bar raised to 90%: CI fails under 90% and Codecov's project and patch targets are 90%
- 45 tests (was 25), including end-to-end CLI tests of every command, catalogue sync with gh mocked, and rnd bump in a real git repo; rnd/ coverage 96% (was 63%)

## [1.1.0.0.0] - 2026-10-07

- Added `rnd bump`: five-segment versions (MAJOR.MINOR.PATCH.MICRO.NANO) with a CHANGELOG section written from the files changed since the last tag
- Kev-4B and Kev-9B measured against hosted Jev and OpenJev on sense-si's 124 phrases, 0-shot and with knowledge in context
- Added `2026-10-07-open-jev-style-decision-models`: Open Jev-style decision models — the landscape, checked against primary sources
- Updated `2026-10-07-openjev-and-open-jev-alternatives`: OpenJev and the other open "Jev" models — what each one is
- Updated experiment `openjev-vs-jev`

## [1.0.0] - 2026-10-07

### Added

- `rnd` CLI over a Markdown research library: `build`, `check`, `search`, `show`,
  `list`, `tools`, `stats`, `new`, `catalog`, `readouts`, `sql`, each listing with `--json`.
- Entry format with source tiers (`primary`, `secondary`, `aggregator`, `user`, `rig`)
  and claim confidence (`unverified`, `verified`, `disputed`, `wrong`; `verified`
  needs a `via:` note).
- SQLite FTS5 index (`rnd.db`), rebuilt automatically when files change; the previous
  index is kept when a rebuild meets errors.
- Instrument registry (`instruments/`) of the studio tools research can call.
- NVIDIA skills catalogue mirror (398 skills, 18 lanes) with a studio-fit review.
- `rnd readouts`: read-only federated search across the readouts knowledge bases,
  with prefix matching and `--any`.
- `experiments/` for rig measurements, with pinned inputs and result receipts.
- `--version`, and `--debug` to show a traceback; unexpected errors otherwise print
  a structured `INTERNAL` error and exit 3.
- `verify.sh` (tests, library check, index build, smoke), CI, landing page and handbook.

### Fixed

- The `rnd sql` error hint pointed at a missing `docs/schema.md`; it now shows how
  to list the tables.
