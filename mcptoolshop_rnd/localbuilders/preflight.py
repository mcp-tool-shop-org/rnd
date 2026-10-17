"""Fit, logprobs, template, and thinking-split preflight for J2 candidates (F5, F6, F13, D1, D-F1, D-F3, E1, E3).

Responsibilities:
- F13 & D-F3 / E3: Computes J2's `num_ctx` from the measured maximum across multiple validation
  task runs to their 30-call cap (including Qwen3.8 with `reattach_thinking` active):
  largest `(prompt_tokens + output_tokens) * 1.5`, rounded up to a power of two, floor `32768`,
  and records which runs it used.
- F5: Asserts five `top_logprobs` at every step from index 1 on.
- D1 & D-F1:
  - Template check: reads the chat template embedded in the candidate's GGUF (`tokenizer.chat_template`)
    and reports whether its sha256 equals `template_sha256` (never exits on mismatch).
  - Thinking split check: for each candidate with thinking on, checks that a thinking reply gives a
    non-empty `reasoning_content` and leaves no `<think>` or `<|channel>thought` tag in `content`
    (never exits on failure).
- F6 & Amendment B item 4: Records the GGUF size, the KV cache size/types, and the measured
  peak VRAM at J2's context. Reports fit and never exits on it. Flags any `Q8_0` candidate
  that exceeds the A100-40GB budget for the labelled `[Q6_K: A100 fit]` arm (and labels Bolt's
  arm `[maker-QAT-IQ2 / 74B-A9B]`).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import sys
from pathlib import Path
from typing import Any, BinaryIO

from .proxy import (
    PINNED_AIDER_VERSION,
    TOP_LOGPROBS_K,
    ProxyConfigError,
    _extract_reasoning_and_content,
    extract_abmine_logprobs,
    verify_aider_synthetic_strings,
)

J2_CONTEXT_FLOOR = 32768
VALIDATION_CALL_CAP = 30
A100_VRAM_CAP_MIB = 40960
RIG_PLAN_CAP_MIB = 26 * 1024  # 26 GB = 26624 MiB
Q6_K_ARM_LABEL = "[Q6_K: A100 fit]"
BOLT_ARM_LABEL = "[maker-QAT-IQ2 / 74B-A9B]"

FORBIDDEN_THINKING_TAGS: tuple[str, ...] = (
    "<think>",
    "</think>",
    "<|channel>thought",
    "<|channel|>thought",
)

_KV_SELF_RE = re.compile(r"KV self size\s*=\s*([\d.]+)\s*MiB", re.IGNORECASE)
_KV_PAIR_RE = re.compile(
    r"K\s*\((\w+)\):\s*([\d.]+)\s*MiB,\s*V\s*\((\w+)\):\s*([\d.]+)\s*MiB",
    re.IGNORECASE,
)

# GGUF metadata value type sizes in bytes for fixed-width scalar types
_GGUF_SCALAR_SIZES: dict[int, int] = {
    0: 1,   # UINT8
    1: 1,   # INT8
    2: 2,   # UINT16
    3: 2,   # INT16
    4: 4,   # UINT32
    5: 4,   # INT32
    6: 4,   # FLOAT32
    7: 1,   # BOOL
    10: 8,  # UINT64
    11: 8,  # INT64
    12: 8,  # FLOAT64
}
_GGUF_TYPE_STRING = 8
_GGUF_TYPE_ARRAY = 9


class PreflightError(Exception):
    """Raised when a preflight invariant (such as Aider version/synthetic strings, top-5 logprobs, or 30-call validation) fails."""


def get_installed_aider_version() -> str:
    """Import the installed `aider` package and return `aider.__version__`."""
    try:
        import aider  # type: ignore[import-not-found]
    except ImportError as exc:
        raise PreflightError(f"installed Aider package is required: {exc}") from exc
    return str(getattr(aider, "__version__", "")).strip()


def check_aider_version_gate(aider_version: str | None = None) -> str:
    """Refuse unless the installed Aider version is `PINNED_AIDER_VERSION` (`0.86.1`)."""
    ver = str(aider_version).strip() if aider_version is not None else get_installed_aider_version()
    if ver != PINNED_AIDER_VERSION:
        raise PreflightError(
            f"installed Aider version {ver!r} does not match pinned {PINNED_AIDER_VERSION!r}"
        )
    return ver


def load_installed_aider_prompts() -> tuple[Any, Any]:
    """Import and return `(CoderPrompts, EditBlockPrompts)` from the installed Aider."""
    try:
        from aider.coders.base_prompts import CoderPrompts  # type: ignore[import-not-found]
        from aider.coders.editblock_prompts import EditBlockPrompts  # type: ignore[import-not-found]
    except ImportError as exc:
        raise PreflightError(
            f"failed to import CoderPrompts and EditBlockPrompts from installed Aider: {exc}"
        ) from exc
    return CoderPrompts, EditBlockPrompts


def verify_installed_aider(
    *,
    aider_version: str | None = None,
    coder_prompts_cls: Any = None,
    editblock_prompts_cls: Any = None,
) -> dict[str, Any]:
    """Import the installed Aider, refuse unless its version is `0.86.1`, and verify `CoderPrompts` and `EditBlockPrompts`.

    A version mismatch or an unrecognised synthetic assistant reply string refuses the run
    (`PreflightError`). Returns `{"aider_version": "0.86.1", "synthetic_strings_verified": True}`.
    """
    ver = check_aider_version_gate(aider_version)
    if coder_prompts_cls is None or editblock_prompts_cls is None:
        real_coder_prompts, real_editblock_prompts = load_installed_aider_prompts()
        coder_prompts_cls = coder_prompts_cls or real_coder_prompts
        editblock_prompts_cls = editblock_prompts_cls or real_editblock_prompts

    try:
        verify_aider_synthetic_strings(
            (coder_prompts_cls, editblock_prompts_cls),
            aider_version=ver,
        )
        if isinstance(coder_prompts_cls, type):
            verify_aider_synthetic_strings(coder_prompts_cls(), aider_version=ver)
        if isinstance(editblock_prompts_cls, type):
            verify_aider_synthetic_strings(editblock_prompts_cls(), aider_version=ver)
    except ProxyConfigError as exc:
        raise PreflightError(str(exc)) from exc

    return {
        "aider_version": ver,
        "synthetic_strings_verified": True,
    }


class ContextSizingResult(dict):
    """Multi-run context sizing result dict that also supports `int(res)` and integer equality."""

    def __int__(self) -> int:
        return int(self["context_length"])

    def __eq__(self, other: object) -> bool:
        if isinstance(other, int) and not isinstance(other, bool):
            return int(self["context_length"]) == other
        return super().__eq__(other)


def next_power_of_two(n: int) -> int:
    """Return the smallest power of two greater than or equal to `n`."""
    if n <= 1:
        return 1
    return 1 << (int(n) - 1).bit_length()


def _max_tokens_for_single_run(
    run_id: str,
    validation_calls: list[dict],
    *,
    require_full_cap: bool,
    expected_calls: int,
) -> int:
    result_calls = [
        c for c in validation_calls if isinstance(c, dict) and c.get("kind", "result") == "result"
    ]
    if require_full_cap and len(result_calls) < expected_calls:
        raise PreflightError(
            f"F13 requires validation run {run_id!r} to reach its {expected_calls}-call cap; "
            f"got {len(result_calls)} calls"
        )
    if not result_calls:
        raise PreflightError(f"validation run {run_id!r} must contain at least one result call")

    max_tokens = 0
    for call in result_calls:
        prompt_t = call.get("prompt_tokens")
        if prompt_t is None:
            prompt_t = call.get("prompt_eval_count", 0)
        output_t = call.get("output_tokens")
        if output_t is None:
            output_t = call.get("eval_count", 0)
        total = int(prompt_t or 0) + int(output_t or 0)
        if total > max_tokens:
            max_tokens = total

    if max_tokens <= 0:
        raise PreflightError(
            f"largest prompt + output token count in validation run {run_id!r} must be > 0"
        )
    return max_tokens


def compute_j2_context_length(
    validation_runs: dict[str, list[dict]] | list[dict],
    *,
    floor: int = J2_CONTEXT_FLOOR,
    require_full_cap: bool = True,
    expected_calls: int = VALIDATION_CALL_CAP,
    require_multiple_runs: bool = True,
) -> ContextSizingResult:
    """Compute J2's context length from the maximum over multiple validation runs (F13, D-F3, E3).

    Accepts either:
    - a mapping `{run_id: [call_dict, ...], ...}`, or
    - a list of run dicts `[{"run_id": "...", "calls": [...]}, ...]`.
    Records `runs_used`, `per_run_max_tokens`, `winning_run`, `max_tokens`, and `context_length`.
    """
    runs_map: dict[str, list[dict]] = {}
    if isinstance(validation_runs, dict):
        for k, v in validation_runs.items():
            if not isinstance(v, list):
                raise PreflightError(f"validation run {k!r} must map to a list of call dicts")
            runs_map[str(k)] = v
    elif isinstance(validation_runs, list):
        if validation_runs and isinstance(validation_runs[0], dict) and (
            "calls" in validation_runs[0] or "validation_calls" in validation_runs[0]
        ):
            for idx, item in enumerate(validation_runs):
                if not isinstance(item, dict):
                    raise PreflightError(f"validation run entry {idx} must be a dict")
                rid = str(item.get("run_id") or item.get("candidate") or item.get("arm") or f"run_{idx}")
                calls = item.get("calls") if "calls" in item else item.get("validation_calls")
                if not isinstance(calls, list):
                    raise PreflightError(f"validation run {rid!r} missing 'calls' list")
                runs_map[rid] = calls
        else:
            runs_map["run_0"] = validation_runs
    else:
        raise PreflightError("validation_runs must be a dict of runs or a list of run dicts")

    if not runs_map:
        raise PreflightError("validation_runs must not be empty")
    if require_multiple_runs and len(runs_map) < 2:
        raise PreflightError(
            f"D-F3 / E3 requires at least 2 validation runs to size J2 context; got {len(runs_map)}"
        )

    per_run_max: dict[str, int] = {}
    overall_max = 0
    winning_run = ""
    for run_id, calls in runs_map.items():
        rmax = _max_tokens_for_single_run(
            run_id,
            calls,
            require_full_cap=require_full_cap,
            expected_calls=expected_calls,
        )
        per_run_max[run_id] = rmax
        if rmax > overall_max:
            overall_max = rmax
            winning_run = run_id

    scaled = math.ceil(overall_max * 1.5)
    ctx_len = max(int(floor), next_power_of_two(scaled))
    return ContextSizingResult(
        {
            "context_length": ctx_len,
            "max_tokens": overall_max,
            "runs_used": list(runs_map.keys()),
            "winning_run": winning_run,
            "per_run_max_tokens": per_run_max,
        }
    )


def compute_j2_context(
    validation_calls: list[dict] | dict[str, list[dict]],
    *,
    floor: int = J2_CONTEXT_FLOOR,
    require_full_cap: bool = True,
    expected_calls: int = VALIDATION_CALL_CAP,
) -> int:
    """Compute J2's integer context length from one or more validation runs (F13)."""
    res = compute_j2_context_length(
        validation_calls,
        floor=floor,
        require_full_cap=require_full_cap,
        expected_calls=expected_calls,
        require_multiple_runs=False,
    )
    return int(res["context_length"])


