"""Library layout rules: what may sit in the public clone, and each experiment's record.

Three rules, all run by `rnd check`:

- **Size.** A file under experiments/ may be at most FILE_LIMIT bytes, and an experiment folder at most
  EXPERIMENT_LIMIT in total. Files and folders that were larger when the rule began are listed in the baseline
  (docs/layout.json) and may not grow past their recorded size; the list may shrink, and growing it is a reviewed
  change. Bulk data goes to a data pack (built from a gitignored staging/ folder), raw run output to rnd-data.
- **Private files.** No file in the library may carry the private tag, have a private-looking name, or, where an
  rnd-data checkout is present, match a SHA-256 in its private manifest. Published files whose names only look
  private (a completed blind pass) are on the baseline's reviewed allow-list.
- **The experiment record.** Every experiment folder has an experiment.json (schema rnd-experiment/v1), except the
  folders the baseline lists as made before the rule.
"""

import fnmatch
import hashlib
import json
import os
import re
import subprocess
from datetime import date
from pathlib import Path

FILE_LIMIT = 256 * 1024
EXPERIMENT_LIMIT = 2 * 1024 * 1024
BASELINE = "docs/layout.json"
BASELINE_SCHEMA = "rnd-layout/v1"
# Built in two parts so this file does not itself carry the tag.
PRIVATE_TAG = "T5-PRIVATE-" + "DO-NOT-PUBLISH"
PRIVATE_NAMES = ("*blind*", "*sealed*", "*gold[-_]key*", "*item[-_]text*", "*itemtext*", "*review[-_]items*")
TAG_SCAN_LIMIT = 8 * 1024 * 1024  # files larger than this are bulk data and fail the size rule anyway
# The exact private match skips files shorter than this: an empty file, `[]` or `{}` hashes the same everywhere, so
# a match says nothing about where it came from (measured 2026-10-19: 3 such false hits, all 0 or 2 bytes).
MIN_PRIVATE_MATCH_BYTES = 16

SCHEMA = "rnd-experiment/v1"
STATUSES = ("designing", "running", "parked", "closed")
# The run vocabulary is shared with the Publisher's outcome.json and lives in one file both sides read.
VOCABULARY = json.loads((Path(__file__).parent / "run_vocabulary.json").read_text(encoding="utf-8"))
COST_UNITS = tuple(VOCABULARY["cost_units"])
VENUES = tuple(VOCABULARY["venues"])
OUTCOMES = tuple(VOCABULARY["outcomes"])
COST_BASES = tuple(VOCABULARY["cost_bases"])
WHY_NOT_NEEDED = tuple(VOCABULARY["why_required_unless"])
ZERO_COST = tuple(VOCABULARY["zero_cost"])
# Older words the recorder maps to a current outcome; a record always holds the current word.
ALIASES = dict(VOCABULARY["aliases"])
TOP_KEYS = {"schema", "name", "status", "design", "template", "budgets", "licences", "runs"}
# excludes: runs of the experiment that fall outside this cap (e.g. made before the budget began), with the reason.
# reconciled: groups of runs that overlapped and share one measured total (a provider balance), with the reason. The
# ledger counts the measured total for the group instead of adding the runs' own estimates, which overcount.
BUDGET_KEYS = {"cost_unit", "cap", "set_by", "excludes", "excludes_why", "reconciled", "phases"}
PHASE_KEYS = {"name", "cap", "set_by", "from"}  # plus an optional "closed"
RECONCILED_KEYS = {"runs", "measured", "why"}
RUN_KEYS = {"id", "venue", "hardware", "date", "cost", "cost_unit", "cost_basis", "cap", "projected_cost", "outcome",
            "why", "raw_manifest_id", "pins"}
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# A home directory in any OS's form: Windows (a drive, then Users, then the account, with either slash), Git Bash and
# WSL mounts of the same, macOS (Users at the root) and Linux or WSL (home at the root), as the tests spell out. Written
# out here, those forms would trip the studio's own identity scan. Needle-free: it names no account, so it can run in public
# CI. The studio's identity scan has the needles; this is the floor under it (rnd-data, 2026-10-20: four public logs
# carried a /home/<account> path the scan's Windows-only patterns missed).
HOME_PATH_RE = re.compile(
    r"(?i)(?:[a-z]:[\\/]+users[\\/]+[^\\/\s\"'*<>|]+|(?:/mnt)?/[a-z]/users/[^/\s\"']+|(?<![\w.])/users/[^/\s\"']+"
    r"|(?<![\w.])/home/[^/\s\"']+)")
