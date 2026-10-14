# Stage 1 result note: relay-s1-20261014b

Written 2026-10-14. **The Director's call, the same day: debug-only tracing, as design amendment v3.2.** The verdict below stands. The conditions are listed at the end.

## The frozen verdict, unchanged

`analyze.py` is byte-identical to its freeze at rnd `cbaed82`, and it was run as written:
`python experiments/interlock-relay/stage1/analyze.py <interlock root> relay-s1-20261014b`.
The full output is `results/relay-s1-20261014b.analysis.json`.

**stage1_holds = false.** Design v3.1's decision rule:
- H1 failing means reject.
- H2's client-time miss means no tracing on counted runs.

### H1: tracing accounts for every request. Fails.

| step | sent | counted | spans | requests counted once | spans = the traced slots' calls | every span closed |
|---|---:|---:|---:|---|---|---|
| decode | 204 | 203 | 68 | **false** | true | true |
| long | 217 | 216 | 66 | **false** | true | true |
| unload | 24 | 23 | 8 | **false** | true | true |
| companion | 63 | 62 | 11 | **false** | **false** | true |

### H2: tracing doesn't change interlock's measurements. Decode and long fail.

| pair | decode tok/s | latency | prompt tok/s | system CPU | client time (median / p99, gate <0.5 / <2 ms) |
|---|---|---|---|---|---|
| decode | holds | holds | holds | holds | **fails**: 0.548 / 0.650 ms |
| long | holds | holds | holds | **inconclusive** (secondary) | **fails**: 0.682 / 0.781 ms |

VRAM was not measured.

### Import check (15 triples): fails

- prompt_tok_s fails its tail: 4 B excursions against 3 allowed. Its mean and interval hold.
- decode_tok_s and latency_ms hold.
- The barrier is reported, not gated. Both gaps are under the band.

### H3: no canary, home path, host or user name in any trace. Holds.

H3 holds in every step, and the stop step stopped mid-run. The receipts check holds.

### The run

- **Steps:** all six exited as expected. The stop step exited 77, its stop-file exit.
- **VRAM peak:** 18,909 MiB, in the companion step.
- **Wall time:** 16 min 55 s.
- **Code and grant:** interlock `a43cc31`, under grant `publisher-5090-relay-s1-2026-10-14`.
- **Refused attempt:** the first attempt, `relay-s1-20261014`, was refused before any model loaded. The README's preflight corrections explain why.

## Diagnosis

Read-only, from the run's own records:
- `logs/<run>.http.json`, `.calls.json` and `.atof.jsonl`;
- `receipts/<run>.jsonl`;
- the interlock source at `a43cc31`.

Item 3 adds a bench, CPU-only, against a stub transport. It made no device or network call. Nothing here re-scores the verdict.

### 1. The H1 off-by-one: a harness artifact

The one request is the runner's **empty-card guard**, a `GET /api/ps` sent before the tracer is attached.

- Every step's HTTP counter shows exactly one `/api/ps`. No step's call table has a `ps` entry.
- The runner reads the card through the adapter's own `loaded_models()`. That is `_card_guards(probe, …)` at `runner.py` ~2296, before `Tracer(...)` and `instrument(adapters, tracer)`.
- The driver's counter counts every request sent from the adapter's file for the whole child process. The tracer counts only what passes through the wrapped transport. So the guard's request is in "sent" and can't be in "counted".
- With that one request set aside, each path matches the call table exactly:

| step | /api/generate sent | table: generate + unload + count + companion | /api/show sent | table: show | other |
|---|---:|---:|---:|---:|---|
| decode | 102 | 101 + 1 | 101 | 101 | |
| long | 117 | 98 + 3 + 16 | 98 | 98 | /api/tags 1 = tags 1 |
| unload | 12 | 4 + 7 + 1 | 11 | 11 | |
| companion | 35 | 21 + 8 + 6 | 27 | 27 | |

**No traced call was missed.** The two counters cover different windows. The analysis's equality check couldn't see that, and the stage 0 runs never ran the card guard, because it fires only for a 5090 spec.

### 2. Companion, spans ≠ the traced slots' calls: a harness artifact

There are three extra spans: call ids 13, 31 and 49, all `unload`, each carrying **no arm and no slot**. Each comes just after a traced `with-companion-on` slot. Call 13 follows calls 11 and 12, in slot `repeat:0:paired:companion-traced`.

