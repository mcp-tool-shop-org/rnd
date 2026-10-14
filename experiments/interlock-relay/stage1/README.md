# interlock-relay, stage 1: the harness and the frozen analysis

Stage 1 is the first device run: Ollama on the 5090, under the Publisher's grant, after the Director's go. This
folder holds the analysis, frozen before any run:
- `analyze.py`, with its amendments S1-A1 to S1-A6 in its docstring;
- its tests, `test_analyze.py`;
- the null simulation, `simulate.py` and `simulation.json`.

The harness, the driver (`scripts/relay_s1.py`) and the specs (`experiments/relay-s1/`) are in interlock, on the
local branch `relay-stage0`. The plan is [../stage1-plan.md](../stage1-plan.md).

## Argon's review, round 1 (2026-10-14), and what R&D did with it

Argon ([the brief](../argon-review-stage1.md), run by hand) found three blocking issues and confirmed the
statistics.
- **The calibration is confirmed,** including the variance argument behind 1.96 × sd(A–A) and the binomial tail
  bound, and that "inconclusive" is reported but still fails stage 1.
- **H1's ground truth is confirmed independent of the hook,** and the honesty of charging B's size calculation to
  B is agreed.

| # | Finding | Disposition |
|---|---|---|
| B1 | `long.yaml` sent no canary, so H3 passed the long step vacuously | **Adopted.** The long prompt's seed carries the canary, and the stop rule says so |
| B2 | Models stay on the card after the stop step (the watcher's `os._exit` skips the unload) and after the import children, so the next preflight refuses | **Adopted, by a restructure.** Every step runs in its own process. Before each step after the first, the driver unloads every model (`keep_alive` 0), waits up to 90 s for an idle card, and runs the preflight. It unloads again at the end. (Interleaved runs already unload at their end; the stop step and the import children didn't.) |
| B3 | A 60 s sleep could outlast the whole decode run, so the stop step would exit 0, and nothing checked that it stopped | **Adopted.** The driver waits until the stop run's trace holds 10 model calls, then writes the stop file. The step passes only on exit 77, `drive()` refuses otherwise, and the analysis's H3 needs the driver's `stopped` record (S1-A5) |
| I1 | The companion arm had no `trace` key, and the plan's 21 GiB companion rule wasn't enforced anywhere | **Adopted, and widened.** `trace: false` on the companion arm. Checking the rule showed interleaved runs have no VRAM ceiling at all; the plan's "abort at 30,500 MiB" was fill-card's. The driver now watches VRAM once a second and stops the step over 30,500 MiB. The 21 GiB rule is gone: the companion step runs at small contexts, below the long step's 13,587 MiB |
| I2 | The barrier check compares spaced calls with back-to-back calls in fresh processes. With a 1% band floor it could fail stage 1 for a reason that has nothing to do with Relay | **Adopted as S1-A6.** The barrier check is reported, not gated. Both arms of every triple take the same barrier, so it can't bias Δ. The check describes the measurement protocol, and it stays in the output beside H2 |
| I3 | B alone computes the request size | **No change.** Argon agrees it's a genuine cost of tracing, charged to B's hook time |
| M1 | A step that didn't run left h2 and h3 entries missing | **Adopted.** "not run" in every section |
