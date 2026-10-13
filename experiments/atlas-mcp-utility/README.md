# atlas-mcp-utility: does `atlas mcp` help an agent answer questions about a repository?

**Status.** Pre-registration, 2026-10-13. Nothing has run.
- R&D approved the design on 2026-10-13, with seven additions that are folded in below.
- The Director approved pricing it and chose to run it on his Claude plan.
- The pilot runs once the key check below is done. The full run needs his go after he has seen what the pilot measured.
- **Amendment 5 (2026-10-13):** the full run becomes a repository ladder. Rung 1 is the 42-task bank below, unchanged. Each later rung adds one linked repository to the workspace. See [ladder.md](ladder.md).
- **On hold (2026-10-13):** the Director ruled that Atlas is built up before any testing. The probes and the pilot wait for the build-up release, and a dated amendment moves the Atlas pin to it before the pilot.

## The question and the decision it feeds

Do coding agents answer real questions about fleet repositories correctly more often, or at lower cost, when the Atlas MCP sidecar (`atlas mcp`, `@dogfood-lab/atlas`) is available?

**The decision:** whether agent kickoffs include `atlas mcp`. Under the org rule, every fleet repository already commits its `atlas/` map, and an agent can read those files without the sidecar. So this measures **what the sidecar adds over the committed map**, not what the map adds over nothing.

**Prior art:** Gloaguen et al. 2026 (arXiv:2602.11988) found that repository context files such as AGENTS.md did not generally raise coding agents' success and raised inference cost by over 20% (as cited in testing-os `docs/atlas-sidecar.dispatch.md`). The sidecar was built to be queried, not pasted into every session. Whether that design escapes the cost has not been measured.

## Pinned before any run

Each sha256 is of the file as committed, with LF line endings (`.gitattributes`).

| What | Pin |
|---|---|
| `tasks.json` | `eb2ba43c88c989022ecf2fe90d950b150e144a3f916540fa68c1d46559acca1a` (amendment 3) |
| `prompt.md` | `a32c1c8f30e88f7264e6efce1d1c608339368b2e44691870206b3105e4e6226d` |
| `allow-list.json` | `ff2500444a24a9f859c081869fe62448fa44006a601c94b0545136ef1184b3b4` (amendment 2) |
| `grade.py` | `f6d09f5144b42fc1c86f632015de33c84d0bfb9dd3faf2f192cb47d24d864455` (amendment 1) |
| `debrief.md` | `ed73ef0864f6b603f32ab3f4a91874c465d537779ff1450094bc82690d312f8c` (amendment 3) |
| Claude Code CLI | 2.1.197 |
| Model | `claude-sonnet-5-5`, at the CLI's default effort for it |
| Atlas | `@dogfood-lab/atlas` 1.26.0 |
| Seed (arm order, key draw) | 20261013 |

A pin changes only before the pilot, and only by a dated amendment here that says why. One example: R&D's key check fixing a key, which changes `tasks.json`'s hash. Another: Atlas 1.27.0 shipping first. After the pilot's first run, nothing pinned changes.

### Amendment 1, 2026-10-13: R&D's blind key audit

Three agents that never saw the keys answered the 15 sampled questions from the pinned commits. R&D compared each answer with its key and graded it with `grade.py`. The answers and verdicts are in `key-audit.json`. Fourteen keys were right, and the audit found a grader defect.

1. **No word cap.** CF01, CF05, CF06 and CF07 were answered correctly (same cause, file and function, and `fixable_in_repo_files`) in 70 to 80 words, and graded wrong only because the text checks capped length at 40 or 60 words. No question states a length, and a cap could favour whichever arm writes less.
   - The cap is removed from every check and from `grade.py`. The hedge rejects still catch an answer that lists every candidate cause.
   - A test now requires all 15 blind answers to grade correct.
2. **TG03's key.** `tests/manifest.test.ts` also spawns the built CLI (line 935 sets `BIN` to `dist/cli.js`; line 985 runs `runCli(['manifest', ...])`). `exercised_via` may now name five spawning tests, and must still include `manifest-cmd` and `verify`.
3. **CF06's pin stays at `4bc808e376`,** though R&D asked for `d888f86c72`, the failing run's head. `d888f86c72` has no Atlas map: research-os adopted Atlas three commits later. Pinning it would leave arm B with no map for this one task.
   - The three commits between change only `.github/workflows/ci.yml`, `codecov.yml` and `atlas/`. The Pages workflow and the cause, a repository setting, are the same at both.
   - CF07 likewise pins the first commit with a map, the child of its failing run's commit.
