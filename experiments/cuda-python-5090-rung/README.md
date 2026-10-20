# CUDA Python on the RTX 5090: a smoke rung for six libraries

**Status:** closed, 2026-10-19. **The question:** do NVIDIA's CUDA Python libraries install and run on the studio
rig's RTX 5090 (consumer Blackwell, compute capability 12.0)? Their docs don't all say. This is the free rung that
gates any of them for rnd-data's optional GPU layer (`rnd-data[gpu]`), before any design depends on them. The
entry is [[2026-10-20-cuda-python-on-5090]].

## Method

- **A fresh environment** (`uv venv`, Python 3.12.13). No existing environment was touched.
- **Each library pinned exactly,** at the version the Publisher checked on PyPI the same day, with its CUDA 13 extra:
  `cuda-python==13.4.4`, `cuda-core[cu13]==1.2.2`, `cuda-cccl[cu13]==1.2.1`, `cupy-cuda13x[ctk]==14.2.0`,
  `numba-cuda[cu13]==0.30.4`, `nvmath-python[cu13]==1.0.0`, `cuda-tile[tileiras]==1.7.0`. These resolved to the
  CUDA 13.4 runtime wheels (`nvidia-cuda-runtime==13.4.92`, `cuda-toolkit==13.4.3`). The full list is in
  [`data/env-freeze.txt`](data/env-freeze.txt).
- **Per library, in its own process** ([`scripts/smoke_rung.py`](scripts/smoke_rung.py)):
  1. import it;
  2. read the device's compute capability (it must be 12.0);
  3. run one small kernel;
  4. check the result against NumPy on the CPU.
- **The kernels:**

  | Library | Kernel |
  |---|---|
  | `cuda.core` | an NVRTC-compiled `sm_120` cubin, launched by `cuda.core` |
  | CuPy | a `RawKernel` |
  | numba-cuda | a `@cuda.jit` axpy |
  | `cuda.compute` | `reduce_into` with `OpKind.PLUS` |
  | nvmath | a 512×512 fp32 `linalg.advanced.matmul` |
  | `cuda.tile` | a cuTile vector add |

- **The load,** stated to the Director before the run:
  - threads capped at 4 of 24;
  - peak VRAM 2,890 MiB against 2,552 MiB idle, far under the rig's 31,200 MiB ceiling;
  - each library under 3 s.
- **The rig:** driver 617.42, Windows 11.

## Results

| Library | Run 1 (NumPy 2.5.4) | Run 2 (NumPy 2.4.6) |
|---|---|---|
| `cuda.core` 1.2.2 | pass | pass |
| CuPy (`cupy-cuda13x`) 14.2.0 | pass | pass |
| numba-cuda 0.30.4 (numba 0.68.0) | **fail:** NumPy 2.5 removed `row_stack`, which numba 0.68 still calls | pass |
| `cuda.compute` (`cuda-cccl` 1.2.1) | fail: the test's own error (`reduce_into` takes keyword arguments only) | pass |
| nvmath-python 1.0.0 | pass | pass |
| `cuda.tile` (`cuda-tile` 1.7.0) | pass | pass |

The raw rows are in [`results/`](results/). In run 1's tracebacks, local paths are replaced with placeholders.

## What it means

- **All six run on the 5090 at compute capability 12.0,** on one shared environment, once NumPy is held below 2.5.
- **cuTile runs on consumer Blackwell.** That answers [[2026-10-07-cutile-on-sm120]].
- **NumPy is the shared pin to watch.** A `[gpu]` extra needs `numpy>=2.4,<2.5` until numba supports 2.5. Left
  alone, the resolver picks 2.5.
- **CuPy uses its own built-in CUDA 13.2 runtime** (`runtimeGetVersion` 13020), though the 13.4.92 runtime wheel is
  installed. It ran correctly.
  - A follow-up on 2026-10-20 ran [`scripts/cupy_runtime_check.py`](scripts/cupy_runtime_check.py) under the
    Publisher's grant. It brings a CuPy context up and lists the CUDA DLLs in the process.
  - No cudart DLL is loaded, although the env's 13.4 wheel ships `cudart64_13.dll`.
  - CuPy does load `nvrtc64_130_0.dll` and `cublasLt64_13.dll` from the 13.x wheels, and `nvrtc-builtins64_134.dll`
    from the system's CUDA 13.4 toolkit.
  - The output is in [`results/cupy-runtime-2026-10-20.txt`](results/cupy-runtime-2026-10-20.txt).
- **A smoke rung shows each library installs and runs a kernel here.** It says nothing yet about speed or about
  features for rnd-data. That comes from the design, after Argon's exploration.

**Licences:** the libraries are Apache-2.0, MIT and BSD-2-Clause. The CUDA runtime wheels they pull carry NVIDIA's
proprietary licence (the CUDA EULA). The studio would depend on them as optional extras, never vendored.
- **Read by the Publisher, 2026-10-20; outside check pending.** The reading below is from the CUDA EULA at
  docs.nvidia.com/cuda/eula. It is [unverified], awaiting the outside check, and nothing should depend on it until that
  check lands.
- **What it doesn't restrict** [unverified]: publishing test or benchmark results. This folder commits only package
  names and versions, results and our own script.
- **What it does restrict** [unverified]:
  - implying NVIDIA sponsors or endorses the work (§1.2(3));
  - redistributing SDK files beyond Attachment A's list (§1.1.2(4), §1.2(2), §2.6).
- **A future `[gpu]` extra** depends on NVIDIA's wheels from PyPI and never vendors them.
