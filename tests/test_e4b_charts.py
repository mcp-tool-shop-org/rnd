"""E4b charts are drawn from the committed results, and the manifest hashes those bytes."""

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHARTS = ROOT / "experiments" / "charts"
RESULTS = ROOT / "experiments" / "e4b" / "results"
SITE = ROOT / "site" / "public" / "charts"
NAMES = ("e4b-verdict.svg", "e4b-triplet-effects.svg", "e4b-pilot-clock.svg", "e4b-igpu-latency.svg")
RESULT_PATHS = (
    "experiments/e4b/results/block-2.json",
    "experiments/e4b/results/block-3.json",
    "experiments/e4b/results/pilot.json",
)


def load_charts():
    spec = importlib.util.spec_from_file_location("make_charts", CHARTS / "make_charts.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class E4bChartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Draw into a temporary directory, never over the tracked charts: a test run must leave the tree clean.
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name)
        cls.mod = load_charts()
        cls.mod.HERE = out / "charts"
        cls.mod.SITE_CHARTS = out / "site"
        cls.mod.HERE.mkdir()
        cls.mod.chart_e4b()
        cls.raw = {name: (cls.mod.HERE / name).read_bytes() for name in NAMES}
        cls.svg = {name: data.decode("utf-8") for name, data in cls.raw.items()}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_four_charts_are_copied_to_the_site(self):
        for name, text in self.svg.items():
            self.assertIn("<svg", text)
            self.assertEqual(self.raw[name], (self.mod.SITE_CHARTS / name).read_bytes())

    def test_a_rebuild_matches_the_committed_charts_byte_for_byte(self):
        # LF on every OS, and no drift between the committed SVGs and what the results draw.
        for name, data in self.raw.items():
            self.assertNotIn(b"\r\n", data, name)
            self.assertEqual(data, (CHARTS / name).read_bytes(), name)
            self.assertEqual(data, (SITE / name).read_bytes(), name)

    def test_manifest_sha256_matches_the_result_bytes(self):
        manifest = json.loads((CHARTS / "manifest.json").read_text(encoding="utf-8"))
        for rel in RESULT_PATHS:
            digest = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
            self.assertEqual(manifest["inputs"][rel]["sha256"], digest, rel)

    def test_verdict_uses_the_results_and_keeps_the_inconclusive_rows(self):
        verdict = self.svg["e4b-verdict.svg"]
        triplets = self.svg["e4b-triplet-effects.svg"]
        self.assertIn("PRE-REGISTERED", verdict)
        self.assertIn("exact Wilcoxon interval", verdict)
        self.assertIn("INCONCLUSIVE", verdict)
        self.assertIn("superseded by block 3", verdict)
        self.assertNotIn("<path", verdict)
        self.assertNotIn("<path", triplets)
        self.assertIn("PRE-REGISTERED", triplets)
        for name in ("block-2.json", "block-3.json"):
            doc = json.loads((RESULTS / name).read_text(encoding="utf-8"))
            for pair in doc["pairs"]:
                if pair["hodges_lehmann"] is None:
                    continue
                estimate = f"{100 * pair['hodges_lehmann']:+.2f}%"
                self.assertIn(estimate, verdict)
                self.assertIn(estimate, triplets)
                coverage = f"{pair['achieved']:.3f}"
                self.assertIn(coverage, verdict)

    def test_pilot_marks_the_tolerance_and_the_p95_from_the_file(self):
        pilot = json.loads((RESULTS / "pilot.json").read_text(encoding="utf-8"))
        chart = self.svg["e4b-pilot-clock.svg"]
        self.assertIn("PRE-REGISTERED PILOT", chart)
        self.assertIn(f"tolerance {self.mod.e4b_fmt_mhz(pilot['clock_tolerance_mhz'])} MHz", chart)
        self.assertIn(f"p95 {self.mod.e4b_fmt_mhz(pilot['p95_clock_range_mhz'])} MHz", chart)
        self.assertNotIn("<path", chart)

    def test_igpu_latency_is_labelled_post_hoc_and_is_not_a_test(self):
        chart = self.svg["e4b-igpu-latency.svg"]
        block = json.loads((RESULTS / "block-3.json").read_text(encoding="utf-8"))
        pair = next(p for p in block["pairs"] if p["pair"] == "igpu-5090")
        paired = [s["value"] for s in pair["slots"] if s["role"] == "paired"]
        self.assertIn("POST HOC", chart)
        self.assertIn("No significance test.", chart)
        self.assertNotIn("significant", chart.lower())
        self.assertIn(f"{min(paired):.1f}–{max(paired):.1f} ms", chart)
        self.assertNotIn("<path", chart)
