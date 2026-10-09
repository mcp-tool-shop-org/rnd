#!/usr/bin/env python3
"""SigLIP2 image embeddings on CPU vs the NPU vs the Intel iGPU — the pre-registered probe
(prereg/siglip2-probe.md, 2026-10-09). Speed and match only; no decision attached.

ai-eyes pins google/siglip2-so400m-patch14-384 @ e8e4872 (its engine.py, read-only). The vision
tower is converted once to OpenVINO IR from that snapshot at full fp32 (prereg amendment
2026-10-09: optimum-intel 2.2.0 has no siglip2 registration; the check is re-run and recorded) — 50 images are sampled from the ai-eye-test project with
random.Random(20261009).sample(sorted(paths), 50), read-only; the sampled list lands in the
receipt. Each (image, device) is embedded 3 times, devices interleaved CPU, NPU, iGPU per image.

Compared per image: cosine of each accelerator vector against the CPU's (same weights), reported
as min/mean/p1 with the 5 worst. Per device: median seconds with min-max spread, cold start
(process start to first embed, with compile and first-embed components) and export time once.

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
DEVICE_ORDER = ("CPU", "NPU", "IGPU")   # the prereg's interleave order


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
    """pairs: [(relpath, cosine vs CPU)]. min/mean/p1 and the 5 worst, lowest cosine first."""
    vals = [c for _, c in pairs]
    worst = sorted(pairs, key=lambda pc: (pc[1], pc[0]))[:5]
    return {"n": len(pairs), "min": round(min(vals), 5) if vals else None,
            "mean": round(sum(vals) / len(vals), 5) if vals else None,
            "p1": round(np_.p1(vals), 5) if vals else None,
            "worst": [{"image": p, "cosine": round(c, 5)} for p, c in worst]}


def pooled_vector(out) -> list:
    """The pooled image embedding from an optimum forward result: pooler_output for the CLIP
    family exports, then image_embeds / pooled_output, then a single output by itself. Accepts a
    ModelOutput or a plain mapping. Batch must be 1 — the probe is single-image."""
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


IR_XML = "siglip2_vision.xml"


def optimum_siglip2_check() -> dict:
    """The registry check behind the prereg's amendment, re-run and recorded: is siglip2
    exportable through optimum-intel on this venv? (Expected no on optimum-intel 2.2.0.)"""
    try:
        import optimum.exporters.openvino  # noqa: F401 -- registering the openvino tasks
        from optimum.exporters.tasks import TasksManager
        TasksManager.get_supported_tasks_for_model_type("siglip2", exporter="openvino",
                                                        library_name="transformers")
        return {"siglip2_supported": True, "error": None}
    except Exception as e:  # noqa: BLE001 -- the exact error is the finding
        return {"siglip2_supported": False,
                "error": f"{type(e).__name__}: {str(e)[:300]}"}


def export_model(cache: Path, export_dir: Path) -> dict:
    """The pinned snapshot's vision tower converted once to OpenVINO IR at fp32 (the prereg
    amendment's path), timed, reused when already on disk. The receipt gets the topology digest."""
    xml = export_dir / IR_XML
    if xml.exists():
        return {"reused": True, "seconds": None, "export_dir": str(export_dir),
                "path": "openvino.convert_model"}
    from transformers import Siglip2VisionModel
    import openvino as ov
    import torch
    export_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    tower = Siglip2VisionModel.from_pretrained(MODEL_ID, revision=REVISION,
                                               cache_dir=str(cache), torch_dtype=torch.float32)
    tower.eval()
    example = torch.zeros(1, 3, 384, 384)  # pinned single-image 384x384 input
    converted = ov.convert_model(tower, example_input=example, input=[1, 3, 384, 384])
    ov.save_model(converted, str(xml))
    return {"reused": False, "seconds": round(time.perf_counter() - t0, 1),
            "export_dir": str(export_dir), "path": "openvino.convert_model"}


def export_digest(export_dir: Path) -> dict:
    out = {"xml_sha256": None, "bytes": 0}
    xml = export_dir / IR_XML
    comp = export_dir / (IR_XML[:-4] + ".bin")
    for p in (xml, comp):
        if not p.exists():
            raise SystemExit(f"{p} missing after export; the cache is not usable")
        out["bytes"] += p.stat().st_size
    out["xml_sha256"] = sha256_file(xml)
    return out


def resolve_devices() -> dict:
    """{label: (openvino device string, full device name)} for the prereg's three. The iGPU is
    found by name; anything else GPU-shaped is refused upstream (it could be the 5090)."""
    ns = _npu_serve()
    import openvino as ov
    core = ov.Core()
    igpu = ns.intel_igpu(core)
    out = {}
    for label, dev in (("CPU", "CPU"), ("NPU", "NPU"), ("IGPU", igpu)):
        try:
            full = core.get_property(dev, "FULL_DEVICE_NAME").strip()
        except Exception:  # device not available at all -> recorded in the compile leg instead
            full = None
        out[label] = {"ov_device": dev, "full_name": full, "available": full is not None}
    return out


def compile_with_retry(export_dir: Path, ov_device: str):
    """(compiled, meta): compile the IR on one device with the one allowed retry after dropping
    the first failed attempt. A compile error is a recorded outcome, not a loop."""
    import openvino as ov
    attempts, err = 0, None
    compiled = None
    load_seconds = None
    core = ov.Core()
    while attempts < 2:
        attempts += 1
        try:
            t0 = time.perf_counter()
            compiled = core.compile_model(str(export_dir / IR_XML), ov_device)
            load_seconds = round(time.perf_counter() - t0, 1)
            err = None
            break
        except Exception as e:  # noqa: BLE001 -- the failure text is the finding
            err = f"{type(e).__name__}: {str(e)[:600]}"
            compiled = None
            gc.collect()  # drop the failed attempt before the one allowed retry
    return compiled, {"attempts": attempts, "load_seconds": load_seconds, "load_error": err}


