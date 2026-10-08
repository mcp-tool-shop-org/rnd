"""Entry files: parsing and validation.

An entry is a Markdown file with frontmatter. Sources and claims live in the
body as tagged list items so the file stays readable in any editor:

    ## Sources
    - [primary] https://developer.nvidia.com/blog/cuda-graphs/ — NVIDIA blog
    ## Claims
    - [unverified] Rubin is compute capability 10.7 (via: aggregator summary)
"""

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
CONFIDENCE = ("verified", "unverified", "disputed", "wrong")
INSTRUMENT_STATUS = ("shipped", "planned", "retired")

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
ITEM_RE = re.compile(r"^\s*[-*]\s+\[([A-Za-z-]+)\]\s+(.+?)\s*$")
URL_RE = re.compile(r"https?://[^\s)>\]]+")
MDLINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
VIA_RE = re.compile(r"\(via:\s*([^)]+)\)\s*$")
WIKILINK_RE = re.compile(r"\[\[([a-z0-9][a-z0-9._-]*)\]\]")
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.M)


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


def parse_claims(text):
    items = []
    for line in text.splitlines():
        m = ITEM_RE.match(line)
        if not m:
            continue
        confidence, rest = m.group(1).lower(), m.group(2)
        via = VIA_RE.search(rest)
        items.append({
            "confidence": confidence,
            "text": rest[:via.start()].strip() if via else rest,
            "via": via.group(1).strip() if via else "",
        })
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
    for e in entries:
        for link in e.links:
            if link not in ids:
                problems.append(Problem("warning", e.path, f"[[{link}]] points at no entry"))
    return entries, problems
