# agent-ab-harness: paired runs of a coding agent, two arms per task

A harness for A/B experiments on a coding agent (Claude Code CLI, headless). Each task runs once per arm, on a fresh copy of a pinned repository checkout, inside an isolated sandbox. Every run's answer is graded against a key fixed before the run. Design the experiment with the [A/B experiment template](https://mcp-tool-shop-org.github.io/rnd/handbook/ab-experiments/) before writing any code for it.

Instrument: `instruments/agent-ab-harness.md`.

## What it does

- **Isolation:** the harness runs as root, in a Docker sandbox with no host mounts.
  - The agent runs as an unprivileged user with an emptied home and a fresh placeholder sign-in.
  - Every tree the agent must not read is root-only.
  - A containment probe plants sentinels and must pass before any counted run. Its pass is tied to the pinned files, the CLI and the installed tools.
- **Arms:** arm A is the agent with its built-in tools. Arm B adds one MCP server; its first message is held until the server has connected. Each start is checked against its arm: the tools, MCP servers, model, permission mode and key source.
- **Routes:**
  - `plan` (the pinned model on a Claude plan);
  - `haiku` (Haiku on the plan);
  - `local` (an Ollama model on the host, at a pinned context).
- **Records, per run:**
  - token totals per turn, from the CLI's own result;
  - task-only wall time;
  - tool calls, refused calls and shell reads;
  - cost at API rates (plan routes) or the GPU window (local);
  - the graded answer;
  - an optional debrief, kept apart from the run's figures.
- **Stops the whole run** on:
  - a start that doesn't match its arm;
  - a hook;
  - any write to the checkout or the shared cache;
  - a writing or executing shell form that ran;
  - a plan limit, a sign-in failure, an error result, or the token ceiling.
- **Replay:** `run.py --replay <run>.jsonl …` puts recorded streams through the same checks with no CLI.

## Usage (in the sandbox, as root)

```
python run.py --probe --work <dir> --tools <dir> --ceiling <tokens> --run-as <user>
python run.py --pilot --work <dir> --tools <dir> --ceiling <tokens> --run-as <user> [--label shakedown [--route haiku|local]]
python run.py --replay <run>.jsonl ...
```

## Inputs

These are the pinned files, checked against the table below at every start:

| File | What it holds |
|---|---|
| `tasks.json` | the tasks: repository, commit, question, key and grading rules |
| `prompt.md` | the prompt template, with `{question}` |
| `allow-list.json` | the CLI, the model, the tools and permission rules, and each arm's MCP servers and prompt note |
| `grade.py` | the grader |
| `debrief.md` | the optional debrief prompt |

The files here are example inputs: 42 repository-reading tasks with audited keys (`key-audit.json`), from an earlier experiment that was withdrawn. A new experiment brings its own tasks, prompt and arms, re-pins them, and runs its own probe.

**Before reusing it,** check these against the new experiment's design:
- the sample of tasks;
- the turn cap (`max_turns`), which a run's turns share;
- the effort setting per route;
- whether files such as a committed `atlas/` map should be in the checkout. Remove them from git history as well as the working tree.

Each sha256 is of the file as committed, with LF line endings (`.gitattributes`).

| What | Pin |
|---|---|
| `tasks.json` | `eb2ba43c88c989022ecf2fe90d950b150e144a3f916540fa68c1d46559acca1a` |
| `prompt.md` | `a32c1c8f30e88f7264e6efce1d1c608339368b2e44691870206b3105e4e6226d` |
| `allow-list.json` | `975d32721641482ec7681937cb28753c6d9a42879594304b6f18e8951fa51dd5` |
| `grade.py` | `0d63c6c7e200a4c239a3d8a873d1a8a6f05434033716ee8600745b6cdff947e7` |
| `debrief.md` | `ed73ef0864f6b603f32ab3f4a91874c465d537779ff1450094bc82690d312f8c` |

Tests: `tests/test_agent_ab_harness_run.py` and `tests/test_agent_ab_harness_grade.py`. Recorded streams for replay are in `tests/fixtures/agent_ab_harness/`.
