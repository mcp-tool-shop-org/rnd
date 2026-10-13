"""The atlas-mcp-utility grader, pinned before any run (experiments/atlas-mcp-utility).

Every task's example answer grades correct, a perturbed one grades wrong,
and every free-text check has a scattershot answer that grades wrong, so a
model cannot pass by listing every candidate cause.
"""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / "experiments" / "atlas-mcp-utility"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


grade = _load("atlas_mcp_utility_grade", HERE / "grade.py")
TASKS = json.loads((HERE / "tasks.json").read_text(encoding="utf-8"))


def as_text(answer):
    return "I read the repository.\n\n```json\n" + json.dumps(answer) + "\n```\n"


def set_field(answer, field, value):
    parts = field.split(".")
    target = answer
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = value


def perturbed(task):
    """The example with its first check's field made wrong."""
    answer = copy.deepcopy(task["grade"]["example"])
    rule = task["grade"]["checks"][0]
    value = grade.field_value(answer, rule["field"])
    kind = rule["kind"]
    if kind in ("path", "workflow", "exact"):
        wrong = "not/the-answer.txt"
    elif kind in ("path_set", "workflow_set"):
        wrong = value[:-1] if len(value) > 1 else value + ["not/the-answer.txt"]
    elif kind == "path_subset_between":
        wrong = value + ["tests/not-one-of-them.test.ts"]
    elif kind == "dict":
        wrong = dict(list(value.items())[:-1])
    elif kind == "bool":
        wrong = not value
    elif kind == "line":
        wrong = value + 5
    elif kind == "node_version":
        wrong = "16"
    elif kind == "text":
        wrong = "something unrelated happened"
    else:
        raise AssertionError(kind)
    set_field(answer, rule["field"], wrong)
    return answer


class EveryTask(unittest.TestCase):
    def test_bank_holds_42_tasks_each_with_a_grade_block(self):
        self.assertEqual(len(TASKS), 42)
        for task in TASKS:
            self.assertIn("checks", task["grade"], task["id"])
            self.assertIn("example", task["grade"], task["id"])

    def test_each_example_grades_correct(self):
        for task in TASKS:
            with self.subTest(task=task["id"]):
                result = grade.grade(task, as_text(task["grade"]["example"]))
                self.assertTrue(result["correct"], result)

    def test_each_perturbed_example_grades_wrong(self):
        for task in TASKS:
            with self.subTest(task=task["id"]):
                self.assertFalse(grade.grade(task, as_text(perturbed(task)))["correct"])

    def test_each_free_text_check_has_a_scattershot_answer_that_grades_wrong(self):
        texts = [t for t in TASKS if any(c["kind"] == "text" for c in t["grade"]["checks"])]
        self.assertEqual(sorted(t["id"] for t in texts), ["CF01", "CF02", "CF03", "CF04", "CF05", "CF06", "CF07", "TG01"])
        for task in texts:
            with self.subTest(task=task["id"]):
                self.assertTrue(task["grade"].get("scattershot"), "no scattershot answer")
                for answer in task["grade"]["scattershot"]:
                    self.assertFalse(grade.grade(task, as_text(answer))["correct"], answer)
                    # It is the hedge rule that fails it: without the reject
                    # patterns the same answer passes every other check.
                    lenient = copy.deepcopy(task)
                    for rule in lenient["grade"]["checks"]:
                        if rule["kind"] == "text":
                            rule["reject"] = []
                    self.assertTrue(grade.grade(lenient, as_text(answer))["correct"], answer)

    def test_every_blind_audit_answer_grades_correct(self):
        # R&D's blind key audit (key-audit.json): agents that never saw the
        # keys answered 15 sampled questions. Each answer was right, so each
        # must grade correct, the long CI-failure answers (70 to 80 words)
        # among them (amendment 1).
        audit = json.loads((HERE / "key-audit.json").read_text(encoding="utf-8"))
        by_id = {t["id"]: t for t in TASKS}
        self.assertEqual(len(audit["results"]), 15)
        for entry in audit["results"]:
            with self.subTest(task=entry["id"]):
                result = grade.grade(by_id[entry["id"]], as_text(entry["blind_answer"]))
                self.assertTrue(result["correct"], result)

    def test_no_check_imposes_a_length_no_question_states(self):
        for task in TASKS:
            for rule in task["grade"]["checks"]:
                self.assertNotIn("max_words", rule, task["id"])

    def test_extra_fields_in_an_answer_are_ignored(self):
        task = next(t for t in TASKS if t["id"] == "RC01")
        answer = dict(task["grade"]["example"], reasoning="from the imports")
        self.assertTrue(grade.grade(task, as_text(answer))["correct"])


class Answers(unittest.TestCase):
    def test_the_last_top_level_object_is_the_answer(self):
        text = 'First guess: {"files": ["a.ts"]}\nOn reflection: {"files": ["b.ts"], "why": {"note": "x"}}\nDone.'
        self.assertEqual(grade.extract_answer(text), {"files": ["b.ts"], "why": {"note": "x"}})

    def test_no_object_is_incorrect(self):
        task = TASKS[0]
        result = grade.grade(task, "I could not find it.")
        self.assertFalse(result["correct"])
        self.assertEqual(result["reason"], "no JSON object in the answer")

    def test_a_missing_field_is_incorrect(self):
        task = next(t for t in TASKS if t["id"] == "FP02")
        self.assertFalse(grade.grade(task, as_text({"file": "src/escape_the_valley/cli.py"}))["correct"])


class NormalForm(unittest.TestCase):
    def test_paths(self):
        self.assertEqual(grade.normal_path("  ./.\\src\\\\a.ts/ "), "src/a.ts")
        self.assertEqual(grade.normal_path("./././tests/x.py"), "tests/x.py")
        self.assertNotEqual(grade.normal_path("SRC/a.ts"), grade.normal_path("src/a.ts"))

    def test_workflows_compare_by_file_name(self):
        self.assertEqual(grade.workflow_name(".github/workflows/ci.yml"), "ci.yml")
        self.assertEqual(grade.workflow_name("ci.yml"), "ci.yml")

    def test_node_versions(self):
        rule = {"kind": "node_version", "field": "node", "expect": "20"}
        self.assertTrue(grade.check(rule, {"node": "v20"})[0])
        self.assertTrue(grade.check(rule, {"node": "20.x"})[0])
        self.assertTrue(grade.check(rule, {"node": 20})[0])
        self.assertFalse(grade.check(rule, {"node": "20.11.0"})[0])

    def test_a_bool_must_be_a_json_bool(self):
        rule = {"kind": "bool", "field": "will_break", "expect": False}
        self.assertTrue(grade.check(rule, {"will_break": False})[0])
        self.assertFalse(grade.check(rule, {"will_break": "false"})[0])

    def test_a_dotted_version_is_not_read_as_a_rejected_major(self):
        task = next(t for t in TASKS if t["id"] == "CF02")
        answer = dict(task["grade"]["example"], change="node-version: 20 -> 22.21.0")
        self.assertTrue(grade.grade(task, as_text(answer))["correct"])

    def test_a_negation_of_a_rival_is_not_a_hedge(self):
        task = next(t for t in TASKS if t["id"] == "CF05")
        answer = dict(task["grade"]["example"], cause="The github-pages environment's branch policy rejects main; it is not a token problem.")
        self.assertTrue(grade.grade(task, as_text(answer))["correct"])


if __name__ == "__main__":
    unittest.main()
