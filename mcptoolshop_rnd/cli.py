"""rnd — the R&D seat's command line.

Exit codes: 0 ok · 1 invalid library files · 2 usage or not found ·
3 runtime failure (an external tool, or an unexpected error; --debug shows the traceback).
"""

import argparse
import importlib
import json
import os
import re
import sqlite3
import sys
import traceback
from datetime import date
from pathlib import Path

from . import __version__, abmine, catalog, collect, datapack, digest, layout, model, numbers, probe, questions, rawdata, readouts, release, runs, similar, store, watch

SOURCE_ROOT = Path(__file__).resolve().parent.parent


def is_library(path):
    """A library is a folder holding entries/ and instruments/."""
    return (path / "entries").is_dir() and (path / "instruments").is_dir()


def find_root(override=None, cwd=None):
    """--library, then $RND_ROOT, then the nearest library at or above cwd, then the source checkout."""
    explicit = override or os.environ.get("RND_ROOT")
    if explicit:
        return Path(explicit).resolve()
    here = Path(cwd or Path.cwd()).resolve()
    for d in (here, *here.parents):
        if is_library(d):
            return d
    return SOURCE_ROOT if is_library(SOURCE_ROOT) else None


ROOT = find_root()


def fail(code, message, hint="", exit_code=2):
    print(f"error: {code}: {message}", file=sys.stderr)
    if hint:
        print(f"  hint: {hint}", file=sys.stderr)
    return exit_code


def report(problems, quiet_warnings=False):
    for p in problems:
        if p.level == "error" or not quiet_warnings:
            print(str(p), file=sys.stderr)


class MissingExtraError(Exception):
    def __init__(self, module, extra):
        super().__init__(f"optional dependency {module!r} is not installed")
        self.code = "MISSING_EXTRA"
        self.hint = f'install the opt-in extra: pip install "mcptoolshop-rnd[{extra}]"'


def require_extra(module, extra):
    """Lazily import an opt-in extra's module, or fail with MISSING_EXTRA and an install hint."""
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        raise MissingExtraError(module, extra) from exc


def _in_instruments(path):
    if ROOT is None or path is None:
        return False
    return Path(path).resolve().is_relative_to((ROOT / "instruments").resolve())


def open_db(args):
    target = args.db or store.default_db(ROOT)
    if _in_instruments(target):
        sys.exit(fail("INSTRUMENTS_PROTECTED", f"refusing to write index under instruments/: {target}",
                      "instrument files are edited only by the R&D seat in a reviewed diff"))
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
    target = args.db or store.default_db(ROOT)
    if _in_instruments(target):
        return fail("INSTRUMENTS_PROTECTED", f"refusing to write index under instruments/: {target}",
                    "instrument files are edited only by the R&D seat in a reviewed diff")
    counts, problems = store.build(ROOT, args.db)
    report(problems)
    if counts is None:
        return fail("INDEX_INVALID", "build halted on errors; the previous index was kept",
                    "fix the files named above, then rebuild", 1)
    warnings = sum(p.level == "warning" for p in problems)
    print(f"built rnd.db: {counts['entries']} entries, {counts['questions']} questions, {counts['catalogs']} catalogues "
          f"({counts['catalog_items']} items), {counts['experiments']} experiment records, {counts['runs']} runs, "
          f"{counts['files']} files, {warnings} warnings")
    return 0


def cmd_check(args):
    entries, problems = model.load_all(ROOT)
    _, frag_problems = release.load_fragments(ROOT)
    problems.extend(model.Problem("error", where, msg) for where, msg in frag_problems)
    problems.extend(numbers.check_all(ROOT, entries))
    known_claim_ids = {c["id"] for e in entries for c in e.claims if c["id"]}
    _, q_problems = questions.load_all(ROOT, known_claim_ids=known_claim_ids)
    problems.extend(q_problems)
    for d in catalog.catalog_dirs(ROOT):
        _, _, cat_problems = catalog.load(d)
        problems.extend(model.Problem("warning" if "no catalog.json" in p else "error", d.name, p)
                        for p in cat_problems)
    problems.extend(model.Problem("error", f"datapacks/{name}", msg) for name, msg in datapack.check_all(ROOT))
    problems.extend(model.Problem(level, where, msg)
                    for level, where, msg in layout.check(ROOT, registry_ids=layout.registry_ids(ROOT)))
    report(problems)
    errors = sum(p.level == "error" for p in problems)
    warnings = len(problems) - errors
    packs = len(datapack.manifests(ROOT))
    print(f"checked {len(entries)} entries{f' and {packs} data packs' if packs else ''}: {errors} errors, {warnings} warnings")
    return 1 if errors else 0


def cmd_search(args):
    con = open_db(args)
    query_str = " ".join(args.query)
    include_questions = not args.catalog_only and args.kind in (None, "question")
    try:
        ents, items = store.search(con, query_str, limit=args.limit, raw=args.raw,
                                   kind=args.kind, field=args.field,
                                   catalogs=not args.entries_only, entries=not args.catalog_only,
                                   exact=args.exact)
        qs = (store.search_questions(con, query_str, limit=args.limit, raw=args.raw,
                                     field=args.field, exact=args.exact)
              if include_questions else [])
    except sqlite3.OperationalError as exc:
        return fail("QUERY_INVALID", str(exc), "drop --raw to search plain words")

    for r in ents + items + qs:
        r["snip"] = " ".join(r["snip"].replace("#", " ").split())
    if not ents and not items and not qs:
        store.record_search_miss(ROOT, query_str, args.db)

    def text(_):
        if ents:
            print(f"Entries ({len(ents)})")
            for r in ents:
                print(f"  {r['id']}  [{r['kind']}/{r['relevance']}] {r['title']}")
                print(f"      {r['snip'].strip()}")
                for fc in r.get("flagged_claims", []):
                    by_txt = ", ".join(
                        f"{b['id']} ({b['entry_id']})" if b.get("entry_id") else b["id"] for b in fc["by"]
                    )
                    cid = fc["id"] or "claim"
                    if fc["state"] == "superseded":
                        print(f"      ! [superseded] {cid}: {fc['text'][:90]} — replaced by {by_txt or 'unlinked'}")
                    else:
                        tail = f" — contradicted by {by_txt}" if by_txt else ""
                        print(f"      ! [disputed] {cid}: {fc['text'][:90]}{tail}")
        if qs:
            print(f"Questions ({len(qs)})")
            for q_row in qs:
                ans = f" (answered by {', '.join(q_row['answered_by'])})" if q_row["answered_by"] else ""
                print(f"  {q_row['id']}  [question/{q_row['status']}] {q_row['title']}{ans}")
                print(f"      {q_row['snip'].strip()}")
        if items:
            print(f"Catalogue items ({len(items)})")
            for r in items:
                fit = f" fit:{r['fit']}" if r["fit"] else ""
                print(f"  {r['catalog']}:{r['name']}  ({r['family']}{fit})")
                print(f"      {r['snip'].strip()}")
        if not ents and not items and not qs:
            print("no matches")
    emit(args, {"entries": ents, "catalog_items": items, "questions": qs}, text)
    return 0


