"""Mergeability scorer for J2 runs (F10, NB2, F9).

Responsibilities:
- Verifies `tests/**` is never in `allowed_paths`, and every test file's sha256 equals its pre-run value.
- Verifies `git status --porcelain -uall --ignored` shows nothing outside `allowed_paths` (untracked files count,
  including an untracked `conftest.py`), ignoring only the fixed list:
  `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.aider.tags.cache.v4/`.
- Parses `pytest --junitxml` output over the full suite, the target test and the held-out twin:
  - matches target and twin nodes strictly on exact `file::name` (with the class part `file::Class::name` when
    inside a class), treating any missing node as not passed;
  - `errors == 0` and `failures == 0`;
  - `skipped` and `xfail` equal the parent's baseline;
  - `passed >= baseline_passed + len(target_nodes) + len(twin_nodes)`.
- On the VM, executes the scoring pytest inside builder containment (`wrap_as_builder` + `builder_env`),
  staging the held-out twin only for that run and removing it afterwards, and catches `TimeoutExpired`
  (killing the process group and reporting `score_timeout`).
"""
from __future__ import annotations

import fnmatch
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from .contain import BUILDER_USER, builder_env, run_bounded_subprocess, wrap_as_builder
from .workspace import (
    SCORER_IGNORED_PATTERNS,
    TaskSpec,
    WorkspaceError,
    is_scorer_ignored,
    is_test_path,
    normal_rel_path,
    snapshot_test_hashes,
    validate_allowed_paths,
)

DEFAULT_SCORE_TIMEOUT_S = 300


class ScoreError(Exception):
    """Raised when scoring inputs or XML are malformed."""


@dataclass(frozen=True)
class JUnitSummary:
    """Aggregated counts and exact per-node outcomes parsed from JUnit XML."""

    passed: int
    failed: int
    errors: int
    skipped: int
    xfail: int
    node_outcomes: dict[str, str] = field(default_factory=dict)

    def outcome_for(self, node_id: str) -> str | None:
        """Return the outcome for `node_id` matching strictly on exact `file::name` (with class part)."""
        norm = normal_rel_path(node_id)
        return self.node_outcomes.get(norm)


def _candidate_node_ids(testcase: ET.Element) -> list[str]:
    """Derive exact `file::name` (or `file::Class::name`) pytest node IDs from a `<testcase>` element.

    Never emits bare test names or file-less suffixes so a same-named test in another file or class
    can never satisfy a missing target or twin node.
    """
    ids: list[str] = []
    explicit = testcase.attrib.get("nodeid")
    if explicit:
        norm_exp = normal_rel_path(explicit)
        if "::" in norm_exp:
            ids.append(norm_exp)

    name = testcase.attrib.get("name", "").strip()
    classname = testcase.attrib.get("classname", "").strip()
    file_attr = testcase.attrib.get("file", "").strip()

    if file_attr and name:
        norm_file = normal_rel_path(file_attr)
        mod_dotted = norm_file[:-3].replace("/", ".") if norm_file.endswith(".py") else norm_file.replace("/", ".")
        mod_stem = Path(norm_file).stem
        if not classname or classname == mod_dotted or classname == mod_stem:
            ids.append(f"{norm_file}::{name}")
        elif classname.startswith(mod_dotted + "."):
            cls_part = classname[len(mod_dotted) + 1 :].replace(".", "::")
            ids.append(f"{norm_file}::{cls_part}::{name}")
        else:
            cls_tail = classname.split(".")[-1]
            if cls_tail and cls_tail != mod_stem:
                ids.append(f"{norm_file}::{cls_tail}::{name}")
            else:
                ids.append(f"{norm_file}::{name}")
    elif classname and name:
        parts = classname.split(".")
        mod_idx: int | None = None
        for idx, part in enumerate(parts):
            if part.startswith("test_") or part.endswith("_test"):
                mod_idx = idx
                break
        if mod_idx is not None:
            file_guess = "/".join(parts[: mod_idx + 1]) + ".py"
            cls_parts = parts[mod_idx + 1 :]
        elif len(parts) >= 2 and parts[-1][:1].isupper():
            file_guess = "/".join(parts[:-1]) + ".py"
            cls_parts = [parts[-1]]
        else:
            file_guess = "/".join(parts) + ".py"
            cls_parts = []
        if cls_parts:
            ids.append(f"{file_guess}::{'::'.join(cls_parts)}::{name}")
        else:
            ids.append(f"{file_guess}::{name}")

    return list(dict.fromkeys(ids))


