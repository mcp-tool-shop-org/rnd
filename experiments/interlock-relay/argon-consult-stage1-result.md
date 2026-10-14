# Argon consult: interlock-relay stage 1 result

**For Argon, from R&D. 2026-10-14.** This brief is self-contained: everything you need is below. Nothing will run until Mike has your answer and gives his go.

## What this experiment is

**interlock** is the studio's local-model measurement harness. It runs models on an RTX 5090 through Ollama, measures decode and prompt speed, latency, CPU and VRAM, and writes receipts.

**The question:** can NVIDIA's NeMo Relay 0.10.1, an open tracing library, trace interlock's model calls without changing what interlock measures? Relay writes ATOF spans: one start and one end per model call, through a native extension.

**Wiring:** interlock wraps the adapter's HTTP transport in a hook.
- Every request is classified (show, generate, unload, ps, and so on) and timed.
- It is counted in a per-run call table, `calls.json`.
- When tracing is on, the request is also emitted to Relay as an `llm.call` / `llm.call_end` pair.

The design was pre-registered (v3.1), and its analysis code was frozen before any counted run. You reviewed both in earlier rounds.

**Stage 1** is the 5090 run. It pairs traced and untraced arms in A1–B–A2 triples: alone, traced, alone. There are 30 triples per pair.

### The hypotheses

- **H1, the trace accounts for every request:**
  - (a) the number of requests the adapter actually sent equals the call table's total;
  - (b) the trace's spans are exactly the call ids of the traced slots;
  - (c) every span is closed.
  - "Sent" is counted by the stage driver, which patches `http.client.HTTPConnection.request` for the whole child process and counts requests whose stack passes through the Ollama adapter's file.
