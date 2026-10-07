"""Federated, read-only search over the studio's readouts knowledge bases.

readouts (a separate monorepo) holds study-swarm-built, verified SQLite knowledge
bases: models, engines, training, sprites, vocology, Godot, Blender, Rust and more.
Its root index.json lists each KB with its database and FTS5 table, so one search
can fan out across all of them without copying anything into this repo.
"""

import json
import os
import re
import sqlite3
from pathlib import Path

DEFAULT_ROOT = "E:/AI/readouts"


class ReadoutsError(RuntimeError):
    def __init__(self, code, message, hint=""):
        super().__init__(message)
        self.code, self.hint = code, hint


def root_dir(override=None):
    return Path(override or os.environ.get("RND_READOUTS") or DEFAULT_ROOT)


def knowledge_bases(root):
    index = Path(root) / "index.json"
    if not index.is_file():
        raise ReadoutsError("READOUTS_MISSING", f"no readouts index at {index.as_posix()}",
                            "clone readouts there, or set RND_READOUTS / --root to its checkout")
    try:
        return json.loads(index.read_text(encoding="utf-8"))["knowledge_bases"]
    except (ValueError, KeyError) as exc:
        raise ReadoutsError("READOUTS_INDEX_INVALID", f"{index.as_posix()} is not a readouts index: {exc}",
                            "regenerate it with readouts' shared/gen_root_index.py")


def prefix_query(text, any_word=False):
    """Quote each word and match it as a prefix, so 'listener' also finds 'listeners'.
    Words are ANDed by default; any_word=True ORs them for exploration."""
    words = re.findall(r"[\w.+#]+", text, flags=re.UNICODE)
    return (" OR " if any_word else " ").join('"' + w.replace('"', "") + '"*' for w in words)


def search(root, text, limit=5, kb=None, any_word=False):
    """Return (results, problems). Results are grouped per KB in best-match order."""
    query = prefix_query(text, any_word)
    if not query:
        return [], []
    results, problems = [], []
    for entry in knowledge_bases(root):
        name = entry.get("name") or entry.get("kb")
        if kb and name != kb:
            continue
        fts, db_rel = entry.get("fts"), entry.get("db")
        if not fts or not re.fullmatch(r"\w+", fts) or not db_rel:
            problems.append(f"{name}: index entry has no usable fts/db")
            continue
        db = Path(root) / db_rel
        if not db.is_file():
            problems.append(f"{name}: database missing at {db_rel}")
            continue
        try:
            con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
            rows = con.execute(
                f"SELECT slug, name, snippet({fts}, -1, '[', ']', ' … ', 14), bm25({fts}) "
                f"FROM {fts} WHERE {fts} MATCH ? ORDER BY bm25({fts}) LIMIT ?",
                (query, limit)).fetchall()
            con.close()
        except sqlite3.Error as exc:
            problems.append(f"{name}: {exc}")
            continue
        for slug, title, snip, rank in rows:
            results.append({"kb": name, "noun": entry.get("noun", ""), "slug": slug, "name": title,
                            "snip": " ".join((snip or "").split()), "rank": rank, "db": db_rel})
    best = {}
    for r in results:
        best[r["kb"]] = min(best.get(r["kb"], 0.0), r["rank"])
    results.sort(key=lambda r: (best[r["kb"]], r["kb"], r["rank"]))
    return results, problems