def _classify_testcase(testcase: ET.Element) -> str:
    """Return one of `'passed'`, `'failure'`, `'error'`, `'skipped'`, `'xfail'`."""
    if testcase.find("error") is not None:
        return "error"
    if testcase.find("failure") is not None:
        return "failure"
    if testcase.find("xfail") is not None:
        return "xfail"
    skipped_el = testcase.find("skipped")
    if skipped_el is not None:
        skip_type = (skipped_el.attrib.get("type") or "").lower()
        skip_msg = (skipped_el.attrib.get("message") or "").lower()
        if "xfail" in skip_type or skip_msg.startswith("xfail"):
            return "xfail"
        return "skipped"
    return "passed"


def parse_junitxml(xml_source: str | Path) -> JUnitSummary:
    """Parse a JUnit XML string or file path into a `JUnitSummary`."""
    text: str
    if isinstance(xml_source, Path):
        text = xml_source.read_text(encoding="utf-8")
    else:
        s = str(xml_source).strip()
        if s.startswith("<"):
            text = s
        else:
            p = Path(s)
            if p.is_file():
                text = p.read_text(encoding="utf-8")
            else:
                raise ScoreError(f"JUnit XML source is neither XML text nor an existing file: {xml_source}")

    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise ScoreError(f"Invalid JUnit XML: {exc}") from exc

    testcases = list(root.iter("testcase"))
    passed = failed = errors = skipped = xfail = 0
    outcomes: dict[str, str] = {}

    for tc in testcases:
        status = _classify_testcase(tc)
        if status == "passed":
            passed += 1
        elif status == "failure":
            failed += 1
        elif status == "error":
            errors += 1
        elif status == "xfail":
            xfail += 1
        elif status == "skipped":
            skipped += 1
        for nid in _candidate_node_ids(tc):
            if nid not in outcomes or outcomes[nid] == "passed":
                outcomes[nid] = status

    return JUnitSummary(
        passed=passed,
        failed=failed,
        errors=errors,
        skipped=skipped,
        xfail=xfail,
        node_outcomes=outcomes,
    )


def merge_junit_summaries(*summaries: JUnitSummary) -> JUnitSummary:
    """Combine multiple `JUnitSummary` objects (e.g. main suite + separate twin run)."""
    passed = sum(s.passed for s in summaries)
    failed = sum(s.failed for s in summaries)
    errors = sum(s.errors for s in summaries)
    skipped = sum(s.skipped for s in summaries)
    xfail = sum(s.xfail for s in summaries)
    outcomes: dict[str, str] = {}
    for s in summaries:
        for k, v in s.node_outcomes.items():
            if k not in outcomes or outcomes[k] == "passed":
                outcomes[k] = v
    return JUnitSummary(
        passed=passed,
        failed=failed,
        errors=errors,
        skipped=skipped,
        xfail=xfail,
        node_outcomes=outcomes,
    )


def parse_git_status_porcelain(status_output: str) -> list[tuple[str, str]]:
    """Parse `git status --porcelain --ignored` output into `(status_code, rel_path)` pairs."""
    entries: list[tuple[str, str]] = []
    for raw_line in status_output.splitlines():
        line = raw_line.rstrip("\r\n")
        if len(line) < 4:
            continue
        code = line[:2]
        rest = line[3:].strip()
        if " -> " in rest and code[0] in ("R", "C"):
            old_p, new_p = rest.split(" -> ", 1)
            entries.append((code, normal_rel_path(old_p.strip('"'))))
            entries.append((code, normal_rel_path(new_p.strip('"'))))
        else:
            entries.append((code, normal_rel_path(rest.strip('"'))))
    return entries