def build_minimal_gguf_with_template(
    template_text: str | None,
    *,
    extra_int_key: tuple[str, int] | None = None,
) -> bytes:
    """Build a valid minimal GGUF v3 binary header containing `tokenizer.chat_template` for testing."""
    kv_entries: list[bytes] = []
    if extra_int_key is not None:
        k_bytes = extra_int_key[0].encode("utf-8")
        kv_entries.append(struct.pack("<Q", len(k_bytes)) + k_bytes + struct.pack("<II", 4, int(extra_int_key[1])))
    if template_text is not None:
        key_b = b"tokenizer.chat_template"
        val_b = template_text.encode("utf-8")
        kv_entries.append(
            struct.pack("<Q", len(key_b))
            + key_b
            + struct.pack("<I", _GGUF_TYPE_STRING)
            + struct.pack("<Q", len(val_b))
            + val_b
        )
    header = b"GGUF" + struct.pack("<IQQ", 3, 0, len(kv_entries))
    return header + b"".join(kv_entries)


def _read_exact(stream: BinaryIO, n: int) -> bytes:
    data = stream.read(n)
    if len(data) != n:
        raise ValueError(f"unexpected EOF in GGUF header (wanted {n} bytes, got {len(data)})")
    return data


def _read_gguf_string(stream: BinaryIO, count_fmt: str) -> str:
    (length,) = struct.unpack(count_fmt, _read_exact(stream, struct.calcsize(count_fmt)))
    raw = _read_exact(stream, int(length))
    return raw.decode("utf-8", errors="replace")


