"""Property tests for the math ladder generator (experiments/verifier-gold/math-ladder/generate.py).

Step 0 of the distill-ladder plan: randomized but replayable. Hypothesis draws seeds and knob settings, prints
the falsifying example and a reproduce blob on any failure, and keeps a fixed example budget so CI time is
bounded. A generator bug would corrupt every arm at once, including the oracle, so these run before any card
time. The pinned-v1 test guards the pre-registered file against any change to the generator.
"""

import hashlib
import importlib.util
import json
import random
import re
import unittest
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

ROOT = Path(__file__).resolve().parent.parent
LADDER = ROOT / "experiments" / "verifier-gold" / "math-ladder"
_spec = importlib.util.spec_from_file_location("ladder_generate", LADDER / "generate.py")
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)

V1_SHA_PREFIX = "a1062f61554d99ad"  # pre-registered in math-ladder/README.md
CLAIM = re.compile(r"`f\((-?\d+)\)` returns (-?\d+)\.")

PROFILE = settings(max_examples=200, deadline=None, print_blob=True,
                   suppress_health_check=[HealthCheck.too_slow])

knobs = st.fixed_dictionaries({
    "steps": st.sampled_from(gen.STEPS),
    "precedence": st.integers(0, 3),
    "traps": st.integers(0, 3),
    "control": st.integers(0, 3),
    "units": st.integers(0, 3),
    "nearmiss": st.integers(0, 3),
})


def execute(src: str, x: int) -> int:
    env = {"__builtins__": {"range": range, "round": round, "int": int}}
    exec(src, env)
    return env["f"](x)


class PinnedV1(unittest.TestCase):
    def test_generator_reproduces_the_preregistered_v1_file(self):
        rows, _ = gen.generate()
        text = gen.to_text(rows)
        self.assertEqual(hashlib.sha256(text.encode()).hexdigest()[:16], V1_SHA_PREFIX)
        self.assertEqual(text, (LADDER / "ladder.jsonl").read_text(encoding="utf-8"))


class Properties(unittest.TestCase):
    @PROFILE
    @given(k=knobs, seed=st.integers(0, 2**32 - 1))
    def test_build_runs_or_fails_only_in_the_skipped_ways(self, k, seed):
        """Any knob setting builds a function that returns an int, or fails only with the two errors the
        generator skips (division by zero, a non-int result). Nothing else may escape."""
        src, naive_src, x = gen.build(k, random.Random(seed))
        for s, naive in ((src, False), (naive_src, True)):
            try:
                v = gen.run(s, x, naive=naive)
            except (ZeroDivisionError, ValueError):
                continue
            self.assertIsInstance(v, int)
            self.assertNotIsInstance(v, bool)

    @PROFILE
    @given(level=st.integers(0, 3), true=st.integers(-10**9, 10**9), naive=st.integers(-10**9, 10**9),
           seed=st.integers(0, 2**32 - 1))
    def test_near_miss_distance_is_what_its_level_declares(self, level, true, naive, seed):
        value, why = gen.near_miss(level, true, naive, random.Random(seed))
        diff = abs(value - true)
        if level == 3 and naive != true:
            self.assertEqual(value, naive)
            self.assertIn("naive", why)
        elif level >= 2:
            self.assertEqual(diff, 1)
        elif level == 1:
            self.assertGreaterEqual(diff, 2)
            self.assertLessEqual(diff, max(2, round(abs(true) * 0.2)))
        else:
            self.assertGreaterEqual(diff, 5)

    @settings(max_examples=25, deadline=None, print_blob=True)
    @given(seed=st.integers(0, 2**32 - 1),
           cell=st.sampled_from(gen.cells()))
    def test_any_seed_labels_match_execution_and_both_labels_appear(self, seed, cell):
        """For a random seed and cell: every claim's label agrees with running its function, unsupported
        claims are never the truth, both labels appear, and the cell is full."""
        rows, _ = gen.generate(seed, [cell], n_per_cell=10)
        self.assertEqual(len(rows), 10)
        self.assertEqual({r["label"] for r in rows}, {"supported", "unsupported"})
        for r in rows:
            x, value = map(int, CLAIM.fullmatch(r["claim"]).groups())
            truth = execute(r["context"][0]["text"], x)
            self.assertEqual(truth, r["ladder"]["true"])
            self.assertEqual(value == truth, r["label"] == "supported", r["id"])

    @settings(max_examples=10, deadline=None, print_blob=True)
    @given(seed=st.integers(0, 2**32 - 1))
    def test_same_seed_gives_identical_output(self, seed):
        some = gen.cells()[::7]
        a, _ = gen.generate(seed, some, n_per_cell=4)
        b, _ = gen.generate(seed, some, n_per_cell=4)
        self.assertEqual(gen.to_text(a), gen.to_text(b))

    def test_every_preregistered_cell_has_both_labels_and_thirty_items(self):
        rows = [json.loads(line) for line in (LADDER / "ladder.jsonl").read_text(encoding="utf-8").splitlines()]
        by_cell = {}
        for r in rows:
            by_cell.setdefault(r["ladder"]["cell"], []).append(r["label"])
        self.assertEqual(len(by_cell), len(gen.cells()))
        for cell, labels in by_cell.items():
            self.assertEqual(len(labels), 30, cell)
            self.assertEqual(labels.count("supported"), 15, cell)


if __name__ == "__main__":
    unittest.main()
