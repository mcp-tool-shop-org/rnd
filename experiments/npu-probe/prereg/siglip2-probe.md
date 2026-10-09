# Probe: SigLIP2 image embeddings on the NPU and iGPU

Pre-registered 2026-10-09, before any image runs. Measurement only — **no decision is attached** (the
handoff: "speed and match only; no claim about quality"). The point: ai-eyes scores images through
SigLIP2 on the CPU today; the probe prices moving that to the Intel devices.

## Pinned

- **Model (ai-eyes' own pin,** `E:/AI/ai-eyes-mcp/src/ai_eyes_mcp/engine.py`, read-only**):**
  `google/siglip2-so400m-patch14-384` @ `e8e487298228002f3d8a82e0cd5c8ea9c567f57f`, already in
  `E:/AI-Models/hf-cache`. Vision encoder only, exported to OpenVINO via optimum
  (`OVModelForFeatureExtraction`); the text tower does not run. No `trust_remote_code`.
- **Images:** 50 sampled from `E:/AI/style-dataset-lab/projects/ai-eye-test/` (backgrounds + outputs,
  185 image files, `.png`/`.webp`/`.jpg`), seed 20261009 (`random.Random(20261009).sample(sorted(paths),
  50)`), read-only. The sampled list is recorded in the receipt.
- **Devices:** CPU (the reference), NPU, and the Intel iGPU, in that order per image, one image at a
  time (batch 1, SigLIP2's own 384×384 input). **Never the 5090** — the iGPU is found by name, as
  `npu_serve.intel_igpu` does.
- **Timing:** per image and device, seconds; every (image, device) repeated 3 times, devices
  interleaved. Reported per device: median and min–max spread of per-image seconds, plus cold load
  (process start to first embed) and export time once.

## Compared

- Per image: cosine of the NPU and iGPU vectors against the CPU's, same weights. Report min, mean, p1
  per device, and the worst 5 images with their paths from the sampled list.
- Speed per device as above; the headline is NPU and iGPU median vs CPU median.

## Rules

- NPU/iGPU legs only inside a Publisher-logged window, announced via Mike before and after; the CPU leg
  is single-image and seconds long, so it rides along in the same window without its own CPU grant.
- Nothing is written to the datasets or the model cache beyond OpenVINO's own export cache
  (`E:/AI/rnd-npu-index/`, outside the repo).
- Receipt: `results/2026-10-09-siglip2-probe.json` (rerun date in the name if later), one JSON, every
  number in the probe's README section coming from it.
- Verdict wording for the report: "hypothesis tested", with the measured numbers. Whether ai-eyes moves
  is the Publisher's call, informed by ai-eyes' own scoring bar — not this probe.

## Amendments

- **2026-10-09, before any image runs — the export path is not optimum.** The pin said "exported to
  OpenVINO via optimum (`OVModelForFeatureExtraction`)". That path is unavailable on this venv:
  optimum-intel 2.2.0 (with optimum 2.3.0) registers `siglip` and `clip` for OpenVINO
  feature-extraction but **not** `siglip2` —
  `TasksManager.get_supported_tasks_for_model_type("siglip2", "openvino")` fails, so the pinned
  call would abort at export. The export path is therefore: transformers' own
  `Siglip2VisionModel` from the same pinned snapshot (vision tower only, as pinned), converted once
  with `openvino.convert_model` at full fp32 — ai-eyes' default dtype is full precision
  (`DEFAULT_DTYPE = None`, engine.py). Devices, sampling, repeats, comparison, the failure policy
  and the receipt are unchanged; the receipt records the registry check and the export path used.
  If a later optimum-intel release adds siglip2, that is a new lane, not this probe.