def _skip_gguf_value(stream: BinaryIO, vtype: int, count_fmt: str) -> None:
    if vtype in _GGUF_SCALAR_SIZES:
        _read_exact(stream, _GGUF_SCALAR_SIZES[vtype])
        return
    if vtype == _GGUF_TYPE_STRING:
        (length,) = struct.unpack(count_fmt, _read_exact(stream, struct.calcsize(count_fmt)))
        _read_exact(stream, int(length))
        return
    if vtype == _GGUF_TYPE_ARRAY:
        (elem_type,) = struct.unpack("<I", _read_exact(stream, 4))
        (count,) = struct.unpack(count_fmt, _read_exact(stream, struct.calcsize(count_fmt)))
        if elem_type in _GGUF_SCALAR_SIZES:
            _read_exact(stream, _GGUF_SCALAR_SIZES[elem_type] * int(count))
        else:
            for _ in range(int(count)):
                _skip_gguf_value(stream, elem_type, count_fmt)
        return
    raise ValueError(f"unsupported GGUF metadata value type: {vtype}")


def read_gguf_chat_template(gguf_path: str | Path) -> str | None:
    """Read `tokenizer.chat_template` from a GGUF file's metadata header without loading tensor weights."""
    p = Path(gguf_path)
    if not p.is_file():
        return None
    with open(p, "rb") as f:
        magic = f.read(4)
        if magic != b"GGUF":
            return None
        (version,) = struct.unpack("<I", _read_exact(f, 4))
        count_fmt = "<I" if version == 1 else "<Q"
        _tensor_count = struct.unpack(count_fmt, _read_exact(f, struct.calcsize(count_fmt)))[0]
        kv_count = struct.unpack(count_fmt, _read_exact(f, struct.calcsize(count_fmt)))[0]
        for _ in range(int(kv_count)):
            key = _read_gguf_string(f, count_fmt)
            (vtype,) = struct.unpack("<I", _read_exact(f, 4))
            if key == "tokenizer.chat_template" and vtype == _GGUF_TYPE_STRING:
                return _read_gguf_string(f, count_fmt)
            _skip_gguf_value(f, vtype, count_fmt)
    return None


