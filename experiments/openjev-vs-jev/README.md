# Local decision models against hosted Jev, on sense-si's 124 phrases

OpenJev first, then Kev-4B and Kev-9B (see [Kev](#kev-4b-and-kev-9b-run-2026-10-07)).

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
E:\AI\llama.cpp\llama-server.exe -m E:\AI-Models\openjev\OpenJev-Q4_K_M.gguf -ngl 999 -c 16384 -np 2 --jinja --no-mmap --port 8000 --host 127.0.0.1

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

## Results (run 2026-10-07 on the Robot rig, RTX 5090)

124 phrases, 73 marked clean. A constant guess at the base rate scores Brier
0.2421; a useful model must beat that. Receipts: `results/compare.json`,
`results/openjev.jsonl`, `results/determinism.json`.

| | hosted Jev 1.13 | local OpenJev Q4_K_M |
|---|---|---|
| Brier, raw [95% CI] | 0.334 [0.293, 0.371] | 0.256 [0.233, 0.280] |
| Brier after sense-si's temperature fit | 0.252 | 0.251 |
| AUC, pooled [95% CI] | 0.56 [0.46, 0.66] | 0.46 [0.35, 0.57] |
| AUC, mean within mix (5 mixes) | 0.57 | 0.59 |
| mean p(clean) | 0.28 | 0.59 |
| sense-si decision layer | not adopted | not adopted |
| cost per run | API spend | free, ~1.3 s per phrase (p90 1.7 s) |

- **Neither model judges these phrases.** Both AUC intervals include 0.5, and after
  temperature scaling both land at the base rate. sense-si's decision layer rejects
  both on the same four grounds.
- **OpenJev tracks hosted Jev.** Pearson r = 0.61 between their probabilities, but
  OpenJev sits about 0.3 higher, so they fall on the same side of 0.5 only 15% of
  the time. Raw Brier favours OpenJev only because its offset happens to sit
  nearer this set's 59% clean rate.
- **Deterministic:** five repeated phrases gave identical answers.
- **No railed readouts:** OpenJev's answers ran 0.23 to 0.74, so the top-20 letter
  readout never had to floor a letter.
- Pooled AUC on this set mostly measures which mix a phrase came from (ai-jam-sessions
  PR #88), which is why the within-mix column is there.

**Verdict:** as a free local stand-in for hosted Jev on this question, OpenJev is
adequate: it ranks phrases much as Jev does, at no API cost. But the question
itself is beyond both models from this input, so swapping models does not rescue
the phrase-clean judgement. The licence (CC BY-NC 4.0) limits OpenJev to research use.

**Run notes:** this run served the model with memory mapping on (the command above
now adds `--no-mmap`, since mapping kept about 9 GB of the file in system RAM). The
chat template was the GGUF's own (`--jinja`); its rendering was not compared with
the transformers template.

## Kev-4B and Kev-9B (run 2026-10-07)

Asked by ai-jam-sessions after the OpenJev run, with the Director's go. Kev
(`jaredpalmer/kev`, Apache-2.0) serves the same `/v1/systemone` API, so the
identical request bodies were sent to it.

### Pinned inputs

| what | value |
|---|---|
| models | `jaredpalmer/kev-4b@v1.0` (adapter + pointer head on `Qwen/Qwen3.5-4B-Base` @ `1001bb4d`), `jaredpalmer/kev-9b@v1.0` (on `Qwen/Qwen3.5-9B-Base` @ `68c46c4b`); fitted serving temperatures 2.41 and 2.19 |
| server | `kev.serve` from `jaredpalmer/kev` @ `5e42a7a`, bf16, torch 2.8.0+cu128, transformers 5.19.0 |
| kernels | reference PyTorch paths: `flash-linear-attention` and `causal_conv1d` need Triton, which this Windows rig lacks. Kev documents these paths as exact but slower |
| memory | `kev_serve_capped.py` capped PyTorch at 0.82 of the card for Kev-9B, so a large request fails instead of paging past the VRAM watchdog's ceiling |
| runner | `kev_run.sh 4b\|9b`: checks the GPU is free, serves, runs both request sets, stops the server |

### Two request sets

- **0-shot:** the identical state hosted Jev and OpenJev saw (`requests.jsonl`).
- **Knowledge in context** (`build_knowledge_requests.py`): the same state plus three additions.
  - ai-jam-sessions' per-phrase join evidence (`phrase_evidence`: joins, switches,
    air, spectral jump, repeat similarity, click z, f0 step, octave jumps, pct_max…).
  - A rubric in the question naming the defect kinds the Director marks and the
    evidence field that measures each.
  - Four labelled examples (two clean, two not), drawn leave-one-mix-out, so none
    comes from the mix being scored. Examples carry evidence only, to stay inside
    Kev's validated 8,192 tokens (largest request: 5,702 tokens).

  The evidence files are ai-jam-sessions run outputs and stay out of this repo;
  the join to sense-si ids was checked on start and end times for all 124.

### Results

Scored by `compare_all.py` (receipt `results/compare-all.json`). In-sample base
rate Brier 0.242; a constant 0.5 scores 0.250.

| model | Brier raw | Brier, sense-si temperature fit | Brier, leave-one-mix-out temperature | AUC pooled [95% CI] | AUC within mix | mean p | r with Jev |
|---|---|---|---|---|---|---|---|
| hosted Jev 1.13 | 0.334 | 0.252 | 0.251 | 0.56 [0.46, 0.66] | 0.57 | 0.28 | — |
| OpenJev Q4_K_M | 0.256 | 0.251 | 0.257 | 0.46 [0.35, 0.57] | 0.59 | 0.59 | 0.61 |
| Kev-4B | 0.292 | 0.240 | 0.275 | 0.54 [0.44, 0.64] | 0.64 | 0.81 | 0.67 |
| Kev-9B | 0.306 | 0.242 | 0.278 | 0.52 [0.42, 0.63] | 0.60 | 0.84 | 0.66 |
| Kev-4B + knowledge | 0.254 | 0.248 | 0.260 | 0.48 [0.38, 0.59] | 0.54 | 0.61 | 0.42 |
| Kev-9B + knowledge | 0.278 | 0.253 | 0.251 | 0.42 [0.32, 0.52] | 0.49 | 0.56 | 0.19 |

The leave-one-mix-out base rate (each mix scored with the other six mixes' clean
rate) is 0.278. That is worse than a constant 0.5, because the mixes' clean rates
differ a lot. Leave-one-mix-out temperatures run large, which flattens a model
towards 0.5, so a Brier near 0.25 in that column means "no usable signal".

| | OpenJev 27B Q4 (llama.cpp) | Kev-4B | Kev-9B |
|---|---|---|---|
| median / p90 latency per phrase | 1.30 / 1.74 s | 0.43 / 0.86 s | 0.51 / 0.90 s |
| GPU memory, total on the card | ~19 GB | 17 GB loaded; the uncapped allocator then grew to ~30–32 GB | 22 GB loaded, 27.8 GB peak under the 0.82 cap |
| deterministic on 5 repeats | yes | yes | yes |
| licence | CC BY-NC 4.0 (research only) | Apache-2.0 | Apache-2.0 |

### Reading it: two different questions

**1. Can a decision model judge phrase-clean from this evidence?** No, not yet.
- Every 0-shot model sits at the base rate once calibrated. Kev-4B's 0.240 and
  Kev-9B's 0.242 are within noise of 0.242, and every pooled AUC interval
  includes 0.5.
- Kev-4B's within-mix AUC of 0.64 is the best seen. It rests on five mixes of
  16–20 phrases, so it is a lead, not a result.
- Putting the knowledge in context did not help, and for Kev-9B it hurt (AUC 0.42
  [0.32, 0.52]). The join evidence plus rubric moved the answers away from
  Jev's (r 0.19) without moving them towards the Director's marks.
- This agrees with ai-jam-sessions' reading: the evidence is the limit, not the
  model.

**2. Is Kev a good general local decision engine for sense-si?** On cost,
speed and licence, yes.
- It tracks hosted Jev more closely than OpenJev does (r 0.67 vs 0.61).
- It answers about 3 times faster per phrase, even on the slow reference kernels.
- It fits the 5090 at 4B and at 9B (9B under the memory cap).
- Its Apache-2.0 licence allows product use, which OpenJev's CC BY-NC does not.
- Kev reads "clean" far more often than Jev does (mean p 0.81–0.84 vs 0.28), so
  any threshold must be fitted on our own data.
- Kev-4B is the better buy here: the 9B adds memory and nothing measurable.

Nothing here rates Kev on the questions it was built for. Its own held-out
evaluation (0.82–0.89 on unseen sources) stands untested by us.

**Run notes:**
- Kev echoes the request's `model` field, so the receipts say `"model": "openjev"`; the runner and file name identify the model.
- Without the memory cap, Kev-4B's caching allocator held up to 31.9 GB. The VRAM watchdog logged two of the three over-ceiling samples that trigger a kill.
