# Amendment 5, 2026-10-13: the full run becomes a repository ladder

**The decision.** The Director ruled on 2026-10-13:
- **The pilot runs as pre-registered.** Four pairs, one repository per run.
- **The full run becomes a ladder.** It starts with one repository per run and adds one repository per rung.
- **Atlas is built up before any testing.** Nothing runs (probes, pilot or any rung) until the build-up release
  ships:
  - AM's CI annotations;
  - the test-file rule fix (testing-os#158);
  - multi-repository Atlas.

  Then one dated amendment moves the Atlas pin to that release, before the pilot, as the README allows. The pilot,
  rung 1 and every later rung all run on that one release.

**Why.** Every task in the 42-task bank can be answered from inside one checkout. That is probably where a map helps
least, since one repository is easy to search with grep. The Director expects Atlas to matter most when an agent has
to work across several repositories at once. A ladder measures that. Each rung adds one repository to the same
workspace, so the result is a curve: what the sidecar adds as the work spreads from one repository to two, three
and four.

This file pre-registers the ladder's structure before the pilot runs. The task banks for rungs 2 to 4 don't exist
yet. Each is written, key-checked and pinned by its own dated amendment before its rung runs. Nothing pinned for
rung 1 changes.

## The rungs

| Rung | Repositories in the workspace | Task bank |
|---|---|---|
| 1 | one: each task's own repository | the 42-task bank, as pinned in README.md (the original full run) |
| 2 | Cognate, Attestia | 5 anchors + 12 cross-repository tasks |
| 3 | Cognate, Attestia, RepoMesh | 5 anchors + 12 cross-repository tasks |
| 4 | the three, plus a fourth linked repository | 5 anchors + 12 cross-repository tasks |

**The chain.** The Director chose Cognate, Attestia and RepoMesh, three public fleet repositories built to work
together. Their links are in the code:
- **Cognate imports Attestia.** Four of Cognate's packages depend on `@mcptoolshop/attestia` (^2.0.5), the package
  Attestia publishes. Attestia's event types name Cognate as the producer of its `external` domain.
- **Cognate imports RepoMesh.** Cognate's `repomesh-bridge` package depends on `@mcptoolshop/repomesh` (^2.3.1).
  RepoMesh's own registry lists Cognate as a node that consumes three of its capabilities (registry, ledger and
  schema).
- **Cognate is R1.** It has five tasks in the 42-task bank, all high confidence, pinned at `0f8e850ba8`
  (2026-10-01). They are the anchors.
- **R4 is proposed by the Atlas session** from an edge survey and approved by R&D. One candidate is shipcheck: it is
  in the 42-task bank, it is a node in RepoMesh's registry, and RepoMesh's verify action runs it. Another is
  repomesh-license-verifier, which consumes RepoMesh's ledger.
- **Each later repository is pinned to match R1.** Its pin is the commit whose published version is the one Cognate's
  lockfile resolves at `0f8e850ba8`, or the nearest commit before 2026-10-01 if none matches exactly. The workspace is
  then one consistent state, so a question about a dependency bump has one right answer.

Rung k's workspace is rung k−1's plus one repository, so each rung adds exactly one.

**What Atlas can and cannot see across these repositories,** from Atlas 1.26.0's code (the Atlas session, 2026-10-13):
- **Each server answers about one checkout,** the one it starts in. No tool takes a repository argument, and nothing
  joins the answers of several servers.
- **Each map records some facts about other repositories,** per door:
  - the actions and reusable workflows it uses;
  - the repositories it dispatches to;
  - the packages it publishes.
- **No map records an import of another repository's package as an edge.** So "Attestia publishes X, Cognate
  imports X" can't be joined from the maps today; the agent has to join it.

Each cross-repository task is therefore labelled by whether the pinned Atlas release can see its edge (`atlas_sees_edge`: yes
or no), and results are reported for both labels. A gain on edges Atlas can't see would come from the single-repository
answers alone.

**Two kinds of task per rung:**
- **Anchors** are Cognate's five tasks from the 42-task bank, unchanged, asked again in each rung's larger workspace.
  The question doesn't change; only the number of repositories around it does. The anchors measure what the extra
  repositories cost each arm.