def check_gguf_template(
    *,
    expected_template_sha256: str | None,
    gguf_path: str | Path | None = None,
    embedded_template: str | None = None,
) -> dict:
    """Compare the chat template embedded in the candidate's GGUF against `expected_template_sha256` (D1).

    Reports match or mismatch for R&D to read and never exits.
    """
    if embedded_template is None and gguf_path is not None:
        try:
            embedded_template = read_gguf_chat_template(gguf_path)
        except Exception as exc:  # noqa: BLE001
            return {
                "checked": True,
                "matches": False,
                "expected_sha256": expected_template_sha256,
                "embedded_sha256": None,
                "status": "error",
                "report": f"failed to read GGUF template: {exc}",
            }

    if embedded_template is None:
        return {
            "checked": bool(expected_template_sha256 is not None),
            "matches": False,
            "expected_sha256": expected_template_sha256,
            "embedded_sha256": None,
            "status": "missing_template",
            "report": "no tokenizer.chat_template found in GGUF",
        }

    norm_bytes = embedded_template.encode("utf-8").replace(b"\r\n", b"\n")
    raw_bytes = embedded_template.encode("utf-8")
    norm_sha = hashlib.sha256(norm_bytes).hexdigest()
    raw_sha = hashlib.sha256(raw_bytes).hexdigest()
    exp = str(expected_template_sha256).strip() if expected_template_sha256 else None
    matches = bool(exp and exp in (norm_sha, raw_sha))
    actual_sha = raw_sha if (exp and exp == raw_sha) else norm_sha

    return {
        "checked": True,
        "matches": matches,
        "expected_sha256": exp,
        "embedded_sha256": actual_sha,
        "status": "match" if matches else "mismatch",
        "report": (
            "GGUF embedded template matches template_sha256"
            if matches
            else f"GGUF template sha256 mismatch: embedded {actual_sha} != expected {exp}"
        ),
    }


