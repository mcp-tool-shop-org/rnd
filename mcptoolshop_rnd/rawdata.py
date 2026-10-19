"""rnd-data: ingest raw run outputs into the public store and its private companion, and verify every copy.

The stores (scale plan P3; the Director made rnd-data public on 2026-10-19, open research by default):
- **rnd-data (public git)** holds each run's manifest (`runs/<id>/manifest.json`, rnd-data-run/v1) and the run's small
  public files (at most SMALL_LIMIT bytes) under `runs/<id>/files/`.
- **rnd-data-private (private git)** holds only the named exceptions, under `runs/<id>/` (a public run's private
  files) and `private/<source>/` (private sources), listed in `manifest.json` (rnd-data-private/v1).
- **The blob store** holds every larger file once, by content, at `<root>/blobs/<sha[:2]>/<sha>`. A machine finds
  each store's root through the public checkout's `store.local.json` (gitignored) or `$RND_DATA_STORE_<NAME>`, so no
  machine path is ever committed.

**What a public manifest says about a private file:**
- **Private only for identity** (the studio's identity scan flags it): listed by path and size with its reason, but
  no hash, so the run stays complete.
- **Private for its content** (sealed, blind, item text, unapproved, private project): left out, and counted by
  reason in `private_files`.

No hash of a private file is ever published: a short label file's hash could be matched by guessing (Argon, round 3).

Ingest never deletes or changes its source. From a source on the same volume as the blob store, a blob is
hard-linked: the same bytes under a second name, which is not a second copy and is never counted as one.
"""

import fnmatch
import hashlib
import json
import os
import shutil
from datetime import date
from pathlib import Path

from . import layout

SMALL_LIMIT = 256 * 1024
RUN_SCHEMA = "rnd-data-run/v1"
PRIVATE_SCHEMA = "rnd-data-private/v1"
SEP = "--"
REASONS = ("sealed", "blind", "item-text", "unapproved", "private-project", "identity")
LISTED_REASONS = ("identity",)  # listed (no hash) in a public manifest; every other reason is counted only
# Text files that take the private tag as a first-line comment. Data files (JSON, JSONL, CSV, tars) are never tagged:
# the tag would change their bytes or how they parse, and many are pinned by hash.
TAG_COMMENTS = {".md": "<!-- {tag} -->", ".txt": "# {tag}", ".py": "# {tag}", ".sh": "# {tag}"}


