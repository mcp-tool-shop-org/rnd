# atlas-mcp-utility: does `atlas mcp` help an agent answer questions about a repository?

**Status:** pre-registration draft, 2026-10-13, for R&D's review. Nothing has run. The Director approved pricing it. **Running it needs his go on the budget below.**

## The question and the decision it feeds

Do coding agents answer real questions about fleet repositories correctly more often, or at lower cost, when the Atlas MCP sidecar (`atlas mcp`, `@dogfood-lab/atlas`) is available?

**The decision:** whether agent kickoffs include `atlas mcp`. Under the org rule, every fleet repository already commits its `atlas/` map, and an agent can read those files without the sidecar. So this measures **what the sidecar adds over the committed map**, not what the map adds over nothing.

**Prior art:** Gloaguen et al. 2026 (arXiv:2602.11988) found that repository context files such as AGENTS.md did not generally raise coding agents' success and raised inference cost by over 20% (as cited in testing-os `docs/atlas-sidecar.dispatch.md`). The sidecar was built to be queried, not pasted into every session. Whether that design escapes the cost has not been measured.

## Design

**Pairs.** Each task runs twice:
- arm A, without `atlas mcp`;
- arm B, with it.

Everything else is the same in both arms: model, prompt, checkout, tool allow-list, CLI version, and settings. The order of the two arms within each pair comes from a seeded random draw (seed recorded). Both runs of a pair go back to back, so drift in the service lands on both.

**Tasks.** `tasks.json` holds 42 tasks from 17 public fleet repositories, each pinned to a commit. The bank was built on 2026-10-13. Each task carries:
- the question as the agent gets it, ending in the JSON shape of its answer;
- the answer key and how it is checked;
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
- CF09 to CF13 share one fix pattern. They exist because Atlas's D1 rule found them, so they favour Atlas by construction. Their keys were re-derived independently from the lockfiles and the fix diffs.

**Checkouts.** For each task:
1. `git init`, then `git fetch --no-tags <url> <commit>` and a detached checkout. The checkout holds full history up to the pin and **no later history**, because later fix commits name the answers.
2. `atlas map` with the engine under test, committed locally, so both arms see one current map. Many pins carry maps from older engines; the map an agent would meet today is a regenerated one.
3. A fresh copy of that checkout for every run.

**The agent.**
- Claude Code in print mode (`claude -p`), model `claude-sonnet-5-5`. Subagents run on Sonnet 5.5 under the standing rules.
- The CLI's default effort for that model at the pinned CLI version. The version and the effective settings are recorded from each run.
- `--max-turns 40`.
- The same prompt template in both arms: answer one question about the repository in the working directory, using the tools given, and end with one JSON object in the stated shape.
- Tools are an allow-list: Read, Grep, Glob, and Bash limited to read-only `git log`, `git show`, `git grep`, `git ls-files` and `ls`. Arm B adds `mcp__atlas__*`, from the sidecar started in the checkout at the pinned Atlas version.
- There is no Edit, Write, web search, web fetch, `gh` or network.
- `--strict-mcp-config` makes sure arm A has no MCP server at all.

**Grading.**
- The answer is the last JSON object in the run's final text. A run with no parseable object is incorrect.
- `grade.py` (standard library only) applies each task's `check_method`. It lands on this pull request before any run, with tests that every key grades correct and a perturbed key grades wrong. Its sha256 is recorded here when it lands, and nothing about grading changes after the first run.
- A refusal, or a run that hits the turn cap with no answer, counts as incorrect in either arm and is reported separately.

## Metrics, pre-registered

**Primary: correctness.** Each pair is correct or incorrect in each arm. The test is an exact two-sided McNemar on the discordant pairs, α = 0.05.

**Secondary: tokens.**
- "Tokens" means the sum of `input_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens` and `output_tokens` over every turn of a run, from the CLI's JSON result.
- This is defined up front because the figure the harness shows for a finished agent is the last turn's context, not the total.
- The estimate is the Hodges–Lehmann estimate of the per-pair log ratio B/A, with its exact interval, as in E4b.

**Also reported:**
- tool calls (same treatment, counted from the `stream-json` events);
- the CLI's `total_cost_usd`;
- wall time, recorded but not gated;
- precision and recall on set-valued keys;
- each stratum on its own;
- a sensitivity run with one task per correlated cause.

**Power, said plainly.** With 42 pairs, McNemar detects only a large difference in correctness (about ten discordant pairs against two). The token ratio is the more sensitive measure.

## Decision rule

- **Include `atlas mcp` in kickoffs** if either:
  - correctness is significantly better in arm B; or
  - correctness is not significantly different, B's point estimate is not lower, and the token interval lies wholly below 1.
- **Do not include it** if either:
  - correctness is significantly worse in arm B; or
  - the token interval lies wholly above 1 with no gain in correctness.
- **Otherwise, inconclusive:** kickoffs stay as they are, and the result is filed.

## Stop rules (andon)

1. **The pilot comes first:** 4 pairs, one from each stratum plus a second CI failure. If the pilot's measured cost per run is over 1.5 times the estimate below, stop and re-price before the full run.
2. **A run that fails in the harness or the service** (not a wrong answer) is retried once. If it fails again, its pair is dropped and reported. If more than 20% of runs fail this way, stop.
3. **Spending reaches the approved ceiling:** stop where it is and report what ran.
4. **Rig load.** The sidecar's refresh is a full map run, so the experiment runs only while no measurement holds a GPU grant (The Publisher's grant-start and grant-end messages).

## Price

**Rates (Anthropic API, cached 2026-10-06).** Sonnet 5.5:
- $2 per million input tokens;
- $10 per million output tokens;
- $0.20 per million cache-read tokens;
- $2.50 per million 5-minute cache-write tokens.

**Assumptions per run** (none measured yet; the pilot measures them):

| Stratum | Turns | Mean context | Cache reads | Cache writes | Output | Cost per run |
|---|---|---|---|---|---|---|
| Structure | ~8 | ~45k | 0.36M | 60k | 6k | ~$0.28 |
| Workflow breakage | ~15 | ~60k | 0.9M | 90k | 12k | ~$0.53 |
| CI failure | ~30 | ~90k | 2.7M | 140k | 25k | ~$1.14 |

**Totals:**

| | Runs | Estimate |
|---|---|---|
| Pilot (4 pairs) | 8 | ~$6 |
| Full run (42 pairs) | 84 | ~$39 (structure $16, breakage $6, CI failures $16) |
| Re-run reserve (10%) | | ~$4 |
| **Total** | 92 | **~$49** (range ~$25 to ~$150) |

**Token volume.** About 90 million tokens processed in all, about 90% of them cache reads.

**The ceiling to approve:** $150 at API rates, enforced by stop rule 3.

**On Opus 5.5 instead** ($4 input, $20 output, $0.20 cache read, $5 cache write), the full run is about $63, about $80 with the pilot and the reserve, with a ceiling of $250.

**Which account pays is the Director's call:**
- An API key bills these dollars.
- Running under his Claude plan bills nothing directly, but uses the same volume of his plan's usage.

**Wall time.** About 2 to 6 minutes per run, so roughly 4 to 6 hours run one at a time.

## What this does not measure

- Agents that write code. Every task is a read-and-answer question, because fixes would need a hidden test per task, which this bank does not have.
- Whether a person is helped by the page.
- Models other than Sonnet 5.5.
- Kickoff text that tells the agent to use the sidecar. Arm B only makes it available.

## Files

- `tasks.json`: the 42 tasks with their keys.
- `grade.py` and its tests: land before any run.
- `results/`: written by the run, one record per run with its usage, answer and grade.