The runner's order in the slot's `finally` (`runner.py` ~1044 and ~1100–1114) is:
1. `tracer.end_slot()` takes the slot's call ids;
2. the companion's `stop` session (`stop_session` → `unload`) runs;
3. then `tracer.set_emitting(False)`.

So the companion's unload starts after the slot has closed, while emission is still on. It is traced and counted (under `_run`), but belongs to no slot. That gives three traced companion slots and three stray spans. The tracer did what it was told; the order of the runner's `finally` is wrong for a companion arm.

### 3. Client time: real

The gate compares hook time per slot, traced against untraced. Each slot holds two calls, a `show` and a `generate`. From the receipts:

| pair | traced: median per slot | untraced: median per slot | traced extra per call |
|---|---:|---:|---:|
| decode | 614 µs | 71 µs | ≈ 270 µs |
| long | 761 µs | 75 µs | ≈ 343 µs |

Against a stub transport on this CPU, run quiet and warm in a tight loop (`hookbench.py`, beside this note):

| call | body | untraced hook | traced hook (Relay) | of which `json.dumps` for the size |
|---|---:|---:|---:|---:|
| show | 21 B | 1.9 µs | 31.0 µs | 0.6 µs |
| decode generate | 240 B | 2.1 µs | 32.2 µs | 1.1 µs |
| long generate | 148 KB | 2.2 µs | 138.1 µs | 104.4 µs |

What the evidence shows:
- **The cost is real Relay work, not bookkeeping.** In a profile, the traced path's time is Relay's native `llm.call` and `llm.call_end`, the sanitizer wrappers, and the one `json.dumps` interlock does to give Relay a request size. The lock and the slot accounting are a few microseconds.
- **The long pair's extra time is the request-size serialisation.** Long minus decode is about 147 µs per slot live, and about 106 µs per generate on the bench. That is the `json.dumps` of a 148 KB prompt that only Relay's request record uses.
- **The live hook is about 9–17× the warm bench,** both untraced (35 against 2 µs per call) and traced (≈270 against 30 µs).
  - **Shown on the CPU alone, after Argon's suggestion** (`coldbench.py`, beside this note). The bench puts the stage's barrier (trace flush, `gc.collect()`, a 250 ms rest) before each two-call slot, and the stub transport blocks the way the live server does (show 2 ms, generate 300 ms). Three of the four hook entries then run on a thread waking from a sleep or a blocking read.

    | pair | warm: untraced / traced, per slot | cold: untraced / traced, per slot | cold traced − untraced | live |
    |---|---|---|---:|---|
    | decode | 4.1 / 68.4 µs | 101.0 / 611.8 µs | 510.8 µs | 71 / 614 µs per slot; client-time median 548 µs |
    | long | 6.5 / 246.8 µs | 104.7 / 696.7 µs | 592.0 µs | 75 / 761 µs per slot; client-time median 682 µs |

  - The cold bench lands within about 10% of the live traced figures, with no device. The live miss is the same Relay work, run on a waking core.
- **Removing the dumps alone would not pass the gate.** Decode is 0.548 ms with a negligible dumps cost. Relay's own per-call cost on this rig is what misses 0.5 ms per two-call slot.

### 4. The import check's prompt_tok_s tail: note only

There were 4 B excursions against 3 allowed, over 15 triples. The mean and interval hold, and decode tok/s and latency hold.

Checked read-only after Argon's question:
- **Position:** the excursions are triples 4, 6, 9 and 11. None is triple 0, right after process start.
- **Sign:** three are positive, meaning the import process was *faster* (+0.045, +0.043, +0.040), and one is negative (−0.043).
- **Size:** each is just over the band of 0.039, which comes from 15 A–A pairs.

That is not a one-sided slowdown from importing Relay. **Noise at n = 15.**

## What a stage 1 rerun would need

None of this is started. Each step needs its own approval.

1. **A dated amendment to the design and the frozen analysis**, re-frozen before any run. For example:
   - **H1:** attach the tracer before the card guard, so the guard's `/api/ps` is traced and counted. Or start the HTTP counter at `instrument()`. Either way, the decision has to be explicit; the analysis must not be quietly loosened.
   - **Companion:** end the slot after the companion's stop, or switch emission off before it. The amendment says which slot the stop belongs to.
   - **Client time:** the 0.5 ms gate stays. Size the request without serialising the body, for example from the transport's own byte count. That removes the size-dependent part, but item 3 shows it isn't enough on its own. The amendment has to say whether Relay's per-call cost can pass at all, or whether H2's answer is simply "no tracing on counted runs".
