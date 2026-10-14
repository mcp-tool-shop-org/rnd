"""Tests for the frozen stage 1 analysis, on synthetic data. Run: python -m unittest test_analyze (in this folder)."""

from __future__ import annotations

import json
import random
import tempfile
import unittest
from pathlib import Path

import analyze as an


def _slot(arm_round, role, pair, latency, *, traced, hook_us=50.0, call_ids=()):
    return {"phase": "repeat", "round": arm_round, "role": role, "pair": pair, "latency_ms": latency,
            "throughput": 1000.0 / latency * 60, "prompt_tok_s": 8000.0, "sensors": {"dedicated_mib": 13600},
            "cpu": {"slot_end": {"cpu_percent": 8.0}}, "hook_us": hook_us, "traced": traced,
            "call_ids": list(call_ids)}


def _rows(n, *, shift=0.0, noise=0.02, seed=1, hook_b=80.0, pair="decode"):
    rng = random.Random(seed)
    a, b = [], []
    for i in range(n):
        base = 450 * (1 + rng.gauss(0, noise))
        a.append(_slot(i, "alone-before", pair, base * (1 + rng.gauss(0, noise)), traced=False))
        b.append(_slot(i, "paired", pair, base * (1 + shift) * (1 + rng.gauss(0, noise)), traced=True, hook_us=hook_b))
        a.append(_slot(i, "alone-after", pair, base * (1 + rng.gauss(0, noise)), traced=False))
    return [{"id": f"T/{pair}-off/r", "artifacts": {"slots": a}}, {"id": f"T/{pair}-on/r", "artifacts": {"slots": b}}]


class Statistics(unittest.TestCase):
    def test_t_quantiles_match_the_tables(self):
        for p, df, expected in ((0.95, 29, 1.6991), (0.95, 10, 1.8125), (0.975, 29, 2.0452), (0.95, 1, 6.3138)):
            self.assertAlmostEqual(an.t_quantile(p, df), expected, places=3)

    def test_percentile_interpolates(self):
        self.assertEqual(an.percentile([1, 2, 3, 4], 50), 2.5)
        self.assertEqual(an.percentile([5], 95), 5)


class H2(unittest.TestCase):
    def test_no_shift_holds(self):
        result = an.h2_run(_rows(30), "decode")
        self.assertEqual(result["triples"], 30)
        self.assertEqual(result["metrics"]["latency_ms"]["verdict"], "holds")
        self.assertEqual(result["client_time"]["verdict"], "holds")

    def test_a_ten_percent_slowdown_fails(self):
        result = an.h2_run(_rows(30, shift=0.10), "decode")
        self.assertEqual(result["metrics"]["latency_ms"]["verdict"], "fails")
        self.assertFalse(result["holds"])

    def test_an_interval_that_spans_zero_but_overruns_delta_is_inconclusive_not_failed(self):
        # band 0.10 (delta 0.05); the mean is 0.03 and the 90% interval is about [-0.007, 0.067]
        result = an.equivalence([0.09] * 5 + [-0.03] * 5, [0.051, -0.051] * 5)  # band about 0.105
        self.assertEqual(result["verdict"], "inconclusive")
        self.assertFalse(result["primary"])
        self.assertTrue(result["tail"])

    def test_too_few_triples_is_not_measured(self):
        self.assertEqual(an.h2_run(_rows(5), "decode")["metrics"]["latency_ms"]["verdict"], "not measured")

    def test_a_slow_hook_fails_the_client_time_gate(self):
        self.assertEqual(an.h2_run(_rows(30, hook_b=900.0), "decode")["client_time"]["verdict"], "fails")

    def test_the_tail_bound_is_four_at_thirty(self):
        self.assertEqual(an.tail_bound(30), 4)
        self.assertEqual(an.tail_bound(15), 3)

    def test_the_band_has_a_floor(self):
        flat = [0.0] * 20
        self.assertEqual(an.equivalence(flat, flat)["band"], an.BAND_FLOOR)
        self.assertEqual(an.equivalence(flat, flat)["verdict"], "holds")

    def test_incomplete_rounds_are_dropped(self):
        rows = _rows(12)
        rows[1]["artifacts"]["slots"].pop()  # round 11 loses its B
        self.assertEqual(an.h2_run(rows, "decode")["triples"], 11)


class H1H3(unittest.TestCase):
    def _write(self, tmp, events, counts, sent):
        trace = Path(tmp) / "t.atof.jsonl"
        trace.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
        calls = Path(tmp) / "t.calls.json"
        calls.write_text(json.dumps({"counts": counts}), encoding="utf-8")
        http = Path(tmp) / "t.http.json"
        http.write_text(json.dumps({"adapter_requests": sent}), encoding="utf-8")
        return trace, calls, http

    def _events(self, ids, *, close=True):
        out = [{"category": "agent", "scope_category": "start"}]
        for i in ids:
            out.append({"category": "llm", "scope_category": "start", "metadata": {"call_id": i}})
            if close:
                out.append({"category": "llm", "scope_category": "end", "metadata": {"call_id": i}})
        out.append({"category": "agent", "scope_category": "end"})
        return out

    def test_h1_holds_when_counts_and_spans_match(self):
        rows = [{"artifacts": {"slots": [{"traced": True, "call_ids": [2, 3]}, {"traced": False, "call_ids": [1]}]}}]
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._write(tmp, self._events([2, 3]), {"A": {"generate": {"n": 3}}}, 3)
            self.assertTrue(an.h1_run(*paths, rows)["holds"])
            paths = self._write(tmp, self._events([2, 3], close=False), {"A": {"generate": {"n": 3}}}, 4)
            result = an.h1_run(*paths, rows)
            self.assertFalse(result["checks"]["requests_counted_once"])
            self.assertFalse(result["checks"]["every_span_closed"])

    def test_h3_finds_a_canary_and_an_open_run_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "x.atof.jsonl"
            trace.write_text(json.dumps({"category": "agent", "scope_category": "start", "note": an.CANARY}) + "\n",
                             encoding="utf-8")
            result = an.h3_trace(trace, {"host": "somehost"})
            self.assertFalse(result["checks"]["no_canary"])
            self.assertFalse(result["checks"]["run_scope_closed"])
            self.assertTrue(result["checks"]["no_host"])


class Whole(unittest.TestCase):
    def test_a_stop_run_that_was_not_stopped_does_not_hold_and_missing_steps_are_marked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir()
            (root / "logs" / "p.driver.json").write_text(json.dumps(
                {"needles": {}, "check_passed": True, "steps": {"stop": {"stopped": False, "exit": 0}}}),
                encoding="utf-8")
            events = [{"category": "agent", "scope_category": "start"}, {"category": "agent", "scope_category": "end"}]
            (root / "logs" / "p-stop.atof.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n",
                                                            encoding="utf-8")
            result = an.analyze(root, "p")
            self.assertFalse(result["h3"]["stop"]["checks"]["stopped_mid_run"])
            self.assertFalse(result["h3"]["stop"]["holds"])
            self.assertEqual(result["h2"]["decode"]["reason"], "not run")
            self.assertEqual(result["h3"]["long"]["reason"], "not run")
            self.assertFalse(result["stage1_holds"])


if __name__ == "__main__":
    unittest.main()
