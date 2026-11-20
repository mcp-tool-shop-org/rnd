"""Entry files: parsing and validation.

An entry is a Markdown file with frontmatter. Sources and claims live in the
body as tagged list items so the file stays readable in any editor:

    ## Sources
    - [primary] https://developer.nvidia.com/blog/cuda-graphs/ — NVIDIA blog
    ## Claims
    - [unverified] Rubin is compute capability 10.7 (via: aggregator summary)
"""

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import frontmatter

KINDS = (
    "finding",     # a fact or result learned from a source
    "concept",     # an idea, technique or principle worth knowing
    "release",     # a product/toolkit/library release
    "paper",       # a paper or formal study
    "tool",        # an external tool, library or catalogue item
    "catalog",     # a pointer to an ingested catalogue (see catalogs/)
    "rig-fact",    # a measured fact about our own machines
    "event",       # a talk, webinar, conference
    "question",    # an open question the seat is tracking
    "decision",    # a decision taken on the strength of research
    "instrument",  # a studio tool/protocol the seat can use (instruments/)
)
RELEVANCE = ("act", "watch", "reference")
STATUS = ("active", "draft", "superseded")
TIERS = ("primary", "secondary", "aggregator", "user", "rig")
CONFIDENCE = ("verified", "unverified", "disputed", "wrong", "superseded")
INSTRUMENT_STATUS = ("shipped", "planned", "retired")

FORWARD_RELATIONS = ("supersedes", "contradicts", "supports")
REVERSE_RELATIONS = ("superseded-by", "contradicted-by", "supported-by")
ALL_RELATIONS = FORWARD_RELATIONS + REVERSE_RELATIONS
INVERSE_OF = {
    "supersedes": "superseded-by",
    "contradicts": "contradicted-by",
    "supports": "supported-by",
    "superseded-by": "supersedes",
    "contradicted-by": "contradicts",
    "supported-by": "supports",
}
RECONCILE_STATE = {"supersedes": "superseded", "contradicts": "disputed", "supports": None}

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
CLAIM_ID_RE = re.compile(r"^c-[a-z0-9][a-z0-9._-]*$")
ITEM_RE = re.compile(r"^\s*[-*]\s+\[([A-Za-z-]+)\]\s+(.+?)\s*$")
CLAIM_LINE_RE = re.compile(r"^(\s*[-*]\s+)\[([A-Za-z-]+)\](\s+)(.+?)(\r?\n?)$")
CLAIM_PREFIX_RE = re.compile(r"^\[(c-[^\]]*)\](?!\()\s*(.*)$")
CLAUSE_RE = re.compile(
    r"\((via|supersedes|contradicts|supports|superseded-by|contradicted-by|supported-by):\s*([^)]*)\)\s*$"
)
URL_RE = re.compile(r"https?://[^\s)>\]]+")
MDLINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
VIA_RE = re.compile(r"\(via:\s*([^)]+)\)\s*$")
WIKILINK_RE = re.compile(r"\[\[([a-z0-9][a-z0-9._-]*)\]\]")
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.M)


class ReconcileError(Exception):
    def __init__(self, code, message, hint="", exit_code=1):
        super().__init__(message)
        self.code, self.hint, self.exit_code = code, hint, exit_code


@dataclass
class Problem:
    level: str  # "error" halts the build; "warning" is reported
    path: str
    message: str

    def __str__(self):
        return f"{self.level}: {self.path}: {self.message}"


@dataclass
class Entry:
    id: str
    path: str
    title: str
    date: str
    kind: str
    relevance: str
    status: str
    fields: list
    tags: list
    body: str
    sources: list = field(default_factory=list)   # dicts: tier, url, label
    claims: list = field(default_factory=list)    # dicts: confidence, text, via
    links: list = field(default_factory=list)
    relevance_note: str = ""
    extra: dict = field(default_factory=dict)


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    return [str(value)]


def sections(body):
    """Map lower-cased '## heading' -> section text."""
    out = {}
    matches = list(HEADING_RE.finditer(body))
    for n, m in enumerate(matches):
        end = matches[n + 1].start() if n + 1 < len(matches) else len(body)
        out[m.group(1).strip().lower()] = body[m.end():end].strip()
    return out


