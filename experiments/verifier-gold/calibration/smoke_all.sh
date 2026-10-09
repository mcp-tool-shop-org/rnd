#!/usr/bin/env bash
# The whole smoke as one run (the Publisher's reading of the rest rule: short loads, one rest before and one
# after). Each candidate in candidates.txt, smallest first, with its think setting; each unloaded after.
#   bash smoke_all.sh <scratch-project-dir>
set -uo pipefail
PROJ=${1:?scratch project dir}; HERE="$(cd "$(dirname "$0")" && pwd)"
n=$(curl -s http://127.0.0.1:11434/api/ps | python -c "import json,sys; print(len(json.load(sys.stdin).get('models',[])))")
[ "$n" = 0 ] || { echo "REFUSED: $n model(s) on the card"; exit 4; }
grep -v '^#' "$HERE/candidates.txt" | while read -r model think; do
  [ -n "$model" ] || continue
  echo "== $model think=$think $(date +%T)"
  bash "$HERE/smoke.sh" "$PROJ" "$model" "$think"
done
echo "== smoke done $(date +%T)"
