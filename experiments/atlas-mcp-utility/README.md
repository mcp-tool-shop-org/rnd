# atlas-mcp-utility: harness only, unvalidated

**The experiment this was built for is withdrawn (2026-10-13).** It was badly designed. Arm B made Atlas available
without telling the agent what it was for, so the runs measured whether a model happens to pick Atlas, not whether
Atlas makes it faster. Most of its tasks were also narrow lookups or CI-failure questions that Atlas isn't for. Its
write-ups, amendments and results have been removed from this file. No result from it should be cited.

**What's left is the harness: `run.py` and its inputs.** It runs Claude Code agents in a Docker sandbox, two arms
per task, and records each run. It ran end to end in a few shakedown rounds, but that shows only that it runs. It
does not show that it measures correctly, and it was designed around the same flawed experiment. Treat it as
untrusted code. Any future experiment reviews it line by line before relying on it.

The pins below are kept only because `run.py` refuses to start without them.

Each sha256 is of the file as committed, with LF line endings (`.gitattributes`).

| What | Pin |
|---|---|
| `tasks.json` | `eb2ba43c88c989022ecf2fe90d950b150e144a3f916540fa68c1d46559acca1a` (amendment 3) |
| `prompt.md` | `a32c1c8f30e88f7264e6efce1d1c608339368b2e44691870206b3105e4e6226d` |
| `allow-list.json` | `975d32721641482ec7681937cb28753c6d9a42879594304b6f18e8951fa51dd5` (amendment 13) |
| `grade.py` | `f6d09f5144b42fc1c86f632015de33c84d0bfb9dd3faf2f192cb47d24d864455` (amendment 1) |
| `debrief.md` | `ed73ef0864f6b603f32ab3f4a91874c465d537779ff1450094bc82690d312f8c` (amendment 3) |
| Claude Code CLI | 2.1.197 |
| Model | `claude-sonnet-5-5`, at medium effort (`--effort medium`, amendment 7) |
| Where it runs | the local Docker sandbox `atlas-pilot`, on the Director's plan (amendment 7) |
| Atlas | `@dogfood-lab/atlas` 1.26.0 |
| Seed (arm order, key draw) | 20261013 |

Files: `run.py` (the harness; tests in `tests/test_atlas_mcp_utility_run.py`), `grade.py` (tests in
`tests/test_atlas_mcp_utility_grade.py`), `tasks.json`, `prompt.md`, `debrief.md`, `allow-list.json`, and
`key-audit.json` (grader test data).