- **H2, tracing doesn't change the measurements:**
  - each metric is equivalent (TOST against a band taken from the run's own A–A noise), plus a tail gate;
  - plus a hard **client-time gate**. hᵢ = hook time of the traced slot − the mean hook time of its two untraced neighbours. It must have a median under 0.5 ms and a p99 under 2 ms.
  - Hook time is the time the hook spends outside the model call: before the request goes out and after it returns. A slot holds two calls, `show` and `generate`.
- **H3, nothing leaks:** no canary, host, user or home path in any trace; scopes closed; a stop-file run stops cleanly.
- **The import check:** the same equivalence, measured across processes, so that importing Relay alone doesn't shift anything.

### The pre-registered decision rule (a strict tree)

1. **If H1, H3 or H4 fails:** reject, remove the integration and keep the native counter. (H4 was decided in stage 0 and held.)
2. **Otherwise, if H2 fails on any device:** adopt `--trace` for debugging runs only. Traced runs are marked in their receipts and never enter the routing table.
3. Otherwise, adopt it.

## The frozen verdict, unchanged

Run `relay-s1-20261014b`, at interlock `a43cc31`, on 2026-10-14:
- all six steps ran;
- VRAM peaked at 18.9 GB;
- wall time 16 min 55 s.

The analysis is byte-identical to its freeze. **stage1_holds = false.**

| Check | Result |
|---|---|
| H1 (a), requests counted once | **fails** in every traced step. Sent − counted = **exactly 1** each time: decode 204/203, long 217/216, unload 24/23, companion 63/62 |
| H1 (b), spans = the traced slots' calls | holds, except **companion: fails** (11 spans, 8 traced call ids) |
| H1 (c), every span closed | holds everywhere |
| H2 decode | decode tok/s, latency, prompt tok/s and system CPU all **hold**. Client time **fails**: median 0.548 ms, p99 0.650 ms |
| H2 long | decode tok/s, latency and prompt tok/s **hold**. System CPU is **inconclusive** (secondary). Client time **fails**: median 0.682 ms, p99 0.781 ms |
| Import check (15 triples) | **fails** on one tail: prompt tok/s has 4 excursions against 3 allowed. Its mean and interval hold, and decode tok/s and latency hold |
| H3 | **holds** in every step, including the stop step |

Under the tree, H1 failing means **reject**. Nothing is re-scored.

## Diagnosis

Read-only, from the run's own records and the code. Item C adds a CPU-only bench.

### A. H1's off-by-one: a harness artifact, in our reading

Before a 5090 run, the runner checks that the card is empty. It does that through the adapter's own method:

```python
# runner.py, in the procedure, before the tracer exists
if _uses_5090(spec):
    probe = _card_probe(adapters, spec)        # adapter.loaded_models -> GET /api/ps
    _card_guards(probe, path, wall())          # heartbeat, then require_card_empty(probe())
tracer = Tracer(root=root, run_id=name, mode=trace)
with tracer:
    instrument(adapters, tracer)               # wraps the transport from here on
```

The driver's counter covers the whole child process. The tracer covers only the wrapped transport. The evidence:
- Every step's counter shows exactly one `/api/ps`, and no step's call table has a `ps` entry.
- With that request set aside, every path matches the table exactly:

| Step | generate sent | table: generate + unload + count + companion | show sent / table | Other |
|---|---:|---:|---:|---|
| decode | 102 | 101 + 1 | 101 / 101 | |
| long | 117 | 98 + 3 + 16 | 98 / 98 | tags 1 / 1 |
| unload | 12 | 11 + 1 | 11 / 11 | |
| companion | 35 | 21 + 8 + 6 | 27 / 27 | |

Stage 0 never hit this, because the guard fires only for a 5090 spec.

### B. The companion's stray spans: a harness artifact, in our reading

There are three extra spans: call ids 13, 31 and 49. All three are `unload` calls with **no arm and no slot**, and each follows a traced `with-companion-on` slot. Call 13 comes right after calls 11 and 12 of slot `repeat:0:paired:companion-traced`.

The order in the slot's `finally` is:

```python
slot_calls = tracer.end_slot()       # takes the slot's call ids (success path)
...
_session(adapters, companion, "stop", ...)   # the companion's stop is an unload
...
if tracer is not None and per_arm_trace:
    tracer.set_emitting(False)       # emission off only now
```

So the companion's unload starts after the slot has closed, while emission is still on. It is traced and counted under `_run`, but belongs to no slot. That's three traced companion slots and three stray spans.

### C. Client time: real

From the receipts (two calls per slot):

| Pair | Traced, median per slot | Untraced, median per slot | Traced extra per call |
|---|---:|---:|---:|
| decode | 614 µs | 71 µs | ≈ 270 µs |
| long | 761 µs | 75 µs | ≈ 343 µs |

**A bench on the same CPU**, against a stub transport, run warm in a tight loop, with no device or network:

| Call | Body | Untraced hook | Traced hook | Of which `json.dumps` for the size |
|---|---:|---:|---:|---:|
| show | 21 B | 1.9 µs | 31.0 µs | 0.6 µs |
| decode generate | 240 B | 2.1 µs | 32.2 µs | 1.1 µs |
| long generate | 148 KB | 2.2 µs | 138.1 µs | 104.4 µs |

**The traced path, per call:**

```python
size = len(json.dumps(body)) if body is not None and tracer.mode == "relay" and tracer.emitting else 0
record = tracer.start(...)   # under a lock: RelaySink.start -> nemo_relay.llm.call(...), metadata dict
...                          # the model call (not charged)
tracer.end(record, ...)      # under the lock: RelaySink.end -> nemo_relay.llm.call_end(...)
```

Relay's request and response sanitizers replace content with a byte length.

**What a profile of the traced path shows:**
- The time is Relay's native `llm.call` and `llm.call_end`, plus the sanitizer wrappers (about 30 µs warm).
- Interlock serialises the request once to size it, which costs about 104 µs at 148 KB. That accounts for the gap between long and decode: about 147 µs per slot live, about 106 µs per generate on the bench.
- The lock and the bookkeeping cost a few µs.

**Live against the bench:** live hook time is about **9–17×** the warm bench, both untraced (35 vs 2 µs per call) and traced (≈270 vs 30 µs).
- Our hypothesis, **not shown:** each slot is followed by the stage's barrier (trace flush, `gc.collect()`, a 250 ms rest). So the next slot's first calls run on a cold CPU, with clocks down and caches cold, which multiplies all hook code alike.

**Removing the `json.dumps` alone would not pass the gate.** Decode misses it with almost no dumps cost.

### D. The import check's tail

prompt tok/s had 4 excursions against 3 allowed, over 15 triples. Its mean and interval hold. We haven't diagnosed it.

## The amendment we would propose for a rerun

It would be dated, frozen before any run, and would need your review and Mike's go.

1. **H1 (a):** decide the window explicitly. Either:
   - bring the empty-card guard inside the tracer window, by instrumenting before the guard, so its `/api/ps` is traced and counted (it would land in `_run`); or
   - start the driver's counter at `instrument()`. In that case the analysis would read the count from a marker the runner writes, not from the whole process.

   We lean to the first: everything the adapter sends is then in both counts.
2. **The companion:** run the companion's stop before `end_slot()`, so its unload belongs to the slot that started it.
   - This changes the traced slot's contents: one more call, an unload.
   - So the A arms' slots must change in the same way. The untraced companion arm already stops its companion in the same `finally`.
3. **Client time:**
   - The 0.5 ms gate stays.
   - Size the request without serialising the body, for example from the byte count the transport already sends.
   - Optionally, measure the cold-CPU effect: hook time per call against its position after the barrier, plus the CPU clock at the slot's start. This is reported, not gated.
4. **Re-freeze the analysis** with the H1 window rule from item 1. Nothing else in it changes.

## Questions for Argon

1. **Do the two artifact diagnoses hold?**
   - Would the fixes make H1 (a) and the companion's span check sound? The fixes are: bring the guard inside the tracer window (or exclude it explicitly), and end the slot after the companion's stop.
   - Or would either fix mask something? For example, a real missed call that happens to also be off by one, or a stop that should never be traced.
   - Is H1's frozen "reject" right to stand as the verdict for this run, even if the cause is the harness? We think yes: a frozen rule is applied as written, and a rerun is a new pre-registration.
2. **Client time:**
   - Is the cold-CPU-after-barrier hypothesis plausible for 9–17× on a Windows desktop CPU, and on both arms alike? How would you show it without moving the gate?
   - What could legitimately bring Relay's per-call cost under 0.5 ms per two-call slot? Candidates: no `json.dumps` sizing, batching or deferring the native calls off the calling thread, a cheaper sanitizer, dropping the per-call metadata dict.
   - Which of those would change what the design tests? Deferring the spans, for instance, moves cost rather than removing it.
   - The decision rule already allows "debug tracing only, never on counted runs" when H2 fails. Should that simply be the conclusion?
3. **Is a rerun worth it at all?** Relay's native `call` + `call_end` cost about 30 µs warm, and the live overhead was 9–17× the bench. Is there a realistic path to under 0.5 ms per slot on this rig, or would a rerun mostly re-measure H1's harness fix?
4. **The import-check tail:** prompt tok/s, 4 excursions against 3 allowed, over 15 triples. Noise at n = 15, or something to look at before any rerun?
5. **Your verdict:** one of
   - (a) **rerun** with the amendment, as is or as you'd change it;
   - (b) **stop at "debug only":** treat H1 as a harness defect to fix, and adopt `--trace` for debugging runs, never on counted runs;
   - (c) **reject**, as the frozen tree says.

   Say which, and what would change your mind.
