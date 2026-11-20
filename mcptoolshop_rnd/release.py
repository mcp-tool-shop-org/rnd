"""Micro version bumps for a library that changes daily.

Versions have five segments, MAJOR.MINOR.PATCH.MICRO.NANO:
  - MAJOR / MINOR / PATCH: the rnd tool itself (semver meaning);
  - MICRO: a structural library change (a new experiment, catalogue or instrument family);
  - NANO: an ordinary library update (entries filed or revised, results added).
A bump raises one segment and resets the ones after it. `1.0.0` reads as `1.0.0.0.0`.
"""

import re
import secrets
import subprocess
from datetime import date
from pathlib import Path

from . import frontmatter

LEVELS = ("major", "minor", "patch", "micro", "nano")
VERSION_RE = re.compile(r'^__version__ = "([^"]+)"', re.M)
LIBRARY_DIRS = ("entries", "instruments", "experiments", "catalogs")
CHANGES_DIR = "changes"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLUG_RE = re.compile(r"[^a-z0-9]+")


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


def add_fragment(root, text, level="nano", today=None):
    """Write one changelog fragment under changes/ using a 32-bit random hex token to prevent branch collisions."""
    if level not in LEVELS:
        raise ReleaseError("BAD_LEVEL", f"level {level!r} is not one of {', '.join(LEVELS)}")
    body = " ".join((text or "").strip().splitlines()).strip()
    if not body:
        raise ReleaseError("BAD_CHANGE", "change text must not be empty", 'pass a short summary: rnd change "what changed"')
    day = today or date.today().isoformat()
    if not DATE_RE.match(day):
        raise ReleaseError("BAD_DATE", f"date {day!r} must be YYYY-MM-DD")
    slug = re.sub(r"-+", "-", SLUG_RE.sub("-", body.lower())).strip("-")[:32] or "change"
    changes_dir = Path(root) / CHANGES_DIR
    changes_dir.mkdir(parents=True, exist_ok=True)
    while True:
        filename = f"{day}-{secrets.token_hex(4)}-{slug}.md"
        target = changes_dir / filename
        try:
            with open(target, "x", encoding="utf-8", newline="\n") as fh:
                fh.write(f"---\nlevel: {level}\ndate: {day}\n---\n\n{body}\n")
            return f"{CHANGES_DIR}/{filename}"
        except FileExistsError:  # pragma: no cover
            continue


def _parse_fragment(root, path):
    rel = path.relative_to(root).as_posix()
    base = Path(root) / CHANGES_DIR
    if path.parent != base or path.suffix != ".md":
        return None, (rel, "fragment must be a .md file directly under changes/")
    try:
        raw = path.read_text(encoding="utf-8")
        meta_text, body = frontmatter.split(raw)
        if meta_text is None:
            return None, (rel, "missing frontmatter (expected 'level: nano|micro|patch|minor|major')")
        meta = frontmatter.parse(meta_text)
    except (OSError, UnicodeDecodeError, frontmatter.FrontmatterError) as exc:
        return None, (rel, f"unreadable fragment: {exc}")
    unknown = sorted(set(meta) - {"level", "date"})
    if unknown:
        return None, (rel, f"unknown fragment keys: {', '.join(unknown)}")
    level = meta.get("level")
    if not isinstance(level, str) or level not in LEVELS:
        return None, (rel, f"fragment 'level' must be one of {', '.join(LEVELS)}; got {level!r}")
    frag_date = meta.get("date")
    if frag_date is not None and (not isinstance(frag_date, str) or not DATE_RE.match(frag_date)):
        return None, (rel, f"fragment 'date' must be YYYY-MM-DD, got {frag_date!r}")
    frag_text = " ".join(body.strip().splitlines()).strip()
    if not frag_text:
        return None, (rel, "fragment body is empty")
    return {"path": rel, "level": level, "date": frag_date or "", "text": frag_text}, None


def load_fragments(root):
    """Return (valid_fragments, problems) for files under changes/."""
    base = Path(root) / CHANGES_DIR
    if not base.is_dir():
        return [], []
    valid, problems = [], []
    for path in sorted(p for p in base.rglob("*") if p.is_file() and not p.name.startswith(".")):
        frag, err = _parse_fragment(root, path)
        if err is not None:
            problems.append(err)
        else:
            valid.append(frag)
    valid.sort(key=lambda f: (f["date"], f["path"]))
    return valid, problems


def highest_level(levels):
    """Return the most significant bump level among an iterable of level names."""
    return min(levels, key=LEVELS.index)


def fragments_changelog_section(version, fragments, notes=(), today=None):
    """Format one CHANGELOG section listing every fragment's text."""
    lines = [f"## [{version}] - {today or date.today().isoformat()}", ""]
    lines += [f"- {n}" for n in notes]
    lines += [f"- {f['text']}" for f in fragments]
    return "\n".join(lines) + "\n"
