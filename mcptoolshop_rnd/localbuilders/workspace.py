"""Clean task workspace builder for J2 (F7, F9).

Responsibilities:
- Exports the task's `parent_commit` via `git archive` into a fresh `git init` repository
  (never a git worktree), so no git history or object store reaches the fix commit.
- Runs all git commands with `GIT_CONFIG_NOSYSTEM=1` and an empty temporary `HOME`.
- Removes `docs/runs/`, `CHANGELOG.md` and design notes from the exported tree (F7).
- Adds the PR's scrubbed test from the task bank into the tree before the baseline commit.
- Snapshots the pre-run sha256 of every test file so the scorer can verify test integrity (F10).
"""
from __future__ import annotations

import fnmatch
import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
from dataclasses import dataclass, field
from pathlib import Path

DESIGN_NOTE_GLOBS = (
    "DESIGN.md",
    "*/DESIGN.md",
    "*/*/DESIGN.md",
    "experiments/**/DESIGN.md",
    "experiments/**/*design*.md",
    "experiments/**/*brief*.md",
    "docs/*design*.md",
    "docs/**/*design*.md",
)


class WorkspaceError(Exception):
    """Raised when workspace creation or task bank validation fails."""


def normal_rel_path(path: str | Path) -> str:
    """Normalize a relative path to forward slashes without leading './'."""
    text = str(path).strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    while "//" in text:
        text = text.replace("//", "/")
    return text.rstrip("/")


def is_test_path(rel_path: str | Path) -> bool:
    """Return True if `rel_path` is inside `tests/**`, is `conftest.py`, or is a `test_*.py` file."""
    norm = normal_rel_path(rel_path)
    if not norm:
        return False
    parts = norm.split("/")
    if parts[0] == "tests" or "tests" in parts:
        return True
    base = parts[-1]
    if base == "conftest.py":
        return True
    if base.startswith("test_") and base.endswith(".py"):
        return True
    if base.endswith("_test.py"):
        return True
    return False


def validate_allowed_paths(allowed_paths: list[str]) -> list[str]:
    """Ensure `allowed_paths` is non-empty and never includes `tests/**` or test files (F10)."""
    if not allowed_paths:
        raise WorkspaceError("allowed_paths must not be empty")
    normalized = []
    for raw in allowed_paths:
        norm = normal_rel_path(raw)
        if not norm or is_test_path(norm):
            raise WorkspaceError(f"tests/** is never permitted in allowed_paths: {raw!r}")
        normalized.append(norm)
    return normalized


