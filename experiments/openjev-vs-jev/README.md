# Local OpenJev against hosted Jev, on sense-si's 124 phrases

**Question:** can a free, local Jev-shaped decision model stand in for hosted Jev
(`typesafe/jev-1.13`, paid) in sense-si's research loop?

**Design:** ask OpenJev the identical question sense-si asked hosted Jev ("Is this
phrase clean?" as a yes/no with true/false criteria) over the identical 124 hearing
records. Score both against the Director's listening marks with sense-si's own study
code. Hosted Jev's answers come from sense-si's published run
(`docs/calibration/phrases.json`), so this costs no API spend.

Research entry: `2026-10-07-openjev-and-open-jev-alternatives`.

## Pinned inputs

| what | value |
|---|---|
| model | `openjev/openjev-GGUF` `OpenJev-Q4_K_M.gguf`, sha256 `7baa5501dfeb7d2b80d7bfa3fe85373304557e30efcea8fb350b5f3f1252ef21` (16.55 GB; licence CC BY-NC 4.0, research use) |
| server | llama.cpp `llama-server` build 11433 (GGUF made with b11147) |
| helper | `openjev/openjev` `helper/shim.py`, sha256 `81a22f1b1b8912a465059207ef9f60b7c6c16b4de6372305d867efbe38a1987a` (unmodified, Apache-2.0) |
| tokenizer | `openjev/openjev` tokenizer files (letters A/B are single tokens 32/33) |
| requests | sense-si `origin/main` at `f778c1d`, rebuilt by `build_requests.py`; every label matches the hosted run |
| hosted Jev | `typesafe/jev-1.13`, dated `jev-1.13-20260917`, raw `p_yes` per phrase |

## Run (GPU steps need the Director's go)

```powershell
# 1. model server (GPU)
E:\AI\llama.cpp\llama-server.exe -m E:\AI-Models\openjev\OpenJev-Q4_K_M.gguf -ngl 999 -c 16384 -np 2 --jinja --port 8000 --host 127.0.0.1

# 2. decision helper, with the authors' documented settings (CPU)
$env:VLLM='http://127.0.0.1:8000/v1'; $env:TOKENIZER='E:\AI-Models\openjev\tokenizer'
$env:READOUT_T='0.85'; $env:READOUT_NOUL_T='1.829074'; $env:READOUT_NOUL_BIAS='0'; $env:READOUT_INSTR_STYLE='pyrepr'
E:\AI\envs\openjev-shim\Scripts\python.exe E:\AI-Models\openjev\shim.py --port 8765

# 3. ask, then score
python run_openjev.py
E:\AI\sense-si\.venv\Scripts\python.exe compare.py
```

## Deviations from the authors' setup (read before trusting the numbers)

- **llama.cpp instead of vLLM.** The helper speaks the OpenAI chat API to either.
  The vLLM-only `allowed_token_ids` is ignored by llama.cpp; the helper's own comment
  says vLLM reports log-probabilities before that mask, so the readout is unaffected.
- **`READOUT_TARGETED` off.** The authors' numbers read each letter's exact score by
  token id, through vLLM-only parameters. Here the letters are read from the top-20
  list. For a yes/no question both letters are almost always in it; if one is not,
  the helper floors it at -30, so any phrase whose answer sits at the 0/1 rail is
  suspect and is reported.
- **Q4_K_M quantisation.** The authors measured Q4_K_M at −0.34 points against the
  16-bit model (95% interval −1.06 to +0.39) on 1,789 held-out questions.
- **The yes/no calibration constants** (`1.829074`, bias `0`) were fitted by the
  authors on their own boolean sets, not on singing records. sense-si's study code
  refits a temperature on its inner split, as it did for hosted Jev.

## Results

Not yet run: waiting for the Director's go on GPU use.
