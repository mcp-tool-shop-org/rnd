"""calibrate_metrics is checked against the hand-computed cases in offrig's own test suite
(crates/offrig-core/src/calibrate.rs @ 0f8b1c4), so the Python scorer can't drift from the Rust one
without a test going red. Pure stdlib; runs everywhere, no devices."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent
                        / "experiments" / "verifier-gold" / "calibration"))
import calibrate_metrics as cm


def close(a, b):
    assert abs(a - b) < 5e-4, f"{a} vs {b}"


def gold(cid, check="grounded", label="unsupported", subtle=False):
    return {"id": cid, "check_type": check, "label": label, "subtle": subtle}


class WilsonMatchesPublishedValues(unittest.TestCase):
    def test_published(self):
        close(cm.wilson_ci(0, 100)[1], 0.0370)  # 3.8415 / 103.8415
        lo, hi = cm.wilson_ci(4, 100)  # the largest count whose upper bound stays under 10%
        close(lo, 0.0157)
        close(hi, 0.0984)
        self.assertLess(hi, cm.MAX_FALSE_ACCEPT_UPPER)
        lo, hi = cm.wilson_ci(5, 100)
        close(lo, 0.0215)
        close(hi, 0.1118)
        self.assertGreater(hi, cm.MAX_FALSE_ACCEPT_UPPER)
        close(cm.wilson_ci(10, 20)[0], 0.299)
        close(cm.wilson_ci(10, 20)[1], 0.701)
        close(cm.wilson_ci(20, 20)[0], 0.8389)
        self.assertEqual(cm.wilson_ci(20, 20)[1], 1.0)
        self.assertEqual(cm.wilson_ci(0, 0), (0.0, 1.0))


def base_gold(subtle=0):
    # 100 unsupported (the first `subtle` near-misses) and 100 supported, interleaved as in calibrate.rs's
    # gold_set, so slices over the list mix the classes the same way.
    g = []
    for i in range(100):
        g.append(gold(f"u{i}", label="unsupported", subtle=i < subtle))
        g.append(gold(f"s{i}", label="supported"))
    return g


class GoldCannotTellScoredAsDecided(unittest.TestCase):
    def test_hand_computed_case(self):
        # 100 supported, 100 unsupported (first 10 near-misses), 40 cannot_tell.
        g = base_gold(subtle=10) + [gold(f"t{i}", label="cannot_tell") for i in range(40)]
        o = {}
        for i in range(100):
            # unsupported gold: 2 false accepts (one a near-miss), 3 abstains, 95 right.
            o[f"u{i}"] = "supported" if i in (0, 50) else ("cannot_tell" if 1 <= i <= 3 else "unsupported")
            # supported gold: 1 judged unsupported, 4 abstains, 95 right.
            o[f"s{i}"] = "unsupported" if i == 0 else ("cannot_tell" if 1 <= i <= 4 else "supported")
        for i in range(40):  # cannot_tell gold: 4 accepted, 10 said unsupported, 26 cannot_tell
            o[f"t{i}"] = "supported" if i <= 3 else ("unsupported" if i <= 13 else "cannot_tell")
        r = cm.metrics(g, o)[0]
        self.assertEqual((r["n"], r["cannot_tell_n"], r["missing"]), (240, 40, 0))
        self.assertEqual((r["false_accept"]["hits"], r["false_accept"]["of"]), (6, 140))
        close(r["false_accept"]["low"], cm.wilson_ci(6, 140)[0])
        close(r["false_accept"]["high"], cm.wilson_ci(6, 140)[1])
        u = r["false_accept_unsupported_only"]
        self.assertEqual((u["hits"], u["of"]), (2, 100))
        close(u["high"], cm.wilson_ci(2, 100)[1])
        s = r["subtle_false_accept"]
        self.assertEqual((s["hits"], s["of"]), (1, 10))
        c = r["cannot_tell_gold"]
        self.assertEqual((c["n"], c["false_accept"]["hits"], c["said_unsupported"]), (40, 4, 10))
        close(c["said_cannot_tell"]["rate"], 26.0 / 40.0)
        # Abstains: 3 + 4 of 200 supported and unsupported; the 26 are not abstains.
        self.assertEqual((r["abstain"]["hits"], r["abstain"]["of"]), (7, 200))
        # Decided supported: 96, 95 right. Decided not-supported: 97 unsupported (95 right)
        # plus 14 cannot_tell decided (10 right) = 111, 105 right.
        close(r["decided_balanced_accuracy"], (95.0 / 96.0 + 105.0 / 111.0) / 2.0)
        self.assertLess(r["false_accept"]["high"], 0.10)
        self.assertTrue(r["passes_default_rule"])

    def test_accepting_cannot_tell_fails_the_rule_the_old_one_passed(self):
        g = base_gold() + [gold(f"t{i}", label="cannot_tell") for i in range(40)]
        o = {c["id"]: c["label"] for c in g[:200]}  # all right on the 200
        for i in range(40):  # accepts 10 of 40 cannot_tell claims
            o[f"t{i}"] = "supported" if i < 10 else "cannot_tell"
        r = cm.metrics(g, o)[0]
        self.assertEqual(r["false_accept_unsupported_only"]["hits"], 0)
        self.assertLess(r["false_accept_unsupported_only"]["high"], 0.10)
        self.assertEqual((r["false_accept"]["hits"], r["false_accept"]["of"]), (10, 140))
        self.assertGreater(r["false_accept"]["high"], 0.10)
        self.assertFalse(r["passes_default_rule"])
        self.assertEqual(r["abstain"]["hits"], 0)  # their silence is not an abstain

    def test_cannot_tell_everywhere_still_fails_on_abstain(self):
        g = base_gold() + [gold(f"t{i}", label="cannot_tell") for i in range(400)]
        o = {c["id"]: "cannot_tell" for c in g}
        r = cm.metrics(g, o)[0]
        # The 400 right answers do not dilute abstain: it is over the other 200.
        self.assertEqual((r["abstain"]["hits"], r["abstain"]["of"]), (200, 200))
        self.assertEqual(r["abstain"]["rate"], 1.0)
        self.assertEqual(r["false_accept"]["hits"], 0)
        self.assertEqual(r["cannot_tell_gold"]["said_cannot_tell"]["rate"], 1.0)
        self.assertIsNone(r["decided_balanced_accuracy"])
        self.assertFalse(r["passes_default_rule"])

    def test_missing_answers_fail_the_rule(self):
        g = base_gold()
        o = {c["id"]: c["label"] for c in g[:199]}  # one claim unanswered
        r = cm.metrics(g, o)[0]
        self.assertEqual(r["missing"], 1)
        self.assertFalse(r["passes_default_rule"])


if __name__ == "__main__":
    unittest.main()
