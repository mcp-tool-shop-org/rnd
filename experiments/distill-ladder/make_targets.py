"""The distillation exercise's training rows (PLAN.md, Data; Argon round 1, B1): sft.py's `{"messages": [...]}` rows for
arms B-full, B-matched and C.

The prompt is offrig's own. `offrig verify calibrate` is run over the training items against `fake_ollama.py` with the
student's settings (thinking off), and each claim's system and user messages are taken from the logged request, byte
for byte. offrig sends a 1-token sizing call before a claim's real call; the request kept is the last one with
`num_predict` above 1.

The target is offrig's reply contract, keys in its order (reasoning, verdict, evidence_quote, evidence_source), as
compact JSON:
- **B (the oracle):** the function is run line by line with its input; `reasoning` names each executed line and the
  value of `v` after it, then what f returns and what the claim says; `verdict` is the item's label; `evidence_quote`
  is the last executed line before `return v` (a whole line, as offrig's quote rule wants); `evidence_source` is
  `ctx1`.
- **C (the teacher):** the teacher's own `reasoning` and `evidence_quote` from its offrig verdicts, kept only where its
  `final_verdict` (after offrig's quote rule) equals the label; `verdict` is that final verdict; `evidence_source` is
  `ctx1`.
- **B-matched:** B's rows for exactly the items C kept.

`--replies` writes `{"id", "content"}` rows for fake_ollama.py's replay, so offrig itself can score a target set.

  python -I make_targets.py b --train train.jsonl --requests requests.jsonl --out b-full.jsonl [--replies b-replies.jsonl]
  python -I make_targets.py c --train train.jsonl --requests requests.jsonl --verdicts verdicts.jsonl --out c.jsonl
  python -I make_targets.py matched --b b-full.jsonl --c c.jsonl --out b-matched.jsonl
"""

import argparse
import json
import sys
from pathlib import Path

KEYS = ("reasoning", "verdict", "evidence_quote", "evidence_source")


def read(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def prompts(requests: Path) -> dict[str, list[dict]]:
    """Each claim id's system and user messages, from its last real (num_predict > 1) call."""

    out = {}
    for r in read(requests):
        body = r["request"]
        if r.get("id") is None or (body.get("options") or {}).get("num_predict", 0) <= 1:
            continue
        msgs = [{"role": m["role"], "content": m["content"]} for m in body["messages"]]
        if [m["role"] for m in msgs] != ["system", "user"]:
            raise SystemExit(f"{r['id']}: expected a system and a user message, got {[m['role'] for m in msgs]}")
        out[r["id"]] = msgs
    return out


def trace(src: str, x: int) -> tuple[list[tuple[str, int]], int]:
    """Run f(x) and record (line, v after it) for every executed line that assigns v, in order."""

    lines = src.split("\n")
    steps: list[tuple[str, int]] = []
    pending: list[str] = []

    def tracer(frame, event, arg):
        if frame.f_code.co_name != "f":
            return tracer
        if event in ("line", "return") and pending:
            if "v" in frame.f_locals:
                steps.append((pending.pop(), frame.f_locals["v"]))
            else:
                pending.pop()
        if event == "line":
            text = lines[frame.f_lineno - 1].strip()
            if text.startswith("v = "):
                pending.append(text)
        return tracer

    env = {"__builtins__": {"range": range, "round": round, "int": int}}
    exec(compile(src, "<ladder>", "exec"), env)  # our own generated source, not external input
    sys.settrace(tracer)
    try:
        result = env["f"](x)
    finally:
        sys.settrace(None)
    return steps, result


def oracle(row: dict) -> dict:
    src = row["context"][0]["text"]
    x = int(row["claim"].split("`f(")[1].split(")`")[0])
    claimed = row["claim"].rsplit(" returns ", 1)[1].rstrip(".")
    steps, result = trace(src, x)
    if result != row["ladder"]["true"]:
        raise SystemExit(f"{row['id']}: the trace returns {result}, the generator's truth is {row['ladder']['true']}")
    parts = [f"x is {x}."] + [f"{line} gives v = {v}." for line, v in steps]
    match = str(result) == claimed
    parts.append(f"f returns {result}; the claim says {claimed}, so it {'matches' if match else 'does not match'}.")
    verdict = "supported" if match else "unsupported"
    if verdict != row["label"]:
        raise SystemExit(f"{row['id']}: the oracle reads {verdict}, the label is {row['label']}")
    return {"reasoning": " ".join(parts), "verdict": verdict, "evidence_quote": steps[-1][0], "evidence_source": "ctx1"}


def sft_row(rid: str, msgs: list[dict], contract: dict) -> dict:
    content = json.dumps({k: contract[k] for k in KEYS}, ensure_ascii=False, separators=(",", ":"))
    return {"id": rid, "messages": msgs + [{"role": "assistant", "content": content}]}


def write(rows: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8", newline="\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("arm", choices=("b", "c", "matched"))
    ap.add_argument("--train", type=Path)
    ap.add_argument("--requests", type=Path)
    ap.add_argument("--verdicts", type=Path)
    ap.add_argument("--b", type=Path)
    ap.add_argument("--c", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--replies", type=Path)
    a = ap.parse_args()
    if a.arm == "matched":
        keep = {r["id"] for r in read(a.c)}
        rows = [r for r in read(a.b) if r["id"] in keep]
        if len(rows) != len(keep):
            raise SystemExit(f"B holds {len(rows)} of C's {len(keep)} ids")
        write(rows, a.out)
        print(json.dumps({"arm": "B-matched", "rows": len(rows)}))
        return
    train = read(a.train)
    msgs = prompts(a.requests)
    missing = [r["id"] for r in train if r["id"] not in msgs]
    if missing:
        raise SystemExit(f"{len(missing)} training items have no captured prompt, e.g. {missing[:3]}")
    rows, dropped = [], {}
    if a.arm == "b":
        for r in train:
            rows.append(sft_row(r["id"], msgs[r["id"]], oracle(r)))
    else:
        by_id = {r["id"]: r for r in train}
        verdicts = [v for v in read(a.verdicts) if v["claim_id"] in by_id]
        seen = [v["claim_id"] for v in verdicts]
        if len(seen) != len(set(seen)) or set(seen) != set(by_id):
            # Every training item once, across the resumed teacher windows (Argon round 2, N1).
            raise SystemExit(f"the verdicts cover {len(set(seen))} of {len(by_id)} training items, "
                             f"with {len(seen) - len(set(seen))} repeated")
        for v in verdicts:
            r = by_id[v["claim_id"]]
            fv = v.get("final_verdict")
            if fv != r["label"]:
                dropped[str(fv)] = dropped.get(str(fv), 0) + 1
                continue
            rows.append(sft_row(r["id"], msgs[r["id"]], {"reasoning": v.get("reasoning") or "", "verdict": fv,
                                                         "evidence_quote": v.get("evidence_quote") or "",
                                                         "evidence_source": "ctx1"}))
    write(rows, a.out)
    if a.replies:
        write([{"id": r["id"], "content": r["messages"][-1]["content"]} for r in rows], a.replies)
    print(json.dumps({"arm": a.arm.upper(), "rows": len(rows), "dropped_by_final_verdict": dropped}))


if __name__ == "__main__":
    main()