4. **WR02 reworded** to ask for "the function that saves the game". `_atomic_write_text` does the physical write, so "writes" had two fair readings. The key, `save_game`, is unchanged.

`tasks.json` and `grade.py` are re-pinned above. `prompt.md` and `allow-list.json` are unchanged.

### Amendment 2, 2026-10-13: the runs isolated from the rig, and the harness

The Director gave his go for the pilot only, on his Claude plan, with a ceiling of 30 million tokens.

**The problem.** Building the harness showed that a print-mode run on this rig would otherwise load the operator's user settings, including hooks that inject memory notes into the prompt. It could also read files outside its checkout, among them memory notes and other repositories that discuss the triage this bank replays. `--bare` isolates all of that, but it accepts only API-key auth, and this run is on a plan.

**The isolation instead:**
1. `--setting-sources local`: no user settings, hooks or permissions.
2. **Reads held to the checkout.**
   - `Read(./**)` is allowed.
   - `Read(~/**)`, `Read(//c/Users/**)`, `Read(//d/**)` and `Read(//e/AI/**)` are denied, as are Edit, Write, NotebookEdit, WebFetch, WebSearch and Task. The D: drive holds the archive, memory copies among it.
   - Glob and Grep search inside the checkout under the Read rules.
   - Bash keeps only `git log` and `git show`. `ls` would list any directory, and `git grep --no-index` reads any path whatever order its flags come in (R&D's review). `git -C <elsewhere>` matches no allowed form.
   - The harness refuses a `--work` under `C:/Users`, `D:/` or `E:/AI`, since a deny rule outranks `Read(./**)`.
3. `--no-session-persistence`.
4. **The prompt goes in on stdin.** The CLI is started as the binary the npm `.cmd` shim wraps, since a `.cmd` cannot be started without a shell.
5. **Every run is checked:**
   - its init event shows its arm's tools (arm A: no MCP tools; arm B: the Atlas tools and no other server's) and the pinned model;
   - no hook ran: no hook event, and no `[loadout-hook]` text in the stream;
   - `git status --porcelain` on its copy is empty afterwards, because `git log --output=` can write a file.

   A run that fails a check stops the pilot.

**What stays.** The user-level CLAUDE.md may still load in print mode without `--bare`. It is the same in both arms, and it is what kickoffs run with. The probes record whether it loads.

