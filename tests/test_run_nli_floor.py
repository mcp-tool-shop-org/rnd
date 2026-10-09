"""run_nli_floor's pure parts and its pipeline over a synthetic gold tree, with a scripted fake NLI.
The scorer itself is proven against calibrate.rs in test_calibrate_metrics.py; these tests pin the
runner's own contracts: prereg denominators, premise/truncation rules, the label map, the offrig
run-directory wire shape, and that receipt metrics equal calibrate_metrics on the same outcomes.
Pure stdlib; no devices, no models."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

CAL = Path(__file__).resolve().parent.parent / "experiments" / "verifier-gold" / "calibration"
sys.path.insert(0, str(CAL))
import calibrate_metrics as cm
import run_nli_floor as rn


class FakeTok:
    def __call__(self, premise, hypothesis):
        return {"input_ids": [0] * (len(premise.split()) + len(hypothesis.split()) + 3)}


class FakeNLI:
    """Scripted answers keyed on the hypothesis text."""

    def __init__(self, answers):
        self.tok = FakeTok()
        self.answers = answers
        self.labels = ["contradiction", "entailment", "neutral"]
        self.ir_digest = "fake"

    def score(self, premise, hypothesis):
        label = self.answers[hypothesis]  # KeyError falls through: run_legs must abort on it
        return {"label": label, "probs": {label: 0.9}}


def make_claim(cid, check="grounded", split="tune", label="supported", claim=None, **extra):
    r = {"id": cid, "check_type": check, "split": split, "claim": claim or f"claim text {cid}",
         "label": label, "subtle": False, "origin": "synthetic",
         "context": [{"source": "f#L1", "text": "alpha beta"}, {"source": "f#L9", "text": "gamma"}]}
    r.update(extra)
    return r


class PureParts(unittest.TestCase):
    def test_premise_joins_contexts_in_record_order(self):
        c = make_claim("x", context=[{"text": "one"}, {"text": "two"}, {"text": "three"}])
        self.assertEqual(rn.premise_of(c), "one\n\ntwo\n\nthree")

    def test_label_map_assertion(self):
        rn.assert_label_map(["contradiction", "entailment", "neutral"])
        rn.assert_label_map(["CONTRADICTION", "Entailment", "neutral"])  # case-insensitive
        with self.assertRaises(SystemExit):
            rn.assert_label_map(["entailment", "not_nli", "neutral"])

    def test_truncation_boundary(self):
        tok = FakeTok()
        short = rn.pair_token_count(tok, " ".join(["w"] * 500), " ".join(["w"] * 9))  # 512
        long = rn.pair_token_count(tok, " ".join(["w"] * 500), " ".join(["w"] * 10))  # 513
        self.assertEqual(short, 512)
        self.assertFalse(short > rn.MAX_LEN)
        self.assertTrue(long > rn.MAX_LEN)

    def test_line_matches_offrig_wire_shape(self):
        rec = {"id": "c1", "check_type": "grounded", "gold_label": "unsupported", "subtle": True,
               "has_doc_comment": None, "self_referential": False, "origin": "synthetic",
               "verdict": "cannot_tell", "wall_seconds": 0.5}
        line = rn.build_line(rec)
        self.assertEqual(list(line), rn.LINE_FIELDS)
        self.assertEqual(len(line), 21)
        self.assertEqual(line["status"], "ok")
        self.assertIsNone(line["error_code"])
        self.assertEqual(line["model_verdict"], line["final_verdict"])

    def test_real_gold_matches_prereg_denominators(self):
        gold = rn.load_gold(rn.GOLD_ROOT)
        self.assertEqual(rn.check_denominators(gold), [])
        self.assertEqual(len(gold), 270 + 230 + 223 + 236)

    def test_denominator_check_catches_a_moved_gold(self):
        gold = rn.load_gold(rn.GOLD_ROOT)
        broken = gold[:-1]
        self.assertTrue(rn.check_denominators(broken))

    def test_load_gold_refuses_a_check_type_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "prs").mkdir()
            (root / "diffs").mkdir()
            bad = make_claim("bad1", check="reasoning", split="heldout")
            (root / "grounded.jsonl").write_text(json.dumps(bad) + "\n", encoding="utf-8")
            (root / "prs" / "grounded-prs.jsonl").write_text("", encoding="utf-8")
            (root / "diffs" / "reasoning-diffs.jsonl").write_text("", encoding="utf-8")
            with self.assertRaises(SystemExit):
                rn.load_gold(root)


class PipelineOverSyntheticGold(unittest.TestCase):
    """Six claims, both check types and splits, strata fields present and absent. The fake NLI's
    answers are scripted; the receipt must equal calibrate_metrics on the same outcomes."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "prs").mkdir()
        (root / "diffs").mkdir()
        self.gold = [
            make_claim("g1", label="supported", has_doc_comment=True),
            make_claim("g2", label="unsupported", has_doc_comment=False, self_referential=True),
            make_claim("g3", label="cannot_tell"),  # no strata fields -> "unknown"
            make_claim("g4", split="heldout", label="unsupported"),
            make_claim("r1", check="reasoning", label="supported"),
            make_claim("r2", check="reasoning", label="unsupported"),
        ]
        files = {"grounded.jsonl": [self.gold[0], self.gold[1], self.gold[2], self.gold[3]],
                 "prs/grounded-prs.jsonl": [], "diffs/reasoning-diffs.jsonl": self.gold[4:]}
        for rel, rows in files.items():
            (root / rel).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        self.root = root
        # entailment->supported, contradiction->unsupported, neutral->cannot_tell
        self.answers = {"claim text g1": "entailment", "claim text g2": "entailment",  # false accept
                        "claim text g3": "contradiction", "claim text g4": "contradiction",
                        "claim text r1": "neutral", "claim text r2": "contradiction"}
        self.nli = FakeNLI(self.answers)

    def tearDown(self):
        self.tmp.cleanup()

    def test_end_to_end(self):
        gold = rn.load_gold(self.root)
        records = rn.run_legs(self.nli, gold)
        self.assertEqual(len(records), 6)
        self.assertTrue(all(not r["truncated"] for r in records))
        receipt = rn.build_receipt(records, gold, "GPU-test", "fake", "test", None, 0.0)
        for leg, d in receipt["legs"].items():
            ct, split = leg.split("/")
            leg_gold = [c for c in gold if c["check_type"] == ct and c["split"] == split]
            outcomes = {r["id"]: r["verdict"] for r in records
                        if r["check_type"] == ct and r["split"] == split}
            self.assertEqual(d["metrics"], cm.metrics(leg_gold, outcomes)[0])
            self.assertEqual(d["metrics"]["missing"], 0)
        # g2: gold unsupported judged supported -> a false accept in grounded/tune
        fa = receipt["legs"]["grounded/tune"]["metrics"]["false_accept"]
        self.assertEqual((fa["hits"], fa["of"]), (1, 2))  # over unsupported + cannot_tell
        # g2's scripted false accept fails the rule on grounded/tune with n=3
        self.assertFalse(receipt["decision_inputs"]["nli_grounded_tune_passes"])
        self.assertIsNotNone(receipt["decision_inputs"]["nli_grounded_tune_decided_balanced_accuracy"])
        st = receipt["legs"]["grounded/tune"]["strata"]
        self.assertIn("unknown", st["has_doc_comment"])  # g3 carries no strata fields
        self.assertIn("synthetic", st["origin"])

    def test_run_dir_is_offrig_shaped(self):
        gold = rn.load_gold(self.root)
        records = rn.run_legs(self.nli, gold)
        run_dir = Path(self.tmp.name) / "run"
        rn.write_run_dir(run_dir, rn.build_manifest(self.root, gold, records, "fake", {}), records)
        lines = (run_dir / "verdicts.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 6)
        first = json.loads(lines[0])
        self.assertEqual(set(first), set(rn.LINE_FIELDS))
        self.assertEqual(first["claim_id"], "g1")
        self.assertEqual(first["final_verdict"], "supported")
        self.assertEqual(first["gold_label"], "supported")
        man = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(man["selected"]), 6)
        self.assertEqual(len(man["gold"]), 3)
        self.assertEqual(man["skipped_unlabelled"], 0)
        self.assertEqual(man["model"], "nli-deberta-v3-base")

    def test_inference_error_aborts_with_nothing_written(self):
        self.answers.pop("claim text r2")  # the fake raises KeyError partway
        gold = rn.load_gold(self.root)
        with self.assertRaises(SystemExit):
            rn.run_legs(self.nli, gold)


if __name__ == "__main__":
    unittest.main()
