#!/usr/bin/env bash
# Prebuild 1 of 4: Muse (R&D's go, 2026-10-18). A --high-mem CPU runtime (0.26/hr measured) converts Muse at its pinned
# revision and llama.cpp commit, and uploads the Q8_0 to the studio's private GGUF repo only if it byte-matches
# expect_sha256 c321320a... The write token is read at Windows User scope by the Git Bash wrapper (run.sh) and reaches
# WSL only through WSLENV; smoke_window sends it to the VM as a /dev/shm file after the VM gate. From Git Bash:
#   bash /e/AI/Publisher/receipts/colab/window13e-prebuild-muse-20261018/run.sh
set -uo pipefail
D=window13e-prebuild-muse-20261018
[ -n "${HF_TOKEN_GGUF_WRITE:-}" ] || { echo "REFUSED: HF_TOKEN_GGUF_WRITE didn't reach WSL"; exit 2; }
unset PIN_STUB HF_TOKEN HF_TOKEN_GGUF_READ
export PIN_ROLE=prebuild PIN_ONLY=muse-glimmer-30b PIN_GPU=CPU PIN_HIGH_MEM=1 PIN_SESSION=pb-muse
export PIN_GGUF_REPO=<private-gguf-repo> PIN_HF_TOKEN_FROM=HF_TOKEN_GGUF_WRITE
export PIN_CAP_UNITS=1 PIN_WALL_S=7200 PIN_SKIP_BINARY=1 PIN_GATE_MIN_DISK_GB=111 PIN_GATE_MIN_HF_MBPS=60 PIN_GATE_MIN_RAM_GB=40
export PIN_STALL_S=2400 PIN_DOWNLOADS=pin-result.json
export PIN_UPLOADS="$D/apache-2.0.txt"
bash "$D/smoke_window.sh" /dev/null "$D" 2>&1 | tee "$D/rig.log"
