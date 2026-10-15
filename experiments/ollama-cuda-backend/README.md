# The studio's CUDA backend for Ollama

The studio runs its own `ggml-cuda.dll` for Ollama on the RTX 5090: Ollama's own llama.cpp pin, built with CUDA 13.4 for compute capability 12.0 only. This folder holds the build records and the sandbox test. The story is in [newsletter issue 9](https://mcp-tool-shop-org.github.io/rnd/newsletter/issue-09/).

**Status, 2026-10-15:**
- **The 0.40.4 build to the studio standard,** on CUDA 13.4 Update 2, is built (see `build-0.40.4-cuda-13.4.3.md`).
- **Nothing is activated.** The installed Ollama runs the stock backend until a sandbox test passes and activation is decided separately.
- **The sandbox test** waits for the outside reviewer's green light and a GPU grant.

| File | What it is |
|---|---|
| `build-0.35.1-cuda-13.4.1.md` | The first studio build (Ollama 0.35.1, llama.cpp b11232) and its activation method |
| `build-0.40.4-cuda-13.4.1.md`, `.cmd` | The rebuild for 0.40.4 (b11521) after the install replaced the backend, with its capped run |
| `build-0.40.4-cuda-13.4.3.md`, `.cmd` | The rebuild to the studio standard on CUDA 13.4 Update 2 (nvcc V13.4.92) |
| `run-build.ps1` | The capped launcher: E-core affinity, below-normal priority, typeperf, a stop rule |
| `sandbox-plan-v1.md` | The sandbox test plan as first written |
| `sandbox_test-v3.py`, `sandbox_test-v2-to-v3.diff` | The test after two review rounds: isolation, per-prompt exclusivity, breach handling, the near-tie rule |

The build folders themselves (the DLLs, logs and monitor CSVs) stay on the rig. Every DLL is recorded here by sha256.

**The weekly check:** the scheduled task `gpu-stack-weekly-argon` reads the rig's versions every Monday and writes a paste-ready brief for the outside reviewer. If an update has replaced the studio's backend again, it raises an alert.
