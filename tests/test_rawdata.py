"""rnd-data: ingest into the public store and its private companion, the blob store, tagging, and verify."""

import contextlib
import io
import json
import os
import shutil
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mcptoolshop_rnd import layout, rawdata

from .test_cli import CliBase
from .test_rnd import write

TAG = "T5-PRIVATE-" + "DO-NOT-PUBLISH"


def rmtree_force(path):
    """Blobs are read-only, and Windows won't delete a read-only file: clear the flag, then delete."""
    def unlock(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    shutil.rmtree(path, onerror=unlock)


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
        self.addCleanup(rmtree_force, self.base)
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

    def test_hardlink_is_the_same_file_and_read_only(self):
        self.ingest(link=True)
        sha = rawdata.sha256_file(self.src / "colab/window1-20261016/big.bin")
        blob = self.blobs / rawdata.blob_rel(sha)
        self.assertTrue(os.path.samefile(blob, self.src / "colab/window1-20261016/big.bin"))
        with self.assertRaises(PermissionError):
            blob.open("ab").write(b"an append through either name")  # the Publisher's case: it must not land

    def test_a_live_tree_is_copied_by_default(self):
        self.ingest()
        sha = rawdata.sha256_file(self.src / "colab/window1-20261016/big.bin")
        blob = self.blobs / rawdata.blob_rel(sha)
        self.assertFalse(os.path.samefile(blob, self.src / "colab/window1-20261016/big.bin"))
        with open(self.src / "colab/window1-20261016/big.bin", "ab") as f:
            f.write(b"appended to the live file")                      # the source keeps working...
        self.assertEqual(rawdata.sha256_file(blob), sha)                 # ...and the blob is untouched
        with self.assertRaises(PermissionError):
            blob.open("ab").write(b"x")

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
        os.chmod(self.blobs / rawdata.blob_rel(sha), stat.S_IWRITE)  # damage it on purpose
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
        self.addCleanup(rmtree_force, self.base)
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
                                      "--dry-run")
        self.assertEqual(code, 0, err)
        self.assertIn("would ingest: runs 6", out)
        code, out, err = self.run_cli("raw", "ingest", str(self.src), "--prefix", "receipts", "--reasons", str(reasons))
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


RULES = Path(__file__).resolve().parent.parent / "docs" / "raw-data-rules" / "receipts.json"


