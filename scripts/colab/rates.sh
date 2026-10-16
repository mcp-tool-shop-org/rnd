#!/usr/bin/env bash
# Measure Colab's compute-unit rate per GPU type: one short session each.
#
#   GPUS="T4 L4 A100" ./rates.sh
#
# For each card: read `colab usage`, start a session, read the rate while it runs,
# run probe.py on it (wrapped in an outer timeout: a hung exec must not hold a paid
# VM), stop the session, and read the balance after. The rate shows while a session
# runs; the balance only moves after it ends. The last line lists any session still
# alive, and it must be empty.
set -u
here="$(cd "$(dirname "$0")" && pwd)"
export COLUMNS=150
for gpu in ${GPUS:-T4 L4 A100}; do
  s="rate-$gpu"
  echo "===== $gpu $(date -u +%FT%TZ)"
  colab usage 2>&1 | grep -E "balance|rate"
  if colab new --gpu "$gpu" -s "$s" 2>&1 | tail -3; then
    sleep 20
    echo "-- during"
    colab usage 2>&1 | grep -E "balance|rate|assign"
    timeout 180 colab exec -s "$s" -f "$here/probe.py" --timeout 90 2>&1 | tail -25
  fi
  colab stop -s "$s" 2>&1 | tail -2
  sleep 5
  echo "-- after"
  colab usage 2>&1 | grep -E "balance|rate|assign"
done
echo "== sessions still alive (must be none):"
colab sessions 2>&1 | tail -5
