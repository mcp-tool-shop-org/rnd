"""rnd — the R&D seat's command line.

Exit codes: 0 ok · 1 invalid library files · 2 usage or not found ·
3 runtime failure (an external tool, or an unexpected error; --debug shows the traceback).
"""

import argparse
import json
import re
import sqlite3
import sys
import traceback
from datetime import date
from pathlib import Path

from . import __version__, catalog, model, readouts, store

ROOT = Path(__file__).resolve().parent.parent


def fail(code, message, hint="", exit_code=2):
    print(f"error: {code}: {message}", file=sys.stderr)
    if hint:
        print(f"  hint: {hint}", file=sys.stderr)
    return exit_code


def report(problems, quiet_warnings=False):
    for p in problems:
        if p.level == "error" or not quiet_warnings:
            print(str(p), file=sys.stderr)


def open_db(args):
    con, problems = store.connect(ROOT, args.db)
    report(problems, quiet_warnings=True)
    if con is None:
        sys.exit(fail("INDEX_INVALID", "the index could not be built", "run `rnd check` to see every problem", 1))
    if any(p.level == "error" for p in problems):
        print("warning: files have errors; showing the last good index (run `rnd check`)", file=sys.stderr)
    return con


def emit(args, data, text_fn):
    if getattr(args, "json", False):
        print(json.dumps(data, indent=1, ensure_ascii=False, default=str))
    else:
        text_fn(data)


# ---------------------------------------------------------------- commands

def cmd_build(args):
    counts, problems = store.build(ROOT, args.db)
    report(problems)
    if counts is None:
        return fail("INDEX_INVALID", "build halted on errors; the previous index was kept",
                    "fix the files named above, then rebuild", 1)
    warnings = sum(p.level == "warning" for p in problems)
    print(f"built rnd.db: {counts['entries']} entries, {counts['catalogs']} catalogues "
          f"({counts['catalog_items']} items), {warnings} warnings")
    return 0


def cmd_check(args):
    entries, problems = model.load_all(ROOT)
    for d in catalog.catalog_dirs(ROOT):
        _, _, cat_problems = catalog.load(d)
        problems.extend(model.Problem("warning" if "no catalog.json" in p else "error", d.name, p)
                        for p in cat_problems)
    report(problems)
    errors = sum(p.level == "error" for p in problems)
    warnings = len(problems) - errors
    print(f"checked {len(entries)} entries: {errors} errors, {warnings} warnings")
    return 1 if errors else 0


def cmd_search(args):
    con = open_db(args)
    try:
        ents, items = store.search(con, " ".join(args.query), limit=args.limit, raw=args.raw,
                                   kind=args.kind, field=args.field,
                                   catalogs=not args.entries_only, entries=not args.catalog_only)
    except sqlite3.OperationalError as exc:
        return fail("QUERY_INVALID", str(exc), "drop --raw to search plain words")

    for r in ents + items:
        r["snip"] = " ".join(r["snip"].replace("#", " ").split())

    def text(_):
        if ents:
            print(f"Entries ({len(ents)})")
            for r in ents:
                print(f"  {r['id']}  [{r['kind']}/{r['relevance']}] {r['title']}")
                print(f"      {r['snip'].strip()}")
        if items:
            print(f"Catalogue items ({len(items)})")
            for r in items:
                fit = f" fit:{r['fit']}" if r["fit"] else ""
                print(f"  {r['catalog']}:{r['name']}  ({r['family']}{fit})")
                print(f"      {r['snip'].strip()}")
        if not ents and not items:
            print("no matches")
    emit(args, {"entries": ents, "catalog_items": items}, text)
    return 0


