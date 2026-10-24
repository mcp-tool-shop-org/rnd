"""colab-drift compare.py: what counts as a decision, and reading replies the way role-set reads them.

The G4 write-up first said every one of 65 drifted critic calls changed a decision, because compare.py counted any
labelled line (2026-10-23 correction). Then DECIDING was left out entirely, though role-set acts on it on verdict
calls; Argon's review of rnd #225 (2026-10-24) found that, and that the parser disagreed with role-set's on case,
bold, a repeated ANSWER line and multi-line flaw replies. These cases pin the rules. The full G4 check (178 matched,
65 drifted, 28 decision, 3 verdict, 10 evidence) runs from the private journals in rnd-local; it isn't repeated here.
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from collections import defaultdict, deque
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "experiments/stage1-regeneration/colab-drift/scripts/compare.py"
spec = importlib.util.spec_from_file_location("colab_drift_compare", SCRIPT)
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)


def score(ref_text: str, got: str, check: str | None = None) -> dict:
    refs = defaultdict(deque)
    refs["k"].append(("R", ref_text))
    row = {"key": "k", "completion": {"text": got}}
    if check:
        row["check"] = check
    return compare.score([row], refs)["per"]["R"]


class DecisionFields(unittest.TestCase):
    def test_exact_is_not_drift(self):
        s = score("VERDICT: supported\nDECIDING: x", "VERDICT: supported\nDECIDING: x", "verdict")
        self.assertEqual((s["exact"], s["drift"], s["decision_drift"]), (1, 0, 0))

    def test_contrasted_only_is_not_a_decision(self):
        s = score("TRAIT: T03\nCONTRASTED: T05", "TRAIT: T03\nCONTRASTED: none", "trait")
        self.assertEqual((s["drift"], s["decision_drift"], s["verdict_drift"]), (1, 0, 0))
        self.assertEqual(dict(s["field_changes"]), {"CONTRASTED": 1})

    def test_deciding_on_a_verdict_call_is_evidence_drift(self):
        s = score("VERDICT: supported\nDECIDING: a b", "VERDICT: supported\nDECIDING: b a", "verdict")
        self.assertEqual((s["decision_drift"], s["verdict_drift"], s["evidence_drift"]), (0, 0, 1))
        self.assertEqual(dict(s["field_changes"]), {"DECIDING": 1})

    def test_deciding_on_a_twin_verdict_is_not_evidence_drift(self):
        s = score("VERDICT: cannot_tell\nDECIDING: a", "VERDICT: cannot_tell\nDECIDING: b", "twin_verdict")
        self.assertEqual((s["field_changes"]["DECIDING"], s["evidence_drift"]), (1, 0))

    def test_deciding_emphasis_and_spacing_are_not_a_change(self):
        s = score("VERDICT: supported\nDECIDING: the **line**  here", "VERDICT: supported\nDECIDING: the line here",
                  "verdict")
        self.assertEqual((s["drift"], s["evidence_drift"], dict(s["field_changes"])), (1, 0, {}))

    def test_trait_change_is_a_decision_not_a_verdict(self):
        s = score("TRAIT: T03\nCONTRASTED: none", "TRAIT: T07\nCONTRASTED: none", "trait")
        self.assertEqual((s["decision_drift"], s["verdict_drift"]), (1, 0))

    def test_flaw_label_is_a_decision(self):
        s = score("guess", "none", "flaw")
        self.assertEqual((s["decision_drift"], dict(s["field_changes"])), (1, {"LABEL": 1}))

    def test_verdict_change_counts_both(self):
        s = score("VERDICT: unsupported\nDECIDING: x", "VERDICT: cannot_tell\nDECIDING: x", "verdict")
        self.assertEqual((s["decision_drift"], s["verdict_drift"]), (1, 1))

    def test_answer_change_is_a_decision_not_a_verdict(self):
        s = score("Working\nANSWER: turn 1", "Working\nANSWER: turn 2", "answer")
        self.assertEqual((s["decision_drift"], s["verdict_drift"], dict(s["field_changes"])), (1, 0, {"ANSWER": 1}))


class ReadsAsRoleSetReads(unittest.TestCase):
    """Each case is an input where the old regex and role-set's parser disagreed (Argon review bt, question 2)."""

    def test_verdict_in_any_case_is_read(self):
        s = score("Verdict: supported\nDECIDING: x", "Verdict: unsupported\nDECIDING: x", "verdict")
        self.assertEqual(s["verdict_drift"], 1)

    def test_verdict_case_and_period_are_not_a_change(self):
        s = score("VERDICT: supported\nDECIDING: x", "VERDICT: Supported.\nDECIDING: x", "verdict")
        self.assertEqual((s["drift"], s["decision_drift"]), (1, 0))

    def test_bold_trait_is_read(self):
        s = score("**TRAIT:** T03\nCONTRASTED: none", "**TRAIT:** T07\nCONTRASTED: none", "trait")
        self.assertEqual(s["decision_drift"], 1)

    def test_trait_commentary_is_not_a_change(self):
        s = score("TRAIT: T03\nCONTRASTED: none", "TRAIT: **T03** (decides the step)\nCONTRASTED: none", "trait")
        self.assertEqual(s["decision_drift"], 0)

    def test_answer_reads_the_last_line(self):
        s = score("ANSWER: draft\nANSWER: turn 1", "ANSWER: draft\nANSWER: turn 2", "answer")
        self.assertEqual(s["decision_drift"], 1)
        s = score("ANSWER: maybe 1\nANSWER: turn 2", "ANSWER: maybe 3\nANSWER: turn 2", "answer")
        self.assertEqual(s["decision_drift"], 0)

    def test_flaw_reply_with_reasoning_reads_its_first_word(self):
        s = score("guess\nThe checker used outside knowledge.", "none\nThe checker quoted the line.", "flaw")
        self.assertEqual((s["decision_drift"], dict(s["field_changes"])), (1, {"LABEL": 1}))

    def test_two_unreadable_flaw_replies_are_not_a_change(self):
        s = score("- guess", "- none", "flaw")
        self.assertEqual(s["decision_drift"], 0)


class Matching(unittest.TestCase):
    def test_unmatched_key_is_reported(self):
        out = compare.score([{"key": "nope", "completion": {"text": "x"}}], defaultdict(deque))
        self.assertEqual(len(out["unmatched"]), 1)

    def test_unconsumed_reference_rows_are_counted(self):
        refs = defaultdict(deque)
        refs["a"].append(("R", "guess"))
        refs["b"].append(("R", "none"))
        out = compare.score([{"key": "a", "check": "flaw", "completion": {"text": "guess"}}], refs)
        self.assertEqual((out["per"]["R"]["exact"], out["per"]["R"]["ref_unconsumed"]), (1, 1))

    def test_a_key_in_two_named_references_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            row = json.dumps({"key": "k", "check": "flaw", "completion": {"text": "guess"}}) + "\n"
            for name in ("fresh", "r1", "r2"):
                Path(d, name + ".jsonl").write_text(row, encoding="utf-8")
            r = subprocess.run([sys.executable, "-I", str(SCRIPT), "--fresh", str(Path(d, "fresh.jsonl")),
                                "--ref", f"A={Path(d, 'r1.jsonl')}", "--ref", f"B={Path(d, 'r2.jsonl')}"],
                               capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("REFUSED", r.stderr)


if __name__ == "__main__":
    unittest.main()
