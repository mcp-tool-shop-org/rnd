"""Run records: outcome.json mapped onto a run, written into experiment.json, and the index's record tables
(runs, budgets, files, manifest_files, copies) with `rnd runs`, `rnd ledger` and `rnd where`."""

import json
import os
from unittest import mock

from mcptoolshop_rnd import layout, runs, store

from .test_cli import CliBase
from .test_rnd import write

OUTCOME = {"window": "14b", "card": "A100", "cap": 15.2, "spent": 6.4, "basis": "rate_x_runtime",
           "outcome": "results", "why": "80 of 80 scored", "date": "2026-10-19", "commit": "6ee4fb7"}


def record(name, **over):
    r = {"schema": "rnd-experiment/v1", "name": name, "status": "running", "design": "README.md",
         "template": None, "budgets": [{"cost_unit": "colab_units", "cap": 300, "set_by": "the Director"}],
         "licences": [], "runs": []}
    r.update(over)
    return r


class RunsBase(CliBase):
    def setUp(self):
        super().setUp()
        env = mock.patch.dict(os.environ, {"RND_DATA": str(self.root / "rnd-data"),
                                           "RND_DATA_PRIVATE": str(self.root / "rnd-data-private")})
        env.start()
        self.addCleanup(env.stop)
        write(self.root, "experiments/demo/README.md", "# demo\n")
        write(self.root, "experiments/demo/experiment.json", json.dumps(record("demo")))

    def outcome(self, name="outcome.json", **over):
        d = dict(OUTCOME)
        d.update(over)
        return str(write(self.root, f"receipts/{name}", json.dumps({k: v for k, v in d.items() if v is not None})))

    def saved(self):
        return json.loads((self.root / "experiments/demo/experiment.json").read_text(encoding="utf-8"))


class FromOutcomeTests(RunsBase):
    def test_the_publishers_fields_map_onto_a_run(self):
        run = runs.from_outcome(OUTCOME, venue="colab", cost_unit="colab_units")
        self.assertEqual((run["id"], run["hardware"], run["cost"], run["cost_basis"], run["cap"]),
                         ("14b", "A100", 6.4, "rate_x_runtime", 15.2))
        self.assertEqual(run["pins"], {"commit": "6ee4fb7"})
        self.assertIsNone(run["projected_cost"])
        self.assertEqual(layout.validate_data(self.root, "demo", record("demo", runs=[run])), [])

    def test_an_alias_is_mapped_and_never_stored(self):
        run = runs.from_outcome({**OUTCOME, "outcome": "not-assigned", "spent": 0}, venue="colab",
                                cost_unit="colab_units")
        self.assertEqual(run["outcome"], "no-capacity")

    def test_given_values_fill_gaps_but_never_override(self):
        bare = {k: v for k, v in OUTCOME.items() if k != "date"}
        run = runs.from_outcome(bare, venue="colab", cost_unit="colab_units", date="2026-10-19",
                                pins={"role-set": "6ee4fb7"})
        self.assertEqual(run["date"], "2026-10-19")
        self.assertEqual(run["pins"], {"commit": "6ee4fb7", "role-set": "6ee4fb7"})
        with self.assertRaises(runs.RecordError) as ctx:
            runs.from_outcome(OUTCOME, venue="colab", cost_unit="colab_units", date="2026-10-20")
        self.assertEqual(ctx.exception.code, "OUTCOME_CONFLICT")
        with self.assertRaises(runs.RecordError):
            runs.from_outcome({**OUTCOME, "pins": {"seed": "0"}}, venue="colab", cost_unit="colab_units",
                              pins={"seed": "1"})

    def test_missing_fields_and_bad_shapes_are_refused(self):
        with self.assertRaises(runs.RecordError) as ctx:
            runs.from_outcome(OUTCOME)
        self.assertIn("venue", str(ctx.exception))
        self.assertIn("cost_unit", str(ctx.exception))
        with self.assertRaises(runs.RecordError):
            runs.from_outcome(["not", "an", "object"])


