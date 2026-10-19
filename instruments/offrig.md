---
id: offrig
title: offrig — big models on rented RunPod GPUs
date: 2026-10-09
kind: instrument
relevance: reference
fields: [studio-tooling, gpu-computing]
tags: [instrument]
instrument_status: shipped
invoke: "offrig CLI (on PATH) or MCP tools mcp__offrig__*; start with offrig_status"
when: "A research task needs a model too big for the 5090, or a GPU job that should not run locally."
where: "E:/AI/offrig · github.com/mcp-tool-shop-org/offrig"
---

## Summary

Prices a session before spending, launches pods, feeds handoffs, and keeps project memory. Spending is capped by the Director.

## Studio relevance

Costs money: price with offrig_plan and confirm before launching.

## The verifier and `verify calibrate` (updated 2026-10-09)

R&D's calibration work, together with the Publisher's PRs reviewed by R&D, shaped calibrate on 2026-10-09:
- **`--num-predict`** sets the reply budget (in the manifest and the resume identity). The chain's 4096 starved
  gemma4:31b's thinking.
- **Quote rule 2** (offrig#47): comment and diff markers are stripped per line, and a short quote counts when
  it's a whole line. Every verdict pins `quote_rule`; a verdict without the pin came from a pre-#47 binary,
  which means rule 1.
- **`--keep-thinking`** (#48) writes `thinking.jsonl` in the run directory, untrusted and never scored. Keep it
  out of public commits unless it's been scanned.
- **Repeated failures on one claim** (#46, #49): a 5xx or a dropped reply twice on the same claim counts against
  the model **only if** a health probe shows the server still answers. A server that's down charges nothing.
- **Adaptive context, `--num-ctx auto`** (#53, approved and merging):
  - the window is sized from a measured probe band;
  - one resolved window per run;
  - `shift:false` and `truncate:false` on every request;
  - `context_overflow` is offrig's sizing failure, never charged to the model;
  - a reply that used its whole `num_predict` is always `truncated`.
- **Per-provider and account-wide budget caps** (#51, #52): an unreadable cap fails closed, and manual pods are
  shown as uncounted.
- **GPU count on a pod** (#55, R&D review 2026-10-11: changes needed). `offrig_status` and `offrig_job` report
  the pod record's count, the plan's count and, in the job view, what `nvidia-smi` lists. A mismatch warns and
  never shuts the pod down. R&D's required changes:
  - the measured count drives `gpu_mismatch` too, with `gpu_mismatch_source` (record, measured or both);
  - a record without a count, with nothing measured, gives `gpu_mismatch: null` (unknown) and a warning, never
    `false`, which would read as confirmed;
  - `nvidia-smi` listing no cards against a plan above 0 is a mismatch, not "not measured";
  - one test per case. Merge on green after that, with no re-review.
- **Readiness and the host CUDA pin** (#56, for 1.1.0; R&D review 2026-10-11: pass with two changes).
  - **Why:** in pilot 3 an SGLang engine logged that startup finished, then deadlocked. `/health` stayed down while
    `/v1/models` answered, and the pod sat on a CUDA 13.2 host where the working pilots had run on 13.0.
  - **Ready now means one chat completion returned a choice,** tried twice.
  - **engine_hung:** the startup line followed by 3 minutes without `/health` is reported, with the pod left up.
  - **An exact `cuda_versions` pin** is sent as `allowedCudaVersions`, and refused alongside a floor.
  - **R&D's changes:**
    - two failed completions are also reported, never a shutdown, on every surface. A slow first request on a large
      engine would otherwise throw away the download, and the deadline watchdog already bounds the cost of waiting;
    - the startup line is detected by a count over the whole log, not a 40-line tail.
  - **The CUDA list:** RunPod's documented v1 values plus 13.1 and 13.2, which are observed but not documented.
- **The 1.1.0 treatment** (#57; R&D review 2026-10-11: pass with three changes).
  - **Checked against the code:** the version, every README command and flag against `--help`, the readiness and
    hang paths, the CUDA list and how it is sent, and that every Unreleased item carried into 1.1.0. The "not re-run on
    a rented pod" notes are accurate.
  - **R&D's changes:**
    - the hang happened on 2026-10-11, not 2026-10-12, according to the pilot 3 record's own UTC times and commit;
    - don't imply that the 13.2 host caused the hang, because the run record says it isn't shown;
    - say that a pod from `offrig up` or the app has no watchdog, so a failed launch keeps billing until
      `offrig down`. Only a pod RunPod reports as ERROR or EXITED is terminated on every surface.
- **`cuda_runtime`** (#37; R&D review 2026-10-11: pass with one change).
  - **What it does:** a profile names the CUDA its software is built for, which may be newer than any host (13.4).
  - **The floor:** the oldest listed host of that major, sent as `gpu.minCudaVersion`. This is NVIDIA's minor-version
    compatibility, and it matches the cloud-cu134 probe for 13.4 on 13.0 hosts.
  - **A pin beside a runtime** is accepted only if every pinned version is that major and at or above the floor.
  - **R&D's change:** the compatibility note must appear whenever the runtime is newer than its floor, including
    listed versions such as 13.2 and 12.8, not only for unlisted ones.
- **Release 1.1.1** (2026-10-12; tag v1.1.1 at 5397759, #61; published on the Director's request).
  - **What's in it:**
    - all four MCP behaviour hints on all 15 side-car tools, pinned by a test (#60);
    - CI fails when a release binary contains `OFFRIG_TEST_`, and the engine-timing overrides are now debug-only (#60);
    - `.offrig/.gitignore` is written on first use (#58);
    - `cuda_runtime` on a profile (#37).
  - **Release checks:** the SHA256SUMS match, the identity scan is clean, the binaries contain no home or runner paths
    and no `OFFRIG_TEST_`, and shipcheck's hard gates pass.
  - **On the rig:** installed, with the 1.1.0 binaries kept beside it as a fallback. `writer-qwen235` stays pinned to
    host CUDA 13.0.

**Operating facts, read from the source (2026-10-19, offrig 1.2.0 at 8f0b59c, README and `%APPDATA%\offrig\config.toml`).**
Read these before planning a pod; earlier same-day claims made without reading them were wrong.
- **Profiles:** `config.toml` is read once per process. A fresh `offrig-mcp` process (the README's stdio shell driver)
  reads a changed config, and plans and pods live in the project DB, so no app restart is needed.
- **One lane, one live pod:** `offrig_launch` refuses while the lane has an open plan or a live pod. Pods run in
  sequence.
- **Choosing a pod:** choose on the job's bottleneck, not $/hr: CPU cores and RAM for conversions, network for downloads, disk, VRAM headroom, stock and the cost of a redo. On 2026-10-19 the A100 converter pod had 128 cores and 2 TB RAM, and downloaded 249 GB at about 211 MB/s.
- **Container disk:** `offrig_plan` takes `container_disk_gb` (1–2000) per plan. It overrides the profile's size,
  so a small-disk profile can still convert a large model.
- **Profiles on this rig** (2026-10-19):
  - small, medium, frontier, frontier-mini, frontier-mini-awq;
  - job (RTX PRO 6000 first, then A100/H100);
  - jam (A40 first, then A6000/A5000/3090/L4/4090). Prices: the README's table says $0.49/hr; offrig_offers listed
    the A40 at $0.59/hr on 2026-10-19. Prices move, so read offrig_offers live. Its `wait_for_gpu_minutes` is 0, so with
    no capacity it fails at once unless the plan sets `wait_minutes` (job and convert-cheap wait 20);
  - probe-blackwell, writer-qwen235;
  - convert-cheap and critic-h200 (added 2026-10-19).
- **Network volumes:** a profile can carry `network_volume_id`, and `offrig stage` stages weights on one. It bills
  monthly, so only a human stages; no agent tool can.
- **GPU pods only:** `gpu_count` is 1–8.

**Calibrate what is served:** a model's calibration holds for one engine and one set of settings (model digest,
think, `num_predict`, `num_ctx`, quote rule). A served engine or settings change means a new calibration, never
a rescore. Results and protocols are in `experiments/verifier-gold/calibration/`.

**Rig caveat (updated 16:14):** the VRAM/temperature watchdog (`E:/AI/training/_watchdog.ps1`) has guarded Ollama's runner since 2026-10-09 16:14. Before that it didn't, and the rest of this paragraph describes that earlier state.
A breach from an Ollama run kills nothing. Runs on the 5090 Ollama keep their own temperature/VRAM watch and
unload the model themselves.
