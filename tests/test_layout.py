"""Layout rules: the size limits and baseline, private files, experiment records, and `rnd new-experiment`."""

import json
import os
from pathlib import Path
from unittest import mock

from mcptoolshop_rnd import layout

from .test_cli import CliBase
from .test_rnd import write

TAG = "T5-PRIVATE-" + "DO-NOT-PUBLISH"  # built in parts so this file does not carry the tag


def record(name, **over):
    r = {"schema": "rnd-experiment/v1", "name": name, "status": "running", "design": "README.md",
         "template": None, "budgets": [], "licences": [], "runs": []}
    r.update(over)
    return r


RUN = {"id": "14b", "venue": "colab", "hardware": "A100", "date": "2026-10-19", "cost": 6.4,
       "cost_unit": "colab_units", "cost_basis": "rate_x_runtime", "cap": 15.2, "projected_cost": 4.0,
       "outcome": "results", "raw_manifest_id": None, "pins": {"role-set": "47a5882"}}


class LayoutBase(CliBase):
    def setUp(self):
        super().setUp()
        env = mock.patch.dict(os.environ, {"RND_DATA": str(self.root / "no-rnd-data")})
        env.start()
        self.addCleanup(env.stop)

    def experiment(self, name, rec=None, files=None):
        write(self.root, f"experiments/{name}/README.md", "# x\n")
        if rec is not False:
            write(self.root, f"experiments/{name}/experiment.json", json.dumps(rec or record(name)))
        for rel, text in (files or {}).items():
            write(self.root, f"experiments/{name}/{rel}", text)

    def problems(self, registry=None):
        return [(lvl, where, msg) for lvl, where, msg in
                layout.check(self.root, layout.library_files(self.root), registry)]

    def errors(self, registry=None):
        return [(w, m) for lvl, w, m in self.problems(registry) if lvl == "error"]


