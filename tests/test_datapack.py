"""Data packs: manifests built, validated and verified, and `rnd check` reading them."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from mcptoolshop_rnd import datapack

from .test_cli import CliBase

SPEC = {
    "title": "Demo pack",
    "description": "Two files for the tests.",
    "version": "1",
    "include": ["data/*.json"],
    "exclude": ["data/skip*"],
    "licences": [
        {"applies_to": "data/answers.json", "licence": "Llama 3.1 Community License", "notice": "Built with Llama"},
        {"applies_to": "data/labels.json", "licence": "MIT"},
    ],
    "generators": [{"model": "llama3.1:8b", "pin": "46e0c10c039e", "role": "answers"}],
    "host": {"kind": "huggingface", "repo": "someone/demo", "visibility": "private"},
}


def make_source(root: Path) -> Path:
    src = root / "experiments" / "demo"
    (src / "data").mkdir(parents=True)
    (src / "data" / "answers.json").write_bytes(b'{"a": 1}\n')
    (src / "data" / "labels.json").write_bytes(b'{"b": 2}\n')
    (src / "data" / "skip-me.json").write_text("{}", encoding="utf-8")
    (src / "README.md").write_text("not in the pack", encoding="utf-8")
    return src


class DatapackUnitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.src = make_source(self.tmp)

    def build(self, **over):
        kw = dict(name="demo", title=SPEC["title"], description=SPEC["description"], include=SPEC["include"],
                  exclude=SPEC["exclude"], licences=SPEC["licences"], generators=SPEC["generators"],
                  host=SPEC["host"], origin={"source": "experiments/demo"}, today="2026-10-08")
        kw.update(over)
        return datapack.build(self.src, **kw)

    def test_build_hashes_the_matching_files_only(self):
        m = self.build()
        self.assertEqual([f["path"] for f in m["files"]], ["data/answers.json", "data/labels.json"])
        self.assertEqual(m["totals"], {"files": 2, "bytes": 18})
        self.assertEqual(datapack.validate(m), [])
        self.assertEqual(m["manifest_sha256"], datapack.manifest_hash(m))

    def test_the_manifest_hash_is_deterministic(self):
        self.assertEqual(self.build()["manifest_sha256"], self.build()["manifest_sha256"])

    def test_verify_passes_on_a_true_copy_and_names_every_difference(self):
        m = self.build()
        self.assertTrue(datapack.verify(m, self.src)["ok"])
        (self.src / "data" / "labels.json").write_text('{"b": 3}\n', encoding="utf-8")
        (self.src / "data" / "answers.json").unlink()
        rep = datapack.verify(m, self.src)
        self.assertFalse(rep["ok"])
        self.assertEqual((rep["missing"], rep["changed"]), (["data/answers.json"], ["data/labels.json"]))

    def test_an_edited_manifest_fails_its_own_hash(self):
        m = self.build()
        m["title"] = "changed"
        self.assertIn("manifest_sha256 does not match", " ".join(datapack.validate(m)))
        self.assertFalse(datapack.verify(m, self.src)["ok"])

    def test_every_file_needs_a_licence(self):
        with self.assertRaises(datapack.DatapackError) as cm:
            self.build(licences=[{"applies_to": "data/labels.json", "licence": "MIT"}])
        self.assertIn("no licence covers: data/answers.json", str(cm.exception))

    def test_a_licence_glob_must_match_something(self):
        with self.assertRaises(datapack.DatapackError) as cm:
            self.build(licences=SPEC["licences"] + [{"applies_to": "nothing/*", "licence": "MIT"}])
        self.assertIn("matches no file", str(cm.exception))

    def test_bad_inputs_are_refused(self):
        for over, code in ((dict(name="Bad Name"), "BAD_NAME"), (dict(include=["*.csv"]), "NO_FILES")):
            with self.assertRaises(datapack.DatapackError) as cm:
                self.build(**over)
            self.assertEqual(cm.exception.code, code)
        with self.assertRaises(datapack.DatapackError) as cm:
            datapack.build(self.tmp / "missing", name="demo", title="t", description="d", include=["*"],
                           licences=[], generators=[], host={}, origin={})
        self.assertEqual(cm.exception.code, "NO_SOURCE")

    def test_generators_and_host_are_checked(self):
        with self.assertRaises(datapack.DatapackError) as cm:
            self.build(generators=[{"model": "x"}], host={"kind": "ftp"})
        msg = str(cm.exception)
        self.assertIn("generators[0] needs model, pin and role", msg)
        self.assertIn("host.kind must be one of", msg)
        with self.assertRaises(datapack.DatapackError) as cm:
            self.build(host={"kind": "huggingface"})
        self.assertIn("host.repo is required", str(cm.exception))
        self.assertTrue(self.build(host={"kind": "none"})["files"])

    def test_paths_must_stay_inside_and_be_unique(self):
        m = self.build()
        m["files"].append(dict(m["files"][0]))
        m["files"].append({"path": "../escape", "bytes": 0, "sha256": "0" * 64})
        m["totals"] = {"files": 4, "bytes": sum(f["bytes"] for f in m["files"])}
        problems = " ".join(datapack.validate(m, hashed=False))
        self.assertIn("repeats data/answers.json", problems)
        self.assertIn("must stay inside the pack", problems)

    def test_validate_rejects_a_non_object_and_wrong_totals(self):
        self.assertEqual(datapack.validate([]), ["manifest must be a JSON object"])
        m = self.build()
        m["totals"]["bytes"] += 1
        self.assertIn("totals do not match", " ".join(datapack.validate(m, hashed=False)))


class DatapackCliTests(CliBase):
    def setUp(self):
        super().setUp()
        make_source(self.root)
        d = self.root / "datapacks" / "demo"
        d.mkdir(parents=True)
        (d / "spec.json").write_text(json.dumps(SPEC), encoding="utf-8")

    def test_build_list_verify_and_check(self):
        code, out, _ = self.run_cli("datapack", "build", "demo", "--source", "experiments/demo")
        self.assertEqual(code, 0, out)
        self.assertIn("2 files, 18 bytes", out)
        m = json.loads((self.root / "datapacks" / "demo" / "datapack.json").read_text(encoding="utf-8"))
        self.assertEqual(m["origin"]["source"], "experiments/demo")

        code, out, _ = self.run_cli("datapack", "list")
        self.assertIn("demo", out)
        self.assertIn("huggingface:someone/demo@unpinned", out)

        code, out, _ = self.run_cli("datapack", "verify", "demo", "--copy", str(self.root / "experiments" / "demo"))
        self.assertEqual((code, out.startswith("PASS")), (0, True))

        code, out, _ = self.run_cli("check")
        self.assertEqual(code, 0)
        self.assertIn("and 1 data packs", out)

        path = self.root / "datapacks" / "demo" / "datapack.json"
        m["description"] = "edited by hand"
        path.write_text(json.dumps(m), encoding="utf-8")
        code, out, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("manifest_sha256 does not match", out + err)

    def test_hosted_json_pins_the_upload_and_must_match_the_manifest(self):
        self.run_cli("datapack", "build", "demo", "--source", "experiments/demo")
        d = self.root / "datapacks" / "demo"
        m = json.loads((d / "datapack.json").read_text(encoding="utf-8"))
        (d / "hosted.json").write_text(json.dumps({"revision": "abc123def4567890", "manifest_sha256": m["manifest_sha256"]}),
                                       encoding="utf-8")
        code, out, _ = self.run_cli("datapack", "list")
        self.assertIn("@abc123def456", out)
        self.assertEqual(self.run_cli("check")[0], 0)
        (d / "hosted.json").write_text(json.dumps({"revision": "x", "manifest_sha256": "0" * 64}), encoding="utf-8")
        code, out, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("hosted.json records a different manifest", out + err)
        (d / "hosted.json").write_text("{not json", encoding="utf-8")
        self.assertEqual(self.run_cli("check")[0], 1)

    def test_verify_reports_a_damaged_copy(self):
        self.run_cli("datapack", "build", "demo", "--source", "experiments/demo")
        (self.root / "experiments" / "demo" / "data" / "labels.json").write_text("{}", encoding="utf-8")
        code, out, _ = self.run_cli("datapack", "verify", "demo", "--copy", str(self.root / "experiments" / "demo"))
        self.assertEqual(code, 1)
        self.assertIn("changed: data/labels.json", out)

    def test_usage_errors_and_a_missing_spec(self):
        code, _, err = self.run_cli("datapack", "build", "demo")
        self.assertEqual(code, 2)
        self.assertIn("USAGE", err)
        code, _, err = self.run_cli("datapack", "verify", "demo")
        self.assertEqual(code, 2)
        code, _, err = self.run_cli("datapack", "build", "nope", "--source", "experiments/demo")
        self.assertEqual(code, 2)
        self.assertIn("UNREADABLE", err)

    def test_list_when_empty_and_json(self):
        shutil.rmtree(self.root / "datapacks")
        code, out, _ = self.run_cli("datapack", "list")
        self.assertIn("no data packs", out)
        self.run_cli("datapack", "list", "--json")


if __name__ == "__main__":
    unittest.main()