def parse_sources(text):
    items = []
    for line in text.splitlines():
        m = ITEM_RE.match(line)
        if not m:
            continue
        tier, rest = m.group(1).lower(), m.group(2)
        md = MDLINK_RE.search(rest)
        if md:
            url = md.group(2)
            label = (rest[:md.start()] + md.group(1) + rest[md.end():]).strip(" —-:")
        else:
            u = URL_RE.search(rest)
            url = u.group(0) if u else ""
            label = (rest[:u.start()] + rest[u.end():] if u else rest).strip(" —-:")
        items.append({"tier": tier, "url": url, "label": label})
    return items


def make_claim_id(entry_id, text, taken=frozenset()):
    """Stable deterministic claim id (`c-<hex>`) derived from (entry_id, sentence), avoiding collisions."""
    base = f"{entry_id}\n{text.strip()}".encode("utf-8")
    digest = hashlib.sha256(base).hexdigest()
    for n in (8, 10, 12, 16):
        cand = f"c-{digest[:n]}"
        if cand not in taken:
            return cand
    salt = 1
    while True:  # pragma: no cover
        salted = f"{entry_id}\n{salt}\n{text.strip()}".encode("utf-8")
        cand = f"c-{hashlib.sha256(salted).hexdigest()[:8]}"
        if cand not in taken:
            return cand
        salt += 1


def parse_claim_line(line):
    """Parse one claim list item line into a dict, or return None if the line is not a claim item."""
    m = ITEM_RE.match(line)
    if not m:
        return None
    confidence, rest = m.group(1).lower(), m.group(2)
    claim_id = ""
    pm = CLAIM_PREFIX_RE.match(rest)
    if pm:
        claim_id = pm.group(1).strip()
        rest = pm.group(2).strip()
    peeled = []
    cur = rest.rstrip()
    while True:
        cm = CLAUSE_RE.search(cur)
        if not cm:
            break
        peeled.append((cm.group(1), cm.group(2)))
        cur = cur[:cm.start()].rstrip()
    via = ""
    relations = {}
    for key, val in reversed(peeled):
        if key == "via":
            via = val.strip()
        else:
            targets = [t.strip() for t in val.split(",") if t.strip()]
            bucket = relations.setdefault(key, [])
            for t in targets:
                if t not in bucket:
                    bucket.append(t)
    return {
        "id": claim_id,
        "state": confidence,
        "confidence": confidence,
        "text": cur,
        "via": via,
        "relations": relations,
    }


def parse_claims(text):
    items = []
    for line in text.splitlines():
        parsed = parse_claim_line(line)
        if parsed is not None:
            items.append(parsed)
    return items


