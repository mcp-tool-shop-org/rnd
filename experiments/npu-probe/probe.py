"""Can the Core Ultra 9 285K's NPU (Intel AI Boost) carry the studio's small, always-on models?

Times an embedding model and an NLI cross-encoder on the NPU against the CPU, through OpenVINO, and checks
the NPU's outputs against the CPU's. Devices are CPU and NPU only: OpenVINO also sees the RTX 5090 as a
GPU device, and this script must never use it (the 5090 is shared through the Publisher's grants).

  E:/AI/envs/npu-openvino/Scripts/python.exe probe.py --out results/<date>.json
"""

import argparse
import json
import statistics
import time
from pathlib import Path

import numpy as np
import openvino as ov
from optimum.intel import OVModelForFeatureExtraction, OVModelForSequenceClassification
from transformers import AutoTokenizer

ALLOWED = ("CPU", "NPU")
SEQ = 512  # the NPU wants static shapes; 512 tokens covers a chunk (offrig's 800-2000 chars) or a claim + evidence

EMBEDDERS = ["BAAI/bge-small-en-v1.5", "BAAI/bge-base-en-v1.5"]
NLI = ["cross-encoder/nli-deberta-v3-base"]

TEXTS = [
    "Lane ports start at 11500, two apart, for 64 lanes; the port above each lane's own is the handoff runner's second tunnel.",
    "A synchronous run defaults to 30 seconds and is capped at 120; a requested timeout of 0 becomes 1 second.",
    "The calibration runner refuses cloud model names and any server that is not on this machine.",
    "Chunks run from 800 to 2000 characters, and files larger than 1,000,000 bytes are not indexed.",
] * 4

PAIRS = [  # (premise = evidence, hypothesis = claim, expected)
    ("pub const LANE_PORT_BASE: u16 = 11500;\npub const LANE_PORT_STEP: u16 = 2;", "Lane ports start at 11500 and are two apart.", "entailment"),
    ("pub const LANE_PORT_BASE: u16 = 11500;\npub const LANE_PORT_STEP: u16 = 2;", "Lane ports start at 11500 and are one apart.", "contradiction"),
    ("export const MIN_CALIBRATION_RUNS = 5;", "A pack needs at least 3 recorded runs before a rate is claimed.", "contradiction"),
    ("export const MIN_CALIBRATION_RUNS = 5;", "A pack needs at least 5 recorded runs before a rate is claimed.", "entailment"),
] * 4


def device_name(core: ov.Core, d: str) -> str:
    return core.get_property(d, "FULL_DEVICE_NAME")


def timed(fn, n_warm=2, n=10):
    for _ in range(n_warm):
        fn()
    t = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        t.append(time.perf_counter() - t0)
    return statistics.median(t), min(t)


def load(cls, name: str, device: str, batch: int):
    m = cls.from_pretrained(name, export=True, compile=False)
    m.reshape(batch, SEQ)  # static shape, required by the NPU and harmless on CPU
    m.to(device)
    t0 = time.perf_counter()
    m.compile()
    return m, time.perf_counter() - t0


def embed_case(name: str, device: str, batch: int) -> dict:
    tok = AutoTokenizer.from_pretrained(name)
    m, compile_s = load(OVModelForFeatureExtraction, name, device, batch)
    enc = tok(TEXTS[:batch], padding="max_length", truncation=True, max_length=SEQ, return_tensors="np")

    def run():
        out = m(**enc).last_hidden_state[:, 0]  # bge uses the CLS vector
        return out / np.linalg.norm(out, axis=1, keepdims=True)

    vec = np.asarray(run())
    med, best = timed(run)
    return {"compile_s": round(compile_s, 2), "batch": batch, "median_s": round(med, 4), "best_s": round(best, 4),
            "items_per_s": round(batch / med, 1), "_vec": vec}


def nli_case(name: str, device: str, batch: int) -> dict:
    tok = AutoTokenizer.from_pretrained(name)
    m, compile_s = load(OVModelForSequenceClassification, name, device, batch)
    labels = [m.config.id2label[i].lower() for i in range(len(m.config.id2label))]
    p = PAIRS[:batch]
    enc = tok([a for a, _, _ in p], [b for _, b, _ in p], padding="max_length", truncation=True, max_length=SEQ,
              return_tensors="np")

    def run():
        return np.asarray(m(**enc).logits)

    logits = run()
    med, best = timed(run)
    got = [labels[i] for i in logits.argmax(1)]
    right = sum(g == e for g, (_, _, e) in zip(got, p))
    return {"compile_s": round(compile_s, 2), "batch": batch, "median_s": round(med, 4), "best_s": round(best, 4),
            "items_per_s": round(batch / med, 1), "right": f"{right}/{len(p)}", "_logits": logits}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--batches", default="1,8")
    a = ap.parse_args()
    core = ov.Core()
    devices = [d for d in core.available_devices if d in ALLOWED]
    report = {"openvino": ov.__version__, "devices": {d: device_name(core, d) for d in devices},
              "excluded_devices": [d for d in core.available_devices if d not in ALLOWED], "seq": SEQ, "cases": []}
    batches = [int(b) for b in a.batches.split(",")]
    for kind, names, fn, key in (("embed", EMBEDDERS, embed_case, "_vec"), ("nli", NLI, nli_case, "_logits")):
        for name in names:
            for batch in batches:
                ref = None
                for d in ("CPU", "NPU"):
                    row = {"kind": kind, "model": name, "device": d}
                    try:
                        r = fn(name, d, batch)
                        out = r.pop(key)
                        if d == "CPU":
                            ref = out
                        elif ref is not None:
                            if kind == "embed":
                                r["min_cosine_vs_cpu"] = round(float((out * ref).sum(1).min()), 5)
                            else:
                                r["max_abs_logit_diff_vs_cpu"] = round(float(np.abs(out - ref).max()), 4)
                                r["argmax_agrees_with_cpu"] = bool((out.argmax(1) == ref.argmax(1)).all())
                        row |= r
                    except Exception as e:  # an op the NPU can't compile is a finding, not a crash
                        row["error"] = f"{type(e).__name__}: {str(e)[:300]}"
                    print(json.dumps(row), flush=True)
                    report["cases"].append(row)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