def cmd_show(args):
    con = open_db(args)
    row = con.execute("SELECT * FROM entries WHERE id = ?", (args.id,)).fetchone()
    if row is None:
        item = None
        if ":" in args.id:
            cat, name = args.id.split(":", 1)
            item = con.execute("SELECT * FROM catalog_items WHERE catalog=? AND name=?", (cat, name)).fetchone()
        if item is None:
            hits = [r[0] for r in con.execute("SELECT id FROM entries WHERE id LIKE ? LIMIT 5", (f"%{args.id}%",))]
            return fail("NOT_FOUND", f"no entry {args.id!r}",
                        f"did you mean: {', '.join(hits)}" if hits else "try `rnd search <words>`")
        data = dict(item)
        emit(args, data, lambda d: print("\n".join(f"{k}: {v}" for k, v in d.items() if v)))
        return 0
    data = dict(row)
    data["fields"], data["tags"] = json.loads(data["fields"]), json.loads(data["tags"])
    data["extra"] = json.loads(data["extra"])
    data["sources"] = [dict(r) for r in con.execute(
        "SELECT tier, url, label FROM sources WHERE entry_id=? ORDER BY ord", (args.id,))]
    data["claims"] = [dict(r) for r in con.execute(
        "SELECT confidence, text, via FROM claims WHERE entry_id=? ORDER BY ord", (args.id,))]
    data["linked_from"] = [r[0] for r in con.execute("SELECT src FROM links WHERE dst=?", (args.id,))]

    def text(d):
        print(f"{d['title']}\n{d['id']} · {d['kind']} · relevance:{d['relevance']} · {d['date']} · {d['path']}")
        print(f"fields: {', '.join(d['fields'])}   tags: {', '.join(d['tags'])}")
        if d["linked_from"]:
            print(f"linked from: {', '.join(d['linked_from'])}")
        print()
        print((ROOT / d["path"]).read_text(encoding="utf-8").split("---", 2)[-1].strip())
    emit(args, data, text)
    return 0


def cmd_list(args):
    con = open_db(args)
    sql, params = "SELECT id, title, kind, relevance, date, status FROM entries WHERE 1=1", []
    for col, val in (("kind", args.kind), ("relevance", args.relevance), ("status", args.status)):
        if val:
            sql += f" AND {col} = ?"
            params.append(val)
    if args.field:
        sql += " AND id IN (SELECT entry_id FROM entry_fields WHERE field = ?)"
        params.append(args.field)
    if args.tag:
        sql += " AND id IN (SELECT entry_id FROM entry_tags WHERE tag = ?)"
        params.append(args.tag)
    sql += " ORDER BY date DESC, id"
    rows = [dict(r) for r in con.execute(sql, params)]

    def text(rs):
        for r in rs:
            print(f"{r['date']}  {r['id']:<44} [{r['kind']}/{r['relevance']}] {r['title']}")
        print(f"{len(rs)} entries")
    emit(args, rows, text)
    return 0


def cmd_tools(args):
    con = open_db(args)
    rows = []
    for r in con.execute("SELECT id, title, extra, relevance_note FROM entries WHERE kind='instrument' ORDER BY id"):
        extra = json.loads(r["extra"])
        if args.status and extra.get("instrument_status") != args.status:
            continue
        rows.append({"id": r["id"], "title": r["title"], **extra})

    def text(rs):
        for r in rs:
            print(f"{r['id']:<22} {r.get('instrument_status', ''):<8} {r['title']}")
            print(f"    invoke: {r.get('invoke', '')}")
            if r.get("when"):
                print(f"    when:   {r['when']}")
        print(f"{len(rs)} instruments")
    emit(args, rows, text)
    return 0


def cmd_stats(args):
    con = open_db(args)
    q = lambda sql: [tuple(r) for r in con.execute(sql)]
    data = {
        "built_at": q("SELECT value FROM meta WHERE key='built_at'")[0][0],
        "entries": q("SELECT count(*) FROM entries")[0][0],
        "by_kind": q("SELECT kind, count(*) FROM entries GROUP BY kind ORDER BY 2 DESC"),
        "by_relevance": q("SELECT relevance, count(*) FROM entries GROUP BY relevance ORDER BY 2 DESC"),
        "by_field": q("SELECT field, count(*) FROM entry_fields GROUP BY field ORDER BY 2 DESC, 1"),
        "sources_by_tier": q("SELECT tier, count(*) FROM sources GROUP BY tier ORDER BY 2 DESC"),
        "claims_by_confidence": q("SELECT confidence, count(*) FROM claims GROUP BY confidence ORDER BY 2 DESC"),
        "catalogs": q("SELECT name, count, substr(ref,1,12), synced_at FROM catalogs"),
    }

    def text(d):
        print(f"index built {d['built_at']} · {d['entries']} entries")
        for key in ("by_kind", "by_relevance", "by_field", "sources_by_tier", "claims_by_confidence"):
            print(f"{key}: " + ", ".join(f"{k} {n}" for k, n in d[key]))
        for name, count, ref, synced in d["catalogs"]:
            print(f"catalogue {name}: {count} items @ {ref} (synced {synced})")
    emit(args, data, text)
    return 0


