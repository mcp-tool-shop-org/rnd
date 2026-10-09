#!/usr/bin/env bash
# One model's math-ladder run, in its own scratch project so its verdicts never share a store with the
# calibration gold (offrig's check types are fixed, so the separate store is the separation; origin
# math-ladder-v1 and ml- ids mark every verdict too). GPU: only inside the Publisher's ladder grant.
# Rests first (the Director's 15-minute rule), checks the watchdog and an empty card, runs, unloads, and exits 3
# if the run is incomplete so the sequence stops. Rerunning the same line resumes.
#   bash ladder_step.sh <model> <think> <structured> <rest-seconds> [project]
set -uo pipefail
MODEL=${1:?model}; THINK=${2:?think}; STRUCT=${3:?structured}; REST=${4:?rest}; PROJ=${5:-/e/AI/rnd-ladder}
HERE="$(cd "$(dirname "$0")" && pwd)"; OFFRIG=${OFFRIG:-"$HOME/.local/bin/offrig.exe"}; OLLAMA=http://127.0.0.1:11434
TAG=${MODEL//[:\/]/_}; OUT="$PROJ/ladder-$TAG"
loaded() { curl -s "$OLLAMA/api/ps" | python -c "import json,sys; print(len(json.load(sys.stdin).get('models',[])))"; }
mkdir -p "$PROJ"
[ "$REST" -gt 0 ] && { echo "== rest ${REST}s from $(date +%T)"; sleep "$REST"; }
HB=${WATCHDOG_HEARTBEAT:-/e/AI/training/_watchdog_HEARTBEAT}
age=$(( $(date +%s) - $(stat -c %Y "$HB" 2>/dev/null || echo 0) )); [ "$age" -le 60 ] || { echo "REFUSED: watchdog heartbeat ${age}s old"; exit 5; }
[ "$(loaded)" = 0 ] || { echo "REFUSED: a model is on the card"; exit 4; }
echo "== $MODEL think=$THINK structured=$STRUCT ladder start $(date +%T)"
if [ -f "$OUT/manifest.json" ]; then
  "$OFFRIG" verify calibrate --resume "$OUT" --project "$PROJ" 2>&1 | tail -12
else
  "$OFFRIG" verify calibrate "$HERE/ladder.jsonl" --model "$MODEL" --think "$THINK" --structured "$STRUCT" \
    --split tune --project "$PROJ" --out "$OUT" 2>&1 | tail -12
fi
curl -s "$OLLAMA/api/generate" -d "{\"model\":\"$MODEL\",\"keep_alive\":0}" >/dev/null; sleep 5
echo "== $MODEL end $(date +%T); models loaded after unload: $(loaded)"
if "$OFFRIG" verify calibrate --report-only "$OUT" --project "$PROJ" 2>&1 | grep -qi incomplete; then echo "== INCOMPLETE"; exit 3; fi
python "$HERE/report.py" "$OUT" | tail -32
