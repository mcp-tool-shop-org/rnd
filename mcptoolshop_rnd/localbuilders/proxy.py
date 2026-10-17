"""Loopback logging proxy between Aider and llama-server (F1, F3, F4, F5).

Responsibilities:
- F1: Always sends `stream: false` upstream so `--reasoning-format deepseek` separates thinking.
- F3: Overrides Aider's sampling (`temperature`, `top_p`, `top_k`, `min_p`, etc.) with the candidate's
  pinned card values, and injects `chat_template_kwargs`, both loaded from a per-candidate JSON config
  file passed in. Never hard-codes model values. Records the exact injected dict on every
  `generations.jsonl` line.
- F4: Counts model calls per task and refuses the 31st (HTTP 429, recorded in `generations.jsonl`),
  and enforces the 15-minute task wall (900 s).
- F5: Adds `logprobs: true, top_logprobs: 5` upstream. Writes the full response (`logprobs` and
  `reasoning_content` included) to `generations.jsonl` in `mcptoolshop_rnd.abmine`'s format, plus
  `llama-server`'s `timings` and wall time. Strips `logprobs` and `reasoning_content` from the reply
  returned to Aider, which gets a plain OpenAI completion.
- Records thinking tokens, output tokens, and truncation (`finish_reason == "length"`) per call.

Standard library only (`http.server` + `urllib`).
"""
from __future__ import annotations

import copy
import hashlib
import http.server
import json
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

DEFAULT_MAX_CALLS = 30
DEFAULT_WALL_LIMIT_S = 15 * 60.0  # 15 minutes
TOP_LOGPROBS_K = 5

SAMPLING_KEYS = (
    "temperature",
    "top_p",
    "top_k",
    "min_p",
    "repeat_penalty",
    "presence_penalty",
    "frequency_penalty",
    "mirostat",
    "mirostat_tau",
    "mirostat_eta",
    "seed",
)


class ProxyConfigError(Exception):
    """Raised when a per-candidate config file is missing or malformed."""


@dataclass(frozen=True)
class CandidateConfig:
    """Per-candidate sampling and template kwargs loaded from a JSON file (F3)."""

    arm: str
    sampling: dict
    chat_template_kwargs: dict
    config_sha256: str
    extra: dict = field(default_factory=dict)

    @property
    def injected_dict(self) -> dict:
        """The exact injected dictionary recorded on every generations.jsonl line and receipt."""
        return {
            "sampling": copy.deepcopy(self.sampling),
            "chat_template_kwargs": copy.deepcopy(self.chat_template_kwargs),
        }


