"""retrieval_bench's pure parts: the pre-registered query set, the variant query fixes, scoring
(the hit metric, the zero-vector rule, numpy/pure path agreement), the paired fact bootstrap and
the CI quantile pins. Pure stdlib; no servers, no models, no devices."""

import sys
import unittest
from pathlib import Path

PROBE = Path(__file__).resolve().parent.parent / "experiments" / "npu-probe"
sys.path.insert(0, str(PROBE))
import retrieval_bench as rb

try:
    import numpy  # noqa: F401
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def synthetic():
    """Three chunks over two stores that also hold a target file. Targets: f1 -> (role-os,
    r1.md); f2 -> (offrig, g1.md)."""
    corpus = [{"store": "role-os", "chunk_id": 1, "source": "r1.md"},
              {"store": "role-os", "chunk_id": 2, "source": "r1.md"},
              {"store": "offrig", "chunk_id": 3, "source": "g1.md"}]
    docs = [[1.0, 0.0], [0.7, 0.7], [-1.0, 0.0]]
    queries = [{"fact": "f1", "form": "true", "text": "t",
                "targets": [["role-os", "r1.md"]]},
               {"fact": "f1", "form": "false", "text": "u",
                "targets": [["role-os", "r1.md"]]},
               {"fact": "f2", "form": "true", "text": "v",
                "targets": [["offrig", "g1.md"]]},
               {"fact": "f2", "form": "false", "text": "w",
                "targets": [["offrig", "g1.md"]]}]
    # q0 lands on d0 (rank 1); q1 ranks d2 first (a non-target), then d1 (rank 2); q2 hits d2 at
    # rank 1; q3 ranks d1 first (non-target), then ties at 0 (stable: d0, d2) -> target at rank 3.
    qvecs = [[1.0, 0.0], [-0.9, 0.1], [-1.0, 0.0], [0.0, 1.0]]
    return corpus, queries, docs, qvecs


class QuerySet(unittest.TestCase):
    def test_prereg_denominators(self):
        qs = rb.bench_queries()
        self.assertEqual(len(qs), 120)
        self.assertEqual(len({q["fact"] for q in qs}), 60)
        self.assertEqual(sorted({q["form"] for q in qs}), ["false", "true"])
        for q in qs:
            self.assertTrue(q["targets"])
            for corpus_name, _file in q["targets"]:
                self.assertIn(corpus_name, ("role-os", "offrig"))

    def test_both_target_shapes_present(self):
        qs = rb.bench_queries()
        self.assertTrue(any(len(q["targets"]) > 1 for q in qs))   # spans: several files
        self.assertTrue(any(len(q["targets"]) == 1 for q in qs))  # file: exactly one


class Fixes(unittest.TestCase):
    def test_apply_fix(self):
        self.assertEqual(rb.apply_fix("task", "nomic-embed-text", "query", ["x"]),
                         ["search_query: x"])
        self.assertEqual(rb.apply_fix("task", "bge-base-en-v1.5", "query", ["x"]), ["x"])
        self.assertTrue(rb.apply_fix("bge_instr", "bge-base-en-v1.5", "query", ["x"])[0]
                        .startswith(rb.BGE_INSTRUCTION))
        self.assertEqual(rb.apply_fix("none", "bge-base-en-v1.5", "query", ["x"]), ["x"])

    def test_variants_match_the_prereg(self):
        self.assertEqual(rb.DECISION_VARIANTS, ("b", "c"))
        self.assertEqual(rb.VARIANTS["a"]["chunks"], "stored")
        self.assertEqual(rb.VARIANTS["a"]["queries"], ("ollama", "nomic-embed-text", "task"))
        self.assertEqual(rb.VARIANTS["b"]["queries"], ("serve", "bge-base-en-v1.5", "none"))
        self.assertEqual(rb.VARIANTS["c"]["queries"], ("serve", "nomic-embed-text", "task"))


