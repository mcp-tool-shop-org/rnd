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
CLAIM_HEAD_RE = re.compile(r"^(\s*[-*]\s+)\[([A-Za-z-]+)\](\s+)(\S.*)$")
NON_CONT_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)]|#{1,6})\s+")
CLAIM_PREFIX_RE = re.compile(r"^\[(c-[^\]]*)\](?!\()\s*(.*)$")
CLAUSE_RE = re.compile(
    r"\((via|supersedes|contradicts|supports|superseded-by|contradicted-by|supported-by):\s*([^)]*)\)\s*$"
)
URL_RE = re.compile(r"https?://[^\s)>\]]+")
MDLINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
VIA_RE = re.compile(r"\(via:\s*([^)]+)\)\s*$")
WIKILINK_RE = re.compile(r"\[\[([a-z0-9][a-z0-9._-]*)\]\]")
HEADING_LINE_RE = re.compile(r"^##\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


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


def _read_raw_text(path):
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def _split_eol(line):
    body = line.rstrip("\r\n")
    return body, line[len(body):]


def _body_start_line(lines):
    if not lines:
        return 0
    first = lines[0][1:] if lines[0].startswith("\ufeff") else lines[0]
    if first.strip() != "---":
        return 0
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return i + 1
    return 0


def _opening_fence(line_body):
    fm = FENCE_RE.match(line_body)
    if not fm:
        return None
    marker = fm.group(1)
    if marker[0] == "`" and "`" in line_body[fm.end():]:
        return None
    return marker[0], len(marker)


def _is_closing_fence(line_body, fence_ch, fence_n):
    stripped = line_body.lstrip(" ")
    if len(line_body) - len(stripped) > 3:
        return False
    return stripped.startswith(fence_ch * fence_n) and stripped.lstrip(fence_ch).strip() == ""


def _section_spans(lines, start=0):
    """Yield (lower_heading, body_start_idx, body_end_idx) outside fenced code blocks."""
    headings = []
    fence = None
    for idx in range(start, len(lines)):
        ln, _ = _split_eol(lines[idx])
        if fence is not None:
            if _is_closing_fence(ln, *fence):
                fence = None
            continue
        opened = _opening_fence(ln)
        if opened is not None:
            fence = opened
            continue
        hm = HEADING_LINE_RE.match(ln)
        if hm:
            headings.append((hm.group(1).strip().lower(), idx))
    spans = []
    for k, (name, h_idx) in enumerate(headings):
        end = headings[k + 1][1] if k + 1 < len(headings) else len(lines)
        spans.append((name, h_idx + 1, end))
    return spans


def _unclosed_fence(lines, start=0, line_offset=0):
    """Return (fence_marker, 1based_open_line) if an entry body ends inside an open code fence."""
    fence = None
    open_line = 0
    for idx in range(start, len(lines)):
        ln, _ = _split_eol(lines[idx])
        if fence is not None:
            if _is_closing_fence(ln, *fence):
                fence = None
                open_line = 0
            continue
        opened = _opening_fence(ln)
        if opened is not None:
            fence = opened
            open_line = line_offset + idx + 1
    if fence is not None:
        return fence[0] * fence[1], open_line
    return None


def claims_section_span(lines, start=0):
    """Return (span_or_None, real_count) for '## Claims' headings outside code fences.

    When multiple real '## Claims' headings exist, the last heading wins (matching
    `sections()`), and `real_count > 1` is flagged as an error by `rnd check`.
    """
    matches = [(s, e) for name, s, e in _section_spans(lines, start) if name == "claims"]
    if not matches:
        return None, 0
    return matches[-1], len(matches)


def sections(body):
    """Map lower-cased '## heading' -> section text, ignoring headings inside code fences."""
    lines = body.splitlines(keepends=True)
    out = {}
    for name, start, end in _section_spans(lines, 0):
        out[name] = "".join(lines[start:end]).strip()
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


def _match_trailing_clause(cur, seen_via=False):
    cm = CLAUSE_RE.search(cur)
    if not cm:
        return None
    key, raw_val = cm.group(1), cm.group(2)
    if key == "via":
        val = raw_val.strip()
        if seen_via or not val:
            return None
        return cm, "via", val
    val = raw_val.strip()
    if not val:
        return None
    targets = [t.strip() for t in val.split(",")]
    if not targets or not all(CLAIM_ID_RE.match(t) for t in targets):
        return None
    return cm, key, targets


def _is_claim_continuation(line_body):
    if not line_body.strip():
        return False
    if NON_CONT_RE.match(line_body) or line_body.lstrip().startswith(">"):
        return False
    if _opening_fence(line_body) is not None:
        return False
    return True


def _iter_claim_blocks(lines, start=0, end=None):
    """Yield (block_start, block_end) line index spans inside one Claims slice."""
    limit = len(lines) if end is None else end
    i = start
    fence = None
    while i < limit:
        ln, _ = _split_eol(lines[i])
        if fence is not None:
            if _is_closing_fence(ln, *fence):
                fence = None
            i += 1
            continue
        opened = _opening_fence(ln)
        if opened is not None:
            fence = opened
            i += 1
            continue
        if CLAIM_HEAD_RE.match(ln):
            j = i + 1
            while j < limit and _is_claim_continuation(_split_eol(lines[j])[0]):
                j += 1
            yield i, j
            i = j
            continue
        i += 1


def parse_claim_block(block_lines):
    """Parse one claim (single- or multi-line wrapped) block into a dict, or None."""
    if not block_lines:
        return None
    first_body, _ = _split_eol(block_lines[0])
    m = CLAIM_HEAD_RE.match(first_body)
    if not m:
        return None
    confidence = m.group(2).lower()
    rest = " ".join([m.group(4).rstrip()] + [ln.strip() for ln in block_lines[1:] if ln.strip()])
    claim_id = ""
    pm = CLAIM_PREFIX_RE.match(rest)
    if pm:
        claim_id = pm.group(1).strip()
        rest = pm.group(2).strip()
    peeled = []
    cur = rest.rstrip()
    seen_via = False
    while True:
        matched = _match_trailing_clause(cur, seen_via=seen_via)
        if matched is None:
            break
        cm, key, val = matched
        if key == "via":
            seen_via = True
        peeled.append((key, val))
        cur = cur[:cm.start()].rstrip()
    via = ""
    relations = {}
    for key, val in reversed(peeled):
        if key == "via":
            via = val
        else:
            bucket = relations.setdefault(key, [])
            for t in val:
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


def parse_claim_line(line):
    """Parse one claim list item line into a dict, or return None if the line is not a claim item."""
    return parse_claim_block([line])


def parse_claims(text):
    lines = text.splitlines(keepends=True)
    items = []
    for b_start, b_end in _iter_claim_blocks(lines):
        parsed = parse_claim_block(lines[b_start:b_end])
        if parsed is not None:
            items.append(parsed)
    return items


def load(path, root):
    """Parse one entry file. Returns (entry_or_None, problems)."""
    rel = Path(path).relative_to(root).as_posix()
    try:
        text = _read_raw_text(path)
    except (OSError, UnicodeDecodeError) as exc:
        return None, [Problem("error", rel, f"unreadable: {exc}")]
    return load_text(text, rel)


def load_text(text, rel):
    """Parse entry text already in memory for library-relative `rel`. Returns (entry_or_None, problems)."""
    problems = []
    try:
        meta, body = frontmatter.read(text)
    except frontmatter.FrontmatterError as exc:
        return None, [Problem("error", rel, f"unreadable: {exc}")]

    def err(msg):
        problems.append(Problem("error", rel, msg))

    entry_id = str(meta.get("id") or Path(rel).stem)
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

    body_lines = body.splitlines(keepends=True)
    raw_lines = text.splitlines(keepends=True)
    body_start = _body_start_line(raw_lines)
    unclosed = _unclosed_fence(raw_lines, start=body_start)
    if unclosed is not None:
        fence_marker, open_line = unclosed
        err(f"unclosed code fence ({fence_marker}) opened at line {open_line}; close the fence so later sections are not hidden")
    secs = sections(body)
    sources = parse_sources(secs.get("sources", ""))
    for s in sources:
        if s["tier"] not in TIERS:
            err(f"source tier [{s['tier']}] must be one of {', '.join(TIERS)}")
        if not s["url"] and s["tier"] not in ("user", "rig"):
            err(f"[{s['tier']}] source has no URL: {s['label'][:60]!r}")
    claims_span, claims_count = claims_section_span(body_lines, 0)
    if claims_count > 1:
        err(f"multiple '## Claims' headings ({claims_count} found); keep one Claims section")
    claims_text = "".join(body_lines[claims_span[0]:claims_span[1]]) if claims_span is not None else ""
    claims = parse_claims(claims_text)
    for c in claims:
        if c["confidence"] not in CONFIDENCE:
            err(f"claim tag [{c['confidence']}] must be one of {', '.join(CONFIDENCE)}")
        if c["confidence"] in ("verified", "wrong") and not c["via"]:
            err(f"[{c['confidence']}] claim needs '(via: who/what, date)': {c['text'][:60]!r}")
        if c["confidence"] == "superseded" and not c["relations"].get("superseded-by"):
            problems.append(Problem(
                "warning",
                rel,
                f"[superseded] claim {c['id'] or '<unassigned>'} has no '(superseded-by: <id>)' link; "
                f"link the replacing claim with `rnd reconcile` or set its state back (e.g. [verified] or [unverified]): "
                f"{c['text'][:60]!r}",
            ))
        if c["id"] and not CLAIM_ID_RE.match(c["id"]):
            err(f"claim id {c['id']!r} must match 'c-<id>' (lower-case letters, digits, '.', '_' or '-')")
        for rel_name, targets in c["relations"].items():
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
    taken_claim_ids = set()
    for e in entries:
        for link in e.links:
            if link not in ids:
                problems.append(Problem("warning", e.path, f"[[{link}]] points at no entry"))
        for c in e.claims:
            cid = c["id"]
            if not cid:
                continue
            taken_claim_ids.add(cid)
            if cid in seen_claims:
                problems.append(Problem(
                    "error", e.path,
                    f"duplicate claim id {cid!r} (also in {seen_claims[cid][0].path})"))
            else:
                seen_claims[cid] = (e, c)
    provisional_claims = {}
    for e in entries:
        if e.path.startswith("instruments/"):
            continue
        for c in e.claims:
            if not c["id"]:
                pid = make_claim_id(e.id, c["text"], taken_claim_ids)
                taken_claim_ids.add(pid)
                provisional_claims[pid] = (e, c)
    for e in entries:
        for c in e.claims:
            cid = c["id"]
            for rel_name, targets in c["relations"].items():
                inv = INVERSE_OF[rel_name]
                state_reset = (
                    " and set its state back"
                    if (rel_name == "superseded-by" and c["state"] == "superseded")
                    or (rel_name == "contradicted-by" and c["state"] == "disputed")
                    else ""
                )
                for tid in targets:
                    if tid == cid:
                        continue
                    target = seen_claims.get(tid)
                    if target is None:
                        if rel_name in FORWARD_RELATIONS:
                            hint = f"run `rnd reconcile {e.id}`"
                        else:
                            prov = provisional_claims.get(tid)
                            clause = f"({inv}: {cid or '<id>'})"
                            if prov is not None:
                                prov_entry, _ = prov
                                assign_step = f"run `rnd claims assign {e.id}`, " if not cid else ""
                                hint = (
                                    f"remove stale '({rel_name}: {tid})' from {e.path}{state_reset}, or {assign_step}"
                                    f"add '{clause}' to the claim in {prov_entry.path} and run `rnd reconcile {prov_entry.id}`"
                                )
                            else:
                                assign_step = f"run `rnd claims assign {e.id}`, " if not cid else ""
                                hint = (
                                    f"remove stale '({rel_name}: {tid})' from {e.path}{state_reset}, or {assign_step}"
                                    f"add '{clause}' to the replacing claim in <newer-entry> and run `rnd reconcile <newer-entry>`"
                                )
                        problems.append(Problem(
                            "error", e.path,
                            f"claim {cid or '<unassigned>'} states '{rel_name}: {tid}', which does not exist; {hint}"))
                        continue
                    other_entry, other_claim = target
                    if not cid:
                        if rel_name in FORWARD_RELATIONS:
                            hint = f"run `rnd reconcile {e.id}`"
                        else:
                            hint = (
                                f"run `rnd claims assign {e.id}` and add '({inv}: <id>)' to {tid} in "
                                f"{other_entry.path}, or remove '({rel_name}: {tid})' from {e.path}{state_reset}"
                            )
                        problems.append(Problem(
                            "error", e.path,
                            f"claim with '{rel_name}: {tid}' has no id (link present on one side only); {hint}"))
                        continue
                    if cid not in other_claim["relations"].get(inv, []):
                        if rel_name in FORWARD_RELATIONS:
                            hint = f"run `rnd reconcile {e.id}`"
                        else:
                            hint = (
                                f"add '({inv}: {cid})' to {tid} in {other_entry.path} and run "
                                f"`rnd reconcile {other_entry.id}`, or remove '({rel_name}: {tid})' from {e.path}{state_reset}"
                            )
                        problems.append(Problem(
                            "error", e.path,
                            f"claim {cid} states '{rel_name}: {tid}', but {tid} in {other_entry.id} lacks "
                            f"'{inv}: {cid}' (link present on one side only); {hint}"))
    return entries, problems


def _claims_section_line_range(lines):
    """Return (start, end) line indices for the active '## Claims' body in splitlines(keepends=True)."""
    span, _ = claims_section_span(lines, _body_start_line(lines))
    return span


def _insert_inverse_clause(rest, inv_rel, src_id):
    """Add `src_id` into a trailing `(inv_rel: ...)` clause or append one, leaving the sentence untouched."""
    trimmed = rest.rstrip()
    clauses = []
    cur = trimmed
    seen_via = False
    while True:
        matched = _match_trailing_clause(cur, seen_via=seen_via)
        if matched is None:
            break
        cm, key, val = matched
        if key == "via":
            seen_via = True
        clauses.append((cm.start(), cm.end(), key, val))
        cur = cur[:cm.start()].rstrip()
    for start, end, key, tokens in clauses:
        if key == inv_rel:
            if src_id in tokens:
                return rest
            updated = f"({inv_rel}: {', '.join([*tokens, src_id])})"
            return trimmed[:start] + updated + trimmed[end:]
    return f"{trimmed} ({inv_rel}: {src_id})"


def _rewrite_claim_block(block_lines, new_state=None, assign_id="", add_inverse=()):
    """Edit one (possibly wrapped) claim block in place, keeping words, indentation, and line endings."""
    if not block_lines:
        return block_lines
    first_body, first_eol = _split_eol(block_lines[0])
    m = CLAIM_HEAD_RE.match(first_body)
    if not m:
        return list(block_lines)
    parsed = parse_claim_block(block_lines)
    pending_inv = [
        (rel, src) for rel, src in add_inverse
        if not (parsed and src in parsed["relations"].get(rel, []))
    ]
    prefix, old_state, ws, first_rest = m.group(1), m.group(2), m.group(3), m.group(4)
    state_out = new_state or old_state
    needs_id = bool(assign_id and not (parsed and parsed["id"]) and not CLAIM_PREFIX_RE.match(first_rest))
    id_prefix = f"[{assign_id}] " if needs_id else ""
    if len(block_lines) == 1:
        rest_out = f"{id_prefix}{first_rest}"
        for inv_rel, src_id in pending_inv:
            rest_out = _insert_inverse_clause(rest_out, inv_rel, src_id)
        return [f"{prefix}[{state_out}]{ws}{rest_out}{first_eol}"]
    out = [f"{prefix}[{state_out}]{ws}{id_prefix}{first_rest}{first_eol}", *block_lines[1:-1]]
    last_body, last_eol = _split_eol(block_lines[-1])
    for inv_rel, src_id in pending_inv:
        last_body = _insert_inverse_clause(last_body, inv_rel, src_id)
    out.append(f"{last_body}{last_eol}")
    return out


def _display_rel_path(path, root=None):
    p = Path(path).resolve()
    if root is not None:
        try:
            return p.relative_to(Path(root).resolve()).as_posix()
        except ValueError:
            pass
    for parent in p.parents:
        if (parent / "entries").is_dir() and (parent / "instruments").is_dir():
            return p.relative_to(parent).as_posix()
    return Path(path).as_posix()


def _require_single_claims_heading(lines, rel_path):
    span, count = claims_section_span(lines, _body_start_line(lines))
    if count > 1:
        raise ReconcileError(
            "MULTIPLE_CLAIMS_HEADINGS",
            f"{rel_path}: multiple '## Claims' headings ({count} found)",
            "keep a single '## Claims' section before running this command",
            exit_code=1,
        )
    return span


def _plan_claim_line_edits(path, edits_by_ord, root=None):
    """Verify every target claim and compute new raw text, or None if unchanged. Writes nothing."""
    rel = _display_rel_path(path, root)
    raw = _read_raw_text(path)
    lines = raw.splitlines(keepends=True)
    span = _require_single_claims_heading(lines, rel)
    if span is None:
        if edits_by_ord:
            raise ReconcileError(
                "CLAIM_MISMATCH",
                f"{rel}: missing '## Claims' section",
                "check `## Claims` headings and run `rnd check`",
                exit_code=1,
            )
        return None
    start, end = span
    blocks = list(_iter_claim_blocks(lines, start, end))
    for ord_idx, spec in sorted(edits_by_ord.items()):
        if ord_idx < 0 or ord_idx >= len(blocks):
            raise ReconcileError(
                "CLAIM_MISMATCH",
                f"{rel}: claim #{ord_idx} was not found inside the Claims section",
                "check `## Claims` headings and run `rnd check`",
                exit_code=1,
            )
        b_start, b_end = blocks[ord_idx]
        live = parse_claim_block(lines[b_start:b_end])
        exp_id = spec.get("expected_id", "")
        exp_text = spec.get("expected_text")
        if live is None or live["id"] != exp_id or (exp_text is not None and live["text"] != exp_text):
            raise ReconcileError(
                "CLAIM_MISMATCH",
                f"{rel}: line does not match parsed claim #{ord_idx} (expected id {exp_id!r})",
                "check `## Claims` headings and run `rnd check`",
                exit_code=1,
            )

    replacements = []
    for ord_idx, spec in sorted(edits_by_ord.items()):
        b_start, b_end = blocks[ord_idx]
        old_block = lines[b_start:b_end]
        updated = _rewrite_claim_block(
            old_block,
            new_state=spec.get("state"),
            assign_id=spec.get("assign_id", ""),
            add_inverse=spec.get("add_inverse", ()),
        )
        if updated != old_block:
            replacements.append((b_start, b_end, updated))
    if not replacements:
        return None
    new_lines = list(lines)
    for b_start, b_end, updated in sorted(replacements, reverse=True):
        new_lines[b_start:b_end] = updated
    return "".join(new_lines)


def _apply_claim_line_edits(path, edits_by_ord, root=None):
    """Apply {ord: edit_spec} strictly inside the Claims section, keeping line endings."""
    new_raw = _plan_claim_line_edits(path, edits_by_ord, root=root)
    if new_raw is None:
        return False
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_raw)
    return True


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
    _require_single_claims_heading(_read_raw_text(resolved).splitlines(keepends=True), entry.path)
    taken = {c["id"] for e in entries for c in e.claims if c["id"]}
    edits = {}
    assigned = []
    for ord_idx, c in enumerate(entry.claims):
        if c["id"]:
            continue
        cid = make_claim_id(entry.id, c["text"], taken)
        taken.add(cid)
        edits[ord_idx] = {"assign_id": cid, "expected_id": "", "expected_text": c["text"]}
        assigned.append(cid)
    if edits:
        _apply_claim_line_edits(resolved, edits, root=root)
    return entry.id, entry.path, assigned


