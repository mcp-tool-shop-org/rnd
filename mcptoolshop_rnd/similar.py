"""Read-only FTS5 similar-claims lookup (`rnd similar <entry>`)."""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from . import model, store

STOPWORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "but", "by",
    "can", "could", "did", "do", "does", "done", "for", "from", "had", "has",
    "have", "having", "he", "her", "here", "him", "his", "how", "if", "in",
    "into", "is", "it", "its", "just", "may", "might", "more", "most", "must",
    "no", "nor", "not", "now", "of", "on", "one", "only", "or", "other", "our",
    "out", "over", "own", "same", "she", "should", "so", "some", "such", "than",
    "that", "the", "their", "them", "then", "there", "these", "they", "this",
    "those", "through", "to", "too", "under", "up", "use", "used", "uses",
    "using", "very", "was", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "will", "with", "within", "without", "would",
})


class SimilarError(Exception):
    def __init__(self, code: str, message: str, hint: str = "", exit_code: int = 2):
        super().__init__(message)
        self.code, self.hint, self.exit_code = code, hint, exit_code


def claim_fts_query(text: str) -> str:
    """Build a safe FTS5 OR query from Unicode word tokens matching `porter unicode61`."""
    cleaned = re.sub(r"<!--[\s\S]*?-->", " ", text or "")
    cleaned = re.sub(r"https?://\S+", " ", cleaned)
    raw_tokens = re.findall(r"[^\W_]+", cleaned)
    terms: list[str] = []
    seen: set[str] = set()
    for tok in raw_tokens:
        low = tok.lower()
        if (len(low) < 2 and low.isascii()) or low in STOPWORDS:
            continue
        if low not in seen:
            seen.add(low)
            terms.append('"' + low + '"')
    if not terms:
        for tok in raw_tokens:
            low = tok.lower()
            if low not in seen:
                seen.add(low)
                terms.append('"' + low + '"')
    return " OR ".join(terms)


def _resolve_readable_entry(root: Path, target: str) -> model.Entry:
    root_res = Path(root).resolve()
    target_path = Path(target)
    if not target_path.is_absolute():
        candidate = (Path.cwd() / target_path).resolve()
        if not candidate.is_file():
            candidate = (root_res / target_path).resolve()
    else:
        candidate = target_path.resolve()

    target_posix = Path(target).as_posix()
    for path in model.entry_paths(root_res):
        res = path.resolve()
        rel = res.relative_to(root_res).as_posix()
        entry, probs = model.load(res, root_res)
        if res == candidate or rel == target_posix or (entry is not None and entry.id == target):
            if entry is None:
                msg = probs[0].message if probs else f"{rel}: unreadable entry"
                raise SimilarError("UNREADABLE", msg, "fix the entry's encoding or frontmatter", exit_code=1)
            return entry

    if candidate.is_file():
        load_root = root_res if candidate.is_relative_to(root_res) else candidate.parent
        entry, probs = model.load(candidate, load_root)
        if entry is None:
            msg = probs[0].message if probs else f"{candidate.name}: unreadable entry"
            raise SimilarError("UNREADABLE", msg, "fix the entry's encoding or file frontmatter", exit_code=1)
        return entry

    raise SimilarError("NOT_FOUND", f"no entry {target!r}", "pass an entry id or path to a Markdown file", exit_code=2)


def _compute_provisional_ids(entries: list[model.Entry]) -> dict[tuple[str, int], str]:
    taken = {c["id"] for e in entries for c in e.claims if c["id"]}
    provisional: dict[tuple[str, int], str] = {}
    for e in entries:
        if e.path.startswith("instruments/"):
            continue
        for ord_idx, c in enumerate(e.claims):
            if not c["id"]:
                pid = model.make_claim_id(e.id, c["text"], taken)
                taken.add(pid)
                provisional[(e.id, ord_idx)] = pid
    return provisional


def _open_claims_fts_readonly(root: Path, db_path=None):
    """Open claims_fts read-only from rnd.db when fresh, or build an in-memory FTS5 index without writing."""
    entries: list[model.Entry] = []
    seen_ids: set[str] = set()
    for path in model.entry_paths(root):
        entry, _ = model.load(path, root)
        if entry is None or entry.id in seen_ids:
            continue
        seen_ids.add(entry.id)
        entries.append(entry)

    provisional = _compute_provisional_ids(entries)

    cand_db = Path(db_path or store.default_db(root))
    if cand_db.is_file():
        try:
            con = sqlite3.connect(f"file:{cand_db.as_posix()}?mode=ro", uri=True)
            con.row_factory = sqlite3.Row
            has_fts = con.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='claims_fts'"
            ).fetchone()
            fp = con.execute("SELECT value FROM meta WHERE key='fingerprint'").fetchone()
            if has_fts and fp and fp[0] == store.fingerprint(root):
                return con, provisional
            con.close()
        except sqlite3.DatabaseError:
            pass

    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript(
        """
        CREATE TABLE entries (id TEXT PRIMARY KEY, date TEXT, kind TEXT);
        CREATE TABLE claims (entry_id TEXT, ord INTEGER, id TEXT, state TEXT, text TEXT, relations TEXT);
        CREATE VIRTUAL TABLE claims_fts USING fts5(entry_id UNINDEXED, ord UNINDEXED, text, tokenize='porter unicode61');
        """
    )
    for e in entries:
        con.execute("INSERT INTO entries VALUES (?,?,?)", (e.id, e.date, e.kind))
        if e.claims:
            con.executemany(
                "INSERT INTO claims VALUES (?,?,?,?,?,?)",
                [(e.id, n, c["id"] or None, c["state"], c["text"], json.dumps(c["relations"], sort_keys=True))
                 for n, c in enumerate(e.claims)],
            )
            con.executemany(
                "INSERT INTO claims_fts VALUES (?,?,?)",
                [(e.id, n, c["text"]) for n, c in enumerate(e.claims)],
            )
    return con, provisional


