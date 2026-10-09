"""Property tests for the distill-ladder plan's Step 0, items 2 and 4 (ASPIRE's share).

Item 2, dedupe and seal (experiments/distill-ladder/dedupe.py): a training item is dropped exactly when its
normalised-source hash is in a test set, and the seal changes when any single item changes.
Item 4, scoring helpers: Wilson intervals (math-ladder/report.py and calibration/difficulty.py) and the
ladder report's per-cell tally. Randomized but replayable: Hypothesis prints a reproduce blob on any failure.
"""

import importlib.util
import unittest
from pathlib import Path

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

ROOT = Path(__file__).resolve().parent.parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dedupe = _load("distill_dedupe", ROOT / "experiments" / "distill-ladder" / "dedupe.py")
report = _load("ladder_report", ROOT / "experiments" / "verifier-gold" / "math-ladder" / "report.py")
difficulty = _load("calibration_difficulty", ROOT / "experiments" / "verifier-gold" / "calibration" / "difficulty.py")

PROFILE = settings(max_examples=200, deadline=None, print_blob=True, suppress_health_check=[HealthCheck.too_slow])

# Function sources shaped like the ladder's: a few indented lines of code.
LINE = st.text(alphabet="abcdefxyv =+-*/()0123456789:", min_size=1, max_size=20)
SOURCE = st.lists(LINE, min_size=1, max_size=5).map(lambda ls: "def f(x):\n" + "\n".join("    " + s for s in ls))


@st.composite
def items(draw, prefix: str, min_size: int = 0, max_size: int = 8):
    sources = draw(st.lists(SOURCE, min_size=min_size, max_size=max_size))
    return [{"id": f"{prefix}-{i}", "claim": draw(st.text(max_size=20)), "context": [{"text": s}]}
            for i, s in enumerate(sources)]


def _respell(text: str, crlf: bool, trailing: str, doubled: bool) -> str:
    """The same source with different whitespace: line endings, trailing spaces, doubled inner spaces, blanks."""
    lines = []
    for line in text.split("\n"):
        indent = len(line) - len(line.lstrip())
        body = line[indent:].replace(" ", "  ") if doubled else line[indent:]
        lines.extend([line[:indent] + body + trailing, ""])
    return ("\r\n" if crlf else "\n").join(lines)


class TestDedupe(unittest.TestCase):
    @PROFILE
    @given(items("train"), items("test1"), items("test2"))
    def test_drops_exactly_the_items_whose_source_is_in_a_test_set(self, train, test1, test2):
        kept, dropped = dedupe.dedupe(train, test1, test2)
        test_hashes = {dedupe.source_hash(r) for r in test1 + test2}
        self.assertEqual([r for r in train if dedupe.source_hash(r) not in test_hashes], kept)
        self.assertEqual([r["id"] for r in train if dedupe.source_hash(r) in test_hashes], dropped)
        self.assertEqual(len(kept) + len(dropped), len(train))
        self.assertEqual(dedupe.dedupe(kept, test1, test2), (kept, []))  # idempotent

    @PROFILE
    @given(items("test", min_size=1), st.data(), st.booleans(), st.sampled_from(["", " ", "\t "]), st.booleans())
    def test_a_whitespace_respelling_of_a_test_item_is_still_dropped(self, test, data, crlf, trailing, doubled):
        target = data.draw(st.sampled_from(test))
        copy = {"id": "train-copy", "context": [{"text": _respell(target["context"][0]["text"], crlf, trailing,
                                                                   doubled)}]}
        kept, dropped = dedupe.dedupe([copy], test)
        self.assertEqual((kept, dropped), ([], ["train-copy"]))

    @PROFILE
    @given(SOURCE, SOURCE)
    def test_different_code_is_never_merged(self, a, b):
        assume(dedupe.normalise_source(a) != dedupe.normalise_source(b))
        self.assertNotEqual(dedupe.source_hash({"context": [{"text": a}]}),
                            dedupe.source_hash({"context": [{"text": b}]}))

    def test_a_changed_constant_is_a_different_item(self):
        a = {"context": [{"text": "def f(x):\n    v = x * 3\n    return v"}]}
        b = {"context": [{"text": "def f(x):\n    v = x * 4\n    return v"}]}
        self.assertNotEqual(dedupe.source_hash(a), dedupe.source_hash(b))


class TestSeal(unittest.TestCase):
    @PROFILE
    @given(items("v2", min_size=1), st.data())
    def test_the_seal_changes_when_any_single_item_changes(self, rows, data):
        before = dedupe.seal(rows)
        self.assertEqual(before, dedupe.seal([dict(r) for r in rows]))  # stable across runs and copies
        i = data.draw(st.integers(0, len(rows) - 1))
        field = data.draw(st.sampled_from(["claim", "id", "context", "label"]))
        changed = [dict(r) for r in rows]
        if field == "context":
            changed[i]["context"] = [{"text": rows[i]["context"][0]["text"] + "\n    pass"}]
        else:
            changed[i][field] = str(rows[i].get(field)) + "x"
        self.assertNotEqual(before, dedupe.seal(changed))

    @PROFILE
    @given(items("v2", min_size=1))
    def test_removing_adding_or_reordering_changes_the_seal(self, rows):
        before = dedupe.seal(rows)
        self.assertNotEqual(before, dedupe.seal(rows[:-1]))
        self.assertNotEqual(before, dedupe.seal(rows + [{"id": "extra"}]))
        reordered = rows[::-1]
        if dedupe.canonical_jsonl(reordered) != dedupe.canonical_jsonl(rows):
            self.assertNotEqual(before, dedupe.seal(reordered))


