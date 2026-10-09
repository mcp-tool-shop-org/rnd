#!/usr/bin/env bash
# The whole smoke as one run (the Publisher's reading of the rest rule: short loads, one rest before and one
# after). Each candidate in candidates.txt, smallest first, with its think setting; each unloaded after.
#   bash smoke_all.sh <scratch-project-dir>
set -uo pipefail
PROJ=${1:?scratch project dir}; HERE="$(cd "$(dirname "$0")" && pwd)"
# The VRAM watchdog must be alive: read the heartbeat's modified time only, never open the file (the
# Publisher, 2026-10-09: opening it collided with the watchdog's own writes).
HB=${WATCHDOG_HEARTBEAT:-/e/AI/training/_watchdog_HEARTBEAT}
age=$(( $(date +%s) - $(stat -c %Y "$HB" 2>/dev/null || echo 0) ))
[ "$age" -le 60 ] || { echo "REFUSED: watchdog heartbeat is ${age}s old"; exit 5; }
n=$(curl -s http://127.0.0.1:11434/api/ps | python -c "import json,sys; print(len(json.load(sys.stdin).get('models',[])))")
[ "$n" = 0 ] || { echo "REFUSED: $n model(s) on the card"; exit 4; }
grep -v "^#" "$HERE/candidates.txt" | while read -r model think _rest; do
  [ -n "$model" ] || continue
  echo "== $model think=$think $(date +%T)"
  bash "$HERE/smoke.sh" "$PROJ" "$model" "$think"
done
echo "== smoke done $(date +%T)"