class RecordCommandTests(RunsBase):
    def test_record_adds_then_refuses_a_duplicate_then_replaces(self):
        src = self.outcome()
        code, out, _ = self.run_cli("runs", "record", "--experiment", "demo", "--from", src,
                                    "--venue", "colab", "--cost-unit", "colab_units", "--pin", "seed=0")
        self.assertEqual(code, 0, out)
        self.assertIn("added run 14b", out)
        self.assertEqual(self.saved()["runs"][0]["pins"], {"commit": "6ee4fb7", "seed": "0"})
        code, _, err = self.run_cli("runs", "record", "--experiment", "demo", "--from", src,
                                    "--venue", "colab", "--cost-unit", "colab_units")
        self.assertEqual(code, 1)
        self.assertIn("already recorded", err)
        src2 = self.outcome("o2.json", spent=6.06, basis="balance")
        code, out, _ = self.run_cli("runs", "record", "--experiment", "demo", "--from", src2, "--venue", "colab",
                                    "--cost-unit", "colab_units", "--replace")
        self.assertEqual(code, 0)
        self.assertIn("replaced", out)
        self.assertEqual(len(self.saved()["runs"]), 1)
        self.assertEqual(self.saved()["runs"][0]["cost"], 6.06)

    def test_nothing_is_written_when_the_record_would_be_invalid(self):
        before = (self.root / "experiments/demo/experiment.json").read_text(encoding="utf-8")
        bad = self.outcome(why=None, outcome="lost-vm")  # a lost-vm run needs a why
        code, _, err = self.run_cli("runs", "record", "--experiment", "demo", "--from", bad,
                                    "--venue", "colab", "--cost-unit", "colab_units")
        self.assertEqual(code, 1)
        self.assertIn("needs a why", err)
        self.assertIn("nothing was written", err)
        leak = self.outcome("leak.json", why="see /mnt/c/" + "Users/someone/log")
        code, _, err = self.run_cli("runs", "record", "--experiment", "demo", "--from", leak,
                                    "--venue", "colab", "--cost-unit", "colab_units")
        self.assertIn("machine path", err)
        self.assertEqual((self.root / "experiments/demo/experiment.json").read_text(encoding="utf-8"), before)

    def test_usage_errors(self):
        self.assertEqual(self.run_cli("runs", "record", "--experiment", "demo")[0], 2)
        self.assertEqual(self.run_cli("runs", "record", "--experiment", "demo", "--from", "nope.json")[0], 2)
        code, _, err = self.run_cli("runs", "record", "--experiment", "demo", "--from", self.outcome(),
                                    "--venue", "colab", "--cost-unit", "colab_units", "--pin", "bad")
        self.assertEqual(code, 2)
        code, _, err = self.run_cli("runs", "record", "--experiment", "nope", "--from", self.outcome(),
                                    "--venue", "colab", "--cost-unit", "colab_units")
        self.assertIn("doesn't exist", err)
        write(self.root, "experiments/demo/experiment.json", "{broken")
        code, _, err = self.run_cli("runs", "record", "--experiment", "demo", "--from", self.outcome(),
                                    "--venue", "colab", "--cost-unit", "colab_units")
        self.assertIn("not valid JSON", err)


