ARGON REPLY | torch builds and GGUF bytes | to the Publisher | 2026-10-18
(Filed verbatim from Mike's paste. The bundle was torch-gguf-part1.txt, SHA256 1a7521369d1c78dade9a9357efc0a4c2186ef37d3254201dd774a652f54aaed8, 157 lines.)

Verified header: `torch-gguf-part1.txt` (`SHA256: 1a7521369d1c78dade9a9357efc0a4c2186ef37d3254201dd774a652f54aaed8`, `LINES: 157`) (`checked`, `torch-gguf-part1.txt:1-2`).

1. The Cause — `worth knowing`
* Why `torch` differed across hosts (`checked`, `torch-gguf-part1.txt:9-23`, `scripts/colab/pin_window.py:700-713`): Models with `env` (Muse, Gemma 4) create a fresh `virtualenv` where `requirements-convert_hf_to_gguf.txt` (`--extra-index-url https://download.pytorch.org/whl/cpu` + `torch==2.11.0`, `torch-gguf-part1.txt:145-148`) installs `torch==2.11.0+cpu` on both A100 and CPU. Models without `env` run in `/usr/bin/python3` (`pin_window.py:701-703`), where preinstalled `torch==2.11.0+cu130` on the A100 image already satisfies `torch==2.11.0`, while the CPU image has `2.11.0+cpu`.
* Which conversion step differs (`checked` / `unsure`):
  * Not the BF16-to-FP32 cast (`checked`): `convert_hf_to_gguf.py` loads safetensors on CPU (`safe_open(..., framework="pt", device="cpu")`) and upcasts `bfloat16` via `data_torch.to(torch.float32)` (`checked`, `convert_hf_to_gguf.py`), which is an exact 16-bit left shift with zero rounding.
  * Where `torch` or CPU ISA can flip a bit (`checked` / `unsure`): First, in `modify_tensors`, hybrid/SSM architectures (such as `Qwen3NextModel` / `Mamba2Model`) run transcendental PyTorch ops like `data_torch = -torch.exp(data_torch)` on `.A_log` tensors (`checked`, `oxillama_arch` `ssm.rs` and `convert_hf_to_gguf.py`). Second, after `data_torch.numpy()`, `gguf.quants.quantize` computes `Q8_0` block scales (`amax / 127.0`) and `np.round(x * id)` in float32 (`checked`, `convert_hf_to_gguf.py`). Whether `2.11.0+cu130` vs `2.11.0+cpu` links different Sleef/OpenMP/MKL flags (`unsure`) or whether the A100 VM and CPU `--high-mem` VM have different x86 SIMD dispatch (`AVX512` vs `AVX2`, `checked`, PyTorch backends.cpu docs) that only hits a boundary tie on Qwen3.8's weights (`unsure`), either will change the GGUF hash while keeping file size (`29047084448` bytes) identical (`checked`, `torch-gguf-part1.txt:9-13`).

2. The Confirming Test — `worth knowing`
* Cheaper localization before a 30 GB run (`checked`):
  1. Single-shard / single-layer test (<30 s on CPU): Pass only the first safetensors shard (or a 20-line script calling `gguf.GGUFReader` on both existing GGUFs if kept, or running `convert_hf_to_gguf.py` on layer 0's tensors) under `2.11.0+cpu` vs `2.11.0+cu130` (`checked`, `convert_hf_to_gguf.py`).
  2. Record `lscpu` / `torch.backends.cpu.get_cpu_capability()` (`checked`, PyTorch backends.cpu docs): If `2.11.0+cu130` in a venv on a CPU VM reproduces `2ab268e0…`, `torch` build alone is proven; if it still gives `6beabf07…`, the difference is the CPU VM's microarchitecture (`AVX2` vs `AVX512`) rather than `torch` (`unsure`).

3. What to Pin From Now On — `change before the next study`
* New pins (`checked`): Always run `converter_python` (`pin_window.py:696-718`) in an isolated `virtualenv` (never `/usr/bin/python3`), pinning the exact `torch==2.11.0+cpu` wheel URL/hash so GPU and CPU images never diverge (`checked`, `torch-gguf-part1.txt:11-23`).
* The five existing system-python pins (`checked`): Keep R&D's current plan—prebuild Qwen3.8 and Granite on an A100 where their pins were made (`checked`, `torch-gguf-part1.txt:25-26`)—until the confirming test in Q2 proves whether `torch==2.11.0+cu130` in a CPU VM reproduces `2ab268e0…`.

4. Risks We're Missing — `change before the next prebuild`
* CPU ISA dispatch (`AVX512` vs `AVX2`) (`checked`, PyTorch backends.cpu docs): Even on the same Colab image tag (`release-colab-external-images_20261014-060047_RC00`, `torch-gguf-part1.txt:7`), Colab's CPU pool spans different Xeon/EPYC generations (`unsure`), while A100 VMs always sit on uniform `a2-highgpu-1g` Cascade Lake/ Milan hosts (`unsure`). That makes A100 prebuilds more hardware-uniform than CPU VMs, not fragile. Pinning `NPY_DISABLE_CPU_FEATURES="AVX512F,AVX512_SKX"` and `ATEN_CPU_CAPABILITY=avx2` (plus `OMP_NUM_THREADS=1`) in future studies eliminates host-CPU drift (`checked`, PyTorch Environment Variables docs).
