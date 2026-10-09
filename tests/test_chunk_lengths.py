"""Pins chunk_lengths.py's port against the five chunker cases in offrig index.rs's own test module
(@ a45fe53) — if the port drifts from the Rust chunker, these go red, and the bucket measurement
can't silently mismeasure. Pure stdlib; no tokenizer."""

import sys
import tempfile
import unittest
from pathlib import Path

PROBE = Path(__file__).resolve().parent.parent / "experiments" / "npu-probe"
sys.path.insert(0, str(PROBE))
import chunk_lengths as cl

MIN_CHARS, MAX_CHARS = cl.MIN_CHARS, cl.MAX_CHARS


def para(n, ch):
    return ch * n


def body_of(c):
    return c["body"].split("\n", 1)[1] if "\n" in c["body"] else ""


class ChunkerMatchesRust(unittest.TestCase):
    def test_documents_split_on_paragraphs_within_the_size_band(self):
        text = "\n\n".join(para(500, chr(ord('a') + i)) for i in range(12))
        chunks = cl.chunk("docs/a.md", "doc", text)
        self.assertGreater(len(chunks), 1)
        for i, c in enumerate(chunks):
            n = len(body_of(c))
            self.assertLessEqual(n, MAX_CHARS, f"chunk {i} has {n}")
            if i + 1 < len(chunks):
                self.assertGreaterEqual(n, MIN_CHARS, f"chunk {i} has {n}")
            self.assertEqual(c["ordinal"], i)
            self.assertTrue(c["body"].startswith("[docs/a.md \u00b7 doc \u00b7 a.md]\n"))
        # Nothing is lost and no paragraph is cut.
        all_body = "\n\n".join(body_of(c) for c in chunks)
        self.assertEqual(all_body, "\n\n".join(para(500, chr(ord('a') + i)) for i in range(12)))

    def test_a_heading_starts_a_chunk_once_the_last_one_is_big_enough(self):
        big = para(900, 'x')
        text = f"# One\n\n{big}\n\n## Two\n\nshort tail paragraph\n\n{big}"
        chunks = cl.chunk("a.md", "doc", text)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0]["title"], "One")
        self.assertEqual(chunks[1]["title"], "Two")
        self.assertIn("## Two", chunks[1]["body"])
        small = cl.chunk("a.md", "doc", "# One\n\nhi\n\n## Two\n\nthere")
        self.assertEqual(len(small), 1)

    def test_code_breaks_at_declarations_and_titles_them(self):
        f1 = "fn first() {\n    " + para(900, 'a') + "\n}"
        f2 = "fn second() {\n    " + para(900, 'b') + "\n}"
        chunks = cl.chunk("src/lib.rs", "code", f1 + "\n" + f2)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0]["title"], "fn first() {")
        self.assertEqual(chunks[1]["title"], "fn second() {")
        self.assertIn("code \u00b7 fn second() {", chunks[1]["body"])

    def test_oversized_blocks_and_lines_are_cut_to_fit(self):
        long_line = para(5000, 'z')
        chunks = cl.chunk("big.log", "log", long_line)
        self.assertEqual(len(chunks), 3)
        self.assertTrue(all(len(body_of(c)) <= MAX_CHARS for c in chunks))
        self.assertEqual(cl.chunk("e.md", "doc", "  \n\n"), [])

    def test_header_and_titles(self):
        self.assertEqual(cl.header("src/a.rs", "code", "t"), "[src/a.rs \u00b7 code \u00b7 t]")
        c = cl.chunk("d.md", "doc", "# A\n\nbody text here")
        self.assertEqual(c[0]["title"], "A")


class WalkRules(unittest.TestCase):
    """The accept rules from index.rs: secret-like names, over-1MB, binary (NUL in the first 8192
    bytes), non-UTF-8, empty; kind by extension. .git/.offrig are never walked."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel: str, data: bytes):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def rels(self):
        return {rel: why for rel, kind, text, why in cl.walk_accept(self.root)}, \
               {rel: kind for rel, kind, text, why in cl.walk_accept(self.root)}

    def test_accept_and_skip_reasons(self):
        self.write("src/a.mjs", b"const x = 1;\n")
        self.write("notes.md", b"# hi\n\nsome prose\n")
        self.write("run.log", b"a log line\n")
        self.write(".env.local", b"SECRET=1\n")
        self.write("id_rsa", b"not really a key\n")
        self.write("my-credentials.txt", b"nope\n")
        self.write("cert.pem", b"-----BEGIN\n")
        self.write("blob.bin", b"ab\x00cd\n")
        self.write("broken.txt", b"\xff\xfe invalid\n")
        self.write("blank.txt", b"   \n\n")
        self.write(".git/ignored.mjs", b"const hidden = 1;\n")
        self.write(".offrig/offrig.db", b"junk\n")
        skips, kinds = self.rels()
        self.assertEqual(skips[".env.local"], "secrets-like file")
        self.assertEqual(skips["id_rsa"], "secrets-like file")
        self.assertEqual(skips["my-credentials.txt"], "secrets-like file")
        self.assertEqual(skips["cert.pem"], "secrets-like file")
        self.assertEqual(skips["blob.bin"], "binary")
        self.assertEqual(skips["broken.txt"], "not UTF-8 text")
        self.assertEqual(skips["blank.txt"], "empty")
        self.assertNotIn(".git/ignored.mjs", skips)
        self.assertNotIn(".offrig/offrig.db", skips)
        self.assertEqual(kinds["src/a.mjs"], "code")
        self.assertEqual(kinds["notes.md"], "doc")
        self.assertEqual(kinds["run.log"], "log")

    def test_over_1mb(self):
        big = b"x" * (cl.MAX_FILE_BYTES + 1)
        self.write("big.txt", big)
        skips, _ = self.rels()
        self.assertEqual(skips["big.txt"], "over 1 MB")

    def test_secret_like_name_set_matches_rust(self):
        for name, is_secret in [(".env", True), (".env.production", True), ("id_ed25519", True),
                                ("aws-credentials.json", True), ("a.p12", True), ("a.pfx", True),
                                ("a.key", True), ("notes.md", False), ("identifier.mjs", False),
                                ("keynote.txt", False)]:
            self.assertEqual(cl.secret_like(name), is_secret, name)


if __name__ == "__main__":
    unittest.main()


class BucketLadderMatchesTheMeasurement(unittest.TestCase):
    """npu_serve's nomic ladder must cover the measured corpus max; if either side moves without the
    other, this goes red."""

    def test_nomic_top_rung_covers_the_measured_max(self):
        import json
        # npu_serve imports numpy/openvino at module level; read the spec constant without importing.
        src = (PROBE / "npu_serve.py").read_text(encoding="utf-8")
        self.assertIn('"buckets": (128, 256, 512, 1024, 2048)', src)
        receipt = json.loads((PROBE / "results" / "2026-10-09-nomic-chunk-lengths.json")
                             .read_text(encoding="utf-8"))
        observed_max = receipt["decision"]["observed_max_tokens"]
        self.assertLessEqual(observed_max, 2048)
        self.assertEqual(receipt["decision"]["suggested_bucket"], 2048)
        self.assertLessEqual(receipt["queries"]["tokens"]["max"], 512)