- **Cross-repository tasks** need the newest repository and at least one earlier one. They are of these types:
  - **cross reach:** a change to a file in one repository, and what it reaches in the others;
  - **cross door:** which workflows across the workspace run a given tool or version;
  - **cross break:** a dependency bump in one repository, and which call sites in the others break;
  - **cross CI:** a failure in one repository caused by a change in another, replayed where the fleet's history has
    one.

  Keys come from the code, workflow files, lockfiles, fix commits or run logs, **never from Atlas's output**, as in
  rung 1. R&D blind-audits a sample of each bank, at least a third of it including every medium-confidence key,
  before that rung's pin.

## What each arm gets

- **Both arms** get a fresh copy of every checkout in the rung's workspace, side by side under one workspace folder.
  Each checkout is at its pinned commit, with its own regenerated, locally committed `atlas/` map, as in rung 1.
  - The prompt names the repositories and their folders.
  - Answers write paths as `<repository>/<path>`.
  - The grader's path normal form keeps that first segment.
- **Arm A** has no MCP server, as in rung 1. It can read every committed map.
- **Arm B** adds Atlas over every repository in the workspace. With Atlas 1.26.0 that means one `atlas mcp` server
  per checkout, named for its repository, because each server answers only about the repository it starts in. Its
  tools are then `mcp__<repository>__atlas_*`, seven per repository.
