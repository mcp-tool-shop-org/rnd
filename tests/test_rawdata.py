"""rnd-data: ingest into the public store and its private companion, the blob store, tagging, and verify."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mcptoolshop_rnd import layout, rawdata

from .test_cli import CliBase
from .test_rnd import write

TAG = "T5-PRIVATE-" + "DO-NOT-PUBLISH"


def make_stores(base: Path):
    public, private, blobs = base / "rnd-data", base / "rnd-data-private", base / "blobs-root"
    write(public, "store.json", json.dumps({"schema": "rnd-data-store/v1"}))
    write(private, "README.md", "# private\n")
    blobs.mkdir()
    return public, private, blobs


def make_receipts(base: Path) -> Path:
    src = base / "receipts"
    write(src, "colab/window1-20261016/outcome.json", json.dumps({"window": "1"}))
    write(src, "colab/window1-20261016/job.log", "ran fine\n")
    write(src, "colab/window1-20261016/try1/outcome.json", json.dumps({"window": "1-try1"}))
    write(src, "colab/window1-20261016/launch.out", "C:/" + "Users/someone/x\n")  # identity
    write(src, "colab/window1-20261016/blind_key.json", "{}")                    # auto: blind
    (src / "colab/window1-20261016/big.bin").write_bytes(b"x" * (rawdata.SMALL_LIMIT + 1))
    write(src, "colab/window2-20261017/notes.txt", "no outcome here\n")
    (src / "colab/window2-20261017/big-copy.bin").write_bytes(b"x" * (rawdata.SMALL_LIMIT + 1))  # same bytes
    write(src, "colab/units-ledger.md", "ledger\n")
    write(src, "commandui/log.txt", "other product\n")
    write(src, "README.txt", "top\n")
    return src


class IngestTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.base, True)
        self.public, self.private, self.blobs = make_stores(self.base)
        self.src = make_receipts(self.base)
        env = mock.patch.dict(os.environ, {"RND_DATA_STORE_D": str(self.blobs)})
        env.start()
        self.addCleanup(env.stop)
        reasons = {"colab/window1-20261016/launch.out": "identity"}

        def classify(rel):
            return reasons.get(rel) or ("blind" if layout.private_name(rel) else None)
        self.classify = classify

    def ingest(self, **kw):
        return rawdata.ingest_tree(self.src, self.public, self.private, "receipts", self.classify, **kw)

    def manifest(self, rid):
        return json.loads((self.public / "runs" / rid / "manifest.json").read_text(encoding="utf-8"))

    def test_groups_split_and_blobs(self):
        st = self.ingest(link=False, commit="abc")
        ids = sorted(p.parent.name for p in (self.public / "runs").glob("*/manifest.json"))
        self.assertEqual(ids, ["receipts", "receipts--colab", "receipts--colab--window1-20261016",
                               "receipts--colab--window1-20261016--try1", "receipts--colab--window2-20261017",
                               "receipts--commandui"])
        m = self.manifest("receipts--colab--window1-20261016")
        by_path = {f["path"]: f for f in m["files"]}
        self.assertEqual(by_path["launch.out"]["visibility"], "private")
        self.assertIsNone(by_path["launch.out"]["sha256"])        # identity: listed, no hash
        self.assertNotIn("blind_key.json", by_path)               # content reason: counted, not listed
        self.assertEqual(m["private_files"], {"blind": 1})
        self.assertEqual(m["rnd_commit"], "abc")
        self.assertTrue((self.public / "runs/receipts--colab--window1-20261016/files/job.log").is_file())
        self.assertFalse((self.public / "runs/receipts--colab--window1-20261016/files/launch.out").exists())
        self.assertTrue((self.private / "runs/receipts--colab--window1-20261016/launch.out").is_file())
        self.assertEqual(st["blobs_copied"], 1)
        self.assertEqual(st["blobs_present"], 1)                  # the second copy of the same bytes
        self.assertEqual(len(list(self.blobs.glob("blobs/*/*"))), 1)
        pm = json.loads((self.private / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual({f["reason"] for f in pm["files"]}, {"identity", "blind"})
        self.assertEqual(rawdata.verify(self.public, self.private, deep=True), [])

    def test_hardlink_is_the_same_file(self):
        self.ingest()
        sha = rawdata.sha256_file(self.src / "colab/window1-20261016/big.bin")
        self.assertTrue(os.path.samefile(self.blobs / rawdata.blob_rel(sha), self.src / "colab/window1-20261016/big.bin"))

    def test_rerun_is_unchanged_and_a_changed_source_is_refused(self):
        self.ingest(link=False)
        self.assertEqual(self.ingest(link=False)["unchanged"], 6)
        write(self.src, "colab/window1-20261016/job.log", "edited\n")
        with self.assertRaises(rawdata.RawError) as ctx:
            self.ingest(link=False)
        self.assertEqual(ctx.exception.code, "RUN_CHANGED")

    def test_update_replaces_a_changed_run_and_drops_what_it_no_longer_has(self):
        self.ingest(link=False)
        write(self.src, "colab/window1-20261016/job.log", "corrected\n")
        (self.src / "colab/window1-20261016/launch.out").unlink()            # a private file moved away
        st = self.ingest(link=False, update=True)
        self.assertEqual((st["updated"], st["unchanged"]), (1, 5))
        m = self.manifest("receipts--colab--window1-20261016")
        self.assertNotIn("launch.out", {f["path"] for f in m["files"]})
        self.assertEqual((self.public / "runs/receipts--colab--window1-20261016/files/job.log").read_bytes(),
                         (self.src / "colab/window1-20261016/job.log").read_bytes())
        pm = json.loads((self.private / "manifest.json").read_text(encoding="utf-8"))
        self.assertNotIn("runs/receipts--colab--window1-20261016/launch.out", {f["path"] for f in pm["files"]})
        self.assertFalse((self.private / "runs/receipts--colab--window1-20261016/launch.out").exists())
        self.assertEqual(rawdata.verify(self.public, self.private), [])

    def test_dry_run_writes_nothing(self):
        st = self.ingest(dry_run=True)
        self.assertEqual(st["runs"], 6)
        self.assertFalse((self.public / "runs").exists())
        self.assertFalse((self.private / "manifest.json").exists())

    def test_verify_finds_damage_and_a_published_private_hash(self):
        self.ingest(link=False)
        (self.public / "runs/receipts--colab--window1-20261016/files/job.log").write_text("tampered")
        sha = rawdata.sha256_file(self.src / "colab/window1-20261016/big.bin")
        (self.blobs / rawdata.blob_rel(sha)).write_bytes(b"short")
        mp = self.public / "runs/receipts/manifest.json"
        m = json.loads(mp.read_text())
        m["files"].append({"path": "x", "sha256": "a" * 64, "bytes": 1, "visibility": "private"})
        mp.write_text(json.dumps(m))
        problems = " | ".join(rawdata.verify(self.public, self.private))
        self.assertIn("hash differs", problems)
        self.assertIn("size differs", problems)
        self.assertIn("is private but its hash is published", problems)
        self.assertEqual(rawdata.verify(self.public, run="nope"), ["no run 'nope' in this store"])

    def test_bad_inputs(self):
        with self.assertRaises(rawdata.RawError):
            rawdata.ingest_tree(self.src, self.base / "nowhere", self.private, "r", self.classify)
        with self.assertRaises(rawdata.RawError):
            rawdata.ingest_tree(self.src, self.public, self.private, "r", lambda rel: "secret-ish")
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(rawdata.RawError) as ctx:
                rawdata.store_root(self.public)
            self.assertEqual(ctx.exception.code, "NO_STORE_ROOT")
            write(self.public, "store.local.json", json.dumps({"d": str(self.blobs)}))
            self.assertEqual(rawdata.store_root(self.public), self.blobs)
            write(self.public, "store.local.json", "{bad")
            with self.assertRaises(rawdata.RawError):
                rawdata.store_root(self.public)


class PrivateSourceTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.base, True)
        _, self.private, _ = make_stores(self.base)
        self.src = self.base / "rnd-local"
        write(self.src, "critic-signal/notes.md", "# notes\n")
        write(self.src, "critic-signal/items.jsonl", '{"a": 1}\n')
        write(self.src, "critic-signal/pinned.md", "# pinned\n")
        write(self.src, "projects/repo-scale/PLAN.md", "# the approved plan\n")
        write(self.src, "projects/skip/x.md", "excluded\n")

    def test_reasons_tags_and_pins(self):
        pinned = rawdata.sha256_file(self.src / "critic-signal/pinned.md")[:8]
        classify = lambda rel: None if rel.startswith("projects/repo-scale/") else "item-text"  # noqa: E731
        st = rawdata.ingest_private(self.src, self.private, "rnd-local", classify, pinned_text=f"pin {pinned}",
                                    exclude=("projects/skip",))
        self.assertEqual((st["private"], st["public_skipped"], st["tagged"], st["pinned_untagged"],
                          st["data_untagged"], st["excluded"]), (3, 1, 1, 1, 1, 1))
        m = json.loads((self.private / "manifest.json").read_text(encoding="utf-8"))
        f = {e["path"]: e for e in m["files"]}
        notes = f["private/rnd-local/critic-signal/notes.md"]
        self.assertTrue(notes["tagged"])
        self.assertTrue((self.private / notes["path"]).read_text().startswith(f"<!-- {TAG} -->"))
        self.assertEqual(notes["source_sha256"], rawdata.sha256_file(self.src / "critic-signal/notes.md"))
        self.assertIn("pinned elsewhere", f["private/rnd-local/critic-signal/pinned.md"]["untagged_why"])
        self.assertIn("data file", f["private/rnd-local/critic-signal/items.jsonl"]["untagged_why"])
        self.assertEqual((self.private / "private/rnd-local/critic-signal/items.jsonl").read_bytes(),
                         (self.src / "critic-signal/items.jsonl").read_bytes())
        with self.assertRaises(rawdata.RawError):
            rawdata.ingest_private(self.src, self.private, "rnd-local", classify)
        with self.assertRaises(rawdata.RawError):
            rawdata.ingest_private(self.src, self.private, "other", lambda rel: "nope")
        with self.assertRaises(rawdata.RawError):
            rawdata.ingest_private(self.src, self.base / "nowhere", "x", classify)
        self.assertEqual(rawdata.verify(self.base / "rnd-data", self.private), [])

    def test_the_library_check_reads_the_companion(self):
        lib = self.base / "lib"
        write(lib, "entries/x.md", "# notes\n")  # the untagged original of a tagged private note
        rawdata.ingest_private(self.src, self.private, "rnd-local", lambda rel: "item-text")
        with mock.patch.dict(os.environ, {"RND_DATA_PRIVATE": str(self.private)}):
            hashes, problem = layout.private_manifest(lib)
        self.assertIsNone(problem)
        self.assertIn(rawdata.sha256_file(self.src / "critic-signal/notes.md"), hashes)


class RawCommandTests(CliBase):
    def setUp(self):
        super().setUp()
        self.public, self.private, self.blobs = make_stores(self.root / "stores")
        self.src = make_receipts(self.root / "in")
        env = mock.patch.dict(os.environ, {"RND_DATA_STORE_D": str(self.blobs), "RND_DATA": str(self.public),
                                           "RND_DATA_PRIVATE": str(self.private)})
        env.start()
        self.addCleanup(env.stop)

    def test_ingest_private_verify_and_where(self):
        reasons = write(self.root, "reasons.json", json.dumps({"colab/window1-20261016/launch.out": "identity",
                                                               "commandui/": "unapproved"}))
        code, out, err = self.run_cli("raw", "ingest", str(self.src), "--prefix", "receipts", "--reasons", str(reasons),
                                      "--copy", "--dry-run")
        self.assertEqual(code, 0, err)
        self.assertIn("would ingest: runs 6", out)
        code, out, err = self.run_cli("raw", "ingest", str(self.src), "--prefix", "receipts", "--reasons", str(reasons),
                                      "--copy")
        self.assertEqual(code, 0, err)
        m = json.loads((self.public / "runs/receipts--commandui/manifest.json").read_text())
        self.assertEqual((m["files"], m["private_files"]), ([], {"unapproved": 1}))
        code, out, _ = self.run_cli("raw", "verify", "--deep")
        self.assertEqual(code, 0, out)
        self.assertIn("0 problems", out)
        self.assertIn("as rnd-data:receipts--colab--window1-20261016:job.log", self.run_cli("where", "job.log")[1])
        code, out, _ = self.run_cli("where", "launch.out", "--json")
        self.assertEqual(json.loads(out)[0]["tier"], "T5")
        src2 = self.root / "local"
        write(src2, "a/plan.md", "# plan\n")
        code, out, err = self.run_cli("raw", "private", str(src2), "--as", "rnd-local")
        self.assertEqual(code, 0, err)
        self.assertIn("public_skipped 1", out)
        (self.public / "runs/receipts/files/README.txt").write_text("tampered")
        self.assertEqual(self.run_cli("raw", "verify")[0], 1)

    def test_usage(self):
        self.assertEqual(self.run_cli("raw", "ingest")[0], 2)
        self.assertEqual(self.run_cli("raw", "ingest", str(self.src))[0], 2)
        self.assertEqual(self.run_cli("raw", "private", str(self.src))[0], 2)
        bad = write(self.root, "bad.json", "[1]")
        self.assertEqual(self.run_cli("raw", "ingest", str(self.src), "--prefix", "r", "--reasons", str(bad))[0], 1)
        self.assertEqual(self.run_cli("raw", "ingest", str(self.src), "--prefix", "r", "--reasons", "missing.json")[0], 1)
