"""Loopback logging proxy between Aider and llama-server (F1, F3, F4, F5, D1, D2, E1-E3).

Responsibilities:
- F1: Always sends `stream: false` upstream so `--reasoning-format deepseek` separates thinking.
- F3 & D1: Overrides Aider's sampling (`temperature`, `top_p`, `top_k`, `min_p`, `repeat_penalty`,
  `presence_penalty`, etc.) with the candidate's pinned card values, sending every key in the
  candidate's `sampling` block on every call (including disabled values `top_k: 0`, `min_p: 0.0`,
  `repeat_penalty: 1.0`, `presence_penalty: 0.0`), and injects `chat_template_kwargs`, loaded by
  `candidate` id from `card-values.json`. Never hard-codes model values. Records the exact injected
  dict and applied transforms on every `generations.jsonl` line.
- D2 & E1-E3: Applies per-candidate message `transforms` (`fold_system`, `reattach_thinking`) before
  forwarding upstream; refuses unknown transform names at start.
- F4: Counts model calls per task and refuses the 31st (HTTP 429, recorded in `generations.jsonl`),
  and enforces the 15-minute task wall (900 s). On a late wall cap after a completed upstream call,
  logs the `"result"` row first and then the `"refused"` row so no generated token is lost.
- F5: Adds `logprobs: true, top_logprobs: 5` upstream. Writes the full response (`logprobs` and
  `reasoning_content` included) to `generations.jsonl` in `mcptoolshop_rnd.abmine`'s format, plus
  `llama-server`'s `timings` and wall time. Strips `logprobs` and `reasoning_content` from the reply
  returned to Aider, which gets a plain OpenAI completion.
- Records thinking tokens (or `thinking_words_estimate` when no token count is reported), output
  tokens, and truncation (`finish_reason == "length"`) per call.

Standard library only (`http.server` + `urllib`).
"""
from __future__ import annotations

import copy
import hashlib
import http.server
import json
import os
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

DEFAULT_MAX_CALLS = 30
DEFAULT_WALL_LIMIT_S = 15 * 60.0  # 15 minutes
TOP_LOGPROBS_K = 5
PROXY_FILE_MODE = 0o600

PINNED_AIDER_VERSION = "0.86.1"

# Fixed assistant acknowledgement strings emitted by Aider at PINNED_AIDER_VERSION
# (in `aider/coders/base_prompts.py`, `aider/coders/editblock_prompts.py`, `aider/coders/base_coder.py`,
# and `aider/history.py`: after repo map, read-only files, editable files, and history summaries
# when `examples_as_sys_msg: true` is pinned).
AIDER_SYNTHETIC_ASSISTANT_STRINGS: tuple[str, ...] = (
    "Ok.",
    "Ok",
    "Ok, any changes I propose will be to those files.",
    "Ok, based on your requests I will suggest which files need to be edited and then stop and wait for your approval.",
    "Ok, I won't try and edit those files without asking first.",
    "Ok, I will use these files as references.",
    "Ok, I will use these images as references.",
    "I see that you interrupted my previous reply.",
    "I understand.",
)

KNOWN_TRANSFORMS: tuple[str, ...] = (
    "fold_system",
    "reattach_thinking",
)

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
    """Raised when a per-candidate config file or transform name is missing or malformed."""


