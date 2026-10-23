"""Runs, budgets and where bytes live: the record side of the index.

- `from_outcome` maps a Publisher window record (outcome.json, in the shared vocabulary) onto a run.
- `record` writes that run into experiments/<name>/experiment.json, checked against the schema first.
- `index_rows` reads every experiment record, data-pack manifest and (when a checkout is present) rnd-data manifest
  into rows for rnd.db: experiments, runs, budgets, files, manifest_files and copies.

The text stays the source of truth: rnd.db is rebuilt from these files, never edited.
"""

import fnmatch
import hashlib
import json
import os
from pathlib import Path

from . import datapack, layout

# outcome.json field -> run field. Everything else in a run comes from the outcome's own fields of the same name,
# or from the recorder's options when the outcome doesn't carry it.
OUTCOME_MAP = {"window": "id", "card": "hardware", "spent": "cost", "basis": "cost_basis", "cap": "cap",
               "outcome": "outcome", "why": "why"}
SHARED = ("venue", "cost_unit", "date", "projected_cost", "raw_manifest_id")
RNDDATA_RUN_SCHEMA = "rnd-data-run/v1"
RNDDATA_PRIVATE_SCHEMA = "rnd-data-private/v1"


class RecordError(Exception):
    def __init__(self, code, message, hint=""):
        super().__init__(message)
        self.code, self.hint = code, hint


def _pins(value) -> dict:
    """An outcome's pins as a dict; anything else but empty is refused, not passed to dict() to raise TypeError."""
    if not value:
        return {}
    if not isinstance(value, dict):
        raise RecordError("OUTCOME_SHAPE", "outcome.json's pins must be an object")
    return dict(value)


def from_outcome(outcome: dict, **given) -> dict:
    """A run from an outcome.json.

    - **A `run` object** (written by the Publisher's `publisher outcome write`, in exactly the run fields) is read as
      written, with no mapping.
    - **An older file without one** is mapped field by field (OUTCOME_MAP); its `commit` becomes a pin.

    `given` supplies what the outcome lacks (venue, cost_unit, date, id, projected_cost, raw_manifest_id, pins). A
    field present in both must agree: nothing is silently overridden."""
    if not isinstance(outcome, dict):
        raise RecordError("OUTCOME_SHAPE", "outcome.json must be a JSON object")
    if "run" in outcome:
        if not isinstance(outcome["run"], dict):
            raise RecordError("OUTCOME_SHAPE", "outcome.json's run must be an object")
        run = {k: v for k, v in outcome["run"].items() if k != "pins"}
        pins = _pins(outcome["run"].get("pins"))
    else:
        run = {}
        for src, dst in OUTCOME_MAP.items():
            if src in outcome and outcome[src] is not None:
                run[dst] = outcome[src]
        for key in SHARED:
            if outcome.get(key) is not None:
                run[key] = outcome[key]
        pins = _pins(outcome.get("pins"))
        if outcome.get("commit"):
            pins.setdefault("commit", outcome["commit"])
    for key, value in given.items():
        if value is None:
            continue
        if key == "pins":
            for k, v in value.items():
                if k in pins and pins[k] != v:
                    raise RecordError("OUTCOME_CONFLICT", f"pin {k!r} is {pins[k]!r} in outcome.json, {v!r} given")
                pins[k] = v
            continue
        if run.get(key) is not None and run[key] != value:
            raise RecordError("OUTCOME_CONFLICT", f"{key} is {run[key]!r} in outcome.json but {value!r} was given",
                              "drop the option, or fix outcome.json with its owner")
        run[key] = value
    if isinstance(run.get("outcome"), str) and run["outcome"] in layout.ALIASES:
        run["outcome"] = layout.ALIASES[run["outcome"]]
    run["pins"] = pins
    run.setdefault("projected_cost", None)
    run.setdefault("raw_manifest_id", None)
    missing = [k for k in ("id", "venue", "hardware", "date", "cost", "cost_unit", "cost_basis", "outcome")
               if run.get(k) is None]
    if missing:
        raise RecordError("OUTCOME_MISSING", f"the run lacks {', '.join(missing)}",
                          "pass it as an option (--venue, --cost-unit, --date, ...) or have outcome.json carry it")
    return run


