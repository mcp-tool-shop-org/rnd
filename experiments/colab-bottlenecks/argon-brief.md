# Argon consult: Colab Pro+ bottlenecks for studio experiments (2026-10-16)

**From:** R&D, for Browser Argon. **Kind:** a consult, not a code review. There is no bundle. Everything we
measured is below.

**Answer format:**
- `## 2026-10-16 · rnd · Colab bottlenecks · instruments/colab.md (rnd #117)`
- then one section per question: the answer, how sure you are (`checked` / `likely` / `unsure`), and a source
  link where one exists;
- then anything we didn't ask but should have.

Severity per question: `before first use`, `before a design depends on it`, `nice to know`.

## The setup

- **The CLI:** google-colab-cli 0.7.4 in WSL Ubuntu on Windows, signed in with OAuth (scopes: openid, profile,
  email, cloud-platform, colaboratory, drive.file).
- **The VMs we were given** (2026-10-16, ~19:00Z): the same image on every card, with driver 580.82.07, CUDA 13.0,
  Python 3.13.15 and a 236 GB overlay disk.
- **Measured rates:**

  | Card | Units/hour | GPU memory | Host |
  |---|---|---|---|
  | T4 | 1.07 | 15,360 MiB | 2 cores, 12.7 GB |
  | L4 | 1.54 | 23,034 MiB | 12 cores, 53.0 GB |
  | A100 (40 GB assigned) | 5.30 | 40,960 MiB | 12 cores, 83.5 GB |

- **The uses:**
  - Ollama and transformers inference on open models, for model comparisons and a thinking-effort study;
  - a "what runs on your card" table, built on real T4, L4 and A100 cards;
  - a Linux path for a GPU safety governor;
  - possibly small fine-tunes.
- **Rules that bind the answers:**
  - no paid per-token APIs (the Colab units are prepaid, so allowed);
  - no secrets on the VM;
  - every run's machine line is recorded, and a run on the wrong card is refused, not swapped.

## Questions

**Q1. `google.colab.ai` from outside the Colab UI** (`before a design depends on it`).

From a CLI session, it fails with: `TimeoutException: Requesting secret MODEL_PROXY_API_KEY timed out. Secrets
can only be fetched when running from the Colab UI.`

- Is there any supported way to use it headless? For example: through the VS Code Colab extension's kernel, the
  official colab-mcp server driving a browser notebook, or a documented secret-passing route.
- Which models does it serve, and with what rate limits? Do its calls spend compute units?
- If it's truly UI-only, what's the least manual way to run a few hundred prompts through it?

**Q2. CUDA 13.4 on driver 580 (CUDA 13.0)** (`before a design depends on it`). Our standard stack is a CUDA 13.4
torch nightly (cu134) plus an Ollama backend built against CUDA 13.4.3.

- Does NVIDIA's minor-version compatibility cover these on driver 580 with no cuda-compat package?
- What breaks under minor-version compatibility (PTX JIT, newer cuBLAS or cuDNN features)?
- Is the T4 (sm_75) still supported by CUDA 13.x toolkits and by current torch nightlies?

**Q3. Sessions that hang and keep spending** (`before first use`). One `colab exec` (the colab.ai call, on an L4)
hung for about 16 minutes before we stopped the session by hand.

- What is the right pattern to guarantee teardown: an outer `timeout`, `colab run` instead of `new`+`exec`, or a
  server-side idle limit we can set?
- Is there any way to cap the spend per session or per day?

**Q4. Getting model weights onto a fresh VM** (`before first use`). Ollama models are 5–25 GB each, and every
session starts empty.

- Which is fastest per unit: pulling from the Ollama registry, Hugging Face, or a Google Drive cache mounted with
  `colab drivemount`?
- Can Ollama run its model store directly from a Drive mount, or must it copy to local disk first?
- Are there any known throughput limits on Drive inside Colab?

**Q5. Pinning the hardware and image** (`before a design depends on it`).

- Can we request an A100 80 GB specifically, or is 40 versus 80 only luck?
- How often does Colab change the VM image (driver, CUDA, Python)? Is there a way to pin or detect a version,
  so a multi-week study keeps one machine line?

**Q6. A Linux GPU-safety governor on a Colab VM** (`nice to know`). The governor samples VRAM, use, temperature and
host RAM at 1 Hz. It drains, then checkpoints and frees the GPU, before an out-of-memory error.

- Inside a Colab VM, are NVML readings and the cgroup memory limit reliable?
- What does Colab do when the host runs out of RAM: kill the kernel, or the whole VM?
- Is GPU temperature readable?

**Q7. Anything else** that commonly wastes units or breaks reproducibility on Colab Pro+ for this kind of work.