def sha256_text(text: str) -> str:
    """Return the hex sha256 digest of a UTF-8 string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_aider_synthetic_strings(
    prompts_obj: Any,
    *,
    aider_version: str = PINNED_AIDER_VERSION,
) -> bool:
    """Verify that an Aider prompts/coder object (or tuple of prompt classes) at `PINNED_AIDER_VERSION` uses only named synthetic replies."""
    if str(aider_version).strip() != PINNED_AIDER_VERSION:
        raise ProxyConfigError(
            f"Aider version {aider_version!r} does not match PINNED_AIDER_VERSION {PINNED_AIDER_VERSION!r}"
        )
    if isinstance(prompts_obj, (list, tuple)):
        if not prompts_obj:
            raise ProxyConfigError("prompts_obj sequence must not be empty")
        for item in prompts_obj:
            verify_aider_synthetic_strings(item, aider_version=aider_version)
        return True

    base_attrs = (
        "files_content_assistant_reply",
        "files_no_full_files_with_repo_map_reply",
        "repo_content_assistant_reply",
    )
    dynamic_attrs = tuple(
        name
        for name in dir(prompts_obj)
        if not name.startswith("_") and (name.endswith("_assistant_reply") or name.endswith("_map_reply"))
    )
    attrs = tuple(dict.fromkeys((*base_attrs, *dynamic_attrs)))
    found_any = False
    for attr in attrs:
        val = getattr(prompts_obj, attr, None)
        if val is not None:
            found_any = True
            if str(val) not in AIDER_SYNTHETIC_ASSISTANT_STRINGS:
                raise ProxyConfigError(
                    f"Aider prompt attribute {attr}={val!r} is not in AIDER_SYNTHETIC_ASSISTANT_STRINGS"
                )
    if not found_any:
        raise ProxyConfigError("prompts_obj defines none of the expected Aider assistant reply attributes")
    return True


@dataclass(frozen=True)
class CandidateConfig:
    """Per-candidate sampling, template kwargs, and transforms loaded from JSON (F3, D1, D2)."""

    candidate: str
    sampling: dict
    chat_template_kwargs: dict
    config_sha256: str
    transforms: tuple[str, ...] = ()
    reattach_max_turns: int | None = None
    template_sha256: str | None = None
    extra: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        for t_name in self.transforms:
            if t_name not in KNOWN_TRANSFORMS:
                raise ProxyConfigError(
                    f"unknown transform {t_name!r} for candidate {self.candidate!r}; "
                    f"allowed: {KNOWN_TRANSFORMS}"
                )
        if self.reattach_max_turns is not None:
            if not isinstance(self.reattach_max_turns, int) or isinstance(self.reattach_max_turns, bool) or self.reattach_max_turns <= 0:
                raise ProxyConfigError(
                    f"reattach_max_turns must be None or a positive integer; got {self.reattach_max_turns!r}"
                )

    @property
    def arm(self) -> str:
        return self.candidate

    @property
    def injected_dict(self) -> dict:
        """The exact injected dictionary recorded on every generations.jsonl line and receipt."""
        return {
            "sampling": copy.deepcopy(self.sampling),
            "chat_template_kwargs": copy.deepcopy(self.chat_template_kwargs),
            "transforms": list(self.transforms),
            "reattach_max_turns": self.reattach_max_turns,
        }


def load_candidate_config(
    path: str | Path,
    candidate: str | None = None,
) -> CandidateConfig:
    """Load per-candidate configuration from `card-values.json` (or a single-candidate JSON file).

    When `path` contains a `"candidates"` list (as in `experiments/local-builders/card-values.json`),
    selects the entry matching `candidate` (unless the list has a single entry and `candidate` is omitted).
    Never supplies model-specific defaults: the entry must explicitly define `sampling` and
    `chat_template_kwargs`. Refuses unknown transform names at start.
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

    entry: dict
    if "candidates" in data:
        cand_list = data.get("candidates")
        if not isinstance(cand_list, list) or not cand_list:
            raise ProxyConfigError(f"candidate config {p} has an empty or invalid 'candidates' list")
        if candidate is None:
            if len(cand_list) == 1 and isinstance(cand_list[0], dict):
                entry = cand_list[0]
            else:
                raise ProxyConfigError(
                    f"candidate id is required when loading from multi-candidate file {p}"
                )
        else:
            target = str(candidate).strip()
            matched = [
                item
                for item in cand_list
                if isinstance(item, dict)
                and (item.get("candidate") == target or item.get("arm") == target)
            ]
            if not matched:
                available = [item.get("candidate") for item in cand_list if isinstance(item, dict)]
                raise ProxyConfigError(
                    f"candidate {target!r} not found in {p}; available: {available}"
                )
            entry = matched[0]
    else:
        entry = data
        if candidate is not None:
            entry_id = entry.get("candidate") or entry.get("arm") or entry.get("model")
            if entry_id and str(entry_id) != str(candidate).strip():
                raise ProxyConfigError(
                    f"requested candidate {candidate!r} does not match single-entry config {entry_id!r}"
                )

    sampling = entry.get("sampling")
    if not isinstance(sampling, dict) or not sampling:
        raise ProxyConfigError(f"candidate config in {p} must contain a non-empty 'sampling' object")
    for k, v in sampling.items():
        if v is None:
            raise ProxyConfigError(f"sampling key {k!r} in {p} must not be null (D1)")

    kwargs = entry.get("chat_template_kwargs")
    if not isinstance(kwargs, dict):
        raise ProxyConfigError(f"candidate config in {p} must contain a 'chat_template_kwargs' object")

    raw_transforms = entry.get("transforms", [])
    if not isinstance(raw_transforms, list) or not all(isinstance(t, str) for t in raw_transforms):
        raise ProxyConfigError(f"candidate config in {p} 'transforms' must be a list of strings")

    reattach_max_turns = entry.get("reattach_max_turns")
    cand_id = str(entry.get("candidate") or entry.get("arm") or entry.get("model") or candidate or p.stem)
    template_sha256 = entry.get("template_sha256")
    extra = {
        k: v
        for k, v in entry.items()
        if k
        not in (
            "candidate",
            "arm",
            "sampling",
            "chat_template_kwargs",
            "transforms",
            "reattach_max_turns",
            "template_sha256",
        )
    }
    return CandidateConfig(
        candidate=cand_id,
        sampling=copy.deepcopy(sampling),
        chat_template_kwargs=copy.deepcopy(kwargs),
        config_sha256=config_sha,
        transforms=tuple(raw_transforms),
        reattach_max_turns=reattach_max_turns,
        template_sha256=str(template_sha256) if template_sha256 else None,
        extra=extra,
    )