class Scoring(unittest.TestCase):
    def test_hit_ranks_and_rr(self):
        corpus, queries, docs, qvecs = synthetic()
        rows = rb.score_variant(corpus, queries, docs, qvecs, use_numpy=False)
        self.assertEqual([r["hit_at"][1] for r in rows], [True, False, True, False])
        self.assertTrue(all(r["hit_at"][5] and r["hit_at"][10] for r in rows))
        self.assertEqual([r["rr"] for r in rows], [1.0, 0.5, 1.0, 1.0 / 3.0])

    def test_zero_doc_vector_scores_zero(self):
        corpus = [{"store": "role-os", "chunk_id": 1, "source": "r1.md"},
                  {"store": "role-os", "chunk_id": 2, "source": "z.md"}]
        docs = [[0.0, 0.0], [1.0, 0.0]]
        queries = [{"fact": "f", "form": "true", "text": "t",
                    "targets": [["role-os", "z.md"]]}]
        rows = rb.score_variant(corpus, queries, docs, [[1.0, 0.0]], use_numpy=False)
        self.assertEqual(rows[0]["rr"], 1.0)

    @unittest.skipUnless(HAS_NUMPY, "numpy not in this python; the venv run covers this")
    def test_numpy_and_pure_paths_agree(self):
        corpus, queries, docs, qvecs = synthetic()
        qvecs = qvecs + [[0.0, 0.0]]  # a zero query: all sims 0.0, ties by index in both paths
        queries = queries + [{"fact": "f3", "form": "true", "text": "z",
                              "targets": [["offrig", "g1.md"]]}]
        self.assertEqual(rb.score_variant(corpus, queries, docs, qvecs, use_numpy=True),
                         rb.score_variant(corpus, queries, docs, qvecs, use_numpy=False))
        zero = rb.score_variant([corpus[0]], [queries[3]], [[0.0, 0.0]], [[1.0, 0.0]],
                                use_numpy=True)
        self.assertEqual(zero[0]["hit_at"], {1: False, 5: False, 10: False})

    def test_summarize(self):
        corpus, queries, docs, qvecs = synthetic()
        rows = rb.score_variant(corpus, queries, docs, qvecs, use_numpy=False)
        out = rb.summarize(rows)
        self.assertEqual(out["recall@1"], 0.5)
        self.assertEqual(out["recall@5"], 1.0)
        self.assertAlmostEqual(out["mrr"], (1.0 + 0.5 + 1.0 + 1.0 / 3.0) / 4.0)


class Bootstrap(unittest.TestCase):
    def test_resample_sets_deterministic(self):
        d1 = rb.resample_sets(60, resamples=5, seed=1)
        d2 = rb.resample_sets(60, resamples=5, seed=1)
        self.assertEqual(d1, d2)
        self.assertEqual(len(d1), 5)
        self.assertTrue(all(len(d) == 60 for d in d1))
        self.assertTrue(all(0 <= i < 60 for d in d1 for i in d))
        self.assertNotEqual(d1, rb.resample_sets(60, resamples=5, seed=2))

    def test_fact_level_resampling_keeps_both_forms(self):
        rows = []
        for fact, hits in (("fa", [True, False]), ("fb", [True, True])):
            for form, h in zip(("true", "false"), hits):
                rows.append({"fact": fact, "hit_at": {1: h}, "rr": 0.0})
        draws = [[0, 1], [0, 0], [1, 1]]
        self.assertEqual(rb.bootstrap_recall(rows, draws, k=1), [0.75, 0.5, 1.0])

    def test_identity_draw_is_the_plain_recall(self):
        corpus, queries, docs, qvecs = synthetic()
        rows = rb.score_variant(corpus, queries, docs, qvecs, use_numpy=False)
        identity = [list(range(len({r["fact"] for r in rows})))]
        self.assertEqual(rb.bootstrap_recall(rows, identity, k=1),
                         [rb.summarize(rows)["recall@1"]])

    def test_ci_nearest_rank_pins(self):
        out = rb.ci(list(range(100)))
        self.assertEqual(out, (2, 97))
        self.assertEqual(rb.ci([0.42]), (0.42, 0.42))


if __name__ == "__main__":
    unittest.main()
