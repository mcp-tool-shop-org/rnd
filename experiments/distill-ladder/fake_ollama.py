"""A stand-in for Ollama on loopback, for the distillation exercise's data steps (PLAN.md, Data). No model, no card.

`offrig verify calibrate --url http://127.0.0.1:<port>` renders its own prompt for every claim and sends it here, so:
- **capture:** every `/api/chat` request body is appended to `--log`, one JSON object a line. The training rows take
  their system and user messages from these, byte for byte as offrig sends them;
- **replay:** `--replies <file.jsonl>` maps claim ids to the assistant text to return (rows `{"id", "content"}`), so a
  set of targets can be scored by offrig's own parser and quote rule before any training. A claim with no reply gets
  a well-formed `cannot_tell`.

The claim id is read from the prompt's `CLAIM (id <id>):` line. The model is reported with the name, digest and
context length given on the command line, and as having thinking, so offrig's settings checks pass.

  python -I fake_ollama.py --port 11493 --model distill-fake --log requests.jsonl [--replies replies.jsonl]
"""

import argparse
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CLAIM_ID = re.compile(r"^CLAIM \(id ([^)]+)\):$", re.M)
DEFAULT = {"reasoning": "No reply was supplied for this claim.", "verdict": "cannot_tell", "evidence_quote": "",
           "evidence_source": ""}


def make_handler(model: str, digest: str, ctx: int, log: Path, replies: dict, lock: threading.Lock):
    tag = {"name": model, "model": model, "modified_at": "2026-10-22T00:00:00Z", "size": 1, "digest": digest,
           "details": {"format": "gguf", "family": "qwen3", "parameter_size": "1.7B", "quantization_level": "Q8_0"}}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def _send(self, obj, status=200):
            data = json.dumps(obj).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _body(self):
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n) or b"{}")

        def do_GET(self):
            if self.path == "/api/version":
                return self._send({"version": "0.0.0-fake"})
            if self.path == "/api/tags":
                return self._send({"models": [tag]})
            if self.path == "/api/ps":
                return self._send({"models": []})
            return self._send({"error": f"not served: {self.path}"}, 404)

        def do_POST(self):
            body = self._body()
            if self.path == "/api/show":
                return self._send({"capabilities": ["completion", "thinking"], "details": tag["details"],
                                   "model_info": {"general.architecture": "qwen3", "qwen3.context_length": ctx}})
            if self.path == "/api/generate":
                return self._send({"model": model, "response": "", "done": True, "done_reason": "unload"})
            if self.path != "/api/chat":
                return self._send({"error": f"not served: {self.path}"}, 404)
            user = next((m["content"] for m in body.get("messages", []) if m.get("role") == "user"), "")
            found = CLAIM_ID.search(user)
            cid = found.group(1) if found else None
            with lock, log.open("a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps({"id": cid, "request": body}, ensure_ascii=False) + "\n")
            content = replies.get(cid) if cid is not None else None
            if content is None:
                content = json.dumps(DEFAULT)
            return self._send({"model": model, "created_at": "2026-10-22T00:00:00Z",
                               "message": {"role": "assistant", "content": content}, "done": True,
                               "done_reason": "stop", "prompt_eval_count": len(user) // 4, "eval_count": len(content) // 4})

        def do_DELETE(self):
            return self._send({})

    return Handler


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=11493)
    ap.add_argument("--model", default="distill-fake")
    ap.add_argument("--digest", default="0" * 64)
    ap.add_argument("--ctx", type=int, default=32768)
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--replies", type=Path)
    a = ap.parse_args()
    replies = {}
    if a.replies:
        for line in a.replies.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                replies[r["id"]] = r["content"]
    server = ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(a.model, a.digest, a.ctx, a.log, replies, threading.Lock()))
    print(f"fake ollama on 127.0.0.1:{a.port} as {a.model}; {len(replies)} replies; logging to {a.log}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
