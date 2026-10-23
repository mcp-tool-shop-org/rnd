"""colab-drift compare.py: what counts as a decision (2026-10-23 correction).

The G4 write-up first said every one of 65 drifted critic calls changed a decision, because compare.py counted any
labelled line. CONTRASTED is scaffolding role-set never parses and DECIDING is a quoted span; only VERDICT, TRAIT,
ANSWER and a bare flaw LABEL are decisions. These cases pin that rule. The full G4 check (178 matched, 65 drifted,
3 verdict changes) runs from the private journals in rnd-local; it isn't repeated here.
"""
import importlib.util
import unittest
from collections import defaultdict, deque
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "experiments/stage1-regeneration/colab-drift/scripts/compare.py"
spec = importlib.util.spec_from_file_location("colab_drift_compare", SCRIPT)
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)


def score(ref_text: str, got: str) -> dict:
    refs = defaultdict(deque)
    refs["k"].append(("R", ref_text))
    return compare.score([{"key": "k", "completion": {"text": got}}], refs)["per"]["R"]


class DecisionFields(unittest.TestCase):
    def test_exact_is_not_drift(self):
        s = score("VERDICT: supported\nDECIDING: x", "VERDICT: supported\nDECIDING: x")
        self.assertEqual((s["exact"], s["drift"], s["decision_drift"]), (1, 0, 0))

    def test_contrasted_only_is_not_a_decision(self):
        s = score("TRAIT: T03\nCONTRASTED: T05", "TRAIT: T03\nCONTRASTED: none")
        self.assertEqual((s["drift"], s["decision_drift"], s["verdict_drift"]), (1, 0, 0))
        self.assertEqual(dict(s["field_changes"]), {"CONTRASTED": 1})

    def test_deciding_only_is_not_a_decision(self):
        s = score("VERDICT: supported\nDECIDING: a b", "VERDICT: supported\nDECIDING: b a")
        self.assertEqual((s["decision_drift"], s["verdict_drift"]), (0, 0))

    def test_trait_change_is_a_decision_not_a_verdict(self):
        s = score("TRAIT: T03\nCONTRASTED: none", "TRAIT: T07\nCONTRASTED: none")
        self.assertEqual((s["decision_drift"], s["verdict_drift"]), (1, 0))

    def test_flaw_label_is_a_decision(self):
        s = score("guess", "none")
        self.assertEqual((s["decision_drift"], dict(s["field_changes"])), (1, {"LABEL": 1}))

    def test_verdict_change_counts_both(self):
        s = score("VERDICT: unsupported\nDECIDING: x", "VERDICT: cannot_tell\nDECIDING: x")
        self.assertEqual((s["decision_drift"], s["verdict_drift"]), (1, 1))

    def test_unmatched_key_is_reported(self):
        out = compare.score([{"key": "nope", "completion": {"text": "x"}}], defaultdict(deque))
        self.assertEqual(len(out["unmatched"]), 1)


if __name__ == "__main__":
    unittest.main()