def embed_one(compiled, pixel_values) -> list:
    """One image through a compiled OpenVINO model, output keyed by the converted graph's port
    names (pooler_output is the embedding; pooled_vector picks it)."""
    ports = compiled.outputs
    result = compiled([pixel_values])
    return pooled_vector({port.get_any_name(): result[port] for port in ports})


def model_input_names(compiled) -> list:
    """The compiled model's input names (one on this IR); recorded in the receipt."""
    return [i.get_any_name() for i in compiled.inputs]


def load_processor(cache: Path):
    """The repo's own preprocessor_config (the 384 px pipeline), from the pinned snapshot."""
    from transformers import AutoImageProcessor
    return AutoImageProcessor.from_pretrained(MODEL_ID, revision=REVISION, cache_dir=str(cache))


def env_versions() -> dict:
    import importlib.metadata as im
    def ver(name):
        try:
            return im.version(name)
        except im.PackageNotFoundError:
            return None
    return {"python": sys.version.split()[0], "openvino": ver("openvino"),
            "optimum": ver("optimum"), "optimum-intel": ver("optimum-intel"),
            "transformers": ver("transformers"), "numpy": ver("numpy"), "pillow": ver("pillow")}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--images", type=Path, required=True, help="the ai-eye-test project dir (read-only)")
    ap.add_argument("--cache", type=Path, required=True, help="the HF cache with the pinned snapshot")
    ap.add_argument("--export-dir", type=Path, required=True,
                    help="where the OpenVINO export lives (outside the repo)")
    ap.add_argument("--out", type=Path, required=True, help="the receipt JSON")
    ap.add_argument("--limit", type=int, default=None,
                    help="first N sampled images only; marks the receipt as a smoke run")
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

    export = optimum_siglip2_check() | {"ir": export_model(cache, a.export_dir)}
    export["digest"] = export_digest(a.export_dir)
    export["model"] = MODEL_ID
    export["revision"] = REVISION

    devices = resolve_devices()
    models, dev_report = {}, {}
    for label in DEVICE_ORDER:
        info = dict(devices[label])
        if not info["available"]:
            info["status"] = "device_unavailable"
            dev_report[label] = info
            continue
        model, meta = compile_with_retry(a.export_dir, info["ov_device"])
        info.update(meta)
        info["status"] = "ok" if model is not None else "load_error"
        dev_report[label] = info
        if model is not None:
            models[label] = model
            info["inputs"] = model_input_names(model)
    if "CPU" not in models:
        raise SystemExit("the CPU reference failed to compile; the probe cannot run "
                         "(receipt aborted before any timing)")

    times = {label: [] for label in models}
    ref_vecs, acc_vecs = {}, {label: {} for label in models}
    first_embed = {}
    for rep in range(REPEATS):
        for p in images:
            for label in DEVICE_ORDER:
                if label not in models:
                    continue
                t0 = time.perf_counter()
                v = embed_one(models[label], pixels[p])
                dt = time.perf_counter() - t0
                times[label].append(round(dt, 4))
                if label not in first_embed:
                    first_embed[label] = {"seconds": round(dt, 4),
                                          "from_process_start": round(time.time() - process_start, 1)}
                if rep == 0:
                    acc_vecs[label][p] = v
            if rep == 0:
                ref_vecs[p] = acc_vecs["CPU"][p]
        print(f"pass {rep + 1}/{REPEATS} done", flush=True)

    match = {}
    for label in ("NPU", "IGPU"):
        if label in acc_vecs and acc_vecs[label]:
            match[label] = summarize_matches(
                [(rel[p], np_.cosine(acc_vecs[label][p], ref_vecs[p])) for p in images])
    for label, info in dev_report.items():
        if times.get(label):
            info["timing"] = device_stats(times[label])
            info.update(first_embed.get(label, {}))

    receipt = {"date": time.strftime("%Y-%m-%d"),
               "kind": "npu-probe: SigLIP2 image embeddings, speed and match only",
               "prereg": "experiments/npu-probe/prereg/siglip2-probe.md",
               "smoke": a.limit is not None, "limit": a.limit,
               "model": export, "environment": env_versions(),
               "images": {"root": str(root_images).split(":\\")[-1], "sampled_n": len(images),
                          "sampled": [rel[p] for p in images], "seed": SAMPLE_SEED,
                          "selector": "random.Random(seed).sample(sorted(paths), 50)"},
               "repeats": REPEATS, "device_order": list(DEVICE_ORDER),
               "preprocess": {**device_stats(pre_secs),
                              "note": "CPU-side once per image, shared across devices and repeats"},
               "devices": dev_report, "match_vs_cpu": match,
               "wall_seconds_total": round(time.perf_counter() - t0_wall, 1)}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {a.out}")
    for label in DEVICE_ORDER:
        d = dev_report[label]
        if d.get("timing"):
            print(f"{label:5s} median {d['timing']['median_s']}s  "
                  f"({d['timing']['min_s']}-{d['timing']['max_s']}s)", flush=True)
        else:
            print(f"{label:5s} {d['status']}: {d.get('load_error') or d.get('full_name')}",
                  flush=True)


if __name__ == "__main__":
    main()
