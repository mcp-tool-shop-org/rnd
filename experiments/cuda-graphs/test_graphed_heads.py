"""CPU checks that graphed_heads' eager path reproduces aspire-si's train_head and score_set.

Needs torch and an aspire-si checkout (ASPIRE_SI env var, default E:/AI/aspire-si). Not part of
rnd's own suite, which has no torch. The graph path itself needs a GPU and is checked by bench.py.
  python -m unittest test_graphed_heads   (from this directory, in the aspire-cu134 env)
"""

from __future__ import annotations

import os
import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASPIRE = Path(os.environ.get("ASPIRE_SI", "E:/AI/aspire-si"))
sys.path[:0] = [str(ASPIRE), str(ASPIRE / "examples" / "sft-experiment"), str(HERE)]

import torch  # noqa: E402
from critic_heads import HPARAMS, score_set, train_head  # noqa: E402

from graphed_heads import batch_plan, score_set_fast, stack_features, train_head_fast  # noqa: E402


def fake_cache(n_pairs: int, dim: int, max_len: int, seed: int = 0):
    g = torch.Generator().manual_seed(seed)
    rng = random.Random(seed)
    feats, masks = [], []
    for _ in range(2 * n_pairs):
        t = rng.randint(min(3, max_len), max_len)
        feats.append(torch.randn(t, dim, generator=g).half())
        masks.append(torch.ones(t, dtype=torch.long))
    return feats, masks, [(2 * i, 2 * i + 1) for i in range(n_pairs)]


class BatchPlan(unittest.TestCase):
    def test_matches_original_loop(self):
        index = [(2 * i, 2 * i + 1) for i in range(19)]
        flip = [i % 3 == 0 for i in range(19)]
        plan = batch_plan(index, flip, 7, 2, 8)
        # The original loop, written out.
        rng, pairs, expect = random.Random(7), list(range(19)), []
        for _ in range(2):
            rng.shuffle(pairs)
            for start in range(0, 19, 8):
                ks = []
                for i in pairs[start : start + 8]:
                    s, f = index[i]
                    ks += [f, s] if flip[i] else [s, f]
                expect.append(ks)
        self.assertEqual(plan, expect)
        self.assertEqual([len(b) for b in plan], [16, 16, 6, 16, 16, 6])


class Equivalence(unittest.TestCase):
    def check(self, role: str, pooling: str, max_len: int):
        feats, masks, index = fake_cache(13, 24, max_len)
        hp = {**HPARAMS, "hidden_dim": 16, "dropout": 0.0, "epochs": 2, "batch_pairs": 4}
        ref = train_head(role, pooling, 42, feats, masks, index, None, "cpu", hp)
        ref_scores = score_set(ref, feats, masks, index, "cpu")
        x, m, lens = stack_features(feats, masks, "cpu")
        head, losses = train_head_fast(role, pooling, 42, x, m, lens, index, None, hp)
        got = score_set_fast(head, x, m, lens, index, chunk=5)
        self.assertEqual(len(losses), 2 * 4)
        for a, b in zip(ref_scores[0] + ref_scores[1], got[0] + got[1]):
            self.assertAlmostEqual(a, b, delta=1e-4)
        for p, q in zip(ref.parameters(), head.parameters()):
            self.assertTrue(torch.allclose(p, q, atol=1e-5))

    def test_auditor_attention(self):
        self.check("auditor", "attention", 9)

    def test_advocate_mean_length1(self):
        self.check("advocate", "mean", 1)

    def test_a_head_does_not_depend_on_heads_trained_before_it(self):
        # Dropout on: each head's masks must come from its own seed, not from how much RNG earlier
        # heads in the process consumed (the defect ASPIRE found in train_head, 2026-10-08).
        feats, masks, index = fake_cache(13, 24, 9)
        hp = {**HPARAMS, "hidden_dim": 16, "dropout": 0.3, "epochs": 2, "batch_pairs": 4}
        x, m, lens = stack_features(feats, masks, "cpu")
        torch.manual_seed(1234)
        alone, losses_alone = train_head_fast("auditor", "attention", 43, x, m, lens, index, None, hp)
        torch.manual_seed(1234)
        train_head_fast("auditor", "attention", 42, x, m, lens, index, None, hp)  # an earlier head
        torch.rand(1000)  # and unrelated RNG use in between
        after, losses_after = train_head_fast("auditor", "attention", 43, x, m, lens, index, None, hp)
        self.assertEqual(losses_alone, losses_after)
        for p, q in zip(alone.parameters(), after.parameters()):
            self.assertTrue(torch.equal(p, q))

    def test_training_leaves_the_callers_rng_alone(self):
        feats, masks, index = fake_cache(5, 8, 4)
        hp = {**HPARAMS, "hidden_dim": 8, "dropout": 0.3, "epochs": 1, "batch_pairs": 2}
        x, m, lens = stack_features(feats, masks, "cpu")
        torch.manual_seed(7)
        expected = torch.rand(3)
        torch.manual_seed(7)
        train_head_fast("advocate", "mean", 42, x, m, lens, index, None, hp)
        self.assertTrue(torch.equal(torch.rand(3), expected))

    def test_stack_pads_with_zero_mask(self):
        feats, masks, _ = fake_cache(2, 4, 6)
        x, m, lens = stack_features(feats, masks, "cpu")
        self.assertEqual(x.dtype, torch.float16)
        for k, t in enumerate(lens):
            self.assertEqual(int(m[k].sum()), t)
            self.assertTrue(torch.equal(x[k, :t], feats[k]))
            self.assertEqual(float(x[k, t:].abs().sum()), 0.0)


if __name__ == "__main__":
    unittest.main()
