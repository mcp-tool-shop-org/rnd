# Audit brief, round 1: NeMo Relay inside interlock, on local models (design v0)

You are auditing an experiment design, attached below in full. Attack it. Nothing has run, and nothing will until you raise nothing structural and the Director approves. The design is revised and sent back to you after each round.

## Context

- **interlock** is the studio's own Python harness. It measures local models (Ollama on an RTX 5090; OpenVINO on an Intel NPU and integrated GPU), writes JSONL receipts with strict validation, and builds a routing table that decides which device serves which task.
  - Its measurements are its product. Anything that perturbs them, or breaks its safety rules, is a defect.
  - The design's facts about both codebases are cited to files and lines. Read them as given, but say where a claim looks wrong.
- **NeMo Relay 0.10.1** is NVIDIA's tracing library, used here through its Python API only (no gateway).
- **No cloud or paid models** may appear anywhere.

## What to attack

1. **Confounds.**
   - Is the tracer really the only difference between the arms? Consider Relay's native dispatcher thread competing for CPU during measured calls, GC pressure, file writes on the same disk, and warm-up effects.
   - Do off–on–off triples on a warm model control for drift?
2. **Measurement.**
   - Is "within interlock's own noise band" the right bar for H2, or too loose to catch a real perturbation?
   - Is client-side added time the right overhead measure, when interlock's latency is server-reported?
3. **Completeness (H1).** Is matching against receipts and interlock's call counts a sound check? Does the worker-thread context copy for OpenVINO create a way for calls to be missed or misattributed?
4. **Safety (H3).** Is anything missing from the list of interlock rules a tracer could break? Is "no socket opened" testable as designed?
5. **Value (H4).**
   - Is comparing against a 10-line native counter a fair test of added value?
   - Is the pre-fix E5 search, whose answer is known, a valid case?
   - What would a trace genuinely add for a measurement harness?
6. **Power and size.** Is sizing the triples from the receipts' noise sound? Are 30 triples per device and call kind enough, or too many?
7. **Readable either way.** Could a result support both adopting and rejecting? Are the hypotheses falsifiable as written?
8. **Real use.** Does this design test Relay the way interlock would actually use it day to day?
9. **Cost and order.** Is stage 0, on fakes, the right gate before any device run?

## How to answer

- **Rank the findings:** structural (the design must change), important (it should change), minor.
- **For each:** the problem, a concrete way it misleads or wastes, and the fix.
- **End with a verdict:** "structural issues remain", or "no structural issues; ready for the Director".

## The design (v0)

# NeMo Relay inside interlock, on local models — design v0

