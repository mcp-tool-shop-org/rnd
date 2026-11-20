"""Read-only `rnd digest --since <git ref or YYYY-MM-DD>`: summarize claim and question changes."""

from __future__ import annotations

import datetime as dt
import re
import subprocess
import tempfile
from collections import deque
from pathlib import Path

from . import model, questions

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class DigestError(Exception):
    def __init__(self, code: str, message: str, hint: str = "", exit_code: int = 2):
        super().__init__(message)
        self.code, self.hint, self.exit_code = code, hint, exit_code


def _run_git(root: Path, *args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    except OSError as exc:
        raise DigestError("GIT_FAILED", f"git could not run: {exc}", "install git and ensure it is on PATH", exit_code=3) from exc


def resolve_since(root: Path, spec: str) -> tuple[str, str]:
    """Resolve a git ref or YYYY-MM-DD date (last commit on HEAD at or before that day) to (sha, date)."""
    spec = (spec or "").strip()
    if not spec or spec.startswith("-"):
        raise DigestError("UNKNOWN_REF", f"unknown git ref {spec!r}", "pass a git tag, commit SHA, branch, or YYYY-MM-DD", exit_code=2)

    if DATE_RE.match(spec):
        try:
            dt.date.fromisoformat(spec)
        except ValueError:
            raise DigestError("BAD_SINCE", f"invalid calendar date {spec!r}", "pass a valid YYYY-MM-DD date or a git ref", exit_code=2) from None
        proc = _run_git(root, "log", "--date-order", "--format=%H%x09%ct%x09%cs", "HEAD")
        if proc.returncode != 0:
            detail = proc.stderr.decode("utf-8", "replace").strip()
            raise DigestError("GIT_FAILED", detail or "git log failed", "run inside a git checkout of the library", exit_code=3)
        rows = []
        for line in proc.stdout.decode("utf-8", "replace").splitlines():
            parts = line.split("\t")
            if len(parts) == 3:
                rows.append((parts[0], int(parts[1]), parts[2]))
        eligible = [(sha, ct, cs, idx) for idx, (sha, ct, cs) in enumerate(rows) if cs <= spec]
        if not eligible:
            if rows:
                first_sha, _, first_cs = rows[-1]
                raise DigestError(
                    "BAD_SINCE",
                    f"no commit on HEAD at or before {spec}",
                    f"earliest commit on HEAD is {first_sha[:8]} ({first_cs}); pass a date on or after {first_cs} or a git ref",
                    exit_code=2,
                )
            raise DigestError("BAD_SINCE", "HEAD has no commits", "commit the library before running digest", exit_code=2)
        best = max(eligible, key=lambda r: (r[1], -r[3]))
        return best[0], best[2]

    proc = _run_git(root, "rev-parse", "--verify", "--quiet", f"{spec}^{{commit}}")
    if proc.returncode != 0:
        raise DigestError(
            "UNKNOWN_REF",
            f"unknown git ref {spec!r}",
            "pass an existing git tag, branch, commit SHA, or a YYYY-MM-DD date",
            exit_code=2,
        )
    sha = proc.stdout.decode("utf-8", "replace").strip()
    date_proc = _run_git(root, "show", "-s", "--format=%cs", sha)
    commit_date = date_proc.stdout.decode("utf-8", "replace").strip() if date_proc.returncode == 0 else ""
    return sha, commit_date


def _load_snapshot_at_commit(root: Path, sha: str) -> tuple[list[model.Entry], list[questions.Question]]:
    """Load entries and questions from `sha` via git objects inside a temporary directory."""
    tree_proc = _run_git(root, "ls-tree", "-r", "-z", sha, "--", "entries", "instruments", "questions")
    if tree_proc.returncode != 0:
        detail = tree_proc.stderr.decode("utf-8", "replace").strip()
        raise DigestError("GIT_FAILED", detail or f"git ls-tree failed for {sha[:8]}", exit_code=3)

    blobs: list[tuple[str, str]] = []
    for rec in tree_proc.stdout.split(b"\x00"):
        if not rec:
            continue
        meta_raw, path_raw = rec.split(b"\t", 1)
        meta_parts = meta_raw.decode("ascii").split()
        obj_type, obj_sha = meta_parts[1], meta_parts[2]
        rel_path = path_raw.decode("utf-8", "surrogateescape")
        if obj_type == "blob" and rel_path.endswith(".md") and not Path(rel_path).name.startswith("_"):
            blobs.append((obj_sha, rel_path))

    with tempfile.TemporaryDirectory() as td:
        tmp_root = Path(td)
        if blobs:
            batch_in = "".join(f"{b_sha}\n" for b_sha, _ in blobs).encode("ascii")
            try:
                cat_proc = subprocess.run(
                    ["git", "-C", str(root), "cat-file", "--batch"],
                    input=batch_in,
                    capture_output=True,
                    check=True,
                )
            except (OSError, subprocess.CalledProcessError) as exc:
                raise DigestError("GIT_FAILED", f"git cat-file failed for {sha[:8]}: {exc}", exit_code=3) from exc
            out = cat_proc.stdout
            pos = 0
            for _, rel_path in blobs:
                nl = out.index(b"\n", pos)
                header = out[pos:nl].decode("ascii").split()
                size = int(header[2])
                pos = nl + 1
                data = out[pos:pos + size]
                pos += size + 1
                dest = tmp_root / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)

        entries, _ = model.load_all(tmp_root)
        known_ids = {c["id"] for e in entries for c in e.claims if c["id"]}
        qs, _ = questions.load_all(tmp_root, known_claim_ids=known_ids)
        return entries, qs


