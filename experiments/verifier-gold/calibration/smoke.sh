#!/usr/bin/env bash
# Calibration smoke: 4 grounded + 4 reasoning tune claims per candidate, to settle --think and --structured
# per model and measure seconds per claim before any full run. GPU: run only in a slot the Publisher grants.
# The new offrig migrates a project's store to schema v6, so it runs against a scratch project, never the
# R&D project an older offrig MCP server uses.
#   bash smoke.sh <scratch-project-dir> <model> [think]
set -uo pipefail
PROJ=${1:?scratch project dir}; MODEL=${2:?model}; THINK=${3:-on}
GOLD="$(cd "$(dirname "$0")/.." && pwd)"
OFFRIG=${OFFRIG:-"$HOME/.local/bin/offrig.exe"}
mkdir -p "$PROJ"
for ct in grounded reasoning; do
  case $ct in grounded) files=("$GOLD/grounded.jsonl" "$GOLD/prs/grounded-prs.jsonl");; reasoning) files=("$GOLD/diffs/reasoning-diffs.jsonl");; esac
  "$OFFRIG" verify calibrate "${files[@]}" --model "$MODEL" --think "$THINK" --check-type "$ct" --split tune \
    --limit 4 --project "$PROJ" --out "$PROJ/smoke-${MODEL//[:\/]/_}-$ct-think$THINK" 2>&1 | tail -6
done
curl -s http://127.0.0.1:11434/api/generate -d "{\"model\":\"$MODEL\",\"keep_alive\":0}" >/dev/null
