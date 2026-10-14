"""Stage 0 of the interlock-relay design: the readers and the five pre-registered questions (H4a, H4b).

Frozen before any planted case runs. Nothing here imports interlock or Relay: it reads files and receipt rows.

- `read_studio_trace(path)`: one schema-aware reader for ATOF files, with no branch on which tool wrote the file.
  It returns every scope as a normalised record. The fields H4b compares are
  `(span_id, parent_id, start_ns, end_ns, model, prompt_tokens, completion_tokens, status)`; the record also keeps
  the scope's category, name and metadata, which the questions read.
- `read_events(path)`: the native event log (`logs/<run_id>.events.jsonl`), as the same call records.
- `diagnose_from_trace(path)` and `diagnose_from_events(path)`: the five answers from an ordered log.
- `diagnose_from_receipt(row)`: the five answers from `artifacts.call_counts` alone. It answers by elimination
  wherever the counts rule out one of a question's two options, so the aggregate counter gets its best fair score.

Every answer is a string from the question's options, or CANT.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

CANT = "can't tell"
QUESTIONS = ("q1_count_growth", "q2_companion", "q3_unload_order", "q4_count_timeout", "q5_openvino_runaway")
NORMALISED = ("span_id", "parent_id", "start_ns", "end_ns", "model", "prompt_tokens", "completion_tokens", "status")


# -- readers ------------------------------------------------------------------------------------------------------


def _ns(stamp: str) -> int:
    """An ATOF timestamp (RFC 3339, with up to nine fraction digits) as integer nanoseconds since the epoch."""

    stamp = stamp.replace("Z", "+00:00")
    head, _, rest = stamp.partition(".")
    fraction, zone = (rest[:-6], rest[-6:]) if rest else ("", stamp[-6:])
    if not rest:
        head = stamp[:-6]
    whole = datetime.fromisoformat(head + zone)
    nanos = int((fraction + "000000000")[:9]) if fraction else 0
    return int(whole.timestamp()) * 1_000_000_000 + nanos


def _usage(*places) -> tuple[int | None, int | None]:
    for place in places:
        if not isinstance(place, dict):
            continue
        usage = place.get("usage") if isinstance(place.get("usage"), dict) else place
        prompt = usage.get("prompt_tokens", usage.get("input_tokens"))
        completion = usage.get("completion_tokens", usage.get("output_tokens"))
        if isinstance(prompt, int) or isinstance(completion, int):
            return (prompt if isinstance(prompt, int) else None, completion if isinstance(completion, int) else None)
    return None, None


def _status(metadata: dict, end: dict) -> str | None:
    if isinstance(metadata.get("status"), str):
        return metadata["status"]
    code = metadata.get("otel.status_code")
    if code == "OK":
        return "ok"
    if code == "ERROR":
        return "error"
    return None


def read_studio_trace(path: Path) -> list[dict]:
    """Every ATOF scope in the file, start and end paired by uuid, in start order. Marks are kept as zero-length
    records with category "mark"."""

    starts: dict[str, dict] = {}
    ends: dict[str, dict] = {}
    marks: list[dict] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("kind") == "mark":
            marks.append(event)
        elif event.get("kind") == "scope":
            (starts if event.get("scope_category") == "start" else ends)[event["uuid"]] = event
    records = []
    for uuid, start in starts.items():
        end = ends.get(uuid, {})
        metadata = {**(start.get("metadata") or {}), **(end.get("metadata") or {})}
        prompt, completion = _usage(metadata, end.get("data"), (end.get("data") or {}).get("annotated_response")
                                    if isinstance(end.get("data"), dict) else None)
        records.append({
            "span_id": uuid,
            "parent_id": start.get("parent_uuid"),
            "start_ns": _ns(start["timestamp"]),
            "end_ns": _ns(end["timestamp"]) if end else None,
            "model": (start.get("category_profile") or {}).get("model_name"),
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "status": _status(metadata, end) if end else "open",
            "category": start.get("category"),
            "name": start.get("name"),
            "metadata": metadata,
        })
    for mark in marks:
        t = _ns(mark["timestamp"])
        records.append({"span_id": mark["uuid"], "parent_id": mark.get("parent_uuid"), "start_ns": t, "end_ns": t,
                        "model": None, "prompt_tokens": None, "completion_tokens": None, "status": None,
                        "category": "mark", "name": mark.get("name"), "metadata": mark.get("data") or {}})
    return sorted(records, key=lambda r: (r["start_ns"], r["span_id"]))


def normalised(records: list[dict]) -> list[tuple]:
    """The H4b comparison set: the eight fields of every model-call record."""

    return [tuple(r[f] for f in NORMALISED) for r in records if r["category"] == "llm"]


def _call(kind, slot, start_ns, end_ns, status, extra) -> dict:
    return {"kind": kind, "slot": slot, "endpoint": extra.get("endpoint"), "start_ns": start_ns, "end_ns": end_ns,
            "status": status,
            "ms": None if end_ns is None else (end_ns - start_ns) / 1e6,
            "worker_still_running": bool(extra.get("worker_still_running"))}


def calls_from_trace(records: list[dict]) -> list[dict]:
    return [_call(r["metadata"].get("kind"), r["metadata"].get("slot"), r["start_ns"], r["end_ns"], r["status"],
                  r["metadata"]) for r in records if r["category"] == "llm"]


def read_events(path: Path) -> list[dict]:
    calls = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if "call_id" in event:
            calls.append(_call(event.get("kind"), event.get("slot"), event["t_ns"], event.get("end_ns"),
                               event.get("status"), event))
    return sorted(calls, key=lambda c: c["start_ns"])


# -- the five questions, from an ordered log ---------------------------------------------------------------------


def _q1(calls):
    """Did count-call latency grow monotonically across the steps of the slot?"""

    ms = [c["ms"] for c in calls if c["kind"] == "count" and c["ms"] is not None]
    if len(ms) < 2:
        return CANT
    return "grew" if all(b > a for a, b in zip(ms, ms[1:])) else "did not grow"


def _q2(calls):
    """Did the companion call overlap the generate call in wall-clock time, or finish before it started?"""

    comp = [c for c in calls if c["kind"] == "companion" and c["end_ns"] is not None]
    gen = [c for c in calls if c["kind"] == "generate" and c["end_ns"] is not None]
    if len(comp) != 1 or len(gen) != 1:
        return CANT
    a, b = comp[0], gen[0]
    if a["end_ns"] <= b["start_ns"]:
        return "finished before"
    if a["start_ns"] < b["end_ns"] and b["start_ns"] < a["end_ns"]:
        return "overlapped"
    return CANT


def _q3(calls):
    """What was the order: unload, generate, unload; or unload, companion?"""

    seq = [c["kind"] for c in calls if c["kind"] in ("unload", "generate", "companion")]
    if seq[:3] == ["unload", "generate", "unload"]:
        return "unload-generate-unload"
    if seq[:2] == ["unload", "companion"]:
        return "unload-companion"
    return CANT


def _q4(calls):
    """Was the timed-out count retried and successful before the main generate call, or did it fail after it?"""

    gen = [c for c in calls if c["kind"] == "generate"]
    counts = [c for c in calls if c["kind"] == "count"]
    timeouts = [c for c in counts if c["status"] == "timeout"]
    if not gen or not timeouts:
        return CANT
    g = gen[0]["start_ns"]
    t = timeouts[0]
    if t["end_ns"] <= g and any(c["status"] == "ok" and c["start_ns"] >= t["end_ns"] and c["end_ns"] <= g
                                for c in counts):
        return "retried and succeeded before"
    if t["start_ns"] >= gen[0]["end_ns"] and not any(c["status"] == "ok" and c["start_ns"] > t["start_ns"]
                                                     for c in counts):
        return "failed after"
    return CANT


def _q5(calls):
    """Which call in a multi-call OpenVINO slot left its worker running, and did later calls run while it was?"""

    ov = [c for c in calls if str(c.get("endpoint") or "").startswith("openvino/")]
    if len(ov) < 2:
        return CANT
    stuck = [i for i, c in enumerate(ov) if c["worker_still_running"]]
    if len(stuck) != 1:
        return CANT
    i = stuck[0]
    later = any(c["start_ns"] >= ov[i]["end_ns"] for c in ov[i + 1:])
    return f"call {i + 1}; later calls ran: {'yes' if later else 'no'}"


def diagnose_calls(calls: list[dict]) -> dict:
    return dict(zip(QUESTIONS, (_q1(calls), _q2(calls), _q3(calls), _q4(calls), _q5(calls))))


def diagnose_from_trace(path: Path) -> dict:
    return diagnose_calls(calls_from_trace(read_studio_trace(path)))


def diagnose_from_events(path: Path) -> dict:
    return diagnose_calls(read_events(path))


# -- the same questions, from the aggregate counter ---------------------------------------------------------------


def diagnose_from_receipt(row: dict) -> dict:
    counts = (row.get("artifacts") or {}).get("call_counts") or {}

    def n(kind, key="n"):
        return (counts.get(kind) or {}).get(key, 0)

    out = dict.fromkeys(QUESTIONS, CANT)
    # Q1 and Q2 need per-call times and wall-clock order: a per-kind sum has neither.
    # Q3: answer only when the counts make one of the two orders impossible.
    a = n("unload") >= 2 and n("generate") >= 1
    b = n("unload") >= 1 and n("companion") >= 1
    if a != b:
        out["q3_unload_order"] = "unload-generate-unload" if a else "unload-companion"
    # Q4: with no successful count, "retried and succeeded" is impossible.
    if n("count", "timeouts") >= 1 and n("generate") >= 1:
        succeeded = n("count") - n("count", "timeouts") - n("count", "errors")
        if succeeded == 0:
            out["q4_count_timeout"] = "failed after"
    # Q5: which of several calls, and what ran after it, is order the counter does not keep.
    return out
