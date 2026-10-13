"""Collect experiment records from the studio's tool repositories into the public library.

A tool repository commits its own pre-registered specs and run records (interlock's receipts),
the way every repository commits its Atlas map. The library keeps only a trimmed copy of the
numbers it publishes. This module makes that copy repeatable and checkable:

- `experiments/<name>/collect.json` names the source repository, the sibling clone to read it
  from, and each source: a path, the commit to read it at, the SHA-256 of its bytes, the output
  file, and the trim function that turns the bytes into the published record.
- The bytes are read with `git show <commit>:<path>`, so the clone needs that commit and nothing
  else; its working tree and branch don't matter.
- A source whose bytes no longer hash to the pinned SHA-256 is refused, never re-trimmed.
- The trim function lives in the experiment's own module (default `extract.py`), because what a
  record keeps is the experiment's decision. It must return a record whose `provenance` names
  the source repository, the source path and the SHA-256 of the bytes it read.
- Every output passes the public guard before anything is written: no machine path, no home
  directory, no environment dump. A module may add its own stricter `assert_public`.
- `--check` recomputes every output and compares it byte for byte with the committed file, so
  drift between a source and its published copy is found, not assumed away.

Outputs are written as indented JSON with LF line endings on every OS.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

SPEC = "collect.json"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
FN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
# A trimmed record is public. These shapes mean a machine detail survived the trim.
PRIVATE = (
    (re.compile(r"[A-Za-z]:[\\/]"), "a drive path"),
    (re.compile(r"\\\\"), "a backslash path"),
    (re.compile(r"(?i)[\\/](users|home)[\\/]"), "a home directory"),
    (re.compile(r"(?i)appdata|localappdata"), "an AppData path"),
    (re.compile(r'(?i)"(argv|environment|env|server_config_line)"\s*:'), "an environment field"),
)


class CollectError(Exception):
    def __init__(self, code, message, hint=""):
        super().__init__(message)
        self.code, self.hint = code, hint


@dataclass(frozen=True)
class Context:
    """What a trim function may use: the source's identity and a reader for other files at a commit."""

    repo: str
    clone: Path
    source: str
    commit: str

    def show(self, commit: str, path: str) -> bytes:
        return git_show(self.clone, commit, path)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_show(clone: Path, commit: str, path: str) -> bytes:
    got = subprocess.run(["git", "-C", str(clone), "show", f"{commit}:{path}"], capture_output=True)
    if got.returncode != 0:
        detail = got.stderr.decode("utf-8", "replace").strip().splitlines()
        raise CollectError("COLLECT_SOURCE_UNREADABLE",
                           f"{commit[:7]}:{path} could not be read from the clone ({detail[-1] if detail else 'no output'})",
                           "fetch the source repository in the clone so it holds that commit, or pass --clone")
    return got.stdout


def experiments(root: Path) -> list[Path]:
    return sorted(p.parent for p in (root / "experiments").glob(f"*/{SPEC}"))


def load_spec(exp_dir: Path) -> dict:
    path = exp_dir / SPEC
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise CollectError("COLLECT_NO_SPEC", f"{path.as_posix()} does not exist",
                           "add experiments/<name>/collect.json (see `rnd collect --help`)") from None
    except json.JSONDecodeError as exc:
        raise CollectError("COLLECT_BAD_SPEC", f"{SPEC} is not JSON: {exc}") from None
    problems = spec_problems(spec)
    if problems:
        raise CollectError("COLLECT_BAD_SPEC", f"{exp_dir.name}/{SPEC}: {problems[0]}",
                           "; ".join(problems[1:]) if len(problems) > 1 else "")
    return spec


def spec_problems(spec) -> list[str]:
    if not isinstance(spec, dict):
        return ["the spec is a JSON object"]
    out = []
    if not isinstance(spec.get("repo"), str) or not REPO_RE.match(spec["repo"]):
        out.append("repo is owner/name")
    if not isinstance(spec.get("sibling"), str) or not NAME_RE.match(spec.get("sibling", "") or ""):
        out.append("sibling is the clone's folder name next to the library (lower case, digits, hyphens)")
    module = spec.get("module", "extract.py")
    if not isinstance(module, str) or "/" in module or "\\" in module or not module.endswith(".py"):
        out.append("module is a .py file name inside the experiment folder")
    sources = spec.get("sources")
    if not isinstance(sources, list) or not sources:
        out.append("sources lists at least one source")
        return out
    outs = set()
    for i, s in enumerate(sources):
        where = f"sources[{i}]"
        if not isinstance(s, dict):
            out.append(f"{where} is an object")
            continue
        path = s.get("path")
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in path.split("/"):
            out.append(f"{where}.path is a repository-relative path")
        if not isinstance(s.get("commit"), str) or not SHA_RE.match(s["commit"]):
            out.append(f"{where}.commit is a full 40-hex commit")
        if not isinstance(s.get("sha256"), str) or not SHA256_RE.match(s["sha256"]):
            out.append(f"{where}.sha256 is the 64-hex SHA-256 of the source bytes")
        o = s.get("out")
        if not isinstance(o, str) or not o.endswith(".json") or o.startswith("/") or ".." in o.split("/"):
            out.append(f"{where}.out is a .json path inside the experiment folder")
        elif o in outs:
            out.append(f"{where}.out {o} is written twice")
        else:
            outs.add(o)
        if not isinstance(s.get("fn"), str) or not FN_RE.match(s["fn"]):
            out.append(f"{where}.fn names a function in the module")
    return out