def _rel_targets(rels: dict, rel_key: str, owner_map: dict[str, str]) -> list[dict]:
    return [{"id": tid, "entry_id": owner_map.get(tid, "")} for tid in rels.get(rel_key, [])]


def compute_digest(root, since_spec: str) -> dict:
    """Compare the library at `since_spec` (in git) against the current tree without writing anything."""
    root_path = Path(root)
    sha, since_date = resolve_since(root_path, since_spec)
    old_all_entries, old_qs = _load_snapshot_at_commit(root_path, sha)
    new_all_entries, _ = model.load_all(root_path)
    known_new_ids = {c["id"] for e in new_all_entries for c in e.claims if c["id"]}
    new_qs, _ = questions.load_all(root_path, known_claim_ids=known_new_ids)

    old_entries = [e for e in old_all_entries if not e.path.startswith("instruments/")]
    new_entries = [e for e in new_all_entries if not e.path.startswith("instruments/")]
    old_entry_ids = {e.id for e in old_entries}

    entries_added = [
        {"id": e.id, "title": e.title, "date": e.date, "kind": e.kind, "path": e.path}
        for e in sorted(new_entries, key=lambda x: (x.date, x.id))
        if e.id not in old_entry_ids
    ]

    old_claims = [(e.id, ord_idx, c) for e in old_entries for ord_idx, c in enumerate(e.claims)]
    new_claims = [(e.id, ord_idx, c) for e in new_entries for ord_idx, c in enumerate(e.claims)]
    new_owner = {c["id"]: eid for eid, _, c in new_claims if c["id"]}

    old_by_id: dict[str, deque[int]] = {}
    for idx, (_, _, c) in enumerate(old_claims):
        if c["id"]:
            old_by_id.setdefault(c["id"], deque()).append(idx)

    matched_old: set[int] = set()
    matched_new: set[int] = set()
    matched_pairs: list[tuple[int, int]] = []

    # Pass 1: match claims by id when both sides carry an id.
    for n_idx, (_, _, nc) in enumerate(new_claims):
        cid = nc["id"]
        if not cid:
            continue
        bucket = old_by_id.get(cid)
        if bucket:
            o_idx = bucket.popleft()
            matched_old.add(o_idx)
            matched_new.add(n_idx)
            matched_pairs.append((o_idx, n_idx))

    # Pass 2: match remaining claims lacking ids on at least one side by (entry_id, exact text).
    old_by_key: dict[tuple[str, str], deque[int]] = {}
    for o_idx, (eid, _, oc) in enumerate(old_claims):
        if o_idx in matched_old:
            continue
        old_by_key.setdefault((eid, oc["text"]), deque()).append(o_idx)

    for n_idx, (eid, _, nc) in enumerate(new_claims):
        if n_idx in matched_new:
            continue
        bucket = old_by_key.get((eid, nc["text"]))
        while bucket:
            o_idx = bucket.popleft()
            if nc["id"] and old_claims[o_idx][2]["id"]:
                continue
            matched_old.add(o_idx)
            matched_new.add(n_idx)
            matched_pairs.append((o_idx, n_idx))
            break

    claims_added = [
        {
            "entry_id": eid,
            "ord": ord_idx,
            "id": nc["id"] or None,
            "state": nc["state"],
            "text": nc["text"],
        }
        for n_idx, (eid, ord_idx, nc) in enumerate(new_claims)
        if n_idx not in matched_new
    ]

    claims_state_changed = []
    for o_idx, n_idx in matched_pairs:
        _, _, oc = old_claims[o_idx]
        eid, ord_idx, nc = new_claims[n_idx]
        if oc["state"] == nc["state"]:
            continue
        claims_state_changed.append({
            "entry_id": eid,
            "ord": ord_idx,
            "id": nc["id"] or oc["id"] or None,
            "old_state": oc["state"],
            "new_state": nc["state"],
            "text": nc["text"],
            "replaced_by": _rel_targets(nc["relations"], "superseded-by", new_owner),
            "contradicted_by": _rel_targets(nc["relations"], "contradicted-by", new_owner),
        })

    old_qs_by_id = {q.id: q for q in old_qs}
    questions_opened = []
    questions_answered = []
    questions_parked = []
    for q in sorted(new_qs, key=lambda x: (x.date, x.id)):
        oq = old_qs_by_id.get(q.id)
        old_status = oq.status if oq is not None else None
        if q.status in ("open", "investigating") and old_status not in ("open", "investigating"):
            questions_opened.append({
                "id": q.id,
                "title": q.title,
                "date": q.date,
                "status": q.status,
                "previous_status": old_status,
            })
        elif q.status == "answered" and old_status != "answered":
            questions_answered.append({
                "id": q.id,
                "title": q.title,
                "date": q.date,
                "previous_status": old_status,
                "answered_by": list(q.answered_by),
            })
        elif q.status == "parked" and old_status != "parked":
            questions_parked.append({
                "id": q.id,
                "title": q.title,
                "date": q.date,
                "previous_status": old_status,
            })

    return {
        "since": since_spec,
        "since_commit": sha,
        "since_date": since_date,
        "counts": {
            "entries_added": len(entries_added),
            "claims_added": len(claims_added),
            "claims_state_changed": len(claims_state_changed),
            "questions_opened": len(questions_opened),
            "questions_answered": len(questions_answered),
            "questions_parked": len(questions_parked),
        },
        "entries_added": entries_added,
        "claims_added": claims_added,
        "claims_state_changed": claims_state_changed,
        "questions_opened": questions_opened,
        "questions_answered": questions_answered,
        "questions_parked": questions_parked,
    }


