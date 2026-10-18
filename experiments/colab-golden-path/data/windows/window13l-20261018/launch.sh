#!/usr/bin/env bash
# Window 13l = step 6 W-A (DRAFT for R&D's review; nothing opens before R&D's go). Writers Qwen3.8, Gemma, Granite and
# Bolt, Muse critiques; resumed at w1 from the real sealed drafts (resume.tar 3d8b7ed5, unchanged since the stub rungs),
# Granite and Bolt w0 priors beside them (prior.tar ed826377). One A100, role-set 430285a (gate, prefetch, upload fix).
# - Pre-built Q8_0s are prefetched from the private repo at revision d847f5b8 with the READ token, byte-checked against
#   their pins, and the token is dropped before any wave. Bolt is the maker's GGUF, fetched as before.
# - Disk, measured: the four repo GGUFs 122.4 GB (Gemma 32.64 + Granite 31.11 + Muse 29.61 + Qwen3.8 29.05, from the
#   repo listing) + Bolt 22.0 (HF API) = 144.4 GB, + 20 margin = 164.4 against 204.2 free: floor 165.
# - HF floor 60 MB/s: the gate's 200 MB short read undersells the pipe about 2.7x (R&D, 2026-10-18), until recalibrated.
# - One window: survival run 13c held a busy session 4.5 h (270/270 lines, gaps 60-61 s); W-A projects ~4.1 h. The wall
#   is 16200 s, the length survival proved; the cap stops it at 25.1 units first only if the rate rises.
#   MSYS_NO_PATHCONV=1 wsl -d Ubuntu -e bash -l window13l-20261018/launch.sh
# Run from Git Bash so the read token goes over with WSLENV (presence only is checked here):
#   HF_TOKEN_GGUF_READ="$(powershell.exe -NoProfile -Command "[Environment]::GetEnvironmentVariable('HF_TOKEN_GGUF_READ','User')" | tr -d '\r\n')" WSLENV=HF_TOKEN_GGUF_READ MSYS_NO_PATHCONV=1 wsl -d Ubuntu -e bash -l window13l-20261018/launch.sh
set -uo pipefail
D=window13l-20261018
cd "$D" || exit 2
[ -n "${HF_TOKEN_GGUF_READ:-}" ] || { echo "REFUSED: HF_TOKEN_GGUF_READ didn't reach WSL"; exit 2; }
check() { [ "$(sha256sum "$1" | cut -d' ' -f1)" = "$2" ] || { echo "REFUSED: $1 is not $2" >&2; exit 2; }; }
check resume.tar 3d8b7ed583a3d23ace92c9263a7d59e006f06dc246adabf27e5d66dbdd7f15c1
check prior.tar ed8263776dc09b7e64688b37bcd097b415740895aafdc83beb2abc6bf23efc50
check pack.tar aa11101c9d47e45f3d5626342906090f5360dc2809da80c8318e6bdc21f90fbb
check card-values.json 36cd89bbd95f2918528ae40b6ebfc1b91c3f17daccc0db708f36251b0bc9e207
check pin_window.py 3b6dbb5b477fc48963bdbbb842b80ab68a1004c073ad6294bdb15be84ab738bc
check window1-20261016/build/llama-server b4659b3fc74037deb96b2148c455753121fa21dde174d7124547e2bf9ffd37c3
unset PIN_STUB PIN_PILOT_TWINS PIN_ONLY PIN_SKIP_BINARY PIN_PILOT_CRITIC_FOR HF_TOKEN HF_TOKEN_GGUF_WRITE
export PIN_GPU=A100 PIN_SESSION=pinw13l PIN_CAP_UNITS=25.1 PIN_WALL_S=16200
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
bash "$D/smoke_window.sh" window1-20261016/build/llama-server "$D" 2>&1 | tee "$D/rig.log"
