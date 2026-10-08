#!/bin/bash
# Score Kev judge fine-tune seeds on one extra pair set with aspire-si's judge_kev.py.
#   bash score_set.sh <set-name> <pairs.json (WSL path)> [seed ...]
# e.g. bash score_set.sh second /mnt/e/AI/aspire-si-runs/2026-10-08-auditor/second/second_set.json frozen 0 1 2
# A seed of "frozen" serves the untrained reference, jaredpalmer/kev-4b@v1.0.
# Results go to results/judge-4b-full-s<N>-<set-name>.json next to this script, wherever the
# experiment folder lives. PyTorch capped at 0.82 of the card; one server at a time.
set -euo pipefail
SET=${1:?set name}; PAIRS=${2:?pairs json}; shift 2
SEEDS=${@:-0 1 2}
HERE="$(cd "$(dirname "$0")" && pwd)"
RES="$HERE/results"
JUDGE=/mnt/e/AI/aspire-si/examples/sft-experiment/judge_kev.py
PORT=8011
cd ~/kev/kev
export HF_HOME=/mnt/e/AI-Models/hf-cache HF_HUB_OFFLINE=1
for S in $SEEDS; do
  if [ "$S" = frozen ]; then RUN=kev-4b-frozen; SPEC="jaredpalmer/kev-4b@v1.0"
  else RUN=judge-4b-full-s$S; SPEC="/mnt/e/AI-Models/kev/judge-ft/runs/$RUN"; fi
  ${KEV_VENV:-.venv}/bin/python - > "$RES/$RUN-$SET-serve.log" 2>&1 <<PY &
import runpy, sys, torch
torch.cuda.set_per_process_memory_fraction(0.82, 0)
sys.argv = ["kev.serve", "--run", "$SPEC", "--port", "$PORT"]
runpy.run_module("kev.serve", run_name="__main__")
PY
  SV=$!
  for i in $(seq 1 120); do curl -s -m 2 http://127.0.0.1:$PORT/v1/models >/dev/null && break; sleep 3; done
  python3 "$JUDGE" --judge-set "$PAIRS" --out "$RES/$RUN-$SET.json" --name "$RUN-$SET" \
    --url http://127.0.0.1:$PORT/v1/systemone | tail -12
  kill $SV; sleep 3; pkill -f "/kev/kev/${KEV_VENV:-.venv}/bin/python" || true
  echo "SCORE-DONE $RUN $SET"
done
