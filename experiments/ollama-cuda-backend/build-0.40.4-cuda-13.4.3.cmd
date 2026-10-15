@echo off
rem Ollama 0.40.4 CUDA 13.4 Update 2 (13.4.3, nvcc V13.4.92) ggml-cuda backend to the studio standard (Argon, 2026-10-15). Build only.
rem Launched by run-build.ps1 under start /AFFINITY 3FC /BELOWNORMAL (E-cores 2-9), plus -j 8.
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul || exit /b 10
set "NVCC=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.4\bin\nvcc.exe"
rem Refuse unless nvcc is exactly 13.4 Update 2 (version.json 13.4.3), nvcc V13.4.92, as verified 2026-10-15.
"%NVCC%" --version | findstr /c:"V13.4.92" >nul || (echo REFUSED: nvcc is not V13.4.92 & exit /b 12)
cd /d E:\AI\ollama-src-0404 || exit /b 11
cmake -S llama/server --preset llama_cuda_v13_windows -B E:/AI/ollama-cu1343-0404/build -G Ninja ^
  -DCMAKE_CUDA_ARCHITECTURES=120a-real ^
  -DGGML_CUDA_FA_ALL_QUANTS=ON -DGGML_CUDA_COMPRESSION_MODE=speed -DGGML_CUDA_GRAPHS=ON -DGGML_CUDA_NO_VMM=OFF ^
  -DCUDAToolkit_ROOT="C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.4" ^
  -DCMAKE_CUDA_COMPILER="C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.4/bin/nvcc.exe" ^
  -DCMAKE_INSTALL_PREFIX=E:/AI/ollama-cu1343-0404/stage || exit /b 1
cmake --build E:/AI/ollama-cu1343-0404/build --target ggml-cuda -j 8 || exit /b 2
"%NVCC%" --version
echo BUILD_OK
