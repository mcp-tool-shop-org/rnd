#!/usr/bin/env bash
# CUDA 13.4 nightly on a RunPod CUDA 13.0 host: the same pins as experiments/kev-judge-finetune/env.
set -uo pipefail
cd /workspace/job
nvidia-smi | head -4
pip install -q uv 2>/dev/null
uv venv -q --python 3.12 .venv-cu134
uv pip install -q -p .venv-cu134/bin/python --pre "torch==2.16.0.dev20261008+cu134" --index-url https://download.pytorch.org/whl/nightly/cu134 || { echo "INSTALL-FAIL torch"; exit 2; }
uv pip install -q -p .venv-cu134/bin/python "transformers==5.19.0" "peft==0.21.2" "accelerate==1.15.0" || { echo "INSTALL-FAIL hf"; exit 2; }
uv pip freeze -p .venv-cu134/bin/python > freeze.txt
.venv-cu134/bin/python cu134_probe.py
echo PROBE-DONE
