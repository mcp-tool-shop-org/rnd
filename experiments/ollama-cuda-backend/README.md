# The studio's CUDA backend for Ollama

The studio runs its own `ggml-cuda.dll` for Ollama on the RTX 5090: Ollama's own llama.cpp pin, built with CUDA 13.4 for compute capability 12.0 only. This folder holds the build records, the sandbox test and the diagnosis that followed it. The story is in [newsletter issue 9](https://mcp-tool-shop-org.github.io/rnd/newsletter/issue-09/).

**Status, 2026-10-15:**
- **The 0.40.4 build to the studio standard,** on CUDA 13.4 Update 2, is built (see `build-0.40.4-cuda-13.4.3.md`).
- **Nothing is activated.** The installed Ollama runs the stock backend until activation is decided separately.
- **The sandbox test** ran on the same day and **failed criterion 2:** outputs diverged from stock on 2 of 3 prompts, at positions that weren't near-ties. Nothing is activated (see `sandbox-result-cu1343.md`).
- **The diagnosis** (harness v6, the same day) found the cause: the cuBLAS library. Putting only CUDA 13.4.3's cuBLAS into stock Ollama reproduces the studio build bit for bit, and the studio's own kernels change nothing. By the rule set before the run, the build is **eligible** for activation. Activation is a separate go, with stock CUDA 13.0 kept as a switchable fallback (see `diag-result-v6.md`).

| File | What it is |
|---|---|
| `build-0.35.1-cuda-13.4.1.md` | The first studio build (Ollama 0.35.1, llama.cpp b11232) and its activation method |
| `build-0.40.4-cuda-13.4.1.md`, `.cmd` | The rebuild for 0.40.4 (b11521) after the install replaced the backend, with its capped run |
| `build-0.40.4-cuda-13.4.3.md`, `.cmd` | The rebuild to the studio standard on CUDA 13.4 Update 2 (nvcc V13.4.92) |
| `run-build.ps1` | The capped launcher: E-core affinity, below-normal priority, typeperf, a stop rule |
| `sandbox-plan-v1.md` | The sandbox test plan as first written |
| `sandbox_test-v3.py`, `sandbox_test-v2-to-v3.diff` | The test after two review rounds: isolation, per-prompt exclusivity, breach handling, the near-tie rule |
| `sandbox-result-cu1343.md`, `sandbox-record-cu1343.jsonl` | The test's result (FAIL on criterion 2) and its record, with one log line's PATH removed |
| `abmine-cu1343.txt`, `.json` | The ab_dataminer's reading of that record: the two builds already disagree at step 0 |
| `diag_test-v4-draft.py`, `diag_test-v3-to-v4.diff` | The first draft of the diagnosis harness, and its change from the sandbox test |
| `diag/` | The frozen diagnosis harness v6, its freeze file, and its tests, including an offline dry run of the whole run (run in the rnd suite by `tests/test_diag_harness.py`) |
| `diag_test-v4-to-v5.diff`, `diag_test-v5-to-v6.diff` | The outside review's three fixes (v5), and the fix for the crash that stopped v5's run (v6) |
| `diag-v6-pre-run-notes.md` | Where cuBLAS runs in this model, and which cuBLAS known issues apply, written before the run |
| `argon-review-diag-v6.md`, `-round2.md`, `-round2-additions.md` | The outside review briefs for v6, as sent |
| `diag-result-v6.md`, `diag-record-v6.jsonl`, `diag-analysis-v6.json` | The diagnosis result (the cause is cuBLAS; ELIGIBLE), its record and its ab_dataminer analysis |
| `diag-record-v5-aborted.jsonl` | The record of v5's run, which stopped at the first arm before anything loaded |

The build folders themselves (the DLLs, logs and monitor CSVs) stay on the rig. Every DLL is recorded here by sha256.

**The weekly check:** the scheduled task `gpu-stack-weekly-argon` reads the rig's versions every Monday and writes a paste-ready brief for the outside reviewer. If an update has replaced the studio's backend again, it raises an alert.