WILSONS = [("report", report.wilson), ("difficulty", difficulty.wilson)]
COUNTS = st.integers(1, 2000).flatmap(lambda n: st.tuples(st.integers(0, n), st.just(n)))


class TestWilson(unittest.TestCase):
    @PROFILE
    @given(COUNTS)
    def test_bounds_lie_in_unit_interval_and_contain_the_rate(self, kn):
        k, n = kn
        for name, wilson in WILSONS:
            lo, hi = wilson(k, n)
            self.assertTrue(0.0 <= lo <= k / n <= hi <= 1.0, (name, lo, k / n, hi))

    @PROFILE
    @given(COUNTS)
    def test_symmetric_in_successes_and_failures(self, kn):
        k, n = kn
        for name, wilson in WILSONS:
            lo, hi = wilson(k, n)
            flo, fhi = wilson(n - k, n)
            self.assertAlmostEqual(lo, 1 - fhi, places=12, msg=name)
            self.assertAlmostEqual(hi, 1 - flo, places=12, msg=name)

    @PROFILE
    @given(st.integers(0, 50), st.integers(1, 50))
    def test_more_data_at_the_same_rate_never_widens_the_interval(self, k, n):
        assume(k <= n)
        for name, wilson in WILSONS:
            lo, hi = wilson(k, n)
            lo4, hi4 = wilson(4 * k, 4 * n)
            self.assertLessEqual(hi4 - lo4, hi - lo + 1e-12, name)

    def test_offrig_reference_case_and_empty_cell(self):
        for name, wilson in WILSONS:
            with self.subTest(name):
                lo, hi = wilson(6, 140)
                self.assertAlmostEqual(lo, 0.0198, places=4)
                self.assertAlmostEqual(hi, 0.0903, places=4)
                self.assertEqual(wilson(0, 0), (0.0, 1.0))


CELLS = ["L1", "L2", "L3", "steps=2", "traps=3"]
VERDICTS = st.sampled_from(["supported", "unsupported", "cannot_tell", None])


@st.composite
def ladder_run(draw):
    gold = {}
    for i in range(draw(st.integers(1, 30))):
        gold[f"c{i}"] = {"label": draw(st.sampled_from(["supported", "unsupported"])),
                         "ladder": {"cell": draw(st.sampled_from(CELLS))}}
    ids = list(gold) + ["not-in-gold"]
    lines = [{"claim_id": draw(st.sampled_from(ids)), "final_verdict": draw(VERDICTS),
              **({"status": "unusable"} if draw(st.integers(0, 9)) == 0 else {})}
             for _ in range(draw(st.integers(0, 60)))]
    return gold, lines


class TestTally(unittest.TestCase):
    @PROFILE
    @given(ladder_run())
    def test_per_cell_counts_sum_to_the_total(self, run):
        gold, lines = run
        cells = report.tally(gold, lines)
        in_gold = [ln for ln in lines if ln["claim_id"] in gold]
        self.assertEqual(sum(c[0] + c[5] for c in cells.values()), len(in_gold))
        self.assertEqual(sum(c[5] for c in cells.values()), sum(ln.get("status") == "unusable" for ln in in_gold))
        for n, right, fa, neg, ab, _ in cells.values():
            self.assertTrue(0 <= right <= n and 0 <= fa <= neg <= n and 0 <= ab <= n)

    @PROFILE
    @given(ladder_run(), st.sampled_from(CELLS))
    def test_a_cells_counts_depend_only_on_its_own_lines(self, run, cell):
        gold, lines = run
        mine = [ln for ln in lines if ln["claim_id"] in gold and gold[ln["claim_id"]]["ladder"]["cell"] == cell]
        self.assertEqual(report.tally(gold, lines).get(cell, [0] * 6), report.tally(gold, mine).get(cell, [0] * 6))

    @PROFILE
    @given(ladder_run(), st.randoms(use_true_random=False))
    def test_line_order_does_not_matter(self, run, rnd):
        gold, lines = run
        shuffled = list(lines)
        rnd.shuffle(shuffled)
        self.assertEqual(dict(report.tally(gold, lines)), dict(report.tally(gold, shuffled)))

    def test_hand_counted_cell(self):
        gold = {"a": {"label": "unsupported", "ladder": {"cell": "L1"}},
                "b": {"label": "supported", "ladder": {"cell": "L1"}}}
        lines = [{"claim_id": "a", "final_verdict": "supported"}, {"claim_id": "a", "final_verdict": "cannot_tell"},
                 {"claim_id": "b", "final_verdict": "supported"}, {"claim_id": "b", "status": "unusable"}]
        self.assertEqual(report.tally(gold, lines)["L1"], [3, 1, 1, 2, 1, 1])


if __name__ == "__main__":
    unittest.main()
