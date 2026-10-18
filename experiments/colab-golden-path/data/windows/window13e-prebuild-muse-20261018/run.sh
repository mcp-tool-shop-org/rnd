#!/usr/bin/env bash
# Git Bash wrapper: the write token by name from Windows User scope into this process only, then WSL via WSLENV.
set -uo pipefail
HF_TOKEN_GGUF_WRITE="$(powershell.exe -NoProfile -Command "[Environment]::GetEnvironmentVariable('HF_TOKEN_GGUF_WRITE','User')" | tr -d '\r\n')"
export HF_TOKEN_GGUF_WRITE WSLENV=HF_TOKEN_GGUF_WRITE
MSYS_NO_PATHCONV=1 wsl -d Ubuntu -e bash -l window13e-prebuild-muse-20261018/launch.sh
