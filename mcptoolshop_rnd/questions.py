"""Open research questions stored one file per question under questions/."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from . import frontmatter, model

QUESTIONS_DIR = "questions"
STATUSES = ("open", "investigating", "answered", "parked")
KNOWN_KEYS = {"id", "title", "date", "status", "fields", "tags", "answered_by"}


class QuestionError(Exception):
    def __init__(self, code: str, message: str, hint: str = "", exit_code: int = 2):
        super().__init__(message)
        self.code, self.hint, self.exit_code = code, hint, exit_code


@dataclass
class Question:
    id: str
    path: str
    title: str
    date: str
    status: str
    fields: list[str]
    tags: list[str]
    answered_by: list[str] = field(default_factory=list)
    body: str = ""


def question_paths(root):
    base = Path(root) / QUESTIONS_DIR
    if base.is_dir():
        yield from sorted(p for p in base.rglob("*.md") if not p.name.startswith("_"))


def load(path, root):
    """Parse one question file. Returns (question_or_None, problems)."""
    rel = Path(path).relative_to(root).as_posix()
    problems = []
    try:
        text = Path(path).read_text(encoding="utf-8")
        meta_text, body = frontmatter.split(text)
        if meta_text is None:
            return None, [model.Problem("error", rel, "missing frontmatter")]
        meta = frontmatter.parse(meta_text)
    except (OSError, UnicodeDecodeError, frontmatter.FrontmatterError) as exc:
        return None, [model.Problem("error", rel, f"unreadable: {exc}")]

    def err(msg):
        problems.append(model.Problem("error", rel, msg))

    unknown = sorted(set(meta) - KNOWN_KEYS)
    if unknown:
        err(f"unknown question frontmatter keys: {', '.join(unknown)}")

    qid = str(meta.get("id") or Path(path).stem)
    if not model.ID_RE.match(qid):
        err(f"id {qid!r} must be lower-case letters, digits, '.', '_' or '-'")
    title = str(meta.get("title") or "").strip()
    if not title:
        err("missing 'title'")
    qdate = str(meta.get("date") or "")
    if not model.DATE_RE.match(qdate):
        err(f"'date' must be YYYY-MM-DD, got {qdate!r}")
    status = str(meta.get("status") or "open")
    if status not in STATUSES:
        err(f"'status' must be one of {', '.join(STATUSES)}; got {status!r}")
    fields = model._as_list(meta.get("fields"))
    if not fields:
        err("'fields' needs at least one research field, e.g. [gpu-computing]")
    tags = model._as_list(meta.get("tags"))
    answered_by = model._as_list(meta.get("answered_by"))

    if status == "answered" and not answered_by:
        err("'answered' question needs 'answered_by' listing at least one existing claim id")

    q = Question(
        id=qid,
        path=rel,
        title=title,
        date=qdate,
        status=status,
        fields=fields,
        tags=tags,
        answered_by=answered_by,
        body=body,
    )
    return q, problems


def load_all(root, known_claim_ids=None):
    """Load and validate every question file under questions/."""
    qs, problems, seen = [], [], {}
    for path in question_paths(root):
        q, probs = load(path, root)
        problems.extend(probs)
        if q is None:
            continue
        if q.id in seen:
            problems.append(model.Problem("error", q.path, f"duplicate id {q.id!r} (also {seen[q.id]})"))
            continue
        seen[q.id] = q.path
        qs.append(q)
    if known_claim_ids is not None:
        for q in qs:
            for cid in q.answered_by:
                if cid not in known_claim_ids:
                    problems.append(model.Problem("error", q.path, f"answered_by claim id {cid!r} does not exist"))
    return qs, problems


def _slugify(text: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")[:60]


def _yaml_scalar(value: str) -> str:
    if (" #" in value or value[:1] in ("'", '"', "[")) and '"' not in value:
        return f'"{value}"'
    if (" #" in value or value[:1] in ("'", '"', "[")) and "'" not in value:
        return f"'{value}'"
    return value


def new_question(
    root,
    title: str,
    *,
    fields=None,
    tags=None,
    qid=None,
    today=None,
    status: str = "open",
    answered_by=None,
) -> str:
    """Create one question file under questions/ and return its POSIX path relative to root."""
    title_clean = " ".join((title or "").strip().splitlines()).strip()
    if not title_clean:
        raise QuestionError("BAD_TITLE", "question title must not be empty", 'rnd new-question "What needs checking?"')
    if status not in STATUSES:
        raise QuestionError("BAD_STATUS", f"'status' must be one of {', '.join(STATUSES)}; got {status!r}")
    day = today or date.today().isoformat()
    if not model.DATE_RE.match(day):
        raise QuestionError("BAD_DATE", f"'date' must be YYYY-MM-DD, got {day!r}")
    slug = qid or f"{day}-{_slugify(title_clean) or 'question'}"
    if not model.ID_RE.match(slug):
        raise QuestionError("BAD_ID", f"id {slug!r} is not valid", "use lower-case letters, digits and '-'")
    folder = Path(root) / QUESTIONS_DIR
    path = folder / f"{slug}.md"
    if path.exists():
        raise QuestionError("EXISTS", f"{path.relative_to(root).as_posix()} already exists", "pick another title or --id")
    field_list = [f.strip() for f in (fields or ["general"]) if str(f).strip()]
    if not field_list:
        field_list = ["general"]
    tag_list = [t.strip() for t in (tags or []) if str(t).strip()]
    ans_list = [a.strip() for a in (answered_by or []) if str(a).strip()]
    folder.mkdir(parents=True, exist_ok=True)
    content = (
        f"---\n"
        f"id: {slug}\n"
        f"title: {_yaml_scalar(title_clean)}\n"
        f"date: {day}\n"
        f"status: {status}\n"
        f"fields: [{', '.join(field_list)}]\n"
        f"tags: [{', '.join(tag_list)}]\n"
        f"answered_by: [{', '.join(ans_list)}]\n"
        f"---\n\n"
        f"## Question\n\n"
        f"{title_clean}\n\n"
        f"## Notes\n\n"
        f"- \n"
    )
    path.write_text(content, encoding="utf-8", newline="\n")
    return path.relative_to(root).as_posix()
