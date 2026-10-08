"""Micro version bumps for a library that changes daily.

Versions have five segments, MAJOR.MINOR.PATCH.MICRO.NANO:
  - MAJOR / MINOR / PATCH: the rnd tool itself (semver meaning);
  - MICRO: a structural library change (a new experiment, catalogue or instrument family);
  - NANO: an ordinary library update (entries filed or revised, results added).
A bump raises one segment and resets the ones after it. `1.0.0` reads as `1.0.0.0.0`.
"""

import re
import subprocess
from datetime import date
from pathlib import Path

from . import frontmatter

LEVELS = ("major", "minor", "patch", "micro", "nano")
VERSION_RE = re.compile(r'^__version__ = "([^"]+)"', re.M)
LIBRARY_DIRS = ("entries", "instruments", "experiments", "catalogs")


class ReleaseError(Exception):
    def __init__(self, code, message, hint=""):
        super().__init__(message)
        self.code, self.hint = code, hint


def parse(version):
    parts = version.split(".")
    if not 1 <= len(parts) <= 5 or not all(p.isdigit() for p in parts):
        raise ReleaseError("BAD_VERSION", f"version {version!r} is not 1 to 5 dot-separated numbers")
    return [int(p) for p in parts] + [0] * (5 - len(parts))


def bump(version, level="nano"):
    if level not in LEVELS:
        raise ReleaseError("BAD_LEVEL", f"level {level!r} is not one of {', '.join(LEVELS)}")
    v = parse(version)
    i = LEVELS.index(level)
    v[i] += 1
    v[i + 1:] = [0] * (4 - i)
    return ".".join(map(str, v))


def read_version(root):
    text = (Path(root) / "mcptoolshop_rnd" / "__init__.py").read_text(encoding="utf-8")
    m = VERSION_RE.search(text)
    if not m:
        raise ReleaseError("BAD_VERSION", "mcptoolshop_rnd/__init__.py has no __version__ line")
    return m.group(1)


def write_version(root, new):
    p = Path(root) / "mcptoolshop_rnd" / "__init__.py"
    p.write_text(VERSION_RE.sub(f'__version__ = "{new}"', p.read_text(encoding="utf-8")), encoding="utf-8")


def _git(root, *args):
    try:
        out = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8")
    except OSError as exc:
        raise ReleaseError("GIT_FAILED", f"git could not run: {exc}", "install git, or bump by hand") from exc
    if out.returncode != 0:
        raise ReleaseError("GIT_FAILED", out.stderr.strip() or f"git {' '.join(args)} failed")
    return out.stdout


def last_tag(root):
    try:
        return _git(root, "describe", "--tags", "--abbrev=0", "--match", "v*").strip()
    except ReleaseError:
        return None


def changes(root, since):
    """(status, path) for library files changed since a tag, including uncommitted and untracked ones."""
    found = {}
    if since:
        for line in _git(root, "diff", "--name-status", since, "--", *LIBRARY_DIRS).splitlines():
            status, *paths = line.split("\t")
            found[paths[-1]] = "A" if status.startswith(("A", "R", "C")) else "D" if status == "D" else "M"
    for path in _git(root, "ls-files", "--others", "--exclude-standard", "--", *LIBRARY_DIRS).splitlines():
        found[path] = "A"
    return [(status, path) for path, status in sorted(found.items())]


def _title(root, path):
    try:
        meta, _ = frontmatter.read((Path(root) / path).read_text(encoding="utf-8"))
        return str(meta.get("title") or "").strip()
    except (OSError, UnicodeDecodeError, frontmatter.FrontmatterError):
        return ""


def changelog_section(root, version, changed, notes=(), today=None):
    words = {"A": "Added", "M": "Updated", "D": "Removed"}
    lines = [f"## [{version}] - {today or date.today().isoformat()}", ""]
    lines += [f"- {n}" for n in notes]
    entries = [(s, p) for s, p in changed if p.startswith(("entries/", "instruments/")) and p.endswith(".md")]
    for s, p in entries:
        title = _title(root, p) if s != "D" else ""
        lines.append(f"- {words[s]} `{Path(p).stem}`" + (f": {title}" if title else ""))
    groups = {}
    for s, p in changed:
        parts = Path(p).parts
        if parts[0] in ("experiments", "catalogs") and len(parts) > 1:
            groups.setdefault(f"{parts[0][:-1]} `{parts[1]}`", set()).add(s)
    for name, kinds in sorted(groups.items()):
        lines.append(f"- {'Added' if kinds == {'A'} else 'Updated'} {name}")
    if len(lines) == 2:
        lines.append("- No library changes; version bump only.")
    return "\n".join(lines) + "\n"


def insert_changelog(root, section):
    p = Path(root) / "CHANGELOG.md"
    text = p.read_text(encoding="utf-8")
    marker = "## [Unreleased]"
    if marker not in text:
        raise ReleaseError("BAD_CHANGELOG", "CHANGELOG.md has no '## [Unreleased]' heading")
    head, tail = text.split(marker, 1)
    rest = tail.lstrip("\n")
    p.write_text(head + marker + "\n\n" + section + ("\n" + rest if rest else ""), encoding="utf-8")
