#!/bin/bash
# Serve a fine-tuned Kev run from WSL (capped at 0.82 of the card) and score it with
# aspire-si's own judge_kev.py on the 149 confirmation pairs and the 127 judge pairs.
#   bash score.sh judge-4b-full-s0
set -euo pipefail
RUN=${1:?run name under /mnt/e/AI-Models/kev/judge-ft/runs}
RUNDIR=/mnt/e/AI-Models/kev/judge-ft/runs/$RUN
RES="/mnt/e/AI/Research and Development/experiments/kev-judge-finetune/results"
JUDGE=/mnt/e/AI/aspire-si/examples/sft-experiment/judge_kev.py
PORT=8011
mkdir -p "$RES"
cd ~/kev/kev
export HF_HOME=/mnt/e/AI-Models/hf-cache HF_HUB_OFFLINE=1
.venv/bin/python - > "$RES/$RUN-serve.log" 2>&1 <<PY &
import runpy, sys, torch
torch.cuda.set_per_process_memory_fraction(0.82, 0)
sys.argv = ["kev.serve", "--run", "$RUNDIR", "--port", "$PORT"]
runpy.run_module("kev.serve", run_name="__main__")
PY
SV=$!
for i in $(seq 1 120); do curl -s -m 2 http://127.0.0.1:$PORT/v1/models >/dev/null && break; sleep 3; done
curl -s -m 2 http://127.0.0.1:$PORT/v1/models | head -c 300; echo
for SET in confirm judge; do
  if [ $SET = confirm ]; then PAIRS=/mnt/e/AI/aspire-si-runs/2026-10-08-kev-confirm/fresh/confirm_set.json
  else PAIRS=/mnt/e/AI/aspire-si-runs/2026-10-07-sft/a3/data/judge_set.json; fi
  python3 "$JUDGE" --judge-set "$PAIRS" --out "$RES/$RUN-$SET.json" --name "$RUN-$SET" \
    --url http://127.0.0.1:$PORT/v1/systemone | tail -30
done
kill $SV; sleep 3; pkill -f "/kev/kev/.venv/bin/python" || true
echo "SCORE-DONE $RUN"