def cmd_show(args):
    con = open_db(args)
    row = con.execute("SELECT * FROM entries WHERE id = ?", (args.id,)).fetchone()
    if row is None:
        item = None
        if ":" in args.id:
            cat, name = args.id.split(":", 1)
            item = con.execute("SELECT * FROM catalog_items WHERE catalog=? AND name=?", (cat, name)).fetchone()
        if item is not None:
            data = dict(item)
            emit(args, data, lambda d: print("\n".join(f"{k}: {v}" for k, v in d.items() if v)))
            return 0
        qrow = con.execute("SELECT * FROM questions WHERE id = ?", (args.id,)).fetchone()
        if qrow is not None:
            qdata = dict(qrow)
            qdata["fields"] = json.loads(qdata["fields"] or "[]")
            qdata["tags"] = json.loads(qdata["tags"] or "[]")
            qdata["answered_by"] = json.loads(qdata["answered_by"] or "[]")

            def qtext(d):
                print(f"{d['title']}\n{d['id']} · question · status:{d['status']} · {d['date']} · {d['path']}")
                print(f"fields: {', '.join(d['fields'])}   tags: {', '.join(d['tags'])}")
                if d["answered_by"]:
                    print(f"answered_by: {', '.join(d['answered_by'])}")
                print()
                print((ROOT / d["path"]).read_text(encoding="utf-8").split("---", 2)[-1].strip())
            emit(args, qdata, qtext)
            return 0
        hits = [r[0] for r in con.execute(
            "SELECT id FROM entries WHERE id LIKE ? UNION SELECT id FROM questions WHERE id LIKE ? LIMIT 5",
            (f"%{args.id}%", f"%{args.id}%"))]
        return fail("NOT_FOUND", f"no entry {args.id!r}",
                    f"did you mean: {', '.join(hits)}" if hits else "try `rnd search <words>`")
    data = dict(row)
    data["fields"], data["tags"] = json.loads(data["fields"]), json.loads(data["tags"])
    data["extra"] = json.loads(data["extra"])
    data["sources"] = [dict(r) for r in con.execute(
        "SELECT tier, url, label FROM sources WHERE entry_id=? ORDER BY ord", (args.id,))]
    claims = []
    for r in con.execute("SELECT id, state, confidence, text, via, relations FROM claims WHERE entry_id=? ORDER BY ord",
                         (args.id,)):
        cd = dict(r)
        rels = json.loads(cd["relations"] or "{}")
        cd["relations"] = rels
        if cd["state"] == "superseded":
            cd["replaced_by"] = [
                {"id": tid, "entry_id": (con.execute("SELECT entry_id FROM claims WHERE id=?", (tid,)).fetchone() or [""])[0]}
                for tid in rels.get("superseded-by", [])
            ]
        if cd["state"] == "disputed":
            cd["contradicted_by"] = [
                {"id": tid, "entry_id": (con.execute("SELECT entry_id FROM claims WHERE id=?", (tid,)).fetchone() or [""])[0]}
                for tid in rels.get("contradicted-by", [])
            ]
        claims.append(cd)
    data["claims"] = claims
    data["linked_from"] = [r[0] for r in con.execute("SELECT src FROM links WHERE dst=?", (args.id,))]

    def text(d):
        print(f"{d['title']}\n{d['id']} · {d['kind']} · relevance:{d['relevance']} · {d['date']} · {d['path']}")
        print(f"fields: {', '.join(d['fields'])}   tags: {', '.join(d['tags'])}")
        if d["linked_from"]:
            print(f"linked from: {', '.join(d['linked_from'])}")
        for c in d["claims"]:
            cid = c["id"] or "claim"
            if c["state"] == "superseded":
                by_txt = ", ".join(
                    f"{b['id']} ({b['entry_id']})" if b.get("entry_id") else b["id"]
                    for b in c.get("replaced_by", [])
                )
                print(f"! [superseded] {cid}: {c['text']} — replaced by {by_txt or 'unlinked'}")
            elif c["state"] == "disputed":
                by_txt = ", ".join(
                    f"{b['id']} ({b['entry_id']})" if b.get("entry_id") else b["id"]
                    for b in c.get("contradicted_by", [])
                )
                tail = f" — contradicted by {by_txt}" if by_txt else ""
                print(f"! [disputed] {cid}: {c['text']}{tail}")
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
        "questions": q("SELECT count(*) FROM questions")[0][0],
        "by_kind": q("SELECT kind, count(*) FROM entries GROUP BY kind ORDER BY 2 DESC"),
        "by_relevance": q("SELECT relevance, count(*) FROM entries GROUP BY relevance ORDER BY 2 DESC"),
        "by_field": q("SELECT field, count(*) FROM entry_fields GROUP BY field ORDER BY 2 DESC, 1"),
        "sources_by_tier": q("SELECT tier, count(*) FROM sources GROUP BY tier ORDER BY 2 DESC"),
        "claims_by_confidence": q("SELECT confidence, count(*) FROM claims GROUP BY confidence ORDER BY 2 DESC"),
        "catalogs": q("SELECT name, count, substr(ref,1,12), synced_at FROM catalogs"),
    }
    if getattr(args, "usage", False):
        data["usage"] = store.read_search_misses(ROOT, args.db)

    def text(d):
        print(f"index built {d['built_at']} · {d['entries']} entries · {d['questions']} questions")
        for key in ("by_kind", "by_relevance", "by_field", "sources_by_tier", "claims_by_confidence"):
            print(f"{key}: " + ", ".join(f"{k} {n}" for k, n in d[key]))
        for name, count, ref, synced in d["catalogs"]:
            print(f"catalogue {name}: {count} items @ {ref} (synced {synced})")
        if "usage" in d:
            u = d["usage"]
            print(f"search misses ({u['path']}): {u['misses']}")
            for m in u["top_misses"]:
                print(f"  {m['count']:>4}  {m['query']}")
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


def cmd_new_experiment(args):
    try:
        written = layout.new_experiment(ROOT, args.name, args.title or args.name, args.template)
    except ValueError as exc:
        return fail("NEW_EXPERIMENT", str(exc), "pick another name, or a template from `ls site/src/content/docs/handbook`")
    for path in written:
        print(path)
    print(f"experiments/{args.name}/staging/ (gitignored: build data packs from here)")
    return 0