def slugify(text):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")[:60]


def cmd_new(args):
    today = args.date or date.today().isoformat()
    slug = args.id or f"{today}-{slugify(args.title)}"
    if not model.ID_RE.match(slug):
        return fail("BAD_ID", f"id {slug!r} is not valid", "use lower-case letters, digits and '-'")
    folder = ROOT / ("instruments" if args.kind == "instrument" else f"entries/{today[:4]}")
    path = folder / f"{slug}.md"
    if path.exists():
        return fail("EXISTS", f"{path.relative_to(ROOT).as_posix()} already exists", "pick another title or --id")
    template = (ROOT / "entries" / "_template.md").read_text(encoding="utf-8")
    text = (template.replace("{{id}}", slug).replace("{{title}}", args.title)
            .replace("{{date}}", today).replace("{{kind}}", args.kind)
            .replace("{{relevance}}", args.relevance)
            .replace("{{fields}}", ", ".join(args.field or ["general"]))
            .replace("{{tags}}", ", ".join(args.tag or [])))
    folder.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(path.relative_to(ROOT).as_posix())
    return 0


def cmd_catalog(args):
    if args.action == "sync":
        try:
            catalog.sync(ROOT, args.name)
        except catalog.CatalogError as exc:
            return fail(exc.code, str(exc), exc.hint, 3)
        return cmd_build(args)
    con = open_db(args)
    if args.action == "lanes":
        row = con.execute("SELECT lanes FROM catalogs WHERE name=?", (args.name,)).fetchone()
        lanes = json.loads(row[0]) if row and row[0] else []
        for lane in lanes:
            lane["fits"] = dict(con.execute(
                "SELECT coalesce(nullif(fit,''),'-'), count(*) FROM catalog_items WHERE catalog=? "
                "AND (' | ' || lanes || ' | ') LIKE ? GROUP BY 1", (args.name, f"% | {lane['title']} | %")).fetchall())
        emit(args, lanes, lambda ls: [print(f"{l['count']:>4}  {l['title']:<22} {l['fits']}") for l in ls])
        return 0
    if args.action == "families":
        rows = [dict(r) for r in con.execute(
            "SELECT family, count(*) AS n, max(fit) AS fit, max(family_note) AS note FROM catalog_items "
            "WHERE catalog=? GROUP BY family ORDER BY n DESC, family", (args.name,))]
        emit(args, rows, lambda rs: [print(f"{r['n']:>4}  {r['family']:<22} {r['fit'] or '-':<9} {r['note'] or ''}") for r in rs])
        return 0
    sql, params = "SELECT name, family, lanes, fit, note, description FROM catalog_items WHERE catalog=?", [args.name]
    if args.fit:
        sql += " AND fit=?"
        params.append(args.fit)
    if args.family:
        sql += " AND family=?"
        params.append(args.family)
    if args.lane:
        sql += " AND (' | ' || lanes || ' | ') LIKE ?"
        params.append(f"% | {args.lane} | %")
    rows = [dict(r) for r in con.execute(sql + " ORDER BY family, name", params)]

    def text(rs):
        for r in rs:
            print(f"{r['name']:<46} {r['fit'] or '-':<9} {(r['note'] or r['description'])[:110]}")
        print(f"{len(rs)} items")
    emit(args, rows, text)
    return 0


def cmd_readouts(args):
    root = readouts.root_dir(args.root)
    try:
        if args.list or not args.query:
            kbs = readouts.knowledge_bases(root)

            def text(rows):
                for k in rows:
                    print(f"{k.get('entries', ''):>5} {k.get('noun', ''):<12} {k['name']:<26} {(k.get('what') or '')[:80]}")
                print(f"{len(rows)} knowledge bases in {root.as_posix()}")
            emit(args, kbs, text)
            return 0
        rows, problems = readouts.search(root, " ".join(args.query), limit=args.limit, kb=args.kb,
                                         any_word=args.any)
    except readouts.ReadoutsError as exc:
        return fail(exc.code, str(exc), exc.hint)
    for p in problems:
        print(f"warning: {p}", file=sys.stderr)

    def text(rs):
        current = None
        for r in rs:
            if r["kb"] != current:
                current = r["kb"]
                print(f"{current} ({r['noun']})")
            print(f"  {r['slug']}  {r['name']}")
            print(f"      {r['snip']}")
        if not rs:
            print("no matches")
    emit(args, rows, text)
    return 0


