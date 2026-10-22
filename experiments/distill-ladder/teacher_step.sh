#!/usr/bin/env bash
# The distillation exercise's teacher leg (PLAN.md, card plan leg 2): gemma4:31b answers training items in offrig's
# contract, in the settings it was scored at on ladder v1 (think on, structured on; offrig's own num_ctx and
# num_predict), in its own scratch project. Same guards as math-ladder/ladder_step.sh: rests first, a fresh watchdog
# heartbeat and an empty card, then the run, then an unload (keep_alive 0), and exit 3 if the run is incomplete.
# Rerunning the same line resumes on the same output directory, and appends to its log.
# STOP_AFTER=<n> (the stub only): stop offrig once its verdicts file has n lines, to prove the resume.
#   bash teacher_step.sh <gold.jsonl> <out-dir> <rest-seconds> [project]
set -uo pipefail
GOLD=${1:?gold}; OUT=${2:?out}; REST=${3:?rest}; PROJ=${4:-/e/AI/rnd-distill-teacher}
MODEL=gemma4:31b
OFFRIG=${OFFRIG:-"$HOME/.local/bin/offrig.exe"}; OLLAMA=http://127.0.0.1:11434
loaded() { curl -s "$OLLAMA/api/ps" | python -c "import json,sys; print(len(json.load(sys.stdin).get('models',[])))"; }
mkdir -p "$PROJ"
[ "$REST" -gt 0 ] && { echo "== rest ${REST}s from $(date +%T)"; sleep "$REST"; }
HB=${WATCHDOG_HEARTBEAT:-/e/AI/training/_watchdog_HEARTBEAT}
age=$(( $(date +%s) - $(stat -c %Y "$HB" 2>/dev/null || echo 0) )); [ "$age" -le 60 ] || { echo "REFUSED: watchdog heartbeat ${age}s old"; exit 5; }
[ "$(loaded)" = 0 ] || { echo "REFUSED: a model is on the card"; exit 4; }
if [ -f "$OUT/manifest.json" ]; then WHERE=(--resume "$OUT"); else WHERE=(--out "$OUT"); fi
echo "== $MODEL teacher on $GOLD ${WHERE[*]} start $(date +%T)"
"$OFFRIG" verify calibrate "$GOLD" --model "$MODEL" --think on --structured on --split tune --project "$PROJ" "${WHERE[@]}" >> "$OUT.log" 2>&1 &
PID=$!
if [ -n "${STOP_AFTER:-}" ]; then
  while kill -0 "$PID" 2>/dev/null; do
    n=0; [ -f "$OUT/verdicts.jsonl" ] && n=$(grep -c . "$OUT/verdicts.jsonl")
    if [ "$n" -ge "$STOP_AFTER" ]; then echo "== stub stop at $n verdicts"; kill "$PID"; break; fi
    sleep 5
  done
fi
wait "$PID"; RC=$?
tail -12 "$OUT.log"
curl -s "$OLLAMA/api/generate" -d "{\"model\":\"$MODEL\",\"keep_alive\":0}" >/dev/null; sleep 5
echo "== $MODEL end $(date +%T) rc=$RC; models loaded after unload: $(loaded)"
if "$OFFRIG" verify calibrate --report-only "$OUT" --project "$PROJ" 2>&1 | grep -qi incomplete; then echo "== INCOMPLETE"; exit 3; fi
echo "== COMPLETE: $(grep -c . "$OUT/verdicts.jsonl") verdicts"