class RawError(Exception):
    def __init__(self, code, message, hint=""):
        super().__init__(message)
        self.code, self.hint = code, hint


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def store_root(public: Path, name: str = "d") -> Path:
    env = os.environ.get(f"RND_DATA_STORE_{name.upper()}")
    if env:
        return Path(env)
    local = public / "store.local.json"
    if local.exists():
        try:
            roots = json.loads(local.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RawError("STORE_LOCAL", f"store.local.json is not valid JSON ({exc})")
        if roots.get(name):
            return Path(roots[name])
    raise RawError("NO_STORE_ROOT", f"no root for store {name!r} on this machine",
                   f"set $RND_DATA_STORE_{name.upper()}, or write {{\"{name}\": \"<root>\"}} to rnd-data's store.local.json")


def blob_rel(sha: str) -> str:
    return f"blobs/{sha[:2]}/{sha}"


def run_id(rel_dir: str) -> str:
    return rel_dir.strip("/").replace("/", SEP)


def group_of(rel: str, run_dirs: set[str]) -> str:
    """The run a file belongs to: its nearest ancestor folder holding an outcome.json, else its window folder (two
    levels, for Colab), else its top folder; '.' for a file at the source's top."""
    parts = rel.split("/")
    for i in range(len(parts) - 1, 0, -1):
        d = "/".join(parts[:i])
        if d in run_dirs:
            return d
    if len(parts) > 2 and parts[0] == "colab":
        return "/".join(parts[:2])
    return parts[0] if len(parts) > 1 else "."


def plan_runs(source: Path, exclude: tuple = ()) -> dict[str, list[str]]:
    files = sorted(p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file())
    files = [f for f in files if not any(f == x or f.startswith(x.rstrip("/") + "/") for x in exclude)]
    run_dirs = {f.rsplit("/", 1)[0] for f in files if f.endswith("/outcome.json")}
    groups = {}
    for f in files:
        groups.setdefault(group_of(f, run_dirs), []).append(f)
    return groups


def run_dirs_of(groups: dict[str, list[str]]) -> set[str]:
    """The groups that are runs (their folder holds an outcome.json); every other group is a collection."""
    return {g for g, files in groups.items()
            if any(f == f"{g}/outcome.json" or (g == "." and f == "outcome.json") for f in files)}


# ------------------------------------------------------------------ rules (what may be public)

RULES_SCHEMA = "rnd-data-rules/v1"


def load_rules(path: Path) -> dict:
    """A rules file: deny by default for content (see docs/raw-data-rules/)."""
    try:
        rules = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RawError("RULES_UNREADABLE", f"{path}: {exc}")
    if rules.get("schema") != RULES_SCHEMA:
        raise RawError("RULES_SCHEMA", f"{path}: schema must be {RULES_SCHEMA!r}")
    for r in rules.get("private", []) + rules.get("content_markers", []) + [{"reason": rules.get("default")}]:
        if r.get("reason") not in REASONS:
            raise RawError("RULES_REASON", f"{path}: {r.get('reason')!r} is not one of {', '.join(REASONS)}")
    for r in rules.get("private", []) + rules.get("public", []) + rules.get("licences", []):
        if not (r.get("name") or r.get("path")):
            raise RawError("RULES_PATTERN", f"{path}: every rule needs a 'name' or 'path' pattern")
    return rules


def _rule_matches(rule: dict, rel: str) -> bool:
    name = rel.rsplit("/", 1)[-1]
    if rule.get("name") and not fnmatch.fnmatchcase(name, rule["name"]):
        return False
    if rule.get("path") and not fnmatch.fnmatchcase(rel, rule["path"]):
        return False
    return True


def _has_marker(path: Path, marker: bytes) -> bool:
    tail = b""
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8 << 20), b""):
            if marker in tail + chunk:
                return True
            tail = chunk[-(len(marker) - 1):] if len(marker) > 1 else b""
    return False


def rules_classifier(rules: dict, source: Path, reasons: dict):
    """(classify, licence_for) for ingest_tree. classify(rel) -> None (public) or a reason, in the rules' order:
    the reasons file (identity), a private-looking name, the private rules, the content markers, the public rules,
    then the default."""
    keys = sorted(reasons, key=len, reverse=True)

    def classify(rel):
        for k in keys:
            if rel == k or (k.endswith("/") and rel.startswith(k)):
                return reasons[k]
        if layout.private_name(rel):
            return "sealed" if "sealed" in rel.lower() else "blind"
        for r in rules.get("private", []):
            if _rule_matches(r, rel):
                return r["reason"]
        for m in rules.get("content_markers", []):
            if _has_marker(source / rel, m["marker"].encode()):
                return m["reason"]
        for r in rules.get("public", []):
            if _rule_matches(r, rel):
                return None
        return rules["default"]

    def licence_for(rel):
        for r in rules.get("licences", []):
            if _rule_matches(r, rel):
                return r["licence"]
        return None
    return classify, licence_for


def _place_blob(src: Path, sha: str, root: Path, link: bool) -> str:
    target = root / blob_rel(sha)
    if target.exists():
        if target.stat().st_size != src.stat().st_size:
            raise RawError("BLOB_CLASH", f"{blob_rel(sha)} exists with a different size", "the blob store needs repair")
        return "present"
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    if tmp.exists():
        tmp.unlink()
    if link:
        try:
            os.link(src, tmp)
        except OSError as exc:
            raise RawError("NO_HARDLINK", f"can't hard-link {src.name} into the blob store ({exc})",
                           "a hard link needs the source and the store on one NTFS volume; pass --copy to copy instead")
        os.replace(tmp, target)
        return "linked"
    shutil.copy2(src, tmp)
    if sha256_file(tmp) != sha:
        tmp.unlink()
        raise RawError("COPY_HASH", f"the copy of {src.name} doesn't hash to {sha[:12]}")
    os.replace(tmp, target)
    return "copied"


