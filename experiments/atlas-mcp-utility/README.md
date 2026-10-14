# atlas-mcp-utility: does `atlas mcp` help an agent answer questions about a repository?

**Status.** Pre-registration, 2026-10-13. Nothing has run.
- R&D approved the design on 2026-10-13, with seven additions that are folded in below.
- The Director approved pricing it and chose to run it on his Claude plan.
- The pilot runs once the key check below is done. The full run needs his go after he has seen what the pilot measured.
- **Amendment 5 (2026-10-13):** the full run becomes a repository ladder. Rung 1 is the 42-task bank below, unchanged. Each later rung adds one linked repository to the workspace. See [ladder.md](ladder.md).
- **Amendment 6 (2026-10-13):** Kimi K3's consult. CF09 to CF13 leave the decision set, cut-list misreads are reported, and the ladder decides on its cross-repository tasks. See below and ladder.md.
- **On hold (2026-10-13):** the Director ruled that Atlas is built up before any testing. The probes and the pilot wait for the build-up release, and a dated amendment moves the Atlas pin to it before the pilot.
- **Amendment 7 (2026-10-13):** every attempt runs at medium effort, and the probes, pilot and ladder run in a mountless local Docker sandbox on the Director's plan instead of on the rig. See below.

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
| `allow-list.json` | `5ff2761451034917592411206c84153c68fa50e8278c20900fc3230c47511338` (amendment 7) |
| `grade.py` | `f6d09f5144b42fc1c86f632015de33c84d0bfb9dd3faf2f192cb47d24d864455` (amendment 1) |
| `debrief.md` | `ed73ef0864f6b603f32ab3f4a91874c465d537779ff1450094bc82690d312f8c` (amendment 3) |
| Claude Code CLI | 2.1.197 |
| Model | `claude-sonnet-5-5`, at medium effort (`--effort medium`, amendment 7) |
| Where it runs | the local Docker sandbox `atlas-pilot`, on the Director's plan (amendment 7) |
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

### Amendment 4, 2026-10-13: each run starts with exactly its arm's tools

**What the first probe found.** The probes ran at 13:24 and failed closed with 0 tokens spent. The CLI's sign-in had gone stale, so every call answered 401, and the Director signed in again. But the init events recorded before the 401 showed something the isolation in amendment 2 had missed:
- Arm A's start offered 27 built-in tools, 15 skills and 30 slash commands. Among the tools were SendMessage, PushNotification, PowerShell, Workflow, CronCreate, RemoteTrigger and Skill.
- `--allowedTools` only pre-approves. It removes nothing, so any tool that runs without a permission prompt was open to the model. SendMessage could have reached the other Claude sessions live on the rig.
- The isolation check read only MCP tools and the model, so it passed.
- Nothing ran past the init, so nothing leaked.

