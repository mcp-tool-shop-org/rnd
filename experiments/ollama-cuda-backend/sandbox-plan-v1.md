# Sandbox test: the 0.40.4 CUDA 13.4 backend on 11500 (plan; needs a GPU grant)

**Goal:** show that the new `ggml-cuda.dll` (sha256 `ab9bef88…2cb2c`, BUILD.md) loads on the RTX 5090 under Ollama 0.40.4, gives the stock build's answers, and is no slower. Nothing is activated. The installed Ollama is untouched.

## The sandbox tree (built before the grant; no GPU)

`E:\AI\ollama-cu134-0404\run\`:
- `ollama.exe`, copied from `%LOCALAPPDATA%\Programs\Ollama\ollama.exe` (27 MB);
- `lib\ollama\`, a copy of the installed `lib\ollama` top-level files only (43 files, 41 MB: `llama-server.exe`, `ggml.dll`, `ggml-base.dll`, the `ggml-cpu-*.dll`, `libllama*.dll`, `libomp.dll` and so on). `cuda_v12`, `rocm_v7_1` and `vulkan` are left out;
- `lib\ollama\cuda_v13\`, copied from `E:\AI\ollama-cu134-0404\lib\ollama\cuda_v13` (the new build, 13 DLLs).

These are copies, not links (C: and E: are different volumes). The copied files are hashed against the installed ones before the grant.

0.40.4 resolves `LibOllamaPath` to `<exe dir>\lib\ollama` first on Windows (`ml/path.go`), so the sandbox exe uses its own tree.

**Runner path:** `E:\AI\ollama-cu134-0404\run\lib\ollama\llama-server.exe`. **It is not on the VRAM watchdog's guard list**, which names the installed `…\Ollama\lib\ollama\llama-server.exe`. The Publisher adds it for the grant window, or the test doesn't run.

## The environment

The sandbox server only (11434 is not touched):

    OLLAMA_HOST=127.0.0.1:11500
    OLLAMA_LLM_LIBRARY=cuda_v13
    OLLAMA_MODELS=E:\AI-Models\Ollama     (read-only use: no pull, create, copy or delete is sent)
    OLLAMA_NOPRUNE=1                      (0.40.4 prunes unused blobs at startup otherwise; this store is shared)
    OLLAMA_KEEP_ALIVE=30s
    OLLAMA_DEBUG=1                        (the log names the backend path it loads)

It's started as `run\ollama.exe serve`, logging to `E:\AI\ollama-cu134-0404\sandbox-11500.log`. It runs at normal priority with no affinity, as stock does, so tokens/s compare fairly. The work is on the GPU, and its CPU use is light.

## The model, options and prompts

- **Model:** `qwen3:8b`, already in the store. **Options:** `think: false`, `num_ctx: 2048`, `num_predict: 128`, `temperature: 0`, `top_k: 1`, `seed: 42`, `keep_alive: "30s"`.
- **Prompts:** three fixed prompts, written into the run script before the grant:
  1. "Explain in three sentences why the sky is blue."
  2. "Write a Python function that returns the n-th Fibonacci number iteratively."
  3. "List five uses of a hammer, one per line."

## Order: one server and one model at a time

| Step | Server | What |
|---|---|---|
| 1 | stock 11434 (already running, CUDA library currently stock) | Check `/api/ps` is empty on both servers. Run the 3 prompts (**stock A**). Unload with `keep_alive: 0`. Check `/api/ps` is empty. |
| 2 | stock 11434 | Run the 3 prompts again (**stock B**), which shows whether stock is itself repeatable. Unload and check empty. |
| 3 | sandbox 11500 | Start the server. Run the 3 prompts (**sandbox**). Unload and check empty. Stop the 11500 server. |

The two servers never have a model loaded at the same time: each step checks the other server's `/api/ps` is empty before it loads.

## Pass criteria, fixed now

1. **The new DLL loads.** The sandbox log names `E:\AI\ollama-cu134-0404\run\lib\ollama\cuda_v13`, with library CUDA and compute capability 12.0. The log may not print the CUDA runtime version. If it doesn't, the proof is the path plus the sha256 of the DLL at that path, read after the run (`ab9bef88…`).
2. **The outputs match.** Greedy decoding with a fixed seed.
   - **Pass:** the sandbox output equals stock A's, token for token, on all 3 prompts.
   - **The tolerance**, used only if exact equality fails: the CUDA 13.4 build compiles sm_120a SASS, and stock JITs PTX from CUDA 13.0, so floating-point order can differ. It passes if, on every prompt, the first divergence from stock A comes at token 32 or later, and the output stays on the same task.
   - If stock A and stock B differ, the sandbox is held to the same standard stock meets against itself.
   - The divergence index is reported either way.
3. **No slower.** Tokens/s (`eval_count / eval_duration`) on each prompt. It passes if the sandbox is at least 0.95× stock A, averaged over the 3. Load time and prompt-eval rate are reported too.
4. **Cleanup:**
   - `/api/ps` is empty on both servers;
   - the 11500 server is stopped;
   - no `llama-server.exe` from the sandbox path is left running;
   - `memory.used` is back to baseline (±200 MiB).

## VRAM and time

- **Baseline now:** `memory.used` 1,672 MiB, read 2026-10-15.
- **Expected peak:** about 6.9 GB total `memory.used`. That's 5.2 GB for qwen3:8b at num_ctx 2048 with think false (the Publisher's stock smoke) on top of the baseline. One model is loaded at a time, so the peak is a single model.
- **The cap for the grant:** 9,216 MiB total `memory.used`, baseline included. The headroom allows for the new build's different kernels and workspace. `nvidia-smi` is sampled every 1 s through the whole test, and loads stop if it passes the cap.
- **Expected wall time** (inferred): 2–4 min. That's 3 model loads of about 5–15 s each, 9 generations of 128 tokens, and the sandbox start and stop. The tree copy is under 70 MB and happens before the grant.

## After

The measured peak, the outputs' comparison, tokens/s and the log lines go to the Publisher. Activation (the swap in `lib\ollama` with Ollama stopped, and the start script's expected hash moved to `ab9bef88f8bf016b`) is a separate go.