2. **An Argon review** of the amendment and the code.
3. **Mike's go, then a Publisher grant**, under the same ready-check protocol.

## Argon's consult (Gemini, pasted by Mike, 2026-10-14) and R&D's disposition

Argon's verdict is **(b): stop at "debug only".** Fix the two H1 harness defects and the sizing, verify H1 in a deterministic test, and adopt `--trace` for debugging runs only. Traced runs are marked in their receipts and kept out of the routing table.

**Kept:**
- **Both artifact diagnoses hold.** Argon checked the per-endpoint accounting: a real missed call could not hide behind the guard's `/api/ps`.
- **H1 (a):** instrument before the card guard, and keep the driver's counter process-wide. That is the strongest invariant: every request the adapter sends must be in `calls.json`. Not a marker-sliced counter.
- **The companion:** stop the companion before `end_slot()`, in both arms alike. Make `end_slot()` the one place that ends slot-scoped emission, so no later teardown call can leave an orphan span.
  - R&D's caveat: only when tracing is per arm. With run-wide tracing, calls between slots are meant to be traced into `_run`.
- **The verdict for `relay-s1-20261014b` stays `stage1_holds = false`** as frozen. Fixing a harness boundary is a new pre-registration, not a re-score.
- **The cold-wake explanation.** Shown since then, on CPU alone (item 3).
- **Deferring or batching Relay's calls off the calling thread is invalid.** Relay timestamps inside `call` and `call_end`, so deferral would test a queue, not Relay.
- **Sizing from the transport's byte count instead of `json.dumps`.** It's cheap, and it removes about 100+ µs per long call when debugging.
- **The import tail is noise.** Checked (item 4).
- **No 5090 rerun for full adoption.**
  - The cold bench puts decode at about 511 µs with nothing size-dependent to remove.
  - In the warm profile, Relay's native `call` and `call_end` are about 50 of the 64 µs per slot. Trimming all of interlock's own wrapper work would leave roughly 400 µs cold, by estimate. That is above Argon's 0.35 ms margin for option (a).
  - A rerun would re-measure the same miss.

**Not taken as stated:**
- **Argon's (b) adopts debug tracing even though the frozen tree says H1 failing means reject.**
  - It does so by reclassifying H1 as a harness defect, verified by a test.
  - R&D agrees with the substance. The failure is a counting-window bug, and every request is accounted for.
  - But it is a departure from the pre-registered tree. It must be a **dated amendment (v3.2) and Mike's decision**, recorded as such, not a quiet re-reading.
  - The stakes are low: a traced run never enters the routing table.
- **Argon's point that Ollama's duration ticks make prompt tok/s coarse is not checked.** Item 4 doesn't depend on it.

**R&D's recommendation:** (b), as amendment v3.2, if Mike agrees. The work would be:
1. **The three code fixes in interlock:** instrument before the guard; stop the companion before `end_slot()`, with `end_slot()` ending per-arm emission; size from the transport's byte count.
2. **A deterministic test** against a local fake Ollama server. It runs the 5090 guard path and the companion teardown, and asserts:
   - sent = counted, with the driver's process-wide counter;
   - spans = the traced slots' calls;
   - every span closed;
   - no prompt text in the trace.
3. **A check of "debug only" in interlock:** a traced run is marked in its receipt and never appended to the routing table. Add a test if it isn't already enforced.
4. **An Argon code review** of 1–3, per the protocol.
5. **No 5090 or NPU time.** Stage 2 is cancelled for Relay under the tree (H2 failed on the 5090).

## The decision (2026-10-14)

The Director chose (b), debug only, recorded as design amendment v3.2 ([design.md](../design.md), change log). The work goes through an Argon build brief: Argon writes the diffs and tests, R&D applies and verifies them on the stage branch, and a separate Argon code review follows.

**A defect found while writing that brief:** the stage 1 run appended its 9 rows to interlock's `table/routing.jsonl`, the 4 traced arms included, plus a `table/gaps.md` line. `receipts.py` excludes only `descriptive` rows, so nothing kept traced rows out.
- The table changes were never committed. They were reverted on the stage branch, and a copy of the diff was kept.
- The receipts stay as the record.
- Enforcing "debug only" in the table is one of the brief's items.

**The build round closed the same day.** Argon's build was applied with six recorded departures, then reviewed by Argon on the branch and approved as is. The record, with the verdict and the disposition: [../argon-code-review-v32.md](../argon-code-review-v32.md). Interlock `relay-stage0` at `ca4aa8e` goes to the Publisher for merge.

