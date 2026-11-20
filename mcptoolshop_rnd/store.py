"""The SQLite index (rnd.db). Always rebuildable from the files; never edited."""

from collections import Counter
import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from . import catalog, model, questions, runs

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE entries (
  id TEXT PRIMARY KEY, path TEXT, title TEXT, date TEXT, kind TEXT,
  relevance TEXT, status TEXT, fields TEXT, tags TEXT, body TEXT,
  relevance_note TEXT, extra TEXT);
CREATE TABLE entry_fields (entry_id TEXT, field TEXT);
CREATE TABLE entry_tags (entry_id TEXT, tag TEXT);
CREATE TABLE sources (entry_id TEXT, ord INTEGER, tier TEXT, url TEXT, label TEXT);
CREATE TABLE claims (entry_id TEXT, ord INTEGER, id TEXT, state TEXT, confidence TEXT, text TEXT, via TEXT, relations TEXT);
CREATE TABLE claim_relations (src_entry_id TEXT, src_id TEXT, rel TEXT, dst_id TEXT, dst_entry_id TEXT);
CREATE TABLE links (src TEXT, dst TEXT);
CREATE TABLE questions (
  id TEXT PRIMARY KEY, path TEXT, title TEXT, date TEXT,
  status TEXT, fields TEXT, tags TEXT, answered_by TEXT, body TEXT);
CREATE TABLE question_fields (question_id TEXT, field TEXT);
CREATE TABLE catalogs (name TEXT PRIMARY KEY, title TEXT, upstream TEXT, ref TEXT,
  synced_at TEXT, license TEXT, count INTEGER, lanes TEXT);
CREATE TABLE catalog_items (catalog TEXT, name TEXT, family TEXT, lanes TEXT, description TEXT,
  license TEXT, path TEXT, url TEXT, bytes INTEGER, fit TEXT, note TEXT, family_note TEXT,
  PRIMARY KEY (catalog, name));
CREATE VIRTUAL TABLE entries_fts USING fts5(id UNINDEXED, title, tags, body, tokenize='porter unicode61');
CREATE VIRTUAL TABLE claims_fts USING fts5(entry_id UNINDEXED, ord UNINDEXED, text, tokenize='porter unicode61');
CREATE VIRTUAL TABLE questions_fts USING fts5(id UNINDEXED, title, fields, body, tokenize='porter unicode61');
CREATE VIRTUAL TABLE catalog_fts USING fts5(catalog UNINDEXED, name, family, description, note, lanes,
  tokenize='porter unicode61');
CREATE TABLE experiments (name TEXT PRIMARY KEY, status TEXT, template TEXT, design TEXT);
CREATE TABLE runs (experiment TEXT, id TEXT, venue TEXT, hardware TEXT, date TEXT, cost REAL, cost_unit TEXT,
  cost_basis TEXT, cap REAL, projected_cost REAL, outcome TEXT, why TEXT, raw_manifest_id TEXT, pins TEXT,
  PRIMARY KEY (experiment, id));
CREATE TABLE budgets (experiment TEXT, cost_unit TEXT, cap REAL, set_by TEXT, excludes TEXT, excludes_why TEXT,
  reconciled TEXT, phases TEXT, PRIMARY KEY (experiment, cost_unit));
