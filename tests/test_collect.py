"""rnd collect: trimmed records copied from a tool repository at pinned commits, checked byte for byte."""

import hashlib
import json
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from mcptoolshop_rnd import collect

RECEIPT = b'{"kind": "header", "run_id": "demo-1"}\n{"kind": "row", "value": 42.5}\n'

MODULE = textwrap.dedent('''
    import hashlib, json

    def keep(raw, ctx):
        rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
        return {
            "provenance": {"repo": ctx.repo, "source": ctx.source, "commit": ctx.commit,
                           "sha256": hashlib.sha256(raw).hexdigest()},
            "values": [r["value"] for r in rows if r["kind"] == "row"],
        }

    def leaky(raw, ctx):
        record = keep(raw, ctx)
        record["note"] = "ran from D:/scratch/work"
        return record

    def anonymous(raw, ctx):
        return {"values": [1]}
''')


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


class CollectTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.lib = base / "library"
        self.src = base / "toolrepo"
        (self.src / "receipts").mkdir(parents=True)
        git(self.src, "init", "-q")
        git(self.src, "config", "user.email", "test@example.invalid")
        git(self.src, "config", "user.name", "test")
        (self.src / "receipts" / "demo-1.jsonl").write_bytes(RECEIPT)
        git(self.src, "add", ".")
        git(self.src, "commit", "-q", "-m", "receipt")
        self.commit = git(self.src, "rev-parse", "HEAD")
        self.exp = self.lib / "experiments" / "demo"
        self.exp.mkdir(parents=True)
        (self.exp / "extract.py").write_text(MODULE, encoding="utf-8")
        self.write_spec(fn="keep")

    def tearDown(self):
        self.tmp.cleanup()

    def write_spec(self, fn="keep", sha=None, commit=None, **extra):
        spec = {
            "repo": "example-org/toolrepo",
            "sibling": "toolrepo",
            "sources": [{
                "path": "receipts/demo-1.jsonl",
                "commit": commit or self.commit,
                "sha256": sha or hashlib.sha256(RECEIPT).hexdigest(),
                "out": "results/demo-1.json",
                "fn": fn,
            }],
            **extra,
        }
        (self.exp / "collect.json").write_text(json.dumps(spec), encoding="utf-8")

    def test_collect_writes_the_trimmed_record_with_provenance_and_lf(self):
        rep = collect.run(self.lib, "demo")
        self.assertTrue(rep["ok"])
        raw = (self.exp / "results" / "demo-1.json").read_bytes()
        self.assertNotIn(b"\r\n", raw)
        doc = json.loads(raw)
        self.assertEqual(doc["values"], [42.5])
        self.assertEqual(doc["provenance"]["sha256"], hashlib.sha256(RECEIPT).hexdigest())
        self.assertEqual(doc["provenance"]["source"], "receipts/demo-1.jsonl")

    def test_check_passes_when_committed_and_finds_drift_after_an_edit(self):
        collect.run(self.lib, "demo")
        self.assertTrue(collect.run(self.lib, "demo", check=True)["ok"])
        out = self.exp / "results" / "demo-1.json"
        out.write_text(out.read_text(encoding="utf-8").replace("42.5", "43.0"), encoding="utf-8")
        rep = collect.run(self.lib, "demo", check=True)
        self.assertFalse(rep["ok"])
        self.assertEqual(rep["drift"], ["results/demo-1.json"])
        self.assertIn("43.0", out.read_text(encoding="utf-8"), "check never writes")

    def test_a_source_that_no_longer_matches_its_pin_is_refused(self):
        self.write_spec(sha="0" * 64)
        with self.assertRaises(collect.CollectError) as caught:
            collect.run(self.lib, "demo")
        self.assertEqual(caught.exception.code, "COLLECT_SOURCE_CHANGED")
        self.assertFalse((self.exp / "results").exists(), "nothing is written on a refusal")

    def test_a_commit_the_clone_lacks_is_refused(self):
        self.write_spec(commit="1" * 40)
        with self.assertRaises(collect.CollectError) as caught:
            collect.run(self.lib, "demo")
        self.assertEqual(caught.exception.code, "COLLECT_SOURCE_UNREADABLE")

    def test_a_record_with_a_machine_path_is_refused(self):
        self.write_spec(fn="leaky")
        with self.assertRaises(collect.CollectError) as caught:
            collect.run(self.lib, "demo")
        self.assertEqual(caught.exception.code, "COLLECT_NOT_PUBLIC")
        self.assertFalse((self.exp / "results").exists())

    def test_a_record_without_provenance_is_refused(self):
        self.write_spec(fn="anonymous")
        with self.assertRaises(collect.CollectError) as caught:
            collect.run(self.lib, "demo")
        self.assertEqual(caught.exception.code, "COLLECT_NO_PROVENANCE")

    def test_a_missing_clone_names_the_sibling(self):
        with self.assertRaises(collect.CollectError) as caught:
            collect.run(self.lib, "demo", clone=Path(self.tmp.name) / "nowhere")
        self.assertEqual(caught.exception.code, "COLLECT_NO_CLONE")

    def test_spec_problems_are_named(self):
        problems = collect.spec_problems({"repo": "nope", "sibling": "Bad Name", "sources": [
            {"path": "../x", "commit": "abc", "sha256": "z", "out": "x.txt", "fn": "1x"}]})
        joined = " | ".join(problems)
        for needle in ("repo", "sibling", "path", "commit", "sha256", "out", "fn"):
            self.assertIn(needle, joined)

    def test_the_cli_lists_collects_and_checks(self):
        import contextlib
        import io

        from mcptoolshop_rnd import cli

        (self.lib / "entries").mkdir()
        (self.lib / "instruments").mkdir()
        base = ["--library", str(self.lib)]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(base + ["collect"]), 0)
            self.assertEqual(cli.main(base + ["collect", "demo"]), 0)
            self.assertEqual(cli.main(base + ["collect", "demo", "--check", "--json"]), 0)
        text = out.getvalue()
        self.assertIn("example-org/toolrepo", text)
        self.assertIn("wrote experiments/demo/results/demo-1.json", text)
        (self.exp / "results" / "demo-1.json").write_text("{}\n", encoding="utf-8")
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            self.assertEqual(cli.main(base + ["collect", "demo", "--check"]), 1)
            self.assertEqual(cli.main(base + ["collect", "missing-exp"]), 2)
        self.assertIn("COLLECT_NO_SPEC", err.getvalue())

    def test_refusals_for_a_broken_experiment(self):
        (self.exp / "collect.json").write_text("{not json", encoding="utf-8")
        with self.assertRaises(collect.CollectError) as caught:
            collect.run(self.lib, "demo")
        self.assertEqual(caught.exception.code, "COLLECT_BAD_SPEC")
        with self.assertRaises(collect.CollectError) as caught:
            collect.run(self.lib, "Bad Name")
        self.assertEqual(caught.exception.code, "COLLECT_BAD_NAME")
        self.write_spec(fn="nothing_here")
        with self.assertRaises(collect.CollectError) as caught:
            collect.run(self.lib, "demo")
        self.assertEqual(caught.exception.code, "COLLECT_NO_FUNCTION")
        (self.exp / "extract.py").unlink()
        with self.assertRaises(collect.CollectError) as caught:
            collect.run(self.lib, "demo")
        self.assertEqual(caught.exception.code, "COLLECT_NO_MODULE")

    def test_a_module_can_refuse_and_add_its_own_guard(self):
        (self.exp / "extract.py").write_text(MODULE + textwrap.dedent('''
            def refuses(raw, ctx):
                raise SystemExit("no header")

            def assert_public(text, name):
                if "42.5" in text:
                    raise SystemExit(name + " carries a forbidden number")
        '''), encoding="utf-8")
        self.write_spec(fn="refuses")
        with self.assertRaises(collect.CollectError) as caught:
            collect.run(self.lib, "demo")
        self.assertEqual(caught.exception.code, "COLLECT_TRIM_REFUSED")
        self.write_spec(fn="keep")
        with self.assertRaises(collect.CollectError) as caught:
            collect.run(self.lib, "demo")
        self.assertEqual(caught.exception.code, "COLLECT_NOT_PUBLIC")
        self.assertIn("forbidden number", str(caught.exception))

    def test_the_guard_catches_home_and_environment_fields(self):
        for text in ('{"p": "/home/someone/x"}', '{"environment": {}}', '{"p": "E:\\\\AI\\\\x"}'):
            with self.assertRaises(collect.CollectError):
                collect.guard_public(text, "x.json")
        collect.guard_public('{"ok": "results/block-2.json", "rate": 218.5}', "x.json")


if __name__ == "__main__":
    unittest.main()