def load_module(exp_dir: Path, spec: dict):
    path = exp_dir / spec.get("module", "extract.py")
    if not path.is_file():
        raise CollectError("COLLECT_NO_MODULE", f"{path.as_posix()} does not exist")
    module_spec = importlib.util.spec_from_file_location(f"rnd_collect_{exp_dir.name.replace('-', '_')}", path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def guard_public(text: str, name: str, module=None) -> None:
    found = [label for pattern, label in PRIVATE if pattern.search(text)]
    if found:
        raise CollectError("COLLECT_NOT_PUBLIC", f"{name} still carries {', '.join(found)}",
                           "trim that field in the experiment's module; the library is public")
    extra = getattr(module, "assert_public", None)
    if callable(extra):
        try:
            extra(text, name)
        except SystemExit as exc:
            raise CollectError("COLLECT_NOT_PUBLIC", str(exc)) from None


def render(record: dict) -> str:
    return json.dumps(record, indent=2) + "\n"


def collect_one(exp_dir: Path, spec: dict, source: dict, clone: Path, module) -> tuple[str, str]:
    """(output path, rendered text) for one source. Raises CollectError on any refusal."""

    raw = git_show(clone, source["commit"], source["path"])
    digest = sha256(raw)
    if digest != source["sha256"]:
        raise CollectError("COLLECT_SOURCE_CHANGED",
                           f"{source['path']} at {source['commit'][:7]} hashes to {digest[:12]}…, "
                           f"not the pinned {source['sha256'][:12]}…",
                           "a pinned source never changes; pin the new commit and its SHA-256 on purpose")
    fn = getattr(module, source["fn"], None)
    if not callable(fn):
        raise CollectError("COLLECT_NO_FUNCTION", f"{source['fn']} is not defined in {spec.get('module', 'extract.py')}")
    ctx = Context(repo=spec["repo"], clone=clone, source=source["path"], commit=source["commit"])
    try:
        record = fn(raw, ctx)
    except SystemExit as exc:
        raise CollectError("COLLECT_TRIM_REFUSED", f"{source['fn']} refused {source['path']}: {exc}") from None
    if not isinstance(record, dict):
        raise CollectError("COLLECT_TRIM_REFUSED", f"{source['fn']} did not return a JSON object")
    prov = record.get("provenance")
    if not isinstance(prov, dict) or prov.get("sha256") != digest or prov.get("repo") != spec["repo"] \
            or prov.get("source") != source["path"]:
        raise CollectError("COLLECT_NO_PROVENANCE",
                           f"{source['fn']}'s record must carry provenance with repo {spec['repo']}, "
                           f"source {source['path']} and the sha256 of the bytes it read")
    text = render(record)
    guard_public(text, source["out"], module)
    return source["out"], text


def run(root: Path, name: str, clone: Path | None = None, check: bool = False) -> dict:
    """Collect (or, with check, verify) every source of one experiment. Nothing is written on a refusal."""

    if not NAME_RE.match(name or ""):
        raise CollectError("COLLECT_BAD_NAME", f"{name!r} is not an experiment folder name")
    exp_dir = root / "experiments" / name
    spec = load_spec(exp_dir)
    clone = clone or (root.parent / spec["sibling"])
    if not (clone / ".git").exists():
        raise CollectError("COLLECT_NO_CLONE", f"no git clone of {spec['repo']} at {clone.as_posix()}",
                           f"clone it next to the library as {spec['sibling']}/, or pass --clone")
    module = load_module(exp_dir, spec)
    results = [collect_one(exp_dir, spec, source, clone, module) for source in spec["sources"]]
    report = {"experiment": name, "repo": spec["repo"], "files": [], "drift": []}
    for out, text in results:
        target = exp_dir / out
        if check:
            current = target.read_bytes() if target.is_file() else None
            if current != text.encode("utf-8"):
                report["drift"].append(out)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8", newline="\n")
        report["files"].append(out)
    report["ok"] = not report["drift"]
    return report