def _load_private(private: Path) -> dict:
    p = private / "manifest.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"schema": PRIVATE_SCHEMA, "files": [], "copies": []}


def _save_private(private: Path, m: dict) -> None:
    m["files"].sort(key=lambda f: f["path"])
    m["copies"] = sorted(m["copies"], key=lambda c: (c["location"], c["store"]))
    (private / "manifest.json").write_text(json.dumps(m, indent=1, ensure_ascii=False) + "\n", encoding="utf-8",
                                           newline="\n")


def _copy_checked(src: Path, dst: Path, sha: str) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    if sha256_file(dst) != sha:
        raise RawError("COPY_HASH", f"{dst.name} doesn't hash to its source")


def ingest_tree(source: Path, public: Path, private: Path, prefix: str, classify, *, exclude: tuple = (),
                link: bool = True, dry_run: bool = False, commit: str | None = None, update: bool = False,
                licence_for=None) -> dict:
    """Ingest every file under `source` as runs `<prefix>--<group>`. `classify(rel)` returns None for a public file
    or a reason from REASONS. Idempotent: a run whose manifest exists and matches is left alone; one that differs is
    refused, since its source changed after it was ingested, unless `update` replaces it."""
    for d, what in ((public, "store.json"), (private, "README.md")):
        if not (d / what).is_file():
            raise RawError("NOT_A_STORE", f"{d} is not an rnd-data checkout (no {what})")
    root = None if dry_run else store_root(public, "d")
    pm = _load_private(private)
    known_private = {f["path"] for f in pm["files"]}
    stats = {"runs": 0, "unchanged": 0, "public": 0, "private": 0, "blobs_linked": 0, "blobs_copied": 0,
             "blobs_present": 0, "bytes": 0}
    groups = plan_runs(source, exclude)
    is_run = run_dirs_of(groups)
    licence_for = licence_for or (lambda rel: None)
    for group, files in sorted(groups.items()):
        rid = run_id(f"{prefix}/{group}" if group != "." else prefix)
        entries, copies, counted, private_rows = [], [], {}, []
        for rel in files:
            src = source / rel
            sha, size = sha256_file(src), src.stat().st_size
            inner = rel if group == "." else rel[len(group) + 1:]
            reason = classify(rel)
            if reason is not None and reason not in REASONS:
                raise RawError("BAD_REASON", f"{rel}: {reason!r} is not one of {', '.join(REASONS)}")
            if reason is None:
                entries.append({"path": inner, "sha256": sha, "bytes": size, "tier": "T4",
                                "licence": licence_for(rel), "visibility": "public"})
                store_, loc = ("rnd-data", f"runs/{rid}/files/{inner}") if size <= SMALL_LIMIT else ("d", blob_rel(sha))
                copies.append({"sha256": sha, "store": store_, "location": loc})
            else:
                if reason in LISTED_REASONS:
                    entries.append({"path": inner, "sha256": None, "bytes": size, "tier": "T4", "licence": None,
                                    "visibility": "private", "private_why": reason})
                else:
                    counted[reason] = counted.get(reason, 0) + 1
                ppath = f"runs/{rid}/{inner}"
                store_, loc = ("rnd-data-private", ppath) if size <= SMALL_LIMIT else ("d", blob_rel(sha))
                private_rows.append(({"path": ppath, "sha256": sha, "bytes": size, "reason": reason, "tagged": False},
                                     {"sha256": sha, "store": store_, "location": loc}, src, size))
        manifest = {"schema": RUN_SCHEMA, "id": rid, "kind": "run" if group in is_run else "collection",
                    "source": f"{prefix}/{group}" if group != "." else prefix,
                    "models": [], "licence_note": "generating models not yet recorded for this run",
                    "files": entries, "copies": copies, "private_files": dict(sorted(counted.items()))}
        mpath = public / "runs" / rid / "manifest.json"
        updating = False
        if mpath.exists():
            old = json.loads(mpath.read_text(encoding="utf-8"))
            if all(old.get(k) == manifest[k] for k in ("kind", "files", "copies", "private_files")):
                stats["unchanged"] += 1
                continue
            if not update:
                raise RawError("RUN_CHANGED", f"run {rid} was ingested before, and its source has changed since",
                               "compare the source with the manifest; pass --update to replace it (git keeps the old)")
            updating = True
        stats["updated" if updating else "runs"] = stats.get("updated" if updating else "runs", 0) + 1
        stats["public"] += sum(1 for e in entries if e["visibility"] == "public")
        stats["private"] += len(private_rows)
        stats["bytes"] += sum(r[3] for r in private_rows) + sum(e["bytes"] for e in entries if e["visibility"] == "public")
        if dry_run:
            continue
        if updating:
            # The run's previous small files and private entries give way to the new ones; git keeps the old. Blobs are
            # content-addressed and shared, so they're never removed here.
            keep = {c["location"] for c in copies if c["store"] == "rnd-data"}
            files_dir = public / "runs" / rid / "files"
            if files_dir.is_dir():
                for p in sorted(files_dir.rglob("*"), reverse=True):
                    rel_loc = p.relative_to(public).as_posix()
                    if p.is_file() and rel_loc not in keep:
                        p.unlink()
            prefix_ = f"runs/{rid}/"
            for f in [f for f in pm["files"] if f["path"].startswith(prefix_)]:
                pm["files"].remove(f)
                known_private.discard(f["path"])
                if (private / f["path"]).is_file():
                    (private / f["path"]).unlink()
            pm["copies"] = [c for c in pm["copies"] if not c["location"].startswith(prefix_)]
        for e, c in zip([e for e in entries if e["visibility"] == "public"], copies):
            src = source / (e["path"] if group == "." else f"{group}/{e['path']}")
            if c["store"] == "rnd-data":
                _copy_checked(src, public / c["location"], e["sha256"])
            else:
                stats["blobs_" + _place_blob(src, e["sha256"], root, link)] += 1
        for entry, copy, src, size in private_rows:
            if entry["path"] in known_private:
                continue
            if copy["store"] == "rnd-data-private":
                _copy_checked(src, private / copy["location"], entry["sha256"])
            else:
                stats["blobs_" + _place_blob(src, entry["sha256"], root, link)] += 1
            pm["files"].append(entry)
            pm["copies"].append(copy)
            known_private.add(entry["path"])
        manifest["ingested"] = date.today().isoformat()
        if commit:
            manifest["rnd_commit"] = commit
        mpath.parent.mkdir(parents=True, exist_ok=True)
        mpath.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        _save_private(private, pm)
    return stats


