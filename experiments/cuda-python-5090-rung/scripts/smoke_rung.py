"""The 5090 smoke rung for six CUDA Python libraries (R&D, 2026-10-20; the Director's go).

Per library, in its own process: import, the device's compute capability (must be 12.0), one small kernel, and a
result checked against NumPy on the CPU. Prints one JSON line per library. Read-only apart from its output file.

Run: <rung env python> smoke_rung.py <library>   (or no argument: all six, one process each)
"""
import json, os, subprocess, sys, time, traceback

LIBS = ["cuda.core", "cupy", "numba-cuda", "cuda.compute", "nvmath", "cuda.tile"]
N = 1 << 20


def cc_of():
    from cuda.core import Device
    d = Device(0)
    return tuple(d.compute_capability), d.name


def t_cuda_core():
    import numpy as np
    from cuda.core import Device, LaunchConfig, Program, ProgramOptions, launch
    import cupy as cp  # device memory for the test; the kernel is compiled and launched by cuda.core alone
    dev = Device(0)
    dev.set_current()
    cc = dev.compute_capability
    src = r'extern "C" __global__ void add_one(float* x, size_t n) {' \
          r' size_t i = blockIdx.x * blockDim.x + threadIdx.x; if (i < n) x[i] += 1.0f; }'
    prog = Program(src, code_type="c++", options=ProgramOptions(arch=f"sm_{cc.major}{cc.minor}"))
    mod = prog.compile("cubin")
    ker = mod.get_kernel("add_one")
    s = dev.create_stream()
    a = cp.arange(N, dtype=cp.float32)
    launch(s, LaunchConfig(grid=(N + 255) // 256, block=256), ker, a.data.ptr, np.uint64(N))
    s.sync()
    return bool(np.allclose(cp.asnumpy(a), np.arange(N, dtype=np.float32) + 1)), f"cubin sm_{cc.major}{cc.minor}"


def t_cupy():
    import numpy as np, cupy as cp
    a = cp.arange(N, dtype=cp.float32)
    k = cp.RawKernel(r'extern "C" __global__ void sq(float* x, int n) {'
                     r' int i = blockIdx.x * blockDim.x + threadIdx.x; if (i < n) x[i] = x[i] * x[i]; }', "sq")
    k(((N + 255) // 256,), (256,), (a, np.int32(N)))
    cp.cuda.Stream.null.synchronize()
    ref = np.arange(N, dtype=np.float32) ** 2
    ok = bool(np.allclose(cp.asnumpy(a), ref)) and abs(float(a.sum()) - float(ref.sum())) / float(ref.sum()) < 1e-3
    return ok, f"cuda runtime {cp.cuda.runtime.runtimeGetVersion()}"


def t_numba():
    import numpy as np
    from numba import cuda

    @cuda.jit
    def axpy(out, x, y):
        i = cuda.grid(1)
        if i < out.size:
            out[i] = 2.0 * x[i] + y[i]
    x = np.arange(N, dtype=np.float32)
    y = np.ones(N, dtype=np.float32)
    out = cuda.device_array_like(x)
    axpy[(N + 255) // 256, 256](out, cuda.to_device(x), cuda.to_device(y))
    return bool(np.allclose(out.copy_to_host(), 2 * x + y)), "numba.cuda.jit"


def t_compute():
    import numpy as np, cupy as cp
    import cuda.compute as cc_
    d_in = cp.arange(N, dtype=cp.int64)
    d_out = cp.empty(1, dtype=cp.int64)
    h_init = np.array([0], dtype=np.int64)
    cc_.reduce_into(d_in=d_in, d_out=d_out, num_items=N, op=cc_.OpKind.PLUS, h_init=h_init)
    return int(d_out.get()[0]) == int(np.arange(N, dtype=np.int64).sum()), "reduce_into PLUS"


def t_nvmath():
    import numpy as np, cupy as cp
    import nvmath
    a = cp.random.default_rng(0).standard_normal((512, 512), dtype=cp.float32)
    b = cp.random.default_rng(1).standard_normal((512, 512), dtype=cp.float32)
    c = nvmath.linalg.advanced.matmul(a, b)
    ok = bool(np.allclose(cp.asnumpy(c), cp.asnumpy(a) @ cp.asnumpy(b), rtol=1e-3, atol=1e-2))
    return ok, "linalg.advanced.matmul 512x512 fp32"


def t_tile():
    import numpy as np, cupy as cp
    import cuda.tile as ct
    TILE = 256

    @ct.kernel
    def vadd(a, b, c):
        bid = ct.bid(0)
        x = ct.load(a, index=(bid,), shape=(TILE,))
        y = ct.load(b, index=(bid,), shape=(TILE,))
        ct.store(c, index=(bid,), tile=x + y)
    a = cp.arange(N, dtype=cp.float32)
    b = cp.ones(N, dtype=cp.float32)
    c = cp.empty_like(a)
    ct.launch(cp.cuda.get_current_stream(), (N // TILE, 1, 1), vadd, (a, b, c))
    cp.cuda.get_current_stream().synchronize()
    return bool(np.allclose(cp.asnumpy(c), np.arange(N, dtype=np.float32) + 1)), "cuTile vadd"


TESTS = {"cuda.core": t_cuda_core, "cupy": t_cupy, "numba-cuda": t_numba, "cuda.compute": t_compute,
         "nvmath": t_nvmath, "cuda.tile": t_tile}


def one(lib):
    row = {"lib": lib}
    t0 = time.time()
    try:
        cc, name = cc_of()
        row["device"], row["cc"] = name, f"{cc[0]}.{cc[1]}"
        ok, note = TESTS[lib]()
        row.update(ok=bool(ok) and cc == (12, 0), note=note)
    except Exception as exc:  # the rung records the failure; it never hides one
        row.update(ok=False, error=f"{type(exc).__name__}: {exc}"[:400],
                   where=traceback.format_exc().strip().splitlines()[-3:-1])
    row["seconds"] = round(time.time() - t0, 2)
    print(json.dumps(row))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        one(sys.argv[1])
    else:
        env = {**os.environ, "OMP_NUM_THREADS": "4", "NUMBA_NUM_THREADS": "4", "MKL_NUM_THREADS": "4"}
        for lib in LIBS:
            subprocess.run([sys.executable, __file__, lib], env=env, timeout=600)
