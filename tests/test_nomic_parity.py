"""nomic_parity's pure parts: offrig's wire semantics mirrored from index.rs @ a45fe53 (task_prefix,
quantize/dequantize, cosine), the store reader against a synthetic schema-v6 sqlite, the benchmark's
query extraction, and the worst-k pick. Pure stdlib; no devices, no servers, no models."""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

PROBE = Path(__file__).resolve().parent.parent / "experiments" / "npu-probe"
sys.path.insert(0, str(PROBE))
import nomic_parity as np_


class RustMirrors(unittest.TestCase):
    def test_task_prefix_matches_the_rust_test(self):
        # index.rs @ a45fe53: nomic_gets_its_task_prefixes_and_other_models_none
        self.assertEqual(np_.task_prefix("nomic-embed-text", "document"), "search_document: ")
        self.assertEqual(np_.task_prefix("nomic-embed-text:v1.5", "query"), "search_query: ")
        self.assertEqual(np_.task_prefix("bge-m3", "query"), "")

    def test_cosine_matches_the_rust_test(self):
        # index.rs @ a45fe53: cosine_orders_vectors_and_survives_zeros
        self.assertAlmostEqual(np_.cosine([1.0, 0.0], [2.0, 0.0]), 1.0)
        self.assertAlmostEqual(np_.cosine([1.0, 0.0], [0.0, 3.0]), 0.0)
        self.assertAlmostEqual(np_.cosine([1.0, 0.0], [-1.0, 0.0]), -1.0)
        self.assertEqual(np_.cosine([0.0, 0.0], [1.0, 1.0]), 0.0)

    def test_quantize_round_trip_error_within_one_step(self):
        # index.rs @ a45fe53: the int8 round trip test (worst error over one step)
        v = [0.13, -0.52, 0.97, 0.0, 1.0, -1.0, 0.004]
        q, scale = np_.quantize(v)
        back = np_.dequantize(q, scale)
        for x, b in zip(v, back):
            self.assertLessEqual(abs(x - b), scale + 1e-9)

    def test_dequantize_sign_and_zero_scale(self):
        self.assertEqual(np_.dequantize(bytes([0xFF, 0x00, 0x7F]), 0.5), [-0.5, 0.0, 63.5])
        q, scale = np_.quantize([0.0, 0.0])
        self.assertEqual(scale, 0.0)
        self.assertEqual(np_.dequantize(q, scale), [0.0, 0.0])

    def test_p1_nearest_rank(self):
        self.assertEqual(np_.p1(list(range(1, 101))), 1)
        self.assertEqual(np_.p1([5.0] * 100), 5.0)
        vals = [0.9] * 99 + [0.5]
        self.assertEqual(np_.p1(vals), 0.5)

    def test_worst_k_orders_by_the_bound_comparison(self):
        rows = [{"item": f"i{i}", "cos": {"c_vs_a_fresh": c}} for i, c in
                enumerate([0.99, 0.80, 0.95, 0.70, 0.999, 0.61])]
        worst = np_.worst_k(rows, 3)
        self.assertEqual([r["item"] for r in worst], ["i5", "i3", "i1"])


def make_store(path: Path, model="nomic-embed-text", dim=3, rows=((1, "a/b.mjs", "body one"), (2, "c.py", "body two"))):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    con.execute("CREATE TABLE chunks (id INTEGER PRIMARY KEY, source TEXT NOT NULL, kind TEXT NOT NULL,"
                " title TEXT NOT NULL, ordinal INTEGER NOT NULL, body TEXT NOT NULL,"
                " sha256 TEXT NOT NULL, created_at INTEGER NOT NULL)")
    con.execute("CREATE TABLE embeddings (chunk_id INTEGER PRIMARY KEY, model TEXT NOT NULL,"
                " dim INTEGER NOT NULL, vec BLOB NOT NULL, scale REAL NOT NULL)")
    con.execute("INSERT INTO settings VALUES ('embed_model', ?)", (model,))
    con.execute("INSERT INTO settings VALUES ('embed_dim', ?)", (str(dim),))
    for cid, src, body in rows:
        con.execute("INSERT INTO chunks VALUES (?, ?, 'code', 't', 0, ?, 'x', 0)", (cid, src, body))
        vec = [0.1 * cid, -0.2, 0.3][:dim]
        q, scale = np_.quantize(vec)
        con.execute("INSERT INTO embeddings VALUES (?, ?, ?, ?, ?)", (cid, model, dim, q, scale))
    con.commit()
    con.close()
    return path


