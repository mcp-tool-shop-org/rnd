"""Data packs: processed research data offered in bulk without living in the library's clone.

The bytes are hosted elsewhere (a Hugging Face dataset repo by default). The library keeps only
`datapacks/<name>/datapack.json`, a small manifest that says what the pack holds and lets anyone
check a downloaded copy byte for byte:

- every file's path, size and SHA-256;
- the licence and notice for each part (model outputs carry their model's terms);
- the models that produced the data, pinned by digest or revision;
- where it lives (repo and the exact revision that was uploaded);
- `manifest_sha256`, the hash of the manifest's canonical JSON without that field.

The integrity model comes from research-packs (a manifest, a receipt of hashes, a one-command
verify, a catalogue), without its research-os admission contract: these are experiment data,
not frozen claim packs.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import re
from datetime import date
from pathlib import Path

SCHEMA = "rnd-datapack/v1"
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
HOST_KINDS = ("huggingface", "github-release", "none")
DIR = "datapacks"
MANIFEST = "datapack.json"
# Written after an upload: {"revision", "uploaded", "manifest_sha256"}. Separate from the manifest so the
# copy uploaded and the copy in the library stay byte-identical.
HOSTED = "hosted.json"


class DatapackError(Exception):
    def __init__(self, code, message, hint=""):
        super().__init__(message)
        self.code, self.hint = code, hint


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def manifest_hash(manifest: dict) -> str:
    body = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    return hashlib.sha256(canonical(body)).hexdigest()


def collect(source: Path, include: list[str], exclude: list[str] | None = None) -> list[Path]:
    """Files under `source` matching any include glob (relative, POSIX) and no exclude glob."""
    exclude = exclude or []
    out = []
    for p in sorted(source.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(source).as_posix()
        if any(fnmatch.fnmatch(rel, g) for g in include) and not any(fnmatch.fnmatch(rel, g) for g in exclude):
            out.append(p)
    return out


def build(source: Path, *, name: str, title: str, description: str, include: list[str],
          exclude: list[str] | None = None, licences: list[dict], generators: list[dict],
          host: dict, origin: dict, version: str = "1", today: str | None = None) -> dict:
    """A manifest for the matching files under `source`. Raises DatapackError on bad input."""
    if not NAME_RE.match(name):
        raise DatapackError("BAD_NAME", f"pack name {name!r} must be lowercase letters, digits and hyphens",
                            "e.g. natural-errors")
    if not source.is_dir():
        raise DatapackError("NO_SOURCE", f"{source} is not a directory")
    files = collect(source, include, exclude)
    if not files:
        raise DatapackError("NO_FILES", f"no files under {source} match {include}", "check the --include globs")
    entries = [{"path": p.relative_to(source).as_posix(), "bytes": p.stat().st_size, "sha256": sha256_file(p)}
               for p in files]
    manifest = {
        "schema": SCHEMA,
        "name": name,
        "version": version,
        "title": title,
        "description": description,
        "created": today or date.today().isoformat(),
        "origin": origin,
        "licences": licences,
        "generators": generators,
        "host": host,
        "files": entries,
        "totals": {"files": len(entries), "bytes": sum(e["bytes"] for e in entries)},
    }
    problems = validate(manifest, hashed=False)
    if problems:
        raise DatapackError("INVALID", "; ".join(problems))
    manifest["manifest_sha256"] = manifest_hash(manifest)
    return manifest


def validate(m: dict, hashed: bool = True) -> list[str]:
    """Problems with a manifest's shape (not its files). Empty when it is well formed."""
    out = []
    if not isinstance(m, dict):
        return ["manifest must be a JSON object"]
    if m.get("schema") != SCHEMA:
        out.append(f"schema must be {SCHEMA}")
    if not isinstance(m.get("name"), str) or not NAME_RE.match(m["name"]):
        out.append("name must be lowercase letters, digits and hyphens")
    for key in ("title", "description", "version", "created"):
        if not isinstance(m.get(key), str) or not m[key].strip():
            out.append(f"{key} is required")
    lic = m.get("licences")
    if not isinstance(lic, list) or not lic:
        out.append("licences must list at least one entry")
    else:
        for i, l in enumerate(lic):
            if not isinstance(l, dict) or not all(isinstance(l.get(k), str) and l[k].strip()
                                                  for k in ("applies_to", "licence")):
                out.append(f"licences[{i}] needs applies_to and licence")
    gens = m.get("generators")
    if not isinstance(gens, list):
        out.append("generators must be a list (empty only for human-made data)")
    else:
        for i, g in enumerate(gens):
            if not isinstance(g, dict) or not all(isinstance(g.get(k), str) and g[k].strip()
                                                  for k in ("model", "pin", "role")):
                out.append(f"generators[{i}] needs model, pin and role")
    host = m.get("host")
    if not isinstance(host, dict) or host.get("kind") not in HOST_KINDS:
        out.append(f"host.kind must be one of {', '.join(HOST_KINDS)}")
    elif host["kind"] != "none" and not (isinstance(host.get("repo"), str) and host["repo"].strip()):
        out.append("host.repo is required unless host.kind is none")
    files = m.get("files")
    if not isinstance(files, list) or not files:
        out.append("files must list at least one file")
    else:
        seen = set()
        for i, f in enumerate(files):
            if not isinstance(f, dict) or not isinstance(f.get("path"), str) \
                    or not re.fullmatch(r"[0-9a-f]{64}", str(f.get("sha256", ""))) \
                    or not isinstance(f.get("bytes"), int) or f["bytes"] < 0:
                out.append(f"files[{i}] needs path, bytes and a sha256")
                continue
            if f["path"].startswith(("/", "../")) or "/../" in f["path"]:
                out.append(f"files[{i}] path must stay inside the pack: {f['path']}")
            if f["path"] in seen:
                out.append(f"files[{i}] repeats {f['path']}")
            seen.add(f["path"])
        for i, l in enumerate(lic if isinstance(lic, list) else []):
            if isinstance(l, dict) and isinstance(l.get("applies_to"), str) \
                    and not any(fnmatch.fnmatch(f.get("path", ""), l["applies_to"]) for f in files if isinstance(f, dict)):
                out.append(f"licences[{i}] applies_to {l['applies_to']!r} matches no file")
        unlicensed = [f["path"] for f in files if isinstance(f, dict) and isinstance(f.get("path"), str)
                      and not any(isinstance(l, dict) and fnmatch.fnmatch(f["path"], str(l.get("applies_to", "")))
                                  for l in (lic if isinstance(lic, list) else []))]
        if unlicensed:
            out.append(f"no licence covers: {', '.join(unlicensed[:5])}")
        tot = m.get("totals", {})
        if tot.get("files") != len(files) or tot.get("bytes") != sum(f.get("bytes", 0) for f in files if isinstance(f, dict)):
            out.append("totals do not match the file list")
    if hashed:
        if m.get("manifest_sha256") != manifest_hash(m):
            out.append("manifest_sha256 does not match the manifest (edited after build?)")
    return out