def cmd_sql(args):
    con = open_db(args)
    try:
        cur = con.execute(args.query)
    except sqlite3.Error as exc:
        return fail("SQL_ERROR", str(exc), "the index is read-only; list its tables with: rnd sql \"SELECT name FROM sqlite_master WHERE type='table'\"")
    cols = [c[0] for c in cur.description or []]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    emit(args, rows, lambda rs: [print(" | ".join(str(v) for v in r.values())) for r in rs])
    return 0


# ---------------------------------------------------------------- parser

def build_parser():
    p = argparse.ArgumentParser(prog="rnd", description="Search and grow the studio R&D library.")
    p.add_argument("--db", help="index path (default: rnd.db in the repo, or $RND_DB)")
    p.add_argument("--debug", action="store_true", help="show the full traceback on an unexpected error")
    p.add_argument("--version", action="version", version=f"rnd {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help_text, json_flag=True):
        sp = sub.add_parser(name, help=help_text, description=help_text)
        sp.set_defaults(fn=fn)
        if json_flag:
            sp.add_argument("--json", action="store_true", help="machine-readable output")
        return sp

    add("build", cmd_build, "rebuild rnd.db from entries/, instruments/ and catalogs/", json_flag=False)
    add("check", cmd_check, "validate every file without touching the index", json_flag=False)

    s = add("search", cmd_search, "full-text search across entries and catalogues")
    s.add_argument("query", nargs="+")
    s.add_argument("--limit", type=int, default=10)
    s.add_argument("--kind", choices=model.KINDS)
    s.add_argument("--field")
    s.add_argument("--entries-only", action="store_true")
    s.add_argument("--catalog-only", action="store_true")
    s.add_argument("--raw", action="store_true", help="pass the query to FTS5 unquoted (AND/OR/NEAR, prefix*)")

    s = add("show", cmd_show, "show one entry (or <catalog>:<item>)")
    s.add_argument("id")

    s = add("list", cmd_list, "list entries, newest first")
    s.add_argument("--kind", choices=model.KINDS)
    s.add_argument("--relevance", choices=model.RELEVANCE)
    s.add_argument("--status", choices=model.STATUS)
    s.add_argument("--field")
    s.add_argument("--tag")

    s = add("tools", cmd_tools, "list the studio instruments this seat can use")
    s.add_argument("--status", choices=model.INSTRUMENT_STATUS)

    add("stats", cmd_stats, "counts by kind, field, source tier and claim confidence")

    s = add("new", cmd_new, "scaffold a new entry file from the template", json_flag=False)
    s.add_argument("title")
    s.add_argument("--kind", choices=model.KINDS, default="finding")
    s.add_argument("--relevance", choices=model.RELEVANCE, default="reference")
    s.add_argument("--field", action="append")
    s.add_argument("--tag", action="append")
    s.add_argument("--id")
    s.add_argument("--date")

    s = add("catalog", cmd_catalog, "work with external catalogues")
    s.add_argument("action", choices=("list", "lanes", "families", "sync"))
    s.add_argument("name", nargs="?", default="nvidia-skills")
    s.add_argument("--fit", choices=catalog.FITS)
    s.add_argument("--family")
    s.add_argument("--lane", help="e.g. 'GPU Development' (see `rnd catalog lanes`)")

    s = add("readouts", cmd_readouts,
            "search the readouts knowledge bases (read-only; $RND_READOUTS or E:/AI/readouts)")
    s.add_argument("query", nargs="*")
    s.add_argument("--kb", help="limit to one knowledge base, e.g. vocology-knowledge")
    s.add_argument("--limit", type=int, default=5, help="results per knowledge base")
    s.add_argument("--any", action="store_true", help="match any word instead of all of them")
    s.add_argument("--list", action="store_true", help="list the knowledge bases")
    s.add_argument("--root", help="readouts checkout (overrides $RND_READOUTS)")

    s = add("sql", cmd_sql, "run a read-only SQL query against the index")
    s.add_argument("query")
    return p


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args) or 0
    except KeyboardInterrupt:
        return fail("INTERRUPTED", "stopped by the user", exit_code=3)
    except Exception as exc:  # last resort: a structured error, never a raw stack by default
        if args.debug:
            traceback.print_exc()
        return fail("INTERNAL", f"{type(exc).__name__}: {exc}",
                    "rerun with --debug for the traceback, and report it if it persists", 3)
