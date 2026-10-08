"""The SQLite index (rnd.db). Always rebuildable from the files; never edited."""

import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from . import catalog, model

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE entries (
  id TEXT PRIMARY KEY, path TEXT, title TEXT, date TEXT, kind TEXT,
  relevance TEXT, status TEXT, fields TEXT, tags TEXT, body TEXT,
  relevance_note TEXT, extra TEXT);
CREATE TABLE entry_fields (entry_id TEXT, field TEXT);
CREATE TABLE entry_tags (entry_id TEXT, tag TEXT);
CREATE TABLE sources (entry_id TEXT, ord INTEGER, tier TEXT, url TEXT, label TEXT);
CREATE TABLE claims (entry_id TEXT, ord INTEGER, confidence TEXT, text TEXT, via TEXT);
CREATE TABLE links (src TEXT, dst TEXT);
CREATE TABLE catalogs (name TEXT PRIMARY KEY, title TEXT, upstream TEXT, ref TEXT,
  synced_at TEXT, license TEXT, count INTEGER, lanes TEXT);
CREATE TABLE catalog_items (catalog TEXT, name TEXT, family TEXT, lanes TEXT, description TEXT,
  license TEXT, path TEXT, url TEXT, bytes INTEGER, fit TEXT, note TEXT, family_note TEXT,
  PRIMARY KEY (catalog, name));
CREATE VIRTUAL TABLE entries_fts USING fts5(id UNINDEXED, title, tags, body, tokenize='porter unicode61');
CREATE VIRTUAL TABLE catalog_fts USING fts5(catalog UNINDEXED, name, family, description, note, lanes,
  tokenize='porter unicode61');
