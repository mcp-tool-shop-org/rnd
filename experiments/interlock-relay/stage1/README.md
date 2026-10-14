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

## Argon's review, round 2 (2026-10-14), and what R&D did with it

Argon found **no blocking issues: stage 1 can run.**
- Round 1's B1, B2, I1, I2, I3 and M1 are resolved, and B3 is partly resolved.
- Both of R&D's rulings were judged sound: the barrier check is reported, and each step runs as a child process.

| # | Finding | Disposition |
|---|---|---|
| I1-R2 | `run_stop` recorded a stop after its 300 s timeout with fewer than 10 spans, and didn't return or check a VRAM breach | **Adopted.** A stop counts only with at least 10 spans, no breach and exit 77. The breach is returned, and `drive()` refuses on it. Tests: a stop after the timeout with too few spans, and a breach-written stop |
| I2-R2 | `wait_idle` didn't wait for the GPU's processes to clear, so the preflight would refuse after the stop step | **Adopted, then corrected on the live rig** (below). The idle wait and the preflight apply the same card condition. Tests: a busy card refuses after the timeout, and a draining card settles |
| M1-R2 | During the import check a VRAM breach went unseen until all 45 children had run | **Adopted.** The watch is created before the re-check, and the re-check refuses at once on a breach. Test: a breach stops the check before the next child |

**One addition, not from Argon: the grant's cap.**
- The driver enforces `--max-minutes` (default 90):
  - no step starts after the cap;
  - a running step gets its remaining time, and at that limit its stop file, so the run's watcher ends it cleanly. A step that still hasn't ended after a 120 s grace is killed;
  - the import check stops between children.
- Tests: no step after the cap, and a step stopped at its limit.

**Post-Argon preflight corrections** (after round 2, before any run; read-only readings of the live rig, no model call). They make the checks match the rig and are part of the run record:
- **Listeners:** a psutil count of listeners on 11434 read 0 while Ollama answered there. Windows build 26340 reports a listening socket as state 0, and interlock's supervisor already works around that. The driver now uses interlock's own `listening_pids`, which finds Ollama's listener.
- **GPU processes:** on Windows (WDDM), `nvidia-smi` lists every desktop app that draws on the GPU (27 of them: the shell, browsers, the Claude app), with no memory figures. "No process on the GPU" could never hold.
  - The check now refuses on a **compute workload**: a process whose name says it runs models (python, Ollama's runner, llama.cpp, ComfyUI, vLLM, LM Studio and similar). An empty `/api/ps` still catches a loaded model.
- **Idle VRAM:** the desktop alone read 2,751–2,811 MiB, over the plan's 2,400.
  - The first preflight allows at most 3,500 MiB, which any loaded model would exceed.
  - Later steps must come back within 512 MiB of the first reading.
- **A quiet CPU** (the Publisher's hold): H2 measures client-side time, so a busy CPU adds noise right where
  equivalence is tested, and the ABA order controls drift but not this. Before every step the system CPU,
  averaged over 5 s, must be at most 25%. That's interlock `6ed29a2`; it read 8% with the rig quiet.
- **The whole preflight now passes read-only on the rig at interlock `bfc484a`:** heartbeat 2 s, nemo-relay 0.10.1, Ollama 0.35.1, one listener, no compute workload, idle 2,811 MiB, logs/ ignored, a clean tree.

The analysis is unchanged since its freeze at rnd `cbaed82`.
