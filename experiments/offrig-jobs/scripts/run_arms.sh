#!/usr/bin/env bash
# Published copy: the four paths below are set by the caller (the run used local paths on the rig). Line 54 is corrected here: in the run (8ff170ba) a literal newline inside that f-string crashed the C/D estimator (RESULTS.md).
# offrig --jobs measurement (plan offrig-jobs-measurement-plan.md, sha f680591b). Runs arms A1 A2 B C D in order on
# the 5090 under the Publisher's grant. Each arm: stop Ollama, start `ollama serve` with that arm's environment, guard
# (watchdog heartbeat, empty card, studio backend), run offrig verify calibrate on bench30 with --jobs N in its own
# project and out dir, sample nvidia-smi every 2 s, record /api/ps after load, unload. Halt rule: an arm whose model
# offloads (size_vram < size) stops the run and is recorded. Afterwards the Ollama desktop app is restarted as found.
#   bash run_arms.sh [arm ...]        (default: A1 A2 B C D)
set -uo pipefail
OFFRIG=${OFFRIG:?path to offrig.exe built from 7e99996a}
GOLD=${GOLD:?path to bench30.jsonl}
BASE=${BASE:?output directory for the runs}
MODEL=gemma4:31b
OLLAMA=http://127.0.0.1:11434
HB=${WATCHDOG_HEARTBEAT:?path to the VRAM watchdog heartbeat file}
APP="$LOCALAPPDATA/Programs/Ollama"
mkdir -p "$BASE"
[ "$(sha256sum "$GOLD" | cut -d' ' -f1)" = 0c88ec0f915c911a99d3fcf2d2e91104c0c65b0f279656f27afa2244099ce547 ] || { echo "REFUSED: bench30 sha"; exit 2; }
"$OFFRIG" --version | grep -q "offrig 1.2.0" || { echo "REFUSED: offrig build"; exit 2; }

stop_ollama() { taskkill //F //IM "ollama app.exe" >/dev/null 2>&1; taskkill //F //IM ollama.exe >/dev/null 2>&1; sleep 5; }
up() { curl -s "$OLLAMA/api/version" >/dev/null; }
loaded() { curl -s "$OLLAMA/api/ps" | python -c "import json,sys; print(len(json.load(sys.stdin).get('models',[])))"; }

arm_env() {  # jobs parallel kv fa
  case $1 in
    A1|A2) echo "1 1 f16 auto";;
    B) echo "2 2 f16 auto";;
    C) echo "4 4 f16 auto";;
    D) echo "4 4 q8_0 1";;
  esac
}


# The Publisher's 26 GB rule for arms C and D (2026-10-23): estimate weights + KV before starting; skip if over 26 GB.
# Per sequence at num_ctx 8192 (gemma4:31b, from `ollama show`): 10 global layers x 4 kv heads x 512 (K and V) x 8192
# tokens, plus 50 sliding-window layers x 16 kv heads x 256 (K and V) x a 1024-token window = 755 M elements.
# f16 is 2 bytes (1.51 GB); q8_0 about 1.0625 bytes (0.80 GB). Base = A1's measured peak minus one f16 sequence.
fits() {  # arm parallel kv
  local a=$1 P=$2 KV=$3
  python - "$BASE/smi-A1.csv" "$P" "$KV" "$a" <<'PY'
import sys,csv
smi,P,KV,a=sys.argv[1],int(sys.argv[2]),sys.argv[3],sys.argv[4]
peak=max(float(r[1].strip().split()[0]) for r in csv.reader(open(smi)) if len(r)>1)/1024  # GiB from MiB
elems=10*4*512*2*8192 + 50*16*256*2*1024
import os
def pk(f): return max(float(r[1].strip().split()[0]) for r in csv.reader(open(f)) if len(r)>1)/1024
th_f16=elems*2/2**30
bfile=os.path.join(os.path.dirname(smi),"smi-B.csv")
meas=pk(bfile)-peak if os.path.exists(bfile) else None   # B has 2 sequences, A1 has 1: one extra f16 sequence
per_f16=max(th_f16, meas or 0)
per=per_f16*(1 if KV=="f16" else 1.0625/2)
est=peak-per_f16+P*per
open(os.path.join(os.path.dirname(smi),"kv-increment.txt"),"w").write(f"theory_f16_GiB {th_f16:.2f} measured_B_minus_A1_GiB {meas if meas is None else round(meas,2)} used {per_f16:.2f}\n")
print(f"   estimate {a}: A1 peak {peak:.1f} GiB - 1 x {per_f16:.2f} + {P} x {per:.2f} = {est:.1f} GiB (theory f16 {th_f16:.2f}, measured B-A1 {meas if meas is None else round(meas,2)})")
sys.exit(0 if est<=26 else 1)
PY
}

