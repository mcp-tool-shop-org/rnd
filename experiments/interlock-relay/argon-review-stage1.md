# Review brief for Argon: NeMo Relay inside interlock, the stage 1 harness and its frozen analysis

R&D, 2026-10-14. You reviewed the stage 0 code in two rounds and found it could finish. Stage 0 decided on fakes that Relay's trace carries what interlock's counter loses (H4a), and that Relay earns its place over a native event log (H4b).

**Stage 1 is the first device run.** Ollama runs on an RTX 5090, under a grant, for about 60 minutes. Before it starts, review two things:
- **The stage 1 harness,** built and tested on fakes. No device or model has been used.
- **The H1/H2/H3 analysis,** frozen in an rnd commit (`43643bc`) before any run.

Your findings are advice: R&D decides what to act on and records why. The run waits for your verdict, then the Director's go and the Publisher's grant.

## What stage 1 decides (design v3.1)

- **H2:** turning Relay tracing on doesn't change what interlock measures on the 5090.
  - **The comparison:** off–on–off triples on the same warm model, each slot followed by the same barrier (flush the trace, `gc.collect()`, a 250 ms rest).
  - **The primary gate** is two one-sided tests on the per-triple difference, at δ = half the noise band.
  - **There's also a tail gate.**
  - **The hard client-time gate:** under 0.5 ms at the median and 2 ms at the 99th percentile.
  - **A process-level import check:** 15 process triples of no import, idle import and no import. It also checks that the barrier doesn't shift the untraced baseline.
- **H1 on the live server:** every model call is counted once, against an independent count below the hook, and traced once in traced slots.
- **H3:** the trace holds no prompt (a canary is planted), host, user or home path; a stop through interlock's stop file leaves a closed trace; and receipts pass `interlock check`.

## How the harness works

- **Arms and pairs:**
  - Arms A and B are the same arm, except B has `trace: true`.
  - A new pair kind, `contrast: trace`, uses interlock's existing ABA order. The spec validator refuses the pair unless the two arms are identical in every key but `id` and `trace`. No companion runs in the pair.
- **What the tracer records:**
  - It switches the sink's events per slot. A call keeps the choice it started with, so no start is ever left without its end.
  - Output is off outside slots, so the trace holds exactly the traced slots' calls.
  - The counter stays on in both arms.
- **Hook time:** each slot records `hook_us`, the time the hooks spent outside the model call (classifying, sizing, counting and the sink), measured in the transport wrapper and in OpenVINO's `_timed_call`.
- **The long-prompt spec** salts each call's prompt with a run-wide number, so Ollama's prompt cache can't skip the prefill.
- **The driver** (`scripts/relay_s1.py`):
  - A full preflight before each step, where any failure refuses before a model call.
  - An `http.client` counter that counts only requests sent from the Ollama adapter's file. That's H1's ground truth; supervisor health checks are excluded, by the design.
  - The four traced runs, run in-process.
  - The stop run in a child process, because the watcher ends its process with `os._exit`.
  - The import check in child processes.
  - Afterwards, `interlock check` runs and a driver record is written.
- **Calls summary:** at close, the tracer writes `logs/<run_id>.calls.json`, the full count table with run-level calls included.

## Three changes R&D made before freezing, which you should check

1. **The band (amendment S1-A1).**
   - The band comes from the run's own A–A pairs, not from committed receipts.
   - The reason: E4's committed 5090 slots carry periodic reload outliers, and no committed receipt has per-call spreads for a 32k-token prefill.
2. **The tail gate (S1-A4).**
   - **The first draft:** band = the 95th percentile of |A–A|, with the gate "p95 |Δ| ≤ band" plus "B's excursions ≤ A–A's + 1".
   - **What the simulation showed:** under the null, that draft failed 27% of runs at n = 30, all in the tail gate.
   - **The redraft:** band = 1.96 × sd(A–A), and the tail gate is an excursion count against a binomial bound (k = 4 at n = 30).
   - **Simulated results** (in the analysis docstring and `simulation.json` below):
     - 1.8% of null runs fail;
     - a 1% shift passes 93% of the time;
     - a 3% shift fails 96% of the time.
   - Is this calibration right, and is "inconclusive" (an interval that spans 0 but overruns δ) handled honestly?
3. **What isn't analysed (S1-A2).** The TTFT proxy isn't analysed: the calls aren't streamed. CPU is the system's at the slot's end, the only CPU reading a slot keeps.

## What to do

1. **Will a triple's only difference be tracing?** Look for anything in the harness that would make A and B differ beyond that:
   - the barrier, the salt and the `json.dumps` size, which is computed only when output is on;
   - the order effects of ABA;
   - the switch between slots.
   - Can a run pass H2 while tracing does cost something?
2. **Check that the analysis is right:** the triple construction, Δ and d, the band, the t-based interval, the tail bound, the client-time gate, the import check and the barrier check.
3. **Check that H1's ground truth is independent of the hook,** and that H3's checks would catch a leak.
4. **Read the specs and the driver** for problems on a live run:
   - VRAM: qwen3:8b at 40,960 tokens peaks at 13,587 MiB (E5); the companion is llama3.1:8b at 4,096; the run aborts at 30,500 MiB.
   - The stop step.
   - The import-check children, which call Ollama outside `interlock run`'s guards. The driver's preflight and a heartbeat re-check before each child stand in for those guards.
5. **Find anything missing** before the counted run.

## How to answer

