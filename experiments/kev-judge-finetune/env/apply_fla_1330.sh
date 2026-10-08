#!/usr/bin/env bash
# Apply upstream fla fix #1330 (commit b8ff84870, 2026-10-06, "Remove stale BT from CP autotune key")
# to flash-linear-attention 0.5.2 in a venv. Triton 3.9 rejects autotune keys that aren't kernel
# arguments, so 0.5.2 fails at import under the cu134 nightly. One line; refuses to patch anything else.
set -euo pipefail
VENV=${1:?usage: apply_fla_1330.sh <venv>}
F="$VENV/lib/python3.12/site-packages/fla/ops/cp/chunk_delta_h.py"
grep -q "^Version: 0.5.2$" "$VENV"/lib/python3.12/site-packages/fla_core-0.5.2.dist-info/METADATA
L=$(sed -n 328p "$F")
if [ "$L" = "    key=['HV', 'K', 'V']," ]; then echo "already applied"; exit 0; fi
[ "$L" = "    key=['HV', 'K', 'V', 'BT']," ] || { echo "line 328 is not the expected one: $L"; exit 1; }
sed -i "328s/key=\['HV', 'K', 'V', 'BT'\],/key=['HV', 'K', 'V'],/" "$F"
sha256sum "$F"
