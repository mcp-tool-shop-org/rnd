"""Freeze the corpus with offrig's own chunker (design v3, sections 3 and 4).

1. `git archive` each source at a pinned commit into BENCH/corpus/<repo>/ (this experiment's folder excluded).
2. `offrig index` the corpus into BENCH/index with an embedder that doesn't answer: offrig stores every chunk and its
   FTS row first, then refuses at the embed step, so no model is touched.
3. Export the chunks to BENCH/chunks.jsonl (private: it carries text) and write results/corpus-manifest.json
   (public: commits, counts, hashes; no text).

Run: E:/AI/envs/embedgemma/Scripts/python.exe -I build_corpus.py
"""

from __future__ import annotations

import io
import json
import os
import shutil
import sqlite3
import subprocess
import tarfile
from collections import Counter

from common import BENCH, CHUNKS, DB, PROJECT, RESULTS, sha256_file, write_jsonl

# The corpus lives inside the offrig project and is indexed by a relative path, so chunk headers read
# `[corpus/<repo>/<path> · kind · title]` the way offrig writes them in production (project-relative).
CORPUS = PROJECT / "corpus"

SOURCES = [
    # (name, repo dir, ref, include prefixes, exclude prefixes, suffixes)
    ("rnd", r"E:\AI\Research and Development", "origin/main",
     ["entries/", "instruments/", "experiments/"], ["experiments/embeddinggemma-2/"], None),
    ("readouts", r"E:\AI\readouts", "origin/main", None, [], (".md",)),
    ("role-set", r"E:\AI\role-set", "origin/main", ["src/"], [], (".py",)),
    ("offrig", r"E:\AI\offrig", "origin/main", ["crates/"], [], (".rs",)),
]
OFFRIG = shutil.which("offrig")
DEAD_EMBED = "http://127.0.0.1:11499"


def git(repo: str, *args: str) -> str:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, check=True, text=True).stdout.strip()


def keep(name: str, path: str, include, exclude, suffixes) -> bool:
    if name == "readouts":
        top = path.split("/", 1)[0]
        return top.endswith("-knowledge") and path.endswith(".md")
    if name == "rnd" and path.startswith("experiments/") and not path.endswith(".md"):
        return False
    if name == "offrig" and "/src/" not in path:
        return False
    if include and not any(path.startswith(p) for p in include):
        return False
    if any(path.startswith(p) for p in exclude):
        return False
    return suffixes is None or path.endswith(suffixes)


def archive(name: str, repo: str, ref: str, include, exclude, suffixes) -> dict:
    commit = git(repo, "rev-parse", ref)
    blob = subprocess.run(["git", "-C", repo, "archive", "--format=tar", commit], capture_output=True, check=True).stdout
    dest = CORPUS / name
    files = 0
    with tarfile.open(fileobj=io.BytesIO(blob)) as tar:
        for member in tar.getmembers():
            if member.isfile() and keep(name, member.name, include, exclude, suffixes):
                target = dest / member.name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(tar.extractfile(member).read())
                files += 1
    return {"name": name, "ref": ref, "commit": commit, "files": files}


def main() -> None:
    if PROJECT.exists():
        raise SystemExit(f"REFUSED: {PROJECT} exists; the corpus is frozen once. Move it aside to rebuild.")
    PROJECT.mkdir(parents=True)
    pins = [archive(*s) for s in SOURCES]
    subprocess.run(["git", "init", "-q", str(PROJECT)], check=True)
    env = dict(os.environ, OFFRIG_EMBED_URL=DEAD_EMBED)
    version = subprocess.run([OFFRIG, "--version"], capture_output=True, text=True, check=True).stdout.strip()
    run = subprocess.run([OFFRIG, "index", "corpus", "--project", str(PROJECT)], capture_output=True, text=True, env=env, cwd=PROJECT)
    if "no embedding server answers" not in (run.stdout + run.stderr):
        raise SystemExit(f"REFUSED: offrig index did not stop at the embed step as expected:\n{run.stdout}\n{run.stderr}")
    con = sqlite3.connect(DB)
    if con.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0] != 0:
        raise SystemExit("REFUSED: the index holds vectors; it must hold none")
    rows = [
        {"id": i, "source": s, "kind": k, "title": t, "ordinal": o, "body": b}
        for i, s, k, t, o, b in con.execute("SELECT id, source, kind, title, ordinal, body FROM chunks ORDER BY id")
    ]
    write_jsonl(CHUNKS, rows)
    root = lambda src: src.replace("\\", "/").split("corpus/", 1)[-1].split("/", 1)[0]
    manifest = {
        "offrig": version,
        "offrig_exe_sha256": sha256_file(__import__("pathlib").Path(OFFRIG)),
        "pins": pins,
        "chunks": len(rows),
        "by_kind": dict(Counter(r["kind"] for r in rows)),
        "by_source": dict(Counter(root(r["source"]) for r in rows)),
        "max_body_chars": max(len(r["body"]) for r in rows),
        "chunks_sha256": sha256_file(CHUNKS),
        "db_sha256": sha256_file(DB),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "corpus-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "pins"}, indent=1))
    for p in pins:
        print(p)


if __name__ == "__main__":
    main()