def load_candidate_config(path: str | Path) -> CandidateConfig:
    """Load per-candidate sampling and chat_template_kwargs from JSON.

    Never supplies model-specific defaults: the JSON file must explicitly define
    `sampling` (a dict) and `chat_template_kwargs` (a dict).
    """
    p = Path(path)
    if not p.is_file():
        raise ProxyConfigError(f"candidate config file not found: {p}")
    raw_bytes = p.read_bytes()
    config_sha = hashlib.sha256(raw_bytes.replace(b"\r\n", b"\n")).hexdigest()
    try:
        data = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProxyConfigError(f"candidate config {p} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ProxyConfigError(f"candidate config {p} must be a JSON object")
    sampling = data.get("sampling")
    if not isinstance(sampling, dict):
        raise ProxyConfigError(f"candidate config {p} must contain a 'sampling' object")
    kwargs = data.get("chat_template_kwargs")
    if not isinstance(kwargs, dict):
        raise ProxyConfigError(f"candidate config {p} must contain a 'chat_template_kwargs' object")
    arm = str(data.get("arm") or data.get("model") or p.stem)
    extra = {k: v for k, v in data.items() if k not in ("arm", "sampling", "chat_template_kwargs")}
    return CandidateConfig(
        arm=arm,
        sampling=copy.deepcopy(sampling),
        chat_template_kwargs=copy.deepcopy(kwargs),
        config_sha256=config_sha,
        extra=extra,
    )


def extract_abmine_logprobs(resp: dict) -> tuple[list[str], list[list[list]]]:
    """Extract (tokens, top) in `mcptoolshop_rnd.abmine` format from an OpenAI/llama-server reply."""
    choices = resp.get("choices") or []
    raw_lp = None
    if choices and isinstance(choices[0], dict):
        raw_lp = choices[0].get("logprobs")
    if raw_lp is None:
        raw_lp = resp.get("logprobs")

    items: list = []
    if isinstance(raw_lp, dict):
        items = raw_lp.get("content") or raw_lp.get("tokens") or []
    elif isinstance(raw_lp, list):
        items = raw_lp

    tokens: list[str] = []
    top: list[list[list]] = []
    for step in items:
        if not isinstance(step, dict):
            continue
        tok = str(step.get("token", ""))
        tokens.append(tok)
        step_top = []
        for cand in step.get("top_logprobs") or []:
            if isinstance(cand, dict) and "token" in cand and "logprob" in cand:
                step_top.append([str(cand["token"]), float(cand["logprob"])])
            elif isinstance(cand, (list, tuple)) and len(cand) >= 2:
                step_top.append([str(cand[0]), float(cand[1])])
        top.append(step_top)
    return tokens, top


def _extract_reasoning_and_content(resp: dict) -> tuple[str, str | None]:
    """Return (content, reasoning_content) from the first choice of a completion reply."""
    choices = resp.get("choices") or []
    if not choices or not isinstance(choices[0], dict):
        return str(resp.get("response", "")), resp.get("reasoning_content")
    ch = choices[0]
    msg = ch.get("message") if isinstance(ch.get("message"), dict) else {}
    content = msg.get("content")
    if content is None:
        content = ch.get("text", "")
    reasoning = msg.get("reasoning_content")
    if reasoning is None:
        reasoning = ch.get("reasoning_content")
    if reasoning is None:
        reasoning = resp.get("reasoning_content")
    return str(content or ""), (str(reasoning) if reasoning is not None else None)


def _count_tokens(resp: dict, tokens: list[str], reasoning: str | None) -> tuple[int, int, int]:
    """Return (prompt_tokens, thinking_tokens, output_tokens) for one model call."""
    usage = resp.get("usage") if isinstance(resp.get("usage"), dict) else {}
    timings = resp.get("timings") if isinstance(resp.get("timings"), dict) else {}

    prompt_tokens = usage.get("prompt_tokens")
    if prompt_tokens is None:
        prompt_tokens = timings.get("prompt_n")
    if prompt_tokens is None:
        prompt_tokens = resp.get("prompt_eval_count", 0)
    prompt_tokens = int(prompt_tokens or 0)

    output_tokens = usage.get("completion_tokens")
    if output_tokens is None:
        output_tokens = timings.get("predicted_n")
    if output_tokens is None:
        output_tokens = resp.get("eval_count")
    if output_tokens is None:
        output_tokens = len(tokens)
    output_tokens = int(output_tokens or 0)

    details = usage.get("completion_tokens_details")
    thinking_tokens = None
    if isinstance(details, dict):
        thinking_tokens = details.get("reasoning_tokens")
    if thinking_tokens is None:
        thinking_tokens = usage.get("reasoning_tokens")
    if thinking_tokens is None:
        thinking_tokens = timings.get("reasoning_n")
    if thinking_tokens is None:
        if "</think>" in tokens:
            idx = tokens.index("</think>")
            thinking_tokens = idx + 1
        elif reasoning:
            thinking_tokens = len(reasoning.split())
        else:
            thinking_tokens = 0
    thinking_tokens = int(thinking_tokens or 0)
    return prompt_tokens, thinking_tokens, output_tokens


def strip_for_aider(resp: dict) -> dict:
    """Return a deep copy of `resp` with `logprobs` and `reasoning_content` removed (F5)."""
    cleaned = copy.deepcopy(resp)
    cleaned.pop("logprobs", None)
    cleaned.pop("reasoning_content", None)
    for choice in cleaned.get("choices") or []:
        if isinstance(choice, dict):
            choice.pop("logprobs", None)
            choice.pop("reasoning_content", None)
            msg = choice.get("message")
            if isinstance(msg, dict):
                msg.pop("reasoning_content", None)
                msg.pop("logprobs", None)
    return cleaned


def transform_request_body(body: dict, config: CandidateConfig) -> dict:
    """Apply F1, F3, F5 to an incoming OpenAI chat completion request body."""
    out = copy.deepcopy(body)
    # F1: Always force stream: false upstream so --reasoning-format deepseek separates thinking.
    out["stream"] = False
    # F3: Strip any Aider-supplied sampling parameters and override with card values.
    for key in SAMPLING_KEYS:
        out.pop(key, None)
    for key, val in config.sampling.items():
        out[key] = copy.deepcopy(val)
    # F3: Inject candidate's chat_template_kwargs.
    out["chat_template_kwargs"] = copy.deepcopy(config.chat_template_kwargs)
    # F5: Request top-5 log-probabilities upstream.
    out["logprobs"] = True
    out["top_logprobs"] = TOP_LOGPROBS_K
    return out


class ProxyState:
    """Per-task state tracked by the logging proxy."""

    def __init__(
        self,
        *,
        upstream_url: str,
        config: CandidateConfig | str | Path,
        generations_path: str | Path,
        max_calls: int = DEFAULT_MAX_CALLS,
        wall_limit_s: float = DEFAULT_WALL_LIMIT_S,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.upstream_url = upstream_url.rstrip("/")
        self.config = config if isinstance(config, CandidateConfig) else load_candidate_config(config)
        self.generations_path = Path(generations_path)
        self.generations_path.parent.mkdir(parents=True, exist_ok=True)
        # Ensure generations.jsonl exists even if 0 calls occur
        if not self.generations_path.exists():
            self.generations_path.write_text("", encoding="utf-8")
        self.max_calls = int(max_calls)
        self.wall_limit_s = float(wall_limit_s)
        self.clock = clock
        self.start_time = self.clock()
        self._lock = threading.Lock()

        self.call_count = 0
        self.call_cap_hits = 0
        self.wall_cap_hits = 0
        self.truncated_calls = 0
        self.thinking_tokens_total = 0
        self.output_tokens_total = 0
        self.prompt_tokens_total = 0
        self.records: list[dict] = []

    def _append_record(self, row: dict) -> None:
        line = json.dumps(row, ensure_ascii=False) + "\n"
        with open(self.generations_path, "a", encoding="utf-8", newline="\n") as f:
            f.write(line)
        self.records.append(row)

    def remaining_wall_s(self) -> float:
        return self.wall_limit_s - (self.clock() - self.start_time)

    def generations_sha256(self) -> str:
        raw = self.generations_path.read_bytes().replace(b"\r\n", b"\n")
        return hashlib.sha256(raw).hexdigest()

    def summary(self) -> dict:
        with self._lock:
            return {
                "arm": self.config.arm,
                "injected": self.config.injected_dict,
                "config_sha256": self.config.config_sha256,
                "call_count": self.call_count,
                "max_calls": self.max_calls,
                "call_cap_hits": self.call_cap_hits,
                "wall_cap_hits": self.wall_cap_hits,
                "cap_hits": {
                    "call_cap": self.call_cap_hits > 0,
                    "call_cap_refusals": self.call_cap_hits,
                    "wall_cap": self.wall_cap_hits > 0,
                    "wall_cap_refusals": self.wall_cap_hits,
                },
                "thinking_tokens": self.thinking_tokens_total,
                "output_tokens": self.output_tokens_total,
                "prompt_tokens": self.prompt_tokens_total,
                "truncated_calls": self.truncated_calls,
                "truncated": self.truncated_calls > 0,
                "generations_sha256": self.generations_sha256(),
            }

    def handle_completion(self, path: str, body: dict) -> tuple[int, dict]:
        """Process one chat/completion request and return (http_status, response_dict)."""
        with self._lock:
            elapsed_before = self.clock() - self.start_time
            if elapsed_before >= self.wall_limit_s:
                self.wall_cap_hits += 1
                refusal = {
                    "kind": "refused",
                    "reason": "wall_cap",
                    "status": 429,
                    "arm": self.config.arm,
                    "prompt": self.call_count,
                    "call_index": self.call_count + 1,
                    "elapsed_s": round(elapsed_before, 4),
                    "wall_limit_s": self.wall_limit_s,
                    "injected": self.config.injected_dict,
                }
                self._append_record(refusal)
                return 429, {
                    "error": {
                        "message": f"Task wall time limit ({self.wall_limit_s}s) exceeded",
                        "type": "wall_cap_exceeded",
                        "code": 429,
                    }
                }

            if self.call_count >= self.max_calls:
                self.call_cap_hits += 1
                refusal = {
                    "kind": "refused",
                    "reason": "call_cap",
                    "status": 429,
                    "arm": self.config.arm,
                    "prompt": self.call_count,
                    "call_index": self.call_count + 1,
                    "max_calls": self.max_calls,
                    "elapsed_s": round(elapsed_before, 4),
                    "injected": self.config.injected_dict,
                }
                self._append_record(refusal)
                return 429, {
                    "error": {
                        "message": f"Task model call cap ({self.max_calls}) exceeded on call {self.call_count + 1}",
                        "type": "call_cap_exceeded",
                        "code": 429,
                    }
                }

            prompt_idx = self.call_count
            self.call_count += 1
            call_number = self.call_count
            timeout_s = max(0.05, self.wall_limit_s - elapsed_before)

        upstream_body = transform_request_body(body, self.config)
        target_url = f"{self.upstream_url}/{path.lstrip('/')}"
        req_bytes = json.dumps(upstream_body).encode("utf-8")
        req = urllib.request.Request(
            target_url,
            data=req_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        call_t0 = self.clock()
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                status = resp.status
                raw_reply = resp.read().decode("utf-8")
        except (TimeoutError, urllib.error.URLError) as exc:
            call_wall_s = self.clock() - call_t0
            with self._lock:
                if isinstance(exc, TimeoutError) or (self.clock() - self.start_time) >= self.wall_limit_s:
                    self.wall_cap_hits += 1
                    refusal = {
                        "kind": "refused",
                        "reason": "wall_cap",
                        "status": 429,
                        "arm": self.config.arm,
                        "prompt": prompt_idx,
                        "call_index": call_number,
                        "wall_time_s": round(call_wall_s, 6),
                        "wall_limit_s": self.wall_limit_s,
                        "injected": self.config.injected_dict,
                    }
                    self._append_record(refusal)
                    return 429, {
                        "error": {
                            "message": f"Task wall time limit ({self.wall_limit_s}s) exceeded during call",
                            "type": "wall_cap_exceeded",
                            "code": 429,
                        }
                    }
                err_row = {
                    "kind": "error",
                    "reason": str(exc),
                    "status": 502,
                    "arm": self.config.arm,
                    "prompt": prompt_idx,
                    "call_index": call_number,
                    "wall_time_s": round(call_wall_s, 6),
                    "injected": self.config.injected_dict,
                }
                self._append_record(err_row)
                return 502, {"error": {"message": f"Upstream error: {exc}", "type": "upstream_error", "code": 502}}

        call_wall_s = self.clock() - call_t0
        with self._lock:
            if (self.clock() - self.start_time) > self.wall_limit_s:
                self.wall_cap_hits += 1
                refusal = {
                    "kind": "refused",
                    "reason": "wall_cap",
                    "status": 429,
                    "arm": self.config.arm,
                    "prompt": prompt_idx,
                    "call_index": call_number,
                    "wall_time_s": round(call_wall_s, 6),
                    "wall_limit_s": self.wall_limit_s,
                    "injected": self.config.injected_dict,
                }
                self._append_record(refusal)
                return 429, {
                    "error": {
                        "message": f"Task wall time limit ({self.wall_limit_s}s) exceeded",
                        "type": "wall_cap_exceeded",
                        "code": 429,
                    }
                }

            upstream_json = json.loads(raw_reply)
            tokens, top = extract_abmine_logprobs(upstream_json)
            content, reasoning_content = _extract_reasoning_and_content(upstream_json)
            prompt_tokens, thinking_tokens, output_tokens = _count_tokens(
                upstream_json, tokens, reasoning_content
            )
            choices = upstream_json.get("choices") or []
            finish_reason = (
                choices[0].get("finish_reason")
                if choices and isinstance(choices[0], dict)
                else upstream_json.get("done_reason")
            )
            truncated = finish_reason == "length"
            if truncated:
                self.truncated_calls += 1
            self.prompt_tokens_total += prompt_tokens
            self.thinking_tokens_total += thinking_tokens
            self.output_tokens_total += output_tokens

            timings = upstream_json.get("timings") if isinstance(upstream_json.get("timings"), dict) else {}
            pred_ms = timings.get("predicted_ms")
            prompt_ms = timings.get("prompt_ms")
            eval_duration_ns = int(pred_ms * 1_000_000) if pred_ms is not None else upstream_json.get("eval_duration_ns")
            prompt_eval_duration_ns = (
                int(prompt_ms * 1_000_000) if prompt_ms is not None else upstream_json.get("prompt_eval_duration_ns")
            )

            raw_logprobs = (
                choices[0].get("logprobs")
                if choices and isinstance(choices[0], dict) and "logprobs" in choices[0]
                else upstream_json.get("logprobs")
            )

            record = {
                "kind": "result",
                "arm": self.config.arm,
                "prompt": prompt_idx,
                "call_index": call_number,
                "response": content,
                "reasoning_content": reasoning_content,
                "tokens": tokens,
                "top": top,
                "logprobs": raw_logprobs,
                "prompt_eval_count": prompt_tokens,
                "eval_count": output_tokens,
                "eval_duration_ns": eval_duration_ns,
                "prompt_eval_duration_ns": prompt_eval_duration_ns,
                "timings": timings,
                "usage": upstream_json.get("usage"),
                "wall_time_s": round(call_wall_s, 6),
                "thinking_tokens": thinking_tokens,
                "output_tokens": output_tokens,
                "prompt_tokens": prompt_tokens,
                "finish_reason": finish_reason,
                "done_reason": finish_reason,
                "truncated": truncated,
                "injected": self.config.injected_dict,
                "upstream_response": upstream_json,
            }
            self._append_record(record)
            aider_reply = strip_for_aider(upstream_json)
            return status, aider_reply


class _ProxyHandler(http.server.BaseHTTPRequestHandler):
    state: ProxyState

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return  # Keep stderr clean during test and harness runs

    def _send_json(self, status: int, payload: dict) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") in ("/health", "/v1/health"):
            self._send_json(200, {"status": "ok", "call_count": self.state.call_count})
            return
        if self.path.rstrip("/") in ("/v1/models", "/models"):
            self._send_json(
                200,
                {"object": "list", "data": [{"id": self.state.config.arm, "object": "model"}]},
            )
            return
        self._send_json(404, {"error": {"message": f"Unsupported GET path: {self.path}"}})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            body = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._send_json(400, {"error": {"message": f"Invalid JSON request: {exc}"}})
            return
        status, reply = self.state.handle_completion(self.path, body)
        self._send_json(status, reply)


class LoggingProxyServer:
    """Loopback HTTP server running `_ProxyHandler` in a background thread."""

    def __init__(
        self,
        state: ProxyState,
        host: str = "127.0.0.1",
        port: int = 0,
    ) -> None:
        self.state = state
        handler_cls = type("BoundProxyHandler", (_ProxyHandler,), {"state": state})
        self.httpd = http.server.ThreadingHTTPServer((host, port), handler_cls)
        self.host, self.port = self.httpd.server_address[0], self.httpd.server_address[1]
        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def openai_base_url(self) -> str:
        return f"http://{self.host}:{self.port}/v1"

    def start(self) -> LoggingProxyServer:
        self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self._thread.start()
        return self

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

    def __enter__(self) -> LoggingProxyServer:
        return self.start()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