**Status:** v0, for audit by Argon. Paper only: no GPU, no NPU, no installs, and nothing runs. The order is Argon audits, then the Director's approval, then tooling tests, then counted runs under the Publisher's grants. Template: [A/B experiments](https://mcp-tool-shop-org.github.io/rnd/handbook/ab-experiments/). Change log at the end.

**Scope:** local models only. No Claude in any arm. The subject is interlock (repository `mcp-tool-shop-org/interlock`, formerly switchyard), the studio's measurement and routing harness:
- Ollama on the RTX 5090 (127.0.0.1:11434 and the run-owned 11441);
- OpenVINO on the Intel NPU and the integrated GPU.

## What the two codebases allow (read on 2026-10-13, interlock main at 1b79b6f, Relay 0.10.1 docs and source)

**interlock's model calls:**
- **Ollama:** interlock uses only Ollama's native endpoints (`/api/generate`, `/api/show`, `/api/tags`, `/api/ps`, `/api/version`), never `/v1`, all non-streaming. There are three HTTP paths:
  - `OllamaAdapter.transport`, the main choke point, per adapter instance (`adapters/ollama.py` 204–303). It covers the measured call, the token counts, the unloads and the companion load.
  - e4b's `urllib_exchange` for its run-owned server (`harness/e4b.py` 2299).
  - The supervisor's GET-only health checks.
- **OpenVINO** runs in process. Every measured call goes through `_timed_call` (`adapters/openvino.py` 578), which runs the call in a worker thread with a hard timeout.

**Relay:**
- **No Ollama-native codec.** Its gateway handles only OpenAI-, Anthropic- and Gemini-style routes, so a gateway is the wrong tool for interlock.
- **A gateway on 11434 would also break the supervisor,** which requires exactly one listener there, and that listener must be the Ollama install.
- **The fit is the Python API:** `llm.call(...)` and `llm.call_end(...)` record a call by hand, with caller-supplied start and end times, device and settings in `data`/`metadata`, and token counts in `annotated_response.usage`. It needs no HTTP, so it works for OpenVINO too.
  - Export is asynchronous, through a native dispatcher thread, and `subscribers.flush()` is needed before reading.
  - Sanitizer guardrails can blank prompts and responses before they reach a file.
  - A conditional-execution guardrail can block a call before it runs.
  - Python 3.11 or later is required, so interlock's 3.12 pin is compatible.

**interlock's rules a tracer must respect:**
- **Receipt rows** allow extra keys only inside `settings`, `latency` and `artifacts`, or as free text in `notes`. A new top-level key fails the schema.
- **Receipts are refused for:**
  - home paths;
  - non-loopback hosts and URLs;
  - fully qualified domain names;
  - token prefixes;
  - a 32-character or longer hex or base64 value under a key named key, token, secret or password.
- **Placement of files:**
  - Any `*.json` under `receipts/` is checked as a receipt, except `*.run.json`.
  - The e4b and fill-card paths refuse a dirty tree, untracked files included.
  - So traces go under the git-ignored `logs/`.
- **The watcher records the top CPU users during each slot** (`top_after_call`). A tracer's thread or process appears there.
- **Timing:** Ollama latency is server-reported (`total_duration`), which hides any client-side cost, so overhead needs a client-side clock. interlock already has an off–on–off scheduler with a noise rule (`schedule_aba`, `aba_call`, `within_band` in `harness/timing.py`).
- **Dependencies:** exactly pinned, with a 90% coverage floor.

**An earlier consult** advised native call counters in interlock's receipts rather than Relay's library. This design tests whether Relay earns its place beside them, and doesn't assume it.

## The integration under test (built only after approval, in a branch, reviewed)

- **An optional `interlock[relay]` extra,** pinned, off by default, and switched on with `--trace`. With `--trace` off, interlock imports nothing from Relay.
- **Hooks:**
  - `OllamaAdapter.transport` and e4b's `urllib_exchange` wrap each call in `llm.call`/`llm.call_end`, with the endpoint, model, client-side times, and the token counts and durations Ollama returns.
  - `OpenvinoAdapter._timed_call` does the same, copying the trace context into its worker thread.
- **A run scope per interlock run,** named by run ID, with marks for the stop file, the grant and the NPU session, the watcher's stops, and unloads.
- **Output:** an ATOF file sink at `logs/<run_id>.atof.jsonl`, with OpenTelemetry off and `OTEL_*` variables refused at start. Sanitizers blank prompts and responses, and the hand-built `annotated_response` carries no prompt text.
- **Receipts:** each row gains `artifacts.trace = {"file": "logs/<run_id>.atof.jsonl", "span": <uuid>}`. That's a relative path and a bare ID, both allowed by the receipt rules.

## The check in three sentences

1. **The question:** can Relay trace interlock's local model calls (Ollama on the 5090, and OpenVINO on the NPU and integrated GPU) completely and safely, without changing what interlock measures? And does its trace add anything that interlock's receipts and native counters don't already give?
2. **What each arm gets:** the same interlock run (same spec, device, model, grant and seed), with `--trace` off in arm A and on in arm B. Arms alternate off–on–off on the same warm model, through interlock's own `schedule_aba`.
3. **Why that answers it:** the tracer is the only difference between the arms. So any change in measured latency, throughput, CPU readings or receipt validity is the tracer's. Completeness and safety are checked on arm B's own files, against the receipt rows of the same run.

## Hypotheses, and how each fails

- **H1, complete capture:** every model call interlock makes in a traced run appears in the trace exactly once, with token counts and durations equal to the receipt's. That covers measured calls, counts, unloads, companions and e4b calls.
  - Fails on any missing, duplicated or mismatched call. It's checked by matching against the receipt rows and interlock's own call counts.
- **H2, no change to what interlock measures:** every receipt metric of arm B is within interlock's own noise band (`within_band`) of the arm-A neighbours on either side. The metrics are latency, prefill and decode rates, the TTFT proxy, VRAM and the CPU readings.
  - Fails if any metric leaves the band on any device.
  - The client-side added time per call is reported, with its interval.
- **H3, safe with interlock's rules:** every rule still holds, or the integration fails.
  - Receipts pass `interlock check`.
  - The e4b and fill-card runs start with no dirty-tree refusal.
  - The stop file still stops a run cleanly.
  - Grant and NPU-session recording is unchanged.
  - The supervisor's listener check passes, because no port is opened.
  - The trace holds no home path, host, URL, token or prompt text, checked by interlock's own receipt refusal rules run over the trace.
  - Nothing leaves the rig.
- **H4, added value:** on runs with known waste, the trace shows something the receipts and a native counter don't.
  - **The known waste:** the pre-fix E5 prefix-fit search (thousands of count calls), re-run on fakes; a companion load; an unload; a retried count after a timeout.
  - **What counts:** the trace places each call in order, across threads, with its time, in a way the receipt rows don't.
  - Fails if a native per-run call counter with per-kind timing (about 10 lines in the receipt) recovers the same facts.

## Stages

**Stage 0, on fakes, no device and no GPU** (interlock's test fakes; this is code review and testing, not a run):
- unit tests for the hooks;
- call-count matching for H1 on fakes, including the pre-fix E5 search for H4;
- receipt validity and dirty-tree checks for H3;
- a test that `--trace` off imports nothing from Relay;
- a test that no socket is opened.

**Stage 1, Ollama on the 5090** (the Publisher's grant, outside measurement windows):
- one model, the E4-style short-decode spec;
- off–on–off triples on the warm model;
- one fill-card run for the long-prompt path;
- one run that exercises the stop file.

**Stage 2, OpenVINO on the NPU and the integrated GPU** (an NPU session):
- one LLM and one embedder per device, in off–on–off triples;
- the worker-thread context copy checked.

## Sample size, from measured noise

- **Per-call noise is interlock's own,** from its repeat-slot spreads in committed receipts. The decode rate is the tightest, and the cold load is the noisiest.
- **Before stage 1,** the spread of the chosen metrics is computed from existing receipts for the same model and device. That sizes the triples so that a shift of half the noise band would be detected at 80% power.
- **Expected size:** about 30 off–on–off triples per device per call kind. The exact figure is set from the receipts, and recorded here by amendment, before any counted run.
- **H1 and H3** are exact checks over every call. They need no sampling.

## Decision rule (pre-registered)

- **Adopt as an optional tracer for debugging runs** (`--trace`, off by default) if H1 and H3 hold on every device.
- **Allow `--trace` on counted measurement runs** only if H2 also holds on every device. Otherwise, receipts record that tracing was on, and such runs don't enter the routing table.
- **Keep it in interlock only if H4 holds.** If it doesn't, the native counters suffice, the extra is removed, and the result is filed.
- **Reject** on any failure of H3 (a rule broken, a port opened, anything leaving the rig, any prompt text or path in a trace) or of H1.

## Cost

- **Plan and API:** none.
- **GPU:** about 30 to 60 minutes of 5090 time in total, outside measurement windows.
- **NPU and integrated GPU:** about 30 minutes in one NPU session.
- **Code:** about 100 to 150 lines plus tests in interlock, as an optional extra, reviewed before any device run. The 90% coverage floor holds.

## Not covered

- The routing table taking Relay data directly. Its importer reads only pinned receipts, so any trace data would enter through receipt fields.
- A gateway in front of Ollama: ruled out above.
- Agents.

## Change log

- **v0, 2026-10-13:** first draft, from both codebases, for Argon's audit, round 1.

