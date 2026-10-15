@echo off
rem Ollama 0.40.4 CUDA 13.4 ggml-cuda backend, build only. Launched by run-build.ps1 under
rem start /AFFINITY 3FC /BELOWNORMAL (E-cores 2-9), so every child (cmake, ninja, nvcc, cl) inherits both.
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul || exit /b 10
cd /d E:\AI\ollama-src-0404 || exit /b 11
cmake -S llama/server --preset llama_cuda_v13_windows -G Ninja -DCMAKE_CUDA_ARCHITECTURES=120 ^
  -DCUDAToolkit_ROOT="C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.4" ^
  -DCMAKE_CUDA_COMPILER="C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.4/bin/nvcc.exe" ^
  -DCMAKE_INSTALL_PREFIX=E:/AI/ollama-cu134-0404/stage || exit /b 1
cmake --build build/llama-server-cuda_v13 --target ggml-cuda -j 8 || exit /b 2
echo BUILD_OK
