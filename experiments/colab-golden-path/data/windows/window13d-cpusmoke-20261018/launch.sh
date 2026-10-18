#!/usr/bin/env bash
# The 0-unit CPU smoke through the new smoke_window (R&D, 2026-10-18), before any real token is used: a DUMMY token in a
# real token's shape (never the real one) goes the prebuild way (PIN_ROLE=prebuild, HF_TOKEN_GGUF_WRITE overridden
# here with the dummy) through the real colab CLI; mock_job reads /dev/shm/hf.token and deletes it. Afterwards the CLI's
# own history (~/.config/colab-cli), the rig log and every file the window kept are searched for the dummy, literally and
# by the hf_ token shape. From the rig in WSL:
#   MSYS_NO_PATHCONV=1 wsl -d Ubuntu -e bash -l window13d-cpusmoke-20261018/launch.sh
set -uo pipefail
D=window13d-cpusmoke-20261018
DUMMY="hf_""DUMMYsmokeNOTaREALtoken20261018abcdEFGH"   # split: this file never holds the token shape
export HF_TOKEN_GGUF_WRITE="$DUMMY"; unset HF_TOKEN_GGUF_READ HF_TOKEN
unset PIN_STUB PIN_GGUF_REPO
export PIN_GPU=CPU PIN_SESSION=cpusmoke PIN_CAP_UNITS=1 PIN_WALL_S=900 PIN_SKIP_BINARY=1 PIN_ROLE=prebuild
export PIN_HF_TOKEN_FROM=HF_TOKEN_GGUF_WRITE PIN_JOB_SCRIPT=mock_job.py PIN_MOCK_S=60 PIN_MOCK_EVERY_S=10
export PIN_DOWNLOADS=pin-result.json PIN_GATE_MIN_HF_MBPS=60 PIN_GATE_MIN_RAM_GB=8
bash "$D/smoke_window.sh" /dev/null "$D" > "$D/rig.log" 2>&1
echo "window exit $?"
grep -E "VM gate|uploaded the token|exec exit|end balance|sessions after|No active" "$D/rig.log"
grep -h "TOKEN FILE READ" "$D/job.log" || echo "NO TOKEN FILE READ LINE"
echo "== search for the dummy (literal, then the hf_ shape)"
H=~/.config/colab-cli
for where in "$H" "$D"; do
  lit=$(grep -rlF -- "$DUMMY" "$where" 2>/dev/null | grep -v '/launch.sh$' || true)
  shp=$(grep -rlE -- 'hf_[A-Za-z0-9]{30,}' "$where" 2>/dev/null | grep -v '/launch.sh$' || true)
  echo "$where: literal hits [${lit:-none}] shape hits [${shp:-none}]"
done
echo "== history file for this session: $(ls -l "$H/history/cpusmoke.jsonl" 2>/dev/null | cut -d' ' -f1,5,9 || echo absent)"
echo "== permissions before: $(stat -c '%a %n' "$H") $(find "$H" -type f -printf '%m ' | sort | uniq -c | tr '\n' ' ')"
chmod 700 "$H" "$H/history" 2>/dev/null; find "$H" -type f -exec chmod 600 {} +
echo "== permissions after: $(stat -c '%a %n' "$H") $(stat -c '%a' "$H/history") $(find "$H" -type f -printf '%m ' | sort | uniq -c | tr '\n' ' ')"
