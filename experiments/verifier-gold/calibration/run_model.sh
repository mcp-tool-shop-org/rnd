#!/usr/bin/env bash
# One candidate's run, both check types, with the settings its smoke settled. grounded runs on the given split
# (tune to select, heldout to confirm); reasoning always runs on all (README amendment: it has under 100
# unsupported per split).
# GPU: only inside the Publisher's chain grant. Resumable: rerun the same line and it resumes each directory.
#   bash run_model.sh <scratch-project-dir> <model> <think> <structured> [split]
set -uo pipefail
PROJ=${1:?scratch project dir}; MODEL=${2:?model}; THINK=${3:?think}; STRUCT=${4:?structured}; SPLIT=${5:-tune}
GOLD="$(cd "$(dirname "$0")/.." && pwd)"
OFFRIG=${OFFRIG:-"$HOME/.local/bin/offrig.exe"}
TAG=${MODEL//[:\/]/_}
for ct in grounded reasoning; do
  case $ct in grounded) files=("$GOLD/grounded.jsonl" "$GOLD/prs/grounded-prs.jsonl");; reasoning) files=("$GOLD/diffs/reasoning-diffs.jsonl");; esac
  S=$SPLIT; [ $ct = reasoning ] && S=all
  OUT="$PROJ/cal-$TAG-$ct-$S"
  if [ -f "$OUT/manifest.json" ]; then
    "$OFFRIG" verify calibrate --resume "$OUT" --project "$PROJ" 2>&1 | tail -25
  else
    "$OFFRIG" verify calibrate "${files[@]}" --model "$MODEL" --think "$THINK" --structured "$STRUCT" \
      --check-type "$ct" --split "$S" --project "$PROJ" --out "$OUT" 2>&1 | tail -25
  fi
done
curl -s http://127.0.0.1:11434/api/generate -d "{\"model\":\"$MODEL\",\"keep_alive\":0}" >/dev/null
