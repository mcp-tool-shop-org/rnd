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

- **2026-10-09, before any image runs — the export path is not optimum.** WITHDRAWN the same day by the
  second amendment below; kept for the audit trail. The pin said "exported to OpenVINO via optimum
  (`OVModelForFeatureExtraction`)". That path is unavailable on this venv: optimum-intel 2.2.0 (with
  optimum 2.3.0) registers `siglip` and `clip` for OpenVINO feature-extraction but **not** `siglip2` —
  `TasksManager.get_supported_tasks_for_model_type("siglip2", "openvino")` fails, so the pinned call
  would abort at export. The export path is therefore: transformers' own `Siglip2VisionModel` from the
  same pinned snapshot (vision tower only, as pinned), converted once with `openvino.convert_model` at
  full fp32 — ai-eyes' default dtype is full precision (`DEFAULT_DTYPE = None`, engine.py). Devices,
  sampling, repeats, comparison, the failure policy and the receipt are unchanged; the receipt records
  the registry check and the export path used. If a later optimum-intel release adds siglip2, that is a
  new lane, not this probe.

- **2026-10-09 (second amendment, still before any image runs) — the checkpoint's model type is `siglip`;
  the export goes through optimum-intel's exporter with a custom export config, and an equivalence gate
  is added before any device timing.** R&D's review found the first amendment checked the wrong name: the
  pinned checkpoint's `config.json` says `model_type: "siglip"`, with a `siglip_vision_model` vision
  config (patch 14, image 384; verified 2026-10-09). Fixed-resolution SigLIP2 checkpoints reuse the
  SigLIP architecture, so optimum-intel 2.2.0's registered `siglip` export path applies after all, and
  the "no siglip2 export" finding does not bear on this probe. The first amendment's path is withdrawn
  for cause, not just superseded: `Siglip2VisionModel.from_pretrained(<pinned>)` raises a RuntimeError
  (verified in the venv — patch_embedding ckpt `[1152, 3, 14, 14]` vs model `[1152, 588]`;
  position_embedding `[729, 1152]` vs `[256, 1152]`), and it is not what ai-eyes runs. ai-eyes runs
  `AutoModel` -> `SiglipModel.get_image_features(pixel_values)` at full precision
  (`DEFAULT_DTYPE = None`; engine.py:87, :324, :691, :696, read-only). The probe measures that function
  and nothing else:

  - **Export path.** A small `PreTrainedModel` wrapper holds the pinned `SiglipModel` (fp32, no
    `trust_remote_code`, no weight-format compression); `forward(pixel_values)` calls
    `get_image_features` and returns its `pooler_output` — ai-eyes' own embedding pick (engine.py:696) —
    as a single raw tensor, before any normalisation. The export config subclasses optimum-intel's own
    `SiglipOpenVINOConfig` (`optimum/exporters/openvino/model_configs.py:6825`, venv source), overriding
    only `inputs` = `pixel_values` `[image_batch_size, num_channels, height, width]` and `outputs` =
    `image_embeds` `[image_batch_size]`. It is passed through the `custom_export_configs` mechanism — no
    registry change, no `register_in_tasks_manager`, no editing the installed package. The entry point is
    `optimum.exporters.openvino.convert.export_from_model` (`convert.py:606`), the exact call
    `main_export` makes after loading the model (`__main__.py:647`); `main_export` itself takes only a
    model id string (`__main__.py:262`) and so cannot receive the wrapper. Against the venv's source it
    is verified that for a registered model type (`custom_architecture = False`, `convert.py:642`) the
    custom config replaces the default in place while the model object — our wrapper — passes through
    untouched (`optimum/exporters/utils.py:577, 581-582`), and that output tensors are named by position
    from `config.outputs` (`convert.py:409`). `fn_get_submodels` is ignored for registered architectures
    (utils.py:538-582) and is omitted for that reason. The receipt records the export path, package
    versions, the model revision, and the IR digest (sha256 + bytes of `openvino_model.xml`).
  - **Device preparation.** The NPU compiles a static reshape of the exported IR to `[1, 3, 384, 384]`;
    the CPU and iGPU legs use the dynamic IR.
  - **Equivalence gate (new; run before any device timing).** The exported IR on OpenVINO CPU is compared
    against transformers' `SiglipModel.get_image_features` on CPU over the same 50 seeded images, through
    ai-eyes' processor path (`AutoProcessor`, pinned revision). **Pass requires minimum cosine >= 0.9999**;
    the receipt reports min, mean and the worst 5. A miss stops the probe: the gate result is recorded and
    no device timing happens, and no alternate export path is substituted to get past it.
  - **CPU reference.** With the gate in place, "CPU (the reference)" in the pin means the transformers
    `SiglipModel` itself at fp32 on CPU — what ai-eyes runs today. The NPU and iGPU legs are compared
    against it (cosine and timing only, as pinned). The OpenVINO CPU leg appears in the gate section,
    with its own timing recorded descriptively.

  Everything else in this prereg — sampling (seed 20261009), the 50 images, 3 interleaved repeats per
  (image, device), the failure policy, the receipt location and the verdict wording — stands unchanged.
