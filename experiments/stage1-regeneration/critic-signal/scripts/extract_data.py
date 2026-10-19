"""Write the critic-signal study's public data files from local receipts. No item text leaves the rig: only ids,
counts, codes, timings and token counts.

  python extract_data.py <publisher-receipts-dir> <rnd-local-phase2-dir>

Writes into ../data/:
- calls.csv: one row per critic call in windows 13w, 13x and 13y, from the rnd proxy's generations.jsonl (the
  record of truth for thinking tokens). The check kind is read from the reply's shape (a verdict reply starts
  "VERDICT"); the reply itself isn't written.
- outcomes.csv: one row per scored item, critic and rule set, from critic-rescore-offline's output.
"""

import csv
import json
import sys
from pathlib import Path

RECEIPTS, LOCAL = Path(sys.argv[1]), Path(sys.argv[2])
OUT = Path(__file__).resolve().parents[1] / "data"
OUT.mkdir(exist_ok=True)
RUNS = [("13w", "muse-glimmer-30b", 0, "window13w-critic-eval-muse-s0-20261019/out/critic-eval/s0"),
        ("13x", "muse-glimmer-30b", 1, "window13x-critic-eval-muse-s1-20261019/out/critic-eval/s1"),
        ("13y", "nemotron-3.5-lightning-30b-a3b", 0, "window13y-critic-eval-lightning-s0-20261019/out/critic-eval/s0")]

with open(OUT / "calls.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["window", "critic", "seed", "call_index", "check", "wall_time_s", "prompt_tokens", "output_tokens",
                "thinking_tokens", "thinking_source", "finish_reason"])
    for win, critic, seed, rel in RUNS:
        for line in (RECEIPTS / rel / "generations.jsonl").read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            reply = (d.get("response") or "").lstrip()
            check = "verdict" if reply.upper().startswith("VERDICT") else ("empty" if not reply else "flaw")
            w.writerow([win, critic, seed, d.get("call_index"), check, round(float(d.get("wall_time_s") or 0), 2),
                        d.get("prompt_tokens"), d.get("output_tokens"),
                        "" if d.get("thinking_tokens") is None else d["thinking_tokens"],
                        d.get("thinking_tokens_source") or "", d.get("finish_reason") or ""])

with open(OUT / "outcomes.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["critic", "runs", "rule_set", "item_id", "perturbation_type", "kind", "accepted", "deciding_rule"])
    for critic, runs, rel in (("muse-glimmer-30b", "13w+13x", "13x/offline"),
                              ("nemotron-3.5-lightning-30b-a3b", "13y", "13y/offline")):
        for line in (LOCAL / rel / "critic-rescore-offline.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            w.writerow([critic, runs, r["rule_set"], r["item_id"], r["perturbation_type"], r["kind"],
                        int(bool(r["accepted"])), r["deciding_rule"]])
print("wrote", OUT / "calls.csv", OUT / "outcomes.csv")