class ReceiptRulesTests(unittest.TestCase):
    """The Publisher's P3 review classes, against the real rules file: each lands where it must."""

    def setUp(self):
        self.base = Path(tempfile.mkdtemp())
        self.addCleanup(rmtree_force, self.base)
        self.src = self.base / "receipts"
        w = "colab/window14b-x-20261019"
        self.files = {
            # must be private
            f"{w}/critic-eval-inputs.tar.gz": "item-text",
            f"{w}/out/items.jsonl": "item-text",
            f"{w}/out/items.jsonl.sha256": "item-text",
            f"{w}/pilot-out.tar": "item-text",
            f"{w}/timing/gw/drafts.jsonl": "item-text",
            f"{w}/midpoint/generations-w0.jsonl": "item-text",
            f"{w}/out/pilot/lesson-T02-plan.json": "item-text",
            "colab/window13t-rescore-20261018/out/rescore/rescore.log": "item-text",
            "colab/window13t-rescore-20261018/rescore-out.tar": "item-text",
            f"{w}/critic-eval-out.json": "item-text",
            f"{w}/job-with-checkpoints.log": "item-text",
            # public by the Director's ruling (2026-10-19): R&D's benchmark data; held-out there is a calibration split
            "verifier-gold/README.md": None,
            "verifier-gold/reasoning-prs-2026-10-08.jsonl": None,
            "colab/window7b-20261017/known-answer-v1.jsonl": None,
            f"{w}/blind_key.json": "blind",
            "commandui/wack-report.xml": "unapproved",
            f"{w}/notes.md": "unapproved",
            f"{w}/launch.out": "identity",
            # public
            f"{w}/outcome.json": None,
            f"{w}/gate.jsonl": None,
            f"{w}/job.log": None,
            f"{w}/launch.sh": None,
            f"{w}/upload/llama-server.gz.part00": None,
            "colab/units-ledger.md": None,
        }
        for rel in self.files:
            body = "plain\n"
            if rel.endswith("job-with-checkpoints.log"):
                body = "step 1\nCALL_CHECKPOINT H4sIAAAA...\n"
            write(self.src, rel, body)
        self.rules = rawdata.load_rules(RULES)
        self.classify, self.licence_for = rawdata.rules_classifier(self.rules, self.src,
                                                                   {f"{w}/launch.out": "identity"})

    def test_every_class_lands_where_it_must(self):
        got = {rel: self.classify(rel) for rel in self.files}
        self.assertEqual(got, self.files)

    def test_licences_and_run_kinds(self):
        self.assertEqual(self.licence_for("colab/w/upload/llama-server.gz"), "MIT (llama.cpp, commit 620d2225)")
        # The Director's ruling (2026-10-19): rnd-data is licensed like rnd. First match wins.
        self.assertEqual(self.licence_for("colab/w/job.log"), "CC-BY-4.0")
        self.assertEqual(self.licence_for("colab/w/launch.sh"), "MIT")
        self.assertEqual(self.licence_for("colab/w/scripts/collect.py"), "MIT")
        self.assertTrue(self.licence_for("verifier-gold/reasoning-prs-2026-10-08.jsonl").startswith("CC-BY-4.0 (the code"))
        self.assertEqual(self.licence_for("verifier-gold/build.py"), "MIT")  # a script stays MIT, above the gold rule
        public, private, blobs = make_stores(self.base)
        with mock.patch.dict(os.environ, {"RND_DATA_STORE_D": str(blobs)}):
            rawdata.ingest_tree(self.src, public, private, "receipts", self.classify, licence_for=self.licence_for,
                                link=False)
        kinds = {p.parent.name: json.loads(p.read_text())["kind"] for p in (public / "runs").glob("*/manifest.json")}
        self.assertEqual(kinds["receipts--colab--window14b-x-20261019"], "run")
        self.assertEqual(kinds["receipts--verifier-gold"], "collection")
        m = json.loads((public / "runs/receipts--colab--window14b-x-20261019/manifest.json").read_text())
        public_paths = {f["path"] for f in m["files"] if f["visibility"] == "public"}
        self.assertEqual(public_paths, {"outcome.json", "gate.jsonl", "job.log", "launch.sh",
                                        "upload/llama-server.gz.part00"})
        self.assertEqual({f["path"]: f["licence"] for f in m["files"]}["upload/llama-server.gz.part00"],
                         "MIT (llama.cpp, commit 620d2225)")
        self.assertEqual(rawdata.verify(public, private), [])

    def test_bad_rules_are_refused(self):
        for bad in ({"schema": "x"}, {"schema": rawdata.RULES_SCHEMA, "default": "nope"},
                    {"schema": rawdata.RULES_SCHEMA, "default": "unapproved", "public": [{"why": "no pattern"}]}):
            p = write(self.base, "r.json", json.dumps(bad))
            with self.assertRaises(rawdata.RawError):
                rawdata.load_rules(p)
        with self.assertRaises(rawdata.RawError):
            rawdata.load_rules(self.base / "missing.json")

    def test_a_marker_split_across_chunks_is_found(self):
        p = self.base / "big.log"
        with mock.patch.object(rawdata, "_has_marker", wraps=rawdata._has_marker):
            p.write_bytes(b"x" * ((8 << 20) - 5) + b"CALL_CHECKPOINT")
            self.assertTrue(rawdata._has_marker(p, b"CALL_CHECKPOINT"))
            p.write_bytes(b"x" * ((8 << 20) + 10))
            self.assertFalse(rawdata._has_marker(p, b"CALL_CHECKPOINT"))