CREATE INDEX idx_fields ON entry_fields(field);
CREATE INDEX idx_tags ON entry_tags(tag);
"""


def default_db(root):
    return Path(os.environ.get("RND_DB") or Path(root) / "rnd.db")


def fingerprint(root):
    """Cheap change detector over every file the index is built from."""
    paths = list(model.entry_paths(root))
    for d in catalog.catalog_dirs(root):
        paths.extend(p for p in d.glob("*.json"))
    stamp = max((p.stat().st_mtime_ns for p in paths), default=0)
    return f"{len(paths)}:{stamp}"


def build(root, db_path=None):
    """Rebuild the index. Returns (counts, problems). Errors leave the old DB in place."""
    db_path = Path(db_path or default_db(root))
    entries, problems = model.load_all(root)
    cats = []
    for d in catalog.catalog_dirs(root):
        meta, items, cat_problems = catalog.load(d)
        problems.extend(model.Problem("error", d.name, p) for p in cat_problems if "no catalog.json" not in p)
        problems.extend(model.Problem("warning", d.name, p) for p in cat_problems if "no catalog.json" in p)
        if meta:
            cats.append((meta, items))
    if any(p.level == "error" for p in problems):
        return None, problems

    tmp = db_path.with_suffix(".db.tmp")
    if tmp.exists():
        tmp.unlink()
    con = sqlite3.connect(tmp)
    try:
        con.executescript(SCHEMA)
        for e in entries:
            con.execute("INSERT INTO entries VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
                e.id, e.path, e.title, e.date, e.kind, e.relevance, e.status,
                json.dumps(e.fields), json.dumps(e.tags), e.body, e.relevance_note,
                json.dumps(e.extra, ensure_ascii=False)))
            con.executemany("INSERT INTO entry_fields VALUES (?,?)", [(e.id, f) for f in e.fields])
            con.executemany("INSERT INTO entry_tags VALUES (?,?)", [(e.id, t) for t in e.tags])
            con.executemany("INSERT INTO sources VALUES (?,?,?,?,?)",
                            [(e.id, n, s["tier"], s["url"], s["label"]) for n, s in enumerate(e.sources)])
            con.executemany("INSERT INTO claims VALUES (?,?,?,?,?)",
                            [(e.id, n, c["confidence"], c["text"], c["via"]) for n, c in enumerate(e.claims)])
            con.executemany("INSERT INTO links VALUES (?,?)", [(e.id, l) for l in e.links])
            con.execute("INSERT INTO entries_fts VALUES (?,?,?,?)",
                        (e.id, e.title, " ".join(e.tags + e.fields), e.body))
        n_items = 0
        for meta, items in cats:
            con.execute("INSERT INTO catalogs VALUES (?,?,?,?,?,?,?,?)", (
                meta["name"], meta["title"], meta["upstream"], meta["ref"],
                meta["synced_at"], meta["license"], meta["count"], json.dumps(meta["lanes"])))
            for it in items:
                con.execute("INSERT INTO catalog_items VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
                    meta["name"], it["name"], it["family"], " | ".join(it.get("lanes", [])),
                    it["description"], it["license"],
                    it["path"], it["url"], it.get("bytes", 0), it["fit"], it["note"], it["family_note"]))
                con.execute("INSERT INTO catalog_fts VALUES (?,?,?,?,?,?)", (
                    meta["name"], it["name"], it["family"], it["description"],
                    " ".join(filter(None, [it["note"], it["family_note"]])),
                    " ".join(it.get("lanes", []))))
                n_items += 1
        built = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        con.executemany("INSERT INTO meta VALUES (?,?)", [
            ("built_at", built), ("fingerprint", fingerprint(root))])
        con.commit()
    finally:
        con.close()
    os.replace(tmp, db_path)
    return {"entries": len(entries), "catalogs": len(cats), "catalog_items": n_items}, problems


def connect(root, db_path=None, rebuild=True):
    """Open the index, rebuilding first when any source file changed."""
    db_path = Path(db_path or default_db(root))
    problems = []
    if rebuild:
        stale = True
        if db_path.exists():
            try:
                con = sqlite3.connect(db_path)
                row = con.execute("SELECT value FROM meta WHERE key='fingerprint'").fetchone()
                con.close()
                stale = not row or row[0] != fingerprint(root)
            except sqlite3.DatabaseError:
                stale = True
        if stale:
            counts, problems = build(root, db_path)
            if counts is None and not db_path.exists():
                return None, problems
    con = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con, problems


def fts_query(text, raw=False):
    """Quote each word so hyphens and operators can't break FTS5 syntax."""
    if raw:
        return text
    words = re.findall(r"[\w.+#]+", text, flags=re.UNICODE)
    return " ".join('"' + w.replace('"', '') + '"' for w in words)


def search(con, text, limit=10, raw=False, kind=None, field=None, catalogs=True, entries=True):
    q = fts_query(text, raw)
    if not q:
        return [], []
    found_entries, found_items = [], []
    if entries:
        sql = ("SELECT e.id, e.title, e.kind, e.relevance, e.date, e.path, "
               "snippet(entries_fts, 3, '[', ']', ' … ', 12) AS snip, bm25(entries_fts, 0, 8, 4, 1) AS rank "
               "FROM entries_fts JOIN entries e ON e.id = entries_fts.id WHERE entries_fts MATCH ?")
        args = [q]
        if kind:
            sql += " AND e.kind = ?"
            args.append(kind)
        if field:
            sql += " AND e.id IN (SELECT entry_id FROM entry_fields WHERE field = ?)"
            args.append(field)
        sql += " ORDER BY rank LIMIT ?"
        args.append(limit)
        found_entries = [dict(r) for r in con.execute(sql, args)]
    if catalogs and not kind and not field:
        sql = ("SELECT c.catalog, c.name, c.family, c.lanes, c.fit, c.url, "
               "snippet(catalog_fts, 3, '[', ']', ' … ', 14) AS snip, bm25(catalog_fts, 0, 6, 3, 1, 2, 2) AS rank "
               "FROM catalog_fts JOIN catalog_items c ON c.catalog = catalog_fts.catalog AND c.name = catalog_fts.name "
               "WHERE catalog_fts MATCH ? ORDER BY rank LIMIT ?")
        found_items = [dict(r) for r in con.execute(sql, [q, limit])]
    return found_entries, found_items