def load(path, root):
    """Parse one entry file. Returns (entry_or_None, problems)."""
    rel = Path(path).relative_to(root).as_posix()
    problems = []
    try:
        text = Path(path).read_text(encoding="utf-8")
        meta, body = frontmatter.read(text)
    except (OSError, UnicodeDecodeError, frontmatter.FrontmatterError) as exc:
        return None, [Problem("error", rel, f"unreadable: {exc}")]

    def err(msg):
        problems.append(Problem("error", rel, msg))

    entry_id = str(meta.get("id") or Path(path).stem)
    if not ID_RE.match(entry_id):
        err(f"id {entry_id!r} must be lower-case letters, digits, '.', '_' or '-'")
    title = str(meta.get("title") or "").strip()
    if not title:
        err("missing 'title'")
    date = str(meta.get("date") or "")
    if not DATE_RE.match(date):
        err(f"'date' must be YYYY-MM-DD, got {date!r}")
    kind = str(meta.get("kind") or "")
    if kind not in KINDS:
        err(f"'kind' must be one of {', '.join(KINDS)}; got {kind!r}")
    relevance = str(meta.get("relevance") or "")
    if relevance not in RELEVANCE:
        err(f"'relevance' must be one of {', '.join(RELEVANCE)}; got {relevance!r}")
    status = str(meta.get("status") or "active")
    if status not in STATUS:
        err(f"'status' must be one of {', '.join(STATUS)}; got {status!r}")
    fields = _as_list(meta.get("fields"))
    if not fields:
        err("'fields' needs at least one research field, e.g. [gpu-computing]")
    tags = _as_list(meta.get("tags"))

    secs = sections(body)
    sources = parse_sources(secs.get("sources", ""))
    for s in sources:
        if s["tier"] not in TIERS:
            err(f"source tier [{s['tier']}] must be one of {', '.join(TIERS)}")
        if not s["url"] and s["tier"] not in ("user", "rig"):
            err(f"[{s['tier']}] source has no URL: {s['label'][:60]!r}")
    claims = parse_claims(secs.get("claims", ""))
    for c in claims:
        if c["confidence"] not in CONFIDENCE:
            err(f"claim tag [{c['confidence']}] must be one of {', '.join(CONFIDENCE)}")
        if c["confidence"] in ("verified", "wrong") and not c["via"]:
            err(f"[{c['confidence']}] claim needs '(via: who/what, date)': {c['text'][:60]!r}")
        if c["id"] and not CLAIM_ID_RE.match(c["id"]):
            err(f"claim id {c['id']!r} must match 'c-<id>' (lower-case letters, digits, '.', '_' or '-')")
        for rel_name, targets in c["relations"].items():
            if not targets:
                err(f"claim relation '({rel_name}: ...)' needs at least one claim id")
            for tid in targets:
                if c["id"] and tid == c["id"]:
                    err(f"claim {c['id']} cannot state '{rel_name}' on itself")

    known = {"id", "title", "date", "kind", "relevance", "status", "fields", "tags"}
    extra = {k: v for k, v in meta.items() if k not in known}
    if kind == "instrument":
        inst_status = str(extra.get("instrument_status") or "")
        if inst_status not in INSTRUMENT_STATUS:
            err(f"instrument needs 'instrument_status' in {', '.join(INSTRUMENT_STATUS)}")
        if not extra.get("invoke"):
            err("instrument needs 'invoke' (how a session calls it)")
    if kind != "rig-fact" and kind != "instrument" and not sources:
        problems.append(Problem("warning", rel, "no '## Sources' items"))

    entry = Entry(
        id=entry_id, path=rel, title=title, date=date, kind=kind,
        relevance=relevance, status=status, fields=fields, tags=tags,
        body=body, sources=sources, claims=claims,
        links=sorted(set(WIKILINK_RE.findall(body))),
        relevance_note=secs.get("studio relevance", ""), extra=extra,
    )
    return entry, problems


ENTRY_DIRS = ("entries", "instruments")


def entry_paths(root):
    for d in ENTRY_DIRS:
        base = Path(root) / d
        if base.is_dir():
            yield from sorted(p for p in base.rglob("*.md") if not p.name.startswith("_"))


def load_all(root):
    entries, problems, seen = [], [], {}
    for path in entry_paths(root):
        entry, probs = load(path, root)
        problems.extend(probs)
        if entry is None:
            continue
        if entry.id in seen:
            problems.append(Problem("error", entry.path, f"duplicate id {entry.id!r} (also {seen[entry.id]})"))
            continue
        seen[entry.id] = entry.path
        entries.append(entry)
    ids = set(seen)
    seen_claims = {}
    for e in entries:
        for link in e.links:
            if link not in ids:
                problems.append(Problem("warning", e.path, f"[[{link}]] points at no entry"))
        for c in e.claims:
            cid = c["id"]
            if not cid:
                continue
            if cid in seen_claims:
                problems.append(Problem(
                    "error", e.path,
                    f"duplicate claim id {cid!r} (also in {seen_claims[cid][0].path})"))
            else:
                seen_claims[cid] = (e, c)
    for e in entries:
        for c in e.claims:
            cid = c["id"]
            for rel_name, targets in c["relations"].items():
                inv = INVERSE_OF[rel_name]
                for tid in targets:
                    if tid == cid:
                        continue
                    target = seen_claims.get(tid)
                    if target is None:
                        problems.append(Problem(
                            "error", e.path,
                            f"claim {cid or '<unassigned>'} states '{rel_name}: {tid}', which does not exist; "
                            f"run `rnd reconcile {e.id}`"))
                        continue
                    other_entry, other_claim = target
                    hint_entry = e.id if rel_name in FORWARD_RELATIONS else other_entry.id
                    if not cid:
                        problems.append(Problem(
                            "error", e.path,
                            f"claim with '{rel_name}: {tid}' has no id (link present on one side only); "
                            f"run `rnd reconcile {hint_entry}`"))
                        continue
                    if cid not in other_claim["relations"].get(inv, []):
                        problems.append(Problem(
                            "error", e.path,
                            f"claim {cid} states '{rel_name}: {tid}', but {tid} in {other_entry.id} lacks "
                            f"'{inv}: {cid}' (link present on one side only); run `rnd reconcile {hint_entry}`"))
    return entries, problems


