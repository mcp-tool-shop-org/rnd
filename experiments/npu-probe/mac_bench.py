"""Exercise the multiply-accumulate engines directly: how many operations per second does each Intel device
really deliver, in FP16 and INT8?

Builds plain OpenVINO graphs, with no model behind them:
- a square matmul, Y = X·W, at n = 1024, 2048 and 4096: 2·n³ operations;
- a 3×3 convolution, 64 → 64 channels on a 1×64×224×224 input: 2·64·64·9·224² operations.
INT8 is made the way OpenVINO expects it: FakeQuantize (256 levels) on the input and the weights, which the
NPU and iGPU compile to integer kernels. Devices: NPU, the Intel iGPU (found by name), and CPU. Never the 5090.

  E:/AI/envs/npu-openvino/Scripts/python.exe mac_bench.py --out results/<date>-mac.json
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np
import openvino as ov
import openvino.opset13 as ops


def const(arr: np.ndarray):
    """A weight constant, float32 only. NumPy 2 (NEP 50) promotes float32 * np.float64 to float64, and a float64
    constant fails OpenVINO's MatMul type check (2026-10-09: chain_model divided by np.sqrt(n))."""
    assert arr.dtype == np.float32, f"constant dtype {arr.dtype}, expected float32"
    return ops.constant(arr)


def fq(node, lo, hi):
    """256-level FakeQuantize, OpenVINO's marker for INT8 execution."""
    c = lambda v: ops.constant(np.array(v, dtype=np.float32))
    return ops.fake_quantize(node, c(lo), c(hi), c(lo), c(hi), 256)


def matmul_model(n: int, int8: bool) -> ov.Model:
    x = ops.parameter([n, n], ov.Type.f32, name="x")
    w = const(np.random.default_rng(0).standard_normal((n, n)).astype(np.float32) * 0.02)
    a, b = (fq(x, -4, 4), fq(w, -0.1, 0.1)) if int8 else (x, w)
    return ov.Model([ops.matmul(a, b, False, False)], [x], f"matmul{n}")


def chain_model(n: int, depth: int, int8: bool) -> ov.Model:
    """`depth` matmuls in one graph, so one host transfer feeds depth x the arithmetic: closer to the
    engine's own rate than a single matmul, whose time is mostly moving the input in and out."""
    x = ops.parameter([n, n], ov.Type.f32, name="x")
    rng = np.random.default_rng(0)
    y = fq(x, -4, 4) if int8 else x
    for _ in range(depth):
        w = const((rng.standard_normal((n, n)) / np.sqrt(n)).astype(np.float32))
        y = ops.matmul(y, fq(w, -0.1, 0.1) if int8 else w, False, False)
        if int8:
            y = fq(y, -4, 4)
    return ov.Model([y], [x], f"chain{depth}x{n}")


def conv_model(int8: bool) -> ov.Model:
    x = ops.parameter([1, 64, 224, 224], ov.Type.f32, name="x")
    w = const(np.random.default_rng(0).standard_normal((64, 64, 3, 3)).astype(np.float32) * 0.05)
    a, b = (fq(x, -4, 4), fq(w, -0.2, 0.2)) if int8 else (x, w)
    return ov.Model([ops.convolution(a, b, [1, 1], [1, 1], [1, 1], [1, 1])], [x], "conv3x3")


def bench(core, model, device, shape, flops, seconds=3.0):
    t0 = time.perf_counter()
    c = core.compile_model(model, device, {"PERFORMANCE_HINT": "THROUGHPUT"} if device != "NPU" else {})
    compile_s = time.perf_counter() - t0
    req = c.create_infer_request()
    x = np.random.default_rng(1).standard_normal(shape).astype(np.float32)
    req.infer({0: x})  # warm
    n, t0 = 0, time.perf_counter()
    while time.perf_counter() - t0 < seconds:
        req.infer({0: x})
        n += 1
    dt = (time.perf_counter() - t0) / n
    return {"compile_s": round(compile_s, 2), "ms_per_call": round(dt * 1000, 3), "tops": round(flops / dt / 1e12, 3)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--only", default="", help="run only cases whose name starts with this")
    ap.add_argument("--cpu", action="store_true", help="include the CPU (it loads every core for a few seconds)")
    a = ap.parse_args()
    core = ov.Core()
    igpu = next((d for d in core.available_devices if d.startswith("GPU")
                 and core.get_property(d, "FULL_DEVICE_NAME").startswith("Intel")), None)
    devices = ["NPU"] + ([igpu] if igpu else []) + (["CPU"] if a.cpu else [])
    cases = [(f"matmul{n}", lambda i, n=n: matmul_model(n, i), [n, n], 2 * n**3) for n in (1024, 2048, 4096)]
    cases.append(("conv3x3", conv_model, [1, 64, 224, 224], 2 * 64 * 64 * 9 * 224 * 224))
    cases += [(f"chain8x{n}", lambda i, n=n: chain_model(n, 8, i), [n, n], 8 * 2 * n**3) for n in (2048, 4096)]
    rows = []
    cases = [c for c in cases if c[0].startswith(a.only)]
    for name, build, shape, flops in cases:
        for prec in ("fp16", "int8"):
            for d in devices:
                row = {"case": name, "precision": prec, "device": d}
                try:
                    row |= bench(core, build(prec == "int8"), d, shape, flops)
                except Exception as e:
                    row["error"] = f"{type(e).__name__}: {str(e)[:200]}"
                print(json.dumps(row), flush=True)
                rows.append(row)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({"openvino": ov.__version__, "devices": {d: core.get_property(d, "FULL_DEVICE_NAME")
                                 for d in devices}, "rows": rows}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