- **History stays equal in both arms.** The run starts in the workspace folder, which isn't a git repository, so a
  bare `git log` or `git show` would fail in both arms. Arm B's servers would still read history through
  `atlas_changes`, the tilt amendment 2 kept `git log` to avoid.
  - So both arms get one allowed form per repository: `Bash(git -C <repository> log:*)` and
    `Bash(git -C <repository> show:*)`.
  - The Bash detector accepts `-C` only with a listed repository folder name: no slash, no `..` and no absolute path.
    It refuses every other `-C`.
  - (The Atlas session's review of #12.)
- **The isolation of amendments 2 and 4 carries over,** with the workspace folder in place of the checkout:
  - the read rules, the deny list and the Bash rules;
  - `--tools` and `--disable-slash-commands`;
  - the Atlas cache, now per server and per attempt (`<run>.cache/<repository>`), with the shared-cache guard
    covering the whole run;
  - the exact-set init check. It expects four built-ins, plus seven Atlas tools and one connected server per
    repository in arm B. The start check, the foreign-server check and the Atlas call count stop assuming one server
    named `atlas`;
  - each rung's sentinel probe, which covers the whole workspace. Arm B's probe asks every server for
    `atlas_overview`, and each must answer.
- **The anchors' answer format.** At rung 1, paths are relative to the repository. From rung 2, answers write
  `<repository>/<path>`.
  - The anchors' keys are prefixed mechanically, never re-keyed by hand.
  - The grader is tested on both forms, so a format slip can't show up as a rung effect.

**One Atlas release for the whole ladder,** the build-up release, so the rungs compare with each other. It is never
a pin bump partway up.
- **If that release serves several repositories from one server,** or joins a package one repository publishes to
  the repositories that import it, arm B uses that mode. One server per checkout, as described above, may then run as
  a comparison arm, by the pin amendment.
- **If it doesn't,** arm B is one server per checkout, as above.

The pin amendment states which, and re-states the exact-set check and the tool names to match. Wherever this file
says 1.26.0, it describes the release Atlas was at when the ladder was designed. The pin amendment replaces it.

## Climbing: one rung at a time

Rung k+1 starts only when all of these hold:
1. **Rung k is valid.** Its isolation checks are clean, no run halted it (amendment 4: an error result from the
   service halts), fewer than 20% of its attempts failed in the harness, and it stayed under its token ceiling.
2. **Rung k+1 has a mini-pilot:** two pairs, one anchor and one cross-repository task, that measure its tokens per run.
   That measurement re-prices the rung. A rung measuring over 1.5 times its estimate stops for re-pricing, as in
   rung 1.
3. **R&D has reported rung k to the Director,** with the re-priced rung k+1, and **he has given his go.**

The ladder may stop at any rung. A shorter ladder is still a result. The curve is reported as far as it goes.

## Metrics, pre-registered

**Within each rung,** the same measures as rung 1:
- correctness by exact two-sided McNemar, α = 0.05;
- tokens as the Hodges–Lehmann estimate of the per-pair log ratio B/A, with its exact interval;
- tool calls, Atlas calls and wall time.

Anchors and cross-repository tasks are reported apart.

**Across the rungs: the ladder test.** The hypothesis is directional: the sidecar's relative advantage grows as
repositories are added.
- **Primary trend: tokens on the anchors.** For each anchor pair at each rung, take log(B/A) in tokens. Rung 1's
  runs of the same five tasks are included.
  - **The test** is Page's L test for an ordered trend. Each anchor task is a block, the rungs 1 to 4 are the
    treatments, and the ordered alternative is that log(B/A) falls as the rung rises: B gets relatively cheaper as
    the workspace grows.
  - **Why this test:** comparing each task with itself keeps differences between tasks out of the trend.
  - **The p-value** is one-sided, from 10,000 permutations of the rung labels within each task, with the seed below.
    α = 0.05.
- **Arm B's fixed cost, reported beside the trend.** Every turn carries seven tool schemas per repository: 28 at
  rung 4. That cost pushes the trend toward the null, for a reason a single multi-repository server (arm C) would
  remove. So each run's first-turn input tokens are reported per arm and rung, as that fixed overhead. A flat trend
  is not read as "maps don't help across repositories" without this figure beside it.
- **Secondary trend: correctness.** Per rung, B's correct share minus A's, with exact intervals, across all of that
  rung's pairs. It is reported as a curve. There is no trend test: with 17 pairs per rung, correctness can only
  show a large effect.
- **Seed:** 20261013, as in rung 1.

## Decision rule

- **Rung 1 decides single-repository kickoffs,** by the README's rule, unchanged.
- **The ladder decides multi-repository kickoffs.** For work that spans several repositories, include one Atlas
  server per repository in the kickoff if either holds:
  - the primary trend test is significant; or
  - at rung 3 or above, a rung's correctness favours B and its token interval lies wholly below 1.

  Otherwise, multi-repository kickoffs follow rung 1's decision. A ladder that stops before rung 3 is reported and
  decides nothing beyond rung 1's rule.
- **Either result goes to the Atlas build-up.** The cross-repository tasks where arm B was wrong, or never called
  Atlas, are the evidence for what multi-repository Atlas should do next.

## Price

Priced at the API rates in README.md (Sonnet 5.5, cached 2026-10-06), so the figures compare with rung 1. Each rung
has 17 pairs, so 34 runs. Tokens per run are assumed to grow with the workspace, because more files and more Atlas
answers are read. Each rung's mini-pilot measures that growth before the rung is approved.

| Rung | Runs | Assumed tokens per run | Tokens | At API rates |
|---|---|---|---|---|
| 2 | 34 + 4 mini-pilot | ~1.5M | ~57M | ~$29 |
| 3 | 34 + 4 | ~2.0M | ~76M | ~$38 |
| 4 | 34 + 4 | ~2.5M | ~95M | ~$48 |
| **Rungs 2–4** | 114 | | **~228M** | **~$115** (range ~$57 to ~$340) |

Rung 1 is priced in README.md (~105M tokens, ~$52).

**What it costs in practice.** Like rung 1, the ladder runs on the Director's Claude subscription plan. The plan
covers it, so the real out-of-pocket cost is far lower than the API-rate figure: it draws on the plan's usage
allowance, not on dollars. Each rung's report states what share of that allowance the rung took.

**Ceilings,** enforced in tokens whichever way a run is billed:
- each rung stops at 1.5 times its re-priced estimate;
- rungs 2 to 4 together stop at 340M tokens.

## What the ladder does not measure

- Agents that write code across repositories. The ladder asks questions, like rung 1. A later rung could ask for a
  cross-repository change graded by each repository's tests, but only by its own amendment, once a bank with hidden
  tests exists.
- Repository sets without code edges between them. A workspace of unrelated repositories measures distraction, not
  cross-repository work. The anchors measure that part.
- More than four repositories. A fifth rung needs its own amendment and the Director's go.

## Who does what

- **The Atlas session** proposes R4 and writes each rung's bank and the harness changes. Each goes as a dated
  amendment by pull request, and all of these must be in place before rung 2 runs:
  - the multi-checkout workspace;
  - one server per repository, with per-server caches;
  - the per-repository `git -C` forms and their detector;
  - the generalised exact-set check and Atlas call count;
  - the prefixed anchor keys;
  - the workspace probe.
- **R&D** approves the chain, audits each bank's keys, rules on each amendment and reports each rung to the Director.
- **The Publisher** merges, and runs only outside GPU grants (stop rule 5).