def path_is_allowed(rel_path: str, allowed_paths: list[str]) -> bool:
    """Return True iff `rel_path` is not a test path and matches `allowed_paths`."""
    norm = normal_rel_path(rel_path)
    if not norm or is_test_path(norm):
        return False
    for pattern in allowed_paths:
        pat = normal_rel_path(pattern)
        if norm == pat or norm.startswith(pat + "/") or fnmatch.fnmatch(norm, pat):
            return True
    return False


def check_workspace_integrity(
    workspace_dir: str | Path,
    pre_test_hashes: dict[str, str],
    allowed_paths: list[str],
    *,
    git_status_output: str | None = None,
    env: dict[str, str] | None = None,
) -> list[str]:
    """Check F10 workspace integrity: allowed_paths, test sha256s, and `git status --porcelain --ignored`.

    Ignores only the fixed named list in `SCORER_IGNORED_PATTERNS`:
    `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.aider.tags.cache.v4/`.
    """
    reasons: list[str] = []
    try:
        norm_allowed = validate_allowed_paths(allowed_paths)
    except WorkspaceError as exc:
        return [str(exc)]

    root = Path(workspace_dir)
    post_hashes = snapshot_test_hashes(root)

    # 1. Every pre-run test file's sha256 must equal its pre-run value.
    for test_rel, expected_sha in sorted(pre_test_hashes.items()):
        norm_rel = normal_rel_path(test_rel)
        if is_scorer_ignored(norm_rel):
            continue
        actual_sha = post_hashes.get(norm_rel)
        if actual_sha is None:
            reasons.append(f"deleted test file: {norm_rel}")
        elif actual_sha != expected_sha:
            reasons.append(f"edited test file: {norm_rel} (sha256 mismatch)")

    # 2. Any newly added test or conftest.py file found on disk is refused.
    for post_rel in sorted(post_hashes):
        if is_scorer_ignored(post_rel):
            continue
        if post_rel not in {normal_rel_path(k) for k in pre_test_hashes}:
            if post_rel == "conftest.py" or post_rel.endswith("/conftest.py"):
                reasons.append(f"untracked conftest.py: {post_rel}")
            else:
                reasons.append(f"added test file: {post_rel}")

    # 3. `git status --porcelain --ignored` shows nothing outside allowed_paths (untracked files count).
    if git_status_output is None:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "-uall", "--ignored"],
            cwd=str(root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if proc.returncode != 0:
            reasons.append(f"git status failed: {proc.stderr.strip()}")
            return reasons
        git_status_output = proc.stdout

    for code, rel_path in parse_git_status_porcelain(git_status_output):
        if not rel_path or is_scorer_ignored(rel_path):
            continue
        if rel_path == "conftest.py" or rel_path.endswith("/conftest.py"):
            msg = f"untracked conftest.py: {rel_path}" if "?" in code else f"modified conftest.py: {rel_path}"
            if msg not in reasons:
                reasons.append(msg)
            continue
        if is_test_path(rel_path):
            msg = f"edited test file: {rel_path}"
            if not any(r.startswith(f"edited test file: {rel_path}") for r in reasons):
                reasons.append(msg)
            continue
        if not path_is_allowed(rel_path, norm_allowed):
            reasons.append(f"changed path outside allowed_paths: {rel_path} ({code.strip()})")

    return reasons


def evaluate_junit_parity(
    summary: JUnitSummary,
    *,
    target_nodes: list[str],
    twin_nodes: list[str],
    baseline: dict,
) -> list[str]:
    """Check F10 and NB2 JUnit XML rules against the task's target, twin, and baseline counts."""
    reasons: list[str] = []

    for node in target_nodes:
        outcome = summary.outcome_for(node)
        if outcome != "passed":
            reasons.append(f"target test did not pass: {node} (outcome={outcome!r})")

    for twin in twin_nodes:
        outcome = summary.outcome_for(twin)
        if outcome != "passed":
            reasons.append(f"failing twin: {twin} (outcome={outcome!r})")

    if summary.errors != 0:
        reasons.append(f"suite errors == {summary.errors} (expected 0)")
    if summary.failed != 0:
        reasons.append(f"suite failures == {summary.failed} (expected 0)")

    base_skipped = int(baseline["skipped"])
    if summary.skipped != base_skipped:
        reasons.append(
            f"skipped count {summary.skipped} != baseline {base_skipped} (pytest.skip in production or test code)"
        )

    base_xfail = int(baseline["xfail"])
    if summary.xfail != base_xfail:
        reasons.append(f"xfail count {summary.xfail} != baseline {base_xfail}")

    base_passed = int(baseline["passed"])
    min_passed = base_passed + len(target_nodes) + len(twin_nodes)
    if summary.passed < min_passed:
        reasons.append(
            f"passed count short ({summary.passed} < {min_passed}): shrunken parametrization or missing tests"
        )

    return reasons


def score_task(
    task: TaskSpec | dict,
    workspace_dir: str | Path,
    pre_test_hashes: dict[str, str],
    *,
    junit_xml: str | Path | JUnitSummary | list[str | Path | JUnitSummary],
    git_status_output: str | None = None,
    env: dict[str, str] | None = None,
) -> dict:
    """Score a completed task workspace against integrity and JUnit XML parity rules."""
    spec = task if isinstance(task, TaskSpec) else TaskSpec.from_dict(task)
    reasons = check_workspace_integrity(
        workspace_dir,
        pre_test_hashes,
        spec.allowed_paths,
        git_status_output=git_status_output,
        env=env,
    )

    items = junit_xml if isinstance(junit_xml, list) else [junit_xml]
    parsed = [s if isinstance(s, JUnitSummary) else parse_junitxml(s) for s in items]
    summary = merge_junit_summaries(*parsed)
    reasons.extend(
        evaluate_junit_parity(
            summary,
            target_nodes=spec.target_nodes,
            twin_nodes=spec.twin_nodes,
            baseline=spec.baseline,
        )
    )

    passed = len(reasons) == 0
    return {
        "task_id": spec.id,
        "passed": passed,
        "correct": passed,
        "reasons": reasons,
        "reason": "; ".join(reasons),
        "counts": {
            "passed": summary.passed,
            "failed": summary.failed,
            "errors": summary.errors,
            "skipped": summary.skipped,
            "xfail": summary.xfail,
        },
        "baseline": dict(spec.baseline),
        "target_nodes": list(spec.target_nodes),
        "twin_nodes": list(spec.twin_nodes),
    }


def run_pytest_and_score(
    task: TaskSpec | dict,
    workspace_dir: str | Path,
    pre_test_hashes: dict[str, str],
    *,
    twin_source_path: str | Path | None = None,
    pytest_cmd: list[str] | None = None,
    env: dict[str, str] | None = None,
    aider_running: bool = False,
    use_sudo_builder: bool = True,
    builder_user: str = BUILDER_USER,
    proxy_port: int = 18080,
    timeout: float = DEFAULT_SCORE_TIMEOUT_S,
    _test_allow_uncontained: bool = False,
) -> dict:
    """Execute pytest as `builder` over the full suite, target test, and held-out twin after Aider exits (F9, F10).

    The twin is read from `twin_source_path` (or `task.twin_test_path`, unreadable by `builder`)
    only at scoring time after Aider has exited, and is removed in `finally:`.
    If pytest exceeds `timeout`, its process group is killed and the run is scored as failed
    with reason `'score_timeout'`.
    """
    if aider_running:
        raise ScoreError("refusing to run held-out twin while Aider is still running")
    if not use_sudo_builder and not _test_allow_uncontained:
        raise ScoreError("refusing to run scoring pytest outside builder containment (F9)")

    spec = task if isinstance(task, TaskSpec) else TaskSpec.from_dict(task)
    root = Path(workspace_dir).resolve()

    run_env = (
        dict(env)
        if env is not None and "PIP_NO_INDEX" in env
        else builder_env(proxy_port=proxy_port, home_dir=root.parent / f".score-home-{spec.id}", base_env=env)
    )
    run_env["CUDA_VISIBLE_DEVICES"] = ""

    # Check workspace integrity BEFORE staging the held-out twin
    integrity_reasons = check_workspace_integrity(
        root,
        pre_test_hashes,
        spec.allowed_paths,
        env=run_env,
    )

    twin_text: str
    if twin_source_path is not None:
        twin_text = Path(twin_source_path).read_text(encoding="utf-8")
    else:
        twin_text = spec.read_twin_test()

    # Determine where the twin test expects to run (from the first twin node's file prefix)
    first_twin_node = spec.twin_nodes[0]
    twin_rel = first_twin_node.split("::", 1)[0] if "::" in first_twin_node else "tests/test_heldout_twin.py"
    staged_twin = root / normal_rel_path(twin_rel)
    staged_twin.parent.mkdir(parents=True, exist_ok=True)
    prior_bytes = staged_twin.read_bytes() if staged_twin.exists() else None

    with tempfile.TemporaryDirectory() as tmp:
        os.chmod(tmp, 0o777)
        xml_path = Path(tmp) / "junit.xml"
        try:
            staged_twin.write_text(twin_text, encoding="utf-8", newline="\n")
            os.chmod(staged_twin, 0o644)
            base_cmd = list(pytest_cmd) if pytest_cmd is not None else [sys.executable, "-m", "pytest"]
            raw_cmd = [*base_cmd, f"--junitxml={xml_path}"]
            full_cmd = wrap_as_builder(
                raw_cmd,
                env=run_env,
                builder_user=builder_user,
                use_sudo=use_sudo_builder,
            )
            try:
                run_bounded_subprocess(
                    full_cmd,
                    cwd=root,
                    env=run_env,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired:
                reasons = [*integrity_reasons, "score_timeout"]
                return {
                    "task_id": spec.id,
                    "passed": False,
                    "correct": False,
                    "reasons": reasons,
                    "reason": "; ".join(reasons),
                    "counts": {"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "xfail": 0},
                    "baseline": dict(spec.baseline),
                    "target_nodes": list(spec.target_nodes),
                    "twin_nodes": list(spec.twin_nodes),
                }
            if not xml_path.is_file():
                raise ScoreError("pytest did not produce a --junitxml report")
            summary = parse_junitxml(xml_path)
        finally:
            if prior_bytes is None:
                if staged_twin.exists():
                    staged_twin.unlink()
            else:
                staged_twin.write_bytes(prior_bytes)

    parity_reasons = evaluate_junit_parity(
        summary,
        target_nodes=spec.target_nodes,
        twin_nodes=spec.twin_nodes,
        baseline=spec.baseline,
    )
    reasons = integrity_reasons + parity_reasons
    passed = len(reasons) == 0
    return {
        "task_id": spec.id,
        "passed": passed,
        "correct": passed,
        "reasons": reasons,
        "reason": "; ".join(reasons),
        "counts": {
            "passed": summary.passed,
            "failed": summary.failed,
            "errors": summary.errors,
            "skipped": summary.skipped,
            "xfail": summary.xfail,
        },
        "baseline": dict(spec.baseline),
        "target_nodes": list(spec.target_nodes),
        "twin_nodes": list(spec.twin_nodes),
    }
