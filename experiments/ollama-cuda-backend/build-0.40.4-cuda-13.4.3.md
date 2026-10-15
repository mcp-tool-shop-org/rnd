# Ollama 0.40.4 CUDA 13.4 Update 2 backend to the studio standard: BUILT (not activated)

**Status:** built on 2026-10-15 (BUILD_OK). Nothing is activated, and the installed Ollama and the older builds are untouched. This replaces the 13.4.1 build in E:\AI\ollama-cu134-0404 as the candidate for activation (Argon, 2026-10-15). That build stays as the record.

## What differs from the 13.4.1 build

| | 13.4.1 build (E:\AI\ollama-cu134-0404) | This build |
|---|---|---|
| Toolkit | CUDA 13.4.1 (GA), nvcc V13.4.59 | CUDA 13.4 Update 2 (`version.json` 13.4.3), nvcc V13.4.92. `build.cmd` refuses unless nvcc reports exactly V13.4.92 |
| Architectures | `120`, which ggml turns into `120a` | `120a-real`, explicit: sm_120a SASS, no PTX |
| FlashAttention quants | `GGML_CUDA_FA_ALL_QUANTS` OFF (default) | ON |
| Fatbin compression | `GGML_CUDA_COMPRESSION_MODE` size (default) | speed |
| CUDA graphs | the default | `GGML_CUDA_GRAPHS=ON` |
| VMM | on (`GGML_CUDA_NO_VMM` OFF, default) | on, explicit |
| cuBLAS / cuBLASLt | from 13.4.1 (file version 6,14,11,1370) | from 13.4 Update 2 `bin\x64` (file version 6,14,11,1380) |

The 13.4 cuBLAS release notes list a fix for an NVFP4 heuristic on compute capability 12.x (CUB-10222), and Update 2 includes it. That's per the Publisher's reading of the release notes, not checked here.

Every CMake option above exists in the pinned llama.cpp (b11521): `ggml/CMakeLists.txt` lines 202–214, and `ggml/src/ggml-cuda/CMakeLists.txt`, checked on 2026-10-15.

## The toolkit, as installed (verified 2026-10-15)

- **nvcc:** `Cuda compilation tools, release 13.4, V13.4.92`, `Build cuda_13.4.r13.4/compiler.38855100_0`. `version.json` reads 13.4.3. Installed with NVIDIA's signed installer: silent, elevated, exit 0.
- **cudart64_13.dll:** 6,14,11,13040, statically linked into ggml-cuda as before.
- **The cuBLAS DLLs that get copied into `cuda_v13`,** from `bin\x64`:
  - `cublas64_13.dll`, version 6,14,11,1380, sha256 `60bbba8868290311e9c1657b2193ddec667744eb555ff843f87acb7c039f9efa`
  - `cublasLt64_13.dll`, version 6,14,11,1380, sha256 `cad63434448e7141629e240ea093ad596a7ef6a0f67b468ba9bc1df6e1eeee33`
- **Driver:** 617.42, unchanged by the install.

## Source and build

