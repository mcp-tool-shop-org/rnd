"""ov_siglip_image in the npu-openvino venv: the custom export config's input/output contract, the
wrapper returning exactly get_image_features' pooler_output (ai-eyes' pick), a full tiny export
through optimum-intel's export_from_model (the prereg amendment's path) with the IR names and the
static NPU reshape checked, and OV-CPU agreeing with the torch reference. rnd's CI installs none of
torch/openvino/optimum-intel, so every class skips there; the tests must pass in the venv. Tiny
random weights only — no downloads, no NPU/iGPU."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

PROBE = Path(__file__).resolve().parent.parent / "experiments" / "npu-probe"
sys.path.insert(0, str(PROBE))

HAVE_EXPORT = all(importlib.util.find_spec(m) is not None
                  for m in ("torch", "transformers", "openvino", "optimum"))
SKIP = "needs the npu-openvino venv (torch, transformers, openvino, optimum-intel); CI skips"


def _load():
    spec = importlib.util.spec_from_file_location("ov_siglip_image", PROBE / "ov_siglip_image.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _tiny_model():
    import torch
    from transformers import SiglipConfig, SiglipModel, SiglipVisionConfig, SiglipTextConfig
    tc = SiglipTextConfig(hidden_size=16, intermediate_size=32, num_hidden_layers=1,
                          num_attention_heads=2, vocab_size=32, max_position_embeddings=16)
    vc = SiglipVisionConfig(hidden_size=16, intermediate_size=32, num_hidden_layers=1,
                            num_attention_heads=2, image_size=28, patch_size=14, num_channels=3)
    # the dict form silently keeps defaults on transformers 5.5.4; pass the objects
    torch.manual_seed(0)
    return SiglipModel(SiglipConfig(vision_config=vc, text_config=tc)).eval()


@unittest.skipUnless(HAVE_EXPORT, SKIP)
class Wrapper(unittest.TestCase):
    def test_wrapper_returns_exactly_pooler_output(self):
        import torch
        oi = _load()
        m = _tiny_model()
        w = oi.SiglipImageFeaturesWrapper(m)
        self.assertEqual(w.config.model_type, "siglip")  # the corrected premise
        x = torch.rand(1, 3, 28, 28)
        with torch.no_grad():
            wrapped = w(x)
            direct = m.get_image_features(pixel_values=x)
        self.assertTrue(torch.is_tensor(wrapped))
        self.assertTrue(torch.equal(wrapped, direct.pooler_output))
        self.assertEqual(tuple(wrapped.shape), (1, 16))


@unittest.skipUnless(HAVE_EXPORT, SKIP)
class Config(unittest.TestCase):
    def test_input_and_output_contract(self):
        oi = _load()
        cfg = oi.SiglipImageFeaturesOpenVINOConfig(_tiny_model().config,
                                                   task="feature-extraction")
        self.assertEqual(list(cfg.inputs), ["pixel_values"])
        self.assertEqual(cfg.inputs["pixel_values"],
                         {0: "image_batch_size", 1: "num_channels", 2: "height", 3: "width"})
        self.assertEqual(list(cfg.outputs), ["image_embeds"])
        self.assertEqual(cfg.outputs["image_embeds"], {0: "image_batch_size"})
        dummy = cfg.generate_dummy_inputs(framework="pt")
        self.assertEqual(list(dummy), ["pixel_values"])
        self.assertEqual(tuple(dummy["pixel_values"].shape[1:]), (3, 28, 28))


@unittest.skipUnless(HAVE_EXPORT, SKIP)
class ExportEndToEnd(unittest.TestCase):
    """The amended path itself, tiny: wrapper through optimum-intel's export_from_model with the
    custom config, the IR contract, the static NPU reshape, and OV-CPU agreeing with torch."""

    def test_tiny_export_ir_contract(self):
        import numpy as np
        import torch
        oi = _load()
        m = _tiny_model()
        w = oi.SiglipImageFeaturesWrapper(m)
        from optimum.exporters.openvino.convert import export_from_model
        cfg = oi.SiglipImageFeaturesOpenVINOConfig(w.config, task="feature-extraction")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            export_from_model(w, output=str(out), task="feature-extraction",
                              custom_export_configs={"model": cfg})
            xml, bin_ = out / "openvino_model.xml", out / "openvino_model.bin"
            self.assertTrue(xml.exists() and bin_.exists())
            import openvino as ov
            core = ov.Core()
            ir = core.read_model(str(xml))
            self.assertEqual([i.get_any_name() for i in ir.inputs], ["pixel_values"])
            self.assertEqual([o.get_any_name() for o in ir.outputs], ["image_embeds"])
            # OV CPU must agree with the torch reference on identical input (the gate's shape)
            compiled = core.compile_model(str(xml), "CPU")
            x = np.random.RandomState(0).rand(1, 3, 28, 28).astype(np.float32)
            got = np.asarray(oi.embed(compiled, x), dtype=np.float32)
            with torch.no_grad():
                ref = w(torch.from_numpy(x)).numpy()[0].astype(np.float32)
            cos = float(np.dot(got, ref) / (np.linalg.norm(got) * np.linalg.norm(ref)))
            self.assertGreaterEqual(cos, 0.9999)
            # the static NPU reshape
            static = oi.static_npu_ir(xml, out / "static.xml", shape=(1, 3, 28, 28))
            ir2 = core.read_model(static["xml"])
            self.assertEqual(str(ir2.inputs[0].get_partial_shape()), "[1,3,28,28]")


@unittest.skipUnless(HAVE_EXPORT, SKIP)
class StaleIRGuard(unittest.TestCase):
    """export_ir reuses an IR only with a provenance sidecar matching the pin and the export
    stack; any mismatch — or a missing sidecar — forces a re-export instead of a silent reuse."""

    def test_reuse_requires_matching_sidecar(self):
        oi = _load()
        w = oi.SiglipImageFeaturesWrapper(_tiny_model())
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            first = oi.export_ir("tiny/test", "rev1", None, d, wrapper=w)
            self.assertFalse(first["reused"])
            self.assertFalse(first["sidecar"]["matched"])
            self.assertIsNone(first["sidecar"]["previous"])
            second = oi.export_ir("tiny/test", "rev1", None, d, wrapper=w)
            self.assertTrue(second["reused"])
            self.assertTrue(second["sidecar"]["matched"])
            fields = second["sidecar"]["fields"]
            self.assertEqual((fields["model_id"], fields["revision"]), ("tiny/test", "rev1"))
            self.assertTrue(fields["optimum-intel"] and fields["openvino"])
            # a different pin must not reuse the leftover IR
            third = oi.export_ir("tiny/test", "rev2", None, d, wrapper=w)
            self.assertFalse(third["reused"])
            self.assertEqual(third["sidecar"]["previous"]["revision"], "rev1")
            # and a missing sidecar never reuses silently
            (d / oi.SIDECAR_NAME).unlink()
            fourth = oi.export_ir("tiny/test", "rev2", None, d, wrapper=w)
            self.assertFalse(fourth["reused"])


if __name__ == "__main__":
    unittest.main()
