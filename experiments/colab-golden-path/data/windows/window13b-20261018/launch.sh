#!/usr/bin/env bash
# Window 13b = step 6 W-B (R&D's go, 2026-10-18): Lightning and Muse critique each other, resumed at w1 from the real
# sealed drafts, the chain's priors beside them. Real run on one A100, cap 8.8 units. From the rig in WSL Ubuntu:
#   MSYS_NO_PATHCONV=1 wsl -d Ubuntu -e bash -l window13b-20261018/launch.sh
set -uo pipefail
D=window13b-20261018
cd "$D" || exit 2
check() { [ "$(sha256sum "$1" | cut -d' ' -f1)" = "$2" ] || { echo "REFUSED: $1 is not $2" >&2; exit 2; }; }
check resume.tar 1f5348940987c7facfb64b564a87c936c86d187f58603853d7e3b2ff0d4eec45
check prior.tar 2b49f6ac54e967a81342ff60cac76ed545ae047275ada2036d5d2ecb9d8aba5e
check pack.tar aa11101c9d47e45f3d5626342906090f5360dc2809da80c8318e6bdc21f90fbb
check card-values.json 36cd89bbd95f2918528ae40b6ebfc1b91c3f17daccc0db708f36251b0bc9e207
check window1-20261016/build/llama-server b4659b3fc74037deb96b2148c455753121fa21dde174d7124547e2bf9ffd37c3
unset PIN_STUB PIN_PILOT_TWINS PIN_PILOT_CRITIC PIN_ONLY PIN_SKIP_BINARY
export PIN_GPU=A100 PIN_SESSION=pinw13b PIN_CAP_UNITS=8.8 PIN_WALL_S=7200
export PIN_ROLE=pilot
export PIN_ROLESET_COMMIT=c1cf4ae2caba722bf59cf79571bfc2fa4e558642
export PIN_RND_COMMIT=018b6cf677aab0e41363d826b589be342d38d8b9
export PIN_PILOT_WRITERS=nemotron-3.5-lightning-30b-a3b,muse-glimmer-30b
export PIN_PILOT_CRITIC_FOR=nemotron-3.5-lightning-30b-a3b=muse-glimmer-30b,muse-glimmer-30b=nemotron-3.5-lightning-30b-a3b
export PIN_PILOT_SLOT_IDS=T02-A-01,T02-C-01,T02-D-01,T02-E-01,T02-B-01,T02-A-02,T02-C-08,T02-D-05
export PIN_PILOT_TWIN_IDS=T04-C-AP-01,T04-D-AP-02
export PIN_PILOT_WAVES=4 PIN_RESUME_WAVE=1
export PIN_RESUME_DIR=/content/resume/pilot-w1 PIN_RESUME_PRIOR_DIR=/content/prior/pilot-w0
export PIN_UPLOADS="$D/pack.tar $D/card-values.json $D/resume.tar $D/prior.tar"
bash "$D/smoke_window.sh" window1-20261016/build/llama-server "$D" 2>&1 | tee "$D/rig.log"