def verify(manifest: dict, copy: Path) -> dict:
    """Recompute every file under `copy` against the manifest. Returns a report; `ok` is the verdict."""
    problems = validate(manifest)
    missing, changed, ok_files = [], [], 0
    for f in manifest.get("files", []):
        p = copy / f["path"]
        if not p.is_file():
            missing.append(f["path"])
        elif p.stat().st_size != f["bytes"] or sha256_file(p) != f["sha256"]:
            changed.append(f["path"])
        else:
            ok_files += 1
    return {"ok": not (problems or missing or changed), "manifest_problems": problems,
            "files_ok": ok_files, "missing": missing, "changed": changed}


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DatapackError("UNREADABLE", f"cannot read {path}: {exc}")


def write(manifest: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / MANIFEST
    path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return path


def manifests(root: Path) -> list[Path]:
    d = root / DIR
    return sorted(d.glob(f"*/{MANIFEST}")) if d.is_dir() else []


def check_all(root: Path) -> list[tuple[str, str]]:
    """(pack, problem) for every manifest in datapacks/ (shape and hash only; no download)."""
    out = []
    for path in manifests(root):
        try:
            m = load(path)
        except DatapackError as exc:
            out.append((path.parent.name, str(exc)))
            continue
        for p in validate(m):
            out.append((path.parent.name, p))
        if isinstance(m, dict) and m.get("name") != path.parent.name:
            out.append((path.parent.name, f"name {m.get('name')!r} differs from its folder"))
        hosted = path.parent / HOSTED
        if hosted.is_file() and isinstance(m, dict):
            try:
                h = load(hosted)
            except DatapackError as exc:
                out.append((path.parent.name, str(exc)))
                continue
            if h.get("manifest_sha256") != m.get("manifest_sha256"):
                out.append((path.parent.name, "hosted.json records a different manifest: rebuild and re-upload, or update it"))
    return out