**Probes, before the pilot** (`run.py --probe`). They are counted against the pilot's 30-million-token ceiling and reported apart from the pilot's runs. R&D reads their report before the first graded run.
- **(a) Containment.** In each denied tree present (the home directory, `E:/AI`, `D:/`), the harness plants two files holding a random token. One is named in the prompt; the other is named nowhere, so only a listing or a search could reveal it.
  - Arm A is asked to reach them by every route: Read the named file; Grep with `path=` set to the tree; Glob rooted in the tree; `ls` the tree; `git grep --no-index`; and `git -C E:/AI/testing-os log -1`, whose commit is also a secret.
  - It passes only if every route was attempted, no token, hidden file name or commit comes back in any tool result, and no hook ran.
  - The files are removed afterwards.
  - The report names each planted value by a label and its sha256, never the value. A leaked value in a tool result is replaced by its label (R&D's review of #8, after CodeQL flagged clear-text storage).
- **(b) The sidecar:** arm B is asked for `atlas_overview`, which must answer.
- **(c) CLAUDE.md:** whether the user-level CLAUDE.md loaded.

If a deny rule does not hold on Windows, the pilot waits for a corrected rule and a new probe, both recorded here. The harness refuses `--pilot` without a passed probe report.

**A limit the permission rules cannot close, and its detector.** `git log` stays allowed in both arms, because arm B's `atlas_changes` reads history and taking history away from arm A alone would tilt the comparison. An allowed `git log` or `git show` can still be turned into something else:
- `--output=<path>` writes a file anywhere;
- a redirection or chain (`>`, `>>`, `|`, `;`, `&&`, a single `&`, or a line break that starts a second command) writes a file or runs another command;
- `<` feeds a file's text to git, and git's error for a bad revision echoes it back;
- command substitution (`$(...)` or backticks) runs another command, even inside double quotes.

Every Bash command a run makes is in its stream. During the pilot, a run that makes any of these calls stops the pilot, and the report names the call. Redirection, chaining and line breaks are read outside quotes, so `--format='%H|%s'` and a quoted newline in `--format` pass. Substitution is read everywhere. Each form has a test, R&D's bypasses on #7 among them.

**The harness** is `run.py`. Its logic (pins, run order, token and call counting, the isolation check, the plan-limit stop, the flip rate) is tested in `tests/test_atlas_mcp_utility_run.py`. `allow-list.json` is re-pinned above.

### Amendment 3, 2026-10-13: a debrief after each graded run, and two stated conventions

**The debrief.** The Director asked to hear from each agent after its task: what cost the most, what was unclear, which tools helped or misled, how sure it was, and what to build next. R&D ruled on how.
- **Same process, a second turn.** Sessions are not persisted, so the harness talks to the CLI with `--input-format stream-json`. It sends the task, waits for its result event, and only then sends the debrief.
- **Graded from the first result only.** The answer is taken from the task's own result. The debrief cannot change it, and a test proves that a debrief naming another answer leaves the grade as it was.
- **One fixed prompt, pinned** (`debrief.md`), the same in both arms. It asks six numbered questions to be answered in plain text without tools: time and cost, clarity, tools, confidence, future development, and anything else. It carries no grade, no key and no hint of the other arm.
- **Not a metric.** A debrief's tokens and tool calls count against the ceiling, but they are reported apart and never enter a run's figures or its grade. A tool call during a debrief is recorded and held to the same isolation checks.
- **Output.** `results/pilot/debriefs.jsonl` holds one record per run: task, arm, rep, each numbered answer as its own field, and the whole text. Home paths are scrubbed, and the identity scan gates the commit. R&D summarises them for the Director, by item and by arm.
  - Item 4, confidence, is a self-report and no metric.
  - Nothing in the decision rule reads the debriefs.
- **Probes take no debrief.** A run whose task failed, or whose plan ran out, gets none. A plan limit reached during a debrief still stops the pilot.

**Two conventions the keys assume, now stated in the questions.** The key auditors' own debriefs found that the keys assumed two conventions the questions did not state. Unstated, they let a correct agent disagree with the key for reasons that have nothing to do with Atlas.
- **The reach and import questions (RC*, WR02)** now say that in Python, an import inside a function body counts, and that `from pkg import module` imports that module's file. RC09's key depends on a lazy import.
- **TG02** now says that `test_*` is "of any file extension". It names no extension: naming `.mjs` would give away two of the four answers, and would mask the possible Atlas `.mjs` test-gap defect this task can measure (R&D's review).

**The failure kind is recorded per CI-failure task** (`failure_kind`: `code` or `setting`), with CF01's defect noted as intermittent.

`tasks.json` is re-pinned and `debrief.md` pinned above. `prompt.md`, `allow-list.json` and `grade.py` are unchanged.

## Design

**Pairs.** Each task runs twice:
- arm A, without `atlas mcp`;
- arm B, with it.

Everything else is the same in both arms: model, prompt, checkout, tool allow-list, CLI version, and settings. The order of the two arms within each pair comes from the seed. Both runs of a pair go back to back, so drift in the service lands on both, and no limit can split a pair.

**Tasks.** `tasks.json` holds 42 tasks from 17 public fleet repositories, each pinned to a commit. Each task carries:
- the question as the agent gets it, ending in the JSON shape of its answer;
- the answer key and how it is checked (`check_method` in words, `grade` as rules);
- where the key came from (`key_source`): the code, the workflow YAML, lockfile `engines`, fix-commit diffs, or run logs, **never Atlas's own output**;
- a confidence (33 high, 9 medium).

| Stratum | Types | Tasks |
|---|---|---|
| Structure | reach (direct and transitive), which workflow runs what, what a file or part is, writers and readers, test gaps | 29 |
| Workflow breakage | a Node pin a test tool does not accept (5), and one negative control that will not break (WB01) | 6 |
| CI failures | the 2026-09-30 triage replayed, with the run's own failure text given in the question | 7 |

The 2026-09-30 triage found eight default branches red from five causes, and Atlas surfaced none of them. Three of the seven CI-failure tasks have a repository setting as their cause (CF05, CF06, CF07). Atlas cannot see settings by design, so these are **negative controls**: the right answer is "not fixable in a file", and they test whether the sidecar wastes tokens or overclaims. A ninth task, for a private repository, is left out of this public bank.

**Known correlations, reported rather than hidden:**
- CF02 and CF03 share one cause, and so do CF05 and CF06.
- CF09 to CF13 share one fix pattern. They exist because Atlas's D1 rule found them, so they favour Atlas by construction.

**The key check, before the pilot.** R&D re-derives 15 keys from the pinned trees:
- the 9 medium-confidence ones: CF01, CF05, CF06, CF07, RC09, TG02, TG03, WR01, WR02;
- 6 high-confidence ones drawn by `random.Random(20261013).sample(sorted(high), 6)`: DR03, DR05, FP02, FP06, RC06, RC07.

A key R&D cannot confirm is fixed or dropped, by a dated amendment.

**Checkouts.** For each task:
1. `git init`, then `git fetch --no-tags <url> <commit>` and a detached checkout. The checkout holds full history up to the pin and **no later history**, because later fix commits name the answers.
2. `atlas map` with the pinned engine, committed locally, so both arms see one current map. Many pins carry maps from older engines; the map an agent would meet today is a regenerated one.
3. A fresh copy of that checkout for every run.

**The agent** (`allow-list.json`):
- Claude Code in print mode, model Sonnet 5.5. Subagents run on Sonnet 5.5 under the standing rules.
- `--max-turns 40`, and `stream-json` output recorded whole.
- The same prompt in both arms (`prompt.md`).
- Tools are an allow-list: Read, Grep, Glob, and Bash limited to read-only `git log`, `git show`, `git grep`, `git ls-files` and `ls`. Arm B adds the `atlas` MCP server, started in the checkout from the pinned package.
- There is no Edit, Write, web search, web fetch, `gh` or network.
- `--strict-mcp-config` makes sure arm A has no MCP server at all.

**Grading (`grade.py`, standard library only):**
- **The answer** is the last top-level JSON object in the run's final text. A run with none is incorrect, and so is a refusal or a run that hits the turn cap with no answer. These are reported separately.
- **The path normal form:**
  - surrounding whitespace removed;
  - backslashes read as slashes;
  - leading `./` removed;
  - repeated slashes collapsed;
  - a trailing slash removed;
  - case kept.

  A workflow is compared by its file name alone.
- **Free text** must hold every required pattern and no reject pattern, with no limit on length (amendment 1). The reject patterns catch a hedge that names a rival cause, so an answer that lists every candidate grades wrong.
- **The tests** (`tests/test_atlas_mcp_utility_grade.py`, in rnd's suite):
  - every task's example grades correct and a perturbed one grades wrong;
  - each of the eight free-text keys has a scattershot answer that grades wrong, and grades correct once the reject rules are removed, so the hedge rule is what catches it;
  - all 15 blind answers from R&D's key audit (`key-audit.json`) grade correct.

## Metrics, pre-registered

**Primary: correctness.** Each pair is correct or incorrect in each arm. The test is an exact two-sided McNemar on the discordant pairs, α = 0.05.

**Secondary: tokens.**
- "Tokens" means the sum of `input_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens` and `output_tokens` over every turn of a run, from the run's own usage records.
- This is defined up front because the figure the harness shows for a finished agent is the last turn's context, not the total.
- The estimate is the Hodges–Lehmann estimate of the per-pair log ratio B/A, with its exact interval, as in E4b.

**Also reported:**
- **Tool calls,** with the same treatment, counted from the `stream-json` events.
- **Use of the sidecar:** the number of `mcp__atlas__*` calls in each arm-B run. The arm-B runs that called it at least once are reported apart from those that never did. A sidecar that is available but unused measures nothing about the sidecar.
- **Wall time,** recorded but not gated.
- **Precision and recall** on set-valued keys.
- **Each stratum** on its own.

**Sensitivity results.** They are read beside the primary result and never drive the decision:
1. without the 9 medium-confidence keys;
2. without CF09 to CF13;
3. with one task per correlated cause.

**Power, said plainly.** With 42 pairs, McNemar detects only a large difference in correctness (about ten discordant pairs against two). The token ratio is the more sensitive measure.

## Decision rule

- **Include `atlas mcp` in kickoffs** if either:
  - correctness is significantly better in arm B; or
  - correctness is not significantly different, B's point estimate is not lower, and the token interval lies wholly below 1.
- **Do not include it** if either:
  - correctness is significantly worse in arm B; or
  - the token interval lies wholly above 1 with no gain in correctness.
- **Otherwise, inconclusive:** kickoffs stay as they are, and the result is filed.

## The pilot

Four pairs, before the full run:
- RC03, a structure task with a known trap for grep;
- CF09, workflow breakage;
- CF02 and CF04, CI failures.

**Run-to-run noise.** RC03 and CF04 run twice in each arm. The flip rate is the share of repeated runs whose correctness differs from the same arm's first run.

**What the pilot reports to the Director before he decides on the full run:**
- its measured tokens per run against the table below, stratum by stratum;
- the flip rate;
- what share of his plan's usage the pilot took, and so what the full run will take.

## Stop rules (andon)

1. **The pilot re-prices.** If its measured tokens per run are over 1.5 times the table's for its stratum, stop and re-price before the full run.
2. **A run that fails in the harness or the service** (not a wrong answer) is retried once. If it fails again, its pair is dropped and reported. If more than 20% of runs fail this way, stop.
3. **The token ceiling.** The harness sums each run's tokens as it goes and stops at **300 million**, reporting what ran. The ceiling holds whichever way the run is billed.
4. **A plan usage limit.** If the plan's usage limit is reached, the run stops and is reported with what ran. It is never retried in a loop. A pair the limit interrupts is dropped and re-run whole later.
5. **Rig load.** The sidecar's refresh is a full map run, so runs happen only while no measurement holds a GPU grant (The Publisher's grant-start and grant-end messages).

## Price

Priced at Anthropic API rates (cached 2026-10-06), so the number compares with any other experiment. Sonnet 5.5:
- $2 per million input tokens;
- $10 per million output tokens;
- $0.20 per million cache-read tokens;
- $2.50 per million 5-minute cache-write tokens.

**Assumptions per run** (none measured yet; the pilot measures them):

| Stratum | Turns | Mean context | Tokens per run | API-rate cost per run |
|---|---|---|---|---|
| Structure | ~8 | ~45k | ~0.43M | ~$0.28 |
| Workflow breakage | ~15 | ~60k | ~1.0M | ~$0.53 |
| CI failure | ~30 | ~90k | ~2.9M | ~$1.14 |

**Totals:**

| | Runs | Tokens | At API rates |
|---|---|---|---|
| Pilot | 12 | ~21M | ~$9 |
| Full run (42 pairs) | 84 | ~77M | ~$39 |
| Re-run reserve (10%) | | ~8M | ~$4 |
| **Total** | 96 | **~105M** | **~$52** (range ~$25 to ~$150) |

About 90% of those tokens are cache reads.

**What it costs in practice.** This experiment runs under a Claude subscription plan, so the plan covers it, and the real out-of-pocket cost is far lower than the API-rate figure. It draws on the plan's usage allowance, not on dollars. The pilot measures what share of that allowance a run takes, so the full run's share is known before anyone commits to it.

The token ceiling (stop rule 3) is set at the volume $150 would buy at the rates above. It is enforced in tokens, so it holds under a plan or an API key alike.

**Wall time.** About 2 to 6 minutes per run, so roughly 4 to 6 hours run one at a time.

## What this does not measure

- Agents that write code. Every task is a read-and-answer question, because fixes would need a hidden test per task, which this bank does not have.
- Whether a person is helped by the page.
- Models other than Sonnet 5.5.
- Kickoff text that tells the agent to use the sidecar. Arm B only makes it available.

## Files

- `tasks.json`: the 42 tasks, their keys and their grading rules.
- `prompt.md`: the prompt both arms get, with the question in place of `{question}`.
- `allow-list.json`: the CLI, the model, the tools, and the two arms' MCP servers.
- `grade.py`: the grader. Its tests are in `tests/test_atlas_mcp_utility_grade.py`.
- `key-audit.json`: R&D's blind key audit, the answers and verdicts behind amendment 1.
- `run.py`: the harness (amendment 2). Its tests are in `tests/test_atlas_mcp_utility_run.py`.
- `debrief.md`: the debrief each graded run is asked after its answer is recorded (amendment 3).
- `results/`: written by the run, one record per run with its usage, answer and grade.
