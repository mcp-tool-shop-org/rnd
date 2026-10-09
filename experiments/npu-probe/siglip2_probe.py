#!/usr/bin/env python3
"""SigLIP image embeddings: transformers CPU (the reference ai-eyes runs) vs the NPU vs the Intel
iGPU — the pre-registered probe (prereg/siglip2-probe.md, 2026-10-09, with the same-day second
amendment). Speed and match only; no decision attached.

ai-eyes pins google/siglip2-so400m-patch14-384 @ e8e4872 (its engine.py, read-only) and calls
AutoModel -> SiglipModel.get_image_features at fp32. The checkpoint's model_type is "siglip", so the
IR is exported through optimum-intel's own exporter with a custom vision-only config
(ov_siglip_image.py). Before any device timing, the amendment's gate runs: the IR on OpenVINO CPU vs
the transformers reference over the same 50 seeded images — minimum cosine >= 0.9999 or the probe
stops, records the gate result, and times nothing.

50 images are sampled from the ai-eye-test project with
random.Random(20261009).sample(sorted(paths), 50), read-only; the sampled list lands in the receipt.
Each (image, device) is embedded 3 times, devices interleaved reference, NPU, iGPU per image. The
NPU compiles a static [1, 3, 384, 384] reshape of the IR; the gate and the iGPU use the dynamic IR.

Compared per image: cosine of each accelerator vector against the transformers reference (same
weights), reported as min/mean/p1 with the 5 worst. Per device: median seconds with min-max spread,
cold start (load/compile and first-embed components), and the export time once.

Failures are recorded outcomes: a compile error or an unpickable output is written to the receipt,
with one retry after dropping the compiled model; no retry loops. The 5090 is never touched: the
iGPU is found by name through npu_serve.intel_igpu (which refuses to guess), and no CUDA device is
referenced anywhere.

    siglip2_probe.py --images E:/AI/style-dataset-lab/projects/ai-eye-test \
        --cache E:/AI-Models/hf-cache --export-dir E:/AI/rnd-npu-index/siglip2-ov \
        --out results/2026-10-09-siglip2-probe.json
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.util
import json
import random
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import nomic_parity as np_

MODEL_ID = "google/siglip2-so400m-patch14-384"
REVISION = "e8e487298228002f3d8a82e0cd5c8ea9c567f57f"  # ai-eyes' pin (engine.py)
IMAGE_EXTS = (".png", ".webp", ".jpg")
SAMPLE_N = 50
SAMPLE_SEED = 20261009
REPEATS = 3
GATE_MIN_COSINE = 0.9999          # the second amendment's pass rule, fixed pre-run
DEVICE_ORDER = ("CPU", "NPU", "IGPU")   # the prereg's interleave order; CPU is the transformers reference


def list_images(root: Path) -> list:
    """Every image file under root (suffix match, case-insensitive), sorted as strings."""
    return sorted(str(p) for p in Path(root).rglob("*")
                  if p.is_file() and p.suffix.lower() in IMAGE_EXTS)


def sample_images(paths: list, n: int = SAMPLE_N, seed: int = SAMPLE_SEED) -> list:
    """The prereg's pin: random.Random(20261009).sample(sorted(paths), 50)."""
    paths = sorted(paths)
    if len(paths) < n:
        raise SystemExit(f"expected at least {n} images, found {len(paths)}")
    return random.Random(seed).sample(paths, n)


def device_stats(seconds: list) -> dict:
    return {"n": len(seconds),
            "median_s": round(statistics.median(seconds), 4) if seconds else None,
            "min_s": round(min(seconds), 4) if seconds else None,
            "max_s": round(max(seconds), 4) if seconds else None}


def summarize_matches(pairs: list) -> dict:
    """pairs: [(relpath, cosine vs the transformers reference)]. min/mean/p1 and the 5 worst,
    lowest cosine first."""
    vals = [c for _, c in pairs]
    worst = sorted(pairs, key=lambda pc: (pc[1], pc[0]))[:5]
    return {"n": len(pairs), "min": round(min(vals), 5) if vals else None,
            "mean": round(sum(vals) / len(vals), 5) if vals else None,
            "p1": round(np_.p1(vals), 5) if vals else None,
            "worst": [{"image": p, "cosine": round(c, 5)} for p, c in worst]}