class PublicOnlyAndRelicenseTests(unittest.TestCase):
    """What a public clone (CI) can check, and reapplying a rules file's licences in place."""

    def setUp(self):
        self.base = Path(tempfile.mkdtemp())
        self.addCleanup(rmtree_force, self.base)
        self.public, self.private, self.blobs = make_stores(self.base)
        self.src = make_receipts(self.base)
        self.reasons = {"colab/window1-20261016/launch.out": "identity"}
        with mock.patch.dict(os.environ, {"RND_DATA_STORE_D": str(self.blobs)}):
            rawdata.ingest_tree(self.src, self.public, self.private, "receipts", self.classify)

    def classify(self, rel):
        return self.reasons.get(rel) or ("blind" if layout.private_name(rel) else None)

    def verify(self, **kw):
        """As a public clone sees it: no blob store configured."""
        skipped = {}
        with mock.patch.dict(os.environ, {}):
            os.environ.pop("RND_DATA_STORE_D", None)
            return rawdata.verify(self.public, self.private, public_only=True, skipped=skipped, **kw), skipped

    def test_a_clean_clone_passes_and_counts_what_it_skipped(self):
        problems, skipped = self.verify()
        self.assertEqual(problems, [])
        self.assertEqual(skipped, {"d": 2})  # the two big files, both blobs
        with mock.patch.dict(os.environ, {}):
            os.environ.pop("RND_DATA_STORE_D", None)
            self.assertIn("no root for store 'd'", " ".join(rawdata.verify(self.public, self.private)))

    def test_it_still_rehashes_git_copies(self):
        (self.public / "runs/receipts--colab--window1-20261016/files/job.log").write_text("tampered")
        self.assertIn("hash differs", " ".join(self.verify()[0]))

    def test_the_tree_rules(self):
        write(self.public, "runs/receipts/files/stray.txt", "named by no manifest\n")
        write(self.public, "runs/receipts--colab/files/note.md", "<!-- " + TAG + " -->\nprivate\n")
        write(self.public, "site/sealed_answers.json", "{}")
        write(self.public, "SECURITY.md", "Report a file carrying " + TAG + ".\n")  # a page naming the tag is fine
        mp = self.public / "runs/receipts/manifest.json"
        m = json.loads(mp.read_text(encoding="utf-8"))
        m["licence_note"] = "copied from C:/" + "Users/someone/run"
        mp.write_text(json.dumps(m), encoding="utf-8")
        problems = " | ".join(self.verify()[0])
        self.assertIn("runs/receipts/files/stray.txt: under runs/ but named by no manifest", problems)
        self.assertIn("runs/receipts--colab/files/note.md: carries the private tag", problems)
        self.assertIn("site/sealed_answers.json: the name looks private", problems)
        self.assertIn("runs/receipts/manifest.json:1: a drive or machine path", problems)
        self.assertIn("runs/receipts/manifest.json:1: a home-directory path", problems)
        self.assertNotIn("SECURITY.md", problems)

    def test_one_run_skips_the_tree_rules(self):
        write(self.public, "runs/receipts/files/stray.txt", "x\n")
        self.assertEqual(self.verify(run="receipts")[0], [])

    def test_relicense_changes_only_the_licence_field(self):
        before = {p: p.read_bytes() for p in (self.public / "runs").rglob("*") if p.is_file()}
        rules = rawdata.load_rules(RULES)
        dry = rawdata.relicense(self.public, rules, "receipts", dry_run=True)
        self.assertEqual({p: p.read_bytes() for p in before}, before)  # a dry run writes nothing
        st = rawdata.relicense(self.public, rules, "receipts")
        self.assertEqual(st, dry)
        self.assertGreater(st["files_changed"], 0)
        for p, old in before.items():
            if p.name != "manifest.json":
                self.assertEqual(p.read_bytes(), old)  # no data file is touched
                continue
            a, b = json.loads(old), json.loads(p.read_bytes())
            for e in b["files"]:
                if e["visibility"] != "public":
                    self.assertIsNone(e["licence"])  # a private entry stays null
            for e in a["files"] + b["files"]:
                if e["visibility"] == "public":
                    e["licence"] = None
            self.assertEqual(a, b)  # nothing else changed
        m = json.loads((self.public / "runs/receipts--colab--window1-20261016/manifest.json").read_text())
        self.assertEqual({f["path"]: f["licence"] for f in m["files"]}["job.log"], "CC-BY-4.0")
        self.assertEqual(rawdata.relicense(self.public, rules, "receipts")["files_changed"], 0)  # idempotent
        self.assertEqual(self.verify()[0], [])
        with self.assertRaises(rawdata.RawError) as ctx:
            rawdata.relicense(self.public, rules, "nothing-here")
        self.assertEqual(ctx.exception.code, "NO_RUNS")

    def test_an_ingest_after_relicense_is_unchanged(self):
        rules = rawdata.load_rules(RULES)
        rawdata.relicense(self.public, rules, "receipts")
        _, licence_for = rawdata.rules_classifier(rules, self.src, {})
        with mock.patch.dict(os.environ, {"RND_DATA_STORE_D": str(self.blobs)}):
            st = rawdata.ingest_tree(self.src, self.public, self.private, "receipts", self.classify,
                                     licence_for=licence_for)
        self.assertEqual(st["unchanged"], 6)