CREATE TABLE files (sha256 TEXT PRIMARY KEY, bytes INTEGER, tier TEXT, licence TEXT);
CREATE TABLE manifest_files (manifest_id TEXT, path TEXT, sha256 TEXT, PRIMARY KEY (manifest_id, path));
CREATE TABLE copies (sha256 TEXT, store TEXT, location TEXT);
CREATE INDEX idx_copies ON copies(sha256);
CREATE INDEX idx_manifest_sha ON manifest_files(sha256);
CREATE INDEX idx_fields ON entry_fields(field);
CREATE INDEX idx_tags ON entry_tags(tag);
CREATE INDEX idx_claims_id ON claims(id);
CREATE INDEX idx_claims_state ON claims(state);
CREATE INDEX idx_question_fields ON question_fields(field);
"""


def default_db(root):
    return Path(os.environ.get("RND_DB") or Path(root) / "rnd.db")


def misses_path(root, db_path=None):
    return Path(db_path or default_db(root)).with_suffix(".misses.jsonl")


def usage_disabled():
    return os.environ.get("RND_NO_USAGE", "").strip().lower() in ("1", "true", "yes")


def _guard_not_instruments(root, path):
    inst = (Path(root) / "instruments").resolve()
    if Path(path).resolve().is_relative_to(inst):
        raise ValueError(f"refusing to write {path} inside instruments/")


SCHEMA_ID = hashlib.sha256(SCHEMA.encode("utf-8")).hexdigest()[:12]


def fingerprint(root):
    """Cheap change detector over every file the index is built from, and the schema it's built with: an rnd
    upgrade that changes the tables rebuilds the index instead of serving the old one."""
    paths = list(model.entry_paths(root)) + list(questions.question_paths(root))
    for d in catalog.catalog_dirs(root):
        paths.extend(p for p in d.glob("*.json"))
    paths.extend(runs.source_paths(root))
    stamp = max((p.stat().st_mtime_ns for p in paths), default=0)
    return f"{SCHEMA_ID}:{len(paths)}:{stamp}"


def build(root, db_path=None):
    """Rebuild the index. Returns (counts, problems). Errors leave the old DB in place."""
    db_path = Path(db_path or default_db(root))
    _guard_not_instruments(root, db_path)
    entries, problems = model.load_all(root)
    known_claim_ids = {c["id"] for e in entries for c in e.claims if c["id"]}
    claim_owner = {c["id"]: e.id for e in entries for c in e.claims if c["id"]}
    qs, q_problems = questions.load_all(root, known_claim_ids=known_claim_ids)
    problems.extend(q_problems)
    cats = []
    for d in catalog.catalog_dirs(root):
        meta, items, cat_problems = catalog.load(d)
        problems.extend(model.Problem("error", d.name, p) for p in cat_problems if "no catalog.json" not in p)
        problems.extend(model.Problem("warning", d.name, p) for p in cat_problems if "no catalog.json" in p)
        if meta:
            cats.append((meta, items))
    record_rows, record_problems = runs.index_rows(root)
    problems.extend(model.Problem(level, where, msg) for level, where, msg in record_problems)
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
            con.executemany(
                "INSERT INTO claims VALUES (?,?,?,?,?,?,?,?)",
                [(e.id, n, c["id"] or None, c["state"], c["confidence"], c["text"], c["via"],
                  json.dumps(c["relations"], sort_keys=True)) for n, c in enumerate(e.claims)],
            )
            if e.claims:
                con.executemany(
                    "INSERT INTO claims_fts VALUES (?,?,?)",
                    [(e.id, n, c["text"]) for n, c in enumerate(e.claims)],
                )
            rel_rows = [
                (e.id, c["id"] or "", rel_name, tid, claim_owner.get(tid, ""))
                for c in e.claims
                for rel_name, tids in c["relations"].items()
                for tid in tids
            ]
            if rel_rows:
                con.executemany("INSERT INTO claim_relations VALUES (?,?,?,?,?)", rel_rows)
            con.executemany("INSERT INTO links VALUES (?,?)", [(e.id, l) for l in e.links])
            con.execute("INSERT INTO entries_fts VALUES (?,?,?,?)",
                        (e.id, e.title, " ".join(e.tags + e.fields), e.body))
        for q in qs:
            con.execute("INSERT INTO questions VALUES (?,?,?,?,?,?,?,?,?)", (
                q.id, q.path, q.title, q.date, q.status,
                json.dumps(q.fields), json.dumps(q.tags), json.dumps(q.answered_by), q.body))
            con.executemany("INSERT INTO question_fields VALUES (?,?)", [(q.id, f) for f in q.fields])
            con.execute("INSERT INTO questions_fts VALUES (?,?,?,?)",
                        (q.id, q.title, " ".join(q.fields + q.tags), q.body))
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
        for table, values in record_rows.items():
            if values:
                marks = ",".join("?" * len(values[0]))
                con.executemany(f"INSERT INTO {table} VALUES ({marks})", values)
        built = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        con.executemany("INSERT INTO meta VALUES (?,?)", [
            ("built_at", built), ("fingerprint", fingerprint(root))])
        con.commit()
    finally:
        con.close()
    os.replace(tmp, db_path)
    return {"entries": len(entries), "questions": len(qs), "catalogs": len(cats), "catalog_items": n_items,
            "experiments": len(record_rows["experiments"]), "runs": len(record_rows["runs"]),
            "files": len(record_rows["files"])}, problems


def connect(root, db_path=None, rebuild=True):
    """Open the index, rebuilding first when any source file changed."""
    db_path = Path(db_path or default_db(root))
    _guard_not_instruments(root, db_path)
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


def exact_words(text):
    """The query's terms, for --exact: split on spaces, case kept, inner punctuation kept, so `Run:ai` and
    `NeMo-Relay` are each one term and never match `Run` or `NeMo` alone. Quotes and trailing commas are dropped."""
    terms = (t.strip("\"'`,;()[]{}") for t in text.split())
    return [t for t in terms if re.search(r"\w", t)]


def exact_match(words, text):
    """True when every word appears as a whole word, same case, in `text` (no stemming)."""
    return all(re.search(r"(?<![\w])" + re.escape(w) + r"(?![\w])", text or "") for w in words)


def exact_snippet(words, text, width=60):
    """A short excerpt around the first exact hit, the hit in brackets."""
    for w in words:
        m = re.search(r"(?<![\w])" + re.escape(w) + r"(?![\w])", text or "")
        if m:
            lo, hi = max(0, m.start() - width), min(len(text), m.end() + width)
            return ("… " if lo else "") + text[lo:m.start()] + "[" + m.group(0) + "]" + text[m.end():hi] + (" …" if hi < len(text) else "")
    return ""


def entry_flagged_claims(con, entry_id):
    """Return superseded or disputed claims on an entry, with any replacing/contradicting claim ids."""
    out = []
    for r in con.execute(
        "SELECT id, state, text, relations FROM claims "
        "WHERE entry_id=? AND state IN ('superseded', 'disputed') ORDER BY ord",
        (entry_id,),
    ):
        rels = json.loads(r["relations"] or "{}")
        rel_key = "superseded-by" if r["state"] == "superseded" else "contradicted-by"
        targets = []
        for tid in rels.get(rel_key, []):
            owner = con.execute("SELECT entry_id FROM claims WHERE id=?", (tid,)).fetchone()
            targets.append({"id": tid, "entry_id": owner["entry_id"] if owner else ""})
        out.append({"id": r["id"] or "", "state": r["state"], "text": r["text"], "by": targets})
    return out


def search(con, text, limit=10, raw=False, kind=None, field=None, catalogs=True, entries=True, exact=False):
    """Full-text search. The index stems words (`pair` finds `pairs`, `paired`); with `exact`, results are
    narrowed to rows holding every query word whole and in the same case, so `PAIR` finds the product,
    not the word."""
    q = fts_query(text, raw)
    if not q:
        return [], []
    words = exact_words(text) if exact and not raw else []
    fetch = min(max(limit * 20, 200), 2000) if words else limit
    found_entries, found_items = [], []
    if entries:
        sql = ("SELECT e.id, e.title, e.kind, e.relevance, e.date, e.path, "
               "snippet(entries_fts, 3, '[', ']', ' … ', 12) AS snip, bm25(entries_fts, 0, 8, 4, 1) AS rank, "
               "entries_fts.title AS ft, entries_fts.tags AS fg, entries_fts.body AS fb "
               "FROM entries_fts JOIN entries e ON e.id = entries_fts.id WHERE entries_fts MATCH ?")
        args = [q]
        if kind:
            sql += " AND e.kind = ?"
            args.append(kind)
        if field:
            sql += " AND e.id IN (SELECT entry_id FROM entry_fields WHERE field = ?)"
            args.append(field)
        sql += " ORDER BY rank LIMIT ?"
        args.append(fetch)
        found_entries = _narrow([dict(r) for r in con.execute(sql, args)], words, ("ft", "fg", "fb"), "fb", limit)
        for r in found_entries:
            r["flagged_claims"] = entry_flagged_claims(con, r["id"])
    if catalogs and not kind and not field:
        sql = ("SELECT c.catalog, c.name, c.family, c.lanes, c.fit, c.url, "
               "snippet(catalog_fts, 3, '[', ']', ' … ', 14) AS snip, bm25(catalog_fts, 0, 6, 3, 1, 2, 2) AS rank, "
               "catalog_fts.name AS fn, catalog_fts.family AS ff, catalog_fts.description AS fd, catalog_fts.note AS fo "
               "FROM catalog_fts JOIN catalog_items c ON c.catalog = catalog_fts.catalog AND c.name = catalog_fts.name "
               "WHERE catalog_fts MATCH ? ORDER BY rank LIMIT ?")
        found_items = _narrow([dict(r) for r in con.execute(sql, [q, fetch])], words, ("fn", "ff", "fd", "fo"), "fd", limit)
    return found_entries, found_items


def search_questions(con, text, limit=10, raw=False, field=None, exact=False):
    """Full-text search across open/answered question files."""
    q = fts_query(text, raw)
    if not q:
        return []
    words = exact_words(text) if exact and not raw else []
    fetch = min(max(limit * 20, 200), 2000) if words else limit
    sql = ("SELECT q.id, q.title, q.status, q.date, q.path, q.fields, q.answered_by, "
           "snippet(questions_fts, 3, '[', ']', ' … ', 12) AS snip, bm25(questions_fts, 0, 8, 4, 1) AS rank, "
           "questions_fts.title AS ft, questions_fts.fields AS fg, questions_fts.body AS fb "
           "FROM questions_fts JOIN questions q ON q.id = questions_fts.id WHERE questions_fts MATCH ?")
    args = [q]
    if field:
        sql += " AND q.id IN (SELECT question_id FROM question_fields WHERE field = ?)"
        args.append(field)
    sql += " ORDER BY rank LIMIT ?"
    args.append(fetch)
    rows = _narrow([dict(r) for r in con.execute(sql, args)], words, ("ft", "fg", "fb"), "fb", limit)
    for r in rows:
        r["fields"] = json.loads(r["fields"] or "[]")
        r["answered_by"] = json.loads(r["answered_by"] or "[]")
    return rows


def record_search_miss(root, query_text, db_path=None, now=None):
    """Append one local line {time, query} beside rnd.db when a search returns nothing."""
    q = str(query_text or "").strip()
    if usage_disabled() or not q:
        return False
    mp = misses_path(root, db_path)
    _guard_not_instruments(root, mp)
    ts = now or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    mp.parent.mkdir(parents=True, exist_ok=True)
    with open(mp, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"time": ts, "query": q}, ensure_ascii=False) + "\n")
    return True


def read_search_misses(root, db_path=None, top_n=10):
    """Return total zero-hit search count and most frequent missed queries from the local log."""
    mp = misses_path(root, db_path)
    if not mp.is_file():
        return {"path": mp.name, "misses": 0, "top_misses": []}
    counts = Counter()
    total = 0
    for line in mp.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        q = str(row.get("query") or "").strip()
        if q:
            counts[q] += 1
            total += 1
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]
    return {
        "path": mp.name,
        "misses": total,
        "top_misses": [{"query": q, "count": n} for q, n in top],
    }


def _narrow(rows, words, text_keys, snip_key, limit):
    """Drop the full-text columns; with exact words, keep only rows that hold them whole and re-snip."""
    out = []
    for r in rows:
        full = "\n".join(str(r.get(k) or "") for k in text_keys)
        if words:
            if not exact_match(words, full):
                continue
            r["snip"] = exact_snippet(words, str(r.get(snip_key) or "")) or exact_snippet(words, full)
        for k in text_keys:
            r.pop(k, None)
        out.append(r)
        if len(out) >= limit:
            break
    return out