def cmd_layout(args):
    """Write the baseline: every file and folder over the limits today, every folder without a record, and every
    published file whose name looks private. Reasons already given in private_allow are kept."""
    old, problems = layout.load_baseline(ROOT)
    problems = [m for m in problems if "needs a reason" not in m]  # filling reasons in is what a rerun is for
    if problems:
        report([model.Problem("error", layout.BASELINE, m) for m in problems])
        return fail("BASELINE_INVALID", f"{layout.BASELINE} can't be read", "fix or remove it, then rerun", 1)
    new = layout.baseline(ROOT)
    for path in new["private_allow"]:
        new["private_allow"][path] = old["private_allow"].get(path, "")
    # Entries added by hand (a page that documents the tag) stay while their file exists.
    for path, why in old["private_allow"].items():
        if path not in new["private_allow"] and (ROOT / path).is_file():
            new["private_allow"][path] = why
    new["private_allow"] = dict(sorted(new["private_allow"].items()))
    grew = [p for p, n in new["files"].items() if p not in old["files"] or n > old["files"][p]]
    grew += [e for e, n in new["experiments"].items() if e not in old["experiments"] or n > old["experiments"][e]]
    if old["files"] or old["experiments"]:
        if grew and not args.allow_growth:
            return fail("BASELINE_GROWS", f"the baseline would grow: {', '.join(grew[:5])}{' ...' if len(grew) > 5 else ''}",
                        "move the data out, or pass --allow-growth and give the reason in the PR", 1)
    target = ROOT / layout.BASELINE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(new, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    unreasoned = [p for p, why in new["private_allow"].items() if not why]
    print(f"wrote {layout.BASELINE}: {len(new['files'])} files and {len(new['experiments'])} experiments over the "
          f"limits, {len(new['no_record'])} experiments without a record, {len(new['private_allow'])} private-looking "
          f"names ({len(unreasoned)} still need a reason)")
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


def cmd_change(args):
    try:
        rel = release.add_fragment(ROOT, args.text, level=args.level)
    except release.ReleaseError as exc:
        return fail(exc.code, str(exc), exc.hint)
    print(rel)
    return 0


def cmd_bump(args):
    fragments, frag_problems = release.load_fragments(ROOT)
    if frag_problems:
        report([model.Problem("error", w, m) for w, m in frag_problems])
        return fail("BAD_FRAGMENT", "malformed changelog fragment(s) under changes/",
                    "run `rnd check` and fix the fragment files", 1)
    try:
        if fragments:
            levels = [f["level"] for f in fragments] + ([args.level] if args.level else [])
            level = release.highest_level(levels)
            old, new = release.resolve_bump_versions(ROOT, level)
            section = release.fragments_changelog_section(new, fragments, args.note or ())
            if not args.dry_run:
                release.apply_bump(ROOT, new, section)
                for f in fragments:
                    p = ROOT / f["path"]
                    if p.exists():
                        p.unlink()
                changes_dir = ROOT / release.CHANGES_DIR
                if changes_dir.is_dir() and not any(changes_dir.iterdir()):
                    changes_dir.rmdir()
            print(f"{'would bump' if args.dry_run else 'bumped'} {old} -> {new} "
                  f"({len(fragments)} fragment(s), level {level})")
            print(section.rstrip())
            if not args.dry_run:
                print(f"\nnext: git add -A && git commit -m \"rnd {new}\" "
                      f"&& git tag -a v{new} -m \"rnd {new}\" && git push --follow-tags")
            return 0

        level = args.level or "nano"
        old, new = release.resolve_bump_versions(ROOT, level)
        since = release.last_tag(ROOT)
        section = release.changelog_section(ROOT, new, release.changes(ROOT, since), args.note or ())
        if not args.dry_run:
            release.apply_bump(ROOT, new, section)
    except release.ReleaseError as exc:
        return fail(exc.code, str(exc), exc.hint, 3 if exc.code == "GIT_FAILED" else 2)
    print(f"{'would bump' if args.dry_run else 'bumped'} {old} -> {new} (changes since {since or 'the first commit'})")
    print(section.rstrip())
    if not args.dry_run:
        print(f"\nnext: git add mcptoolshop_rnd/__init__.py CHANGELOG.md <your changes> && git commit -m \"rnd {new}\" "
              f"&& git tag -a v{new} -m \"rnd {new}\" && git push --follow-tags")
    return 0


def cmd_sync(args):
    try:
        rep = numbers.sync_files(ROOT, paths=args.paths or None, check=args.check)
    except numbers.NumbersError as exc:
        return fail(exc.code, str(exc), exc.hint, exc.exit_code)

    def text(r):
        verb = "would update" if args.check else "updated"
        for c in r["changed"]:
            print(f"{verb} {c['path']}#{c['key']}: {c['was']} -> {c['now']}")
        if not r["changed"]:
            print(f"in sync: {r['bindings']} bound number(s) across {r['checked_files']} file(s)")
        elif args.check:
            print(f"{len(r['changed'])} bound number(s) out of sync; run `rnd sync`")
    emit(args, rep, text)
    return 0 if rep["ok"] else 1


def cmd_claims(args):
    if args.action == "assign":
        if not args.entry:
            return fail("USAGE", "assign needs an entry id or path", "rnd claims assign <entry>")
        try:
            eid, rel, assigned = model.assign_claim_ids(ROOT, args.entry)
        except model.ReconcileError as exc:
            return fail(exc.code, str(exc), exc.hint, exc.exit_code)
        data = {"entry": eid, "path": rel, "assigned": assigned}
        emit(args, data, lambda d: print(
            f"{d['path']}: assigned {len(d['assigned'])} claim id(s)"
            + (f" ({', '.join(d['assigned'])})" if d["assigned"] else " (none needed)")))
        return 0

    con = open_db(args)
    sql = ("SELECT c.id, c.entry_id, c.ord, c.state, c.text, c.via, c.relations "
           "FROM claims c JOIN entries e ON e.id = c.entry_id WHERE 1=1")
    params = []
    if args.state:
        sql += " AND c.state = ?"
        params.append(args.state)
    sql += " ORDER BY e.date DESC, c.entry_id, c.ord"
    rows = []
    for r in con.execute(sql, params):
        d = dict(r)
        d["relations"] = json.loads(d["relations"] or "{}")
        rows.append(d)

    def text(rs):
        for r in rs:
            rel_parts = [f"{k}: {', '.join(v)}" for k, v in r["relations"].items() if v]
            rel_txt = f" ({'; '.join(rel_parts)})" if rel_parts else ""
            print(f"  {r['id'] or '-':<12} [{r['state']}] {r['entry_id']} — {r['text']}{rel_txt}")
        print(f"{len(rs)} claims")
    emit(args, rows, text)
    return 0


def cmd_reconcile(args):
    try:
        rep = model.reconcile_entry(ROOT, args.entry)
    except model.ReconcileError as exc:
        return fail(exc.code, str(exc), exc.hint, exc.exit_code)

    def text(r):
        for l in r["links"]:
            print(f"{l['src_id']} ({l['src_entry']}) {l['relation']} {l['dst_id']} ({l['dst_entry']})")
        print(f"reconciled {len(r['links'])} link(s) across {len(r['changed_files'])} changed file(s)")
    emit(args, rep, text)
    return 0


def cmd_similar(args):
    try:
        rep = similar.find_similar(ROOT, args.entry, limit=args.limit, db_path=args.db)
    except similar.SimilarError as exc:
        return fail(exc.code, str(exc), exc.hint, exc.exit_code)
    emit(args, rep, lambda r: print(similar.render_similar(r)))
    return 0


def cmd_digest(args):
    try:
        rep = digest.compute_digest(ROOT, args.since)
    except digest.DigestError as exc:
        return fail(exc.code, str(exc), exc.hint, exc.exit_code)
    emit(args, rep, lambda r: print(digest.render_digest(r)))
    return 0


def cmd_new_question(args):
    try:
        rel = questions.new_question(
            ROOT,
            args.title,
            fields=args.field,
            tags=args.tag,
            qid=args.id,
            today=args.date,
            status=args.status,
            answered_by=args.answered_by,
        )
    except questions.QuestionError as exc:
        return fail(exc.code, str(exc), exc.hint, exc.exit_code)
    print(rel)
    return 0


def cmd_questions(args):
    con = open_db(args)
    sql, params = "SELECT id, title, status, date, path, fields, tags, answered_by FROM questions WHERE 1=1", []
    if args.status:
        sql += " AND status = ?"
        params.append(args.status)
    if args.field:
        sql += " AND id IN (SELECT question_id FROM question_fields WHERE field = ?)"
        params.append(args.field)
    sql += " ORDER BY date DESC, id"
    rows = []
    for r in con.execute(sql, params):
        d = dict(r)
        d["fields"] = json.loads(d["fields"] or "[]")
        d["tags"] = json.loads(d["tags"] or "[]")
        d["answered_by"] = json.loads(d["answered_by"] or "[]")
        rows.append(d)

    def text(rs):
        for r in rs:
            ans = f" -> {', '.join(r['answered_by'])}" if r["answered_by"] else ""
            print(f"{r['date']}  {r['id']:<44} [{r['status']}] {r['title']}{ans}")
        print(f"{len(rs)} questions")
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


def cmd_runs(args):
    if args.action == "record":
        if not args.experiment or not args.source:
            return fail("RUNS_USAGE", "record needs --experiment and --from", "rnd runs record --experiment NAME --from outcome.json")
        try:
            outcome = json.loads(Path(args.source).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return fail("OUTCOME_UNREADABLE", f"{args.source}: {exc}", "point --from at a window's outcome.json")
        pins = {}
        for spec in args.pin or ():
            key, sep, value = spec.partition("=")
            if not sep or not key or not value:
                return fail("RUNS_USAGE", f"--pin {spec!r} is not KEY=VALUE", "for example --pin role-set=47a5882")
            pins[key] = value
        try:
            run = runs.from_outcome(outcome, id=args.id, venue=args.venue, cost_unit=args.cost_unit, date=args.date,
                                    projected_cost=args.projected_cost, raw_manifest_id=args.raw_manifest,
                                    pins=pins or None)
            action = runs.record(ROOT, args.experiment, run, replace=args.replace)
        except runs.RecordError as exc:
            return fail(exc.code, str(exc), exc.hint, 1)
        print(f"{action} run {run['id']} in experiments/{args.experiment}/experiment.json "
              f"({run['outcome']}, {run['cost']} {run['cost_unit']})")
        return 0
    con = open_db(args)
    sql, params = "SELECT * FROM runs WHERE 1=1", []
    for col, val in (("experiment", args.experiment), ("venue", args.venue), ("outcome", args.outcome),
                     ("cost_unit", args.cost_unit)):
        if val:
            sql += f" AND {col} = ?"
            params.append(val)
    if args.pin:
        for spec in args.pin:
            sql += " AND pins LIKE ?"
            params.append(f"%{spec}%")
    rows = [dict(r) for r in con.execute(sql + " ORDER BY experiment, date, id", params)]
    for r in rows:
        r["pins"] = json.loads(r["pins"] or "{}")

    def text(rs):
        for r in rs:
            print(f"{r['experiment']:<22} {r['id']:<26} {r['date']} {r['venue']:<6} {r['hardware']:<14} "
                  f"{r['cost']:>8} {r['cost_unit']:<11} {r['outcome']}")
        if not rs:
            print("no runs")
    emit(args, rows, text)
    return 0


def cmd_ledger(args):
    con = open_db(args)
    if not con.execute("SELECT 1 FROM experiments WHERE name = ?", (args.experiment,)).fetchone():
        return fail("NO_EXPERIMENT", f"no experiment record named {args.experiment!r}", "list them: rnd sql \"SELECT name FROM experiments\"")
    budgets = {r["cost_unit"]: dict(r) for r in con.execute("SELECT * FROM budgets WHERE experiment = ?", (args.experiment,))}
    excluded = {unit: set(json.loads(b["excludes"] or "[]")) for unit, b in budgets.items()}
    groups = {unit: json.loads(b["reconciled"] or "[]") for unit, b in budgets.items()}
    in_group = {unit: {rid for g in gs for rid in g["runs"]} for unit, gs in groups.items()}
    phases = {unit: json.loads(b["phases"] or "[]") for unit, b in budgets.items()}
    spent, cost_of, date_of = {}, {}, {}
    # Per phase: what each phase's own runs cost (excluded runs never count; a reconciled group counts its measured
    # total in the phase its runs fall in, which validation keeps to one).
    by_phase = {unit: {} for unit in phases}
    for r in con.execute("SELECT id, cost_unit, cost_basis, cost, date FROM runs WHERE experiment = ?", (args.experiment,)):
        date_of[r["id"]] = r["date"]
        u = spent.setdefault(r["cost_unit"], {"runs": 0, "spent": 0.0, "by_basis": {}, "outside": [], "outside_cost": 0.0})
        cost_of[r["id"]] = r["cost"]
        if r["id"] in excluded.get(r["cost_unit"], ()):
            u["outside"].append(r["id"])
            u["outside_cost"] = round(u["outside_cost"] + r["cost"], 4)
            continue
        u["runs"] += 1
        if phases.get(r["cost_unit"]):
            ph = by_phase[r["cost_unit"]].setdefault(layout.phase_of(phases[r["cost_unit"]], r["date"]),
                                                      {"spent": 0.0, "runs": 0})
            ph["runs"] += 1
            if r["id"] not in in_group.get(r["cost_unit"], ()):
                ph["spent"] = round(ph["spent"] + r["cost"], 4)
        if r["id"] in in_group.get(r["cost_unit"], ()):
            continue  # counted below, by its group's measured total
        u["spent"] = round(u["spent"] + r["cost"], 4)
        u["by_basis"][r["cost_basis"]] = round(u["by_basis"].get(r["cost_basis"], 0) + r["cost"], 4)
    rows = []
    for unit in sorted(set(budgets) | set(spent)):
        b = budgets.get(unit)
        s = spent.setdefault(unit, {"runs": 0, "spent": 0.0, "by_basis": {}, "outside": [], "outside_cost": 0.0})
        recs = []
        for g in groups.get(unit, []):
            estimated = round(sum(cost_of.get(rid, 0) for rid in g["runs"]), 4)
            s["spent"] = round(s["spent"] + g["measured"], 4)
            s["by_basis"]["reconciled"] = round(s["by_basis"].get("reconciled", 0) + g["measured"], 4)
            recs.append({"runs": len(g["runs"]), "measured": g["measured"], "runs_estimated": estimated,
                         "why": g["why"]})
            if phases.get(unit) and g["runs"]:
                ph = by_phase[unit].setdefault(layout.phase_of(phases[unit], date_of.get(g["runs"][0])),
                                               {"spent": 0.0, "runs": 0})
                ph["spent"] = round(ph["spent"] + g["measured"], 4)
        phase_rows = []
        for ph in phases.get(unit, []):
            got = by_phase[unit].get(ph["name"], {"spent": 0.0, "runs": 0})
            phase_rows.append({"name": ph["name"], "from": ph["from"], "closed": bool(ph.get("closed")),
                               "cap": ph["cap"], "set_by": ph["set_by"], "spent": got["spent"], "runs": got["runs"],
                               "left": round(ph["cap"] - got["spent"], 4)})
        rows.append({"cost_unit": unit, "cap": b["cap"] if b else None, "set_by": b["set_by"] if b else None,
                     # With phases, the budget's cap is the current phase's, so "left" is that phase's.
                     "spent": s["spent"],
                     "left": phase_rows[-1]["left"] if phase_rows else (round(b["cap"] - s["spent"], 4) if b else None),
                     "runs": s["runs"], "by_basis": s["by_basis"], "reconciled": recs,
                     "outside_cap": {"runs": sorted(s["outside"]), "cost": s["outside_cost"],
                                     "why": b["excludes_why"] if b else None},
                     "phases": phase_rows})

    def text(data):
        rs = data["units"]
        print(f"{args.experiment}: spending per cost unit, computed from its runs (never added across units)")
        for r in rs:
            if r["phases"]:
                cap = f"current phase {r['phases'][-1]['name']}: cap {r['phases'][-1]['cap']}, left {r['left']}"
            else:
                cap = f"cap {r['cap']} (set by {r['set_by']}), left {r['left']}" if r["cap"] is not None else "no budget"
            basis = ", ".join(f"{k} {v}" for k, v in sorted(r["by_basis"].items()))
            print(f"  {r['cost_unit']:<11} spent {r['spent']} over {r['runs']} runs; {cap}")
            if basis:
                print(f"              by basis: {basis}")
            for g in r["reconciled"]:
                print(f"              reconciled: {g['runs']} overlapping runs count as their measured {g['measured']} "
                      f"(their own estimates sum to {g['runs_estimated']}): {g['why']}")
            out = r["outside_cap"]
            if out["runs"]:
                print(f"              outside the cap: {out['cost']} over {', '.join(out['runs'])} ({out['why']})")
            for ph in r["phases"]:
                state = "closed" if ph["closed"] else "open"
                print(f"              phase {ph['name']} (from {ph['from']}, {state}): spent {ph['spent']} over "
                      f"{ph['runs']} runs; cap {ph['cap']} (set by {ph['set_by']}), left {ph['left']}")
        if not rs:
            print("  no budgets and no runs")
    emit(args, {"experiment": args.experiment, "units": rows}, text)
    return 0


def _reasons(path):
    """A reasons file: {"<path or folder/>": "<reason>"}; the longest matching key wins."""
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise rawdata.RawError("REASONS_SHAPE", "the reasons file must map paths to reasons")
    return data


def _classifier(reasons, auto_names):
    keys = sorted(reasons, key=len, reverse=True)

    def classify(rel):
        for k in keys:
            if rel == k or (k.endswith("/") and rel.startswith(k)):
                return reasons[k]
        if auto_names and layout.private_name(rel):
            return "sealed" if "sealed" in rel.lower() else "blind"
        return None
    return classify


def _pinned_text():
    """Every text the library holds, to tell whether a private file's hash is pinned anywhere public."""
    parts = []
    for p in layout.library_files(ROOT):
        full = ROOT / p
        if full.stat().st_size <= 4 * 1024 * 1024:
            parts.append(full.read_bytes().decode("utf-8", errors="ignore"))
    return "\n".join(parts)


def cmd_raw(args):
    public = Path(args.public) if args.public else runs.rnd_data_root(ROOT)
    if args.private:
        private = Path(args.private)
    elif ROOT is not None and is_library(ROOT):
        private = layout.private_root(ROOT)
    else:  # no library: the companion's default is beside the store
        private = Path(os.environ["RND_DATA_PRIVATE"]) if os.environ.get("RND_DATA_PRIVATE") else public.parent / "rnd-data-private"
    try:
        if args.action == "verify":
            if args.public_only and args.deep:
                return fail("RAW_USAGE", "--deep re-hashes blobs, which --public-only skips",
                            "use one: --public-only (a public clone) or --deep (the rig)")
            skipped, report = {}, {}
            problems = rawdata.verify(public, None if args.public_only or not private.is_dir() else private,
                                      deep=args.deep, run=args.run, public_only=args.public_only, skipped=skipped,
                                      report=report)
            if args.json:
                print(json.dumps(rawdata.as_json(problems, report, skipped, public_only=args.public_only), indent=1))
                return 1 if problems else 0
            for line in problems:
                print(f"error: {line}", file=sys.stderr)
            if args.public_only:
                skip = ", ".join(f"{n} in store {s}" for s, n in sorted(skipped.items())) or "none"
                print(f"verified rnd-data, public only (copies skipped: {skip}): {len(problems)} problems")
            else:
                print(f"verified rnd-data{' and rnd-data-private' if private.is_dir() else ''}: {len(problems)} problems"
                      f"{' (blobs re-hashed)' if args.deep else ''}")
            return 1 if problems else 0
        if args.action == "relicense":
            if not (args.rules and args.prefix):
                return fail("RAW_USAGE", "relicense needs --rules and --prefix",
                            "rnd raw relicense --rules docs/raw-data-rules/receipts.json --prefix receipts")
            st = rawdata.relicense(public, rawdata.load_rules(Path(args.rules)), args.prefix, dry_run=args.dry_run)
            print(("would relicense: " if args.dry_run else "relicensed: ") + ", ".join(f"{k} {v}" for k, v in st.items()))
            return 0
        if not args.source:
            return fail("RAW_USAGE", f"{args.action} needs a source folder", "rnd raw ingest <folder> --prefix receipts")
        source = Path(args.source)
        reasons = _reasons(args.reasons)
        if args.action == "ingest":
            if not args.prefix:
                return fail("RAW_USAGE", "ingest needs --prefix (the run ids' first part, e.g. receipts)")
            if args.rules:
                classify, licence_for = rawdata.rules_classifier(rawdata.load_rules(Path(args.rules)), source, reasons)
            else:
                classify, licence_for = _classifier(reasons, True), None
            st = rawdata.ingest_tree(source, public, private, args.prefix, classify,
                                     exclude=tuple(args.exclude or ()), link=args.link, dry_run=args.dry_run,
                                     commit=_git_head(), update=args.update, licence_for=licence_for)
        else:
            if not args.name:
                return fail("RAW_USAGE", "private needs --as NAME (the folder under private/)")
            st = rawdata.ingest_private(source, private, args.name, _classifier(reasons, True),
                                        pinned_text=_pinned_text(), exclude=tuple(args.exclude or ()),
                                        dry_run=args.dry_run)
    except rawdata.RawError as exc:
        return fail(exc.code, str(exc), exc.hint, 1)
    except (OSError, json.JSONDecodeError) as exc:
        return fail("RAW_IO", str(exc), "check the paths and the reasons file", 1)
    print(("would ingest: " if args.dry_run else "ingested: ") + ", ".join(f"{k} {v}" for k, v in st.items()))
    return 0


def cmd_where(args):
    con = open_db(args)
    key = args.key.strip()
    if len(key) >= 8 and all(c in "0123456789abcdef" for c in key.lower()):
        shas = [r[0] for r in con.execute("SELECT sha256 FROM files WHERE sha256 LIKE ?", (key.lower() + "%",))]
    else:
        shas = [r[0] for r in con.execute("SELECT DISTINCT sha256 FROM manifest_files WHERE path = ? OR path LIKE ?",
                                          (key, f"%/{key}"))]
    if not shas:
        return fail("NOT_FOUND", f"no file matches {key!r}", "give a SHA-256 (8+ hex) or a path inside a manifest or experiments/")
    out = []
    for sha in shas:
        f = dict(con.execute("SELECT * FROM files WHERE sha256 = ?", (sha,)).fetchone())
        f["names"] = [dict(r) for r in con.execute("SELECT manifest_id, path FROM manifest_files WHERE sha256 = ? "
                                                    "ORDER BY manifest_id, path", (sha,))]
        f["copies"] = [dict(r) for r in con.execute("SELECT store, location FROM copies WHERE sha256 = ? "
                                                     "ORDER BY store, location", (sha,))]
        out.append(f)

    def text(fs):
        for f in fs:
            print(f"{f['sha256']}  {f['bytes']} bytes  tier {f['tier']}  licence {f['licence'] or '-'}")
            for n in f["names"]:
                print(f"  as {n['manifest_id']}:{n['path']}")
            for c in f["copies"]:
                print(f"  copy {c['store']}: {c['location']}")
    emit(args, out, text)
    return 0


def _git_head():
    import subprocess
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def cmd_probe(args):
    con = open_db(args)

    def library(name):
        ents, items = store.search(con, name, limit=5, exact=True)
        return [r["id"] for r in ents] + [f"{r['catalog']}:{r['name']}" for r in items]

    reports = []
    for url in args.urls:
        try:
            reports.append(probe.probe(url, library=library))
        except probe.ProbeError as exc:
            return fail(exc.code, str(exc), exc.hint)

    def text(rs):
        for r in rs:
            print(f"{r['name']}  ({r['kind']})")
            for key, label in (("licence", "licence"), ("licence_link", "licence link"), ("latest", "latest"),
                               ("released", "released"), ("updated", "last change"), ("archived", "archived"),
                               ("gated", "gated")):
                if r.get(key) not in (None, ""):
                    print(f"  {label:<13} {r[key]}")
            if "telemetry_hits" in r:
                paths = ", ".join(r.get("telemetry_paths") or [])
                print(f"  {'telemetry':<13} {r['telemetry_hits']} code hit(s) for 'telemetry' — a lead to read, not proof"
                      + (f": {paths}" if paths else ""))
            hits = r.get("library_hits") or []
            print(f"  {'in rnd':<13} {', '.join(hits) if hits else 'nothing yet'}")
            for what, why in r["unknown"].items():
                print(f"  unknown {what}: {why}")
    emit(args, reports, text)
    return 0


def cmd_watch(args):
    listing = Path(args.list) if args.list else ROOT / "docs" / "watchlist.json"
    state_path = Path(args.state or os.environ.get("RND_WATCH_STATE") or Path.home() / ".rnd" / "watch-state.json")
    if not args.no_save and _in_instruments(state_path):
        return fail("INSTRUMENTS_PROTECTED", f"refusing to write watch state under instruments/: {state_path}",
                    "instrument files are edited only by the R&D seat in a reviewed diff")
    try:
        sources = watch.load_watchlist(listing)
        known = {s["id"] for s in sources}
        unknown_ids = sorted(set(args.only or ()) - known)
        if unknown_ids:
            return fail("WATCH_UNKNOWN_SOURCE", f"not in the watchlist: {', '.join(unknown_ids)}",
                        "the ids are in docs/watchlist.json")
        state = watch.load_state(state_path)
    except watch.WatchError as exc:
        return fail(exc.code, str(exc), exc.hint)
    rep, new_state = watch.check(sources, state, only=set(args.only or ()))
    if not args.no_save:
        watch.save_state(state_path, new_state)
    rep["state"] = "not saved (--no-save)" if args.no_save else "saved"

    def text(r):
        for row in r["sources"]:
            latest = row["latest"] or {}
            head = f"{row['id']:<20}"
            if row["unknown"]:
                print(f"{head} unknown: {row['unknown']}")
                continue
            tail = f"latest {latest.get('title') or latest.get('key') or '-'}" + (
                f" ({str(latest['date'])[:10]})" if latest.get("date") else "")
            if row.get("latest_prerelease"):
                tail += f"; pre-release {row['latest_prerelease']['key']}"
            if row["baseline"]:
                print(f"{head} baseline recorded; {tail}")
            elif not row["new"]:
                print(f"{head} nothing new; {tail}")
            else:
                print(f"{head} {len(row['new'])} new; {tail}")
                for item in row["new"]:
                    when = f"  {str(item['date'])[:10]}" if item.get("date") else ""
                    pre = " (pre-release)" if item.get("prerelease") else ""
                    print(f"  {item['title'] or item['key']}{pre}{when}  {item['url'] or ''}".rstrip())
        print(f"{r['new_total']} new item(s); {len(r['unknown'])} source(s) unknown; state {r['state']}")
    emit(args, rep, text)
    return 0


def cmd_collect(args):
    try:
        if not args.name:
            rows = []
            for exp_dir in collect.experiments(ROOT):
                spec = collect.load_spec(exp_dir)
                rows.append({"experiment": exp_dir.name, "repo": spec["repo"], "sources": len(spec["sources"])})

            def text(rs):
                if not rs:
                    print("no collected experiments (experiments/<name>/collect.json)")
                for r in rs:
                    print(f"{r['experiment']:<24} {r['repo']}  {r['sources']} source(s)")
            emit(args, rows, text)
            return 0
        rep = collect.run(ROOT, args.name, clone=Path(args.clone) if args.clone else None, check=args.check)

        def text(r):
            verb = "checked" if args.check else "wrote"
            for f in r["files"]:
                mark = "DRIFT " if f in r["drift"] else ""
                print(f"{mark}{verb} experiments/{r['experiment']}/{f}")
            if r["drift"]:
                print(f"{len(r['drift'])} file(s) differ from what {r['repo']} at the pinned commits gives; "
                      f"run `rnd collect {r['experiment']}` and commit")
            elif not args.check:
                print("rebuild the charts if any read these files: python experiments/charts/make_charts.py")
        emit(args, rep, text)
        return 0 if rep["ok"] else 1
    except collect.CollectError as exc:
        return fail(exc.code, str(exc), exc.hint)


def cmd_datapack(args):
    try:
        if args.action == "list":
            rows = []
            for path in datapack.manifests(ROOT):
                m = datapack.load(path)
                host = dict(m.get("host", {}))
                hosted = path.parent / datapack.HOSTED
                if hosted.is_file():   # where an upload landed, kept apart so the manifest hash never moves
                    host.update(datapack.load(hosted))
                rows.append({"name": m.get("name"), "version": m.get("version"), "files": m.get("totals", {}).get("files"),
                             "bytes": m.get("totals", {}).get("bytes"), "host": host,
                             "title": m.get("title")})

            def text(rs):
                for r in rs:
                    h = r["host"]
                    where = f"{h.get('kind')}:{h.get('repo')}@{(h.get('revision') or 'unpinned')[:12]}"
                    print(f"{r['name']:<28} v{r['version']:<4} {r['files']:>5} files {r['bytes']:>14,} B  {where}")
                    print(f"    {r['title']}")
                if not rs:
                    print("no data packs (datapacks/<name>/datapack.json)")
            emit(args, rows, text)
            return 0
        if args.action == "build":
            if not args.target or not args.source:
                return fail("USAGE", "build needs a pack name and --source DIR",
                            "rnd datapack build <name> --source experiments/<x>  (reads datapacks/<name>/spec.json)")
            spec_path = ROOT / datapack.DIR / args.target / "spec.json"
            spec = datapack.load(spec_path)
            source = (ROOT / args.source).resolve()
            try:
                rel = source.relative_to(ROOT.resolve()).as_posix()
            except ValueError:
                rel = source.as_posix()
            origin = {"library": "mcp-tool-shop-org/rnd", "rnd_version": __version__, "commit": _git_head(),
                      "source": rel}
            m = datapack.build(source, name=args.target, title=spec.get("title", ""),
                               description=spec.get("description", ""), include=spec.get("include", []),
                               exclude=spec.get("exclude", []), licences=spec.get("licences", []),
                               generators=spec.get("generators", []), host=spec.get("host", {}),
                               origin=origin, version=str(spec.get("version", "1")))
            path = datapack.write(m, ROOT / datapack.DIR / args.target)
            print(f"wrote {path.relative_to(ROOT).as_posix()}: {m['totals']['files']} files, "
                  f"{m['totals']['bytes']:,} bytes, manifest {m['manifest_sha256'][:12]}")
            return 0
        if args.action == "verify":
            if not args.target or not args.copy:
                return fail("USAGE", "verify needs a pack name and --copy DIR",
                            "rnd datapack verify <name> --copy <downloaded folder>")
            m = datapack.load(ROOT / datapack.DIR / args.target / datapack.MANIFEST)
            rep = datapack.verify(m, Path(args.copy))

            def text(r):
                print(f"{'PASS' if r['ok'] else 'FAIL'}  {args.target}: {r['files_ok']}/{len(m.get('files', []))} files match")
                for p in r["manifest_problems"]:
                    print(f"  manifest: {p}")
                for f in r["missing"]:
                    print(f"  missing: {f}")
                for f in r["changed"]:
                    print(f"  changed: {f}")
            emit(args, rep, text)
            return 0 if rep["ok"] else 1
    except datapack.DatapackError as exc:
        return fail(exc.code, str(exc), exc.hint)
    return 0


def cmd_abmine(args):
    """Analyse an A/B record of greedy generations with top-K logprobs (no GPU, no server)."""
    try:
        records = abmine.load_record_file(args.record)
    except (OSError, abmine.AbmineError) as exc:
        return fail("ABMINE_RECORD", str(exc), "the record is JSON lines with kind \"result\" rows (arm or block, prompt, tokens, top)")
    if not records:
        return fail("ABMINE_EMPTY", f"no result rows in {args.record}", "the record needs rows with kind \"result\"")
    logs = {}
    for spec in args.log or ():
        arm, sep, path = spec.partition("=")
        if not sep or not arm or not path:
            return fail("ABMINE_LOG", f"--log {spec!r} is not ARM=PATH", "for example --log sandbox=E:/runs/sandbox-11500.log")
        try:
            logs[arm] = Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return fail("ABMINE_LOG", str(exc), "check the log path")
    arms = args.arm or None
    unknown = sorted(set((arms or []) + ([args.reference] if args.reference else [])) - set(records))
    if unknown:
        return fail("ABMINE_ARM", f"not in the record: {', '.join(unknown)}", f"the record's arms are {', '.join(sorted(records))}")
    rep = abmine.analyze(records, logs, reference=args.reference, arms=arms)
    emit(args, rep, lambda r: print(abmine.render(r)))
    return 0


# ---------------------------------------------------------------- parser

def build_parser():
    p = argparse.ArgumentParser(prog="rnd", description="Search and grow the studio R&D library.")
    p.add_argument("--library", metavar="DIR",
                   help="the library checkout (default: $RND_ROOT, else the nearest folder with entries/ and instruments/)")
    p.add_argument("--db", help="index path (default: rnd.db in the library, or $RND_DB)")
    p.add_argument("--debug", action="store_true", help="show the full traceback on an unexpected error")
    p.add_argument("--version", action="version", version=f"rnd {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help_text, json_flag=True):
        sp = sub.add_parser(name, help=help_text, description=help_text)
        sp.set_defaults(fn=fn)
        if json_flag:
            sp.add_argument("--json", action="store_true", help="machine-readable output")
        return sp

    add("build", cmd_build, "rebuild rnd.db from entries/, instruments/, questions/ and catalogs/", json_flag=False)
    add("check", cmd_check, "validate every file (entries, fragments, bound numbers, questions, packs, layout)", json_flag=False)

    s = add("search", cmd_search, "full-text search across entries, questions and catalogues")
    s.add_argument("query", nargs="+")
    s.add_argument("--limit", type=int, default=10)
    s.add_argument("--kind", choices=model.KINDS)
    s.add_argument("--field")
    s.add_argument("--entries-only", action="store_true")
    s.add_argument("--catalog-only", action="store_true")
    s.add_argument("--raw", action="store_true", help="pass the query to FTS5 unquoted (AND/OR/NEAR, prefix*)")
    s.add_argument("--exact", action="store_true",
                   help="whole words in the same case, no stemming: `PAIR` finds the product, not 'pairs'")

    s = add("show", cmd_show, "show one entry, question or <catalog>:<item>")
    s.add_argument("id")

    s = add("list", cmd_list, "list entries, newest first")
    s.add_argument("--kind", choices=model.KINDS)
    s.add_argument("--relevance", choices=model.RELEVANCE)
    s.add_argument("--status", choices=model.STATUS)
    s.add_argument("--field")
    s.add_argument("--tag")

    s = add("tools", cmd_tools, "list the studio instruments this seat can use")
    s.add_argument("--status", choices=model.INSTRUMENT_STATUS)

    s = add("stats", cmd_stats, "counts by kind, field, source tier, claim confidence and optional local search misses")
    s.add_argument("--usage", action="store_true", help="include local zero-hit search count and most frequent misses")

    s = add("new", cmd_new, "scaffold a new entry file from the template", json_flag=False)
    s.add_argument("title")
    s.add_argument("--kind", choices=model.KINDS, default="finding")
    s.add_argument("--relevance", choices=model.RELEVANCE, default="reference")
    s.add_argument("--field", action="append")
    s.add_argument("--tag", action="append")
    s.add_argument("--id")
    s.add_argument("--date")

    s = add("new-question", cmd_new_question, "scaffold a new question file under questions/", json_flag=False)
    s.add_argument("title")
    s.add_argument("--field", action="append")
    s.add_argument("--tag", action="append")
    s.add_argument("--id")
    s.add_argument("--date")
    s.add_argument("--status", choices=questions.STATUSES, default="open")
    s.add_argument("--answered-by", action="append", metavar="CLAIM_ID",
                   help="existing claim id(s) answering this question (repeatable)")

    s = add("questions", cmd_questions, "list question files under questions/")
    s.add_argument("--status", choices=questions.STATUSES)
    s.add_argument("--field")

    s = add("claims", cmd_claims, "list claims with id/state/relations, or assign stable claim ids to an entry")
    s.add_argument("action", nargs="?", choices=("list", "assign"), default="list")
    s.add_argument("entry", nargs="?", help="assign: entry id or file path")
    s.add_argument("--state", choices=model.CONFIDENCE, help="list: filter by claim state")

    s = add("reconcile", cmd_reconcile,
            "propagate supersedes/contradicts/supports links from an entry to the older claims it cites")
    s.add_argument("entry", help="entry id or file path")

    s = add("similar", cmd_similar,
            "list claims in other entries closest to each claim of one entry (read-only FTS5)")
    s.add_argument("entry", help="entry id or file path")
    s.add_argument("--limit", type=int, default=5, help="closest claims per claim (default: 5)")

    s = add("digest", cmd_digest,
            "summarize entries, claims and questions changed since a git ref or YYYY-MM-DD date (read-only)")
    s.add_argument("--since", required=True, metavar="REF_OR_DATE",
                   help="git ref (tag, branch, commit SHA) or YYYY-MM-DD date (first-parent commit on HEAD at or before that day)")

    s = add("sync", cmd_sync, "rewrite bound numbers in Markdown files from experiments/<id>/results.json")
    s.add_argument("paths", nargs="*", help="files or folders to sync (default: entries, questions, briefs, experiments)")
    s.add_argument("--check", action="store_true", help="change nothing; exit 1 if any bound literal differs")

    s = add("new-experiment", cmd_new_experiment,
            "scaffold experiments/<name>/ with experiment.json, data/, results/, scripts/ and a gitignored staging/",
            json_flag=False)
    s.add_argument("name")
    s.add_argument("--title", help="the README's title (default: the name)")
    s.add_argument("--template", help="the handbook page the design follows, e.g. model-comparisons")

    s = add("layout", cmd_layout,
            "write docs/layout.json, the baseline of files and folders that predate the size and record rules",
            json_flag=False)
    s.add_argument("action", choices=("baseline",))
    s.add_argument("--allow-growth", action="store_true",
                   help="let the baseline grow (a reviewed change: say why in the PR)")

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

    s = add("change", cmd_change, "record a changelog fragment under changes/ without touching the version or CHANGELOG.md",
            json_flag=False)
    s.add_argument("text", help="one-line changelog entry text")
    s.add_argument("--level", default="nano", choices=release.LEVELS,
                   help="bump level for this fragment (default: nano)")

    s = add("bump", cmd_bump,
            "consume fragments under changes/ (or raise the version directly) and write one CHANGELOG section",
            json_flag=False)
    s.add_argument("level", nargs="?", default=None, choices=release.LEVELS,
                   help="major|minor|patch: the tool; micro: library structure; nano: library content (default when no fragments)")
    s.add_argument("--note", action="append", help="an extra CHANGELOG line (repeatable)")
    s.add_argument("--dry-run", action="store_true", help="print the new version and CHANGELOG section only")

    s = add("datapack", cmd_datapack, "build, list or verify data packs (bulk data hosted outside the clone)")
    s.add_argument("action", choices=("list", "build", "verify"))
    s.add_argument("target", nargs="?", help="pack name (folder under datapacks/)")
    s.add_argument("--source", help="build: the folder the files come from, relative to the library")
    s.add_argument("--copy", help="verify: a downloaded copy of the pack")

    s = add("probe", cmd_probe,
            "licence, latest release, gating, telemetry hits and library hits for a GitHub repo, "
            "Hugging Face model, PyPI project or npm package")
    s.add_argument("urls", nargs="+", metavar="url")

    s = add("collect", cmd_collect,
            "copy an experiment's trimmed records from a tool repository at pinned commits (experiments/<name>/collect.json)")
    s.add_argument("name", nargs="?", help="experiment folder; omit to list the collected experiments")
    s.add_argument("--clone", help="the source repository's clone (default: ../<sibling> next to the library)")
    s.add_argument("--check", action="store_true",
                   help="recompute every output and exit 1 if any differs from the committed file")

    s = add("watch", cmd_watch,
            "check the watchlist's sources (releases, commits, models, feeds, pages) for items new since the last check")
    s.add_argument("--list", help="the watchlist (default: docs/watchlist.json in the library)")
    s.add_argument("--state", help="the state file (default: $RND_WATCH_STATE, else ~/.rnd/watch-state.json)")
    s.add_argument("--only", action="append", metavar="ID", help="check one source (repeatable)")
    s.add_argument("--no-save", action="store_true", help="report without recording what was seen")

    s = add("abmine", cmd_abmine,
            "ab_dataminer: where and how much the arms of an A/B run differ, from a record of greedy generations "
            "with top-K logprobs (Δz per step, forks, drift, tie-breaks, OLLAMA_DEBUG logs); no GPU")
    s.add_argument("action", choices=("analyze",))
    s.add_argument("record", help="the run's JSON-lines record")
    s.add_argument("--log", action="append", metavar="ARM=PATH", help="an arm's OLLAMA_DEBUG server log (repeatable)")
    s.add_argument("--arm", action="append", help="limit to these arms, in this order; the first is the reference of each pair")
    s.add_argument("--reference", help="an arm to break ties at the other arms' forks")

    s = add("runs", cmd_runs, "list recorded runs, or record one from a window's outcome.json into experiment.json")
    s.add_argument("action", nargs="?", default="list", choices=("list", "record"))
    s.add_argument("--experiment", help="list: filter; record: the experiment folder to write to")
    s.add_argument("--from", dest="source", metavar="OUTCOME_JSON", help="record: the window's outcome.json")
    s.add_argument("--venue", choices=layout.VENUES, help="list: filter; record: when outcome.json lacks it")
    s.add_argument("--cost-unit", choices=layout.COST_UNITS, help="list: filter; record: when outcome.json lacks it")
    s.add_argument("--outcome", choices=layout.OUTCOMES, help="list: filter")
    s.add_argument("--date", help="record: YYYY-MM-DD, when outcome.json lacks it")
    s.add_argument("--id", help="record: the run id, when outcome.json has no window")
    s.add_argument("--projected-cost", type=float, help="record: the projection made before the run")
    s.add_argument("--raw-manifest", help="record: the run's manifest id in rnd-data")
    s.add_argument("--pin", action="append", metavar="KEY=VALUE",
                   help="record: a pin (repeatable); list: a substring of the pins to filter on")
    s.add_argument("--replace", action="store_true", help="record: overwrite a run already recorded with this id")

    s = add("ledger", cmd_ledger, "an experiment's spending per cost unit against its budgets, computed from its runs")
    s.add_argument("experiment")

    s = add("raw", cmd_raw, "ingest raw run outputs into rnd-data (public) and rnd-data-private, verify them, or "
            "reapply a rules file's licences", json_flag=False)
    s.add_argument("action", choices=("ingest", "private", "verify", "relicense"))
    s.add_argument("source", nargs="?", help="ingest/private: the folder to read (never changed)")
    s.add_argument("--prefix", help="ingest, relicense: the run ids' first part, e.g. receipts")
    s.add_argument("--as", dest="name", help="private: the folder under private/ in rnd-data-private")
    s.add_argument("--reasons", help="a JSON file mapping paths or folder/ prefixes to a private reason")
    s.add_argument("--rules", help="ingest: a rules file (deny by default for content), e.g. docs/raw-data-rules/receipts.json; "
                   "relicense: the file whose licences to reapply")
    s.add_argument("--exclude", action="append", help="a path or folder to leave out (repeatable)")
    s.add_argument("--link", action="store_true",
                   help="ingest: hard-link blobs instead of copying, only from a read-only snapshot on the store's volume")
    s.add_argument("--update", action="store_true",
                   help="ingest: replace a run whose source changed since it was ingested (git keeps the old manifest)")
    s.add_argument("--dry-run", action="store_true", help="plan and count; write nothing")
    s.add_argument("--public", help="the rnd-data checkout (default: $RND_DATA, else ../rnd-data)")
    s.add_argument("--private", help="the rnd-data-private checkout (default: $RND_DATA_PRIVATE, else ../rnd-data-private)")
    s.add_argument("--run", help="verify: one run id")
    s.add_argument("--deep", action="store_true", help="verify: re-hash every blob, not only check its size")
    s.add_argument("--json", action="store_true",
                   help="verify: the result as JSON (counts, the checked public git files, problems as {rule, where})")
    s.add_argument("--public-only", action="store_true",
                   help="verify: only what a public clone can check (CI): git copies, plus files no manifest names, the "
                        "private tag, private-looking names and machine paths; skips the blob store and the companion")

    s = add("where", cmd_where, "where a file's bytes are: every name and copy, by SHA-256 or path")
    s.add_argument("key", metavar="SHA256_OR_PATH")

    s = add("sql", cmd_sql, "run a read-only SQL query against the index")
    s.add_argument("query")
    return p


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    global ROOT
    if args.library:
        ROOT = find_root(args.library)
    # `rnd raw` works on rnd-data alone, such as in rnd-data's CI, when the store is named.
    raw_alone = args.cmd == "raw" and (getattr(args, "public", None) or os.environ.get("RND_DATA"))
    if args.cmd not in ("readouts", "abmine") and not raw_alone and (ROOT is None or not is_library(ROOT)):
        return fail("NO_LIBRARY", "no rnd library here (a folder with entries/ and instruments/)",
                    "run inside a clone of mcp-tool-shop-org/rnd, or pass --library / set RND_ROOT")
    try:
        return args.fn(args) or 0
    except MissingExtraError as exc:
        return fail(exc.code, str(exc), exc.hint)
    except KeyboardInterrupt:
        return fail("INTERRUPTED", "stopped by the user", exit_code=3)
    except Exception as exc:  # last resort: a structured error, never a raw stack by default
        if args.debug:
            traceback.print_exc()
        return fail("INTERNAL", f"{type(exc).__name__}: {exc}",
                    "rerun with --debug for the traceback, and report it if it persists", 3)
