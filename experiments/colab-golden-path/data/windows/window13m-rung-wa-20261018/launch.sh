#!/usr/bin/env bash
# Window 13m = the rung at role-set 430285a before W-A (R&D, 2026-10-18): W-A's exact launch (window13l launch.sh) as a
# STUB on CPU --high-mem, through smoke_window.sh with the real VM gate, the /dev/shm READ token and the real prefetch of
# the four pre-built Q8_0s at d847f5b8 (~122.4 GB, each sha-checked against its pin, token dropped before Pool). Then
# the stub waves from the same resume.tar and prior.tar. Changes from W-A's launch, and only these: PIN_STUB=1,
# PIN_GPU=CPU, PIN_HIGH_MEM=1, PIN_CAP_UNITS=1, PIN_SESSION=pinw13m, PIN_WALL_S=7200, PIN_SKIP_BINARY=1 (a stub pilot
# builds and serves no llama-server), PIN_STALL_S=2400 (a ~30 GB download writes no log line for minutes), RAM floor 40
# (the CPU --high-mem shape, as in 13e/13g). Disk floor 165 and HF floor 60 are W-A's.
# Criterion (d) carries from 12s6a: c1cf4ae..430285a doesn't touch the lock code, and W-A launches with one exec too.
# From Git Bash:
#   HF_TOKEN_GGUF_READ="$(powershell.exe -NoProfile -Command "[Environment]::GetEnvironmentVariable('HF_TOKEN_GGUF_READ','User')" | tr -d '\r\n')" WSLENV=HF_TOKEN_GGUF_READ MSYS_NO_PATHCONV=1 wsl -d Ubuntu -e bash -l window13m-rung-wa-20261018/launch.sh
set -uo pipefail
D=window13m-rung-wa-20261018
cd "$D" || exit 2
[ -n "${HF_TOKEN_GGUF_READ:-}" ] || { echo "REFUSED: HF_TOKEN_GGUF_READ didn't reach WSL"; exit 2; }
check() { [ "$(sha256sum "$1" | cut -d' ' -f1)" = "$2" ] || { echo "REFUSED: $1 is not $2" >&2; exit 2; }; }
check resume.tar 3d8b7ed583a3d23ace92c9263a7d59e006f06dc246adabf27e5d66dbdd7f15c1
check prior.tar ed8263776dc09b7e64688b37bcd097b415740895aafdc83beb2abc6bf23efc50
check pack.tar aa11101c9d47e45f3d5626342906090f5360dc2809da80c8318e6bdc21f90fbb
check card-values.json 36cd89bbd95f2918528ae40b6ebfc1b91c3f17daccc0db708f36251b0bc9e207
check pin_window.py 3b6dbb5b477fc48963bdbbb842b80ab68a1004c073ad6294bdb15be84ab738bc
unset PIN_PILOT_TWINS PIN_ONLY PIN_PILOT_CRITIC_FOR HF_TOKEN HF_TOKEN_GGUF_WRITE
export PIN_STUB=1 PIN_GPU=CPU PIN_HIGH_MEM=1 PIN_SESSION=pinw13m PIN_CAP_UNITS=1 PIN_WALL_S=7200
export PIN_SKIP_BINARY=1 PIN_STALL_S=2400 PIN_GATE_MIN_RAM_GB=40
export PIN_ROLE=pilot
export PIN_ROLESET_COMMIT=430285a379aa8d6f452e730830d6e765b3c389e0
export PIN_RND_COMMIT=018b6cf677aab0e41363d826b589be342d38d8b9
export PIN_GGUF_REPO=<private-gguf-repo> PIN_GGUF_REVISION=d847f5b87a6b0f8cb9ae3ff5c6330bafb0364670
export PIN_HF_TOKEN_FROM=HF_TOKEN_GGUF_READ
export PIN_GATE_MIN_DISK_GB=165 PIN_GATE_MIN_HF_MBPS=60   # 60: short-read undersell, until the floor is recalibrated
export PIN_PILOT_WRITERS=qwen3.8-27b,gemma-4-31b-it,granite-4.2-30b,nemotron-3.5-bolt-74b-a9b
export PIN_PILOT_CRITIC=muse-glimmer-30b
export PIN_PILOT_SLOT_IDS=T02-A-01,T02-C-01,T02-D-01,T02-E-01,T02-B-01,T02-A-02,T02-C-08,T02-D-05
export PIN_PILOT_TWIN_IDS=T04-C-AP-01,T04-D-AP-02
export PIN_PILOT_WAVES=4 PIN_RESUME_WAVE=1
export PIN_RESUME_DIR=/content/resume/pilot-w1 PIN_RESUME_PRIOR_DIR=/content/prior/pilot-w0
export PIN_UPLOADS="$D/pack.tar $D/card-values.json $D/resume.tar $D/prior.tar"
bash "$D/smoke_window.sh" /dev/null "$D" 2>&1 | tee "$D/rig.log"