# Content markers the public tree must never carry, whatever the rules files say (they're checked against this list).
# CALL_CHECKPOINT lines hold gzip+base64 call-journal checkpoints: drafts in an encoding no scan reads.
CONTENT_MARKERS = ("CALL_CHECKPOINT",)
# A machine path: a drive letter (C:/, E:\), a Git Bash or WSL drive mount (/c/, /mnt/c/), a UNC share, or a home
# directory. Pod and VM paths (/root/, /content/, /workspace/) carry no identity and are allowed. A share's name is word
# characters, dots, dollars and hyphens, so an escaped backslash in code, such as jq's "\\(.sha256)", isn't one.
MACHINE_PATH_RE = re.compile(
    r"(?i)(?:^|[\s\"'(=])(?:[a-z]:[\\/]|(?:/mnt)?/[a-z]/|\\\\[\w.$-]+\\|/home/|/users/|~[\\/])")


def library_files(root: Path) -> list[str]:
    """Every file git would commit (tracked, or untracked and not ignored), as POSIX paths relative to root.

    Without git (a plain copy of the library) every file is walked, skipping .git and staging/ folders."""
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                             capture_output=True, check=True, timeout=60).stdout
        files = sorted({p for p in out.decode("utf-8").split("\0") if p})
        return [p for p in files if (root / p).is_file()]
    except (OSError, subprocess.SubprocessError):
        found = []
        for d, dirs, names in os.walk(root):
            dirs[:] = [x for x in dirs if x not in (".git", "staging", "node_modules", ".venv", "__pycache__")]
            found += [(Path(d) / n).relative_to(root).as_posix() for n in names]
        return sorted(found)


def size_of(path: Path) -> int:
    """A file's size with each CRLF counted as one byte, so a Windows checkout (CRLF) and a Linux one (LF) measure
    the same; files over the scan limit are bulk anyway and are measured as they stand."""
    n = path.stat().st_size
    if n > TAG_SCAN_LIMIT:
        return n
    return n - path.read_bytes().count(b"\r\n")


def experiment_of(path: str) -> str | None:
    parts = path.split("/")
    return parts[1] if len(parts) > 2 and parts[0] == "experiments" else None


def load_baseline(root: Path) -> tuple[dict, list[str]]:
    p = root / BASELINE
    empty = {"files": {}, "experiments": {}, "no_record": [], "private_allow": {}}
    if not p.exists():
        return empty, []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return empty, [f"not valid JSON ({exc})"]
    problems = []
    if not isinstance(data, dict) or data.get("schema") != BASELINE_SCHEMA:
        return empty, [f"schema must be {BASELINE_SCHEMA!r}"]
    for key, kind in (("files", dict), ("experiments", dict), ("no_record", list), ("private_allow", dict)):
        if not isinstance(data.get(key), kind):
            problems.append(f"{key!r} must be a {kind.__name__}")
            data[key] = kind()
    for path, why in data["private_allow"].items():
        if not isinstance(why, str) or not why.strip():
            problems.append(f"private_allow {path!r} needs a reason")
    return data, problems


def baseline(root: Path, files: list[str] | None = None) -> dict:
    """The baseline as the library stands: every oversize file and folder, every folder without a record, and every
    file whose name looks private (each needs a reason added by hand before it passes)."""
    files = library_files(root) if files is None else files
    sizes = {p: size_of(root / p) for p in files}
    big_files, per_exp = {}, {}
    for p, n in sizes.items():
        exp = experiment_of(p)
        if exp is None:
            continue
        per_exp[exp] = per_exp.get(exp, 0) + n
        if n > FILE_LIMIT:
            big_files[p] = n
    exps = sorted({experiment_of(p) for p in files if experiment_of(p)})
    return {
        "schema": BASELINE_SCHEMA,
        "made": date.today().isoformat(),
        "limits": {"file_bytes": FILE_LIMIT, "experiment_bytes": EXPERIMENT_LIMIT},
        "files": dict(sorted(big_files.items())),
        "experiments": {e: n for e, n in sorted(per_exp.items()) if n > EXPERIMENT_LIMIT},
        "no_record": [e for e in exps if f"experiments/{e}/experiment.json" not in sizes],
        "private_allow": {p: "" for p in files if private_name(p)},
    }


