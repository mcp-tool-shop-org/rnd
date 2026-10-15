# Ollama 0.40.4 CUDA 13.4 backend (build only; nothing activated, no GPU used)

Built 2026-10-15. The 0.35.1 build (E:\AI\ollama-cu134) and the installed Ollama were not touched.

**Why:** the 0.40.4 install of 2026-10-14 replaced the studio's CUDA 13.4 `ggml-cuda.dll` with the stock build. The 0.35.1 build can't be copied back, because 0.40.4 pins a different llama.cpp.

## Source

- Ollama tag v0.40.4, commit `45e6011815c74acde6a346512856b69dd79dd22b` (E:/AI/ollama-src-0404, shallow).
- 0.40.4 has no vendored ggml either. ggml comes from llama.cpp, pinned in `LLAMA_CPP_VERSION = b11521` and fetched by FetchContent in `llama/server/CMakeLists.txt`, with Ollama's patches. 0.35.1 pinned b11232. Same pin as the installed 0.40.4, so the same ggml ABI (inferred; the sandbox test checks it).
- Toolkit: CUDA 13.4 (nvcc from v13.4), MSVC from VS 2022 Build Tools (vcvars64), Ninja and CMake.

## Build

`build.cmd`, launched by `run-build.ps1`:

    cmake -S llama/server --preset llama_cuda_v13_windows -G Ninja -DCMAKE_CUDA_ARCHITECTURES=120 ^
      -DCUDAToolkit_ROOT="C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.4" ^
      -DCMAKE_CUDA_COMPILER="C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.4/bin/nvcc.exe" ^
      -DCMAKE_INSTALL_PREFIX=E:/AI/ollama-cu134-0404/stage
    cmake --build build/llama-server-cuda_v13 --target ggml-cuda -j 8

- **Preset flags kept:** GGML_CUDA=ON, `CMAKE_CUDA_FLAGS="-t 4"`. The preset's architecture list (75 to 120, all virtual) was replaced by 120 only, so the DLL runs on the RTX 5090 (sm_120) and nothing else.
- **Output:** `build/llama-server-cuda_v13/bin/ggml-cuda.dll`. 156 ninja steps, ending in BUILD_OK.

**The cap, for a shared machine:**
- launched with `start /AFFINITY 3FC /BELOWNORMAL` (E-cores 2–9), so cmake, ninja, nvcc and cl all inherited it, plus `-j 8`;
- typeperf every 5 s;
- a stop if total CPU held above 50% for 30 s.

**Measured, 16:59:47–17:05:31Z:**
- wall time 343.8 s;
- total machine CPU: peak 74.4% (one 5 s sample), average 41.7%. 17 of 57 samples were above 50%, but never 6 in a row, so the stop didn't fire;
- a per-core reading mid-build showed cores 2–9 at about 97% and all other cores at about 22%, which wasn't the build;
- the watched build processes carried affinity `0x3FC`.

Two caveats on those figures:
- One watched process name kept reading affinity `0x0`. It's a process a non-elevated shell can't open, an elevated or system process, which per-process reads show as `0x0` (explained after the build).
- The build-process CPU figure (peak 22%, average 7%) undercounts, because compiler processes start and finish inside a 5 s sample. The per-core reading is the reliable one.

## lib/ollama/cuda_v13 contents (sha256)

- concrt140.dll  ff1badd9826c1f8f96d44217fe4f5a88edfb26d5f412ddf50c2f78369b93bf1d
- cublas64_13.dll  1119dbca0a808e0c8850bb4221e330daf0b5ddb348d62d37b6ac533854723df9
- cublasLt64_13.dll  0f5bc315fef706b5626248ebd74e8a48a9e82fa2f0cad38330f5f70984913107
- ggml-cuda.dll  ab9bef88f8bf016b95e2d39a57ae2a1e140305b7d6f1e365a49e78ec37b4cb2c
- msvcp140.dll  c47a8526529b331788c99a42fd83dcf2c5b2d50f3b994b067a046ee5ac7ec419
- msvcp140_1.dll  7ae691e4a965aa0ef2dd7341c0c002b0a4de7abdf2b5bbebd46e43dd4a2b3472
- msvcp140_2.dll  57eca59ccee845f0aeb7e80daa7fe1a07ca51145102b98694cb9fd7d28ff79d7
- msvcp140_atomic_wait.dll  c78675bc87789972b0de2e899c933e69cbe97727704e0beedda7038dd4f82546
- msvcp140_codecvt_ids.dll  9a500bef627ec7952a5da11de52b72eb6855b9938a5c2300981bd1136762f89d
- vccorlib140.dll  8e21617692d8fdf98639c2148d3ab944410f692e7c12118c4fe569e7c8ec0b4f
- vcruntime140.dll  3fc9606f9118e1db2c1e483b6a767428cba32c8244bc985b0b93c757c7e1e839
- vcruntime140_1.dll  29bb0b6aa40d0659265f3814606c06e1da38caf9054f21db4f95f75444091ab2
- vcruntime140_threads.dll  3c991ea1004ce39d74778aa190f4edc6dabbf2a82297f74315e2f8ff06c9a1c3

**Where each came from:**
- `ggml-cuda.dll` is this build.
- `cublas64_13` and `cublasLt64_13` are from toolkit v13.4 (`bin/x64`), identical to the 0.35.1 build's.
- The MSVC runtime DLLs are copied unchanged from the installed 0.40.4 `cuda_v13`. They differ from the 0.35.1 build's because 0.40.4 ships a newer runtime.

## Dependencies (dumpbin /dependents ggml-cuda.dll)

ggml-base.dll, cublas64_13.dll, KERNEL32.dll, MSVCP140.dll, VCRUNTIME140_1.dll, VCRUNTIME140.dll, and api-ms-win-crt-*. All resolve:
- `ggml-base.dll` from the installed `lib\ollama` parent;
- cuBLAS and the MSVC runtime from this folder;
- the rest from Windows.

Machine x64. cudart is statically linked, as in 0.35.1.

## Next (each a separate go)

1. **The sandbox test on 11500,** under a GPU grant. It uses the same method as the 0.35.1 BUILD.md: a copy of the installed `ollama.exe` and `lib\ollama` top-level files, with this `cuda_v13` in place of the installed one, and `OLLAMA_LLM_LIBRARY=cuda_v13`. Check that the log shows this DLL loaded and the library is CUDA, then compare a fixed-seed prompt against stock.
2. **Activation,** with Ollama stopped:
   - rename the installed `lib\ollama\cuda_v13` to `cuda_v13.stock-0.40.4.bak` and copy this folder in;
   - update `start-ollama-5090.cmd`'s expected hash to `ab9bef88f8bf016b`.

   Rollback: delete the folder and rename the .bak back.