def check_thinking_split(
    response: dict,
    *,
    thinking_enabled: bool = True,
) -> dict:
    """Check that a thinking reply gives non-empty `reasoning_content` and leaves no thinking tags in `content` (D-F1, E1).

    Checks both `<think>`/`</think>` and Gemma 4's `<|channel>thought`/`<|channel|>thought`.
    Reports pass or failure for R&D to read and never exits.
    """
    content, reasoning_content = _extract_reasoning_and_content(response)
    has_nonempty_reasoning = bool(reasoning_content and reasoning_content.strip())
    leaked_tags = [tag for tag in FORBIDDEN_THINKING_TAGS if tag in (content or "")]

    reasons: list[str] = []
    if thinking_enabled and not has_nonempty_reasoning:
        reasons.append("empty reasoning_content on thinking candidate")
    if leaked_tags:
        reasons.append(f"unsplit thinking tag(s) in content: {leaked_tags}")

    passed = len(reasons) == 0
    return {
        "thinking_enabled": bool(thinking_enabled),
        "passed": passed,
        "has_nonempty_reasoning": has_nonempty_reasoning,
        "leaked_tags": leaked_tags,
        "reasons": reasons,
        "report": "ok" if passed else "; ".join(reasons),
    }


def assert_top_logprobs(
    top_or_response: list | dict,
    *,
    k: int = TOP_LOGPROBS_K,
) -> int:
    """Assert `k` (5) `top_logprobs` candidates at every step from index 1 on (F5).

    Returns the number of steps verified (from index 1 to the end).
    """
    if isinstance(top_or_response, dict):
        if "top" in top_or_response and isinstance(top_or_response["top"], list):
            top = top_or_response["top"]
        else:
            _, top = extract_abmine_logprobs(top_or_response)
    elif isinstance(top_or_response, list):
        top = top_or_response
    else:
        raise PreflightError("top_or_response must be a list of step top_logprobs or a response dict")

    if len(top) < 2:
        raise PreflightError(
            f"preflight requires at least 2 generated token steps to check index 1 on; got {len(top)}"
        )

    verified = 0
    for step_idx, step in enumerate(top[1:], start=1):
        if not isinstance(step, list) or len(step) != k:
            got_len = len(step) if isinstance(step, list) else "non-list"
            raise PreflightError(
                f"step {step_idx} has {got_len} top_logprobs candidates; expected {k} (F5)"
            )
        for cand_idx, cand in enumerate(step):
            if isinstance(cand, (list, tuple)) and len(cand) >= 2:
                tok, lp = cand[0], cand[1]
            elif isinstance(cand, dict) and "token" in cand and "logprob" in cand:
                tok, lp = cand["token"], cand["logprob"]
            else:
                raise PreflightError(f"step {step_idx} candidate {cand_idx} is malformed: {cand!r}")
            if not isinstance(tok, str) or not isinstance(lp, (int, float)) or not math.isfinite(float(lp)):
                raise PreflightError(
                    f"step {step_idx} candidate {cand_idx} has invalid token/logprob: {(tok, lp)!r}"
                )
        verified += 1
    return verified