def _claims_section_line_range(lines):
    """Return (start, end) line indices for the '## Claims' body in splitlines(keepends=True)."""
    i = 0
    if lines and lines[0].strip() == "---":
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            i += 1
        i += 1
    while i < len(lines):
        m = HEADING_RE.match(lines[i].rstrip("\r\n"))
        if m and m.group(1).strip().lower() == "claims":
            start = i + 1
            end = start
            while end < len(lines) and not HEADING_RE.match(lines[end].rstrip("\r\n")):
                end += 1
            return start, end
        i += 1
    return None


def _insert_inverse_clause(rest, inv_rel, src_id):
    """Add `src_id` into a trailing `(inv_rel: ...)` clause or append one, leaving the sentence untouched."""
    trimmed = rest.rstrip()
    clauses = []
    cur = trimmed
    while True:
        cm = CLAUSE_RE.search(cur)
        if not cm:
            break
        clauses.append((cm.start(), cm.end(), cm.group(1), cm.group(2)))
        cur = cur[:cm.start()].rstrip()
    for start, end, key, val in clauses:
        if key == inv_rel:
            tokens = [t.strip() for t in val.split(",") if t.strip()]
            if src_id in tokens:
                return rest
            updated = f"({inv_rel}: {', '.join([*tokens, src_id])})"
            return trimmed[:start] + updated + trimmed[end:]
    return f"{trimmed} ({inv_rel}: {src_id})"


def _rewrite_claim_line(raw_line, new_state=None, assign_id="", add_inverse=()):
    """Edit one claim line in place, preserving its sentence and every non-claim detail."""
    m = CLAIM_LINE_RE.match(raw_line)
    if not m:
        return raw_line
    prefix, old_state, ws, rest, eol = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
    state_out = new_state or old_state
    id_prefix = f"[{assign_id}] " if assign_id and not CLAIM_PREFIX_RE.match(rest) else ""
    rest_out = rest
    for inv_rel, src_id in add_inverse:
        rest_out = _insert_inverse_clause(rest_out, inv_rel, src_id)
    return f"{prefix}[{state_out}]{ws}{id_prefix}{rest_out}{eol}"


def _apply_claim_line_edits(path, edits_by_ord):
    """Apply {ord: edit_spec} strictly inside ## Claims. Returns True if file bytes changed."""
    raw = Path(path).read_text(encoding="utf-8")
    lines = raw.splitlines(keepends=True)
    span = _claims_section_line_range(lines)
    if span is None:
        return False
    start, end = span
    changed = False
    ord_idx = 0
    for idx in range(start, end):
        if parse_claim_line(lines[idx]) is None:
            continue
        spec = edits_by_ord.get(ord_idx)
        ord_idx += 1
        if not spec:
            continue
        updated = _rewrite_claim_line(
            lines[idx],
            new_state=spec.get("state"),
            assign_id=spec.get("assign_id", ""),
            add_inverse=spec.get("add_inverse", ()),
        )
        if updated != lines[idx]:
            lines[idx] = updated
            changed = True
    if changed:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write("".join(lines))
    return changed


def resolve_entry(root, target):
    """Locate an entry by id or file path. Raises ReconcileError on missing or instrument entry."""
    root = Path(root)
    target_path = Path(target)
    if not target_path.is_absolute():
        candidate = (Path.cwd() / target_path).resolve()
        if not candidate.is_file():
            candidate = (root / target_path).resolve()
    else:
        candidate = target_path.resolve()

    loaded = []
    for path in entry_paths(root):
        entry, probs = load(path, root)
        if entry is not None:
            loaded.append((entry, path.resolve()))

    for entry, resolved in loaded:
        if entry.id == target or entry.path == Path(target).as_posix() or resolved == candidate:
            if entry.path.startswith("instruments/"):
                raise ReconcileError(
                    "INSTRUMENTS_PROTECTED",
                    f"{entry.path} is an instrument file and cannot be modified by this command",
                    "instrument files are edited only by the R&D seat in a reviewed diff",
                    exit_code=2,
                )
            return entry, resolved, [e for e, _ in loaded]

    raise ReconcileError("NOT_FOUND", f"no entry {target!r}", "pass an entry id or path under entries/", exit_code=2)