class IndexTests(RunsBase):
    def fill(self):
        for i, (spent, basis, unit, outcome) in enumerate([(6.4, "rate_x_runtime", "colab_units", "results"),
                                                            (0.24, "balance", "colab_units", "tooling-fault"),
                                                            (1.33, "balance", "usd", "boot-fail")]):
            src = self.outcome(f"o{i}.json", window=f"w{i}", spent=spent, basis=basis, outcome=outcome,
                               why="why" if outcome != "results" else "done")
            venue = "runpod" if unit == "usd" else "colab"
            self.assertEqual(self.run_cli("runs", "record", "--experiment", "demo", "--from", src, "--venue", venue,
                                          "--cost-unit", unit)[0], 0)

    def test_runs_lists_and_filters(self):
        self.fill()
        code, out, _ = self.run_cli("runs")
        self.assertEqual(code, 0)
        self.assertEqual(out.count("demo"), 3)
        code, out, _ = self.run_cli("runs", "--venue", "runpod", "--json")
        rows = json.loads(out)
        self.assertEqual([r["id"] for r in rows], ["w2"])
        self.assertEqual(rows[0]["pins"], {"commit": "6ee4fb7"})
        code, out, _ = self.run_cli("runs", "--pin", "nomatch")
        self.assertIn("no runs", out)
        self.assertEqual(len(json.loads(self.run_cli("runs", "--outcome", "results", "--cost-unit",
                                                     "colab_units", "--experiment", "demo", "--json")[1])), 1)

    def test_ledger_keeps_units_apart(self):
        self.fill()
        code, out, _ = self.run_cli("ledger", "demo", "--json")
        self.assertEqual(code, 0)
        units = {u["cost_unit"]: u for u in json.loads(out)["units"]}
        self.assertAlmostEqual(units["colab_units"]["spent"], 6.64)
        self.assertEqual(units["colab_units"]["cap"], 300)
        self.assertAlmostEqual(units["colab_units"]["left"], 293.36)
        self.assertEqual(units["colab_units"]["by_basis"], {"balance": 0.24, "rate_x_runtime": 6.4})
        self.assertEqual((units["usd"]["spent"], units["usd"]["cap"]), (1.33, None))
        code, out, _ = self.run_cli("ledger", "demo")
        self.assertIn("never added across units", out)
        self.assertIn("no budget", out)
        self.assertEqual(self.run_cli("ledger", "nope")[0], 2)
        write(self.root, "experiments/empty/README.md", "x")
        write(self.root, "experiments/empty/experiment.json", json.dumps(record("empty", budgets=[])))
        self.assertIn("no budgets and no runs", self.run_cli("ledger", "empty")[1])

    def test_where_finds_git_pack_and_rnd_data_copies(self):
        payload = write(self.root, "experiments/demo/data/a.json", '{"a": 1}')
        sha = layout.sha256(payload)
        write(self.root, "datapacks/demo/datapack.json", json.dumps({
            "name": "demo", "licences": [{"applies_to": "data/*.json", "licence": "MIT"}],
            "files": [{"path": "data/a.json", "bytes": payload.stat().st_size, "sha256": sha}]}))
        write(self.root, "datapacks/demo/hosted.json", json.dumps({"url": "https://hf.example/d", "revision": "abc"}))
        write(self.root, "rnd-data/runs/w0/manifest.json", json.dumps({
            "schema": runs.RNDDATA_RUN_SCHEMA, "id": "w0", "files": [{"path": "out/a.json", "sha256": sha,
                                                                      "bytes": 8, "tier": "T4"}],
            "copies": [{"sha256": sha, "store": "d", "location": "runs/w0/out/a.json"}]}))
        write(self.root, "rnd-data/runs/bad/manifest.json", "{broken")
        write(self.root, "rnd-data-private/manifest.json", json.dumps({
            "schema": runs.RNDDATA_PRIVATE_SCHEMA, "files": [{"path": "k.json", "sha256": "f" * 64, "bytes": 3}],
            "copies": [{"sha256": "f" * 64, "store": "rnd-data-private", "location": "private/k.json"}]}))
        code, out, _ = self.run_cli("where", sha[:10], "--json")
        self.assertEqual(code, 0)
        f = json.loads(out)[0]
        self.assertEqual((f["tier"], f["licence"]), ("T3", "MIT"))
        stores = {c["store"] for c in f["copies"]}
        self.assertEqual(stores, {"git", "hf", "d"})  # copies come only from each manifest's own list
        self.assertIn("https://hf.example/d@abc/data/a.json", {c["location"] for c in f["copies"]})
        self.assertIn("as datapack:demo:data/a.json", self.run_cli("where", "data/a.json")[1])
        self.assertEqual(json.loads(self.run_cli("where", "k.json", "--json")[1])[0]["tier"], "T5")
        self.assertEqual(self.run_cli("where", "nothing-here.txt")[0], 2)
        counts, problems = store.build(self.root, self.root / "x.db")
        self.assertTrue(any(p.level == "warning" and "rnd-data/runs/bad" in p.path for p in problems))
        write(self.root, "rnd-data/runs/w9/manifest.json", json.dumps({"schema": "wrong", "files": []}))
        _, problems = store.build(self.root, self.root / "y.db")
        self.assertTrue(any("schema must be" in p.message for p in problems))

    def test_an_invalid_record_stops_the_build(self):
        write(self.root, "experiments/demo/experiment.json", json.dumps(record("demo", status="done")))
        counts, problems = store.build(self.root, self.root / "z.db")
        self.assertIsNone(counts)
        self.assertTrue(any("status must be" in p.message for p in problems))

    def test_a_bad_pack_manifest_or_hosted_file_is_skipped(self):
        write(self.root, "datapacks/broken/datapack.json", "{broken")
        write(self.root, "datapacks/ok/datapack.json", json.dumps({"name": "ok", "files": [
            {"path": "x.json", "bytes": 1, "sha256": "e" * 64}]}))
        write(self.root, "datapacks/ok/hosted.json", "{bad")
        write(self.root, "experiments/older/README.md", "no record yet")  # listed in the baseline; skipped here
        rows, _ = runs.index_rows(self.root)
        self.assertIn(("e" * 64, "unhosted", ""), rows["copies"])
        self.assertEqual([r[0] for r in rows["experiments"]], ["demo"])

    def test_the_schema_is_part_of_the_fingerprint(self):
        self.assertTrue(store.fingerprint(self.root).startswith(store.SCHEMA_ID + ":"))