def pooled_vector(out) -> list:
    """The pooled image embedding from a forward result: pooler_output for the CLIP family,
    then image_embeds / pooled_output, then a single output by itself. Accepts a ModelOutput or a
    plain mapping. Batch must be 1 — the probe is single-image."""
    keys = list(out.keys()) if hasattr(out, "keys") else []
    v = None
    for name in ("pooler_output", "image_embeds", "pooled_output"):
        if name in keys and out[name] is not None:
            v = out[name]
            break
    if v is None and len(keys) == 1:
        v = out[keys[0]]
    if v is None:
        raise SystemExit(f"cannot pick the embedding out of output keys {sorted(keys)}; aborting")
    if hasattr(v, "tolist"):
        v = v.tolist()
    if isinstance(v, (list, tuple)) and v and isinstance(v[0], (list, tuple)):
        if len(v) != 1:
            raise SystemExit(f"expected batch 1, got {len(v)}; the probe is single-image")
        v = v[0]
    if not v:
        raise SystemExit("empty embedding from the model; aborting")
    return [float(x) for x in v]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def hub_cache(path: Path) -> Path:
    """HuggingFace's hub cache is the dir that holds models--org--name dirs. Accept being handed
    HF_HOME or the hub dir itself and normalize; anything else passes through untouched."""
    path = Path(path)
    if path.name == "hub":
        return path
    hub = path / "hub"
    return hub if hub.is_dir() else path