def private_name(path: str) -> bool:
    name = path.rsplit("/", 1)[-1].lower()
    return any(fnmatch.fnmatchcase(name, g) for g in PRIVATE_NAMES)


def private_root(root: Path) -> Path:
    """The private companion's checkout: $RND_DATA_PRIVATE, else ../rnd-data-private beside the library."""
    return Path(os.environ["RND_DATA_PRIVATE"]) if os.environ.get("RND_DATA_PRIVATE") else root.parent / "rnd-data-private"


def private_manifest(root: Path) -> tuple[set[str], str | None]:
    """SHA-256s from rnd-data-private's manifest, when a checkout is present. A tagged file's source_sha256 (the
    original's hash) is included, since a leak of the untagged original would match it."""
    p = private_root(root) / "manifest.json"
    if not p.exists():
        return set(), None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return {h for f in data["files"] for h in (f["sha256"], f.get("source_sha256")) if h}, None
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        return set(), f"rnd-data-private's manifest unreadable ({type(exc).__name__}); the exact private check did not run"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check(root: Path, files: list[str] | None = None, registry_ids: set[str] | None = None) -> list[tuple[str, str, str]]:
    """Every layout problem as (level, where, message)."""
    files = library_files(root) if files is None else files
    base, base_problems = load_baseline(root)
    out = [("error", BASELINE, m) for m in base_problems]
    sizes = {p: size_of(root / p) for p in files}

    # Size.
    per_exp = {}
    for p, n in sizes.items():
        exp = experiment_of(p)
        if exp is None:
            continue
        per_exp[exp] = per_exp.get(exp, 0) + n
        if n > FILE_LIMIT:
            allowed = base["files"].get(p)
            if allowed is None:
                out.append(("error", p, f"{n:,} bytes is over the {FILE_LIMIT // 1024} KB limit for a file in "
                                        "experiments/; put bulk data in a data pack (build it from staging/) or raw "
                                        "output in rnd-data"))
            elif n > allowed:
                out.append(("error", p, f"grew from {allowed:,} to {n:,} bytes; a grandfathered file may not grow"))
    for exp, n in sorted(per_exp.items()):
        if n > EXPERIMENT_LIMIT:
            allowed = base["experiments"].get(exp)
            if allowed is None:
                out.append(("error", f"experiments/{exp}", f"{n:,} bytes is over the "
                                                           f"{EXPERIMENT_LIMIT // (1024 * 1024)} MB limit for an experiment"))
            elif n > allowed:
                out.append(("error", f"experiments/{exp}", f"grew from {allowed:,} to {n:,} bytes; a grandfathered "
                                                           "experiment may not grow"))
    for p in base["files"]:
        if p not in sizes:
            out.append(("warning", BASELINE, f"{p} is gone; drop it from the baseline"))

    # Private files.
    hashes, manifest_problem = private_manifest(root)
    if manifest_problem:
        out.append(("warning", "rnd-data", manifest_problem))
    tag = PRIVATE_TAG.encode()
    for p in files:
        if p in base["private_allow"] and base["private_allow"][p].strip():
            continue
        if private_name(p):
            out.append(("error", p, "the name looks private (blind, sealed, gold key, item text, review items); "
                                    "private files live in rnd-data-private, or list a published one in the "
                                    "baseline's private_allow with a reason"))
            continue
        full = root / p
        if sizes[p] <= TAG_SCAN_LIMIT and tag in full.read_bytes():
            out.append(("error", p, "carries the private tag; private files live in rnd-data-private"))
            continue
        if hashes and sizes[p] >= MIN_PRIVATE_MATCH_BYTES and sha256(full) in hashes:
            out.append(("error", p, "matches a file in rnd-data-private's manifest"))

    # Experiment records.
    exps = sorted({experiment_of(p) for p in files if experiment_of(p)})
    for exp in exps:
        rec = f"experiments/{exp}/experiment.json"
        if rec in sizes:
            out += [("error", rec, m) for m in validate_record(root, exp, registry_ids)]
        elif exp not in base["no_record"]:
            out.append(("error", f"experiments/{exp}", "no experiment.json; `rnd new-experiment` makes one"))
    for exp in base["no_record"]:
        if f"experiments/{exp}/experiment.json" in sizes:
            out.append(("warning", BASELINE, f"{exp} now has experiment.json; drop it from no_record"))
    return out