def record(root: Path, experiment: str, run: dict, replace: bool = False) -> str:
    """Add the run to experiments/<experiment>/experiment.json, or replace a run with the same id when `replace`.
    The whole record is validated before anything is written. Returns 'added' or 'replaced'."""
    path = root / "experiments" / experiment / "experiment.json"
    if not path.is_file():
        raise RecordError("NO_RECORD", f"experiments/{experiment}/experiment.json doesn't exist",
                          "`rnd new-experiment` makes one, or write the record for an older experiment first")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RecordError("RECORD_INVALID", f"{path.name} is not valid JSON ({exc})")
    runs = data.setdefault("runs", [])
    at = next((i for i, r in enumerate(runs) if isinstance(r, dict) and r.get("id") == run["id"]), None)
    if at is not None and not replace:
        raise RecordError("RUN_EXISTS", f"run {run['id']!r} is already recorded",
                          "pass --replace to overwrite it with this outcome")
    action = "replaced" if at is not None else "added"
    if at is None:
        runs.append(run)
    else:
        runs[at] = run
    problems = layout.validate_data(root, experiment, data, layout.registry_ids(root))
    if problems:
        raise RecordError("RECORD_INVALID", "; ".join(problems), "nothing was written")
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return action


# ------------------------------------------------------------------ index rows

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rnd_data_root(root: Path) -> Path:
    return Path(os.environ["RND_DATA"]) if os.environ.get("RND_DATA") else root.parent / "rnd-data"


def source_paths(root: Path) -> list[Path]:
    """Every file the record tables are built from, for the index's change detector."""
    paths = []
    exp_dir = root / "experiments"
    if exp_dir.is_dir():
        for d, dirs, names in os.walk(exp_dir):
            dirs[:] = [x for x in dirs if x not in ("staging", "__pycache__", ".hypothesis")]
            paths += [Path(d) / n for n in names]
    paths += datapack.manifests(root)
    paths += [m.parent / "hosted.json" for m in datapack.manifests(root) if (m.parent / "hosted.json").exists()]
    data = rnd_data_root(root)
    if data.is_dir():
        paths += sorted(data.glob("runs/*/manifest.json"))
    if (layout.private_root(root) / "manifest.json").exists():
        paths.append(layout.private_root(root) / "manifest.json")
    return paths


def _licence_for(path: str, licences: list) -> str | None:
    for lic in licences or []:
        if isinstance(lic, dict) and fnmatch.fnmatch(path, lic.get("applies_to", "")):
            return lic.get("licence")
    return None