def ingest_private(source: Path, private: Path, name: str, classify, *, pinned_text: str = "",
                   exclude: tuple = (), dry_run: bool = False) -> dict:
    """Copy the files under `source` that `classify(rel)` gives a reason into `private/<name>/` and list them.
    A file it returns None for is public, and is skipped here (it belongs in a public store).

    A note-type text file (TAG_COMMENTS) whose hash isn't pinned in `pinned_text` gets the private tag as its first
    line, and its entry keeps the original's hash as source_sha256. Data files, and any file whose hash is pinned,
    are stored byte-exact."""
    if not (private / "README.md").is_file():
        raise RawError("NOT_A_STORE", f"{private} is not an rnd-data-private checkout (no README.md)")
    pm = _load_private(private)
    known = {f["path"] for f in pm["files"]}
    stats = {"private": 0, "public_skipped": 0, "tagged": 0, "pinned_untagged": 0, "data_untagged": 0, "excluded": 0}
    for src in sorted(p for p in source.rglob("*") if p.is_file()):
        rel = src.relative_to(source).as_posix()
        if any(rel == x or rel.startswith(x.rstrip("/") + "/") for x in exclude):
            stats["excluded"] += 1
            continue
        reason = classify(rel)
        if reason is None:
            stats["public_skipped"] += 1
            continue
        if reason not in REASONS:
            raise RawError("BAD_REASON", f"{rel}: {reason!r} is not one of {', '.join(REASONS)}")
        path = f"private/{name}/{rel}"
        if path in known:
            raise RawError("PRIVATE_EXISTS", f"{path} is already in the store", "nothing more was written")
        raw = src.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        form = TAG_COMMENTS.get(src.suffix.lower())
        entry = {"path": path, "sha256": sha, "bytes": len(raw), "reason": reason}
        if form and sha[:8] not in pinned_text and layout.PRIVATE_TAG.encode() not in raw:
            stored = (form.format(tag=layout.PRIVATE_TAG) + "\n").encode() + raw
            entry.update(sha256=hashlib.sha256(stored).hexdigest(), bytes=len(stored), source_sha256=sha, tagged=True)
            stats["tagged"] += 1
        else:
            stored = raw
            entry["tagged"] = False
            entry["untagged_why"] = ("its hash is pinned elsewhere, so its bytes must not change" if form
                                     else "a data file: the tag would change its bytes or how it parses")
            stats["pinned_untagged" if form else "data_untagged"] += 1
        stats["private"] += 1
        pm["files"].append(entry)
        pm["copies"].append({"sha256": entry["sha256"], "store": "rnd-data-private", "location": path})
        known.add(path)
        if not dry_run:
            dst = private / path
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(stored)
    if not dry_run:
        _save_private(private, pm)
    return stats