class RunObjectTests(RunsBase):
    RUN = {"id": "14f", "venue": "colab", "hardware": "A100", "date": "2026-10-19", "cost": 0.54,
           "cost_unit": "colab_units", "cost_basis": "estimate", "cap": None, "projected_cost": None,
           "outcome": "test", "why": "pre-step rung try 5", "raw_manifest_id": None, "pins": {"role-set": "89b5f2e"}}

    def test_a_run_object_is_read_as_written(self):
        run = runs.from_outcome({"window": "ignored", "spent": 99, "run": self.RUN})
        self.assertEqual(run, self.RUN)
        self.assertEqual(runs.from_outcome({"run": {**self.RUN, "outcome": "not-assigned", "cost": 0}})["outcome"],
                         "no-capacity")

    def test_options_must_agree_with_a_run_object(self):
        self.assertEqual(runs.from_outcome({"run": self.RUN}, venue="colab")["venue"], "colab")
        with self.assertRaises(runs.RecordError):
            runs.from_outcome({"run": self.RUN}, venue="runpod")
        with self.assertRaises(runs.RecordError):
            runs.from_outcome({"run": ["not", "an", "object"]})

    def test_record_from_a_publisher_file(self):
        src = write(self.root, "receipts/rung/try5/outcome.json", json.dumps({"notes": "free-form", "run": self.RUN}))
        code, out, _ = self.run_cli("runs", "record", "--experiment", "demo", "--from", str(src))
        self.assertEqual(code, 0, out)
        self.assertEqual(self.saved()["runs"][0], self.RUN)