def parse_kv_cache_log(server_log: str) -> dict:
    """Extract KV cache size (MiB) and K/V data types from a `llama-server` log."""
    total_mib: float | None = None
    k_type: str | None = None
    v_type: str | None = None
    k_mib: float | None = None
    v_mib: float | None = None

    for line in server_log.splitlines():
        if m_self := _KV_SELF_RE.search(line):
            total_mib = float(m_self.group(1))
        if m_pair := _KV_PAIR_RE.search(line):
            k_type = m_pair.group(1)
            k_mib = float(m_pair.group(2))
            v_type = m_pair.group(3)
            v_mib = float(m_pair.group(4))
            if total_mib is None:
                total_mib = round(k_mib + v_mib, 2)

    return {
        "total_mib": total_mib,
        "k_type": k_type,
        "v_type": v_type,
        "k_mib": k_mib,
        "v_mib": v_mib,
    }


def evaluate_candidate_fit(
    *,
    arm: str,
    quant: str,
    context_length: int | ContextSizingResult,
    top_or_response: list | dict,
    gguf_path: str | Path | None = None,
    gguf_size_bytes: int | None = None,
    gguf_size_mib: float | None = None,
    kv_cache_mib: float | None = None,
    server_log: str | None = None,
    peak_vram_mib: float | None = None,
    oom: bool = False,
    expected_template_sha256: str | None = None,
    embedded_template: str | None = None,
    thinking_enabled: bool = True,
    reattach_max_turns: int | None = None,
    context_runs_used: list[str] | None = None,
    a100_cap_mib: float = A100_VRAM_CAP_MIB,
    rig_plan_cap_mib: float = RIG_PLAN_CAP_MIB,
) -> dict:
    """Run the F5/F6/F13/D1/D-F1 preflight for one candidate and return the report without exiting on fit, template, or thinking split."""
    if isinstance(context_length, dict):
        ctx_int = int(context_length["context_length"])
        runs_used = list(context_runs_used or context_length.get("runs_used") or [])
    else:
        ctx_int = int(context_length)
        runs_used = list(context_runs_used or [])

    if ctx_int < J2_CONTEXT_FLOOR or (ctx_int & (ctx_int - 1)) != 0:
        raise PreflightError(
            f"J2 context_length must be a power of two >= {J2_CONTEXT_FLOOR}; got {ctx_int}"
        )

    aider_check = verify_installed_aider()
    verified_steps = assert_top_logprobs(top_or_response, k=TOP_LOGPROBS_K)

    if gguf_size_bytes is None and gguf_path is not None:
        p = Path(gguf_path)
        if not p.is_file():
            raise PreflightError(f"GGUF file not found: {p}")
        gguf_size_bytes = p.stat().st_size

    if gguf_size_mib is None and gguf_size_bytes is not None:
        gguf_size_mib = round(gguf_size_bytes / (1024 * 1024), 2)
    elif gguf_size_bytes is None and gguf_size_mib is not None:
        gguf_size_bytes = int(round(gguf_size_mib * 1024 * 1024))

    if gguf_size_mib is None:
        raise PreflightError("either gguf_path, gguf_size_bytes, or gguf_size_mib must be provided")

    kv_info = parse_kv_cache_log(server_log or "")
    if kv_cache_mib is not None:
        kv_info["total_mib"] = float(kv_cache_mib)
    if kv_info["total_mib"] is None:
        raise PreflightError("kv_cache_mib must be provided or present in server_log")

    if peak_vram_mib is None and not oom:
        raise PreflightError("measured peak_vram_mib is required unless oom=True")

    fits_a100 = (not oom) and (peak_vram_mib is not None) and (float(peak_vram_mib) <= float(a100_cap_mib))
    fits_rig = (not oom) and (peak_vram_mib is not None) and (float(peak_vram_mib) <= float(rig_plan_cap_mib))

    norm_quant = quant.strip()
    flagged_for_q6_k = (norm_quant.upper() == "Q8_0") and (not fits_a100)

    if "bolt" in arm.lower() or "iq2" in norm_quant.lower() or "qat" in norm_quant.lower():
        arm_label = BOLT_ARM_LABEL
    elif flagged_for_q6_k or norm_quant.upper() == "Q6_K":
        arm_label = Q6_K_ARM_LABEL
    else:
        arm_label = f"[{norm_quant}]"

    template_check = check_gguf_template(
        expected_template_sha256=expected_template_sha256,
        gguf_path=gguf_path,
        embedded_template=embedded_template,
    )
    thinking_check = (
        check_thinking_split(top_or_response, thinking_enabled=thinking_enabled)
        if isinstance(top_or_response, dict)
        else {
            "thinking_enabled": bool(thinking_enabled),
            "passed": not thinking_enabled,
            "has_nonempty_reasoning": False,
            "leaked_tags": [],
            "reasons": ["response dict not provided"] if thinking_enabled else [],
            "report": "response dict not provided" if thinking_enabled else "ok",
        }
    )

    reattach_cap_report = (
        f"{arm} ran with a cap (reattach_max_turns={reattach_max_turns})"
        if reattach_max_turns is not None
        else None
    )

    return {
        "arm": arm,
        "quant": norm_quant,
        "aider_version": aider_check["aider_version"],
        "synthetic_strings_verified": bool(aider_check["synthetic_strings_verified"]),
        "context_length": ctx_int,
        "context_runs_used": runs_used,
        "reattach_max_turns": reattach_max_turns,
        "reattach_cap_report": reattach_cap_report,
        "gguf_size_bytes": int(gguf_size_bytes),
        "gguf_size_mib": float(gguf_size_mib),
        "kv_cache_mib": float(kv_info["total_mib"]),
        "kv_cache": kv_info,
        "peak_vram_mib": float(peak_vram_mib) if peak_vram_mib is not None else None,
        "oom": bool(oom),
        "top_logprobs_k": TOP_LOGPROBS_K,
        "top_logprobs_verified_steps": verified_steps,
        "template_check": template_check,
        "thinking_split_check": thinking_check,
        "fits_a100": fits_a100,
        "a100_cap_mib": float(a100_cap_mib),
        "fits_rig_plan_cap": fits_rig,
        "rig_plan_cap_mib": float(rig_plan_cap_mib),
        "rig_fit_report": "fits" if fits_rig else "doesn't fit the rig's plan cap",
        "flagged_for_q6_k": flagged_for_q6_k,
        "recommended_quant": "Q6_K" if flagged_for_q6_k else norm_quant,
        "arm_label": arm_label,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point that writes/prints the preflight report and never exits non-zero on fit, template, or thinking split."""
    parser = argparse.ArgumentParser(description="Run J2 fit, template, thinking-split, and top-5 logprobs preflight.")
    parser.add_argument("--input", required=True, help="JSON file holding preflight measurement inputs")
    parser.add_argument("--output", help="Optional path to write the preflight report JSON")
    args = parser.parse_args(argv)

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    ctx = data.get("context_length")
    runs_used: list[str] | None = data.get("context_runs_used")
    if ctx is None and "validation_runs" in data:
        sizing = compute_j2_context_length(data["validation_runs"])
        ctx = int(sizing["context_length"])
        runs_used = list(sizing["runs_used"])
    elif ctx is None and "validation_calls" in data:
        ctx = compute_j2_context(data["validation_calls"])

    report = evaluate_candidate_fit(
        arm=data["arm"],
        quant=data["quant"],
        context_length=int(ctx),
        top_or_response=data["probe_response"],
        gguf_path=data.get("gguf_path"),
        gguf_size_bytes=data.get("gguf_size_bytes"),
        gguf_size_mib=data.get("gguf_size_mib"),
        kv_cache_mib=data.get("kv_cache_mib"),
        server_log=data.get("server_log"),
        peak_vram_mib=data.get("peak_vram_mib"),
        oom=bool(data.get("oom", False)),
        expected_template_sha256=data.get("expected_template_sha256") or data.get("template_sha256"),
        embedded_template=data.get("embedded_template"),
        thinking_enabled=bool(data.get("thinking_enabled", True)),
        reattach_max_turns=data.get("reattach_max_turns"),
        context_runs_used=runs_used,
    )
    text = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)
    # Amendment B item 4 & D1/D-F1: Fit, template, and thinking-split checks report and never exit.
    return 0


if __name__ == "__main__":
    sys.exit(main())