def assign_claim_ids(root, target):
    """Assign deterministic c-<hex> ids to claims in `target` that lack one. Returns (entry_id, path, assigned_ids)."""
    root = Path(root)
    entry, resolved, entries = resolve_entry(root, target)
    taken = {c["id"] for e in entries for c in e.claims if c["id"]}
    edits = {}
    assigned = []
    for ord_idx, c in enumerate(entry.claims):
        if c["id"]:
            continue
        cid = make_claim_id(entry.id, c["text"], taken)
        taken.add(cid)
        edits[ord_idx] = {"assign_id": cid}
        assigned.append(cid)
    if edits:
        _apply_claim_line_edits(resolved, edits)
    return entry.id, entry.path, assigned


def reconcile_entry(root, target):
    """Reconcile forward relations (`supersedes`, `contradicts`, `supports`) stated by `target`."""
    root = Path(root)
    entry, resolved, entries = resolve_entry(root, target)
    path_by_entry = {e.id: root / e.path for e in entries}
    explicit = {}
    taken = set()
    for e in entries:
        for ord_idx, c in enumerate(e.claims):
            if c["id"]:
                explicit[c["id"]] = (e, ord_idx, c)
                taken.add(c["id"])
    provisional = {}
    for e in entries:
        if e.path.startswith("instruments/"):
            continue
        for ord_idx, c in enumerate(e.claims):
            if not c["id"]:
                pid = make_claim_id(e.id, c["text"], taken)
                taken.add(pid)
                provisional[pid] = (e, ord_idx, c)

    file_edits = {}  # entry_id -> {ord_idx: {"state": ..., "assign_id": ..., "add_inverse": [...]}}
    links = []

    def slot(eid, ord_idx):
        return file_edits.setdefault(eid, {}).setdefault(
            ord_idx, {"state": None, "assign_id": "", "add_inverse": []}
        )

    for src_ord, c in enumerate(entry.claims):
        forward = [(rel_name, c["relations"].get(rel_name, [])) for rel_name in FORWARD_RELATIONS]
        if not any(tids for _, tids in forward):
            continue
        src_id = c["id"]
        if not src_id:
            # Find already computed provisional id for this claim if any, else generate.
            src_id = next(
                (pid for pid, (pe, pord, _) in provisional.items() if pe.id == entry.id and pord == src_ord),
                "",
            ) or make_claim_id(entry.id, c["text"], taken)
            taken.add(src_id)
            slot(entry.id, src_ord)["assign_id"] = src_id

        for rel_name, tids in forward:
            inv_rel = INVERSE_OF[rel_name]
            new_state = RECONCILE_STATE[rel_name]
            for tid in tids:
                found = explicit.get(tid) or provisional.get(tid)
                if found is None:
                    raise ReconcileError(
                        "CLAIM_NOT_FOUND",
                        f"claim id {tid!r} does not exist in the library",
                        "check `rnd claims` or run `rnd claims assign <older-entry>` first",
                        exit_code=1,
                    )
                dst_entry, dst_ord, dst_claim = found
                if dst_entry.path.startswith("instruments/"):
                    raise ReconcileError(
                        "INSTRUMENTS_PROTECTED",
                        f"cannot reconcile into instrument file {dst_entry.path}",
                        "instrument files are edited only by the R&D seat in a reviewed diff",
                        exit_code=2,
                    )
                if dst_entry.id == entry.id and dst_ord == src_ord:
                    raise ReconcileError(
                        "SELF_RELATION",
                        f"claim {src_id} cannot state '{rel_name}' on itself",
                        "point the relation at another claim id",
                        exit_code=1,
                    )
                dst_slot = slot(dst_entry.id, dst_ord)
                if not dst_claim["id"]:
                    dst_slot["assign_id"] = tid
                if new_state == "superseded":
                    dst_slot["state"] = "superseded"
                elif new_state == "disputed" and dst_slot["state"] != "superseded" and dst_claim["state"] != "superseded":
                    dst_slot["state"] = "disputed"
                pair = (inv_rel, src_id)
                if pair not in dst_slot["add_inverse"]:
                    dst_slot["add_inverse"].append(pair)
                links.append({
                    "src_entry": entry.id,
                    "src_id": src_id,
                    "relation": rel_name,
                    "dst_id": tid,
                    "dst_entry": dst_entry.id,
                })

    changed_files = []
    for eid, edits in sorted(file_edits.items()):
        p = path_by_entry[eid]
        if _apply_claim_line_edits(p, edits):
            changed_files.append(p.relative_to(root).as_posix())
    return {"entry": entry.id, "links": links, "changed_files": changed_files}
