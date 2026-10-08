#!/bin/bash
# Fine-tune Kev-4B as a planted-error judge, in WSL on the RTX 5090.
#   bash train.sh smoke      # 10 optimizer steps, to measure memory and speed
#   bash train.sh full SEED  # the run
# PyTorch is capped at 0.82 of the card. WSL python is not on the VRAM watchdog's
# guard list, so the cap (and the session watching nvidia-smi) is the protection.
set -euo pipefail
MODE=${1:-smoke}
SEED=${2:-0}
DATA=/mnt/e/AI-Models/kev/judge-ft
OUT=/mnt/e/AI-Models/kev/judge-ft/runs/judge-4b-${MODE}-s${SEED}
cd ~/kev/kev
export HF_HOME=/mnt/e/AI-Models/hf-cache
EXTRA=""
[ "$MODE" = smoke ] && EXTRA="--max_steps 10"
.venv/bin/python - <<PY
import runpy, sys, torch
torch.cuda.set_per_process_memory_fraction(0.82, 0)
sys.argv = ["kev.train",
    "--data", "$DATA/train.jsonl",
    "--base", "Qwen/Qwen3.5-4B-Base", "--base_revision", "1001bb4d826a52d1f399e183466143f4da7b741b",
    "--init_from", "jaredpalmer/kev-4b@v1.0",
    "--epochs", "2", "--lr", "2e-5", "--batch", "1", "--accum", "8",
    "--dtype", "bf16", "--weights_dtype", "bf16", "--checkpointing", "1",
    "--perm_kl", "1.0",
    "--device", "cuda", "--seed", "$SEED", "--out", "$OUT"] + "$EXTRA".split()
runpy.run_module("kev.train", run_name="__main__")
PY
echo "TRAIN-DONE $OUT"
