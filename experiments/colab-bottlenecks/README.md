# Colab Pro+ bottlenecks: Argon's consult, checked

**Question (2026-10-16).** Setting up the studio's Colab Pro+ units (`instruments/colab.md`) hit seven
bottlenecks:
- `google.colab.ai` fails from the CLI;
- CUDA 13.4 on a CUDA 13.0 driver;
- sessions that hang and keep spending;
- model weights on a fresh VM;
- pinning the card and the image;
- a Linux safety governor;
- anything else that wastes units.

R&D asked Browser Argon ([the brief](argon-brief.md)), and [Argon's answer](argon-answer.md) is kept as
received. R&D then checked each load-bearing claim against the primary source: the google-colab-cli source at
tag `v0.7.4`, the official `googlecolab/colab-mcp` source, and our own CUDA record.

**Verdict.** Most of the answer holds and is adopted. Two claims are wrong: Q1's colab-mcp, and Q3's "inactivity
timeout". One is superseded by our own measurement (Q2). The rest are adopted as "likely", to be measured on first use.

## What R&D checked

| Claim | Status | How checked |
|---|---|---|
| The CLI's `colab_request` hook handles only drive and auth credential propagation, with no `GetSecret`, so `google.colab.ai` can't get its key from the CLI | **confirmed** | `runtime.py` and `commands/automation.py` at v0.7.4 |
| "colab-mcp is a thin wrapper over the CLI with no browser tab" | **wrong for the official server** | Argon cited a third-party project (amgallego8/colab-mcp). The official `googlecolab/colab-mcp` opens the Colab page in a browser and drives that notebook over a local websocket (`session.py`, `websocket_server.py`). Code runs in the browser-attached session, so the front end can answer secret requests. That makes it a likely route to `google.colab.ai`, **untested**. |
| `colab exec` and `colab run` default to `--timeout 30` | **confirmed** | `commands/execution.py` and `commands/run.py` |
| "An inactivity timeout that resets on output" | **wrong** | The installed `jupyter-kernel-client` 0.9.0 (PyPI, read in WSL) sets one deadline at the call's start. The output loop never raises on it. Past the deadline it busy-waits until the kernel reports idle, and only the final reply fetch uses the leftover (about zero) time. So a kernel that never goes idle hangs the client forever whatever `--timeout` says. That fits the 16-minute hang. A run that outlives `--timeout` may finish its work and still fail the reply fetch. (The CLI's own comment in `runtime.py` describes this wrongly.) |
| `colab run` tears down in a `finally` block and swallows teardown errors, so a clean exit isn't proof of release | **confirmed** | `commands/run.py` (`_teardown`: each step is wrapped in `except Exception: pass`) |
| `colab whoami` is a hidden debug command that refreshes the token | **confirmed** | `commands/utility.py` and `cli.py` |
| The CLI has no runtime-version (image pin) flag | **confirmed** | no such option in the v0.7.4 commands |
| CUDA 13.4 runs on a 13.0 driver, but PTX JIT may fail | **superseded by our record** | `experiments/cloud-cu134`: the 13.4 nightly on driver 580.159 passed raw Triton JIT, `torch.compile` and CUDA graphs on an A100 (sm_80) and a B200 (sm_100). Colab's driver is the older 580.82, and the T4 (sm_75) and L4 (sm_89) are untested. Run `cu134_probe.py` once per Colab card type before relying on it. |
| The T4 (sm_75) is the oldest card CUDA 13.x supports | adopted, `checked` by Argon | not re-checked; the probe above tests it in practice |
| An A100 on Pro+ is only ever 40 GB; 80 GB needs `--gpu H100` | adopted as **likely** | it matches our assignment; the H100 rate isn't measured yet |
| Image drift shows in `COLAB_RELEASE_TAG` | adopted as **likely** | log it in the probe on the next session |
| Weights: pull from HF or the Ollama registry to `/content`, never run Ollama's store from Drive | adopted as **likely** | measure the pull rate on first use |
| Host OOM kills the worker, not the VM, so a parent supervisor survives | adopted as **likely** | the governor's fault-injection tests check it |
| No server-side spend cap exists | adopted | consistent with the FAQ. The host-side cap stands. |

## What changes

The rules are in `instruments/colab.md`:
- **`--timeout` on every `colab run`:** set it above the expected run time plus a margin. It doesn't protect against a hang, so the three layers below do.
- **Teardown, three layers:**
  - an in-VM watchdog calls `google.colab.runtime.unassign()` at a deadline and in `finally`;
  - the host runs `timeout --signal=SIGINT --kill-after=15s <secs> colab run …`;
  - afterwards, check that `colab sessions` is empty, and `colab stop` until it is.
- **Machine line:** add `COLAB_RELEASE_TAG` and `/proc/cpuinfo`'s model name. Assert the card in the first
  seconds, and unassign on a mismatch.
- **T4:** request `--high-mem`, since 12.7 GB of host RAM can fail shard loading.
- **Python:** a `uv venv` for the cu134 stack. Never pip into the image's system Python.
- **`google.colab.ai`:** test the official colab-mcp route before any design depends on it. It needs a browser
  tab and the Director's go to install.