def sha256_file(path: str | Path) -> str:
    """Compute the sha256 hex digest of a file's raw bytes."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot_test_hashes(workspace_dir: str | Path) -> dict[str, str]:
    """Return `{rel_path: sha256}` for every test and conftest file in `workspace_dir`."""
    root = Path(workspace_dir)
    hashes: dict[str, str] = {}
    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        rel = normal_rel_path(file_path.relative_to(root))
        if rel.startswith(".git/") or rel == ".git":
            continue
        if is_test_path(rel):
            hashes[rel] = sha256_file(file_path)
    return hashes


@dataclass(frozen=True)
class TaskSpec:
    """One task entry from R&D's J2 task bank."""

    id: str
    parent_commit: str
    test_file: str
    target_nodes: list[str]
    twin_nodes: list[str]
    test_cmd: str
    allowed_paths: list[str]
    baseline: dict
    scrubbed_test_path: str | None = None
    scrubbed_test_content: str | None = None
    twin_test_path: str | None = None
    twin_test_content: str | None = None
    difficulty: str = "medium"
    design_notes: list[str] = field(default_factory=list)
    repo: str = ""

    @property
    def target_node_id(self) -> str:
        return self.target_nodes[0]

    @classmethod
    def from_dict(cls, data: dict, bank_dir: str | Path | None = None) -> TaskSpec:
        if not isinstance(data, dict) or not data.get("id"):
            raise WorkspaceError("task entry must be a dict with an 'id'")
        task_id = str(data["id"])
        parent_commit = str(data.get("parent_commit") or "").strip()
        if not parent_commit:
            raise WorkspaceError(f"task {task_id}: missing parent_commit")
        test_file = normal_rel_path(data.get("test_file") or "")
        if not test_file or not is_test_path(test_file):
            raise WorkspaceError(f"task {task_id}: test_file {test_file!r} must be a test file")

        raw_targets = data.get("target_nodes")
        if raw_targets is None and data.get("target_node_id"):
            raw_targets = [str(data["target_node_id"])]
        if not isinstance(raw_targets, list) or not raw_targets:
            raise WorkspaceError(f"task {task_id}: missing target_nodes / target_node_id")
        target_nodes = [str(n) for n in raw_targets]

        raw_twins = data.get("twin_nodes")
        if raw_twins is None and data.get("twin_node_id"):
            raw_twins = [str(data["twin_node_id"])]
        if not isinstance(raw_twins, list) or not raw_twins:
            raise WorkspaceError(f"task {task_id}: missing twin_nodes / twin_node_id")
        twin_nodes = [str(n) for n in raw_twins]

        allowed_paths = validate_allowed_paths(list(data.get("allowed_paths") or []))
        test_cmd = str(data.get("test_cmd") or f"pytest {target_nodes[0]}")
        baseline = dict(data.get("baseline") or {})
        for req_key in ("passed", "skipped", "xfail"):
            if req_key not in baseline:
                raise WorkspaceError(f"task {task_id}: baseline missing {req_key!r}")

        scrubbed_path = data.get("scrubbed_test_path") or data.get("scrubbed_test")
        if scrubbed_path and bank_dir is not None and not Path(scrubbed_path).is_absolute():
            scrubbed_path = str(Path(bank_dir) / scrubbed_path)
        twin_path = data.get("twin_test_path") or data.get("twin_test")
        if twin_path and bank_dir is not None and not Path(twin_path).is_absolute():
            twin_path = str(Path(bank_dir) / twin_path)

        return cls(
            id=task_id,
            parent_commit=parent_commit,
            test_file=test_file,
            target_nodes=target_nodes,
            twin_nodes=twin_nodes,
            test_cmd=test_cmd,
            allowed_paths=allowed_paths,
            baseline={
                "passed": int(baseline["passed"]),
                "skipped": int(baseline["skipped"]),
                "xfail": int(baseline["xfail"]),
            },
            scrubbed_test_path=str(scrubbed_path) if scrubbed_path else None,
            scrubbed_test_content=data.get("scrubbed_test_content"),
            twin_test_path=str(twin_path) if twin_path else None,
            twin_test_content=data.get("twin_test_content"),
            difficulty=str(data.get("difficulty") or "medium"),
            design_notes=[normal_rel_path(p) for p in (data.get("design_notes") or [])],
            repo=str(data.get("repo") or ""),
        )

    def read_scrubbed_test(self) -> str:
        if self.scrubbed_test_content is not None:
            return self.scrubbed_test_content
        if self.scrubbed_test_path:
            p = Path(self.scrubbed_test_path)
            if p.is_file():
                return p.read_text(encoding="utf-8")
        raise WorkspaceError(f"task {self.id}: no readable scrubbed test")

    def read_twin_test(self) -> str:
        if self.twin_test_content is not None:
            return self.twin_test_content
        if self.twin_test_path:
            p = Path(self.twin_test_path)
            if p.is_file():
                return p.read_text(encoding="utf-8")
        raise WorkspaceError(f"task {self.id}: no readable held-out twin test")