- **Rank the findings:** blocking (wrong results, unsafe, or a run that can't answer H2), important, minor.
- **For each:** the file and line, a concrete failure scenario, and the fix.
- **Say where it's right.**
- **End with a verdict:** "blocking issues remain", or "no blocking issues; stage 1 can run".

## Test results

At interlock `4295165`:
- with the `relay` extra: 767 passed, 6 skipped, coverage 93.3%;
- without it: 755 passed, 18 skipped, coverage 92.6%;
- `ruff` is clean.

The new test files are `tests/test_relay_stage1.py` (15) and `tests/test_relay_s1_driver.py` (20).

**The analysis's own tests:** `test_analyze.py`, 12, OK.

**End-to-end on fakes:** a decode-shaped spec run through interlock's real runner, with a fake server and 30 triples, then the frozen analysis:
- H2 holds on every measured metric (VRAM is "not measured": the fake has no sensors);
- H1 holds (191 requests sent and counted, 64 spans, all closed);
- H3 holds.

## The stage 1 plan (GPU time, VRAM, preflight)

## The runs (on the 5090, under the grant)

| Step | Model and shape | Calls | Estimated time |
|---|---|---|---|
| 1. Short decode | qwen3:8b, warm, 256-token prompt, 128 tokens (E4's shape: about 0.45 s a call) | 30 triples, plus 3 warm-up calls | ~2 min |
| 2. Long prompt (fill-card-sized prefill) | qwen3:8b, about 32k-token prompt. Each call gets a distinct prefix so Ollama's prompt cache can't skip the prefill. About 4 s a call at E5's 8,700 tokens/s | 30 triples (the floor is 15, sized by the power rule) | ~8 min |
| 3. Unload and companion | one explicit unload-and-reload cycle and one companion load (llama3.1:8b at a 4,096 context), each in a traced and an untraced slot | about 12 | ~4 min |
| 4. Stop file | one short traced run stopped through `<run_id>.stop` | — | ~2 min |
| 5. Process import check | 15 process triples, each with a process start, 1 warm-up and 3 calls | 180 calls | ~6 min |

- **Measured time:** about 22 minutes.
- **With loads, preflights, rests and margin:** request **60 minutes of 5090 time**, with a hard cap of 90. The design estimated 60–90.
- **When:** outside interlock's measurement windows. The card must be idle and unassigned.

## Peak VRAM

From E5's committed receipts (Ollama 0.35.1, Q4_K_M, f16 KV cache, flash attention):
- **qwen3:8b** at its full 40,960 context: **13,587 MiB** peak. Steps 1, 2, 4 and 5 stay at or under this.
- **Step 3's companion** adds llama3.1:8b at a 4,096 context next to qwen3:8b.
  - The estimate is under 21 GiB in total. That's unmeasured: E5 measured llama3.1:8b only at 53,248 tokens (14,247 MiB).
  - The run's own guard aborts at 30,500 MiB, as in E5.
  - If the companion's first load measures over 21 GiB, step 3 drops the companion and keeps the unload-and-reload cycle alone.
- **Idle baseline before the run:** at or under about 2.2 GiB (E5 saw 2,008–2,169 MiB).

## Preflight (every item refuses before any model call)

- **The grant:** the Publisher's grant id is on the command line. The run is outside every interlock measurement window, and the watchdog heartbeat is fresh.
- **The card:**
  - `/api/ps` is empty, with no other process on the GPU (nvidia-smi);
  - the idle VRAM baseline is recorded;
  - the supervisor sees exactly one listener on 11434, and it's the Ollama install.
- **The server:**
  - Ollama 0.35.1;
  - the CUDA backend library, flash attention and the KV cache type are read from the first load and recorded, as E4b and E5 do.
- **Tracing:**
  - no `OTEL_*` variable;
  - `interlock[relay]` is installed with `nemo-relay==0.10.1`;
  - Relay reports no layered `plugins.toml`;
  - `logs/` is git-ignored.
- **The tree:** clean, with the spec committed and unmodified.
- **Disk:** the traces are about 1.2 KB a call, under 1 MB in all.
- **Stop:** the stop file's path is printed at start, and the halt closes the trace (tested in stage 0).

## What happens with the result

- **H1, H2 and H3 hold on the 5090:** stage 2 (OpenVINO on the NPU and iGPU) is planned and goes to the Director the same way.
- **Any of them fails:** stop and reject, with no stage 2. The native event log and the counter are the fallback, as the design says.

## The frozen analysis (rnd 43643bc): analyze.py

```python
"""Stage 1 of the interlock-relay design: the H1, H2 and H3 analysis, frozen before any counted run.

Pure Python, standard library only. Nothing here imports interlock or Relay: it reads the receipts, the traces and
the driver's records that a stage 1 run leaves in an interlock checkout.

    python analyze.py <interlock checkout> <run-id prefix>

The pre-registered rules, in the design's words where it has them (design v3.1, amendments S1-A1 to S1-A3 below):

**H2, per run (decode and long) and per metric.**
- A triple is one round of one pair: alone-before (A1), paired (B, traced) and alone-after (A2).
- Δᵢ = (B − m) / m and dᵢ = (A2 − A1) / m, where m = (A1 + A2) / 2.
- Band = 1.96 × sd(dᵢ), the run's own A–A noise, floored at 0.01 (S1-A1, S1-A4). δ = band / 2.
- **The primary gate** (two one-sided tests): the 90% interval of the mean Δ, mean ± t(0.95, n−1) · sd / √n, lies
  within [−δ, +δ].
  - If it doesn't, but it contains 0, the metric is inconclusive (underpowered), not failed.
  - Inconclusive still means H2 doesn't hold.
- **The tail gate:** the count of |Δᵢ| > band is at most k(n), the smallest k with P(Binomial(n, 0.025) > k) < 0.001
  (k = 4 at n = 30; S1-A4). The 95th percentile of |Δᵢ| is reported, not gated.
- **Metrics:** latency_ms, throughput (the server's decode tok/s), prompt_tok_s, VRAM (sensors.dedicated_mib) and
  system CPU at the slot's end. A metric with fewer than 10 complete triples is "not measured" (S1-A2).
- **The client-time gate** (hard): hᵢ = hook_us(B) − (hook_us(A1) + hook_us(A2)) / 2, in ms. Median < 0.5 and
  99th percentile < 2.

**H2, the process import check.**
- The same Δ, band and gates, on per-process medians of the measured calls: N1, I and N2 per triple.
- **The barrier check:** the median of the in-process decode A calls (with the barrier) and the median of the N
  processes' calls (no barrier) differ by at most the decode band for that metric.

**H1, per traced run:**
- **Request count:** the driver's count of HTTP requests the adapter sent (below the hook) = the sum of the run's
  call table (`logs/<id>.calls.json`).
- **Spans:** the trace's llm spans = the call ids of the traced slots, each with one start and one end.

**H3:**
- The trace parses, with no canary, host name, user name or home path, and the run scope opens and closes.
- The stop run's trace parses and is closed.
- `interlock check` passes, as reported by the driver.

**Amendments made before any run:**
- **S1-A1:** the band comes from the run's own A–A pairs, not from committed receipts. E4's committed 5090 slots for
  qwen3:8b carry periodic reload outliers (a different load state), and no committed receipt has per-call spreads
  for a 32k-token prefill. The A–A pairs measure noise under the run's own conditions, without looking at B. The
  0.01 floor stops a near-constant metric (VRAM) from making a band of zero.
- **S1-A2:** the "TTFT proxy" isn't analysed. The calls aren't streamed, and a slot records total latency and the
  two server rates, not a first-token time. CPU is the system's at the slot's end, the only CPU reading a slot
  keeps (interlock records no per-process CPU per slot).
- **S1-A3:** the client-time gate compares the hook time a slot's calls spent outside the model call (the hook's
  own measurement, `hook_us`), traced against untraced. Stage 0 measured the same quantity on a bare transport.
- **S1-A4:** the first draft defined the band as the 95th percentile of |dᵢ| and gated "p95 |Δᵢ| ≤ band" plus
  "B's excursions ≤ A–A's + 1". A simulation under the null (`simulate.py`, before any run) failed 27% of
  null runs at n = 30, all in the tail gate: two extreme quantiles from 30 values each. The band is now
  1.96 × sd(dᵢ), the same scale in expectation and far steadier. The tail gate is an excursion count against a
  binomial bound. Simulated (`simulation.json`, 4,000 runs each) at n = 30 and a 2% per-call noise:
  - 1.8% of null runs fail one metric, and at most about 9% fail across five independent metrics (the five here
    are correlated, so fewer);
  - with one call in twenty from a four-times-wider spread, 1.8% fail too;
  - a 1% shift passes 93% of the time;
  - a 3% shift fails 96% of the time.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

BAND_FLOOR = 0.01
MIN_TRIPLES = 10
CANARY = "AMU_CANARY_PROMPT_7c1e"


# -- statistics ------------------------------------------------------------------------------------------------------


def _betacf(a: float, b: float, x: float) -> float:
    """The continued fraction of the regularised incomplete beta function (Lentz's method)."""

    tiny = 1e-300
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c if abs(1 + aa / c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c if abs(1 + aa / c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-14:
            break
    return h


def _ibeta(a: float, b: float, x: float) -> float:
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return front * _betacf(a, b, x) / a
    return 1 - front * _betacf(b, a, 1 - x) / b


def t_cdf(t: float, df: int) -> float:
    x = df / (df + t * t)
    tail = 0.5 * _ibeta(df / 2, 0.5, x)
    return 1 - tail if t >= 0 else tail


def t_quantile(p: float, df: int) -> float:
    """The p-quantile of Student's t with df degrees of freedom, by bisection on the CDF."""

    lo, hi = -100.0, 100.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def percentile(values: list[float], q: float) -> float:
    """Linear interpolation between closest ranks (the same rule as interlock's timing.percentile)."""

    ordered = sorted(values)
    if not ordered:
        raise ValueError("no values")
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * q / 100
    low = math.floor(rank)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (rank - low)


# -- the gates --------------------------------------------------------------------------------------------------------


TAIL_P = 0.025  # a single |Δ| beyond the band under the null, at the band's 1.96 sd scale with Δ's smaller variance
TAIL_ALPHA = 0.001


def tail_bound(n: int) -> int:
    """The smallest k with P(Binomial(n, TAIL_P) > k) < TAIL_ALPHA."""

    cdf = 0.0
    for k in range(n + 1):
        cdf += math.comb(n, k) * TAIL_P**k * (1 - TAIL_P) ** (n - k)
        if 1 - cdf < TAIL_ALPHA:
            return k
    return n


def equivalence(deltas: list[float], aa: list[float]) -> dict:
    """The primary and tail gates for one metric, from its per-triple Δ and A–A d."""

    n = len(deltas)
    if n < MIN_TRIPLES or len(aa) != n:
        return {"verdict": "not measured", "triples": n}
    band = max(1.96 * statistics.stdev(aa), BAND_FLOOR)
    delta = band / 2
    mean = statistics.fmean(deltas)
    sd = statistics.stdev(deltas) if n > 1 else 0.0
    half = t_quantile(0.95, n - 1) * sd / math.sqrt(n)
    low, high = mean - half, mean + half
    primary = -delta <= low and high <= delta
    tail_p95 = percentile([abs(x) for x in deltas], 95)
    b_out = sum(abs(x) > band for x in deltas)
    a_out = sum(abs(x) > band for x in aa)
    allowed = tail_bound(n)
    tail = b_out <= allowed
    if primary and tail:
        verdict = "holds"
    elif not primary and low <= 0 <= high and tail:
        verdict = "inconclusive"
    else:
        verdict = "fails"
    return {
        "verdict": verdict, "triples": n, "band": band, "delta": delta, "mean": mean, "interval": [low, high],
        "half_width": half, "primary": primary, "tail_p95": tail_p95, "b_excursions": b_out, "aa_excursions": a_out,
        "excursions_allowed": allowed, "tail": tail,
    }


def triples(slots_by_arm: dict[str, list[dict]], pair: str) -> list[tuple[dict, dict, dict]]:
    """(A1, B, A2) slots per round of one pair, repeat phase only, rounds where all three are present."""

    rounds: dict[int, dict[str, dict]] = {}
    for slots in slots_by_arm.values():
        for slot in slots:
            if slot.get("phase") == "repeat" and slot.get("pair") == pair:
                rounds.setdefault(slot["round"], {})[slot["role"]] = slot
    out = []
    for index in sorted(rounds):
        roles = rounds[index]
        if {"alone-before", "paired", "alone-after"} <= set(roles):
            out.append((roles["alone-before"], roles["paired"], roles["alone-after"]))
    return out


METRICS = {
    "latency_ms": lambda s: s.get("latency_ms"),
    "decode_tok_s": lambda s: s.get("throughput"),
    "prompt_tok_s": lambda s: s.get("prompt_tok_s"),
    "vram_mib": lambda s: (s.get("sensors") or {}).get("dedicated_mib"),
    "system_cpu_pct": lambda s: ((s.get("cpu") or {}).get("slot_end") or {}).get("cpu_percent"),
}


def _number(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return float(value)


def deltas_for(trips, read) -> tuple[list[float], list[float]]:
    deltas, aa = [], []
    for a1, b, a2 in trips:
        x1, y, x2 = _number(read(a1)), _number(read(b)), _number(read(a2))
        if x1 is None or y is None or x2 is None:
            continue
        m = (x1 + x2) / 2
        if m == 0:
            continue
        deltas.append((y - m) / m)
        aa.append((x2 - x1) / m)
    return deltas, aa


def client_time(trips) -> dict:
    diffs = []
    for a1, b, a2 in trips:
        if all(isinstance(s.get("hook_us"), (int, float)) for s in (a1, b, a2)):
            diffs.append((b["hook_us"] - (a1["hook_us"] + a2["hook_us"]) / 2) / 1000)
    if len(diffs) < MIN_TRIPLES:
        return {"verdict": "not measured", "triples": len(diffs)}
    median, p99 = statistics.median(diffs), percentile(diffs, 99)
    return {"verdict": "holds" if median < 0.5 and p99 < 2.0 else "fails", "triples": len(diffs),
            "median_ms": median, "p99_ms": p99}


def h2_run(rows: list[dict], pair: str) -> dict:
    slots_by_arm = {row["id"].split("/")[1]: (row.get("artifacts") or {}).get("slots") or [] for row in rows}
    trips = triples(slots_by_arm, pair)
    metrics = {name: equivalence(*deltas_for(trips, read)) for name, read in METRICS.items()}
    measured = {k: v for k, v in metrics.items() if v["verdict"] != "not measured"}
    clock = client_time(trips)
    holds = bool(measured) and all(v["verdict"] == "holds" for v in measured.values()) and clock["verdict"] == "holds"
    return {"pair": pair, "triples": len(trips), "metrics": metrics, "client_time": clock, "holds": holds}


def h2_import(record: dict, decode_rows: list[dict]) -> dict:
    """The process import check: per-process medians in N1, I, N2 triples, then the barrier check."""

    trips = []
    for triple in record.get("triples", []):
        n1, imp, n2 = triple["no_import_before"], triple["idle_import"], triple["no_import_after"]
        trips.append(({k: statistics.median(v) for k, v in n1["metrics"].items() if v},
                      {k: statistics.median(v) for k, v in imp["metrics"].items() if v},
                      {k: statistics.median(v) for k, v in n2["metrics"].items() if v}))
    metrics = {name: equivalence(*deltas_for(trips, lambda s, name=name: s.get(name)))
               for name in ("latency_ms", "decode_tok_s", "prompt_tok_s")}
    decode = h2_run(decode_rows, "decode") if decode_rows else None
    barrier = {}
    for name, read in (("latency_ms", METRICS["latency_ms"]), ("decode_tok_s", METRICS["decode_tok_s"])):
        in_process = [v for a1, _b, a2 in (triples({r["id"].split("/")[1]: r["artifacts"]["slots"]
                                                       for r in decode_rows}, "decode") if decode_rows else [])
                      for v in (_number(read(a1)), _number(read(a2))) if v is not None]
        processes = [v for t in record.get("triples", []) for side in ("no_import_before", "no_import_after")
                     for v in t[side]["metrics"].get(name, [])]
        band = (decode or {}).get("metrics", {}).get(name, {}).get("band")
        if in_process and processes and band is not None:
            a, b = statistics.median(in_process), statistics.median(processes)
            gap = abs(a - b) / ((a + b) / 2)
            barrier[name] = {"with_barrier": a, "without": b, "gap": gap, "band": band, "holds": gap <= band}
        else:
            barrier[name] = {"holds": None, "reason": "no data"}
    measured = {k: v for k, v in metrics.items() if v["verdict"] != "not measured"}
    holds = bool(measured) and all(v["verdict"] == "holds" for v in measured.values()) and all(
        b["holds"] is True for b in barrier.values())
    return {"triples": len(trips), "metrics": metrics, "barrier": barrier, "holds": holds}


def h1_run(trace_path: Path, calls_path: Path, http_path: Path, rows: list[dict]) -> dict:
    events = [json.loads(x) for x in trace_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    llm = [e for e in events if e.get("category") == "llm"]
    starts = {e["metadata"]["call_id"] for e in llm if e.get("scope_category") == "start"}
    ends = {e["metadata"]["call_id"] for e in llm if e.get("scope_category") == "end"}
    traced_ids = {i for row in rows for s in (row.get("artifacts") or {}).get("slots") or [] if s.get("traced")
                  for i in s.get("call_ids", [])}
    table = json.loads(calls_path.read_text(encoding="utf-8"))["counts"]
    counted = sum(v["n"] for kinds in table.values() for v in kinds.values())
    sent = json.loads(http_path.read_text(encoding="utf-8"))["adapter_requests"]
    checks = {
        "requests_counted_once": counted == sent,
        "spans_are_the_traced_slots_calls": starts == traced_ids,
        "every_span_closed": starts == ends,
    }
    return {"checks": checks, "sent": sent, "counted": counted, "spans": len(starts), "holds": all(checks.values())}


def h3_trace(trace_path: Path, needles: dict[str, str]) -> dict:
    text = trace_path.read_text(encoding="utf-8")
    events = []
    parsed = True
    for line in text.splitlines():
        if line.strip():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                parsed = False
    agent = [e.get("scope_category") for e in events if e.get("category") == "agent"]
    checks = {
        "parses": parsed,
        "no_canary": CANARY not in text,
        "run_scope_closed": agent == ["start", "end"],
        **{f"no_{k}": (v.lower() not in text.lower()) for k, v in needles.items() if v},
    }
    return {"checks": checks, "holds": all(checks.values())}


# -- the run ----------------------------------------------------------------------------------------------------------


def _rows(root: Path, run_id: str) -> list[dict]:
    path = root / "receipts" / f"{run_id}.jsonl"
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()] if path.is_file() else []


def analyze(root: Path, prefix: str) -> dict:
    driver = json.loads((root / "logs" / f"{prefix}.driver.json").read_text(encoding="utf-8"))
    needles = driver.get("needles", {})
    out: dict = {"prefix": prefix, "h1": {}, "h3": {}, "h2": {}}
    for step in ("decode", "long", "unload", "companion"):
        run_id = f"{prefix}-{step}"
        rows = _rows(root, run_id)
        trace = root / "logs" / f"{run_id}.atof.jsonl"
        if not rows or not trace.is_file():
            out["h1"][step] = {"holds": None, "reason": "not run"}
            continue
        out["h1"][step] = h1_run(trace, root / "logs" / f"{run_id}.calls.json", root / "logs" / f"{run_id}.http.json",
                                 rows)
        out["h3"][step] = h3_trace(trace, needles)
        if step in ("decode", "long"):
            out["h2"][step] = h2_run(rows, step)
    stop_trace = root / "logs" / f"{prefix}-stop.atof.jsonl"
    out["h3"]["stop"] = h3_trace(stop_trace, needles) if stop_trace.is_file() else {"holds": None, "reason": "not run"}
    out["h3"]["receipts_check"] = {"holds": driver.get("check_passed")}
    imports = root / "logs" / f"{prefix}-import.json"
    out["h2"]["import"] = (h2_import(json.loads(imports.read_text(encoding="utf-8")), _rows(root, f"{prefix}-decode"))
                           if imports.is_file() else {"holds": None, "reason": "not run"})
    parts = [v.get("holds") for section in ("h1", "h2", "h3") for v in out[section].values()]
    out["stage1_holds"] = all(p is True for p in parts)
    return out


def main(argv: list[str]) -> int:
    root, prefix = Path(argv[1]), argv[2]
    result = analyze(root, prefix)
    print(json.dumps(result, indent=1, sort_keys=True, default=str))
    return 0 if result["stage1_holds"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

## Its simulation (simulate.py) and results (simulation.json)

```python
"""The null and shifted-run behaviour of the frozen H2 gates (analyze.equivalence), by simulation. No real data.

    python simulate.py

Each run draws n triples: a per-round base, then A1, B and A2 each with independent per-call noise (normal, sd
`sigma`), with B shifted by `shift`. It reports how often equivalence() returns "holds". This is the evidence for
amendment S1-A4, and it runs on the analysis exactly as frozen.
"""

from __future__ import annotations

import json
import random

import analyze as an


def run(*, n: int, shift: float, sigma: float = 0.02, runs: int = 4000, seed: int = 11, heavy: bool = False) -> float:
    rng = random.Random(seed)

    def noise() -> float:
        if heavy and rng.random() < 0.05:
            return rng.gauss(0, 4 * sigma)  # one call in twenty from a four-times-wider spread
        return rng.gauss(0, sigma)

    holds = 0
    for _ in range(runs):
        deltas, aa = [], []
        for _ in range(n):
            base = 1 + noise()
            a1, a2 = base * (1 + noise()), base * (1 + noise())
            b = base * (1 + shift) * (1 + noise())
            m = (a1 + a2) / 2
            deltas.append((b - m) / m)
            aa.append((a2 - a1) / m)
        holds += an.equivalence(deltas, aa)["verdict"] == "holds"
    return holds / runs


def main() -> None:
    rows = []
    for n in (15, 30):
        for shift in (0.0, 0.01, 0.02, 0.03, 0.05):
            rows.append({"n": n, "shift": shift, "holds": run(n=n, shift=shift)})
    rows.append({"n": 30, "shift": 0.0, "heavy_tail": True, "holds": run(n=30, shift=0.0, heavy=True)})
    print(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
```

```json
[
 {
  "n": 15,
  "shift": 0.0,
  "holds": 0.9435
 },
 {
  "n": 15,
  "shift": 0.01,
  "holds": 0.7485
 },
 {
  "n": 15,
  "shift": 0.02,
  "holds": 0.30575
 },
 {
  "n": 15,
  "shift": 0.03,
  "holds": 0.0495
 },
 {
  "n": 15,
  "shift": 0.05,
  "holds": 0.0
 },
 {
  "n": 30,
  "shift": 0.0,
  "holds": 0.9815
 },
 {
  "n": 30,
  "shift": 0.01,
  "holds": 0.92575
 },
 {
  "n": 30,
  "shift": 0.02,
  "holds": 0.4735
 },
 {
  "n": 30,
  "shift": 0.03,
  "holds": 0.037
 },
 {
  "n": 30,
  "shift": 0.05,
  "holds": 0.0
 },
 {
  "n": 30,
  "shift": 0.0,
  "heavy_tail": true,
  "holds": 0.98225
 }
]
```

## The specs

### experiments/relay-s1/decode.yaml

```yaml
id: RELAY-S1-DECODE
procedure: interleaved
order: aba
compile_cache: reuse
question: >
  Does tracing qwen3:8b's calls with NeMo Relay change interlock's short-decode measurements on the 5090?
decision: >
  H2 in the interlock-relay design: tracing on changes no receipt metric beyond half its noise band (two one-sided tests on the per-triple difference), the tail gate holds, and the hook time a traced call adds is under 0.5 ms at the median and 2 ms at the 99th percentile. The analysis is frozen in rnd before the run.
band: 0.10
warmups: 3
repeats: 30
rest_s: 0
trace_barrier_ms: 250
needs:
  grant: true
  npu_session: false
  cpu_window: false
dataset:
  name: relay-s1-fixed-prompt
  rule: >
    The E4 seed repeated 25 times, written out in the arms' prompt, so every call and the process import
    check send the same text.
metrics:
  - decode_tok_s
  - latency_ms
  - prompt_tok_s
  - dedicated_mib
stop_rules:
  - The prompt ends with the canary AMU_CANARY_PROMPT_7c1e. It must not appear in any trace (H3).
  - A failed step stops the sequence. A failed step is inconclusive, not a pass.
  - Order is A-B-A per round. A is untraced, B is the same arm with tracing on. Cold is once per arm and stays out
    of the comparison.
  - After every slot, in both arms, the harness flushes the trace, collects garbage and rests 250 ms.
  - The run refuses --trace off. The comparison is analysed by experiments/interlock-relay/stage1/analyze.py in
    rnd, frozen before the run.
arms:
  - id: decode-off
    task: generate
    device: "5090"
    engine: ollama
    model: qwen3:8b
    revision_or_digest: 500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41
    quant: unrecorded
    licence: unrecorded
    engine_version: "0.35.1"
    thinking_level: "off"
    num_predict: 128
    num_ctx: null
    batch: null
    prompt: "The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. AMU_CANARY_PROMPT_7c1e"
    trace: false
    measure: decode_tok_s
  - id: decode-on
    task: generate
    device: "5090"
    engine: ollama
    model: qwen3:8b
    revision_or_digest: 500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41
    quant: unrecorded
    licence: unrecorded
    engine_version: "0.35.1"
    thinking_level: "off"
    num_predict: 128
    num_ctx: null
    batch: null
    prompt: "The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. AMU_CANARY_PROMPT_7c1e"
    trace: true
    measure: decode_tok_s
pairs:
  - id: decode
    alone: decode-off
    paired: decode-on
    contrast: trace
```

### experiments/relay-s1/long.yaml

```yaml
id: RELAY-S1-LONG
procedure: interleaved
order: aba
compile_cache: reuse
question: >
  Does tracing change interlock's long-prompt (prefill-heavy) measurements of qwen3:8b on the 5090?
decision: >
  H2 in the interlock-relay design: tracing on changes no receipt metric beyond half its noise band (two one-sided tests on the per-triple difference), the tail gate holds, and the hook time a traced call adds is under 0.5 ms at the median and 2 ms at the 99th percentile. The analysis is frozen in rnd before the run.
band: 0.10
warmups: 2
repeats: 30
rest_s: 0
trace_barrier_ms: 250
needs:
  grant: true
  npu_session: false
  cpu_window: false
dataset:
  name: relay-s1-long-prompt
  seed: "The switchyard counts the same cars on every pass. "
  target_tokens: 32768
  rule: >
    Repeat the seed to 32,768 tokens by the served model's count. Each call starts with its own number
    (prompt_salt per_call), so the server's prompt cache never skips the prefill.
metrics:
  - decode_tok_s
  - latency_ms
  - prompt_tok_s
  - dedicated_mib
stop_rules:
  - A failed step stops the sequence. A failed step is inconclusive, not a pass.
  - Order is A-B-A per round. A is untraced, B is the same arm with tracing on. Cold is once per arm and stays out
    of the comparison.
  - After every slot, in both arms, the harness flushes the trace, collects garbage and rests 250 ms.
  - The run refuses --trace off. The comparison is analysed by experiments/interlock-relay/stage1/analyze.py in
    rnd, frozen before the run.
arms:
  - id: long-off
    task: generate
    device: "5090"
    engine: ollama
    model: qwen3:8b
    revision_or_digest: 500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41
    quant: unrecorded
    licence: unrecorded
    engine_version: "0.35.1"
    thinking_level: "off"
    num_predict: 16
    num_ctx: 40960
    batch: null
    prompt_salt: per_call
    trace: false
    measure: decode_tok_s
  - id: long-on
    task: generate
    device: "5090"
    engine: ollama
    model: qwen3:8b
    revision_or_digest: 500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41
    quant: unrecorded
    licence: unrecorded
    engine_version: "0.35.1"
    thinking_level: "off"
    num_predict: 16
    num_ctx: 40960
    batch: null
    prompt_salt: per_call
    trace: true
    measure: decode_tok_s
pairs:
  - id: long
    alone: long-off
    paired: long-on
    contrast: trace
```

### experiments/relay-s1/unload.yaml

```yaml
id: RELAY-S1-UNLOAD
procedure: interleaved
order: aba
compile_cache: reuse
question: >
  Are unload-and-load cycles traced completely, in traced and untraced slots, on the 5090?
decision: >
  H1 and H3 on the live server: every call, unloads and loads included, is counted once and traced once in traced slots. Not an H2 comparison: three rounds are too few.
band: 0.10
warmups: 0
repeats: 3
rest_s: 0
trace_barrier_ms: 250
needs:
  grant: true
  npu_session: false
  cpu_window: false
dataset:
  name: relay-s1-fixed-prompt
  rule: >
    The decode spec's prompt. keep_alive 0 unloads the model at the end of every call, so every call loads it.
metrics:
  - decode_tok_s
  - latency_ms
  - prompt_tok_s
  - dedicated_mib
stop_rules:
  - The prompt ends with the canary AMU_CANARY_PROMPT_7c1e. It must not appear in any trace (H3).
  - A failed step stops the sequence. A failed step is inconclusive, not a pass.
  - Order is A-B-A per round. A is untraced, B is the same arm with tracing on. Cold is once per arm and stays out
    of the comparison.
  - After every slot, in both arms, the harness flushes the trace, collects garbage and rests 250 ms.
  - The run refuses --trace off. The comparison is analysed by experiments/interlock-relay/stage1/analyze.py in
    rnd, frozen before the run.
arms:
  - id: unload-off
    task: generate
    device: "5090"
    engine: ollama
    model: qwen3:8b
    revision_or_digest: 500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41
    quant: unrecorded
    licence: unrecorded
    engine_version: "0.35.1"
    thinking_level: "off"
    num_predict: 32
    num_ctx: null
    batch: null
    prompt: "The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. AMU_CANARY_PROMPT_7c1e"
    keep_alive: 0
    trace: false
    measure: decode_tok_s
  - id: unload-on
    task: generate
    device: "5090"
    engine: ollama
    model: qwen3:8b
    revision_or_digest: 500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41
    quant: unrecorded
    licence: unrecorded
    engine_version: "0.35.1"
    thinking_level: "off"
    num_predict: 32
    num_ctx: null
    batch: null
    prompt: "The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. AMU_CANARY_PROMPT_7c1e"
    keep_alive: 0
    trace: true
    measure: decode_tok_s
pairs:
  - id: unload
    alone: unload-off
    paired: unload-on
    contrast: trace
```

### experiments/relay-s1/companion.yaml

```yaml
id: RELAY-S1-COMPANION
procedure: interleaved
order: aba
compile_cache: reuse
question: >
  Is a companion load on the 5090 traced completely, in traced and untraced slots?
decision: >
  H1 and H3 on the live server: the companion's calls are counted once and traced once in traced slots. Not an H2 comparison.
band: 0.10
warmups: 0
repeats: 3
rest_s: 0
trace_barrier_ms: 250
needs:
  grant: true
  npu_session: false
  cpu_window: false
dataset:
  name: relay-s1-fixed-prompt
  rule: >
    The decode spec's prompt for both models.
metrics:
  - decode_tok_s
  - latency_ms
  - prompt_tok_s
  - dedicated_mib
stop_rules:
  - The prompt ends with the canary AMU_CANARY_PROMPT_7c1e. It must not appear in any trace (H3).
  - A failed step stops the sequence. A failed step is inconclusive, not a pass.
  - Order is A-B-A per round. A is untraced, B is the same arm with tracing on. Cold is once per arm and stays out
    of the comparison.
  - After every slot, in both arms, the harness flushes the trace, collects garbage and rests 250 ms.
  - The run refuses --trace off. The comparison is analysed by experiments/interlock-relay/stage1/analyze.py in
    rnd, frozen before the run.
arms:
  - id: solo
    task: generate
    device: "5090"
    engine: ollama
    model: qwen3:8b
    revision_or_digest: 500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41
    quant: unrecorded
    licence: unrecorded
    engine_version: "0.35.1"
    thinking_level: "off"
    num_predict: 32
    num_ctx: null
    batch: null
    prompt: "The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. AMU_CANARY_PROMPT_7c1e"
    trace: false
    measure: decode_tok_s
  - id: with-companion-on
    task: generate
    device: "5090"
    engine: ollama
    model: qwen3:8b
    revision_or_digest: 500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41
    quant: unrecorded
    licence: unrecorded
    engine_version: "0.35.1"
    thinking_level: "off"
    num_predict: 32
    num_ctx: null
    batch: null
    prompt: "The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. AMU_CANARY_PROMPT_7c1e"
    trace: true
    measure: decode_tok_s
    companion: companion
    companion_device: "5090"
  - id: with-companion-off
    task: generate
    device: "5090"
    engine: ollama
    model: qwen3:8b
    revision_or_digest: 500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41
    quant: unrecorded
    licence: unrecorded
    engine_version: "0.35.1"
    thinking_level: "off"
    num_predict: 32
    num_ctx: null
    batch: null
    prompt: "The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. AMU_CANARY_PROMPT_7c1e"
    trace: false
    measure: decode_tok_s
    companion: companion
    companion_device: "5090"
  - id: companion
    task: generate
    device: "5090"
    engine: ollama
    model: llama3.1:8b
    revision_or_digest: 46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e
    quant: unrecorded
    licence: unrecorded
    engine_version: "0.35.1"
    thinking_level: "off"
    num_predict: 32
    num_ctx: 4096
    batch: null
    prompt: "The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. The switchyard counts the same cars on every pass. AMU_CANARY_PROMPT_7c1e"
    measure: decode_tok_s
pairs:
  - id: companion-traced
    alone: solo
    paired: with-companion-on
  - id: companion-untraced
    alone: solo
    paired: with-companion-off
```

## The driver: scripts/relay_s1.py

```python
"""interlock-relay, stage 1: the driver for the 5090 runs. Nothing here runs without the Publisher's grant.

    uv run --extra relay python scripts/relay_s1.py --grant <id> --prefix relay-s1-<date> [--steps ...]

Steps, in order, each refusing before any model call when the preflight fails:

- ``decode``, ``long``, ``unload``, ``companion``: ``interlock run experiments/relay-s1/<step>.yaml --trace relay``,
  in this process, under a counter of the HTTP requests the Ollama adapter sends (below the hook: H1's ground truth).
  Supervisor health checks aren't counted, by the design's definition. Each step writes ``logs/<id>.http.json``.
- ``stop``: the decode spec in a child process, stopped through ``receipts/<id>.stop`` after a delay. The run's
  watcher ends that process with ``os._exit``, so it can't run in this one. Exit 77 is the expected end.
- ``import``: the process-level import check. There are 15 triples of child processes, in the order no import,
  idle import, no import. Each child makes 1 warm-up and 3 measured calls with the decode spec's untraced arm, and
  the idle-import child imports ``nemo_relay`` first. The output is ``logs/<prefix>-import.json``.

Afterwards ``interlock check`` runs, and ``logs/<prefix>.driver.json`` records the preflight, every step's exit,
the check, and the host, user and home strings that the analysis must not find in a trace. The analysis is
``experiments/interlock-relay/stage1/analyze.py`` in mcp-tool-shop-org/rnd, frozen before the run.
"""

from __future__ import annotations

import argparse
import contextlib
import http.client
import importlib.metadata
import json
import os
import socket
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

STEPS = ("decode", "long", "unload", "companion", "stop", "import")
SPEC_DIR = Path("experiments/relay-s1")
RELAY_VERSION = "0.10.1"
OLLAMA_VERSION = "0.35.1"
IDLE_VRAM_MIB = 2400
IMPORT_TRIPLES = 15
STOP_AFTER_S = 60.0
EXIT_OPERATOR_STOP = 77


class PreflightError(RuntimeError):
    """One preflight item failed. The run stops before any model call."""


# -- the counter below the hook ---------------------------------------------------------------------------------------


_ADAPTER_FILE = os.path.join("interlock", "adapters", "ollama.py")


@contextlib.contextmanager
def count_adapter_requests():
    """Count every ``http.client`` request sent from the Ollama adapter's transport, by path. Requests from anywhere
    else (the supervisor's health checks) aren't counted."""

    counts: dict[str, int] = {}
    lock = threading.Lock()
    original = http.client.HTTPConnection.request

    def counted(self, method, url, *args, **kwargs):
        if any(_ADAPTER_FILE in frame.filename for frame in traceback.extract_stack()):
            path = url.split("?", 1)[0]
            with lock:
                counts[path] = counts.get(path, 0) + 1
        return original(self, method, url, *args, **kwargs)

    http.client.HTTPConnection.request = counted
    try:
        yield counts
    finally:
        http.client.HTTPConnection.request = original


# -- the preflight ----------------------------------------------------------------------------------------------------


class Seams:
    """Every outside read the preflight makes. The defaults are the live ones; tests pass their own."""

    def environ(self) -> dict:
        return dict(os.environ)

    def version(self, package: str) -> str | None:
        try:
            return importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            return None

    def relay_config_paths(self) -> list:
        from nemo_relay import plugin

        report = plugin.validate({"version": 1, "components": []})
        return list(report.get("config_paths") or [])

    def git(self, root: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)  # noqa: S603, S607

    def ollama(self, path: str) -> dict:
        conn = http.client.HTTPConnection("127.0.0.1", 11434, timeout=5)
        try:
            conn.request("GET", path)
            return json.loads(conn.getresponse().read().decode("utf-8"))
        finally:
            conn.close()

    def gpu(self) -> dict:
        def query(args: list[str]) -> str:
            return subprocess.run(["nvidia-smi", *args], capture_output=True, text=True, check=True).stdout  # noqa: S603, S607

        used = query(["--query-gpu=memory.used", "--format=csv,noheader,nounits"]).strip().splitlines()
        apps = [line for line in query(["--query-compute-apps=pid", "--format=csv,noheader"]).splitlines() if line]
        return {"used_mib": int(used[0]), "compute_apps": len(apps)}

    def listeners(self, port: int) -> int:
        import psutil

        return sum(1 for c in psutil.net_connections(kind="tcp") if c.status == "LISTEN" and c.laddr.port == port)

    def heartbeat_age_s(self) -> float:
        from interlock.guards import heartbeat_age_s
        from interlock.harness.runner import heartbeat_path

        return heartbeat_age_s(heartbeat_path(None), time.time())


def preflight(root: Path, grant: str | None, seams: Seams, *, first: bool = True) -> dict:
    """Every item, in order. The first failure raises before any model call. Returns what was read.

    Before the first step the whole tree must be clean. Before a later step, everything but ``receipts/`` and
    ``table/`` must be, since the steps before it wrote their receipts there."""

    from interlock.guards import HEARTBEAT_MAX_AGE_S

    facts: dict = {}

    def need(ok: bool, message: str) -> None:
        if not ok:
            raise PreflightError(f"REFUSED: {message}")

    need(bool(grant), "no grant: the Publisher grants the 5090 for this run")
    age = seams.heartbeat_age_s()
    need(age <= HEARTBEAT_MAX_AGE_S, f"the watchdog heartbeat is {age:.0f}s old")
    facts["heartbeat_age_s"] = round(age, 1)
    otel = sorted(k for k in seams.environ() if k.startswith("OTEL_"))
    need(not otel, f"OTEL variables are set: {', '.join(otel)}")
    relay = seams.version("nemo-relay")
    need(relay == RELAY_VERSION, f"nemo-relay is {relay}, not {RELAY_VERSION} (install interlock[relay])")
    facts["nemo_relay"] = relay
    layered = seams.relay_config_paths()
    need(not layered, f"Relay would layer in {layered}")
    scope = ["--", "."] if first else ["--", ".", ":!receipts", ":!table"]
    status = seams.git(root, "status", "--porcelain", *scope).stdout.strip()
    need(not status, "the interlock tree is not clean" + ("" if first else " outside receipts/ and table/"))
    ignored = seams.git(root, "check-ignore", "-q", "logs/relay-s1-probe").returncode == 0
    need(ignored, "logs/ is not git-ignored")
    facts["git_sha"] = seams.git(root, "rev-parse", "HEAD").stdout.strip()
    version = (seams.ollama("/api/version") or {}).get("version")
    need(version == OLLAMA_VERSION, f"Ollama on 11434 is {version}, not {OLLAMA_VERSION}")
    facts["ollama_version"] = version
    loaded = (seams.ollama("/api/ps") or {}).get("models") or []
    need(not loaded, f"{len(loaded)} model(s) already on the card")
    listeners = seams.listeners(11434)
    need(listeners == 1, f"{listeners} listeners on 11434; the supervisor needs exactly one")
    gpu = seams.gpu()
    need(gpu["compute_apps"] == 0, f"{gpu['compute_apps']} other process(es) on the GPU")
    need(gpu["used_mib"] <= IDLE_VRAM_MIB,
         f"{gpu['used_mib']} MiB in use; the idle baseline is at most {IDLE_VRAM_MIB}")
    facts["idle_vram_mib"] = gpu["used_mib"]
    return facts


# -- the steps --------------------------------------------------------------------------------------------------------


def run_step(step: str, prefix: str, grant: str, root: Path, main=None) -> dict:
    """One traced interlock run in this process, under the request counter."""

    if main is None:
        from interlock.cli import main
    run_id = f"{prefix}-{step}"
    argv = ["run", str(SPEC_DIR / f"{step}.yaml"), "--root", str(root), "--grant", grant, "--trace", "relay",
            "--run-id", run_id]
    with count_adapter_requests() as counts:
        code = main(argv)
    (root / "logs").mkdir(exist_ok=True)
    record = {"run_id": run_id, "exit": code, "adapter_requests": sum(counts.values()), "by_path": counts}
    (root / "logs" / f"{run_id}.http.json").write_text(json.dumps(record, indent=1, sort_keys=True) + "\n",
                                                       encoding="utf-8")
    return record


def run_stop(prefix: str, grant: str, root: Path, *, after_s: float = STOP_AFTER_S, popen=subprocess.Popen,
             sleep=time.sleep) -> dict:
    """The decode spec in a child process, stopped through its stop file."""

    run_id = f"{prefix}-stop"
    argv = [sys.executable, "-m", "interlock", "run", str(SPEC_DIR / "decode.yaml"), "--root", str(root), "--grant",
            grant, "--trace", "relay", "--run-id", run_id]
    proc = popen(argv, cwd=root)
    sleep(after_s)
    stop = root / "receipts" / f"{run_id}.stop"
    stop.parent.mkdir(exist_ok=True)
    stop.write_text("interlock-relay stage 1: the stop-file run\n", encoding="utf-8")
    code = proc.wait(timeout=600)
    return {"run_id": run_id, "exit": code, "expected_exit": EXIT_OPERATOR_STOP, "stopped": code == EXIT_OPERATOR_STOP}


CHILD = r'''
import json, statistics, sys, time
started = time.perf_counter()
args = json.loads(sys.argv[1])
import_s = None
if args["idle_import"]:
    t = time.perf_counter()
    import nemo_relay  # noqa: F401  # idle: imported, never initialised
    import_s = time.perf_counter() - t
import yaml
from interlock.adapters.base import StepRequest
from interlock.adapters.ollama import OllamaAdapter
spec = yaml.safe_load(open(args["spec"], encoding="utf-8"))
arm = next(a for a in spec["arms"] if a["id"] == args["arm"])
keys = ("thinking_level", "num_predict", "num_ctx", "prompt", "keep_alive", "temperature")
request = StepRequest(step_id=arm["id"], task=arm["task"], model=arm["model"], device=arm["device"],
                      engine=arm["engine"], settings={k: arm.get(k) for k in keys})
adapter = OllamaAdapter(device=arm["device"])
ready_s = time.perf_counter() - started
metrics = {"latency_ms": [], "decode_tok_s": [], "prompt_tok_s": []}
for i in range(1 + args["calls"]):
    result = adapter.run(request)
    if not result.ok:
        print(json.dumps({"error": result.error}))
        sys.exit(2)
    if i == 0:
        continue  # the warm-up
    metrics["latency_ms"].append(result.latency_ms)
    metrics["decode_tok_s"].append(result.throughput)
    metrics["prompt_tok_s"].append(result.prompt_tok_s)
print(json.dumps({"metrics": metrics, "import_s": import_s, "ready_s": ready_s}))
'''


def _child(root: Path, *, idle_import: bool, calls: int = 3) -> dict:
    args = {"idle_import": idle_import, "calls": calls, "spec": str(SPEC_DIR / "decode.yaml"), "arm": "decode-off"}
    done = subprocess.run([sys.executable, "-c", CHILD, json.dumps(args)], cwd=root, capture_output=True,  # noqa: S603
                          text=True, check=False, timeout=600)
    if done.returncode != 0:
        raise RuntimeError(f"import-check child failed ({done.returncode}): {done.stdout.strip()} {done.stderr[-400:]}")
    return json.loads(done.stdout.strip().splitlines()[-1])


def run_import(prefix: str, root: Path, *, triples: int = IMPORT_TRIPLES, child=_child, between=None) -> dict:
    """15 triples of processes: no import, idle import, no import. ``between`` runs before each child (the
    heartbeat re-check in the live driver)."""

    record = {"triples": []}
    for _ in range(triples):
        triple = {}
        for side, idle in (("no_import_before", False), ("idle_import", True), ("no_import_after", False)):
            if between is not None:
                between()
            triple[side] = child(root, idle_import=idle)
        record["triples"].append(triple)
    (root / "logs").mkdir(exist_ok=True)
    (root / "logs" / f"{prefix}-import.json").write_text(json.dumps(record, indent=1, sort_keys=True) + "\n",
                                                         encoding="utf-8")
    return {"triples": len(record["triples"])}


# -- the whole run ----------------------------------------------------------------------------------------------------


def drive(root: Path, grant: str, prefix: str, steps: tuple[str, ...], *, seams: Seams | None = None, main=None,
          stop=run_stop, imports=run_import) -> dict:
    seams = seams or Seams()
    if main is None:
        from interlock.cli import main
    out: dict = {"prefix": prefix, "steps": {}, "needles": {
        "host": socket.gethostname(), "user": os.environ.get("USERNAME") or os.environ.get("USER") or "",
        "home": str(Path.home())}}
    out["preflight"] = preflight(root, grant, seams)
    try:
        for step in steps:
            if step not in STEPS:
                raise PreflightError(f"REFUSED: unknown step {step}")
            if step != STEPS[0]:
                preflight(root, grant, seams, first=False)  # the card is idle again; nothing else changed
            if step == "stop":
                out["steps"][step] = stop(prefix, grant, root)
            elif step == "import":
                def recheck():
                    age = seams.heartbeat_age_s()
                    from interlock.guards import HEARTBEAT_MAX_AGE_S

                    if age > HEARTBEAT_MAX_AGE_S:
                        raise PreflightError(f"REFUSED: the watchdog heartbeat is {age:.0f}s old")

                out["steps"][step] = imports(prefix, root, between=recheck)
            else:
                out["steps"][step] = run_step(step, prefix, grant, root, main=main)
                if out["steps"][step]["exit"] != 0:
                    raise PreflightError(f"REFUSED: step {step} exited {out['steps'][step]['exit']}; the run stops")
    finally:
        out["check_passed"] = main(["check", "--root", str(root)]) == 0
        (root / "logs").mkdir(exist_ok=True)
        (root / "logs" / f"{prefix}.driver.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n",
                                                             encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--grant", required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--steps", default=",".join(STEPS))
    args = parser.parse_args(argv)
    try:
        drive(args.root.resolve(), args.grant, args.prefix, tuple(s for s in args.steps.split(",") if s))
    except PreflightError as exc:
        print(exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## The harness diff since the stage 0 code (interlock 95d6844 to 4295165, src only)

```diff
diff --git a/src/interlock/adapters/openvino.py b/src/interlock/adapters/openvino.py
index 2e3c4e4..60249fe 100644
--- a/src/interlock/adapters/openvino.py
+++ b/src/interlock/adapters/openvino.py
@@ -592,17 +592,24 @@ def _timed_call(fn, timeout_s: float, *, kind: str = "generate", model: str | No
     tracer = _TRACER
     if tracer is None:
         return _bounded_call(fn, timeout_s)
+    entered = time.perf_counter_ns()
     record = tracer.start(kind, f"openvino/{kind}", model=model, device=device)
     status = "exception"
+    sent = time.perf_counter_ns()
+    returned = sent
     try:
         result = _bounded_call(fn, timeout_s)
+        returned = time.perf_counter_ns()
         # _bounded_call returns ("ok", value) or ("hang", None), or re-raises. Anything else is not called ok.
         status = {"ok": "ok", "hang": "timeout"}.get(result[0], "exception")
         if status == "timeout":
             record.extra["worker_still_running"] = True
         return result
     finally:
+        if returned == sent:
+            returned = time.perf_counter_ns()
         tracer.end(record, status)
+        tracer.charge(record, (sent - entered) + (time.perf_counter_ns() - returned))
 
 
 def _bounded_call(fn, timeout_s: float):
diff --git a/src/interlock/calltrace.py b/src/interlock/calltrace.py
index 02bf0b3..8a7d7a9 100644
--- a/src/interlock/calltrace.py
+++ b/src/interlock/calltrace.py
@@ -25,6 +25,7 @@ from __future__ import annotations
 import itertools
 import json
 import os
+import sys
 import threading
 import time
 from contextlib import contextmanager
@@ -86,6 +87,7 @@ class CallRecord:
     completion_tokens: int | None = None
     request_bytes: int = 0
     extra: dict = field(default_factory=dict)
+    emitted: bool = False
 
     @property
     def ms(self) -> float | None:
@@ -164,6 +166,9 @@ class Tracer:
         # Every sink call happens under self._lock (the lock order is always tracer, then sink), so a watcher
         # close can't land between a call's count and its sink event (Argon round 2, M-New-1).
         self._closed = False
+        # Stage 1's off-on-off triples switch the sink's events per slot. The counter stays on (design v3.1).
+        self._emit = True
+        self._slot_overhead_ns = 0
         self._offset_ns = 0
         self.trace_file: str | None = None
         self.scope_id: str | None = None
@@ -209,6 +214,19 @@ class Tracer:
             if self._sink is not None:
                 sink, self._sink = self._sink, None
                 sink.close(self.now_ns())
+                self._write_calls()
+
+    def _write_calls(self) -> None:
+        """Every count, run-level calls included, beside the trace: ``logs/<run_id>.calls.json``. A receipt row
+        carries only its own arm's counts, and stage 1's H1 check compares the whole table with an independent
+        count of requests."""
+
+        try:
+            path = self.root / "logs" / f"{self.run_id}.calls.json"
+            path.write_text(json.dumps({"run_id": self.run_id, "mode": self.mode, "counts": self._counts},
+                                       indent=1, sort_keys=True) + "\n", encoding="utf-8")
+        except OSError as exc:  # the trace is already closed; a missing summary is reported, not fatal
+            print(f"interlock: could not write the call summary: {exc}", file=sys.stderr)
 
     def __enter__(self) -> Tracer:
         return self.open()
@@ -231,19 +249,34 @@ class Tracer:
 
     # -- slots and rows ---------------------------------------------------------
 
+    @property
+    def emitting(self) -> bool:
+        return self._emit and self._sink is not None
+
+    def set_emitting(self, on: bool) -> None:
+        """Turn the sink's call events on or off for the calls that start from now. A call keeps the choice it
+        started with, so no start is ever left without its end."""
+
+        with self._lock:
+            self._emit = bool(on)
+
     def begin_slot(self, **slot) -> None:
         with self._lock:
             self._slot = dict(slot)
             self._slot_calls = []
+            self._slot_overhead_ns = 0
 
     def end_slot(self) -> dict:
-        """The slot's calls: their ids, and the measured call's id."""
+        """The slot's calls, and the client time the hooks spent on them (the tracer's own bookkeeping and its
+        sink, in microseconds): stage 1's client-time gate compares this between traced and untraced slots."""
 
         with self._lock:
             calls = list(self._slot_calls)
+            overhead_us = round(self._slot_overhead_ns / 1000, 3)
             self._slot = {}
             self._slot_calls = []
-        return {"call_ids": calls}
+            self._slot_overhead_ns = 0
+        return {"call_ids": calls, "hook_us": overhead_us}
 
     def counts_for(self, arm_id: str) -> dict:
         """``artifacts.call_counts`` for one arm's row."""
@@ -273,10 +306,18 @@ class Tracer:
             if self._slot:
                 self._slot_calls.append(record.call_id)
                 record.extra = {"arm": self._slot.get("arm"), "slot": self._slot.get("index")}
-            if self._sink is not None:
+            if self._sink is not None and self._emit:
+                record.emitted = True
                 self._sink.start(record)
         return record
 
+    def charge(self, record: CallRecord, hook_ns: int) -> None:
+        """Add a call's hook time (everything its hook did outside the model call) to the slot it started in."""
+
+        with self._lock:
+            if self._slot and record.extra.get("slot") == self._slot.get("index"):
+                self._slot_overhead_ns += hook_ns
+
     def end(self, record: CallRecord, status: str, payload: object = None) -> None:
         record.end_ns = self.now_ns()
         record.status = status
@@ -298,7 +339,7 @@ class Tracer:
             entry["timeouts"] += 1
         elif record.status != "ok":
             entry["errors"] += 1
-        if self._sink is not None:
+        if self._sink is not None and record.emitted:
             self._sink.end(record)
 
     @contextmanager
@@ -336,22 +377,29 @@ class _TracedTransport:
         return getattr(self.__wrapped__, name)
 
     def __call__(self, method: str, url: str, body: dict | None, *args, **kwargs):
+        entered = time.perf_counter_ns()
         tracer = self._tracer
         kind = classify(method, url, body)
         model = body.get("model") if isinstance(body, dict) else None
         # Only Relay's request record uses the size. Serialising a long prompt again costs measured time.
-        size = len(json.dumps(body)) if body is not None and tracer.mode == "relay" else 0
+        size = len(json.dumps(body)) if body is not None and tracer.mode == "relay" and tracer.emitting else 0
         record = tracer.start(kind, urlsplit(url).path, model=model, device=self._device, request_bytes=size)
         status, payload = "exception", None
+        sent = time.perf_counter_ns()
+        returned = sent
         try:
             payload = self.__wrapped__(method, url, body, *args, **kwargs)
+            returned = time.perf_counter_ns()
             status = "ok"
             return payload
         except Exception as exc:
+            returned = time.perf_counter_ns()
             status = "timeout" if isinstance(exc, TimeoutError) or "timed out" in str(exc).lower() else "http_error"
             raise
         finally:
             tracer.end(record, status, payload)
+            # Hook time: before the request went out, and after it came back.
+            tracer.charge(record, (sent - entered) + (time.perf_counter_ns() - returned))
 
 
 def traced_transport(transport, tracer: Tracer, *, device: str | None = None):
diff --git a/src/interlock/harness/runner.py b/src/interlock/harness/runner.py
index 6416902..91c4e3c 100644
--- a/src/interlock/harness/runner.py
+++ b/src/interlock/harness/runner.py
@@ -457,6 +457,11 @@ def run_interleaved(
     wall = wall or time.time
     started_at = wall()
     hooks = watch or WatchHooks()
+    per_arm_trace = any("trace" in arm for arm in spec.get("arms") or [])
+    if per_arm_trace and tracer is not None:
+        tracer.set_emitting(False)  # only a traced arm's slots reach the trace; nothing between slots does
+    barrier_ms = spec.get("trace_barrier_ms") or 0
+    salts: dict[str, int] = {}
     tracker = CompileTracker(hooks.clock)
     state_lock = threading.RLock()  # the main loop's mutations and the watcher's flush
     halted_by_watch = False
@@ -922,21 +927,28 @@ def run_interleaved(
                     adapter._slot_probe = probe
                     probe.open()
                 if tracer is not None:
-                    tracer.begin_slot(arm=arm["id"], index=f"{slot.phase}:{slot.round_index}:{slot.role}")
+                    pair_tag = f":{slot.pair}" if slot.pair else ""
+                    tracer.begin_slot(arm=arm["id"], index=f"{slot.phase}:{slot.round_index}:{slot.role}{pair_tag}")
+                    if per_arm_trace:
+                        tracer.set_emitting(arm.get("trace") is True)
                 slot_calls = None
                 try:
                     kind = "ok"
                     error = ""
                     try:
                         result = adapter.run(
-                            _request(
+                            _salted(
                                 arm,
-                                spec,
-                                spec_rel,
-                                cache_dirs.get(arm["id"]),
-                                adapters[arm["engine"]],
-                                prompt_cache,
-                                bound_s=bound,
+                                salts,
+                                _request(
+                                    arm,
+                                    spec,
+                                    spec_rel,
+                                    cache_dirs.get(arm["id"]),
+                                    adapters[arm["engine"]],
+                                    prompt_cache,
+                                    bound_s=bound,
+                                ),
                             )
                         )
                     except AdapterError as exc:
@@ -1031,6 +1043,11 @@ def run_interleaved(
                             if tracer is not None:
                                 slot_calls = tracer.end_slot()
                                 sample["call_ids"] = slot_calls["call_ids"]
+                                sample["hook_us"] = slot_calls["hook_us"]
+                                if per_arm_trace:
+                                    sample["traced"] = arm.get("trace") is True
+                            if arm.get("prompt_salt") == "per_call":
+                                sample["prompt_salt"] = salts[arm["id"]]
                             if epoch is not None:
                                 try:
                                     sample = supervisor.keep_sample(epoch, sample)
@@ -1093,6 +1110,13 @@ def run_interleaved(
                     # attributed to it (Argon I1). The success path has already taken its call ids.
                     if tracer is not None and slot_calls is None:
                         tracer.end_slot()
+                    if tracer is not None and per_arm_trace:
+                        tracer.set_emitting(False)
+                    # Stage 1's barrier, after every slot in both arms: the trace flushed, a collection, a fixed rest.
+                    if tracer is not None and barrier_ms:
+                        tracer.flush()
+                        gc.collect()
+                        hooks.sleep(barrier_ms / 1000)
                 if pending is not None:
                     _resume_after_repair(slot, block_id, arm, pending[0], pending[1])
         finally:
@@ -1453,6 +1477,27 @@ def _request(
     )
 
 
+def _salted(arm: dict, salts: dict[str, int], request: StepRequest) -> StepRequest:
+    """``prompt_salt: per_call``: each call's prompt starts with its own number, so the server's prompt cache
+    can't reuse the previous call's prefill. The number is kept on the sample."""
+
+    if arm.get("prompt_salt") != "per_call":
+        return request
+    # One counter for the run, not per arm: the two arms of a trace contrast send the same prompt otherwise.
+    salts["_run"] = salts.get("_run", 0) + 1
+    salts[arm["id"]] = salts["_run"]
+    settings = dict(request.settings)
+    settings["prompt"] = f"[{salts['_run']}] " + str(settings.get("prompt") or "")
+    return StepRequest(
+        step_id=request.step_id,
+        task=request.task,
+        model=request.model,
+        device=request.device,
+        engine=request.engine,
+        settings=settings,
+    )
+
+
 def _record(
     slot: Slot,
     result,
@@ -1543,6 +1588,9 @@ def _artifacts(records: list[dict], arm_id: str) -> dict | None:
             item["bound_s"] = row["bound_s"]
         if row.get("call_ids"):
             item["call_ids"] = row["call_ids"]
+        for key in ("hook_us", "traced", "prompt_salt"):  # interlock-relay stage 1
+            if row.get(key) is not None:
+                item[key] = row[key]
         if row.get("cpu") is not None:
             item["cpu"] = row["cpu"]
         if row.get("sample"):
@@ -2145,6 +2193,9 @@ def run_spec(
         if spec.get("procedure") != "fill-card":
             raise RunnerError("--models is for a fill-card spec")
         _chosen, recorded_models = resolve_models(spec, models)
+    if trace == "off" and any("trace" in arm for arm in spec.get("arms") or [] if isinstance(arm, dict)):
+        # A spec that switches tracing per arm would run both arms untraced: the comparison would be empty.
+        raise RunnerError("REFUSED: this spec traces some arms and not others; run it with --trace relay or events")
     if trace != "off" and spec.get("id") == "E4b":
         # E4b's model calls go through its own injected seams, not the hook points. A trace that would silently
         # record nothing is refused instead (interlock-relay amendment A3).
diff --git a/src/interlock/harness/spec.py b/src/interlock/harness/spec.py
index 7632cc9..d6030ae 100644
--- a/src/interlock/harness/spec.py
+++ b/src/interlock/harness/spec.py
@@ -151,6 +151,14 @@ def _interleaved(data: dict) -> None:
             # needs its own prompt, or a dataset seed and target the harness builds one from.
             raise SpecError(f"generate arm {arm['id']} has no prompt")
         _arm_storage(arm)
+        # interlock-relay stage 1: an arm traced or not, and a distinct prompt start per call.
+        if "trace" in arm and not isinstance(arm["trace"], bool):
+            raise SpecError(f"arm {arm['id']} trace must be true or false")
+        if arm.get("prompt_salt") not in (None, "per_call"):
+            raise SpecError(f"arm {arm['id']} prompt_salt must be per_call")
+    barrier = data.get("trace_barrier_ms")
+    if barrier is not None and (isinstance(barrier, bool) or not isinstance(barrier, int) or not 0 <= barrier <= 5000):
+        raise SpecError("trace_barrier_ms must be an integer from 0 to 5000")
     for arm in arms:
         companion = arm.get("companion")
         if companion is not None and companion not in seen:
@@ -350,6 +358,10 @@ def _pairs(data: dict, arm_ids: set) -> None:
         if alone not in arm_ids or paired_id not in arm_ids:
             raise SpecError("a pair names an arm that is not in the spec")
         paired = arms[paired_id]
+        contrast = pair.get("contrast")
+        if contrast is not None:
+            _trace_contrast(pair["id"], contrast, arms[alone], paired)
+            continue
         companion = paired.get("companion")
         if companion not in arm_ids:
             raise SpecError(f"paired arm {paired_id} needs a companion arm")
@@ -360,6 +372,22 @@ def _pairs(data: dict, arm_ids: set) -> None:
             raise SpecError(f"arm {paired_id} companion_device does not match the companion arm")
 
 
+def _trace_contrast(pair_id: str, contrast: object, alone: dict, paired: dict) -> None:
+    """``contrast: trace`` (interlock-relay stage 1): the paired slot is the alone arm with tracing on.
+
+    No companion runs. The two arms are the same in every key but their id and ``trace``, which is off for the
+    alone arm and on for the paired one, so the only thing an off-on-off triple changes is the trace."""
+
+    if contrast != "trace":
+        raise SpecError(f"pair {pair_id} contrast must be trace")
+    if alone.get("trace") is not False or paired.get("trace") is not True:
+        raise SpecError(f"pair {pair_id}: the alone arm needs trace false and the paired arm trace true")
+    keys = (set(alone) | set(paired)) - {"id", "trace"}
+    differ = sorted(key for key in keys if alone.get(key) != paired.get(key))
+    if differ:
+        raise SpecError(f"pair {pair_id}: a trace contrast's arms differ in {', '.join(differ)}")
+
+
 def _close(got: object, expected: float, where: str) -> None:
     if isinstance(got, bool) or not isinstance(got, (int, float)) or not math.isclose(float(got), expected):
         raise SpecError(f"{where} is {expected}")
```

## The stage 1 tests

```python
"""Stage 1 of the interlock-relay design, on fakes: the off-on-off triples on interlock's own ABA order.

Arm A and arm B are the same model and settings. B is traced (``trace: true``), A isn't. The tracer switches the
sink's events per slot and the counter stays on. After every slot both arms take the same barrier. No device is used:
the Ollama adapter talks to a fake transport.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from interlock.adapters.ollama import OllamaAdapter
from interlock.calltrace import Tracer
from interlock.harness.runner import RunnerError, run_spec
from interlock.harness.spec import SpecError, validate_spec
from interlock.harness.watch import WatchHooks
from interlock.receipt import check_tree, load_jsonl
from tests.test_run_path import _bind

MODES = ["events", pytest.param("relay", marks=pytest.mark.relay)]


def _need(mode):
    if mode == "relay":
        pytest.importorskip("nemo_relay")


class Server:
    """A fake Ollama: answers show, generate and unload, and logs every request (the H1 ground truth)."""

    def __init__(self):
        self.requests = []

    def __call__(self, method, url, body=None, **kwargs):
        self.requests.append((url.rsplit("/api/", 1)[-1], dict(body or {})))
        if url.endswith("/api/show"):
            return {"model_info": {"qwen3.context_length": 40960}, "details": {"quantization_level": "Q4_K_M"}}
        if body and body.get("keep_alive") == 0 and body.get("prompt") == "":
            return {"done": True}
        return {"response": "ok", "total_duration": 450_000_000, "eval_count": 64, "eval_duration": 320_000_000,
                "prompt_eval_count": 256, "prompt_eval_duration": 30_000_000, "load_duration": 1_000_000}


def _arm(arm_id, *, trace, salt=False):
    arm = {
        "id": arm_id, "task": "generate", "device": "CPU", "engine": "ollama", "model": "qwen3:8b",
        "revision_or_digest": "abc", "quant": "unrecorded", "licence": "unrecorded", "engine_version": "0.35.1",
        "thinking_level": "off", "num_predict": 64, "num_ctx": 4096, "batch": None,
        "prompt": "The switchyard counts the same cars on every pass.", "measure": "decode_tok_s", "trace": trace,
    }
    if salt:
        arm["prompt_salt"] = "per_call"
    return arm


def _spec(*, repeats=3, barrier=250, salt=False):
    return {
        "id": "RELAY-S1-T", "procedure": "interleaved", "order": "aba",
        "question": "Does tracing a call change what interlock measures?",
        "decision": "A test verdict, computed after the run.",
        "needs": {"grant": False, "npu_session": False, "cpu_window": False},
        "stop_rules": ["a failed step stops the sequence"], "dataset": {"name": "fixture"},
        "metrics": ["decode_tok_s", "latency_ms"], "warmups": 1, "repeats": repeats, "band": 0.1,
        "compile_cache": "reuse", "rest_s": 0, "trace_barrier_ms": barrier,
        "arms": [_arm("A", trace=False, salt=salt), _arm("B", trace=True, salt=salt)],
        "pairs": [{"id": "relay", "alone": "A", "paired": "B", "contrast": "trace"}],
    }


def _run(tmp_path, mode, *, slept=None, salt=False, run_id="s1"):
    server = Server()
    repo = tmp_path / "repo"
    spec_path = _bind(repo, _spec(salt=salt))
    hooks = WatchHooks(ram_sampler=None, start_thread=False,
                       sleep=(slept.append if slept is not None else (lambda s: None)))
    rows = run_spec(spec_path, root=repo, adapters={"ollama": OllamaAdapter(transport=server)},
                    date="2026-10-14", run_id=run_id, trace=mode, watch=hooks)
    return repo, rows, server


def _slots(repo, run_id="s1"):
    rows = load_jsonl(repo / "receipts" / f"{run_id}.jsonl")
    return {row["id"].split("/")[1]: row["artifacts"]["slots"] for row in rows}


@pytest.mark.parametrize("mode", MODES)
def test_only_the_traced_arms_calls_reach_the_trace_and_every_call_is_counted(tmp_path: Path, mode):
    _need(mode)
    repo, rows, server = _run(tmp_path, mode)
    assert check_tree(repo) == []
    slots = _slots(repo)
    a_ids = {i for s in slots["A"] for i in s["call_ids"]}
    b_ids = {i for s in slots["B"] for i in s["call_ids"]}
    assert all(s["traced"] is False for s in slots["A"]) and all(s["traced"] is True for s in slots["B"])
    text = next((repo / "logs").glob("s1.*.jsonl")).read_text(encoding="utf-8")
    lines = [json.loads(x) for x in text.splitlines()]
    if mode == "events":
        logged = {x["call_id"] for x in lines if "call_id" in x}
    else:
        llm = [x for x in lines if x.get("category") == "llm"]
        starts = {x["metadata"]["call_id"] for x in llm if x["scope_category"] == "start"}
        ends = {x["metadata"]["call_id"] for x in llm if x["scope_category"] == "end"}
        assert starts == ends  # no start without its end
        logged = starts
    assert b_ids and logged == b_ids  # exactly the traced slots' calls: nothing from A, nothing between slots
    assert not (a_ids & logged)
    # H1's table: every request the server saw is counted, run-level calls included, in logs/<run_id>.calls.json.
    table = json.loads((repo / "logs" / "s1.calls.json").read_text(encoding="utf-8"))["counts"]
    assert sum(v["n"] for kinds in table.values() for v in kinds.values()) == len(server.requests)
    assert sum(v["n"] for row in rows for v in row["artifacts"]["call_counts"].values()) == sum(
        v["n"] for arm, kinds in table.items() if arm != "_run" for v in kinds.values())


@pytest.mark.parametrize("mode", MODES)
def test_every_slot_takes_the_barrier_and_records_its_hook_time(tmp_path: Path, mode):
    _need(mode)
    slept = []
    repo, _rows, _server = _run(tmp_path, mode, slept=slept)
    slots = _slots(repo)
    measured = len(slots["A"]) + len(slots["B"])
    assert slept.count(0.25) == measured  # one barrier after every slot, in both arms
    for arm_slots in slots.values():
        assert all(isinstance(s["hook_us"], float) and s["hook_us"] >= 0 for s in arm_slots)


def test_the_aba_order_gives_off_on_off_triples(tmp_path: Path):
    repo, _rows, _server = _run(tmp_path, "events")
    slots = _slots(repo)
    rounds = {}
    for arm_id, arm_slots in slots.items():
        for s in arm_slots:
            if s["phase"] == "repeat":
                rounds.setdefault(s["round"], {})[s["role"]] = (arm_id, s["traced"])
    assert len(rounds) == 3
    for roles in rounds.values():
        assert roles == {"alone-before": ("A", False), "paired": ("B", True), "alone-after": ("A", False)}


def test_a_salted_arm_sends_a_distinct_prompt_start_on_every_call(tmp_path: Path):
    repo, _rows, server = _run(tmp_path, "events", salt=True)
    prompts = [body["prompt"] for path, body in server.requests if path == "generate" and body.get("prompt")]
    assert len(prompts) == len(set(prompts)) > 4
    assert all(p.startswith("[") for p in prompts)
    salts = [s["prompt_salt"] for arm_slots in _slots(repo).values() for s in arm_slots]
    assert len(salts) == len(set(salts))  # one number per call, across both arms


def test_a_spec_with_traced_arms_refuses_to_run_untraced(tmp_path: Path):
    repo = tmp_path / "repo"
    spec_path = _bind(repo, _spec())
    with pytest.raises(RunnerError, match="traces some arms"):
        run_spec(spec_path, root=repo, adapters={"ollama": OllamaAdapter(transport=Server())}, date="2026-10-14",
                 trace="off")
    assert not (repo / "receipts").exists()


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda s: s["arms"][0].update(trace="yes"), "trace must be true or false"),
        (lambda s: s["arms"][0].update(prompt_salt="sometimes"), "prompt_salt must be per_call"),
        (lambda s: s.update(trace_barrier_ms=-1), "trace_barrier_ms"),
        (lambda s: s.update(trace_barrier_ms=True), "trace_barrier_ms"),
        (lambda s: s["arms"][1].update(num_predict=128), "differ in num_predict"),
        (lambda s: s["arms"][1].update(trace=False), "paired arm trace true"),
        (lambda s: s["pairs"][0].update(contrast="companion"), "contrast must be trace"),
    ],
)
def test_the_stage_1_spec_keys_are_checked(change, message):
    spec = _spec()
    change(spec)
    with pytest.raises(SpecError, match=message):
        validate_spec(spec)


def test_a_call_keeps_the_emission_it_started_with(tmp_path: Path):
    tracer = Tracer(root=tmp_path, run_id="sw", mode="events")
    with tracer:
        tracer.set_emitting(True)
        traced = tracer.start("generate", "/api/generate", model="m", device="5090")
        tracer.set_emitting(False)
        untraced = tracer.start("generate", "/api/generate", model="m", device="5090")
        tracer.end(traced, "ok")  # ends after the switch went off, and is still logged
        tracer.end(untraced, "ok")
        assert tracer.emitting is False
    lines = [json.loads(x) for x in (tmp_path / "logs" / "sw.events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [x["call_id"] for x in lines] == [traced.call_id]
    assert tracer.counts_for("_run")["generate"]["n"] == 2
```
