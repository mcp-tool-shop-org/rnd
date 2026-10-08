"""Does torch.compile work on Windows with triton-windows and the cu134 nightly?

Run with a Python that sees both (the probe venv adds aspire-cu134's site-packages via a .pth file,
so aspire's env is not modified). Prints one JSON line. GPU only after the Publisher grants it.
"""

from __future__ import annotations

import json
import time


def main() -> None:
    import torch
    import triton

    out = {"torch": torch.__version__, "cuda": torch.version.cuda, "triton": triton.__version__}
    net = torch.nn.Sequential(
        torch.nn.Linear(3072, 512), torch.nn.LayerNorm(512), torch.nn.GELU(), torch.nn.Linear(512, 1)
    ).cuda()
    x = torch.randn(16, 3072, device="cuda")
    ref = net(x)
    for mode in ("default", "reduce-overhead"):
        try:
            torch._dynamo.reset()
            f = torch.compile(net, mode=mode)
            t = time.perf_counter()
            y = f(x)
            torch.cuda.synchronize()
            compile_s = time.perf_counter() - t
            for _ in range(5):
                y = f(x)
            torch.cuda.synchronize()
            t = time.perf_counter()
            for _ in range(1000):
                y = f(x)
            torch.cuda.synchronize()
            out[mode] = {
                "ok": True,
                "compile_s": compile_s,
                "us_per_call": (time.perf_counter() - t) * 1e3,
                "max_diff": float((y - ref).abs().max()),
            }
        except Exception as e:  # report, don't crash: the failure is the finding
            out[mode] = {"ok": False, "error": f"{type(e).__name__}: {str(e)[:400]}"}
    t = time.perf_counter()
    for _ in range(1000):
        net(x)
    torch.cuda.synchronize()
    out["eager_us_per_call"] = (time.perf_counter() - t) * 1e3
    print(json.dumps(out))


if __name__ == "__main__":
    main()
