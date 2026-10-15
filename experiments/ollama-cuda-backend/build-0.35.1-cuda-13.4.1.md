# Ollama 0.35.1 CUDA 13.4 backend (build only; nothing activated, no GPU used)

## Source
- ollama tag v0.35.1, commit b0c1ca4f7549d7acdfa52a7dcffc934bc63a43ce (E:/AI/ollama-src, shallow)
- 0.35.1 has no vendored ggml: ggml comes from llama.cpp, pinned in LLAMA_CPP_VERSION = b11232
  (fetched by FetchContent in llama/server/CMakeLists.txt, commit 6f767fe960c3b97cf37fac4626c86400561ca1e4),
  with Ollama's llama/compat patches applied. Same pin as the installed 0.35.1 -> same ggml ABI.
- Toolkit: CUDA 13.4 (nvcc from v13.4), MSVC 19.44.35229, Ninja (from VS Build Tools CMake dir), CMake in Program Files.

## Build (Release, from vcvars64 env; script kept in the session scratchpad)
    cmake -S llama/server --preset llama_cuda_v13_windows -G Ninja -DCMAKE_CUDA_ARCHITECTURES=120 ^
      -DCUDAToolkit_ROOT="C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.4" ^
      -DCMAKE_CUDA_COMPILER="C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.4/bin/nvcc.exe" ^
      -DCMAKE_INSTALL_PREFIX=E:/AI/ollama-cu134/stage
    cmake --build build/llama-server-cuda_v13 --target ggml-cuda
Preset flags retained: GGML_CUDA=ON, GGML_BACKEND_DL=ON, GGML_NATIVE=OFF, CMAKE_CUDA_FLAGS="-t 4".
Arch: the preset's list (75..120, all -virtual/PTX) was replaced by 120 only (ggml turned it into compute_120a;
real SASS for sm_120a). Other GPUs cannot use this DLL. Output: build/llama-server-cuda_v13/bin/ggml-cuda.dll.
cudart is statically linked (installed cuda_v13 also ships no cudart64_13.dll); dumpbin dependents:
ggml-base.dll (from lib/ollama parent), cublas64_13.dll, KERNEL32, MSVCP140, VCRUNTIME140(_1), api-ms-win-crt-*. All resolved.

## lib/ollama/cuda_v13 contents (sha256)
- concrt140.dll  02fc798ee7d3d78f2370d0747ff7cf5fc9f7aef1e77e2fe8310d83c347a642d4
- cublas64_13.dll  1119dbca0a808e0c8850bb4221e330daf0b5ddb348d62d37b6ac533854723df9
- cublasLt64_13.dll  0f5bc315fef706b5626248ebd74e8a48a9e82fa2f0cad38330f5f70984913107
- ggml-cuda.dll  6d3128e946bc9c951f689148d4deed6c663b73842c3c09a02916c9f03d6d1fa7
- msvcp140.dll  9caec14bcd5298be131a04b9546744556fbf650677e2e6b77f72a3e45718bd60
- msvcp140_1.dll  bbb4f2efe0be886467177ad169ccb32817f84530c683c093454db8a967baa0b2
- msvcp140_2.dll  62dd3115c56f26382d3b4c4333b93053cfb576877449f92721b4123c6f24cc78
- msvcp140_atomic_wait.dll  d1d7867728ca6ca37b4245e4063a4916936995976b4485ad7f90f8dc2dc4b578
- msvcp140_codecvt_ids.dll  9d05b296ea0ff6fd2308c9356cb237f2bfee0bf153177869562984ace50abaf2
- vccorlib140.dll  38e505861387b1d38ea76c74b7857599c76d01596b643d6db0e41aa00d75014e
- vcruntime140.dll  43b88113aed8fd9898579e74414bac5bbb94fcb86b2b4c328ea57b32c9a02571
- vcruntime140_1.dll  efa4fe8325e971a4cdfab22f0fbb30abca5368501ccea594a309ce44bff39c1f
- vcruntime140_threads.dll  6a5e0f8ca53ecf09ced1954dc5309d75187108a5b2cf3b3bf47e39fbafe10321

Versions: cudart (toolkit v13.4, static in ggml-cuda) 13.4 (ProductVersion 6,14,11,13040);
cublas64_13 / cublasLt64_13 from toolkit v13.4 = file version 6,14,11,1370 (installed 13.0 copy: 1300);
MSVC runtime DLLs copied unchanged from the installed cuda_v13 (14.44.35211.0).

## Activation mechanism (0.35.1 source)
There is NO OLLAMA_LIBRARY_PATH env var in 0.35.1 (the name only appears in log strings in discover/runner.go).
ml/path.go: LibOllamaPath = first existing of <exe dir>/lib/ollama, <exe dir>/../lib/ollama, then build/lib/ollama and
dist/<os>-<arch>/lib/ollama under exe dir / cwd. discover/runner.go globs LibOllamaPath/*/*ggml-* to find backend
dirs (cuda_v13 etc.); llm/llama_server.go sets GGML_BACKEND_PATH to that dir's ggml-*.dll and prepends the dir to PATH.
llama-server.exe, ggml-base.dll etc. are taken from LibOllamaPath itself (not from the cuda dir).
OLLAMA_LLM_LIBRARY=cuda_v13 forces the dir choice (skips cuda_v12/vulkan/rocm).

## Planned, NOT executed: test instance
1. Make a sandbox tree: E:\AI\ollama-cu134\run\ollama.exe (copy of the installed ollama.exe) and
   E:\AI\ollama-cu134\run\lib\ollama\ = copy (or hardlinks) of the installed lib\ollama top-level files
   (llama-server.exe, ggml*.dll, libllama*.dll, ggml-cpu-*.dll, libomp etc.) with cuda_v12, rocm, vulkan omitted
   and cuda_v13 replaced by this folder's lib\ollama\cuda_v13.
2. Run: set OLLAMA_HOST=127.0.0.1:11500 ; set OLLAMA_LLM_LIBRARY=cuda_v13 ; set OLLAMA_MODELS=<existing models dir, read only use> ;
   run\ollama.exe serve   (different port from the system server; do it only when the GPU is free).
3. Check server log shows library=CUDA and loads this ggml-cuda.dll; compare output of a fixed-seed prompt vs the system server.
## System activation / rollback (later, with Ollama stopped)
Activate: rename installed lib\ollama\cuda_v13 to cuda_v13.cu130.bak, copy this cuda_v13 folder in. (Updates of Ollama overwrite it.)
Rollback: delete the folder and rename the .bak back. Nothing under the installed Ollama was touched by this build.
