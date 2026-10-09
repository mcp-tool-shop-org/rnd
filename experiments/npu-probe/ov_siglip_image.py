#!/usr/bin/env python3
"""The SigLIP image-features export for the probe: a vision-only `image_embeds` OpenVINO IR of the
pinned checkpoint, built through optimum-intel's own exporter with a custom export config
(prereg/siglip2-probe.md, second 2026-10-09 amendment). Importing this module needs the
npu-openvino venv (torch, transformers, openvino, optimum-intel); the probe runner and the tests
import it lazily.

Why this shape (verified against the installed source on 2026-10-09; versions in the receipt):

- The pinned checkpoint google/siglip2-so400m-patch14-384 @ e8e4872 declares model_type "siglip"
  (fixed-resolution SigLIP2 checkpoints reuse the SigLIP architecture; only NaFlex variants are
  siglip2), so the registered path applies and custom_architecture is False
  (optimum/exporters/openvino/convert.py:642).
- ai-eyes runs AutoModel -> SiglipModel.get_image_features(pixel_values) at fp32 and picks
  .pooler_output (E:/AI/ai-eyes-mcp/src/ai_eyes_mcp/engine.py:87, :324, :691, :696, read-only).
  SiglipImageFeaturesWrapper below exports exactly that function as one tensor named image_embeds.
- main_export (optimum/exporters/openvino/__main__.py:262) loads only from a model id string
  (TasksManager.get_model_from_task, __main__.py:596) and hands the loaded model to
  export_from_model (__main__.py:647) — it cannot receive a wrapper instance. export_from_model
  (convert.py:606) takes the instance, so the probe calls main_export's own inner call directly; the
  custom_export_configs contract is identical.
- For a registered type the custom config replaces the default in place while the model object
  passes through untouched: models_and_export_configs = {"model": (model, export_config)}
  (optimum/exporters/utils.py:577), then models_and_export_configs[key] = (entry[0], custom)
  (utils.py:581-582). fn_get_submodels is consulted only in the custom-architecture branch
  (utils.py:583+), so it is omitted.
- Dummy inputs come from config.generate_dummy_inputs (convert.py:325 -> exporters/base.py:224,
  iterating self.inputs against the inherited vision generator); the model goes through
  config.patch_model_for_export (convert.py:339 -> openvino/base.py:269); a single raw-tensor output
  is named config.outputs' first key (openvino/patching_utils.py:375-377); the IR output tensors are
  finally renamed by position from config.outputs (convert.py:409).
- The wrapper subclasses PreTrainedModel only so _infer_library_from_model_or_model_class resolves
  "transformers" (optimum/intel/utils/modeling_utils.py:194-233: module lookup fails, then the
  PreTrainedModel issubclass fallback applies). PreTrainedModel.__init__ does not reinitialise the
  loaded weights (verified empirically); eager attention avoids the init-time sdpa dispatch check,
  which raises ValueError on an unregistered architecture class.
- Weights are exported fp32 with no compression (no ov_config quantization); no trust_remote_code.
"""

from __future__ import annotations

import time
from pathlib import Path

import torch
from transformers import PreTrainedModel, SiglipConfig, SiglipModel

from optimum.exporters.openvino.model_configs import SiglipOpenVINOConfig  # model_configs.py:6825

IMAGE_SIZE = 384  # the pinned checkpoint's fixed input (vision_config image_size = patch 14, 384px)
IR_STEM = "openvino_model"  # export_from_model's file stem for the single "model" entry


class SiglipImageFeaturesWrapper(PreTrainedModel):
    """SiglipModel.get_image_features(pixel_values).pooler_output as the whole forward — exactly the
    embedding ai-eyes consumes. Returns a raw tensor so the exporter names the single output
    image_embeds (patching_utils.py:375-377)."""

    config_class = SiglipConfig

    def __init__(self, model: SiglipModel):
        # Eager attention is trace-safe and numerics identical; the init-time attn check raises on
        # an unknown class otherwise. __init__ does not touch the loaded weights.
        model.config._attn_implementation = "eager"
        super().__init__(model.config)
        self.model = model

    def forward(self, pixel_values: torch.Tensor) -> torch.Tensor:
        out = self.model.get_image_features(pixel_values=pixel_values)
        return out.pooler_output if hasattr(out, "pooler_output") else out


class SiglipImageFeaturesOpenVINOConfig(SiglipOpenVINOConfig):
    """The registered siglip config cut to one input and one output. Never registered in the
    TasksManager registry — instances go through export_from_model's custom_export_configs."""

    @property
    def inputs(self) -> dict:
        return {"pixel_values": {0: "image_batch_size", 1: "num_channels", 2: "height", 3: "width"}}

    @property
    def outputs(self) -> dict:
        return {"image_embeds": {0: "image_batch_size"}}


def load_reference(model_id: str, revision: str, cache_dir) -> SiglipModel:
    """The pinned SiglipModel at fp32 on CPU — what ai-eyes runs today (DEFAULT_DTYPE = None means
    full precision, engine.py:87). This is also the model the wrapper exports."""
    model = SiglipModel.from_pretrained(model_id, revision=revision, cache_dir=str(cache_dir),
                                        torch_dtype=torch.float32)
    model.eval()
    return model


def export_ir(model_id: str, revision: str, cache_dir, output_dir) -> dict:
    """Export the wrapper through optimum-intel's exporter (export_from_model, main_export's inner
    call) with the custom config; reuse a finished export. Returns export metadata for the
    receipt. CPU-only work; no devices are touched here."""
    from optimum.exporters.openvino.convert import export_from_model

    output_dir = Path(output_dir)
    xml = output_dir / (IR_STEM + ".xml")
    bin_ = output_dir / (IR_STEM + ".bin")
    if xml.exists() and bin_.exists():
        return {"reused": True, "seconds": None, "export_dir": str(output_dir),
                "path": "optimum export_from_model + custom SiglipOpenVINOConfig "
                        "(custom_export_configs; no registry change)"}
    output_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    wrapper = SiglipImageFeaturesWrapper(load_reference(model_id, revision, cache_dir))
    wrapper.eval()
    cfg = SiglipImageFeaturesOpenVINOConfig(wrapper.config, task="feature-extraction")
    export_from_model(wrapper, output=str(output_dir), task="feature-extraction",
                      custom_export_configs={"model": cfg})
    seconds = round(time.perf_counter() - t0, 1)
    if not (xml.exists() and bin_.exists()):
        raise SystemExit(f"export finished but {xml} / {bin_} are missing; the IR is not usable")
    return {"reused": False, "seconds": seconds, "export_dir": str(output_dir),
            "path": "optimum export_from_model + custom SiglipOpenVINOConfig "
                    "(custom_export_configs; no registry change)"}


def static_npu_ir(xml_path, out_path, shape=(1, 3, IMAGE_SIZE, IMAGE_SIZE)) -> dict:
    """The dynamic IR reshaped to the pinned static [1, 3, 384, 384] for the NPU (the addendum's
    device preparation), saved beside the dynamic IR. CPU and iGPU keep the dynamic IR."""
    import openvino as ov
    core = ov.Core()
    model = core.read_model(str(xml_path))
    model.reshape(list(shape))
    ov.save_model(model, str(out_path))
    return {"xml": str(out_path), "shape": list(shape)}


def embed(compiled, pixel_values) -> list:
    """One image through a compiled IR; the single output is image_embeds (batch 1 pinned)."""
    result = compiled([pixel_values])
    out = result[compiled.outputs[0]]
    return [float(x) for x in out[0].tolist()]
