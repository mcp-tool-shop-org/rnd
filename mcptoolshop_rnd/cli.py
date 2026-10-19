"""rnd — the R&D seat's command line.

Exit codes: 0 ok · 1 invalid library files · 2 usage or not found ·
3 runtime failure (an external tool, or an unexpected error; --debug shows the traceback).
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import traceback
from datetime import date
from pathlib import Path

from . import __version__, abmine, catalog, collect, datapack, layout, model, probe, readouts, release, store, watch

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
    try:
        ents, items = store.search(con, " ".join(args.query), limit=args.limit, raw=args.raw,
                                   kind=args.kind, field=args.field,
                                   catalogs=not args.entries_only, entries=not args.catalog_only,
                                   exact=args.exact)
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
    if problems:
        report([model.Problem("error", layout.BASELINE, m) for m in problems])
        return fail("BASELINE_INVALID", f"{layout.BASELINE} can't be read", "fix or remove it, then rerun", 1)
    new = layout.baseline(ROOT)
    for path in new["private_allow"]:
        new["private_allow"][path] = old["private_allow"].get(path, "")
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


def cmd_bump(args):
    try:
        old = release.read_version(ROOT)
        new = release.bump(old, args.level)
        since = release.last_tag(ROOT)
        section = release.changelog_section(ROOT, new, release.changes(ROOT, since), args.note or ())
        if not args.dry_run:
            release.write_version(ROOT, new)
            release.insert_changelog(ROOT, section)
    except release.ReleaseError as exc:
        return fail(exc.code, str(exc), exc.hint, 3 if exc.code == "GIT_FAILED" else 2)
    print(f"{'would bump' if args.dry_run else 'bumped'} {old} -> {new} (changes since {since or 'the first commit'})")
    print(section.rstrip())
    if not args.dry_run:
        print(f"\nnext: git add mcptoolshop_rnd/__init__.py CHANGELOG.md <your changes> && git commit -m \"rnd {new}\" "
              f"&& git tag -a v{new} -m \"rnd {new}\" && git push --follow-tags")
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
    s.add_argument("--exact", action="store_true",
                   help="whole words in the same case, no stemming: `PAIR` finds the product, not 'pairs'")

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

    s = add("bump", cmd_bump, "raise the version (default: the nano segment) and add a CHANGELOG section", json_flag=False)
    s.add_argument("level", nargs="?", default="nano", choices=release.LEVELS,
                   help="major|minor|patch: the tool; micro: library structure; nano: library content (default)")
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
    if args.cmd not in ("readouts", "abmine") and (ROOT is None or not is_library(ROOT)):
        return fail("NO_LIBRARY", "no rnd library here (a folder with entries/ and instruments/)",
                    "run inside a clone of mcp-tool-shop-org/rnd, or pass --library / set RND_ROOT")
    try:
        return args.fn(args) or 0
    except KeyboardInterrupt:
        return fail("INTERRUPTED", "stopped by the user", exit_code=3)
    except Exception as exc:  # last resort: a structured error, never a raw stack by default
        if args.debug:
            traceback.print_exc()
        return fail("INTERNAL", f"{type(exc).__name__}: {exc}",
                    "rerun with --debug for the traceback, and report it if it persists", 3)
