"""siglip2_probe's pure parts: the sampled-image rule (the prereg's exact selector pin), the
timing summary, the match summary (min/mean/p1 + worst-5 ordering), and the embedding picker over
the shapes optimum exports can take. Pure stdlib; no models, no devices, no images."""

import random
import sys
import tempfile
import unittest
from pathlib import Path

PROBE = Path(__file__).resolve().parent.parent / "experiments" / "npu-probe"
sys.path.insert(0, str(PROBE))
import siglip2_probe as sp


class Sampling(unittest.TestCase):
    def test_list_images_filters_and_sorts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "b.png").write_bytes(b"x")
            (root / "a.JPG").write_bytes(b"x")
            (root / "notes.txt").write_text("no")
            sub = root / "sub"
            sub.mkdir()
            (sub / "c.webp").write_bytes(b"x")
            (sub / "d.PNG").write_bytes(b"x")
            got = sp.list_images(root)
            self.assertEqual(len(got), 4)
            self.assertEqual(got, sorted(got))
            self.assertTrue(any(p.endswith("c.webp") for p in got))
            self.assertFalse(any(p.endswith("notes.txt") for p in got))

    def test_sample_is_the_preg_pin(self):
        paths = [f"img/{i:03d}.png" for i in range(185)]
        random.Random(7).shuffle(paths)  # unsorted on purpose; the pin sorts first
        self.assertEqual(sp.sample_images(paths),
                         random.Random(20261009).sample(sorted(paths), 50))
        self.assertEqual(len(set(sp.sample_images(paths))), 50)
        self.assertNotEqual(sp.sample_images(paths, seed=1), sp.sample_images(paths))

    def test_sample_refuses_less_than_n(self):
        with self.assertRaises(SystemExit):
            sp.sample_images(["only.png"])


class Summaries(unittest.TestCase):
    def test_device_stats(self):
        out = sp.device_stats([0.3, 0.1, 0.2])
        self.assertEqual(out, {"n": 3, "median_s": 0.2, "min_s": 0.1, "max_s": 0.3})

    def test_summarize_matches_min_mean_p1_and_worst(self):
        pairs = [(f"img/{i}.png", c) for i, c in enumerate([0.99, 0.95, 0.80, 0.999, 0.90, 0.70])]
        out = sp.summarize_matches(pairs)
        self.assertEqual(out["n"], 6)
        self.assertEqual(out["min"], 0.7)
        self.assertAlmostEqual(out["mean"], sum(x[1] for x in pairs) / 6, places=5)
        self.assertEqual([w["cosine"] for w in out["worst"]],
                         [w[1] for w in sorted(pairs, key=lambda pc: (pc[1], pc[0]))[:5]])
        self.assertEqual(out["worst"][0]["image"], "img/5.png")

    def test_summarize_matches_tie_break_by_path(self):
        pairs = [("b.png", 0.5), ("a.png", 0.5), ("c.png", 0.9)]
        out = sp.summarize_matches(pairs)
        self.assertEqual([w["image"] for w in out["worst"][:2]], ["a.png", "b.png"])


class PickEmbedding(unittest.TestCase):
    def test_pooler_output_first(self):
        self.assertEqual(sp.pooled_vector({"pooler_output": [[1.0, 2.0]],
                                           "last_hidden_state": [[9.0]]}), [1.0, 2.0])

    def test_image_embeds_and_single_key_fallbacks(self):
        self.assertEqual(sp.pooled_vector({"image_embeds": [[3.0]]}), [3.0])
        self.assertEqual(sp.pooled_vector({"only_output": [[4.0, 5.0]]}), [4.0, 5.0])

    def test_tolist_path(self):
        class FakeTensor:
            def tolist(self):
                return [[6.0, 7.0]]
        self.assertEqual(sp.pooled_vector({"pooler_output": FakeTensor()}), [6.0, 7.0])

    def test_batch_over_one_and_empty_abort(self):
        with self.assertRaises(SystemExit):
            sp.pooled_vector({"pooler_output": [[1.0], [2.0]]})
        with self.assertRaises(SystemExit):
            sp.pooled_vector({"pooler_output": [[]]})
        with self.assertRaises(SystemExit):
            sp.pooled_vector({"x": [[1.0]], "y": [[2.0]]})


if __name__ == "__main__":
    unittest.main()