class BudgetRuleTests(RunsBase):
    def runs_(self):
        base = dict(RunObjectTests.RUN)
        return [{**base, "id": i, "cost": c} for i, c in (("1", 2.37), ("4", 1.39), ("5", 7.58), ("6", 0.5))]

    def test_excludes_and_reconciled_change_what_the_ledger_counts(self):
        rec = record("demo", runs=self.runs_(), budgets=[{
            "cost_unit": "colab_units", "cap": 300, "set_by": "the Director",
            "excludes": ["1"], "excludes_why": "before the budget began",
            "reconciled": [{"runs": ["4", "5"], "measured": 8.5, "why": "overlapped; balance read 8.5"}]}])
        write(self.root, "experiments/demo/experiment.json", json.dumps(rec))
        self.assertEqual(layout.validate_data(self.root, "demo", rec), [])
        unit = json.loads(self.run_cli("ledger", "demo", "--json")[1])["units"][0]
        self.assertAlmostEqual(unit["spent"], 9.0)  # measured 8.5 for 4+5, plus 6's own 0.5; 1 is outside
        self.assertEqual(unit["runs"], 3)
        self.assertEqual(unit["outside_cap"]["runs"], ["1"])
        self.assertEqual(unit["reconciled"][0]["runs_estimated"], 8.97)
        self.assertEqual(unit["by_basis"], {"estimate": 0.5, "reconciled": 8.5})
        out = self.run_cli("ledger", "demo")[1]
        self.assertIn("count as their measured 8.5", out)
        self.assertIn("outside the cap: 2.37 over 1", out)

    def test_the_budget_rules_are_checked(self):
        bad = record("demo", runs=self.runs_(), budgets=[{
            "cost_unit": "colab_units", "cap": 300, "set_by": "x", "excludes": ["1", "9"],
            "reconciled": [{"runs": ["1", "4"], "measured": -1, "why": ""}, {"runs": ["5"], "measured": 1, "why": "x",
                                                                              "extra": 1}, "x"]},
            {"cost_unit": "usd", "cap": 5, "set_by": "x", "excludes": "1", "excludes_why": "y", "reconciled": {}},
            {"cost_unit": "rig_hours", "cap": 5, "set_by": "x", "excludes_why": "y", "excludes": ["4"]},
            {"cost_unit": "colab_units", "cap": 1, "set_by": "x", "excludes_why": "lonely"}])
        msgs = " | ".join(layout.validate_data(self.root, "demo", bad))
        for needle in ("excludes needs an excludes_why", "names '9', which is not a recorded run",
                       "is named in both excludes and reconciled[0]", "reconciled[0].measured",
                       "reconciled[0].why", "reconciled[1] needs exactly", "reconciled[1].runs must list two",
                       "reconciled[2] must be an object", "budgets[1].excludes must be a list",
                       "budgets[1].reconciled must be a list", "a run in colab_units, not rig_hours",
                       "excludes_why without excludes"):
            self.assertIn(needle, msgs)


