"""Fit and logprobs preflight for J2 candidates (F5, F6, F13, amendment B item 4).

Responsibilities:
- F13: Computes J2's `num_ctx` from a full validation task run to its 30-call cap:
  largest `(prompt_tokens + output_tokens) * 1.5`, rounded up to a power of two, floor `32768`.
- F5: Asserts five `top_logprobs` at every step from index 1 on.
- F6 & Amendment B item 4: Records the GGUF size, the KV cache size/types, and the measured
  peak VRAM at J2's context. Reports fit and never exits on it. Flags any `Q8_0` candidate
  that exceeds the A100-40GB budget for the labelled `[Q6_K: A100 fit]` arm (and labels Bolt's
  arm `[maker-QAT-IQ2 / 74B-A9B]`).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

from .proxy import TOP_LOGPROBS_K, extract_abmine_logprobs

J2_CONTEXT_FLOOR = 32768
VALIDATION_CALL_CAP = 30
A100_VRAM_CAP_MIB = 40960
RIG_PLAN_CAP_MIB = 26 * 1024  # 26 GB = 26624 MiB
Q6_K_ARM_LABEL = "[Q6_K: A100 fit]"
BOLT_ARM_LABEL = "[maker-QAT-IQ2 / 74B-A9B]"

_KV_SELF_RE = re.compile(r"KV self size\s*=\s*([\d.]+)\s*MiB", re.IGNORECASE)
_KV_PAIR_RE = re.compile(
    r"K\s*\((\w+)\):\s*([\d.]+)\s*MiB,\s*V\s*\((\w+)\):\s*([\d.]+)\s*MiB",
    re.IGNORECASE,
)


class PreflightError(Exception):
    """Raised when a preflight invariant (such as top-5 logprobs or 30-call validation) fails."""


def next_power_of_two(n: int) -> int:
    """Return the smallest power of two greater than or equal to `n`."""
    if n <= 1:
        return 1
    return 1 << (int(n) - 1).bit_length()


def compute_j2_context(
    validation_calls: list[dict],
    *,
    floor: int = J2_CONTEXT_FLOOR,
    require_full_cap: bool = True,
    expected_calls: int = VALIDATION_CALL_CAP,
) -> int:
    """Compute J2's context length from a validation run to its 30-call cap (F13).

    Takes the largest `(prompt_tokens + output_tokens)` across calls, multiplies by 1.5,
    rounds up to a power of two, and enforces a floor of `32768`.
    """
    result_calls = [
        c for c in validation_calls if isinstance(c, dict) and c.get("kind", "result") == "result"
    ]
    if require_full_cap and len(result_calls) < expected_calls:
        raise PreflightError(
            f"F13 requires a validation task run to its {expected_calls}-call cap; got {len(result_calls)} calls"
        )
    if not result_calls:
        raise PreflightError("validation_calls must contain at least one result call")

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
        raise PreflightError("largest prompt + output token count in validation run must be > 0")

    scaled = math.ceil(max_tokens * 1.5)
    return max(int(floor), next_power_of_two(scaled))


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
    context_length: int,
    top_or_response: list | dict,
    gguf_path: str | Path | None = None,
    gguf_size_bytes: int | None = None,
    gguf_size_mib: float | None = None,
    kv_cache_mib: float | None = None,
    server_log: str | None = None,
    peak_vram_mib: float | None = None,
    oom: bool = False,
    a100_cap_mib: float = A100_VRAM_CAP_MIB,
    rig_plan_cap_mib: float = RIG_PLAN_CAP_MIB,
) -> dict:
    """Run the F5/F6/F13 preflight for one candidate and return the fit report without exiting on fit."""
    if context_length < J2_CONTEXT_FLOOR or (context_length & (context_length - 1)) != 0:
        raise PreflightError(
            f"J2 context_length must be a power of two >= {J2_CONTEXT_FLOOR}; got {context_length}"
        )

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

    return {
        "arm": arm,
        "quant": norm_quant,
        "context_length": int(context_length),
        "gguf_size_bytes": int(gguf_size_bytes),
        "gguf_size_mib": float(gguf_size_mib),
        "kv_cache_mib": float(kv_info["total_mib"]),
        "kv_cache": kv_info,
        "peak_vram_mib": float(peak_vram_mib) if peak_vram_mib is not None else None,
        "oom": bool(oom),
        "top_logprobs_k": TOP_LOGPROBS_K,
        "top_logprobs_verified_steps": verified_steps,
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
    """CLI entry point that writes/prints the fit preflight report and never exits non-zero on fit."""
    parser = argparse.ArgumentParser(description="Run J2 fit and top-5 logprobs preflight.")
    parser.add_argument("--input", required=True, help="JSON file holding preflight measurement inputs")
    parser.add_argument("--output", help="Optional path to write the preflight report JSON")
    args = parser.parse_args(argv)

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    ctx = data.get("context_length")
    if ctx is None and "validation_calls" in data:
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
    )
    text = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)
    # Amendment B item 4: Fit is a report, never an exit.
    return 0


if __name__ == "__main__":
    sys.exit(main())