class RawPublicOnlyCommandTests(CliBase):
    def setUp(self):
        super().setUp()
        self.public, self.private, self.blobs = make_stores(self.root / "stores")
        src = make_receipts(self.root / "in")
        with mock.patch.dict(os.environ, {"RND_DATA_STORE_D": str(self.blobs)}):
            rawdata.ingest_tree(src, self.public, self.private, "receipts",
                                lambda rel: "identity" if rel.endswith("launch.out")  # it holds a home path
                                else ("blind" if layout.private_name(rel) else None))
        env = mock.patch.dict(os.environ, {"RND_DATA": str(self.public), "RND_DATA_PRIVATE": str(self.private)})
        env.start()
        self.addCleanup(env.stop)

    def test_verify_public_only_and_relicense(self):
        code, out, err = self.run_cli("raw", "verify", "--public-only")
        self.assertEqual(code, 0, err)
        self.assertIn("verified rnd-data, public only (copies skipped: 2 in store d): 0 problems", out)
        self.assertEqual(self.run_cli("raw", "verify", "--public-only", "--deep")[0], 2)
        code, out, err = self.run_cli("raw", "relicense", "--rules", str(RULES), "--prefix", "receipts", "--dry-run")
        self.assertEqual(code, 0, err)
        self.assertIn("would relicense: manifests 6", out)
        code, out, err = self.run_cli("raw", "relicense", "--rules", str(RULES), "--prefix", "receipts")
        self.assertEqual(code, 0, err)
        self.assertIn("relicensed: manifests 6", out)
        self.assertEqual(self.run_cli("raw", "relicense", "--prefix", "receipts")[0], 2)
        self.assertEqual(self.run_cli("raw", "relicense", "--rules", str(RULES), "--prefix", "none")[0], 1)


class RawWithoutLibraryTests(unittest.TestCase):
    """rnd-data's CI installs rnd and runs `rnd raw verify --public-only` in an rnd-data checkout, with no library."""

    def setUp(self):
        self.base = Path(tempfile.mkdtemp())
        self.addCleanup(rmtree_force, self.base)
        self.public, self.private, self.blobs = make_stores(self.base)
        src = make_receipts(self.base)
        with mock.patch.dict(os.environ, {"RND_DATA_STORE_D": str(self.blobs)}):
            rawdata.ingest_tree(src, self.public, self.private, "receipts",
                                lambda rel: "identity" if rel.endswith("launch.out")  # it holds a home path
                                else ("blind" if layout.private_name(rel) else None))

    def main(self, *argv, env=None):
        from mcptoolshop_rnd import cli
        out, err = io.StringIO(), io.StringIO()
        clean = {k: v for k, v in os.environ.items()
                 if k not in ("RND_ROOT", "RND_DATA", "RND_DATA_PRIVATE", "RND_DATA_STORE_D")}
        with mock.patch.object(cli, "ROOT", None), mock.patch.dict(os.environ, {**clean, **(env or {})}, clear=True), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_raw_runs_on_rnd_data_alone(self):
        code, out, err = self.main("raw", "verify", "--public-only", env={"RND_DATA": str(self.public)})
        self.assertEqual(code, 0, err)
        self.assertIn("public only (copies skipped: 2 in store d): 0 problems", out)
        code, out, err = self.main("raw", "verify", "--public-only", "--public", str(self.public))
        self.assertEqual(code, 0, err)
        # The full check finds the companion beside the store, and still needs the blob store's root.
        code, out, err = self.main("raw", "verify", env={"RND_DATA": str(self.public), "RND_DATA_STORE_D": str(self.blobs)})
        self.assertEqual(code, 0, err)
        self.assertIn("verified rnd-data and rnd-data-private: 0 problems", out)

    def test_the_companion_can_be_named_without_a_library(self):
        moved = self.base / "elsewhere" / "rnd-data-private"
        shutil.move(str(self.private), str(moved))                       # no longer beside the store
        env = {"RND_DATA": str(self.public), "RND_DATA_STORE_D": str(self.blobs)}
        code, out, err = self.main("raw", "verify", env={**env, "RND_DATA_PRIVATE": str(moved)})
        self.assertEqual(code, 0, err)
        self.assertIn("verified rnd-data and rnd-data-private: 0 problems", out)
        code, out, err = self.main("raw", "verify", "--private", str(moved), env=env)
        self.assertEqual(code, 0, err)
        self.assertIn("and rnd-data-private", out)
        code, out, err = self.main("raw", "verify", env=env)              # beside the store: not there now
        self.assertEqual(code, 0, err)
        self.assertIn("verified rnd-data: 0 problems", out)

    def test_without_a_named_store_it_still_needs_a_library(self):
        code, _, err = self.main("raw", "verify", "--public-only")
        self.assertEqual(code, 2)
        self.assertIn("NO_LIBRARY", err)
        self.assertEqual(self.main("stats", env={"RND_DATA": str(self.public)})[0], 2)  # only raw is exempt


