"""Grade one atlas-mcp-utility run against its task, as pre-registered.

The answer is the last top-level JSON object in the run's final text. A run
with none is incorrect. Each task's `grade.checks` must all pass for the run
to be correct; `grade.secondary` is reported and never scored.

Path normal form, used wherever a check compares paths:
  surrounding whitespace removed; backslashes read as forward slashes; a
  leading "./" removed, as many times as it appears; repeated slashes
  collapsed; a trailing slash removed. Case is kept: paths compare as git
  stores them. A workflow is compared by its file name alone, so
  ".github/workflows/ci.yml" and "ci.yml" are the same answer.

Free text (`text` checks) is matched without regard to case. It must hold
every `require` pattern, none of the `reject` patterns, and at most
`max_words` words. The reject patterns catch hedges that name a rival cause,
so an answer that lists every candidate grades wrong.

Usage: python grade.py tasks.json TASK_ID ANSWER_TEXT_FILE
Standard library only.
"""
import json
import re
import sys
from pathlib import Path

DECODER = json.JSONDecoder()


def extract_answer(text):
    """The last top-level JSON object in `text`, or None."""
    found = None
    i = 0
    while True:
        j = text.find("{", i)
        if j == -1:
            return found
        try:
            value, end = DECODER.raw_decode(text, j)
        except ValueError:
            i = j + 1
            continue
        if isinstance(value, dict):
            found = value
        i = end


def normal_path(value):
    path = str(value).strip().replace("\\", "/")
    path = re.sub(r"/{2,}", "/", path)
    while path.startswith("./"):
        path = path[2:]
    return path.rstrip("/")


def workflow_name(value):
    return normal_path(value).rsplit("/", 1)[-1]


def field_value(answer, field):
    value = answer
    for part in field.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _strings(value):
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def check(rule, answer):
    """Whether one check passes, and why not when it does not."""
    kind = rule["kind"]
    value = field_value(answer, rule["field"])
    if value is None:
        return False, f"{rule['field']} is missing"
    expect = rule.get("expect")
    if kind == "path":
        ok = isinstance(value, str) and normal_path(value) == normal_path(expect)
    elif kind == "workflow":
        ok = isinstance(value, str) and workflow_name(value) == workflow_name(expect)
    elif kind == "path_set":
        ok = _strings(value) and {normal_path(v) for v in value} == {normal_path(e) for e in expect}
    elif kind == "workflow_set":
        ok = _strings(value) and {workflow_name(v) for v in value} == {workflow_name(e) for e in expect}
    elif kind == "path_subset_between":
        given = {normal_path(v) for v in value} if _strings(value) else None
        ok = given is not None and {normal_path(m) for m in rule["must"]} <= given <= {normal_path(w) for w in rule["within"]}
    elif kind == "exact":
        ok = isinstance(value, str) and value.strip() == expect
    elif kind == "dict":
        ok = isinstance(value, dict) and {k: str(v).strip() for k, v in value.items()} == expect
    elif kind == "bool":
        ok = value is expect
    elif kind == "line":
        number = value if isinstance(value, int) and not isinstance(value, bool) else (int(value) if isinstance(value, str) and value.strip().isdigit() else None)
        ok = number is not None and abs(number - expect) <= rule.get("tolerance", 0)
    elif kind == "node_version":
        ok = isinstance(value, (str, int)) and not isinstance(value, bool) and _node(value) == _node(expect)
    elif kind == "text":
        ok = isinstance(value, str) and _text_ok(rule, value)
    else:
        raise ValueError(f"unknown check kind {kind}")
    return ok, "" if ok else f"{rule['field']} does not match ({kind})"


def _node(value):
    text = str(value).strip().lower()
    if text.startswith("v"):
        text = text[1:]
    return text[:-2] if text.endswith(".x") else text


def _text_ok(rule, value):
    if len(value.split()) > rule.get("max_words", 10**6):
        return False
    if not all(re.search(p, value, re.IGNORECASE) for p in rule.get("require", [])):
        return False
    return not any(re.search(p, value, re.IGNORECASE) for p in rule.get("reject", []))


def secondary(rule, answer):
    value = field_value(answer, rule["field"])
    if rule["kind"] == "set_recall_precision":
        given = set(value) if _strings(value) else set()
        expect = set(rule["expect"])
        hit = len(given & expect)
        return {"field": rule["field"], "recall": hit / len(expect), "precision": hit / len(given) if given else 0.0}
    ok, _ = check(rule, answer) if value is not None else (False, "")
    return {"field": rule["field"], "match": ok}


def grade(task, text):
    """The grade of one run's final text against its task."""
    answer = extract_answer(text)
    if answer is None:
        return {"id": task["id"], "correct": False, "reason": "no JSON object in the answer", "checks": [], "secondary": []}
    results = []
    for rule in task["grade"]["checks"]:
        ok, why = check(rule, answer)
        results.append({"field": rule["field"], "kind": rule["kind"], "pass": ok, "why": why})
    return {
        "id": task["id"],
        "correct": all(r["pass"] for r in results),
        "reason": "" if all(r["pass"] for r in results) else "; ".join(r["why"] for r in results if not r["pass"]),
        "checks": results,
        "secondary": [secondary(rule, answer) for rule in task["grade"].get("secondary", [])],
    }


def main(argv):
    if len(argv) != 4:
        print(__doc__.strip().splitlines()[-2], file=sys.stderr)
        return 2
    tasks = {t["id"]: t for t in json.loads(Path(argv[1]).read_text(encoding="utf-8"))}
    if argv[2] not in tasks:
        print(f"no task {argv[2]}", file=sys.stderr)
        return 2
    print(json.dumps(grade(tasks[argv[2]], Path(argv[3]).read_text(encoding="utf-8")), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