def _npu_serve():
    """npu_serve loaded lazily: it imports openvino at module level, and this file's pure parts
    must stay importable on the plain repo python (the tests)."""
    spec = importlib.util.spec_from_file_location("npu_serve", HERE / "npu_serve.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ov_siglip_image():
    """ov_siglip_image loaded lazily for the same reason: it imports torch/transformers/optimum
    at module level and only runs in the npu-openvino venv."""
    spec = importlib.util.spec_from_file_location("ov_siglip_image", HERE / "ov_siglip_image.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def registry_context() -> dict:
    """Why this export path is legal on this venv, recorded: the corrected premise (siglip IS
    registered) and the first amendment's finding (siglip2 is not), both re-checked at run time."""
    out = {}
    try:
        import optimum.exporters.openvino  # noqa: F401 -- registering the openvino tasks
        from optimum.exporters.tasks import TasksManager
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {str(e)[:300]}"}
    for mtype in ("siglip", "siglip2"):
        try:
            tasks = TasksManager.get_supported_tasks_for_model_type(
                mtype, exporter="openvino", library_name="transformers")
            out[mtype] = {"supported": True, "tasks": sorted(tasks)}
        except Exception as e:  # noqa: BLE001 -- the exact error is part of the finding
            out[mtype] = {"supported": False, "error": f"{type(e).__name__}: {str(e)[:300]}"}
    return out


def env_versions() -> dict:
    import importlib.metadata as im
    def ver(name):
        try:
            return im.version(name)
        except im.PackageNotFoundError:
            return None
    return {"python": sys.version.split()[0], "openvino": ver("openvino"),
            "optimum": ver("optimum"), "optimum-intel": ver("optimum-intel"),
            "transformers": ver("transformers"), "torch": ver("torch"),
            "numpy": ver("numpy"), "pillow": ver("pillow")}


def load_processor(cache: Path):
    """ai-eyes' own processor path: AutoProcessor at the pinned revision (resolves to
    SiglipProcessor; engine.py:299)."""
    from transformers import AutoProcessor
    return AutoProcessor.from_pretrained(MODEL_ID, revision=REVISION, cache_dir=str(cache))


def ref_embed(ref_model, pixel_values) -> list:
    """One image through the transformers reference: get_image_features(pixel_values) ->
    pooler_output, exactly ai-eyes' call (engine.py:691/696), batch 1 pinned, fp32, no grad."""
    import torch
    with torch.no_grad():
        out = ref_model.get_image_features(pixel_values=torch.from_numpy(pixel_values))
    return pooled_vector({"pooler_output": getattr(out, "pooler_output", out)})


def resolve_devices(core) -> dict:
    """{label: meta} for the two OpenVINO devices. The iGPU is found by name; anything else
    GPU-shaped is refused upstream (it could be the 5090). The CPU row is the transformers
    reference, not an OpenVINO device, so it is not resolved here."""
    ns = _npu_serve()
    out = {}
    for label, dev in (("NPU", "NPU"), ("IGPU", ns.intel_igpu(core))):
        try:
            full = core.get_property(dev, "FULL_DEVICE_NAME").strip()
        except Exception:  # not available at all -> recorded in the compile leg instead
            full = None
        out[label] = {"ov_device": dev, "full_name": full, "available": full is not None}
    return out


def compile_with_retry(core, model_or_path, ov_device: str):
    """(compiled, meta): compile on one device with the one allowed retry after dropping the
    first failed attempt. A compile error is a recorded outcome, not a loop."""
    attempts, err, compiled, load_seconds = 0, None, None, None
    while attempts < 2:
        attempts += 1
        try:
            t0 = time.perf_counter()
            compiled = core.compile_model(model_or_path, ov_device)
            load_seconds = round(time.perf_counter() - t0, 1)
            err = None
            break
        except Exception as e:  # noqa: BLE001 -- the failure text is the finding
            err = f"{type(e).__name__}: {str(e)[:600]}"
            compiled = None
            gc.collect()  # drop the failed attempt before the one allowed retry
    return compiled, {"attempts": attempts, "load_seconds": load_seconds, "load_error": err}


def ov_embed(compiled, pixel_values) -> list:
    """One image through a compiled IR; outputs keyed by port name (the custom config's single
    output is image_embeds; pooled_vector picks it)."""
    result = compiled([pixel_values])
    return pooled_vector({port.get_any_name(): result[port] for port in compiled.outputs})


def export_digest(export_dir: Path, stem: str) -> dict:
    out = {"xml_sha256": None, "bytes": 0}
    xml = export_dir / (stem + ".xml")
    comp = export_dir / (stem + ".bin")
    for p in (xml, comp):
        if not p.exists():
            raise SystemExit(f"{p} missing after export; the cache is not usable")
        out["bytes"] += p.stat().st_size
    out["xml_sha256"] = sha256_file(xml)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--images", type=Path, required=True, help="the ai-eye-test project dir (read-only)")
    ap.add_argument("--cache", type=Path, required=True, help="the HF cache with the pinned snapshot")
    ap.add_argument("--export-dir", type=Path, required=True,
                    help="where the OpenVINO export lives (outside the repo)")
    ap.add_argument("--out", type=Path, required=True, help="the receipt JSON")
    ap.add_argument("--limit", type=int, default=None,
                    help="first N sampled images only; marks the receipt as a smoke run")
    ap.add_argument("--gate-only", action="store_true",
                    help="export, transformers reference and the equivalence gate only — the CPU-"
                         "window leg; the device legs wait for the ledgered NPU/iGPU session")
    a = ap.parse_args()
    process_start = time.time()
    t0_wall = time.perf_counter()

    root_images = a.images.resolve()
    images = sample_images(list_images(root_images))
    if a.limit is not None:
        images = images[:a.limit]
    rel = {p: str(Path(p).relative_to(root_images)) for p in images}

    cache = hub_cache(a.cache)
    processor = load_processor(cache)
    from PIL import Image
    import numpy as np
    pixels, pre_secs = {}, []
    for p in images:
        t0 = time.perf_counter()
        with Image.open(p) as im:
            pv = processor(images=im.convert("RGB"), return_tensors="np")["pixel_values"]
        pixels[p] = np.asarray(pv, dtype=np.float32)
        pre_secs.append(round(time.perf_counter() - t0, 4))

    ov_img = _ov_siglip_image()
    registry = registry_context()
    import openvino as ov
    core = ov.Core()

    t0 = time.perf_counter()
    ref = ov_img.load_reference(MODEL_ID, REVISION, cache)
    ref_load_s = round(time.perf_counter() - t0, 1)

    export = {"registry_context": registry, "model_id": MODEL_ID, "revision": REVISION,
              "ir": ov_img.export_ir(MODEL_ID, REVISION, cache, a.export_dir)}
    export["digest"] = export_digest(a.export_dir, ov_img.IR_STEM)
    xml_path = a.export_dir / (ov_img.IR_STEM + ".xml")
    ref_vecs = {p: ref_embed(ref, pixels[p]) for p in images}

    # --- the amendment's equivalence gate, before any device timing -------------------------
    gate = {"rule": f"min cosine >= {GATE_MIN_COSINE} vs the transformers reference",
            "ov_cpu_full_name": core.get_property("CPU", "FULL_DEVICE_NAME").strip()}
    gate_model, gate_meta = compile_with_retry(core, str(xml_path), "CPU")
    gate["compile"] = gate_meta
    gate_compiled = gate_model is not None
    gate_passed = False
    if gate_model is not None:
        gate_secs, gate_pairs = [], []
        for p in images:
            t0 = time.perf_counter()
            v = ov_embed(gate_model, pixels[p])
            gate_secs.append(round(time.perf_counter() - t0, 4))
            gate_pairs.append((rel[p], np_.cosine(v, ref_vecs[p])))
        gate["cosine_vs_reference"] = summarize_matches(gate_pairs)
        gate["timing"] = device_stats(gate_secs)
        gate_passed = gate["cosine_vs_reference"]["min"] is not None and \
            gate["cosine_vs_reference"]["min"] >= GATE_MIN_COSINE
        del gate_model
        gc.collect()
    gate["passed"] = gate_passed
    if not gate_passed:
        gate["status"] = ("miss — the probe stops here, no device timing" if gate_compiled
                          else "the IR failed to compile on CPU — the probe stops here")

    dev_report = {"CPU": {"kind": "transformers SiglipModel, fp32 (ai-eyes' reference)",
                          "load_seconds": ref_load_s}}
    times = {label: [] for label in ("CPU",)}
    acc_vecs = {"CPU": ref_vecs}
    first_embed = {}
    match = {}

    def write_receipt(devices_ok: bool) -> dict:
        receipt = {"date": time.strftime("%Y-%m-%d"),
                   "kind": "npu-probe: SigLIP image embeddings, speed and match only",
                   "prereg": "experiments/npu-probe/prereg/siglip2-probe.md",
                   "smoke": a.limit is not None, "limit": a.limit,
                   "export": export, "environment": env_versions(), "gate": gate,
                   "images": {"root": str(root_images).split(":\\")[-1], "sampled_n": len(images),
                              "sampled": [rel[p] for p in images], "seed": SAMPLE_SEED,
                              "selector": "random.Random(seed).sample(sorted(paths), 50)"},
                   "repeats": REPEATS, "device_order": list(DEVICE_ORDER),
                   "preprocess": {**device_stats(pre_secs),
                                  "note": "CPU-side once per image, shared across devices and repeats",
                                  "processor": "AutoProcessor at the pinned revision (ai-eyes' path)"},
                   "devices": dev_report, "match_vs_reference": match,
                   "comparison_note": "cosine and timing only; no quality claim",
                   "wall_seconds_total": round(time.perf_counter() - t0_wall, 1)}
        if not devices_ok:
            receipt["gate_only_cpu_leg" if a.gate_only and gate_passed else "stopped"] = gate["status"]
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {a.out}")
        return receipt

    if a.gate_only:
        if gate_passed:
            gate["status"] = "passed; device legs await the Publisher-logged NPU/iGPU session"
            write_receipt(devices_ok=False)
            print(f"gate passed (min cosine {gate['cosine_vs_reference']['min']}); device legs held")
            raise SystemExit(0)
        write_receipt(devices_ok=False)
        raise SystemExit(f"gate stopped the probe: {gate['status']}")

    if not gate_passed:
        write_receipt(devices_ok=False)
        raise SystemExit(f"gate stopped the probe: {gate['status']}")

    # --- device legs (inside the Publisher-logged NPU/iGPU window) --------------------------
    devices = resolve_devices(core)
    models = {}
    for label in ("NPU", "IGPU"):
        info = dict(devices[label])
        if not info["available"]:
            info["status"] = "device_unavailable"
            dev_report[label] = info
            continue
        if label == "NPU":
            static = ov_img.static_npu_ir(xml_path, a.export_dir / "openvino_model_static-npu.xml")
            info["static_ir"] = {"shape": static["shape"],
                                 **export_digest(a.export_dir, "openvino_model_static-npu")}
            target = str(a.export_dir / "openvino_model_static-npu.xml")
        else:
            target = str(xml_path)
        model, meta = compile_with_retry(core, target, info["ov_device"])
        info.update(meta)
        info["status"] = "ok" if model is not None else "load_error"
        dev_report[label] = info
        if model is not None:
            models[label] = model
            times[label] = []
            acc_vecs[label] = {}
            info["inputs"] = [i.get_any_name() for i in model.inputs]

    for rep in range(REPEATS):
        for p in images:
            for label in DEVICE_ORDER:
                if label == "CPU":
                    t0 = time.perf_counter()
                    v = ref_embed(ref, pixels[p])
                elif label in models:
                    t0 = time.perf_counter()
                    v = ov_embed(models[label], pixels[p])
                else:
                    continue
                dt = time.perf_counter() - t0
                times[label].append(round(dt, 4))
                if label not in first_embed:
                    first_embed[label] = {"first_embed_seconds": round(dt, 4),
                                          "from_process_start": round(time.time() - process_start, 1)}
                if rep == 0 and label != "CPU":
                    acc_vecs[label][p] = v
        print(f"pass {rep + 1}/{REPEATS} done", flush=True)

    for label in ("NPU", "IGPU"):
        if acc_vecs.get(label):
            match[label] = summarize_matches(
                [(rel[p], np_.cosine(acc_vecs[label][p], ref_vecs[p])) for p in images])
    for label, info in dev_report.items():
        if times.get(label):
            info["timing"] = device_stats(times[label])
        info.update(first_embed.get(label, {}))

    write_receipt(devices_ok=True)
    for label in DEVICE_ORDER:
        d = dev_report[label]
        if d.get("timing"):
            print(f"{label:5s} median {d['timing']['median_s']}s  "
                  f"({d['timing']['min_s']}-{d['timing']['max_s']}s)", flush=True)
        else:
            print(f"{label:5s} {d.get('status', 'ok')}: {d.get('load_error') or d.get('full_name') or ''}",
                  flush=True)


if __name__ == "__main__":
    main()
