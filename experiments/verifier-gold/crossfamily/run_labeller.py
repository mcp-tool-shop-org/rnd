"""Label the blind sample with a local Ollama model from another family. One claim per call, thinking on,
the reply constrained to JSON. Same instructions the Claude labellers had. Run only in a slot the Publisher
has granted, against the local Ollama (never a cloud model: Standing Rule 1).

  python run_labeller.py --model gemma4:31b --out blind_out_gemma4-31b.json
"""

import argparse
import json
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent

INSTRUCTIONS = """You are labelling a claim about code for a gold test set. Judge only from the evidence below.
Each evidence block names its source: repo, PR or commit, SHA, file and lines, and, for a change, whether it
is the code "(before)" or "(after)" the change.

Labels:
- "supported": every part of the claim holds in the evidence, including, for a change, what changed, what
  stayed the same, the direction of the change and its scope.
- "unsupported": the evidence contradicts some part of the claim.
- "cannot_tell": the evidence neither establishes nor contradicts the claim, for example because the deciding
  code isn't shown.
Be strict: a claim with one wrong part is unsupported. Read the code carefully, including language semantics
(operator precedence, short-circuiting, inclusive vs exclusive bounds, type coercion, statement order,
exceptions). Comments and docstrings are not proof of behaviour; the code is. Don't guess at code you can't
see.

Reply with a JSON object: {"reasoning": "<one to three short sentences citing the deciding evidence>",
"label": "supported" | "unsupported" | "cannot_tell"}"""

SCHEMA = {
    "type": "object",
    "properties": {
        "reasoning": {"type": "string"},
        "label": {"type": "string", "enum": ["supported", "unsupported", "cannot_tell"]},
    },
    "required": ["reasoning", "label"],
}


def prompt(item: dict) -> str:
    ev = "\n\n".join(f"[source: {e['source']}]\n{e['text']}" for e in item["evidence"])
    return f"{INSTRUCTIONS}\n\nCLAIM: {item['claim']}\n\nEVIDENCE:\n{ev}"


def ask(host: str, model: str, text: str, timeout: int) -> dict:
    body = {"model": model, "messages": [{"role": "user", "content": text}], "stream": False, "think": True,
            "format": SCHEMA, "options": {"temperature": 0, "num_ctx": 16384}, "keep_alive": "10m"}
    req = urllib.request.Request(f"{host}/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--host", default="http://127.0.0.1:11434")
    ap.add_argument("--timeout", type=int, default=600)
    a = ap.parse_args()
    if "cloud" in a.model:
        raise SystemExit("cloud models are off (Standing Rule 1)")
    items = json.loads((HERE / "blind_in.json").read_text(encoding="utf-8"))
    out = HERE / a.out
    done = json.loads(out.read_text(encoding="utf-8")) if out.exists() else []
    seen = {d["n"] for d in done}
    for item in items:
        if item["n"] in seen:
            continue
        t0 = time.time()
        try:
            r = ask(a.host, a.model, prompt(item), a.timeout)
            reply = json.loads(r["message"]["content"])
            row = {"n": item["n"], "label": reply.get("label"), "reasoning": reply.get("reasoning", ""),
                   "eval_tokens": r.get("eval_count"), "seconds": round(time.time() - t0, 1)}
        except Exception as e:  # a failed call is recorded, not retried silently
            row = {"n": item["n"], "label": None, "reasoning": f"error: {e}", "seconds": round(time.time() - t0, 1)}
        done.append(row)
        out.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{item['n']:3} {row['label']} {row['seconds']}s", flush=True)


if __name__ == "__main__":
    main()