def load_task_bank(bank_path: str | Path) -> list[TaskSpec]:
    """Load a list of `TaskSpec` entries from a task bank JSON file."""
    p = Path(bank_path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    items = raw.get("tasks") if isinstance(raw, dict) else raw
    if not isinstance(items, list) or not items:
        raise WorkspaceError(f"task bank {p} contains no tasks")
    return [TaskSpec.from_dict(item, bank_dir=p.parent) for item in items]


def git_env(home_dir: str | Path, base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Build an isolated git environment with `GIT_CONFIG_NOSYSTEM=1` and empty `HOME` (F9)."""
    home = Path(home_dir).resolve()
    home.mkdir(parents=True, exist_ok=True)
    source = base_env if base_env is not None else os.environ
    env: dict[str, str] = {}
    for k in ("PATH", "SystemRoot", "SYSTEMROOT", "COMSPEC", "WINDIR", "TMP", "TEMP", "TMPDIR"):
        if k in source:
            env[k] = source[k]
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = str(home / ".gitconfig")
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    env["XDG_CONFIG_HOME"] = str(home / ".config")
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _matches_any_glob(rel: str, patterns: tuple[str, ...] | list[str]) -> bool:
    for pat in patterns:
        if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel.lower(), pat.lower()):
            return True
    return False


def strip_leaking_files(
    workspace_dir: str | Path,
    extra_design_notes: list[str] | None = None,
) -> list[str]:
    """Remove `docs/runs/`, `CHANGELOG.md`, and design notes from `workspace_dir` (F7)."""
    root = Path(workspace_dir)
    removed: list[str] = []

    docs_runs = root / "docs" / "runs"
    if docs_runs.exists():
        shutil.rmtree(docs_runs)
        removed.append("docs/runs")

    changelog = root / "CHANGELOG.md"
    if changelog.exists():
        changelog.unlink()
        removed.append("CHANGELOG.md")

    patterns = list(DESIGN_NOTE_GLOBS) + [normal_rel_path(p) for p in (extra_design_notes or [])]
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = normal_rel_path(path.relative_to(root))
        if rel.startswith(".git/") or rel == ".git":
            continue
        base = path.name
        if base.upper().startswith("CHANGELOG"):
            path.unlink()
            removed.append(rel)
            continue
        if _matches_any_glob(rel, patterns):
            path.unlink()
            removed.append(rel)

    return sorted(set(removed))


@dataclass(frozen=True)
class PreparedWorkspace:
    """Metadata and pre-run integrity state for a freshly prepared task workspace."""

    task_id: str
    workspace_dir: Path
    home_dir: Path
    env: dict[str, str]
    parent_commit: str
    baseline_commit: str
    pre_test_hashes: dict[str, str]
    removed_paths: list[str]


def _run_git(cwd: Path, env: dict[str, str], *args: str, binary: bool = False) -> bytes | str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=not binary,
        check=False,
        timeout=60,
    )
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace") if binary else proc.stderr
        raise WorkspaceError(f"git {' '.join(args)} failed in {cwd}: {err.strip()}")
    return proc.stdout


def build_workspace(
    source_repo: str | Path,
    task: TaskSpec | dict,
    dest_dir: str | Path,
    *,
    home_dir: str | Path | None = None,
    bank_dir: str | Path | None = None,
) -> PreparedWorkspace:
    """Create a fresh task workspace from `parent_commit` via `git archive` + `git init` (F7, F9)."""
    spec = task if isinstance(task, TaskSpec) else TaskSpec.from_dict(task, bank_dir=bank_dir)
    validate_allowed_paths(spec.allowed_paths)

    src = Path(source_repo).resolve()
    dest = Path(dest_dir).resolve()
    if dest.exists() and any(dest.iterdir()):
        raise WorkspaceError(f"destination workspace directory is not empty: {dest}")
    dest.mkdir(parents=True, exist_ok=True)

    if home_dir is None:
        home = dest.parent / f".home-{spec.id}"
    else:
        home = Path(home_dir).resolve()
    if home.exists():
        shutil.rmtree(home)
    home.mkdir(parents=True, exist_ok=True)

    env = git_env(home)

    # Export parent_commit via `git archive --format=tar <parent_commit>`
    tar_bytes = _run_git(src, env, "archive", "--format=tar", spec.parent_commit, binary=True)
    assert isinstance(tar_bytes, bytes)
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:*") as tf:
        try:
            tf.extractall(path=dest, filter="data")
        except TypeError:  # pragma: no cover (Python < 3.12 compatibility if filter unsupported)
            tf.extractall(path=dest)

    # F7: Remove docs/runs/, CHANGELOG.md, and design notes
    removed = strip_leaking_files(dest, extra_design_notes=spec.design_notes)

    # F7: Add the PR's scrubbed test
    scrubbed_text = spec.read_scrubbed_test()
    target_test_path = dest / spec.test_file
    target_test_path.parent.mkdir(parents=True, exist_ok=True)
    target_test_path.write_text(scrubbed_text, encoding="utf-8", newline="\n")

    # F9: Initialize a fresh git repository (never a worktree, no remotes, single commit)
    _run_git(dest, env, "init", "-q")
    _run_git(dest, env, "config", "user.name", "builder")
    _run_git(dest, env, "config", "user.email", "builder@localhost")
    _run_git(dest, env, "add", "-A")
    _run_git(dest, env, "commit", "-q", "-m", "baseline")
    head = str(_run_git(dest, env, "rev-parse", "HEAD")).strip()

    pre_hashes = snapshot_test_hashes(dest)
    return PreparedWorkspace(
        task_id=spec.id,
        workspace_dir=dest,
        home_dir=home,
        env=env,
        parent_commit=spec.parent_commit,
        baseline_commit=head,
        pre_test_hashes=pre_hashes,
        removed_paths=removed,
    )