def find_similar(root, target: str, limit: int = 5, db_path=None) -> dict:
    """Return closest claims in other entries for every claim in `target`. Never writes or blocks."""
    if limit < 1:
        raise SimilarError("USAGE", "--limit must be at least 1", "pass a positive integer, e.g. --limit 5", exit_code=2)
    root_path = Path(root)
    entry = _resolve_readable_entry(root_path, target)
    con, provisional = _open_claims_fts_readonly(root_path, db_path=db_path)
    try:
        owner_cache: dict[str, str] = {}

        def owner_of(cid: str) -> str:
            if cid not in owner_cache:
                row = con.execute("SELECT entry_id FROM claims WHERE id = ?", (cid,)).fetchone()
                owner_cache[cid] = row["entry_id"] if row else ""
            return owner_cache[cid]

        claim_results = []
        first_link_id = ""
        for ord_idx, c in enumerate(entry.claims):
            fts_q = claim_fts_query(c["text"])
            hits = []
            if fts_q:
                rows = con.execute(
                    "SELECT c.entry_id, c.ord, c.id, c.state, e.date, c.text, c.relations, "
                    "-bm25(claims_fts) AS raw_score "
                    "FROM claims_fts "
                    "JOIN claims c ON c.entry_id = claims_fts.entry_id AND c.ord = CAST(claims_fts.ord AS INTEGER) "
                    "JOIN entries e ON e.id = c.entry_id "
                    "WHERE claims_fts MATCH ? AND c.entry_id != ? AND e.kind != 'instrument' "
                    "ORDER BY bm25(claims_fts) ASC, e.date DESC, c.entry_id ASC, c.ord ASC "
                    "LIMIT ?",
                    (fts_q, entry.id, limit),
                ).fetchall()
                for r in rows:
                    rels = json.loads(r["relations"] or "{}")
                    cid = r["id"]
                    link_id = cid or provisional.get((r["entry_id"], r["ord"]), "")
                    if not first_link_id and link_id:
                        first_link_id = link_id
                    hit = {
                        "id": cid,
                        "entry_id": r["entry_id"],
                        "ord": r["ord"],
                        "display_ref": cid or f"{r['entry_id']}#{r['ord']}",
                        "link_id": link_id,
                        "state": r["state"],
                        "date": r["date"],
                        "score": round(float(r["raw_score"]), 2),
                        "text": r["text"],
                    }
                    if r["state"] == "superseded":
                        hit["replaced_by"] = [
                            {"id": tid, "entry_id": owner_of(tid)}
                            for tid in rels.get("superseded-by", [])
                        ]
                    elif r["state"] == "disputed":
                        hit["contradicted_by"] = [
                            {"id": tid, "entry_id": owner_of(tid)}
                            for tid in rels.get("contradicted-by", [])
                        ]
                    hits.append(hit)
            claim_results.append({
                "ord": ord_idx,
                "id": c["id"] or None,
                "state": c["state"],
                "text": c["text"],
                "query": fts_q,
                "hits": hits,
            })

        sample_id = first_link_id or "<id>"
        return {
            "entry": entry.id,
            "path": entry.path,
            "date": entry.date,
            "limit": limit,
            "claims": claim_results,
            "relation_clauses": {
                "supersedes": f"(supersedes: {sample_id})",
                "contradicts": f"(contradicts: {sample_id})",
                "supports": f"(supports: {sample_id})",
            },
            "reconcile_command": f"python -m rnd reconcile {entry.id}",
        }
    finally:
        con.close()


def render_similar(rep: dict) -> str:
    """Format `find_similar` output for humans."""
    lines = [f"{rep['entry']} ({rep['date']}) — {len(rep['claims'])} claim(s), top {rep['limit']} per claim"]
    if not rep["claims"]:
        lines.append("  no claims in this entry")
    for c in rep["claims"]:
        cid = c["id"] or f"#{c['ord']}"
        lines.append("")
        lines.append(f"Claim {cid} [{c['state']}]: {c['text']}")
        if not c["hits"]:
            lines.append("  no similar claims in other entries")
            continue
        for h in c["hits"]:
            ref = h["id"] if h["id"] else f"{h['entry_id']}#{h['ord']} (id if linked: {h['link_id']})"
            lines.append(f"  {h['score']:>6.2f}  {ref} [{h['state']}] {h['entry_id']} ({h['date']})")
            lines.append(f"          {h['text']}")
            if h["state"] == "superseded":
                by_txt = ", ".join(
                    f"{b['id']} ({b['entry_id']})" if b.get("entry_id") else b["id"]
                    for b in h.get("replaced_by", [])
                )
                lines.append(f"          ! replaced by {by_txt or 'unlinked'}")
            elif h["state"] == "disputed":
                by_txt = ", ".join(
                    f"{b['id']} ({b['entry_id']})" if b.get("entry_id") else b["id"]
                    for b in h.get("contradicted_by", [])
                )
                lines.append(f"          ! contradicted by {by_txt or 'unlinked'}")

    clauses = rep["relation_clauses"]
    header = (
        "To link a claim above (for example, for the top hit above), add a clause to the new claim line and run reconcile:"
        if clauses["supersedes"] != "(supersedes: <id>)"
        else "To link a claim above, add a clause to the new claim line and run reconcile:"
    )
    lines.extend([
        "",
        header,
        f"  {clauses['supersedes']}",
        f"  {clauses['contradicts']}",
        f"  {clauses['supports']}",
        f"  {rep['reconcile_command']}",
    ])
    return "\n".join(lines)