- **Source:** Ollama v0.40.4 at `45e6011815c74acde6a346512856b69dd79dd22b` (E:/AI/ollama-src-0404), llama.cpp `b11521`. It's the same source as the 13.4.1 build, built in this folder's own `build\`, so the 13.4.1 build tree isn't touched.
- **`build.cmd`:** preset `llama_cuda_v13_windows`, `-B E:/AI/ollama-cu1343-0404/build`, the options above, target `ggml-cuda`, `-j 8`. It refuses unless nvcc is V13.4.92.
- **`run-build.ps1`:** `start /AFFINITY 3FC /BELOWNORMAL` (E-cores 2–9) and typeperf every 5 s. It stops if total CPU holds above 50% for 30 s, and records the wall time with peak and average CPU.

## Result (measured 2026-10-15, 17:53:40–17:59:54Z)

- **BUILD_OK** in **374.0 s**, 201 ninja steps (189 CUDA objects). The 13.4.1 build took 343.8 s and 156 steps.
- **nvcc as used:** V13.4.92. Every CUDA object was compiled with `--generate-code=arch=compute_120a,code=[sm_120a]`, which is sm_120a SASS only, with no `compute_` PTX in the binary (read from `build.ninja`).
- **`ggml-cuda.dll`:** 217,096,704 bytes, sha256 `0ebc0e61c7288e6a7367f21c1fbd9a8501e423927e55902c0f0476cdd8608c6a`. The 13.4.1 build's was 56 MB; FA_ALL_QUANTS and speed compression account for the difference.
- **CPU** (total machine, 5 s samples): peak 54.1% in one sample, average 37.5%. 1 of 62 samples was above 50%, never 6 in a row, so the stop didn't fire. The build processes carried affinity `0x3FC`. One watched process name read `0x0`, as in the 13.4.1 build: an elevated or system process a non-elevated shell can't open, as was worked out after the build. The per-process build CPU figure (peak 19.3%) undercounts the short-lived compiler processes.
- **dumpbin /dependents ggml-cuda.dll:** ggml-base.dll (from the installed `lib\ollama` parent), cublas64_13.dll (this folder), KERNEL32, MSVCP140, VCRUNTIME140, VCRUNTIME140_1 (this folder) and api-ms-win-crt-*. All resolve. Machine x64.

## lib/ollama/cuda_v13 contents (sha256, also in `sha256.txt`)

- concrt140.dll  ff1badd9826c1f8f96d44217fe4f5a88edfb26d5f412ddf50c2f78369b93bf1d
- cublas64_13.dll  60bbba8868290311e9c1657b2193ddec667744eb555ff843f87acb7c039f9efa  (6,14,11,1380)
- cublasLt64_13.dll  cad63434448e7141629e240ea093ad596a7ef6a0f67b468ba9bc1df6e1eeee33  (6,14,11,1380)
- ggml-cuda.dll  0ebc0e61c7288e6a7367f21c1fbd9a8501e423927e55902c0f0476cdd8608c6a
- msvcp140.dll  c47a8526529b331788c99a42fd83dcf2c5b2d50f3b994b067a046ee5ac7ec419
- msvcp140_1.dll  7ae691e4a965aa0ef2dd7341c0c002b0a4de7abdf2b5bbebd46e43dd4a2b3472
- msvcp140_2.dll  57eca59ccee845f0aeb7e80daa7fe1a07ca51145102b98694cb9fd7d28ff79d7
- msvcp140_atomic_wait.dll  c78675bc87789972b0de2e899c933e69cbe97727704e0beedda7038dd4f82546
- msvcp140_codecvt_ids.dll  9a500bef627ec7952a5da11de52b72eb6855b9938a5c2300981bd1136762f89d
- vccorlib140.dll  8e21617692d8fdf98639c2148d3ab944410f692e7c12118c4fe569e7c8ec0b4f
- vcruntime140.dll  3fc9606f9118e1db2c1e483b6a767428cba32c8244bc985b0b93c757c7e1e839
- vcruntime140_1.dll  29bb0b6aa40d0659265f3814606c06e1da38caf9054f21db4f95f75444091ab2
- vcruntime140_threads.dll  3c991ea1004ce39d74778aa190f4edc6dabbf2a82297f74315e2f8ff06c9a1c3

The MSVC runtime is copied from the installed 0.40.4 `cuda_v13`, identical to the 13.4.1 build's.

## After the build (each its own step)

1. **Done:** assemble `lib\ollama\cuda_v13`: this `ggml-cuda.dll`, the two cuBLAS DLLs above, and the MSVC runtime from the installed 0.40.4. Hash every file into `sha256.txt` (one `hash  name` per line). The sandbox test reads its expected DLL hash from there.
2. **Done:** dumpbin /dependents, with every dependency resolved, plus the `--generate-code` flags nvcc actually used (from the ninja log), expected to be `code=sm_120a` with no `compute_` PTX.
3. **The sandbox tree** at `E:\AI\ollama-cu1343-0404\run`, hash-checked as before. Its runner is `E:\AI\ollama-cu1343-0404\run\lib\ollama\llama-server.exe`, which must be on the watchdog guard list for the grant window.
4. **The sandbox test** (`E:\AI\ollama-cu134-0404\sandbox_test.py` v3), only with Argon's green light and a grant.