def apply_fold_system(messages: list[dict]) -> list[dict]:
    """Fold `system` messages into `user` messages for R1-Distill (D2, D-F2, E2).

    - Folds every leading `system` message into the head of the first `user` message,
      separated by a blank line (`"\\n\\n"`).
    - Folds every later `system` message (e.g. Aider's format reminder) into the tail of the
      `user` message before it, or the last one, separated by a blank line (`"\\n\\n"`).
    - Asserts that no `system` message remains in the returned list.
    """
    copied = [copy.deepcopy(m) for m in messages if isinstance(m, dict)]
    first_user_idx: int | None = None
    for idx, msg in enumerate(copied):
        if msg.get("role") == "user":
            first_user_idx = idx
            break

    leading_system_parts: list[str] = []
    out: list[dict] = []
    seen_first_user = False

    for idx, msg in enumerate(copied):
        role = msg.get("role")
        content = str(msg.get("content") or "")
        if role == "system":
            if not seen_first_user and (first_user_idx is None or idx < first_user_idx):
                if content:
                    leading_system_parts.append(content)
            else:
                # Fold into the tail of the preceding user message in `out`
                target_user: dict | None = None
                for prev in reversed(out):
                    if prev.get("role") == "user":
                        target_user = prev
                        break
                if target_user is not None:
                    prev_text = str(target_user.get("content") or "")
                    if prev_text and content:
                        target_user["content"] = f"{prev_text}\n\n{content}"
                    elif content:
                        target_user["content"] = content
                elif content:
                    leading_system_parts.append(content)
            continue

        if role == "user" and not seen_first_user:
            seen_first_user = True
            if leading_system_parts:
                prefix = "\n\n".join(leading_system_parts)
                msg["content"] = f"{prefix}\n\n{content}" if content else prefix
                leading_system_parts = []
        out.append(msg)

    # Edge case: if there were system messages but no user message at all in `messages`
    if leading_system_parts:
        out.insert(0, {"role": "user", "content": "\n\n".join(leading_system_parts)})

    if any(m.get("role") == "system" for m in out):  # pragma: no cover (defensive invariant guard)
        raise ProxyConfigError("fold_system invariant violated: a system message remained after folding")
    return out