class ProtectionRoundOneTests(unittest.TestCase):
    """Argon's rnd-data protection audit, round 1 (F1-F4): each rule fails on its planted defect, and only there."""

    def setUp(self):
        self.base = Path(tempfile.mkdtemp())
        self.addCleanup(rmtree_force, self.base)
        self.public, self.private, self.blobs = make_stores(self.base)
        src = make_receipts(self.base)
        with mock.patch.dict(os.environ, {"RND_DATA_STORE_D": str(self.blobs)}):
            rawdata.ingest_tree(src, self.public, self.private, "receipts",
                                lambda rel: "identity" if rel.endswith("launch.out")  # it holds a home path
                                else ("blind" if layout.private_name(rel) else None))
        self.run_dir = self.public / "runs/receipts--colab--window1-20261016"

    def problems(self):
        with mock.patch.dict(os.environ, {}):
            os.environ.pop("RND_DATA_STORE_D", None)
            return " | ".join(rawdata.verify(self.public, self.private, public_only=True))

    def plant_named(self, inner, body):
        """A file under runs/ that its manifest names, so only the planted rule can fire."""
        data = body if isinstance(body, bytes) else body.encode()
        p = self.run_dir / "files" / inner
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        mp = self.run_dir / "manifest.json"
        m = json.loads(mp.read_text(encoding="utf-8"))
        sha = rawdata.sha256_file(p)
        m["files"].append({"path": inner, "sha256": sha, "bytes": len(data), "tier": "T4", "licence": None,
                           "visibility": "public"})
        m["copies"].append({"sha256": sha, "store": "rnd-data", "location": f"runs/{m['id']}/files/{inner}"})
        mp.write_text(json.dumps(m), encoding="utf-8")
        return f"runs/{m['id']}/files/{inner}"

    def test_clean_store_passes(self):
        self.assertEqual(self.problems(), "")

    def test_home_path_patterns(self):
        u = "Users"  # built in parts, so the studio's identity scan doesn't take these probes for a leak
        hit = ["C:\\" + u + "\\bob\\x", "C:/" + u + "/bob/x", "c:\\\\" + u.lower() + "\\\\bob", "/c/" + u + "/bob/x",
               "/mnt/c/" + u + "/bob/x", "/" + u + "/bob/x", "/home/bob/x", "cd /home/bob && ls"]
        miss = ["/root/x", "/content/x", "/workspace/x", "E:/AI/x", "/mnt/e/AI/Publisher/x",
                "https://github.com/users/bob", "https://site.org/home/page", "a home/bob note", "see /home/ alone"]
        for t in hit:
            self.assertTrue(layout.HOME_PATH_RE.search(t), t)
        for t in miss:
            self.assertFalse(layout.HOME_PATH_RE.search(t), t)

    def test_f1_a_content_marker_under_runs(self):
        rel = self.plant_named("job2.log", "step\nCALL_CHECKPOINT H4sIAAAA...\n")
        self.assertIn(f"{rel}: carries a content marker (CALL_CHECKPOINT)", self.problems())

    def test_f1_the_rules_files_markers_are_all_in_the_package(self):
        rules = rawdata.load_rules(RULES)
        self.assertTrue({m["marker"] for m in rules.get("content_markers", [])} <= set(layout.CONTENT_MARKERS))

    def test_f2_copies_may_not_carry_a_private_hash_or_place(self):
        mp = self.run_dir / "manifest.json"
        m = json.loads(mp.read_text(encoding="utf-8"))
        m["copies"].append({"sha256": "b" * 64, "store": "rnd-data-private", "location": "runs/x/launch.out"})
        m["copies"].append({"sha256": "c" * 64, "store": "d", "location": "blobs/cc/" + "c" * 64})
        m["copies"].append({"sha256": m["copies"][0]["sha256"], "store": "d",
                            "location": f"runs/{m['id']}/files/launch.out"})  # the identity entry's path
        mp.write_text(json.dumps(m), encoding="utf-8")
        got = self.problems()
        self.assertIn("names the private companion", got)
        self.assertIn("carries a hash that isn't a public file's", got)
        self.assertIn("points at a private entry's path", got)
        self.assertNotIn("b" * 64, got)  # never print a hash

    def test_f3_an_oversized_git_file_and_the_tag_anywhere(self):
        rel = self.plant_named("big.json", b"x" * (rawdata.SMALL_LIMIT + 1))
        write(self.public, "notes.json", '{"tier": "' + TAG + '"}')           # outside runs/, innocent name
        write(self.public, "README.md", "Files carrying " + TAG + " are refused.\n")  # an explaining page
        got = self.problems()
        self.assertIn(f"{rel}: over 256 KB in git", got)
        self.assertIn("notes.json: carries the private tag", got)
        self.assertNotIn("README.md", got)

    def test_f4_home_paths_everywhere_drive_paths_outside_raw_files(self):
        home = self.plant_named("smoke.log", "ok\ncd /home/someone/run\n")
        drive_raw = self.plant_named("launch2.out", "copied to /mnt/e/AI/receipts/x\n")
        write(self.public, "site/src/content/docs/handbook/x.md", "see E:/AI/rnd-data\n")
        sp = self.public / "store.json"
        sp.write_text(json.dumps({"schema": "rnd-data-store/v1", "root": "D:/rnd-data"}), encoding="utf-8")
        got = self.problems()
        self.assertIn(f"{home}:2: a home-directory path", got)
        self.assertNotIn("someone", got)                                    # never print the match
        self.assertNotIn(drive_raw, got)                                     # a raw log may show a drive path
        self.assertIn("site/src/content/docs/handbook/x.md:1: a drive or machine path", got)
        self.assertIn("store.json:1: a drive or machine path", got)

    def test_share_paths_and_escaped_backslashes(self):
        bs = "\\"
        share = " " + bs * 2 + "fs01.corp" + bs + "data$" + bs + "x"
        jq = '"' + bs * 2 + "(.sha256)  " + bs * 2 + '(.location)"'
        self.assertTrue(layout.MACHINE_PATH_RE.search(share))
        self.assertFalse(layout.MACHINE_PATH_RE.search(jq))  # rnd-data's site-config jq example, a false positive before

    def test_an_unreadable_file_has_no_lines(self):
        self.assertEqual(rawdata._lines_matching(self.base / "gone.log", layout.HOME_PATH_RE), [])