class ReadStore(unittest.TestCase):
    def test_reads_and_dequantizes(self):
        with tempfile.TemporaryDirectory() as d:
            p = make_store(Path(d) / "s.db")
            model, dim, chunks, stored = np_.read_store(p)
            self.assertEqual((model, dim), ("nomic-embed-text", 3))
            self.assertEqual([c["chunk_id"] for c in chunks], [1, 2])
            got = stored[1]
            want = np_.dequantize(bytes(np_.quantize([0.1, -0.2, 0.3])[0]), np_.quantize([0.1, -0.2, 0.3])[1])
            self.assertEqual(got, want)

    def test_refuses_mixed_models(self):
        with tempfile.TemporaryDirectory() as d:
            p = make_store(Path(d) / "s.db")
            con = sqlite3.connect(p)
            con.execute("UPDATE embeddings SET model='other' WHERE chunk_id=2")
            con.commit()
            con.close()
            with self.assertRaises(SystemExit):
                np_.read_store(p)

    def test_refuses_missing_embeddings(self):
        with tempfile.TemporaryDirectory() as d:
            p = make_store(Path(d) / "s.db")
            con = sqlite3.connect(p)
            con.execute("DELETE FROM embeddings WHERE chunk_id=2")
            con.commit()
            con.close()
            with self.assertRaises(SystemExit):
                np_.read_store(p)


class FactQueries(unittest.TestCase):
    def test_120_queries_id_tagged_true_and_false(self):
        qs = np_.queries_from_facts()
        self.assertEqual(len(qs), 120)  # 60 facts x 2 forms, as pre-registered
        ids = [qid for qid, _ in qs]
        self.assertEqual(ids[:2], ["cal-dedupe:true", "cal-dedupe:false"])
        self.assertEqual(len({qid for qid in ids}), 120)


if __name__ == "__main__":
    unittest.main()


class OllamaContextGuard(unittest.TestCase):
    """The A-fresh reference must be untruncated: parse_show pins how the effective context is read,
    and refuses when it can't be established."""

    def test_num_ctx_from_modelfile_wins(self):
        payload = {"parameters": "num_ctx                        8192\nstop                            <eos>",
                   "model_info": {"nomic-bert.context_length": 2048}}
        got = np_.parse_show(payload)
        self.assertEqual(got["num_ctx"], 8192)
        self.assertEqual(got["context_length"], 2048)
        self.assertEqual(got["effective"], 8192)

    def test_context_length_is_the_fallback(self):
        payload = {"model_info": {"nomic-bert.context_length": 2048,
                                  "general.architecture": "nomic-bert"}}
        got = np_.parse_show(payload)
        self.assertEqual(got["effective"], 2048)
        self.assertIsNone(got["num_ctx"])

    def test_ambiguous_architectures_refuse(self):
        payload = {"model_info": {"a.context_length": 2048, "b.context_length": 4096}}
        with self.assertRaises(SystemExit):
            np_.parse_show(payload)

    def test_nothing_readable_refuses(self):
        with self.assertRaises(SystemExit):
            np_.parse_show({})
        with self.assertRaises(SystemExit):
            np_.parse_show({"parameters": "temperature 1\nstop <eos>"})

    def test_unparseable_num_ctx_falls_back(self):
        payload = {"parameters": "num_ctx auto", "model_info": {"nomic-bert.context_length": 2048}}
        self.assertEqual(np_.parse_show(payload)["effective"], 2048)