def apply_reattach_thinking(
    messages: list[dict],
    logged_replies: list[tuple[str, str, str]],
    *,
    reattach_max_turns: int | None = None,
    synthetic_strings: tuple[str, ...] = AIDER_SYNTHETIC_ASSISTANT_STRINGS,
) -> tuple[list[dict], dict[str, Any]]:
    """Re-attach logged `reasoning_content` onto earlier assistant turns (D2, D-F1, D-F3, E1, E3).

    - `logged_replies` holds `(raw_sha256, stripped_sha256, reasoning_content)` in turn order,
      equivalent to `sha256(content) -> list[reasoning_content]` consumed first in, first out.
    - When the raw `sha256(content)` misses, tries `sha256(content.strip())`.
    - An unmatched assistant turn whose content equals one of Aider's fixed acknowledgement
      strings in `synthetic_strings` is counted as `synthetic`; any other unmatched assistant
      turn is sent without reasoning and counted as `mismatch`.
    - When `reattach_max_turns` is set to `N`, only the last `N` non-synthetic assistant turns
      have their matched `reasoning_content` attached; when `None`, every matched assistant turn
      gets its reasoning back.
    """
    copied = [copy.deepcopy(m) for m in messages if isinstance(m, dict)]
    used_indices: set[int] = set()

    # Track classification per message index in `copied`
    matched_reasoning: dict[int, str] = {}
    non_synthetic_assistant_indices: list[int] = []
    synthetic_count = 0
    mismatch_count = 0

    for msg_idx, msg in enumerate(copied):
        if msg.get("role") != "assistant":
            continue
        content = str(msg.get("content") or "")
        raw_h = sha256_text(content)
        strip_h = sha256_text(content.strip())

        found_entry_idx: int | None = None
        # 1. Exact sha256(content) match in FIFO order
        for entry_idx, (r_sha, _s_sha, _rc) in enumerate(logged_replies):
            if entry_idx not in used_indices and r_sha == raw_h:
                found_entry_idx = entry_idx
                break
        # 2. Fallback to sha256(content.strip()) in FIFO order
        if found_entry_idx is None:
            for entry_idx, (_r_sha, s_sha, _rc) in enumerate(logged_replies):
                if entry_idx not in used_indices and s_sha == strip_h:
                    found_entry_idx = entry_idx
                    break

        if found_entry_idx is not None:
            used_indices.add(found_entry_idx)
            matched_reasoning[msg_idx] = logged_replies[found_entry_idx][2]
            non_synthetic_assistant_indices.append(msg_idx)
        elif content in synthetic_strings:
            msg.pop("reasoning_content", None)
            synthetic_count += 1
        else:
            msg.pop("reasoning_content", None)
            mismatch_count += 1
            non_synthetic_assistant_indices.append(msg_idx)

    if reattach_max_turns is not None:
        eligible_indices = set(non_synthetic_assistant_indices[-int(reattach_max_turns) :])
    else:
        eligible_indices = set(non_synthetic_assistant_indices)

    reattached_count = 0
    for msg_idx, reasoning in matched_reasoning.items():
        if msg_idx in eligible_indices:
            copied[msg_idx]["reasoning_content"] = reasoning
            reattached_count += 1
        else:
            copied[msg_idx].pop("reasoning_content", None)

    stats = {
        "reattached": reattached_count,
        "synthetic": synthetic_count,
        "mismatch": mismatch_count,
        "reattach_max_turns": reattach_max_turns,
    }
    return copied, stats


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


# Tokens that close a reply's thinking. `</think>` for the DeepSeek-style templates; `<|eom|>` and `<|end|>` close the
# analysis message in harmony-style templates (Muse-Glimmer's ends its thinking with `<|eom|>`, window 12d), and count
# only when the reply carries reasoning.
THINK_END = "</think>"
CHANNEL_ENDS = ("<|eom|>", "<|end|>", "<channel|>")  # <channel|>: Gemma 4 closes `<|channel>thought ...` (window 12f)


def _thinking_count(resp: dict, tokens: list[str], reasoning: str | None, output_tokens: int) -> tuple[int | None, str | None]:
    """The reply's thinking tokens and where the count came from: `usage`, `timings`, `marker` (the token that closes the
    thinking, in the logprob stream), or `length` (a reply cut off at the limit with no answer yet, so all of it was
    thinking). `(None, None)` when none of these can say: the caller keeps a word estimate instead.

    Before 2026-10-17 two cases came back None and were summed as 0 downstream: every reply that stopped at the length
    limit (its thinking never closed), and every reply from a harmony-style template (no `</think>`). Those are exactly
    the longest thinkers."""

    usage = resp.get("usage") if isinstance(resp.get("usage"), dict) else {}
    timings = resp.get("timings") if isinstance(resp.get("timings"), dict) else {}
    details = usage.get("completion_tokens_details")
    if isinstance(details, dict) and details.get("reasoning_tokens") is not None:
        return int(details["reasoning_tokens"]), "usage"
    if usage.get("reasoning_tokens") is not None:
        return int(usage["reasoning_tokens"]), "usage"
    if timings.get("reasoning_n") is not None:
        return int(timings["reasoning_n"]), "timings"
    if THINK_END in tokens:
        return tokens.index(THINK_END) + 1, "marker"
    if not reasoning:
        return 0, "none"
    # A channel end counts only with tokens after it: some templates close every assistant turn with <|end|>, and as the
    # last token it would make the whole reply thinking (R&D on #150).
    ends = [tokens.index(m) for m in CHANNEL_ENDS if m in tokens[:-1]]
    if ends:
        return min(ends) + 1, "marker"
    content, _ = _extract_reasoning_and_content(resp)
    choices = resp.get("choices") or []
    finish = choices[0].get("finish_reason") if choices and isinstance(choices[0], dict) else resp.get("done_reason")
    if finish == "length" and not content.strip():
        return output_tokens, "length"
    return None, None


