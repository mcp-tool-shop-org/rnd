# Audit brief, round 2: NeMo Relay inside interlock, on local models (design v1)

You audited v0 in round 1 and found six structural issues and six others. v1 is attached below, with a change-log table saying how each finding was handled. Audit it again, as hard as before.

## What to do

1. **Check each round-1 finding against v1:** resolved, partly resolved or unresolved, with one line of evidence.
2. **Find any new problems v1 introduced.** For example: does the 2-second rest and flush barrier itself distort the slots? Is equivalence by two one-sided tests at half the band sound, or too strict or too loose? Is the H4 blind-reader test fair to both sides? Is the process-level import check designed correctly?
3. **Re-check anything else structural:** confounds, power, real use, results that could be read either way, cost, and order.

## How to answer

- **Rank the findings:** structural, important, minor.
- **For each:** the problem, how it misleads or wastes, and the fix.
- **End with a verdict:** "structural issues remain", or "no structural issues; ready for the Director".

## The design (v1)

# NeMo Relay inside interlock, on local models — design v1

**Status:** v1, for audit by Argon (round 2). Paper only: no GPU, no NPU, no installs, and nothing runs. The order is Argon audits until nothing structural remains, then the Director's approval, then stage 0 (code and tests on fakes), then device runs under the Publisher's grants. Template: [A/B experiments](https://mcp-tool-shop-org.github.io/rnd/handbook/ab-experiments/). Change log at the end, with a table of how each round-1 finding was handled.

**Scope:** local models only. No Claude in any arm. The subject is interlock (repository `mcp-tool-shop-org/interlock`, formerly switchyard), the studio's measurement and routing harness:
- Ollama on the RTX 5090 (127.0.0.1:11434, and the run-owned 11441 in e4b);
- OpenVINO on the Intel NPU and the integrated GPU.

## What the two codebases allow (read on 2026-10-13, interlock main at 1b79b6f, Relay 0.10.1)

**interlock's model calls:**
- **Ollama:** only native endpoints (`/api/generate`, `/api/show`, `/api/tags`, `/api/ps`, `/api/version`), never `/v1`, all non-streaming. Three HTTP paths:
  1. `OllamaAdapter.transport` (`adapters/ollama.py` 204–303), per adapter instance. It carries the measured generate, the token counts (`/api/generate` with `num_predict` 1), the unloads (an empty prompt with `keep_alive` 0) and the companion load.
  2. e4b's `urllib_exchange` for its run-owned server (`harness/e4b.py` 2299).
  3. The supervisor's GET-only health checks (`ollama_supervisor.py` 918).
- **OpenVINO** runs in process. Measured calls go through `_timed_call` (`adapters/openvino.py` 578), which runs the call in a daemon worker thread with a hard timeout.

**interlock's timing:**
- `schedule_aba` (`harness/timing.py` 94) builds one in-process slot list: cold slots, then rounds of alone-before, paired, alone-after.
- `aba_call` (136) compares the paired slot's median with the mean of its neighbours' medians, by a relative band. A result is inconclusive when the neighbours' own spread exceeds half the band.
- Ollama latency is server-reported (`total_duration`).

**Relay:**
- **No Ollama-native codec.** The gateway handles only OpenAI-, Anthropic- and Gemini-style routes. A gateway on 11434 would also break the supervisor's single-listener check, so only the Python API is used.
- **The calls:** `llm.call`/`llm.call_end` take caller-supplied timestamps, `data`/`metadata`, and token usage in `annotated_response`.
- **Export:** asynchronous, through a native dispatcher. `subscribers.flush()` drains it.
- **Guardrails:** sanitizers can blank request and response payloads.
- **Packaging:** Relay requires Python 3.11 or later, and interlock pins 3.12. Its PyPI metadata lists no dependencies for the base package, only for optional extras (the CLI binary, LangChain, LangGraph, Deep Agents). The base install adds nothing that could collide with interlock's pins. The package ships a native extension.

**interlock's rules a tracer must respect:**
- Receipt rows allow extra keys only inside `settings`, `latency` and `artifacts`, or in `notes`.
- The refusal rules cover home paths, non-loopback hosts and URLs, FQDNs, token prefixes, and long hex or base64 values under secret-named keys.
- Any `*.json` under `receipts/` except `*.run.json` is checked as a receipt.
- The e4b and fill-card paths refuse a dirty tree, so traces go under the git-ignored `logs/`.
- The watcher records the top other CPU users per slot (`top_after_call`).
- Dependencies are exactly pinned, with a 90% coverage floor.

## The integration under test (built only after approval, in a branch, reviewed)

- **An optional `interlock[relay]` extra,** pinned to `nemo-relay==0.10.1`, and switched on with `--trace`. With `--trace` off, no module imports Relay.
- **Hooks, all on the calling thread:**
  - `OllamaAdapter.transport` and e4b's `urllib_exchange`: `llm.call` before the request and `llm.call_end` in a `finally`. It records the endpoint, model, client-side start and end (`perf_counter` mapped to UTC), Ollama's returned durations and counts, and a status (`ok`, `http_error`, `timeout`, `exception`).
  - `OpenvinoAdapter._timed_call`: `llm.call` before the worker thread starts, and `llm.call_end` in the calling thread's `finally` once the join returns or times out.
    - A timed-out call is closed as `status: timeout`, with its duration up to the cutoff, and marked `worker_still_running: true`.
    - No Relay call is made inside the worker thread, so no context needs copying.
  - Supervisor health checks are not traced, by definition (see H1).
- **A run scope per interlock run,** opened in a `try`/`finally` around the run.
  - Its exit calls `subscribers.flush()` on every path, including the stop file, `KeyboardInterrupt`, refusals and exceptions.
  - It holds marks for the stop file, the grant, the NPU session, watcher stops and unloads.
- **Output:** an ATOF file sink at `logs/<run_id>.atof.jsonl`, in overwrite mode.
  - OpenTelemetry is off, and the run refuses to start if any `OTEL_*` variable is set.
  - Request and response sanitizers replace every prompt, response and message body with its byte length.
  - Sanitizers for mark and scope events strip any host name, user, environment or path fields. The exact field list is fixed in stage 0 by reading a real ATOF line.
- **Receipts:** each row gains `artifacts.trace = {"file": "logs/<run_id>.atof.jsonl", "span": "<uuid>"}`.
- **The native counter (the baseline for H4, frozen now):** every row gains `artifacts.call_counts`, keyed by call kind (`generate`, `count`, `show`, `tags`, `ps`, `unload`, `companion`), each holding `{"n": int, "ms": float, "errors": int, "timeouts": int}`.
  - These are aggregate counts and cumulative client-side time per kind per row. They're built in the same hook points, whether or not `--trace` is on. That's O(1) space in the receipt.
  - It deliberately holds no event log. Relay's trace is the ordered event log, at O(N), in `logs/`.
- **Retention:** trace files stay in `logs/` until the run's receipts are audited. A spec's expected trace size is estimated at about 1 KB per call and printed at start. Stage 0 measures the real figure. `interlock runs` gains no deletion: removal is by hand, after audit.

## The check in three sentences

1. **The question:** can Relay trace interlock's local model calls (Ollama on the 5090, OpenVINO on the NPU and integrated GPU) completely and safely, without changing what interlock measures or adding meaningful client-side time? And does its ordered trace show diagnostic facts that interlock's aggregate per-kind call counter doesn't?
2. **What each arm gets:** the same interlock process, spec, device, model, grant and seed. Relay is imported in both arms. Arm B has the hooks' trace emission and the file sink on, and arm A has them off.
   - Arms alternate off–on–off through `schedule_aba`.
   - After every slot, in both arms: `subscribers.flush()`, the sink quiesced, `gc.collect()`, and a fixed 2-second rest.
   - A separate process-level check measures what merely importing Relay costs.
3. **Why that answers it:**
   - Within a process, emission is the only difference between the arms, and the barrier keeps one arm's queued work out of the next slot.
   - Across processes, import alone is the only difference.
   - Completeness and safety are checked against an independent count and planted canaries, not against the hooks themselves.

## Hypotheses, and how each fails

- **H1, complete capture.** Every model call that goes through hook points 1 and 2 (Ollama) or `_timed_call` (OpenVINO) appears in the trace exactly once, with the right kind, status and duration. Model calls are `/api/generate`, `/api/show`, `/api/tags` and `/api/ps` through those paths, plus OpenVINO generate and embed. Supervisor health checks are excluded.
  - **The independent ground truth:**
    - for e4b on 11441, the run-owned server's own log, request by request;
    - for the fakes, the fake server's own request log;
    - for 11434, a counter in a stdlib `http.client` wrapper below `transport`, installed only for the test;
    - for OpenVINO, the fake pipeline's call log in stage 0, and a counter around `pipe.generate` and `_infer_embed` in stage 2.
  - **Fails on:** any missing, duplicated or mis-kinded call; a duration outside its ground-truth interval; or an unclosed span, including on timeout and on the stop file.
- **H2, no change to what interlock measures.**
  - **Primary gate:** for each device, call kind and receipt metric (latency, prefill rate, decode rate, the TTFT proxy, VRAM, process CPU), the per-triple difference Δᵢ = Bᵢ − (A₁ᵢ + A₂ᵢ)/2. The 90% interval of the mean Δ must lie within ±δ, where δ is half of that metric's historical relative noise band (equivalence by two one-sided tests).
  - **Tail gate:** the 95th percentile of |Δᵢ| is no more than one noise band, and B's single-slot band excursions are no more frequent than in historical A–A–A triples from committed receipts.
  - **Client-side time, a hard gate:** the median added client time per call (B's hook-to-hook time minus A's, by triple) is under 0.5 ms, and its 99th percentile under 2 ms. Ollama's server-reported duration can't show this cost, so it's gated separately.
  - **CPU and the watcher:**
    - interlock's process CPU per slot passes the primary and tail gates;
    - no new process is spawned;
    - a Relay thread in the process is allowed;
    - any other process in `top_after_call` that differs between arms fails.
  - **The process-level import check:** interlock A-only runs in a process that never imports Relay, against one that imports it and leaves it idle. Same gates.
- **H3, safe with interlock's rules.** All of these must hold, or the integration fails.
  - Receipts pass `interlock check`.
  - The e4b and fill-card runs start with no dirty-tree refusal.
  - The stop file stops a run cleanly, and every line of the trace parses as JSON afterwards, with every call completed before the stop present and closed.
  - Grant and NPU-session recording is unchanged.
  - No listening port is opened by the Python process, and no non-loopback connection is made. In stage 0 this is a socket guard that blocks every `AF_INET`/`AF_INET6` `bind` and `connect` except to the fake's own loopback port. In stages 1 and 2 it's a listener and connection read for the process, plus the supervisor's own listener check.
  - **A canary:** a unique string (`AMU_CANARY_PROMPT_7c1e`) is planted in prompts and in fake responses, and occurs zero times in the trace.
  - **No home path, host name, user name or environment value** is in the trace, checked by interlock's own path, host and token rules and by searching for the machine's host and user names.
  - Nothing leaves the rig.
- **H4, added value over the native counter (decided on fakes, before any device run).**
  - **Planted cases:**
    - the pre-fix E5 prefix-fit search;
    - a companion load overlapping the measured call;
    - an unload followed by an unexpected reload;
    - a count that times out and is retried;
    - an OpenVINO timeout whose worker keeps running.
  - **For each case,** before the run, a question is written whose answer is the diagnostic fact. For example: "which call kind dominated the run's time, and did it grow per step?"; "did the reload follow the unload within the same slot?"
  - **The scoring:** the questions are put to two blind readers, a script and a fresh session, given only the receipt with `artifacts.call_counts`, or only the trimmed trace.
  - **Holds if** the trace answers correctly at least 3 of 5 that the counter can't.
  - **Fails if** the counter answers everything the trace does.

## Stages

**Stage 0, code and tests on interlock's fakes (no device, no GPU):**
- The hooks, the native counter, the run scope with a flush on every exit path, the sanitizers, the canary, and the socket guard.
- H1 against the fakes' request logs.
- H3, including the stop file and a clean JSON parse.
- **H4, decided here.**
- Two test environments, the base pins and the base plus `[relay]`, each holding coverage at or above 90%. The Relay wrapper is covered by tests that run with Relay installed, and a stub covers the import-off path.

If H1, H3 or H4 fails, stop here and reject, with no device run.

**Stage 1, Ollama on the 5090** (the Publisher's grant, outside measurement windows):
- E4-style short decode, in off–on–off triples on the warm model.
- At least 5 triples of the long-prompt (fill-card-sized) path, for heavy prefill.
- At least one explicit unload-and-load cycle, and one companion load, inside traced and untraced slots.
- One stop-file run.
- The process-level import check.

**Stage 2, OpenVINO on the NPU and the integrated GPU** (an NPU session):
- One LLM and one embedder per device, in off–on–off triples.
- One forced timeout per device.
- The process-level import check.

## Sample size, from measured noise

- **Before stage 1,** each metric's relative spread is computed from committed receipts for the same model and device. The number of triples is set so that the two one-sided tests at δ (half the band) have 80% power when the true shift is zero.
- **The working estimate** is 30 triples per device per call kind. The exact figure is recorded by amendment before any counted run.
- **H1 and H3** are exact checks over every call. They need no sampling.

## Decision rule (pre-registered, as a tree)

1. If **H1, H3 or H4 fails:** reject, remove the integration, and keep the native counter (it's justified on its own).
2. Otherwise, if **H2 fails** on any device: adopt `--trace` for debugging runs only. Traced runs are marked in their receipts and never enter the routing table.
3. Otherwise (all four hold): adopt `--trace` for all runs, counted ones included.

## Cost

- **Plan and API:** none.
- **GPU:** about 60 to 90 minutes of 5090 time, outside measurement windows.
- **NPU and integrated GPU:** about 45 minutes in one NPU session.
- **Code:** about 150 to 200 lines plus tests, including the native counter.
- Stages 1 and 2 run only if stage 0 passes.

## Not covered

- The routing table taking Relay data directly. Its importer reads only pinned receipts.
- A gateway in front of Ollama: ruled out above.
- Agents.

## Change log

- **v0, 2026-10-13:** first draft.
- **v1, 2026-10-13:** revised after Argon's round 1 (structural issues remained). How each finding was handled:

| # | Round-1 finding | v1 change |
|---|---|---|
| 1 | The async dispatcher bleeds across ABA slots, and the import state persists | Relay is imported in both arms. Every slot in both arms ends with a flush, quiescing the sink, `gc.collect()` and a 2-second rest. A separate process-level import check |
| 2 | "Every metric within band" conflicts with the power claim | H2 is now an equivalence test by two one-sided tests at δ = half the band, plus a tail gate measured against historical A–A–A triples. (Note: `aba_call` already compares medians, not single calls, but the equivalence test is adopted) |
| 3 | Server-reported duration can't show client overhead | Client-side added time is a hard gate: median under 0.5 ms, 99th percentile under 2 ms |
| 4 | Circular ground truth; OpenVINO timeout spans | Independent ground truth per path (server logs, a fake's request log, a counter below `transport`). Spans open and close on the calling thread, and timeouts close as `status: timeout` |
| 5 | Contradictory decision rule; H4's baseline undefined | The native counter's schema is frozen (aggregate per kind). H4 is decided in stage 0 and gates stages 1 and 2. The decision rule is a strict tree |
| 6 | The watcher's readings are ambiguous; the trace safety scan is inadequate | Exact CPU and process criteria. A canary prompt and response. Host, user and environment fields are stripped, and searched for |
| 7 | H1's endpoints are ambiguous | Model calls are enumerated. Supervisor health checks are excluded |
| 8 | Stage 1 misses prefill, unloads and companions | 5 or more long-prompt triples, an unload-and-load cycle and a companion load in stage 1 |
| 9 | Dependency pins and coverage | Relay's base package has no declared dependencies (PyPI metadata). Two test environments, each held at 90% |
| 10 | A stop-file abort could truncate the trace | A flush on every exit path, and a clean JSON parse asserted after a stop |
| 11 | The socket check's design | Block `AF_INET`/`AF_INET6` `bind` and `connect` except the fake's loopback port, plus process listener and connection reads on device |
| 12 | Trace growth in `logs/` | Size estimated at start and measured in stage 0. Removal by hand after audit |
