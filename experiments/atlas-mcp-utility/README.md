# atlas-mcp-utility: does `atlas mcp` help an agent answer questions about a repository?

**Status.** Pre-registration, 2026-10-13. Nothing has run.
- R&D approved the design on 2026-10-13, with seven additions that are folded in below.
- The Director approved pricing it and chose to run it on his Claude plan.
- The pilot runs once the key check below is done. The full run needs his go after he has seen what the pilot measured.

## The question and the decision it feeds

Do coding agents answer real questions about fleet repositories correctly more often, or at lower cost, when the Atlas MCP sidecar (`atlas mcp`, `@dogfood-lab/atlas`) is available?

**The decision:** whether agent kickoffs include `atlas mcp`. Under the org rule, every fleet repository already commits its `atlas/` map, and an agent can read those files without the sidecar. So this measures **what the sidecar adds over the committed map**, not what the map adds over nothing.

**Prior art:** Gloaguen et al. 2026 (arXiv:2602.11988) found that repository context files such as AGENTS.md did not generally raise coding agents' success and raised inference cost by over 20% (as cited in testing-os `docs/atlas-sidecar.dispatch.md`). The sidecar was built to be queried, not pasted into every session. Whether that design escapes the cost has not been measured.

## Pinned before any run

Each sha256 is of the file as committed, with LF line endings (`.gitattributes`).

| What | Pin |
|---|---|
| `tasks.json` | `cedfb958e51ee1ef9548727c5e5e10e9118fc8e21459b8adfe41c7a9d63d5af8` |
| `prompt.md` | `a32c1c8f30e88f7264e6efce1d1c608339368b2e44691870206b3105e4e6226d` |
| `allow-list.json` | `d1ffe5045ed157942151961c76a649a754e72f4589df87a98e13e7869414bae5` |
| `grade.py` | `ab006b0bf0b227a63bff53126e6a8881de52d321d2af75b713464ea7ca478538` |
| Claude Code CLI | 2.1.197 |
| Model | `claude-sonnet-5-5`, at the CLI's default effort for it |
| Atlas | `@dogfood-lab/atlas` 1.26.0 |
| Seed (arm order, key draw) | 20261013 |

A pin changes only before the pilot, and only by a dated amendment here that says why. One example: R&D's key check fixing a key, which changes `tasks.json`'s hash. Another: Atlas 1.27.0 shipping first. After the pilot's first run, nothing pinned changes.

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
- **Free text** must hold every required pattern, no reject pattern, and at most a stated number of words. The reject patterns catch a hedge that names a rival cause, so an answer that lists every candidate grades wrong.
- **The tests** (`tests/test_atlas_mcp_utility_grade.py`, in rnd's suite):
  - every task's example grades correct and a perturbed one grades wrong;
  - each of the eight free-text keys has a scattershot answer that grades wrong, and grades correct once the reject rules are removed, so the hedge rule is what catches it.

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
- `results/`: written by the run, one record per run with its usage, answer and grade.
