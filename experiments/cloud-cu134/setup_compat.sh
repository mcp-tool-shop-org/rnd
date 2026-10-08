#!/usr/bin/env bash
# CUDA 13.4 forward compatibility on a RunPod CUDA 13.0 host.
set -uo pipefail
cd /workspace/job
nvidia-smi | sed -n 3p
echo "== host driver"; python3 compat_probe.py
echo "== install cuda-compat-13-4"
wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb && dpkg -i cuda-keyring_1.1-1_all.deb >/dev/null
apt-get update -qq >/dev/null 2>&1
apt-cache madison cuda-compat-13-4 | head -3
apt-get install -y -qq cuda-compat-13-4 >/dev/null 2>&1 || { echo "COMPAT-INSTALL-FAIL"; apt-cache search cuda-compat | sort | tail -5; exit 2; }
ls /usr/local/cuda-13.4/compat/
export LD_LIBRARY_PATH=/usr/local/cuda-13.4/compat
echo "== with compat"; python3 compat_probe.py
echo "== torch cu134 probe under compat"
pip install -q uv 2>/dev/null
uv venv -q --python 3.12 .venv-cu134
uv pip install -q -p .venv-cu134/bin/python --pre "torch==2.16.0.dev20261008+cu134" --index-url https://download.pytorch.org/whl/nightly/cu134
uv pip install -q -p .venv-cu134/bin/python "transformers==5.19.0" "peft==0.21.2" "accelerate==1.15.0"
.venv-cu134/bin/python -c "import torch; print('torch sees driver', torch._C._cuda_getDriverVersion() if hasattr(torch._C,'_cuda_getDriverVersion') else 'n/a')"
.venv-cu134/bin/python cu134_probe.py
echo COMPAT-DONE