def _machine_paths(value, where=""):
    if isinstance(value, str):
        return [where] if MACHINE_PATH_RE.search(value) else []
    if isinstance(value, dict):
        return [w for k, v in value.items() for w in _machine_paths(v, f"{where}.{k}" if where else k)]
    if isinstance(value, list):
        return [w for i, v in enumerate(value) for w in _machine_paths(v, f"{where}[{i}]")]
    return []


def _number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate_record(root: Path, exp: str, registry_ids: set[str] | None = None) -> list[str]:
    """Problems in experiments/<exp>/experiment.json."""
    try:
        data = json.loads((root / "experiments" / exp / "experiment.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"not valid JSON ({exc})"]
    return validate_data(root, exp, data, registry_ids)


def validate_data(root: Path, exp: str, data, registry_ids: set[str] | None = None) -> list[str]:
    """Problems in an experiment record held in memory (what `rnd runs record` checks before it writes)."""
    if not isinstance(data, dict):
        return ["must be a JSON object"]
    p = []
    unknown = sorted(set(data) - TOP_KEYS)
    if unknown:
        p.append(f"unknown keys: {', '.join(unknown)}")
    if data.get("schema") != SCHEMA:
        p.append(f"schema must be {SCHEMA!r}")
    if data.get("name") != exp:
        p.append(f"name must be the folder name, {exp!r}")
    if data.get("status") not in STATUSES:
        p.append(f"status must be one of {', '.join(STATUSES)}")
    design = data.get("design")
    if not isinstance(design, str) or not design or not (root / "experiments" / exp / design).is_file():
        p.append("design must name a file in the experiment folder")
    template = data.get("template")
    if template is not None:
        handbook = root / "site" / "src" / "content" / "docs" / "handbook"
        if not isinstance(template, str) or (handbook.is_dir() and not (handbook / f"{template}.md").is_file()):
            p.append("template must name a handbook page (site/src/content/docs/handbook/<template>.md), or be null")

    budgets = data.get("budgets", [])
    units = set()
    if not isinstance(budgets, list):
        p.append("budgets must be a list")
        budgets = []
    for i, b in enumerate(budgets):
        if not isinstance(b, dict):
            p.append(f"budgets[{i}] must be an object")
            continue
        extra = sorted(set(b) - BUDGET_KEYS)
        if extra:
            p.append(f"budgets[{i}]: unknown keys {', '.join(extra)} (spending is computed from runs, never typed)")
        if b.get("cost_unit") not in COST_UNITS:
            p.append(f"budgets[{i}].cost_unit must be one of {', '.join(COST_UNITS)}")
        elif b["cost_unit"] in units:
            p.append(f"budgets[{i}]: a second budget in {b['cost_unit']}; keep one per unit")
        else:
            units.add(b["cost_unit"])
        if not _number(b.get("cap")) or b["cap"] <= 0:
            p.append(f"budgets[{i}].cap must be a positive number")
        if not isinstance(b.get("set_by"), str) or not b["set_by"].strip():
            p.append(f"budgets[{i}].set_by must say who set the cap")
        if "excludes" in b:
            if not isinstance(b["excludes"], list) or not all(isinstance(x, str) and x for x in b["excludes"]):
                p.append(f"budgets[{i}].excludes must be a list of run ids")
            elif not (isinstance(b.get("excludes_why"), str) and b["excludes_why"].strip()):
                p.append(f"budgets[{i}].excludes needs an excludes_why: which runs fall outside the cap, and why")
        elif "excludes_why" in b:
            p.append(f"budgets[{i}].excludes_why without excludes")
        if "reconciled" in b:
            groups = b["reconciled"]
            if not isinstance(groups, list):
                p.append(f"budgets[{i}].reconciled must be a list of groups")
                groups = []
            for j, g in enumerate(groups):
                where = f"budgets[{i}].reconciled[{j}]"
                if not isinstance(g, dict):
                    p.append(f"{where} must be an object")
                    continue
                if set(g) != RECONCILED_KEYS:
                    p.append(f"{where} needs exactly {', '.join(sorted(RECONCILED_KEYS))}")
                if not isinstance(g.get("runs"), list) or len(g.get("runs") or []) < 2 or \
                        not all(isinstance(x, str) and x for x in g["runs"]):
                    p.append(f"{where}.runs must list two or more run ids")
                if not _number(g.get("measured")) or g["measured"] < 0:
                    p.append(f"{where}.measured must be a number, 0 or more")
                if not (isinstance(g.get("why"), str) and g["why"].strip()):
                    p.append(f"{where}.why must say what was measured and why the runs share it")
        if "phases" in b:
            p += _phase_problems(b, i)
            p += _phase_in_force_problems(b, i)

    licences = data.get("licences", [])
    if not isinstance(licences, list) or not all(isinstance(x, str) for x in licences):
        p.append("licences must be a list of licence registry ids")
    elif registry_ids is not None:
        missing = sorted(set(licences) - registry_ids)
        if missing:
            p.append(f"licences not in licences/registry.json: {', '.join(missing)}")

    runs = data.get("runs", [])
    seen = set()
    if not isinstance(runs, list):
        p.append("runs must be a list")
        runs = []
    for i, r in enumerate(runs):
        if not isinstance(r, dict):
            p.append(f"runs[{i}] must be an object")
            continue
        extra = sorted(set(r) - RUN_KEYS)
        if extra:
            p.append(f"runs[{i}]: unknown keys {', '.join(extra)}")
        rid = r.get("id")
        if not isinstance(rid, str) or not rid:
            p.append(f"runs[{i}].id must be a non-empty string")
        elif rid in seen:
            p.append(f"runs[{i}]: id {rid!r} appears twice")
        else:
            seen.add(rid)
        if r.get("venue") not in VENUES:
            p.append(f"runs[{i}].venue must be one of {', '.join(VENUES)}")
        if not isinstance(r.get("hardware"), str):
            p.append(f"runs[{i}].hardware must be a string")
        if not isinstance(r.get("date"), str) or not DATE_RE.match(r["date"]):
            p.append(f"runs[{i}].date must be YYYY-MM-DD")
        if not _number(r.get("cost")) or r["cost"] < 0:
            p.append(f"runs[{i}].cost must be a number, 0 or more")
        if r.get("cost_unit") not in COST_UNITS:
            p.append(f"runs[{i}].cost_unit must be one of {', '.join(COST_UNITS)}")
        if r.get("projected_cost") is not None and not _number(r["projected_cost"]):
            p.append(f"runs[{i}].projected_cost must be a number or null")
        if r.get("outcome") in ALIASES:
            p.append(f"runs[{i}].outcome {r['outcome']!r} is an alias; record it as {ALIASES[r['outcome']]!r}")
        elif r.get("outcome") not in OUTCOMES:
            p.append(f"runs[{i}].outcome must be one of {', '.join(OUTCOMES)}")
        else:
            if r["outcome"] not in WHY_NOT_NEEDED and not (isinstance(r.get("why"), str) and r["why"].strip()):
                p.append(f"runs[{i}]: a {r['outcome']} run needs a why")
            if r["outcome"] in ZERO_COST and r.get("cost") != 0:
                p.append(f"runs[{i}]: a {r['outcome']} run costs nothing; its cost must be 0")
        if r.get("cost_basis") not in COST_BASES:
            p.append(f"runs[{i}].cost_basis must be one of {', '.join(COST_BASES)}")
        if r.get("cap") is not None and (not _number(r["cap"]) or r["cap"] <= 0):
            p.append(f"runs[{i}].cap must be a positive number or null")
        if r.get("raw_manifest_id") is not None and not isinstance(r["raw_manifest_id"], str):
            p.append(f"runs[{i}].raw_manifest_id must be a string or null")
        if not isinstance(r.get("pins", {}), dict):
            p.append(f"runs[{i}].pins must be an object")

    # An excluded run must be a recorded run in the budget's unit, so a typo can't hide spending.
    unit_of = {r.get("id"): r.get("cost_unit") for r in runs if isinstance(r, dict) and isinstance(r.get("id"), str)}
    for i, b in enumerate(budgets):
        if not isinstance(b, dict):
            continue
        named = []
        if isinstance(b.get("excludes"), list):
            named += [("excludes", rid) for rid in b["excludes"]]
        for j, g in enumerate(b.get("reconciled") or [] if isinstance(b.get("reconciled"), list) else []):
            if isinstance(g, dict) and isinstance(g.get("runs"), list):
                named += [(f"reconciled[{j}]", rid) for rid in g["runs"]]
        seen_once = {}
        for where, rid in named:
            if not isinstance(rid, str):
                continue
            if rid not in unit_of:
                p.append(f"budgets[{i}].{where} names {rid!r}, which is not a recorded run")
            elif unit_of[rid] != b.get("cost_unit"):
                p.append(f"budgets[{i}].{where} names {rid!r}, a run in {unit_of[rid]}, not {b.get('cost_unit')}")
            if rid in seen_once:
                p.append(f"budgets[{i}]: {rid!r} is named in both {seen_once[rid]} and {where}; a run counts once")
            else:
                seen_once[rid] = where
        phases = b.get("phases") if "phases" in b and not _phase_problems(b, i) else None
        if phases:
            date_of = {r["id"]: r["date"] for r in runs if isinstance(r, dict) and isinstance(r.get("id"), str)
                       and isinstance(r.get("date"), str) and DATE_RE.match(r["date"])}
            # Every counted run falls in a phase: a run from before the first one belongs in excludes, with its why.
            excluded = {x for x in b["excludes"] if isinstance(x, str)} if isinstance(b.get("excludes"), list) else set()
            for r in runs:
                if not isinstance(r, dict) or not isinstance(r.get("id"), str):
                    continue
                if r.get("cost_unit") != b.get("cost_unit") or r["id"] in excluded:
                    continue
                if isinstance(r.get("date"), str) and DATE_RE.match(r["date"]) and phase_of(phases, r["date"]) is None:
                    p.append(f"budgets[{i}]: run {r.get('id')!r} ({r['date']}) comes before the first phase; "
                             "list it in excludes, with an excludes_why")
            # A reconciled group's measured total is one figure, so all its runs must fall in one phase.
            for j, g in enumerate(b.get("reconciled") or [] if isinstance(b.get("reconciled"), list) else []):
                if not (isinstance(g, dict) and isinstance(g.get("runs"), list)):
                    continue
                spans = {phase_of(phases, date_of.get(rid)) for rid in g["runs"]
                         if isinstance(rid, str) and isinstance(date_of.get(rid), str)}
                spans.discard(None)  # a run before the first phase is reported above
                if len(spans) > 1:
                    p.append(f"budgets[{i}].reconciled[{j}] spans phases {', '.join(sorted(str(s) for s in spans))}; "
                             "a measured group must fall in one phase")

    for where in _machine_paths(data):
        p.append(f"{where} holds a machine path; experiment.json is public, so keep paths relative or in rnd-data")
    return p


def _phase_problems(b: dict, i: int) -> list[str]:
    """What is wrong with a budget's phases: each names its cap, who set it and the date it starts; dates rise, and
    the budget's own cap is the current (last) phase's cap, so it always means the cap in force."""

    p = []
    phases = b["phases"]
    if not isinstance(phases, list) or not phases:
        return [f"budgets[{i}].phases must be a non-empty list"]
    names, last = set(), None
    for j, ph in enumerate(phases):
        where = f"budgets[{i}].phases[{j}]"
        if not isinstance(ph, dict):
            p.append(f"{where} must be an object")
            continue
        if not PHASE_KEYS <= set(ph) or set(ph) - PHASE_KEYS - {"closed"}:
            p.append(f"{where} needs {', '.join(sorted(PHASE_KEYS))}, and may add closed (spending is computed, never typed)")
        if not (isinstance(ph.get("name"), str) and ph["name"].strip()) or ph.get("name") in names:
            p.append(f"{where}.name must be a non-empty name of its own")
        else:
            names.add(ph["name"])
        if not _number(ph.get("cap")) or ph["cap"] <= 0:
            p.append(f"{where}.cap must be a positive number")
        if not (isinstance(ph.get("set_by"), str) and ph["set_by"].strip()):
            p.append(f"{where}.set_by must say who set the cap")
        if not (isinstance(ph.get("from"), str) and DATE_RE.match(ph["from"])):
            p.append(f"{where}.from must be YYYY-MM-DD, the first date the phase covers")
        elif last is not None and ph["from"] <= last:
            p.append(f"{where}.from must come after the phase before it")
        else:
            last = ph["from"]
        if "closed" in ph and not isinstance(ph["closed"], bool):
            p.append(f"{where}.closed must be true or false")
        elif j < len(phases) - 1 and ph.get("closed") is not True:
            p.append(f"{where} must be closed: only the last phase is open")
    return p


def _phase_in_force_problems(b: dict, i: int) -> list[str]:
    """The budget's own cap and set_by are the current (last) phase's, so they always mean the cap in force."""

    cur = b["phases"][-1] if isinstance(b.get("phases"), list) and b["phases"] else None
    if not isinstance(cur, dict):
        return []
    p = []
    if b.get("cap") != cur.get("cap"):
        p.append(f"budgets[{i}].cap must equal its current phase's cap ({cur.get('cap')})")
    if b.get("set_by") != cur.get("set_by"):
        p.append(f"budgets[{i}].set_by must equal its current phase's set_by")
    return p


def phase_of(phases: list[dict], date: str | None) -> str | None:
    """The phase a run dated `date` falls in: the last one starting on or before it; None if it predates them all."""

    found = None
    for ph in phases:
        if date is not None and ph["from"] <= date:
            found = ph["name"]
    return found


def registry_ids(root: Path) -> set[str] | None:
    p = root / "licences" / "registry.json"
    if not p.exists():
        return None
    try:
        return {e["id"] for e in json.loads(p.read_text(encoding="utf-8"))["entries"]}
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        return None


README_TEMPLATE = """# {title}

**Status: designing.** Template: {template_line}.

## The question

<What decision this experiment informs, in one or two sentences.>

## Design

<Fill in the template's sections, or link the design file.>

## Result

<Not run yet.>

Promoted: not yet.
"""


def new_experiment(root: Path, name: str, title: str, template: str | None) -> list[str]:
    """Scaffold experiments/<name>/ and return the paths written. Raises ValueError on a bad name or a clash."""
    if not NAME_RE.match(name):
        raise ValueError(f"name {name!r} is not valid; use lower-case letters, digits, '.', '_' and '-'")
    folder = root / "experiments" / name
    if folder.exists():
        raise ValueError(f"experiments/{name} already exists")
    if template is not None:
        handbook = root / "site" / "src" / "content" / "docs" / "handbook"
        if handbook.is_dir() and not (handbook / f"{template}.md").is_file():
            raise ValueError(f"no handbook page {template!r}; templates are the pages under site/src/content/docs/handbook/")
    record = {
        "schema": SCHEMA, "name": name, "status": "designing", "design": "README.md", "template": template,
        "budgets": [], "licences": [], "runs": [],
    }
    written = {
        "README.md": README_TEMPLATE.format(
            title=title, template_line=f"the handbook's `{template}` page" if template else "none chosen yet"),
        "experiment.json": json.dumps(record, indent=1) + "\n",
        "data/.gitkeep": "", "results/.gitkeep": "", "scripts/.gitkeep": "",
    }
    for rel, text in written.items():
        target = folder / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")
    (folder / "staging").mkdir()
    return [f"experiments/{name}/{rel}" for rel in written]
