#!/usr/bin/env bash
# Survival run (R&D, 2026-10-18): does a busy command-line session last 4.5 h on this plan? CPU runtime (0.08/hr), the
# same smoke_window exec path as the paid windows, mock_job writing a job.log line every 60 s for 16200 s. The answer
# decides whether W-A (about 4.1 h) runs as one window or two. From the rig in WSL:
#   MSYS_NO_PATHCONV=1 wsl -d Ubuntu -e bash -l window13c-survival-20261018/launch.sh
set -uo pipefail
D=window13c-survival-20261018
unset PIN_STUB PIN_HF_TOKEN_FROM PIN_GGUF_REPO
export PIN_GPU=CPU PIN_SESSION=cpusurv PIN_CAP_UNITS=1 PIN_WALL_S=17400 PIN_SKIP_BINARY=1
export PIN_JOB_SCRIPT=mock_job.py PIN_MOCK_S=16200 PIN_MOCK_EVERY_S=60 PIN_DOWNLOADS=pin-result.json
export PIN_GATE_MIN_HF_MBPS=60 PIN_GATE_MIN_RAM_GB=8
bash "$D/smoke_window.sh" /dev/null "$D" 2>&1 | tee "$D/rig.log"