def render_digest(rep: dict) -> str:
    """Format `compute_digest` output for humans."""
    c = rep["counts"]
    lines = [
        f"Digest since {rep['since']} ({rep['since_commit'][:12]}, {rep['since_date']})",
        (
            f"Summary: {c['entries_added']} entries added, {c['claims_added']} claims added, "
            f"{c['claims_state_changed']} claim state change(s), "
            f"{c['questions_opened']} question(s) opened, {c['questions_answered']} answered, {c['questions_parked']} parked"
        ),
        "",
        f"Entries added ({c['entries_added']})",
    ]
    for e in rep["entries_added"]:
        lines.append(f"  {e['date']}  {e['id']}  [{e['kind']}] {e['title']}")

    lines.extend(["", f"Claims added ({c['claims_added']})"])
    for cl in rep["claims_added"]:
        cid = cl["id"] or f"{cl['entry_id']}#{cl['ord']}"
        lines.append(f"  [{cl['state']}] {cid} ({cl['entry_id']}): {cl['text']}")

    lines.extend(["", f"Claim state changes ({c['claims_state_changed']})"])
    for ch in rep["claims_state_changed"]:
        cid = ch["id"] or f"{ch['entry_id']}#{ch['ord']}"
        detail = ""
        if ch["replaced_by"]:
            by_txt = ", ".join(f"{b['id']} ({b['entry_id']})" if b.get("entry_id") else b["id"] for b in ch["replaced_by"])
            detail += f" — replaced by {by_txt}"
        if ch["contradicted_by"]:
            by_txt = ", ".join(f"{b['id']} ({b['entry_id']})" if b.get("entry_id") else b["id"] for b in ch["contradicted_by"])
            detail += f" — contradicted by {by_txt}"
        lines.append(f"  {ch['old_state']} -> {ch['new_state']}  {cid} ({ch['entry_id']}): {ch['text']}{detail}")

    lines.extend(["", f"Questions opened ({c['questions_opened']})"])
    for q in rep["questions_opened"]:
        lines.append(f"  {q['date']}  {q['id']} [{q['status']}] {q['title']}")

    lines.extend(["", f"Questions answered ({c['questions_answered']})"])
    for q in rep["questions_answered"]:
        lines.append(f"  {q['date']}  {q['id']} -> {', '.join(q['answered_by'])}: {q['title']}")

    lines.extend(["", f"Questions parked ({c['questions_parked']})"])
    for q in rep["questions_parked"]:
        lines.append(f"  {q['date']}  {q['id']}: {q['title']}")

    return "\n".join(lines)
