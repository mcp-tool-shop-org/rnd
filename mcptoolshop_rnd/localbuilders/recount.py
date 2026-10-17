"""Re-measure a generations file's thinking counts with the current rules, without rerunning anything.

  python -m mcptoolshop_rnd.localbuilders.recount <generations.jsonl> <out.jsonl>

Each line's `thinking_tokens` and `thinking_tokens_source` are recomputed from the reply it already stores (its
`upstream_response`, `tokens`, `reasoning_content` and `output_tokens`), so a record whose count was null before the
2026-10-17 fix (a reply cut off at the length limit, or a harmony-style template) gets its count. The original file is
never written; `<out.jsonl>` must not exist. A line whose count changes keeps its old value as `thinking_tokens_was`.
Prints a summary: calls, counts that were null, counts still null, and thinking over output tokens.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from mcptoolshop_rnd.localbuilders.proxy import _thinking_count


def recount(src: Path, dest: Path) -> dict:
    if dest.exists():
        raise SystemExit(f"{dest} exists; recount never overwrites")
    if dest.resolve() == src.resolve():
        raise SystemExit("recount never rewrites its input")
    out, summary = [], {"calls": 0, "null_before": 0, "null_after": 0, "changed": 0, "thinking_tokens": 0, "output_tokens": 0}
    for line in src.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        summary["calls"] += 1
        before = r.get("thinking_tokens")
        upstream = r.get("upstream_response") if isinstance(r.get("upstream_response"), dict) else {}
        n, source = _thinking_count(upstream, list(r.get("tokens") or []), r.get("reasoning_content"), int(r.get("output_tokens") or 0))
        if before is None:
            summary["null_before"] += 1
        if n is None:
            summary["null_after"] += 1
        if n != before:
            summary["changed"] += 1
            r["thinking_tokens_was"] = before
        r["thinking_tokens"], r["thinking_tokens_source"] = n, source
        if n is not None:
            r["thinking_words_estimate"] = None
            summary["thinking_tokens"] += n
        summary["output_tokens"] += int(r.get("output_tokens") or 0)
        out.append(json.dumps(r, ensure_ascii=False))
    dest.write_text("".join(x + "\n" for x in out), encoding="utf-8", newline="\n")
    return summary


if __name__ == "__main__":  # pragma: no cover - the CLI shell around recount()
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    print(json.dumps(recount(Path(sys.argv[1]), Path(sys.argv[2]))))
