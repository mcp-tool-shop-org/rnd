#!/bin/bash
# Serve one Kev size on the GPU, run the 0-shot and knowledge-in-context sets, stop the server.
# usage: bash kev_run.sh 4b|9b
set -u
SIZE=$1
EXP="/e/AI/Research and Development/experiments/openjev-vs-jev"
LOG=/e/AI-Models/openjev/work/logs; mkdir -p "$LOG"
say() { echo "$(date +%H:%M:%S) [kev-$SIZE] $*" | tee -a "$LOG/kev.log"; }
export HF_HOME='E:\AI-Models\hf-cache' HF_HUB_OFFLINE=1 OPENJEV_WORK='E:/AI-Models/openjev/work'

used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | tr -d ' \r')
busy=$(ollama ps 2>/dev/null | tail -n +2 | grep -c .)
if [ "$busy" -ne 0 ] || [ "$used" -gt 10000 ]; then say "GPU busy (${used} MiB, ollama models: $busy); not starting"; exit 2; fi
say "GPU free (${used} MiB); starting kev.serve"

cd /e/AI-Models/kev/kev
/e/AI/envs/kev/Scripts/python.exe /e/AI-Models/kev/kev_serve_capped.py "${KEV_CAP:-0.82}" --run "jaredpalmer/kev-$SIZE@v1.0" --port 8009 > "$LOG/kev-$SIZE-serve.log" 2>&1 &
SV=$!
for i in $(seq 1 180); do curl -s -m 2 http://127.0.0.1:8009/v1/models >/dev/null && break; sleep 5; done
say "server up: $(curl -s -m 2 http://127.0.0.1:8009/v1/models | head -c 200); VRAM $(nvidia-smi --query-gpu=memory.used --format=csv,noheader)"

( while kill -0 $SV 2>/dev/null; do nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits; sleep 2; done ) > "$LOG/kev-$SIZE-vram.txt" &
VM=$!

cd "$EXP"
/e/AI/envs/kev/Scripts/python.exe run_openjev.py --url http://127.0.0.1:8009/v1/systemone --name "kev$SIZE" > "$LOG/kev-$SIZE-run.log" 2>&1
say "0-shot exit $? ($(tail -1 "$LOG/kev-$SIZE-run.log"))"
/e/AI/envs/kev/Scripts/python.exe run_openjev.py --url http://127.0.0.1:8009/v1/systemone --name "kev$SIZE-knowledge" --requests requests-knowledge.jsonl > "$LOG/kev-$SIZE-knowledge-run.log" 2>&1
say "knowledge exit $? ($(tail -1 "$LOG/kev-$SIZE-knowledge-run.log"))"

wp=$(cat /proc/$SV/winpid 2>/dev/null); [ -n "$wp" ] && taskkill //F //T //PID "$wp" >/dev/null 2>&1
kill $SV 2>/dev/null; sleep 3; kill $VM 2>/dev/null
say "server stopped; peak VRAM $(sort -n "$LOG/kev-$SIZE-vram.txt" | tail -1) MiB; now $(nvidia-smi --query-gpu=memory.used --format=csv,noheader)"
say DONE