class VerifyJsonTests(CliBase):
    """`rnd raw verify --json`: the shape rnd-data's verifier shares (counts, the checked list, {rule, where})."""

    def setUp(self):
        super().setUp()
        self.public, self.private, self.blobs = make_stores(self.root / "stores")
        src = make_receipts(self.root / "in")
        with mock.patch.dict(os.environ, {"RND_DATA_STORE_D": str(self.blobs)}):
            rawdata.ingest_tree(src, self.public, self.private, "receipts",
                                lambda rel: "identity" if rel.endswith("launch.out")
                                else ("blind" if layout.private_name(rel) else None))
        env = mock.patch.dict(os.environ, {"RND_DATA": str(self.public), "RND_DATA_PRIVATE": str(self.private)})
        env.start()
        self.addCleanup(env.stop)

    def json_run(self, *extra):
        with mock.patch.dict(os.environ, {}):
            os.environ.pop("RND_DATA_STORE_D", None)
            code, out, err = self.run_cli("raw", "verify", "--public-only", "--json", *extra)
        return code, json.loads(out)

    def test_a_clean_store(self):
        code, d = self.json_run()
        self.assertEqual(code, 0)
        self.assertEqual((d["schema"], d["ok"], d["public_only"]), ("rnd-data-verify/v1", True, True))
        self.assertEqual(d["counts"]["manifests"], 6)
        self.assertEqual(d["counts"]["public_git_files"], len(d["checked"]))
        self.assertEqual(d["checked"], sorted(d["checked"]))
        self.assertEqual(d["counts"]["declared_blobs_checked"], 0)
        self.assertEqual(d["skipped"], {"d": 2})
        self.assertEqual(d["problems"], [])

    def test_problems_carry_rule_and_redacted_place(self):
        (self.public / "runs/receipts--colab--window1-20261016/files/job.log").write_text("tampered")
        write(self.public, "runs/receipts/files/stray.txt", "x\n")
        mp = self.public / "runs/receipts/manifest.json"
        m = json.loads(mp.read_text(encoding="utf-8"))
        m["files"].append({"path": "secret-name.json", "sha256": "e" * 64, "bytes": 1, "visibility": "private"})
        mp.write_text(json.dumps(m), encoding="utf-8")
        code, d = self.json_run()
        self.assertEqual(code, 1)
        got = {(p["rule"], p["where"]) for p in d["problems"]}
        self.assertIn(("HASH_DIFFERS", "runs/receipts--colab--window1-20261016/files/job.log"), got)
        self.assertIn(("UNNAMED_FILE", "runs/receipts/files/stray.txt"), got)
        self.assertIn(("PRIVATE_HASH", f"receipts/files[{len(m['files']) - 1}]"), got)
        text = json.dumps(d["problems"])
        self.assertNotIn("e" * 64, text)            # never a hash
        self.assertNotIn("secret-name", text)       # never a private entry's name

    def test_the_full_check_counts_blobs(self):
        with mock.patch.dict(os.environ, {"RND_DATA_STORE_D": str(self.blobs)}):
            code, out, err = self.run_cli("raw", "verify", "--json")
        d = json.loads(out)
        self.assertEqual(code, 0, err)
        self.assertEqual(d["counts"]["declared_blobs_checked"], 2)
        self.assertFalse(d["public_only"])

    def test_a_missing_store_root_is_a_coded_problem(self):
        with mock.patch.dict(os.environ, {}):
            os.environ.pop("RND_DATA_STORE_D", None)
            code, out, _ = self.run_cli("raw", "verify", "--json")
        d = json.loads(out)
        self.assertEqual(code, 1)
        self.assertIn("NO_STORE_ROOT", {p["rule"] for p in d["problems"]})
        self.assertIn("counts", d)

    def test_one_missing_run(self):
        code, d = self.json_run("--run", "nope")
        self.assertEqual((code, d["problems"]), (1, [{"rule": "NO_RUN", "where": "nope"}]))

    def test_every_damage_class_has_its_rule(self):
        blobs = sorted(self.blobs.glob("blobs/*/*"))
        os.chmod(blobs[0], stat.S_IWRITE)
        blobs[0].write_bytes(b"y" * blobs[0].stat().st_size)          # same size, wrong bytes: only --deep sees it
        mp = self.public / "runs/receipts--colab--window2-20261017/manifest.json"
        m = json.loads(mp.read_text(encoding="utf-8"))
        m["copies"].append({"sha256": m["copies"][0]["sha256"], "store": "d", "location": "blobs/00/" + "0" * 64})
        mp.write_text(json.dumps(m), encoding="utf-8")
        (self.public / "runs/receipts--colab--window1-20261016/files/job.log").unlink()
        (self.public / "runs/receipts--commandui/manifest.json").write_text("{broken")
        with mock.patch.dict(os.environ, {"RND_DATA_STORE_D": str(self.blobs)}):
            code, out, _ = self.run_cli("raw", "verify", "--json", "--deep")
        rules = {p["rule"] for p in json.loads(out)["problems"]}
        self.assertEqual(code, 1)
        self.assertTrue({"BAD_MANIFEST", "MISSING", "BLOB_MISSING", "HASH_DIFFERS"} <= rules, rules)