class SizeTests(LayoutBase):
    def test_small_files_pass_and_big_ones_fail(self):
        self.experiment("demo", files={"data/a.csv": "x" * 1000})
        self.assertEqual(self.errors(), [])
        write(self.root, "experiments/demo/data/big.jsonl", "x" * (layout.FILE_LIMIT + 1))
        errs = self.errors()
        self.assertEqual(len(errs), 1)
        self.assertIn("256 KB", errs[0][1])

    def test_an_experiment_over_two_megabytes_fails(self):
        files = {f"data/part{i}.txt": "x" * (200 * 1024) for i in range(11)}
        self.experiment("demo", files=files)
        errs = self.errors()
        self.assertTrue(any(w == "experiments/demo" and "2 MB" in m for w, m in errs))

    def test_the_baseline_grandfathers_but_forbids_growth(self):
        big = "x" * (layout.FILE_LIMIT + 10)
        self.experiment("demo", files={"data/big.jsonl": big})
        write(self.root, layout.BASELINE, json.dumps(layout.baseline(self.root)))
        self.assertEqual(self.errors(), [])
        write(self.root, "experiments/demo/data/big.jsonl", big + "more")
        self.assertTrue(any("may not grow" in m for _, m in self.errors()))

    def test_a_grandfathered_folder_may_not_grow_and_gone_files_warn(self):
        files = {f"data/part{i}.txt": "x" * (200 * 1024) for i in range(11)}
        self.experiment("demo", files=files)
        base = layout.baseline(self.root)
        base["files"]["experiments/demo/data/gone.jsonl"] = 999999
        write(self.root, layout.BASELINE, json.dumps(base))
        self.assertEqual(self.errors(), [])
        self.assertTrue(any(l == "warning" and "is gone" in m for l, _, m in self.problems()))
        write(self.root, "experiments/demo/data/more.txt", "x" * 100)
        self.assertTrue(any(w == "experiments/demo" and "may not grow" in m for w, m in self.errors()))

    def test_crlf_counts_as_one_byte_so_both_platforms_agree(self):
        path = write(self.root, "experiments/demo/data/x.txt", "")
        path.write_bytes(b"a\r\nb\r\n")
        self.assertEqual(layout.size_of(path), 4)
        big = write(self.root, "experiments/demo/data/big.bin", "")
        big.write_bytes(b"\r\n" * (layout.TAG_SCAN_LIMIT // 2 + 1))
        self.assertEqual(layout.size_of(big), big.stat().st_size)

    def test_staging_is_skipped_without_git(self):
        self.experiment("demo", files={"staging/huge.jsonl": "x" * (layout.FILE_LIMIT * 2)})
        with mock.patch.object(layout.subprocess, "run", side_effect=OSError("no git")):
            self.assertEqual(self.errors(), [])

    def test_a_bad_baseline_is_an_error(self):
        write(self.root, layout.BASELINE, "{not json")
        self.assertTrue(any(w == layout.BASELINE and "not valid JSON" in m for w, m in self.errors()))
        write(self.root, layout.BASELINE, json.dumps({"schema": "other"}))
        self.assertTrue(any("schema must be" in m for _, m in self.errors()))
        write(self.root, layout.BASELINE, json.dumps({"schema": layout.BASELINE_SCHEMA, "files": [],
                                                      "experiments": {}, "no_record": [], "private_allow": {}}))
        self.assertTrue(any("'files' must be a dict" in m for _, m in self.errors()))


class PrivateTests(LayoutBase):
    def test_private_names_fail_unless_allowed_with_a_reason(self):
        self.experiment("demo", files={"data/blind_key.json": "{}", "data/Gold_Key.csv": "a",
                                       "data/review-items.json": "[]"})
        self.assertEqual(sum("looks private" in m for _, m in self.errors()), 3)
        base = layout.baseline(self.root)
        self.assertEqual(len(base["private_allow"]), 3)
        write(self.root, layout.BASELINE, json.dumps(base))
        self.assertTrue(any("needs a reason" in m for _, m in self.errors()))
        base["private_allow"] = {p: "published blind pass" for p in base["private_allow"]}
        write(self.root, layout.BASELINE, json.dumps(base))
        self.assertEqual(self.errors(), [])

    def test_the_private_tag_fails_anywhere(self):
        write(self.root, "entries/notes.md", f"# notes\n<!-- {TAG} -->\n")
        errs = self.errors()
        self.assertEqual([w for w, m in errs if "private tag" in m], ["entries/notes.md"])

    def test_a_file_in_the_private_manifest_fails_where_rnd_data_is_present(self):
        path = write(self.root, "entries/copied.json", '{"label": "a"}')
        rnd_data = self.root / "rnd-data"
        write(rnd_data, "private/manifest.json",
              json.dumps({"files": [{"path": "x", "sha256": layout.sha256(path)}]}))
        with mock.patch.dict(os.environ, {"RND_DATA": str(rnd_data)}):
            self.assertIn(("entries/copied.json", "matches a file in rnd-data's private manifest"), self.errors())
            write(rnd_data, "private/manifest.json", "{broken")
            self.assertTrue(any(l == "warning" and "did not run" in m for l, _, m in self.problems()))


class RecordTests(LayoutBase):
    def test_a_good_record_with_runs_and_budgets_passes(self):
        rec = record("demo", budgets=[{"cost_unit": "colab_units", "cap": 300, "set_by": "the Director"}],
                     licences=["apache-2.0"], runs=[RUN, {**RUN, "id": "14c", "outcome": "lost-vm",
                                                          "why": "VM reclaimed", "cap": None}])
        self.experiment("demo", rec)
        self.assertEqual(self.errors({"apache-2.0"}), [])

    def test_a_missing_record_fails_unless_in_no_record(self):
        self.experiment("old", rec=False)
        self.assertTrue(any("no experiment.json" in m for _, m in self.errors()))
        write(self.root, layout.BASELINE, json.dumps(layout.baseline(self.root)))
        self.assertEqual(self.errors(), [])
        write(self.root, "experiments/old/experiment.json", json.dumps(record("old")))
        self.assertTrue(any(l == "warning" and "drop it from no_record" in m for l, _, m in self.problems()))

    def test_every_field_is_checked(self):
        bad = {"schema": "x", "name": "other", "status": "done", "design": "missing.md", "template": "nope",
               "extra": 1, "budgets": [{"cost_unit": "eur", "cap": 0, "spent": 3},
                                        {"cost_unit": "usd", "cap": 5, "set_by": "R&D"},
                                        {"cost_unit": "usd", "cap": 5, "set_by": "R&D"}, "x"],
               "licences": ["not-registered"],
               "runs": [{**RUN, "venue": "cloud", "date": "19/10", "cost": -1, "cost_unit": "gbp",
                         "cost_basis": "guess", "cap": 0, "projected_cost": "a", "outcome": "partial",
                         "raw_manifest_id": 3, "pins": [], "hardware": 5, "other": 1},
                        {**RUN, "id": ""}, {**RUN}, {**RUN}, {**RUN, "outcome": "bad"}, "x"]}
        write(self.root, "site/src/content/docs/handbook/model-comparisons.md", "x")
        self.experiment("demo", bad)
        msgs = " | ".join(m for _, m in self.errors({"apache-2.0"}))
        for needle in ("unknown keys: extra", "schema must be", "name must be the folder", "status must be",
                       "design must name", "template must name", "budgets[0].cost_unit", "budgets[0].cap",
                       "budgets[0].set_by", "spending is computed", "a second budget in usd", "budgets[3] must be",
                       "licences not in", "runs[0].venue", "runs[0].date", "runs[0].cost must", "runs[0].cost_unit",
                       "runs[0].cost_basis", "runs[0].cap", "runs[0].projected_cost", "a partial run needs a why",
                       "runs[0].raw_manifest_id", "runs[0].pins", "runs[0].hardware", "runs[0]: unknown keys other",
                       "runs[1].id", "appears twice", "runs[4].outcome", "runs[5] must be"):
            self.assertIn(needle, msgs)

    def test_lists_and_json_must_be_well_formed(self):
        self.experiment("demo", record("demo", budgets={}, runs={}, licences="x"))
        msgs = " | ".join(m for _, m in self.errors())
        for needle in ("budgets must be a list", "runs must be a list", "licences must be a list"):
            self.assertIn(needle, msgs)
        write(self.root, "experiments/demo/experiment.json", "[1]")
        self.assertTrue(any("must be a JSON object" in m for _, m in self.errors()))
        write(self.root, "experiments/demo/experiment.json", "{oops")
        self.assertTrue(any("not valid JSON" in m for _, m in self.errors()))

    def test_machine_paths_are_refused(self):
        for value in ("E:/AI/rnd-local/x", "D:\\backup\\y", "see /home/me/z", "~/notes", "\\\\server\\share\\f",
                      # Built in parts so this file carries no home path for the identity scan to flag.
                      "/c/" + "Users/someone/run.sh", "/mnt/c/" + "Users/someone/x", "see /c/" + "Users/someone",
                      "/e/AI/Publisher/receipts"):
            rec = record("demo", runs=[{**RUN, "pins": {"where": value}}])
            self.experiment("demo", rec)
            self.assertTrue(any("machine path" in m for _, m in self.errors()), value)
        # Pod and VM paths carry no identity, and URLs and relative paths aren't machine paths.
        for ok in ("scripts/run.py", "/root/llama.cpp/build", "/content/drive", "/workspace/out",
                   "https://github.com/a/b/c"):
            self.experiment("demo", record("demo", runs=[{**RUN, "pins": {"where": ok}}]))
            self.assertEqual(self.errors(), [], ok)

    def test_registry_ids_are_read_from_the_library(self):
        self.assertIsNone(layout.registry_ids(self.root))
        write(self.root, "licences/registry.json", json.dumps({"entries": [{"id": "a"}, {"id": "b"}]}))
        self.assertEqual(layout.registry_ids(self.root), {"a", "b"})
        write(self.root, "licences/registry.json", "{bad")
        self.assertIsNone(layout.registry_ids(self.root))


class VocabularyTests(LayoutBase):
    def test_the_shared_vocabulary_covers_the_publishers_outcomes(self):
        # The Publisher's outcome.json values on 2026-10-19, plus the five agreed the same day.
        for v in ("results", "partial", "test", "tooling-fault", "lost-vm", "cap-stop",
                  "boot-fail", "gate-reject", "refused", "no-capacity", "stopped"):
            self.assertIn(v, layout.OUTCOMES)
        self.assertEqual(layout.ALIASES, {"not-assigned": "no-capacity"})  # merged with the Publisher, 2026-10-19
        self.assertNotIn("not-assigned", layout.OUTCOMES)
        self.assertEqual(layout.WHY_NOT_NEEDED, ("results",))
        self.assertEqual(layout.ZERO_COST, ("no-capacity",))

    def test_an_alias_is_refused_and_no_capacity_must_cost_nothing(self):
        self.experiment("demo", record("demo", runs=[{**RUN, "outcome": "not-assigned", "why": "no card"},
                                                     {**RUN, "id": "x2", "outcome": "no-capacity", "why": "no offer",
                                                      "cost": 1.33},
                                                     {**RUN, "id": "x3", "outcome": "no-capacity", "why": "no offer",
                                                      "cost": 0}]))
        msgs = [m for _, m in self.errors()]
        self.assertTrue(any("is an alias; record it as 'no-capacity'" in m for m in msgs))
        self.assertTrue(any("runs[1]: a no-capacity run costs nothing" in m for m in msgs))
        self.assertFalse(any(m.startswith("runs[2]") for m in msgs))
        self.assertEqual(set(layout.COST_BASES), {"rate_x_runtime", "balance", "estimate"})
        self.assertEqual(layout.VOCABULARY["schema"], "rnd-run-vocabulary/v1")

    def test_a_boot_fail_run_needs_a_why(self):
        self.experiment("demo", record("demo", runs=[{**RUN, "id": "publisher-plan3", "venue": "runpod",
                                                      "cost_unit": "usd", "cost_basis": "balance",
                                                      "outcome": "boot-fail"}]))
        self.assertTrue(any("a boot-fail run needs a why" in m for _, m in self.errors()))


class CommandTests(LayoutBase):
    def test_new_experiment_scaffolds_a_passing_folder(self):
        write(self.root, "site/src/content/docs/handbook/model-comparisons.md", "x")
        code, out, _ = self.run_cli("new-experiment", "probe-x", "--title", "Probe X", "--template", "model-comparisons")
        self.assertEqual(code, 0)
        self.assertIn("experiments/probe-x/experiment.json", out)
        folder = self.root / "experiments" / "probe-x"
        self.assertTrue((folder / "staging").is_dir())
        self.assertIn("# Probe X", (folder / "README.md").read_text(encoding="utf-8"))
        self.assertEqual(json.loads((folder / "experiment.json").read_text())["template"], "model-comparisons")
        self.assertEqual(self.errors(), [])
        code, _, err = self.run_cli("new-experiment", "probe-x")
        self.assertEqual(code, 2)
        self.assertIn("already exists", err)
        code, _, err = self.run_cli("new-experiment", "Bad Name")
        self.assertEqual(code, 2)
        code, _, err = self.run_cli("new-experiment", "other", "--template", "nope")
        self.assertIn("no handbook page", err)

    def test_layout_baseline_keeps_reasons_and_refuses_growth(self):
        self.experiment("demo", files={"data/big.jsonl": "x" * (layout.FILE_LIMIT + 1), "data/blind_in.json": "{}"})
        code, out, _ = self.run_cli("layout", "baseline")
        self.assertEqual(code, 0)
        self.assertIn("1 still need a reason", out)
        code, out, _ = self.run_cli("layout", "baseline")  # a rerun with reasons still blank is fine
        self.assertEqual(code, 0)
        base = json.loads((self.root / layout.BASELINE).read_text())
        base["private_allow"]["experiments/demo/data/blind_in.json"] = "published"
        write(self.root, "docs/tag-page.md", f"the tag is {TAG}\n")
        base["private_allow"]["docs/tag-page.md"] = "documents the tag"
        base["private_allow"]["docs/gone.md"] = "a page since deleted"
        write(self.root, layout.BASELINE, json.dumps(base))
        write(self.root, "experiments/demo/data/big.jsonl", "x" * (layout.FILE_LIMIT + 50))
        code, _, err = self.run_cli("layout", "baseline")
        self.assertEqual(code, 1)
        self.assertIn("would grow", err)
        code, out, _ = self.run_cli("layout", "baseline", "--allow-growth")
        self.assertEqual(code, 0)
        self.assertIn("0 still need a reason", out)
        allow = json.loads((self.root / layout.BASELINE).read_text())["private_allow"]
        self.assertEqual(allow.get("docs/tag-page.md"), "documents the tag")
        self.assertNotIn("docs/gone.md", allow)
        write(self.root, layout.BASELINE, "{bad")
        code, _, err = self.run_cli("layout", "baseline")
        self.assertEqual(code, 1)

    def test_rnd_check_reports_layout_errors(self):
        self.experiment("demo", files={"data/sealed_items.json": "{}"})
        code, out, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("looks private", err)

    def test_the_real_library_passes(self):
        repo = Path(__file__).resolve().parent.parent
        problems = layout.check(repo, registry_ids=layout.registry_ids(repo))
        self.assertEqual([p for p in problems if p[0] == "error"], [])