def verify(public: Path, private: Path | None = None, *, deep: bool = False, run: str | None = None) -> list[str]:
    """Problems with the stores. Every git copy is re-hashed; a blob is checked by size, and re-hashed with `deep`."""
    problems, roots = [], {}
    targets = []
    manifests = sorted((public / "runs").glob("*/manifest.json")) if (public / "runs").is_dir() else []
    if run:
        manifests = [m for m in manifests if m.parent.name == run]
        if not manifests:
            return [f"no run {run!r} in this store"]
    targets += [(m, public) for m in manifests]
    if private is not None and not run and (private / "manifest.json").exists():
        targets.append((private / "manifest.json", private))
    for mpath, base in targets:
        try:
            m = json.loads(mpath.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"{mpath.name}: not valid JSON ({exc})")
            continue
        sizes = {f["sha256"]: f["bytes"] for f in m.get("files", []) if f.get("sha256")}
        for e in m.get("files", []):
            if e.get("visibility") == "private" and e.get("sha256"):
                problems.append(f"{m.get('id')}: {e['path']} is private but its hash is published")
        for c in m.get("copies", []):
            where = f"{m.get('id', 'private')}: {c['location']}"
            if c["store"] in ("rnd-data", "rnd-data-private"):
                p = (public if c["store"] == "rnd-data" else (private or base)) / c["location"]
                if not p.is_file():
                    problems.append(f"{where}: missing")
                elif sha256_file(p) != c["sha256"]:
                    problems.append(f"{where}: hash differs")
                continue
            try:
                roots.setdefault(c["store"], store_root(public, c["store"]))
            except RawError as exc:
                return problems + [str(exc)]
            p = roots[c["store"]] / c["location"]
            if not p.is_file():
                problems.append(f"{where}: missing from store {c['store']}")
            elif p.stat().st_size != sizes.get(c["sha256"], p.stat().st_size):
                problems.append(f"{where}: size differs")
            elif deep and sha256_file(p) != c["sha256"]:
                problems.append(f"{where}: hash differs")
    return problems