**The isolation now** (R&D's ruling, with its five conditions):
1. **`--tools "Read,Grep,Glob,Bash"` and `--disable-slash-commands`.** These decide which built-ins exist at all. The allow and deny rules of amendment 2 stay, and still gate the four that remain. Both flags exist in the pinned CLI 2.1.197.
2. **The start must match its arm exactly.** A run fails the isolation check, and stops the pilot, if any of these differ from its arm:
   - the init's tool list: the four built-ins, plus the seven Atlas tools named in `allow-list.json` in arm B;
   - skills or slash commands, of which there must be none;
   - the MCP servers: none in arm A, and `atlas`, connected, in arm B;
   - the model or the CLI version.

   Each direction, a tool too many and a tool missing, is tested on the real starts captured on 2026-10-13 (`tests/fixtures/atlas_mcp_utility/`). The first probe's starts must be refused; the restricted ones must pass.
3. **Arm B's Atlas caches inside the attempt.** `atlas_refresh` writes its snapshots to `%LOCALAPPDATA%\atlas`, outside the checkout, where the wrote-a-file check cannot see them, and every run shared that cache.
   - The server now starts with `LOCALAPPDATA` and `XDG_CACHE_HOME` set to `<work>/runs/<run>.cache`, created empty before each attempt, retries included.
   - A guard fails the run if the shared cache changed while it ran, in case the override ever does not take. The guard fails closed: no other session may call `atlas_refresh` while the pilot runs.
4. **Any error result stops the pilot,** with its text in the report. A stale sign-in is named as such, with the command that fixes it.
   - **The turn cap is not an error.** The CLI ends a capped run with an error result (`error_max_turns`), but the cap is the agent's own outcome. As "Grading" says, such a run is incorrect and reported apart. The harness had been retrying it as a harness failure; now it grades it.
   - **Only a run with no result at all is retried once:** a crash, or the watchdog. This narrows stop rule 2.
5. **The probe report names each run's outcome, exit code and CLI version, and any error,** with planted values masked. Arm B's probe passes only if its `atlas_overview` call returns a result that is not an error: with no ToolSearch, that call proves the Atlas tools work as they start.

**Unchanged.** The start still lists the agent types, but with no Task tool none can be started. It also still names an auto-memory path under `C:/Users`, the same in both arms; Write and Edit are denied, and so is Read under `C:/Users`.

**A known defect at the pin.** At 1.26.0, Atlas's test-gap rule does not take `test_*.mjs` for a test file. At role-os `fc5222ae78`, `atlas gaps` names the two `.py` scripts no workflow runs, and not the two `.mjs` ones. TG02's key holds all four, so arm B is handed half an answer there. The pin stays, as pre-registered. The defect is filed as dogfood-lab/testing-os#158, and the pilot's report names it under `known_defects_at_the_pin`.

`allow-list.json` is re-pinned above. `tasks.json`, `prompt.md`, `grade.py` and `debrief.md` are unchanged.

### Amendment 6, 2026-10-13: an outside model's consult

The Director asked for an outside model's view before Atlas is built up and anything runs. Kimi K3 wrote its own
design blind, then critiqued this experiment, the ladder and R&D's design ruling. R&D's rulings on each point are in
the research-grounding entry. What changes for rung 1:
- **CF09 to CF13 leave the decision set.** They exist because Atlas's D1 rule found them, so they favour Atlas by
  construction. Keeping them only as a sensitivity result still let them drive the decision.
  - The primary analysis now runs on the other 37 pairs.
  - The five are reported apart.
  - The old sensitivity result "without CF09 to CF13" becomes "with them".
- **A pattern is named and reported:** an arm-B run that acts on a cut Atlas list (`complete: false`) as if it were
  whole, without following its cursor, and grades wrong. A tool that answers confidently but incompletely can do
  worse than an honest "can't tell", and that should be visible, not buried in the totals.
- **A threat is named, not fixed:** one pinned engine for every run means a map defect lands on every arm-B run at
  once, as the `test_*.mjs` gap does for TG02 at 1.26.0. Known defects at the pin are listed in every report, as
  amendment 4 began.

The ladder's changes are in [ladder.md](ladder.md), under amendment 6. Nothing pinned above changes.

### Amendment 7, 2026-10-13: medium effort, and the runs move into a local sandbox

Nothing has run since amendment 4's probe failed closed. These change the pins before any probe, under the Director's rulings of 2026-10-13.

**1. Effort is medium.** Every attempt passes `--effort medium`, which the pinned CLI 2.1.197 accepts.
- The init event does not echo the effort, so the run check can't read it from the stream. Each record takes it from the allow-list the command was built from.
- The price below assumed the CLI's default effort, so it stays an upper bound.

**2. The runs move from the rig into the local Docker sandbox `atlas-pilot`.** That covers the probes, the pilot and every rung of the ladder, in one environment, so no comparison mixes the rig with the sandbox.
- **What it is:** its own Linux VM, with no host folder mounted at all. Its network policy is Balanced: deny by default, common development hosts allowed.
- **Inside it:**
  - the pinned CLI in `/opt/claude-pin`;
  - Atlas in `/opt/atlas-tools`, the `--tools` directory;
  - an empty `/work`;
  - this directory, brought in by `git archive`.
- **The model ruling:** the Director ruled out any paid per-token model API. The sandbox signs in with the claude kit's `/login` on his plan. The sign-in is held on the host and never enters the sandbox.
- **Why it's better:** the containment of amendment 2 was a set of deny rules over trees the agent could otherwise reach. In the sandbox, the operator's files, memory notes and other repositories aren't there to reach. The deny rules stay, as a second layer.
- **Its own load:** the VM runs on the rig's CPU and memory. No probe, pilot or ladder run starts while interlock holds a measurement grant, because its CPU and iGPU arms are timed on that same machine. The Publisher, who holds the grants, schedules the runs.

**3. What the run check now requires, beside amendment 4's:**
- **`permissionMode` is `default`, and the command passes `--permission-mode default`.** The sandbox kit's own user settings set `bypassPermissions`. `--setting-sources local` must keep them out, and this proves it did.
- **`apiKeySource` is `none`.** A run that starts on an API key breaks the Director's ruling and stops the pilot.
- **The CLI version is the pin.** The image's own Claude Code is 2.1.296 and updates itself. The pinned 2.1.197 in `/opt/claude-pin/bin` comes first on PATH. The preflight's `--version` check and the init check both refuse any other version, and the harness starts the CLI with `DISABLE_AUTOUPDATER=1`.

  The pin amendment after the Atlas release moves the CLI to 2.1.296 or later. `/opt/claude-pin` is then reinstalled at that version, and the image's self-updating copy is still never the one run.

**4. The containment probe, rewritten for the sandbox (amendment 2's threat model):**
- **The answer keys are the secret that matters there.** `tasks.json` sits in this directory under the sandbox user's home, so the probe now plants its two sentinels in this directory itself (target "experiment"), beside the keys. It also plants them in the home directory, and in `E:/AI` and `D:/` when those exist, as on the rig.
- **The `git -C` route names a repository the probe makes under the home directory.** Its commit and message are secrets, and it's removed afterwards. `E:/AI/testing-os` doesn't exist in the sandbox.
- **`Read(//proc/**)` joins the denied reads,** as a second layer over a process's environment.
- **The template clones:** whether `prepare()` reaches github.com under Balanced is untested. The probe's own template is the first test of it: a failed fetch stops the probe before any agent runs. If Balanced refuses, github.com is allowed by name, and that is recorded here.

**5. Recorded per run:** the effort, the permission mode and whether the run signed in on the plan (`on_the_plan`, a yes or no), beside the CLI version. The init's own key-source value is never written to a record or a message.

`allow-list.json` is re-pinned above. `tasks.json`, `prompt.md`, `grade.py` and `debrief.md` are unchanged. Every amendment-4 check stands. The hold for the Atlas release, and the Director's go on the plan and its ceiling, are unchanged.

### Amendment 8, 2026-10-13: a shakedown to price the runs, and containment by permission, not by rule

**Why there's a shakedown, not a pilot.** The Director gave his go for the pilot. But a pre-registered pilot freezes every pin at its first run, and today that would freeze the ladder at Atlas 1.26.0 and CLI 2.1.197. 1.26.0 has none of the multi-repository surface the ladder tests, and the release changes the tools' output (the Atlas session's facts, 2026-10-13). 2.1.197 has the `--tools` gap 2.1.295 fixed. So the graded pilot still waits for the release and the pin amendment. What runs now is a **shakedown**:
- the pilot's tasks and harness, run with `--label shakedown`;
- written to `results/shakedown/`;
- never part of the decision, and freezing no pin.

**Its purpose (the Director's).** Price the Sonnet runs, and judge whether a local model is the more feasible route for the ladder. It has two legs on identical tasks:
- **The Sonnet leg,** in `atlas-pilot` on the plan, as amendment 7 set up. Per run, by stratum:
  - tokens;
  - the CLI's own `total_cost_usd`: the API-rate dollar figure, the common unit, though the plan covers it;
  - wall time;
  - correctness, by the pinned grader;
  - turn-cap hits.

  The Director reads his plan's usage before and after, for the share the shakedown took.
- **The local leg,** through the studio's `claude-ollama-local` kit. That's real Claude Code, with every model alias mapped to `nemotron-3.5-lightning` on the rig's Ollama: tools, a 131k context, about 24 GiB. Per run:
  - wall time;
  - GPU time, from the host's Ollama log over the run's window, gathered by the Publisher;
  - tokens;
  - correctness, by the same grader;
  - turn-cap hits;
  - tool-use failures.

  Its cost unit is GPU-hours, with a dollar equivalent at the price offrig quotes for a comparable rented card, labelled as an equivalent.

  It runs only after a one-call check that a local sandbox reaches the host's Ollama. Each run needs a 5090 grant from the Publisher, and none overlaps an interlock measurement. Its start check is a local variant: the base URL is `host.docker.internal`, the key source is the kit's placeholder, and no Anthropic key is present. It's written once that leg's real start has been captured.
- **If the ladder moves to a local model,** its question changes from Claude Code with Sonnet to Claude Code driven by that model. A dated amendment says so before the graded pilot.

**What the sandbox probe found (2026-10-13, 96,139 tokens, failed closed).** One leak in containment: a Grep with its path at the home directory itself returned files under it, both hidden sentinels among them. `Read(~/**)` matches paths under the home directory, not the directory, and a recursive search started there is not filtered file by file. A Grep at `/` or `/home` would do the same. The rig's plan had this shape too, and was never probed past its sign-in.

So deny rules can't be the guarantee. And more than `tasks.json` is at stake:
- **This README names answer keys.** Amendment 1 discusses WR02's key and CF06's cause.
- **`key-audit.json` holds answers.**
- **`/work/runs` keeps every earlier run's stream and record.** Arm B could read arm A's answer to the same task.

**The containment, by permission or absence, not by rule:**
1. **No key material is readable by the agent's process.** That means this whole directory.
2. **No other run's stream, record or debrief is readable by a run.**
3. **The probe proves both.** It adds Grep routes at `/`, `/work` and the home directory, and plants sentinels in a fake earlier run under `/work/runs` and beside the results. Every one must be unreachable.

The deny rules stay as a second layer that counts for nothing on its own.

**The mechanism: one sandbox, two users** (chosen on the sandbox's facts, measured by the Publisher on 2026-10-13).
- **The facts behind the choice:**
  - The kit's own user, `agent`, has passwordless sudo, so it can't be the user an attempt runs as.
  - A second user can run the pinned CLI on the plan, given one file copied from `agent`: `~/.claude/.credentials.json`. It holds placeholders only, since the real sign-in is injected at the sandbox's proxy. `~/.claude.json` holds the account's identity, and is never copied.
  - A fresh sandbox per attempt would also work (4.6 s to create, no `/login`). But it would mean rebuilding the image and driving every attempt through `sbx exec` from Windows, so one sandbox with two users keeps the tested harness.
- **The harness runs as root** (`sudo … run.py --run-as amu`). Everything it writes is private: it sets umask 077, and its git calls read the run user's checkout with `safe.directory=*`.
- **Each attempt's CLI runs as `amu`** (`runuser -u amu`):
  - a user with no sudo and no privileged group;
  - its environment holds only `HOME`, `USER`, `LOGNAME`, `PATH`, `LANG`, `DISABLE_AUTOUPDATER`, `DISABLE_TELEMETRY`
    and `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, plus the sandbox proxy (`HTTPS_PROXY`, `HTTP_PROXY`,
    `NO_PROXY` in both cases, `NODE_USE_ENV_PROXY`) and the CA that proxy presents (`NODE_EXTRA_CA_CERTS`,
    `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`). The placeholder sign-in works only through that proxy. `GH_TOKEN`, the
    MCP gateway, SSH agents and the sandbox's own variables stay out;
  - before each attempt its home is emptied, and a fresh copy of the placeholder sign-in file is installed from a
    root-only copy (`--run-as-credentials`, 0600). A failed sign-in blanks the file, and a blanked file would fail
    every later attempt the same way;
  - its checkout, Atlas cache and MCP config are given to it for that attempt alone, then handed back to root and closed (0700 and 0600). No later attempt can read them.
- **The preflight refuses to start unless all of these hold:**
  - the harness is root;
  - the run user has no sudo and no privileged group;
  - this directory is root-owned 0700, which means it lives outside every home (`/srv/atlas-mcp-utility` in the sandbox);
  - the work directory is root-owned, with others allowed only to pass through (0711);
  - root's home and every other home are closed to others.
- **The probe:**
  - plants sentinels in this directory, root's home, every other home, and a fake earlier run under `/work/runs`;
  - asks for Grep at `/`, at the work directory and at `/home`, beside every earlier route;
  - passes only if nothing comes back.

**The first mechanism-A probe (2026-10-13) failed closed with 0 tokens.**
- The preflight first refused a third home (`/home/ubuntu`, 0750), which was then closed.
- Both runs then answered "Not logged in": the CLI's environment had dropped the sandbox proxy, so the
  placeholder sign-in went direct and was refused.
- Nothing leaked, and no tool ran.
- The environment now carries the proxy set, and the sign-in file is installed fresh before every attempt.

**Recorded for the pin amendment:**
- On the image's 2.1.296, `--model claude-sonnet-5-5` prints `unrecognized_model` but still answers.
- A 4-token reply carried about 27,700 cached tokens (3,436 written, 24,274 read): the system prompt and tools. It belongs in every run's price.

**For the local leg:**
- It runs on the same pinned CLI (2.1.197), not the kit image's own 2.1.280, so the two legs differ only in the model.
- The egress rule that works is `localhost:11434`. The kit's `host.docker.internal:11434` didn't match the filter.
- The kit's init reported its model with a `[1m]` suffix, so the first real call confirms that Ollama loads `nemotron-3.5-lightning` by its own name.

**Two checks added to the harness:**
- **Every tool a run calls, task and debrief, must be one its arm starts with** (`tool_use_problems`). The init alone can't show tools that 2.1.197 registers later.
- **Arm B may start with `atlas` pending and no Atlas tools.** The probe's arm B did, then called `atlas_overview` and got its answer. Each record keeps `atlas_status_at_init`, so the shakedown shows how often a first turn begins without Atlas.

**Order:**
1. The containment fix.
2. A passed re-probe.
3. The Sonnet leg.
4. The reachability check.
5. The local leg.

Nothing in the shakedown is graded into the decision, and nothing it runs freezes a pin. Nothing pinned changes in this amendment.

### Amendment 9, 2026-10-13: read-only shell in the checkout is part of the measured surface

**What stopped the first shakedown (19:12–19:14 EDT, 500,465 tokens).**
- Four RC03 runs answered correctly:
  - arm A: 59,769 and 60,143 tokens;
  - arm B: 71,683 and 71,142, with `atlas` pending at the start.
- The fifth, CF09-A1, made chained shell reads of its own checkout (`cd …; ls …; grep … | head`, then `sed -n …`), and the pinned CLI ran them. That CLI auto-approves its own read-only commands inside the working directory, though the allow-list names only `git log` and `git show`.
- Its next two calls (`awk`, and `node -e`) were refused as needing approval.
- Nothing was written: `git status` was empty.
- Amendment 2's Bash detector stopped the run on the `;` and `|`, as written.

**The ruling.**
- **Reach:** these reads reach nothing the run's Read, Grep and Glob don't already reach. The run user's file permissions are the containment (amendment 8), and they hold.
- **Behaviour:** it's what the pinned CLI does, and what an agent kickoff runs with.
- **So the in-checkout read-only shell is part of the measured surface, in both arms.** Each run records `shell_reads`, its Bash calls that weren't git, so the analysis shows how much each arm leaned on it.

**The detector now stops a run only on a form that:**
- **writes a file:** `>` or `>>` (but not to `/dev/null`, and not a descriptor duplication such as `2>&1`), `--output`, `tee`, or `find -delete`;
- **runs a command the shell doesn't wait for:** a background `&`, or `find -exec`;
- **substitutes a command's output:** `$(…)` or backticks.

A chain, a pipe, a line break and `<` no longer stop a run. The CLI refuses any part of a chain that isn't one of its read-only commands, as the shakedown showed with `awk` and `node`.

**One more guard:** before and after every attempt, the harness removes everything the run user owns under `/tmp`, `/var/tmp` and `/dev/shm`. A read-only chain can't write there, but nothing an attempt leaves behind should survive to the next.

**What follows:** the shakedown runs again from the start, with all its runs on the new rule. The four RC03 runs above are kept as the first price signal. Nothing pinned changes.

### Amendment 10, 2026-10-13: a local route first, refused calls stop nothing, and recorded streams replay

**What stopped the second shakedown (19:22–19:24 EDT, 515,852 tokens).**
- The four RC03 runs answered correctly again, with no shell reads:
  - arm A: $0.0804 and $0.0802 at API rates, 11.0 s and 10.6 s;
  - arm B: $0.1176 and $0.1145, 13.1 s and 11.7 s, with `atlas` pending at the start.
  - That is about 60,000 to 71,000 tokens a run, against the price table's 0.43 million for the stratum.
- CF09-A1 answered too, in 7 turns ($0.1235). One of its calls held `sed -n "$((n-12)),${n}p"`.
  - That is arithmetic expansion, not command substitution. The detector read its `$(` as a substitution and stopped the shakedown.
  - The CLI had refused that call anyway, and one other for its `sort -u -k3` part. Nothing was written.
- The report named the halt but not the call that caused it. Only the per-attempt record did.

**The Director's ruling:** a detector bug is not to be found on the plan again. The harness is shaken down on the local model first, which costs GPU time, not the plan. Sonnet runs again only after a clean local pass, and with the Director's go.

**R&D's rulings on the detector:**
1. **Arithmetic expansion stops nothing.** `$((…))` runs no command, and its `<` and `>` compare. One that holds a `$(` still counts as a substitution.
2. **Only a call that ran can stop a run.** Amendment 9's "a run that makes any of these calls" becomes "a run in which any of these calls ran".
   - A call the CLI refused, as listed in its result's `permission_denials`, wrote nothing and ran nothing.
   - Every refused call, of any tool, is kept in the record's `refused_calls`. It is the agent's own behaviour, reported and never a stop.
   - `is_error` alone never proves a refusal: a command that ran and exited non-zero carries it too. A run with no result lists no refusals, so every stopping form in it counts as run.
3. **A halt names its cause.** The report's `halt_error` carries the stopped run's isolation problems.

**The local route** (`--route local`, accepted only with `--pilot --label shakedown`):
- **What changes is the model alone.** The CLI (2.1.197), tasks, prompt, tools and permission rules are the same.
  - The model is `nemotron-3.5-lightning:latest`, served by Ollama on the host at `http://host.docker.internal:11434` with Ollama's placeholder token.
  - Every model alias and the subagent model point to it. There is no `--effort`, which means nothing to it.
- **The plan is out of reach.** No sign-in file is installed. A run whose result names a Claude model in `modelUsage` stops.
- **The start check:** the local model (with or without a `[1m]` suffix), `apiKeySource` none, and the default permission mode.
  - The pinned CLI's start on this route was captured against a closed port, so no model loaded: the model as passed, `apiKeySource: none`, and the four built-ins. It is a test fixture.
- **The records:** `route` is `local`, and the effort, `on_the_plan` and `total_cost_usd` are null, meaning not applicable.
  - Each run also records `started_at` and `ended_at`, so its GPU time can be read from the host's Ollama log for that window.
  - The price unit is wall time plus GPU time.
- **Results** go to `results/shakedown-local/`. They never count toward the decision.

**Replay.** `run.py --replay <run>.jsonl …` puts recorded streams through the same checks a live run gets (`run_checks`), with no CLI.
- Shakedown 2's five streams are test fixtures, with the plan's rate-limit events dropped.
- Under these rulings, CF09-A1 answers with its two refused calls reported, and the four RC03 runs pass.
- Shakedown 1 kept only its records. Its first stopping call passes under amendment 9; the others were cut at 120 characters inside a quote, so they can't be replayed.

**Order:** the local shakedown, then a clean local pass, then the Director's go, then Sonnet. Nothing pinned changes.

### Amendment 11, 2026-10-13: Haiku partners the local model, the local model gets its context, and a refused out-of-set call stops nothing

**The first local shakedown (19:40–19:45 EDT, nemotron-3.5-lightning, about 280 s of GPU load, peak 27,114 MiB).**
- **RC03: 1 of 4 correct**, where Sonnet got 4 of 4. The flip rate was 1 of 2.
  - Input tokens ran from 232,000 to 1.18 million a run. Ollama does no prompt caching, so every turn re-sends the whole context, and its Anthropic endpoint reports no output tokens.
- **Ollama loaded the model at 32,768 tokens of context,** of which the CLI's system prompt and tools take about 25,000 to 28,000. That alone may explain much of the accuracy.
- **CF09-A1 halted on a call to `Edit`,** a tool its arm doesn't have. The CLI had answered "No such tool available", so nothing ran.
  - It also tried to write with `sed -i`, `ed` and redirections, and to run code (`node -e`, `npx`, `npm run build`). The CLI refused every one, and `git status` stayed empty.

**Rulings:**
1. **A refused out-of-set call stops nothing (R&D).**
   - The CLI's "No such tool available" answer is a refusal, the same as a permission denial: the call never ran. It goes to `refused_calls`.
   - An out-of-set call that ran still stops the run.
   - Replayed under this rule, all five local runs pass the checks. CF09-A1 reaches the turn cap and is graded incorrect, with 17 refused calls.
2. **Haiku is the plan-side partner for the local model (the Director's ruling).** The new `haiku` route runs `claude-haiku-5-5` on the plan, for the shakedown only. Results go to `results/shakedown-haiku/`.
   - Haiku runs at its own default effort, like the local model. That the pinned CLI accepts `--effort` for Haiku is unproven, and a refusal would cost a run on the plan.
   - The Sonnet RC03 runs stay as the Sonnet price signal, at about 8 to 12 cents a run at API rates.
3. **The local model runs at a pinned context.**
   - The model is now `nemotron-3.5-lightning-131k`, built `FROM nemotron-3.5-lightning:latest` with `PARAMETER num_ctx 131072`.
   - The harness refuses to start the local route unless Ollama's `/api/show` gives that `num_ctx`. That call loads nothing onto the GPU.
   - Each local run records `context_length` from `/api/ps` as it ends.
   - Before the derived model runs, a fill check must show that 131,072 fits the card. If it doesn't, the pin moves down by amendment.
4. **The local leg is priced by wall time and GPU time only.** Its token counts are input only, and uncached.

Nothing pinned changes.

### Shakedown results, 2026-10-13: Haiku against the local model, and arm B never had Atlas

Both legs ran the same six pairs (RC03 ×2, CF09, CF02, CF04 ×2) on CLI 2.1.197 with no halt, no dropped pair and no harness failure.

| | Haiku 5.5 (plan, `haiku-1`) | nemotron-3.5-lightning, 131k context (local, `local-2`) |
|---|---|---|
| Correct | 12 of 12 | 11 of 12 (CF02-A1 wrong) |
| Flips on repeats | 0 of 4 | 0 of 4 |
| Wall time per run | 15–77 s (408 s in all) | 17–42 s (319 s in all) |
| Price | $3.10 at API rates for the 12 task turns, about $0.26 a run; the plan covers it | no plan use; about 6 minutes of GPU time at a peak near 28 GB |
| Tokens | 2.41 million, mostly cache reads | 2.80 million input, uncached |
| Tool calls per run | 2–18 | 7–41, more shell reads and refused calls |

**What it says.** On these four read-and-answer tasks, the local model at 131k context nearly matches Haiku. It is faster per run and costs no plan use, but it makes several times as many tool calls. At 32k context it got 1 of 4 RC03 runs right (local-1), so the context setting decides it. Four distinct tasks is far too few to rank the two; this is a shakedown, not a measurement.

**The finding that matters more: no arm B run used Atlas.** Every arm B run in every leg made 0 Atlas calls: Sonnet, nemotron and Haiku alike. There are two causes. (Corrected the same evening: the first version of this note said no leg had the tools at the start.)
- **On the plan route (Sonnet, Haiku), Atlas wasn't there at the start.** The task turn's start shows `atlas` pending and no Atlas tools; they first appear in the debrief turn's start. So arm B ran as arm A, plus a larger prompt, and cost more for it (Haiku RC03: $0.13 to $0.28 against $0.10 to $0.11).
- **On the local route, Atlas was there and went unused.** All six local-2 arm B runs started with `atlas` connected and its tools offered. Nemotron never called one; it read the files instead.
- **The pending start belongs to the plan sign-in path, not to the CLI version.** Arm B's start was captured in the sandbox against a closed port, as both root and `amu`, with the harness's MCP configuration. CLI 2.1.197 and the image's 2.1.280 both start with `atlas` connected and 7 Atlas tools, with or without a 15-second wait before the task. The plan route differs from those captures in its sign-in: the placeholder credentials and the proxy.
- **Before any graded run:** one short start on the plan route must show the Atlas tools in the task turn's start. If they're missing, the harness must hold the task until Atlas has connected. That start costs a few cents of plan, so it waits for the Director's go.
- **A model that is offered Atlas and ignores it is itself a result.** The prompt only makes Atlas available (README, "What this does not measure"). The local leg's zero calls are recorded as that, not as a defect.

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
- CF09 to CF13 share one fix pattern. They exist because Atlas's D1 rule found them, so they favour Atlas by construction. Since amendment 6 they are outside the decision set and reported apart.

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
- **Tools.** `--tools "Read,Grep,Glob,Bash"` makes those four the only built-ins (amendment 4). The allow-list then gates them:
  - Read is held to the checkout, and Grep and Glob search under the same Read rules;
  - Bash is limited to read-only `git log` and `git show` (amendment 2).

  Arm B adds the `atlas` MCP server, started in the checkout from the pinned package, and no other tool.
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

**Primary: correctness.** Each pair is correct or incorrect in each arm. The test is an exact two-sided McNemar on the discordant pairs, α = 0.05, over the 37 pairs other than CF09 to CF13 (amendment 6). The token estimate below uses the same 37.

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
- **Cut-list misreads** (amendment 6): arm-B runs where an Atlas answer said `complete: false`, the agent didn't follow its cursor, and the run graded wrong.

**Sensitivity results.** They are read beside the primary result and never drive the decision:
1. without the 9 medium-confidence keys;
2. with CF09 to CF13 included (amendment 6 took them out of the primary set);
3. with one task per correlated cause.

**Power, said plainly.** With 37 pairs, McNemar detects only a large difference in correctness (about ten discordant pairs against two). The token ratio is the more sensitive measure.

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
2. **A run that fails in the harness** (not a wrong answer) is retried once. If it fails again, its pair is dropped and reported. If more than 20% of runs fail this way, stop. Since amendment 4, that means a run with no result at all: a crash, or the watchdog. A run that ends in an error result from the service stops the pilot. The turn cap is not one; it is graded incorrect.
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
- `run.py`: the harness (amendment 2). Its tests are in `tests/test_atlas_mcp_utility_run.py`, with the CLI's real starts in `tests/fixtures/atlas_mcp_utility/` (amendment 4) and shakedown 2's recorded streams in its `shakedown-2/` (amendment 10).
- `debrief.md`: the debrief each graded run is asked after its answer is recorded (amendment 3).
- `results/`: written by the run, one record per run with its usage, answer and grade.