class PhaseBudgetTests(RunsBase):
    """A budget split into phases, each with its own cap (the Director's phase budgets, 2026-10-22)."""

    def runs_(self):
        base = dict(RunObjectTests.RUN)
        rows = (("1", 2.37, "2026-10-15"), ("4", 1.39, "2026-10-17"),
                ("5", 7.58, "2026-10-17"), ("6", 0.5, "2026-10-19"), ("15a", 3.0, "2026-10-21"), ("15b", 2.0, "2026-10-22"))
        return [{**base, "id": i, "cost": c, "date": d} for i, c, d in rows]

    def budget(self, **over):
        b = {"cost_unit": "colab_units", "cap": 400, "set_by": "the Director, 2026-10-22",
             "excludes": ["1"], "excludes_why": "before the budget began",
             "reconciled": [{"runs": ["4", "5"], "measured": 8.5, "why": "overlapped; balance read 8.5"}],
             "phases": [{"name": "0-4", "cap": 300, "set_by": "the Director, 2026-10-18", "from": "2026-10-16", "closed": True},
                        {"name": "5", "cap": 400, "set_by": "the Director, 2026-10-22", "from": "2026-10-21"}]}
        b.update(over)
        return b

    def test_the_ledger_reports_each_phase_against_its_own_cap(self):
        rec = record("demo", runs=self.runs_(), budgets=[self.budget()])
        write(self.root, "experiments/demo/experiment.json", json.dumps(rec))
        self.assertEqual(layout.validate_data(self.root, "demo", rec), [])
        unit = json.loads(self.run_cli("ledger", "demo", "--json")[1])["units"][0]
        first, current = unit["phases"]
        self.assertEqual((first["name"], first["spent"], first["runs"], first["closed"]), ("0-4", 9.0, 3, True))
        self.assertEqual(first["left"], 291.0)  # 4+5 at their measured 8.5, plus 6's 0.5; 1 is excluded
        self.assertEqual((current["spent"], current["runs"], current["left"]), (5.0, 2, 395.0))
        self.assertEqual(unit["left"], 395.0)  # the cap in force is the current phase's
        self.assertAlmostEqual(unit["spent"], 14.0)
        self.assertNotIn("before_phases", unit)
        out = self.run_cli("ledger", "demo")[1]
        self.assertIn("current phase 5: cap 400, left 395.0", out)
        self.assertIn("phase 0-4 (from 2026-10-16, closed): spent 9.0 over 3 runs; cap 300", out)

    def test_the_phase_rules_are_checked(self):
        bad_phases = [{"name": "a", "cap": 0, "set_by": "", "from": "2026-10-20", "closed": "yes", "spent": 1},
                      {"name": "a", "cap": 5, "set_by": "x", "from": "2026-10-19"},
                      {"name": [], "cap": 5, "set_by": "x", "from": "2026-10-23", "closed": True},
                      "x"]
        msgs = " | ".join(layout.validate_data(self.root, "demo", record(
            "demo", runs=self.runs_(), budgets=[self.budget(phases=bad_phases)])))
        for needle in ("phases[0] needs", "phases[0].cap must be a positive number", "phases[0].set_by must say",
                       "phases[0].closed must be true or false", "phases[1].name must be a non-empty name of its own",
                       "phases[1].from must come after", "phases[1] must be closed: only the last phase is open",
                       "phases[2].name must be a non-empty name of its own", "phases[3] must be an object"):
            self.assertIn(needle, msgs)
        cap_off = " | ".join(layout.validate_data(self.root, "demo", record(
            "demo", runs=self.runs_(), budgets=[self.budget(cap=300)])))
        self.assertIn("cap must equal its current phase's cap (400)", cap_off)
        who_off = " | ".join(layout.validate_data(self.root, "demo", record(
            "demo", runs=self.runs_(), budgets=[self.budget(set_by="someone else")])))
        self.assertIn("set_by must equal its current phase's set_by", who_off)
        # A counted run before the first phase must be excluded; once excluded, it passes.
        early = [*self.runs_(), {**self.runs_()[1], "id": "0", "cost": 1.0, "date": "2026-10-15"}]
        early_msgs = " | ".join(layout.validate_data(self.root, "demo", record("demo", runs=early, budgets=[self.budget()])))
        self.assertIn("run '0' (2026-10-15) comes before the first phase", early_msgs)
        self.assertEqual(layout.validate_data(self.root, "demo", record(
            "demo", runs=early, budgets=[self.budget(excludes=["1", "0"])])), [])
        # A malformed run id in a group is reported, never a crash.
        odd = self.budget(reconciled=[{"runs": [[], "4"], "measured": 1.0, "why": "x"}])
        self.assertTrue(layout.validate_data(self.root, "demo", record("demo", runs=self.runs_(), budgets=[odd])))
        # Malformed excludes, run ids and dates are reported, never a crash or a false "before the first phase".
        weird = [*self.runs_(), {**self.runs_()[1], "id": [], "date": "2026-10-17"},
                 {**self.runs_()[1], "id": "bad-date", "date": "10/20/2026"}]
        weird_msgs = " | ".join(layout.validate_data(self.root, "demo", record(
            "demo", runs=weird, budgets=[self.budget(excludes=[[], "1"])])))
        self.assertIn("excludes must be a list of run ids", weird_msgs)
        self.assertNotIn("'bad-date' (10/20/2026) comes before the first phase", weird_msgs)
        # A phase whose start isn't a date, and a group that isn't an object, are reported one by one.
        bad_from = self.budget(phases=[{"name": "0-4", "cap": 300, "set_by": "x", "from": "October", "closed": True},
                                       {"name": "5", "cap": 400, "set_by": "the Director, 2026-10-22", "from": "2026-10-21"}])
        self.assertIn("phases[0].from must be YYYY-MM-DD", " | ".join(
            layout.validate_data(self.root, "demo", record("demo", runs=self.runs_(), budgets=[bad_from]))))
        not_a_group = self.budget(reconciled=["x"])
        self.assertIn("reconciled[0] must be an object", " | ".join(
            layout.validate_data(self.root, "demo", record("demo", runs=self.runs_(), budgets=[not_a_group]))))
        spans = self.budget(reconciled=[{"runs": ["6", "15a"], "measured": 3.0, "why": "overlapped"}])
        span_msgs = " | ".join(layout.validate_data(self.root, "demo", record("demo", runs=self.runs_(), budgets=[spans])))
        self.assertIn("reconciled[0] spans phases 0-4, 5", span_msgs)
        empty = " | ".join(layout.validate_data(self.root, "demo", record(
            "demo", runs=self.runs_(), budgets=[self.budget(phases=[])])))
        self.assertIn("phases must be a non-empty list", empty)