def reconcile_entry(root, target):
    """Reconcile forward relations (`supersedes`, `contradicts`, `supports`) stated by `target`."""
    root = Path(root)
    entry, resolved, entries = resolve_entry(root, target)
    _require_single_claims_heading(_read_raw_text(resolved).splitlines(keepends=True), entry.path)
    path_by_entry = {e.id: root / e.path for e in entries}
    explicit = {}
    duplicate_ids = set()
    taken = set()
    for e in entries:
        for ord_idx, c in enumerate(e.claims):
            if c["id"]:
                if c["id"] in explicit:
                    duplicate_ids.add(c["id"])
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

    def slot(eid, ord_idx, expected_id, expected_text):
        return file_edits.setdefault(eid, {}).setdefault(
            ord_idx,
            {
                "state": None,
                "assign_id": "",
                "add_inverse": [],
                "expected_id": expected_id,
                "expected_text": expected_text,
            },
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
            slot(entry.id, src_ord, "", c["text"])["assign_id"] = src_id

        for rel_name, tids in forward:
            inv_rel = INVERSE_OF[rel_name]
            new_state = RECONCILE_STATE[rel_name]
            for tid in tids:
                if tid in duplicate_ids:
                    raise ReconcileError(
                        "DUPLICATE_CLAIM_ID",
                        f"claim id {tid!r} appears more than once in the library",
                        "run `rnd check` and resolve duplicate claim ids first",
                        exit_code=1,
                    )
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
                dst_slot = slot(dst_entry.id, dst_ord, dst_claim["id"], dst_claim["text"])
                if not dst_claim["id"]:
                    dst_slot["assign_id"] = tid
                if new_state == "superseded":
                    dst_slot["state"] = "superseded"
                elif new_state == "disputed" and dst_slot["state"] != "superseded" and dst_claim["state"] not in ("superseded", "wrong"):
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

    planned_writes = []
    for eid, edits in sorted(file_edits.items()):
        p = path_by_entry[eid]
        new_raw = _plan_claim_line_edits(p, edits, root=root)
        if new_raw is not None:
            planned_writes.append((p, new_raw))

    changed_files = []
    for p, new_raw in planned_writes:
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(new_raw)
        changed_files.append(p.relative_to(root).as_posix())
    return {"entry": entry.id, "links": links, "changed_files": changed_files}
