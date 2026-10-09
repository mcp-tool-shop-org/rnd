#!/usr/bin/env bash
# One candidate's run, both check types on the given split (tune to select, heldout to confirm), with the
# settings its smoke settled.
# GPU: only inside the Publisher's chain grant. Resumable: rerun the same line and it resumes each directory.
#   bash run_model.sh <scratch-project-dir> <model> <think> <structured> [split]
# CAL_TYPES (default "grounded reasoning") limits the check types, e.g. CAL_TYPES=reasoning for a
# reasoning-only held-out run under the split-case rule.
# Extra calibrate flags (e.g. the gemma rerun's "--num-predict 12288 --keep-thinking") come from CAL_EXTRA and go to
# both a new run and a resume, since offrig's resume identity includes them.
set -uo pipefail
PROJ=${1:?scratch project dir}; MODEL=${2:?model}; THINK=${3:?think}; STRUCT=${4:?structured}; SPLIT=${5:-tune}
GOLD="$(cd "$(dirname "$0")/.." && pwd)"
OFFRIG=${OFFRIG:-"$HOME/.local/bin/offrig.exe"}
TAG=${MODEL//[:\/]/_}
read -r -a EXTRA <<< "${CAL_EXTRA:-}"
for ct in ${CAL_TYPES:-grounded reasoning}; do
  case $ct in grounded) files=("$GOLD/grounded.jsonl" "$GOLD/prs/grounded-prs.jsonl");; reasoning) files=("$GOLD/diffs/reasoning-diffs.jsonl");; esac
  S=$SPLIT
  OUT="$PROJ/cal-$TAG-$ct-$S"
  # offrig's --resume repeats the same model, gold and settings, so the full argument list goes both ways;
  # only --out (a new run) vs --resume (an existing one) differs.
  if [ -f "$OUT/manifest.json" ]; then WHERE=(--resume "$OUT"); else WHERE=(--out "$OUT"); fi
  "$OFFRIG" verify calibrate "${files[@]}" --model "$MODEL" --think "$THINK" --structured "$STRUCT"     --check-type "$ct" --split "$S" --project "$PROJ" ${EXTRA[@]+"${EXTRA[@]}"} "${WHERE[@]}" 2>&1 | tail -25
done
curl -s http://127.0.0.1:11434/api/generate -d "{\"model\":\"$MODEL\",\"keep_alive\":0}" >/dev/null
