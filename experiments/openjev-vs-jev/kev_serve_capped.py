"""Run kev.serve with PyTorch's GPU memory capped, so an oversized request fails with an
out-of-memory error instead of paging the 5090 past the watchdog ceiling.

    python kev_serve_capped.py <fraction> --run ... --port ...
"""
import runpy
import sys

import torch

frac = float(sys.argv.pop(1))
torch.cuda.set_per_process_memory_fraction(frac, 0)
print(f"capped CUDA memory at {frac:.2f} of {torch.cuda.get_device_properties(0).total_memory / 2**30:.1f} GiB", flush=True)
sys.argv[0] = "kev.serve"
runpy.run_module("kev.serve", run_name="__main__")
