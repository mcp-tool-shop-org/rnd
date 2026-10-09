#!/usr/bin/env bash
# One step of the overnight calibration chain: rest, run one model, check it finished, unload.
# GPU: only inside the Publisher's chain grant. Standing rule (Director, 2026-10-08): the card rests 15 min
# with nothing loaded between runs. So every step but the first rests before it loads anything.
#   bash chain_step.sh <scratch-project-dir> <model> <think> <structured> <rest-seconds> [split]
# Exit 0: the model's runs are complete. Exit 3: incomplete (paused, or the server went away), so stop the
# chain. Rerunning the same line resumes it; completed claims are never asked again.
set -uo pipefail
PROJ=${1:?scratch project dir}; MODEL=${2:?model}; THINK=${3:?think}; STRUCT=${4:?structured}
REST=${5:?rest seconds}; SPLIT=${6:-tune}
HERE="$(cd "$(dirname "$0")" && pwd)"
OFFRIG=${OFFRIG:-"$HOME/.local/bin/offrig.exe"}
TAG=${MODEL//[:\/]/_}
OLLAMA=http://127.0.0.1:11434

loaded() { curl -s "$OLLAMA/api/ps" | python -c "import json,sys; print(len(json.load(sys.stdin).get('models',[])))"; }

if [ "$REST" -gt 0 ]; then
  echo "== rest ${REST}s from $(date +%T); models loaded at start: $(loaded)"
  sleep "$REST"
fi
# The VRAM watchdog must be alive: read the heartbeat's modified time only, never open the file (the
# Publisher, 2026-10-09: opening it collided with the watchdog's own writes).
HB=${WATCHDOG_HEARTBEAT:-/e/AI/training/_watchdog_HEARTBEAT}
age=$(( $(date +%s) - $(stat -c %Y "$HB" 2>/dev/null || echo 0) ))
[ "$age" -le 60 ] || { echo "REFUSED: watchdog heartbeat is ${age}s old"; exit 5; }
n=$(loaded)
if [ "$n" != 0 ]; then
  echo "== REFUSED: $n model(s) on the card after the rest; not loading $MODEL"; exit 4
fi

echo "== $MODEL think=$THINK structured=$STRUCT start $(date +%T)"
bash "$HERE/run_model.sh" "$PROJ" "$MODEL" "$THINK" "$STRUCT" "$SPLIT"
curl -s "$OLLAMA/api/generate" -d "{\"model\":\"$MODEL\",\"keep_alive\":0}" >/dev/null
sleep 5
echo "== $MODEL end $(date +%T); models loaded after unload: $(loaded)"

status=0
for ct in grounded reasoning; do
  S=$SPLIT
  OUT="$PROJ/cal-$TAG-$ct-$S"
  rep=$("$OFFRIG" verify calibrate --report-only "$OUT" --project "$PROJ" 2>&1)
  if [ ! -f "$OUT/manifest.json" ] || echo "$rep" | grep -qi "incomplete"; then
    echo "== $ct: INCOMPLETE"; status=3
  else
    echo "== $ct: complete"
  fi
done
exit $status