def _count_tokens(
    resp: dict,
    tokens: list[str],
    reasoning: str | None,
) -> tuple[int, int | None, int | None, int]:
    """Return `(prompt_tokens, thinking_tokens, thinking_words_estimate, output_tokens)` for one call.

    When `reasoning` is non-empty and no token count is reported in `usage`, `timings`, or `tokens`,
    `thinking_tokens` is `None` and the word count is labelled `thinking_words_estimate` so the
    receipt never claims a word count as a token count.
    """
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

    thinking_tokens, _ = _thinking_count(resp, tokens, reasoning, output_tokens)
    thinking_words_estimate = len(reasoning.split()) if thinking_tokens is None and reasoning else None
    return prompt_tokens, thinking_tokens, thinking_words_estimate, output_tokens


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


def transform_request_body(
    body: dict,
    config: CandidateConfig,
    *,
    logged_replies: list[tuple[str, str, str]] | None = None,
    transform_stats_out: dict[str, Any] | None = None,
) -> dict:
    """Apply F1, F3, F5, D1, and D2 (`transforms`) to an incoming OpenAI chat completion request body."""
    out = copy.deepcopy(body)
    # F1: Always force stream: false upstream so --reasoning-format deepseek separates thinking.
    out["stream"] = False
    # F3 & D1: Strip any Aider-supplied sampling parameters and send every key in config.sampling.
    for key in SAMPLING_KEYS:
        out.pop(key, None)
    for key, val in config.sampling.items():
        out[key] = copy.deepcopy(val)
    # F3: Inject candidate's chat_template_kwargs.
    out["chat_template_kwargs"] = copy.deepcopy(config.chat_template_kwargs)
    # F5: Request top-5 log-probabilities upstream.
    out["logprobs"] = True
    out["top_logprobs"] = TOP_LOGPROBS_K

    reattach_stats = {
        "reattached": 0,
        "synthetic": 0,
        "mismatch": 0,
        "reattach_max_turns": config.reattach_max_turns,
    }
    if isinstance(out.get("messages"), list):
        msgs = out["messages"]
        for t_name in config.transforms:
            if t_name == "fold_system":
                msgs = apply_fold_system(msgs)
            elif t_name == "reattach_thinking":
                msgs, reattach_stats = apply_reattach_thinking(
                    msgs,
                    logged_replies or [],
                    reattach_max_turns=config.reattach_max_turns,
                )
            else:  # pragma: no cover (caught at CandidateConfig construction)
                raise ProxyConfigError(f"unknown transform: {t_name!r}")
        out["messages"] = msgs

    if transform_stats_out is not None:
        transform_stats_out.update(reattach_stats)
    return out


