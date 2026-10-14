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
- **The barrier check (reported, not gated; S1-A6):** the median of the in-process decode A calls (with the
  barrier) against the median of the N processes' calls (no barrier), and whether they differ by at most the
  decode band for that metric.

**H1, per traced run:**
- **Request count:** the driver's count of HTTP requests the adapter sent (below the hook) = the sum of the run's
  call table (`logs/<id>.calls.json`).
- **Spans:** the trace's llm spans = the call ids of the traced slots, each with one start and one end.

**H3:**
- The trace parses, with no canary, host name, user name or home path, and the run scope opens and closes.
- The stop run's trace parses and is closed, and the driver recorded a real stop: the stop file was written
  mid-run and the run exited 77 (S1-A5).
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
- **S1-A5 (after Argon's stage 1 review, before any run):** a stop run that finished before its stop file was written
  would leave a normally closed trace and pass H3. H3 now also needs the driver's own record that the stop
  landed mid-run (exit 77). The driver waits for the trace to hold 10 model calls before it writes the stop file.
- **S1-A6 (after Argon's stage 1 review, before any run):** the barrier check is reported, not gated.
  - Both arms of every in-process triple take the same barrier, so a barrier-induced shift in the baseline
    can't bias Δ, and H2's verdict on Relay stands without it.
  - What the check measures is the protocol's own effect: the card's clocks after a 250 ms rest against
    back-to-back calls in a fresh process. Gating on it could reject Relay for a property of the measurement.
  - It's reported beside H2, so a reader knows the conditions the equivalence was shown under.
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
    holds = bool(measured) and all(v["verdict"] == "holds" for v in measured.values())
    return {"triples": len(trips), "metrics": metrics, "barrier_reported": barrier, "holds": holds}


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
            out["h1"][step] = out["h3"][step] = {"holds": None, "reason": "not run"}
            if step in ("decode", "long"):
                out["h2"][step] = {"holds": None, "reason": "not run"}
            continue
        out["h1"][step] = h1_run(trace, root / "logs" / f"{run_id}.calls.json", root / "logs" / f"{run_id}.http.json",
                                 rows)
        out["h3"][step] = h3_trace(trace, needles)
        if step in ("decode", "long"):
            out["h2"][step] = h2_run(rows, step)
    stop_trace = root / "logs" / f"{prefix}-stop.atof.jsonl"
    stopped = (driver.get("steps", {}).get("stop") or {}).get("stopped") is True
    if stop_trace.is_file():
        result = h3_trace(stop_trace, needles)
        result["checks"]["stopped_mid_run"] = stopped
        result["holds"] = all(result["checks"].values())
        out["h3"]["stop"] = result
    else:
        out["h3"]["stop"] = {"holds": None, "reason": "not run"}
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
