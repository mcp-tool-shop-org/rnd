"""snapshot.py's manual-read check: a hand-read entry passes only while its saved copy hashes and quotes as recorded."""

import contextlib
import hashlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "licence_snapshot", Path(__file__).resolve().parents[1] / "licences" / "snapshot.py")
snapshot = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(snapshot)

TEXT = "Policy text. Works made here are not subject to copyright protection within the country. More text."


def entry(**kw):
    e = {"id": "x", "read_date": "2026-11-15", "read_method": "manual", "snapshot_file": "d/x.txt",
         "snapshot_sha256": hashlib.sha256(TEXT.encode("utf-8")).hexdigest(),
         "clauses": ["not subject to copyright protection within the country"]}
    e.update(kw)
    return e


class ManualRead(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "d").mkdir()
        (self.root / "d" / "x.txt").write_text("https://example.org/x.pdf\n\n" + TEXT, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_check(self, e):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            rc = snapshot.check_manual(e, self.root)
        return rc, out.getvalue()

    def test_matching_copy_passes(self):
        rc, out = self.run_check(entry())
        self.assertEqual(rc, 0, out)
        self.assertIn("copy sha256 ok clauses 1/1", out)

    def test_changed_copy_fails(self):
        rc, out = self.run_check(entry(snapshot_sha256="0" * 64))
        self.assertEqual(rc, 1)
        self.assertIn("MISMATCH", out)

    def test_missing_clause_fails(self):
        rc, out = self.run_check(entry(clauses=["a sentence the copy does not hold"]))
        self.assertEqual(rc, 1)
        self.assertIn("MISSING", out)

    def test_no_clause_fails(self):
        rc, _ = self.run_check(entry(clauses=[]))
        self.assertEqual(rc, 1)

    def test_missing_copy_fails(self):
        rc, out = self.run_check(entry(snapshot_file="d/absent.txt"))
        self.assertEqual(rc, 1)
        self.assertIn("saved copy not found", out)


if __name__ == "__main__":
    unittest.main()