class ProxyState:
    """Per-task state tracked by the logging proxy."""

    def __init__(
        self,
        *,
        upstream_url: str,
        config: CandidateConfig | str | Path,
        generations_path: str | Path,
        candidate: str | None = None,
        max_calls: int = DEFAULT_MAX_CALLS,
        wall_limit_s: float = DEFAULT_WALL_LIMIT_S,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.upstream_url = upstream_url.rstrip("/")
        self.config = (
            config
            if isinstance(config, CandidateConfig)
            else load_candidate_config(config, candidate=candidate)
        )
        self.generations_path = Path(generations_path)
        self.generations_path.parent.mkdir(parents=True, exist_ok=True)
        # Ensure generations.jsonl exists even if 0 calls occur, with mode 0600
        if not self.generations_path.exists():
            self.generations_path.write_text("", encoding="utf-8")
        os.chmod(self.generations_path, PROXY_FILE_MODE)
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
        self.thinking_tokens_unknown_calls = 0
        self.thinking_words_estimate_total = 0
        self.output_tokens_total = 0
        self.prompt_tokens_total = 0
        self.records: list[dict] = []

        # D2 / E1: Per-reply (raw_sha256, stripped_sha256, reasoning_content) in turn order,
        # and sha256(content) -> list[reasoning_content] map.
        self._logged_replies: list[tuple[str, str, str]] = []
        self.reasoning_by_hash: dict[str, list[str]] = {}
        self.reattach_reattached_total = 0
        self.reattach_synthetic_total = 0
        self.reattach_mismatch_total = 0

    def _append_record(self, row: dict) -> None:
        line = json.dumps(row, ensure_ascii=False) + "\n"
        with open(self.generations_path, "a", encoding="utf-8", newline="\n") as f:
            f.write(line)
        os.chmod(self.generations_path, PROXY_FILE_MODE)
        self.records.append(row)

    def remaining_wall_s(self) -> float:
        return self.wall_limit_s - (self.clock() - self.start_time)

    def generations_sha256(self) -> str:
        raw = self.generations_path.read_bytes().replace(b"\r\n", b"\n")
        return hashlib.sha256(raw).hexdigest()

    def summary(self) -> dict:
        with self._lock:
            thinking_tokens_val: int | None = (
                None if self.thinking_tokens_unknown_calls > 0 else self.thinking_tokens_total
            )
            thinking_words_val: int | None = (
                self.thinking_words_estimate_total if self.thinking_tokens_unknown_calls > 0 else None
            )
            return {
                "arm": self.config.arm,
                "candidate": self.config.candidate,
                "injected": self.config.injected_dict,
                "transforms": list(self.config.transforms),
                "reattach_max_turns": self.config.reattach_max_turns,
                "reattach_thinking": {
                    "reattached": self.reattach_reattached_total,
                    "synthetic": self.reattach_synthetic_total,
                    "mismatch": self.reattach_mismatch_total,
                    "reattach_max_turns": self.config.reattach_max_turns,
                },
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
                "thinking_tokens": thinking_tokens_val,
                "thinking_words_estimate": thinking_words_val,
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
                    "transforms": list(self.config.transforms),
                    "reattach_max_turns": self.config.reattach_max_turns,
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
                    "transforms": list(self.config.transforms),
                    "reattach_max_turns": self.config.reattach_max_turns,
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
            replies_snapshot = list(self._logged_replies)

        transform_stats: dict[str, Any] = {}
        upstream_body = transform_request_body(
            body,
            self.config,
            logged_replies=replies_snapshot,
            transform_stats_out=transform_stats,
        )
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
                        "transforms": list(self.config.transforms),
                        "reattach_max_turns": self.config.reattach_max_turns,
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
                    "transforms": list(self.config.transforms),
                    "reattach_max_turns": self.config.reattach_max_turns,
                    "injected": self.config.injected_dict,
                }
                self._append_record(err_row)
                return 502, {"error": {"message": f"Upstream error: {exc}", "type": "upstream_error", "code": 502}}

        call_wall_s = self.clock() - call_t0
        with self._lock:
            self.reattach_reattached_total += int(transform_stats.get("reattached", 0))
            self.reattach_synthetic_total += int(transform_stats.get("synthetic", 0))
            self.reattach_mismatch_total += int(transform_stats.get("mismatch", 0))

            upstream_json = json.loads(raw_reply)
            tokens, top = extract_abmine_logprobs(upstream_json)
            content, reasoning_content = _extract_reasoning_and_content(upstream_json)
            if reasoning_content is not None:
                raw_h = sha256_text(content)
                strip_h = sha256_text(content.strip())
                self._logged_replies.append((raw_h, strip_h, reasoning_content))
                self.reasoning_by_hash.setdefault(raw_h, []).append(reasoning_content)

            prompt_tokens, thinking_tokens, thinking_words_estimate, output_tokens = _count_tokens(
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
            if thinking_tokens is not None:
                self.thinking_tokens_total += thinking_tokens
            else:
                self.thinking_tokens_unknown_calls += 1
                self.thinking_words_estimate_total += int(thinking_words_estimate or 0)
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

            # Always log the completed result row FIRST so the dataminer never loses generated tokens (item 7).
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
                "thinking_tokens_source": _thinking_count(upstream_json, tokens, reasoning_content, output_tokens)[1],
                "thinking_words_estimate": thinking_words_estimate,
                "output_tokens": output_tokens,
                "prompt_tokens": prompt_tokens,
                "finish_reason": finish_reason,
                "done_reason": finish_reason,
                "truncated": truncated,
                "transforms": list(self.config.transforms),
                "reattach_max_turns": self.config.reattach_max_turns,
                "reattach_thinking": dict(transform_stats),
                "injected": self.config.injected_dict,
                "upstream_response": upstream_json,
            }
            self._append_record(record)

            # If the call finished past the task wall limit, record the refusal row after the result row and return 429.
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
                    "transforms": list(self.config.transforms),
                    "reattach_max_turns": self.config.reattach_max_turns,
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