def index_rows(root: Path) -> tuple[dict, list[tuple[str, str, str]]]:
    """Rows for the six record tables, and problems as (level, where, message). An invalid experiment record is an
    error (the build stops, as it does for a bad entry); an unreadable rnd-data manifest is a warning and skipped,
    since rnd-data is a separate, optional checkout."""
    rows = {k: [] for k in ("experiments", "runs", "budgets", "files", "manifest_files", "copies")}
    problems = []
    files = {}

    def add_file(sha, size, tier, licence, manifest_id, path, store, location):
        if sha not in files:
            files[sha] = (sha, size, tier, licence)
        rows["manifest_files"].append((manifest_id, path, sha))
        rows["copies"].append((sha, store, location))

    lib_files = layout.library_files(root)
    ids = layout.registry_ids(root)
    for exp in sorted({layout.experiment_of(p) for p in lib_files if layout.experiment_of(p)}):
        rec = root / "experiments" / exp / "experiment.json"
        if not rec.is_file():
            continue
        bad = layout.validate_record(root, exp, ids)
        if bad:
            problems += [("error", f"experiments/{exp}/experiment.json", m) for m in bad]
            continue
        data = json.loads(rec.read_text(encoding="utf-8"))
        rows["experiments"].append((exp, data["status"], data.get("template"), data["design"]))
        for b in data.get("budgets", []):
            rows["budgets"].append((exp, b["cost_unit"], b["cap"], b["set_by"], json.dumps(b.get("excludes", [])),
                                    b.get("excludes_why"), json.dumps(b.get("reconciled", [])),
                                    json.dumps(b.get("phases", []))))
        for r in data.get("runs", []):
            rows["runs"].append((exp, r["id"], r["venue"], r["hardware"], r["date"], r["cost"], r["cost_unit"],
                                 r["cost_basis"], r.get("cap"), r.get("projected_cost"), r["outcome"], r.get("why"),
                                 r.get("raw_manifest_id"), json.dumps(r.get("pins", {}), sort_keys=True)))

    # Data packs: each file's hash from the manifest; the hosted copy when the pack is uploaded.
    for mpath in datapack.manifests(root):
        try:
            m = datapack.load(mpath)
        except datapack.DatapackError:
            continue  # rnd check reports it
        name = m.get("name") or mpath.parent.name
        hosted = {}
        if (mpath.parent / "hosted.json").exists():
            try:
                hosted = json.loads((mpath.parent / "hosted.json").read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                hosted = {}
        for f in m.get("files", []):
            loc = f"{hosted['url']}@{hosted.get('revision', '')}/{f['path']}" if hosted.get("url") else None
            add_file(f["sha256"], f.get("bytes"), "T3", _licence_for(f["path"], m.get("licences")),
                     f"datapack:{name}", f["path"], "hf" if loc else "unhosted", loc or "")

    # rnd-data (public) and rnd-data-private, when their checkouts are present. Copies come only from each
    # manifest's own `copies`. A private file a public manifest lists has no hash there, so it's indexed from the
    # private manifest, which only a machine with that checkout can read.
    data_root, priv_root = rnd_data_root(root), layout.private_root(root)
    manifests = [(m, False) for m in sorted(data_root.glob("runs/*/manifest.json"))] if data_root.is_dir() else []
    if (priv_root / "manifest.json").exists():
        manifests.append((priv_root / "manifest.json", True))
    for mpath, private in manifests:
        where = ("rnd-data-private/manifest.json" if private
                 else f"rnd-data/{mpath.relative_to(data_root).as_posix()}")
        try:
            m = json.loads(mpath.read_text(encoding="utf-8"))
            if m.get("schema") != (RNDDATA_PRIVATE_SCHEMA if private else RNDDATA_RUN_SCHEMA):
                raise ValueError(f"schema must be {RNDDATA_PRIVATE_SCHEMA if private else RNDDATA_RUN_SCHEMA}")
            mid = "rnd-data-private" if private else f"rnd-data:{m['id']}"
            for f in m["files"]:
                sha = f.get("sha256")
                if not sha:
                    continue  # listed private, without its hash
                rows["manifest_files"].append((mid, f["path"], sha))
                if sha not in files:
                    files[sha] = (sha, f.get("bytes"), "T5" if private else f.get("tier", "T4"), f.get("licence"))
            rows["copies"] += [(c["sha256"], c["store"], c["location"]) for c in m.get("copies", [])]
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            problems.append(("warning", where, f"skipped: {type(exc).__name__}: {exc}"))
    # Every file under experiments/ that git would commit: one copy, in the repository. Indexed last, so a file a
    # manifest already names keeps that manifest's tier and licence.
    for p in lib_files:
        if layout.experiment_of(p) is None:
            continue
        full = root / p
        add_file(_sha256(full), full.stat().st_size, "git", None, "git", p, "git", p)
    rows["files"] = list(files.values())
    rows["copies"] = sorted(set(rows["copies"]))
    return rows, problems