run_arm() {
  local a=$1; read -r J P KV FA <<<"$(arm_env "$a")"
  local OUT="$BASE/$a" PROJ="$BASE/proj-$a"
  [ -e "$OUT" ] && { echo "REFUSED: $OUT exists"; return 2; }
  if [ "$a" = C ] || [ "$a" = D ]; then
    [ -f "$BASE/smi-A1.csv" ] || { echo "SKIP $a: no A1 measurement to estimate from"; echo "{\"arm\":\"$a\",\"skipped\":\"no A1 measurement\"}" > "$BASE/skip-$a.json"; return 0; }
    if ! fits "$a" "$P" "$KV" | tee "$BASE/estimate-$a.txt"; then :; fi
    fits "$a" "$P" "$KV" >/dev/null || { echo "SKIP $a: does not fit, $(sed -n 's/.*= //p' "$BASE/estimate-$a.txt") (the 26 GB rule)"; echo "{\"arm\":\"$a\",\"skipped\":\"does not fit\",\"estimate\":\"$(sed -n 's/.*= //p' "$BASE/estimate-$a.txt")\"}" > "$BASE/skip-$a.json"; return 0; }
  fi
  stop_ollama
  local age=$(( $(date +%s) - $(stat -c %Y "$HB" 2>/dev/null || echo 0) )); [ "$age" -le 60 ] || { echo "REFUSED: watchdog ${age}s"; return 5; }
  ( export OLLAMA_NUM_PARALLEL=$P OLLAMA_KV_CACHE_TYPE=$KV; [ "$FA" = 1 ] && export OLLAMA_FLASH_ATTENTION=1;
    "$APP/ollama.exe" serve > "$BASE/serve-$a.log" 2>&1 & echo $! > "$BASE/serve-$a.pid" )
  for i in $(seq 1 60); do up && break; sleep 1; done
  up || { echo "REFUSED: ollama did not start for $a"; return 4; }
  [ "$(loaded)" = 0 ] || { echo "REFUSED: card not empty"; return 4; }
  mkdir -p "$PROJ"
  printf '{"arm":"%s","jobs":%s,"OLLAMA_NUM_PARALLEL":%s,"OLLAMA_KV_CACHE_TYPE":"%s","OLLAMA_FLASH_ATTENTION":"%s","ollama":"%s","offrig":"7e99996a"}\n' \
    "$a" "$J" "$P" "$KV" "$FA" "$(curl -s $OLLAMA/api/version)" > "$BASE/env-$a.json"
  # Warm-up: load the model before offrig starts, so a cold load never hits offrig's request timeout (A1's first
  # try, 23:18:47, aborted at 16 s mid-load). Load time is kept out of the arm's measured wall time.
  curl -s -m 600 "$OLLAMA/api/generate" -d "{\"model\":\"$MODEL\",\"keep_alive\":\"60m\"}" >/dev/null
  for i in $(seq 1 120); do [ "$(loaded)" = 1 ] && break; sleep 2; done
  curl -s "$OLLAMA/api/ps" > "$BASE/ps-$a.json"
  [ "$(loaded)" = 1 ] || { echo "REFUSED: $MODEL did not load for $a"; return 4; }
  ( while :; do nvidia-smi --query-gpu=timestamp,memory.used,utilization.gpu,temperature.gpu,power.draw --format=csv,noheader >> "$BASE/smi-$a.csv"; sleep 2; done ) & local SMI=$!
  echo "== arm $a jobs=$J parallel=$P kv=$KV fa=$FA start $(date +%T)"
  "$OFFRIG" verify calibrate "$GOLD" --model "$MODEL" --think on --structured on --split tune --jobs "$J" \
    --project "$PROJ" --out "$OUT" > "$BASE/$a.log" 2>&1; local RC=$?
  kill $SMI 2>/dev/null
  curl -s "$OLLAMA/api/ps" > "$BASE/ps-$a-end.json"
  curl -s "$OLLAMA/api/generate" -d "{\"model\":\"$MODEL\",\"keep_alive\":0}" >/dev/null; sleep 5
  echo "== arm $a end $(date +%T) rc=$RC; $(grep -c . "$OUT/verdicts.jsonl" 2>/dev/null) verdicts"
  [ $RC = 0 ] || { echo "   offrig exited $RC: see $BASE/$a.log"; return 8; }
  python - "$BASE/ps-$a.json" <<'EOF'
import json,sys
ms=json.load(open(sys.argv[1])).get("models") or []
if not ms: print("   no model in /api/ps: not a measurement"); sys.exit(2)
m=ms[0]
off = m.get("size_vram",0) < m.get("size",0)
print("   size", m.get("size"), "size_vram", m.get("size_vram"), "OFFLOADED" if off else "on-card")
sys.exit(1 if off else 0)
EOF
  case $? in 0) return 0;; 1) return 6;; *) return 7;; esac
}

ARMS=${*:-A1 A2 B C D}
for a in $ARMS; do
  run_arm "$a"; rc=$?
  if [ $rc = 6 ]; then echo "RECORDED: $a offloaded (halt rule for this arm)"; [ "$a" = C ] && continue; break; fi
  [ $rc != 0 ] && { echo "HALT: $a rc=$rc"; break; }
done
stop_ollama
powershell -NoProfile -Command 'Start-Process "$env:LOCALAPPDATA\Programs\Ollama\ollama app.exe"'
sleep 8; echo "== done $(date +%T); ollama $(curl -s $OLLAMA/api/version); models loaded $(loaded)"
