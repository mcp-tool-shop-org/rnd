"""Mine candidate queries from Claude Code session logs (design v3, section 4).

Reads every session transcript under ~/.claude/projects and keeps the search strings agents actually issued:
`rnd search <words>` and `rnd readouts <words>` in Bash calls, and the `query` of offrig_memory_search calls.
Only tool-call arguments are read; no user message is copied. For each session the first query of a run of
searches is kept and later reformulations within five minutes are marked, so a pick can take the first query
per information need. Output: BENCH/query-candidates.jsonl (private; R&D picks from it by hand).

Run: E:/AI/envs/embedgemma/Scripts/python.exe collect_queries.py
"""

from __future__ import annotations

import json
import re
import shlex
from datetime import datetime
from pathlib import Path

from common import BENCH, write_jsonl

LOGS = Path.home() / ".claude" / "projects"
RND = re.compile(r"(?:python(?:\.exe)?\s+-m\s+rnd|rnd)\s+(search|readouts)\s+(.+?)(?:\s*(?:\||&&|;|2>|>|$))")


def when(stamp: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00")) if stamp else None
    except ValueError:
        return None


def from_bash(cmd: str) -> list[tuple[str, str]]:
    out = []
    for m in RND.finditer(cmd):
        try:
            words = [w for w in shlex.split(m.group(2)) if not w.startswith("-")]
        except ValueError:
            continue
        if words:
            out.append((f"rnd {m.group(1)}", " ".join(words)))
    return out


def main() -> None:
    rows = []
    for path in sorted(LOGS.rglob("*.jsonl")):
        session = path.stem
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = ev.get("message") or {}
            if msg.get("role") != "assistant" or not isinstance(msg.get("content"), list):
                continue
            for part in msg["content"]:
                if part.get("type") != "tool_use":
                    continue
                name, args = part.get("name", ""), part.get("input") or {}
                hits = []
                if name in ("Bash", "PowerShell") and isinstance(args.get("command"), str):
                    hits = from_bash(args["command"])
                elif name.endswith("offrig_memory_search") and isinstance(args.get("query"), str):
                    hits = [("offrig_memory_search", args["query"].strip())]
                for tool, q in hits:
                    rows.append({"session": session, "project": path.parent.name, "at": ev.get("timestamp"),
                                 "tool": tool, "query": q})
    rows.sort(key=lambda r: (r["session"], r["at"] or ""))
    prev: dict[str, dict] = {}
    for r in rows:
        last = prev.get(r["session"])
        t, lt = when(r["at"]), when(last["at"]) if last else None
        r["reformulation"] = bool(last and t and lt and (t - lt).total_seconds() < 300)
        prev[r["session"]] = r
    seen, firsts = set(), []
    for r in rows:
        key = r["query"].lower()
        if not r["reformulation"] and key not in seen:
            seen.add(key)
            firsts.append(r)
    write_jsonl(BENCH / "query-candidates.jsonl", rows)
    write_jsonl(BENCH / "query-firsts.jsonl", firsts)
    print(f"{len(rows)} search calls; {len(firsts)} distinct first queries")


if __name__ == "__main__":
    main()
