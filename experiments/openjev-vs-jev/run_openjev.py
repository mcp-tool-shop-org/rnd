"""Send the built requests to a local Jev-style decision endpoint (stdlib only).

    python run_openjev.py [--url http://127.0.0.1:8765/v1/systemone] [--repeat 5]
    python run_openjev.py --url http://127.0.0.1:8009/v1/systemone --name kev4b
    python run_openjev.py --url ... --name kev4b-knowledge --requests requests-knowledge.jsonl

Writes $OPENJEV_WORK/<name>.jsonl (default openjev.jsonl) and <name>-determinism.json
(determinism.json for the default). --repeat re-asks the first N phrases to check
that the answers are deterministic.
"""

import argparse
import json
import os
import time
import urllib.request
from pathlib import Path

WORK = Path(os.environ.get("OPENJEV_WORK", "E:/AI-Models/openjev/work"))


def ask(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers={"content-type": "application/json"}, method="POST")
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=300) as r:
        reply = json.loads(r.read())
    return reply, time.perf_counter() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8765/v1/systemone")
    ap.add_argument("--repeat", type=int, default=5)
    ap.add_argument("--name", default="openjev", help="output stem; the probability field is <name>_p_yes")
    ap.add_argument("--requests", default="requests.jsonl")
    args = ap.parse_args()
    rows = [json.loads(line) for line in (WORK / args.requests).read_text(encoding="utf-8").splitlines()]
    out = WORK / f"{args.name}.jsonl"
    field = f"{args.name}_p_yes"
    with out.open("w", encoding="utf-8") as fh:
        for n, row in enumerate(rows, 1):
            reply, secs = ask(args.url, row["body"])
            ans = reply["answers"]["phrase_clean"]
            rec = {"id": row["id"], "label": row["label"], "jev_p_yes": row["jev_p_yes"],
                   field: ans["noul"], "seconds": round(secs, 3),
                   "input_tokens": (reply.get("usage") or {}).get("input_tokens"), "model": reply.get("model")}
            fh.write(json.dumps(rec) + "\n")
            print(f"{n:>3}/{len(rows)} {row['id']:<48} {args.name}={ans['noul']:.4f} jev={row['jev_p_yes']:.4f} {secs:.2f}s")
    repeats = []
    for row in rows[: args.repeat]:
        a, _ = ask(args.url, row["body"])
        b, _ = ask(args.url, row["body"])
        repeats.append((row["id"], a["answers"]["phrase_clean"]["noul"], b["answers"]["phrase_clean"]["noul"]))
    (WORK / ("determinism.json" if args.name == "openjev" else f"{args.name}-determinism.json")).write_text(json.dumps(repeats, indent=1), encoding="utf-8")
    print("determinism:", "identical" if all(x == y for _, x, y in repeats) else repeats)


if __name__ == "__main__":
    main()
