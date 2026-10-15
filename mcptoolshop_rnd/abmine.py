"""ab_dataminer: find where, and by how much, two arms of an A/B run of the same model differ.

The input is a record of greedy generations from several arms (builds, backends or settings) of one model on the
same prompts. Each generation keeps its tokens and, for every step, the top-K candidates with their
log-probabilities. `rnd abmine analyze` reads it with no GPU and no server and reports, for each pair of arms and
each prompt:

- where the two generations fork (the first differing token), or that they are identical;
- Δz at every step of the matched prefix, the fork included, where both arms saw the same context. With R the
  reference arm and T the test arm, and t1, t2 R's top two candidates at that step:

      Δz = (ℓR(t1) − ℓR(t2)) − (ℓT(t1) − ℓT(t2))

  Δz doesn't depend on how the vocabulary's probability is normalised, so it compares two arms' logits directly. A
  step is censored, and flagged, when t1 or t2 is missing from T's top-K, because then T's gap can't be read;
- the step-0 Δz (the first token after prefill), the mean, p95 and maximum |Δz| over the matched prefix, a drift
  slope per token (a least-squares fit of |Δz| on the step), and the largest pre-fork spikes;
- the fork in detail: both arms' candidates there, the tokens each chose, and Δz at the fork;
- the chosen-token MAE: the mean |ℓR(tok) − ℓT(tok)| over the matched prefix, for the token both arms chose;
- with a reference arm, a tie-break at each fork between two other arms: which way the reference went, where it
  saw the same context.

`analyze` also parses `OLLAMA_DEBUG` server logs for what each arm actually ran: the backend DLLs loaded, the
device, the FlashAttention setting and how it resolved, the KV cache types, and CUDA graph reuse.

`probe` is for a GPU grant, not for analysis. It replays a generation as prefill: the model's chat template is
rendered exactly, in raw mode, ending inside the assistant turn, then the generated tokens up to a position, and
one token is asked for with its top-K. The replay must first reproduce the recorded prompt token count and step-0
candidates on the same backend. If it doesn't, nothing after it is trusted. Comparing replay against decode on one
arm separates the prefill path's numerics from the decode path's.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from statistics import median
from typing import Callable

SPIKE_FLOOR = 0.1  # |Δz| below this is never called a spike
SPIKE_FACTOR = 5.0  # a spike is at least this many times the prefix's median |Δz|


class AbmineError(Exception):
    pass


# ---------------------------------------------------------------- records


@dataclass
class Gen:
    """One arm's greedy generation for one prompt."""

    tokens: list[str]
    top: list[list[tuple[str, float]]]  # per step, the top-K candidates, best first
    prompt_eval_count: int | None = None
    eval_count: int | None = None
    eval_duration_ns: int | None = None
    response: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def tok_per_s(self) -> float | None:
        if self.eval_count and self.eval_duration_ns:
            return self.eval_count / (self.eval_duration_ns / 1e9)
        return None


def _arm_of(row: dict) -> str:
    return str(row.get("arm") or row.get("block") or "")


def load_records(lines) -> dict[str, dict[int, Gen]]:
    """Generations by arm and prompt, from JSON lines whose kind is "result". The arm is `arm`, or `block` as the
    v3 sandbox harness wrote it."""
    out: dict[str, dict[int, Gen]] = {}
    for n, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            raise AbmineError(f"line {n} is not JSON: {e}") from e
        if row.get("kind") != "result":
            continue
        arm = _arm_of(row)
        if not arm or "prompt" not in row:
            raise AbmineError(f"line {n}: a result row needs an arm (or block) and a prompt")
        top = [[(str(t), float(lp)) for t, lp in step] for step in (row.get("top") or [])]
        out.setdefault(arm, {})[int(row["prompt"])] = Gen(
            tokens=[str(t) for t in (row.get("tokens") or [])], top=top,
            prompt_eval_count=row.get("prompt_eval_count"), eval_count=row.get("eval_count"),
            eval_duration_ns=row.get("eval_duration_ns"), response=row.get("response", ""))
    return out


def load_record_file(path: str | Path) -> dict[str, dict[int, Gen]]:
    with open(path, encoding="utf-8") as f:
        return load_records(f)


# ---------------------------------------------------------------- Δz


def logprob(step: list[tuple[str, float]], token: str) -> float | None:
    for t, lp in step:
        if t == token:
            return lp
    return None


def delta_z(ref_step: list[tuple[str, float]], test_step: list[tuple[str, float]]) -> tuple[float | None, str]:
    """Δz at one step, and a reason when it can't be read ("" when it can)."""
    if len(ref_step) < 2:
        return None, "reference has fewer than two candidates"
    (t1, l1), (t2, l2) = ref_step[0], ref_step[1]
    m1, m2 = logprob(test_step, t1), logprob(test_step, t2)
    if m1 is None or m2 is None:
        return None, "censored: a reference candidate is outside the test arm's top-K"
    return (l1 - l2) - (m1 - m2), ""


def fork_index(a: list[str], b: list[str]) -> int | None:
    """The first step where two token lists differ; the shorter length if one is a prefix of the other; None if
    they are identical."""
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return None if len(a) == len(b) else min(len(a), len(b))


def slope(points: list[tuple[int, float]]) -> float | None:
    """The least-squares slope of y on x, or None with fewer than two distinct x."""
    if len(points) < 2:
        return None
    n = len(points)
    mx = sum(x for x, _ in points) / n
    my = sum(y for _, y in points) / n
    sxx = sum((x - mx) ** 2 for x, _ in points)
    if sxx == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in points) / sxx


def p95(values: list[float]) -> float | None:
    """The 95th percentile by linear interpolation between order statistics."""
    if not values:
        return None
    s = sorted(values)
    k = 0.95 * (len(s) - 1)
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def compare(ref: Gen, test: Gen) -> dict:
    """Everything `analyze` reports for one pair of generations of one prompt."""
    fork = fork_index(ref.tokens, test.tokens)
    end = fork if fork is not None else min(len(ref.tokens), len(test.tokens))
    # The fork step itself still has an identical context in both arms, so Δz is read through it.
    upto = fork if fork is not None else end - 1
    last = min(upto, len(ref.top) - 1, len(test.top) - 1)
    steps, censored = [], []
    for i in range(0, last + 1):
        dz, why = delta_z(ref.top[i], test.top[i])
        if dz is None:
            censored.append({"step": i, "reason": why})
        else:
            steps.append((i, dz))
    prefix = [(i, abs(dz)) for i, dz in steps if fork is None or i < fork]
    absvals = [v for _, v in prefix]
    med = median(absvals) if absvals else 0.0
    spikes = sorted(((i, v) for i, v in prefix if v >= max(SPIKE_FLOOR, SPIKE_FACTOR * med)), key=lambda p: -p[1])[:3]
    chosen = []
    for i in range(0, min(end, len(ref.top), len(test.top))):
        a, b = logprob(ref.top[i], ref.tokens[i]), logprob(test.top[i], ref.tokens[i])
        if a is not None and b is not None:
            chosen.append(abs(a - b))
    out = {
        "identical": fork is None,
        "fork": fork,
        "steps_read": len(steps),
        "censored": censored,
        "step0_dz": next((dz for i, dz in steps if i == 0), None),
        "prefix_abs_dz": {"mean": sum(absvals) / len(absvals) if absvals else None, "p95": p95(absvals),
                          "max": max(absvals) if absvals else None, "n": len(absvals)},
        "drift_slope_per_token": slope(prefix),
        "spikes": [{"step": i, "abs_dz": v} for i, v in spikes],
        "chosen_token_mae": sum(chosen) / len(chosen) if chosen else None,
        "chosen_token_n": len(chosen),
    }
    if fork is not None:
        f = {"step": fork,
             "ref_token": ref.tokens[fork] if fork < len(ref.tokens) else None,
             "test_token": test.tokens[fork] if fork < len(test.tokens) else None,
             "ref_top": ref.top[fork][:3] if fork < len(ref.top) else None,
             "test_top": test.top[fork][:3] if fork < len(test.top) else None}
        f["dz"] = next((dz for i, dz in steps if i == fork), None)
        f["censored"] = any(c["step"] == fork for c in censored)
        out["fork_detail"] = f
    return out


def matrix(records: dict[str, dict[int, Gen]], arms: list[str] | None = None) -> dict:
    """Every ordered pair (first arm as reference) over the prompts both have."""
    arms = arms or sorted(records)
    out = {}
    for i, a in enumerate(arms):
        for b in arms[i + 1:]:
            prompts = sorted(set(records.get(a, {})) & set(records.get(b, {})))
            per = {p: compare(records[a][p], records[b][p]) for p in prompts}
            step0 = [abs(c["step0_dz"]) for c in per.values() if c["step0_dz"] is not None]
            maes = [c["chosen_token_mae"] for c in per.values() if c["chosen_token_mae"] is not None]
            out[f"{a} vs {b}"] = {
                "prompts": len(prompts),
                "identical": sum(1 for c in per.values() if c["identical"]),
                "forks": {p: c["fork"] for p, c in per.items() if not c["identical"]},
                "mean_abs_step0_dz": sum(step0) / len(step0) if step0 else None,
                "mean_chosen_token_mae": sum(maes) / len(maes) if maes else None,
                "per_prompt": per,
            }
    return out


def tie_break(records: dict[str, dict[int, Gen]], ref_arm: str, a: str, b: str) -> list[dict]:
    """At each fork between arms a and b, which way the reference arm went, when it saw the same context."""
    out = []
    for p in sorted(set(records.get(a, {})) & set(records.get(b, {}))):
        ga, gb = records[a][p], records[b][p]
        f = fork_index(ga.tokens, gb.tokens)
        if f is None:
            continue
        gr = records.get(ref_arm, {}).get(p)
        row = {"prompt": p, "fork": f}
        if gr is None:
            row["reference"] = "missing"
        elif gr.tokens[:f] != ga.tokens[:f]:
            row["reference"] = f"diverged earlier, at step {fork_index(gr.tokens, ga.tokens)}"
        elif f >= len(gr.tokens):
            row["reference"] = "ended before the fork"
        else:
            tok = gr.tokens[f]
            row["reference_token"] = tok
            row["reference"] = a if f < len(ga.tokens) and tok == ga.tokens[f] else (
                b if f < len(gb.tokens) and tok == gb.tokens[f] else "neither")
            row["reference_top"] = gr.top[f][:3] if f < len(gr.top) else None
        out.append(row)
    return out


# ---------------------------------------------------------------- OLLAMA_DEBUG logs

_LOG_PATTERNS = {
    "backends": re.compile(r"load_backend: loaded (\w+) backend from (.+)$"),
    "device": re.compile(r"Device \d+: (.+?), compute capability ([\d.]+), VMM: (\w+)"),
    "inference_compute": re.compile(r'msg="inference compute".*?library=(\S+) compute=(\S+).*?description="([^"]+)"'),
    "flash_attn_setting": re.compile(r"llama_context: flash_attn\s*=\s*(\S+)"),
    "flash_attn_resolved": re.compile(r"Flash Attention (enabled|disabled)"),
    "kv_types": re.compile(r"K \((\w+)\):\s*[\d.]+ MiB, V \((\w+)\)"),
    "graphs_reused": re.compile(r"graphs reused =\s*(\d+)"),
    "prompt_tokens": re.compile(r"new prompt, .*task\.n_tokens = (\d+)"),
    "n_ctx": re.compile(r"llama_context: n_ctx\s*=\s*(\d+)"),
}


def parse_log(text: str) -> dict:
    """What an OLLAMA_DEBUG server log says the arm actually ran. Fields the log doesn't show stay empty."""
    out: dict = {"backends": [], "device": None, "inference_compute": None, "flash_attn_setting": None,
                 "flash_attn_resolved": None, "kv_types": None, "graphs_reused": [], "prompt_tokens": [],
                 "n_ctx": None}
    for line in text.splitlines():
        if m := _LOG_PATTERNS["backends"].search(line):
            out["backends"].append({"kind": m.group(1), "path": m.group(2).strip()})
        elif m := _LOG_PATTERNS["device"].search(line):
            out["device"] = {"name": m.group(1), "compute": m.group(2), "vmm": m.group(3)}
        elif m := _LOG_PATTERNS["inference_compute"].search(line):
            out["inference_compute"] = {"library": m.group(1), "compute": m.group(2), "description": m.group(3)}
        elif m := _LOG_PATTERNS["flash_attn_setting"].search(line):
            out["flash_attn_setting"] = m.group(1)
            # A forced setting is its own resolution: with --flash-attn off (or on), llama.cpp logs
            # "flash_attn = disabled" (or "enabled") and skips resolve_fused_ops, which only resolves "auto".
            if m.group(1) in ("enabled", "disabled"):
                out["flash_attn_resolved"] = m.group(1)
        elif m := _LOG_PATTERNS["flash_attn_resolved"].search(line):
            out["flash_attn_resolved"] = m.group(1)
        elif m := _LOG_PATTERNS["kv_types"].search(line):
            out["kv_types"] = {"k": m.group(1), "v": m.group(2)}
        elif m := _LOG_PATTERNS["graphs_reused"].search(line):
            out["graphs_reused"].append(int(m.group(1)))
        elif m := _LOG_PATTERNS["prompt_tokens"].search(line):
            out["prompt_tokens"].append(int(m.group(1)))
        elif m := _LOG_PATTERNS["n_ctx"].search(line):
            out["n_ctx"] = int(m.group(1))
    return out


# ---------------------------------------------------------------- the report


def analyze(records: dict[str, dict[int, Gen]], logs: dict[str, str] | None = None, reference: str | None = None,
            arms: list[str] | None = None) -> dict:
    arms = arms or sorted(records)
    out = {"arms": arms, "prompts": {a: sorted(records[a]) for a in arms},
           "matrix": matrix(records, arms), "logs": {a: parse_log(t) for a, t in (logs or {}).items()}}
    if reference:
        others = [a for a in arms if a != reference]
        out["tie_break"] = {f"{a} vs {b}": tie_break(records, reference, a, b)
                            for i, a in enumerate(others) for b in others[i + 1:]}
        out["mae_vs_reference"] = {
            a: _mean([c["chosen_token_mae"] for c in matrix(records, [reference, a])[f"{reference} vs {a}"]
                      ["per_prompt"].values() if c["chosen_token_mae"] is not None]) for a in others}
    return out


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _f(v, nd=3) -> str:
    return "—" if v is None else f"{v:.{nd}f}"


def render(report: dict) -> str:
    """The report as text a person reads."""
    lines = [f"arms: {', '.join(report['arms'])}"]
    for pair, m in report["matrix"].items():
        lines.append(f"\n{pair}: {m['identical']} of {m['prompts']} prompts identical; mean |step-0 Δz| "
                     f"{_f(m['mean_abs_step0_dz'], 4)}; mean chosen-token MAE {_f(m['mean_chosen_token_mae'], 4)}")
        for p, c in m["per_prompt"].items():
            pa = c["prefix_abs_dz"]
            head = "identical" if c["identical"] else f"fork at step {c['fork']}"
            lines.append(f"  prompt {p}: {head}; step-0 Δz {_f(c['step0_dz'], 4)}; prefix |Δz| mean {_f(pa['mean'], 4)} "
                         f"p95 {_f(pa['p95'], 4)} max {_f(pa['max'], 4)} (n {pa['n']}); slope {_f(c['drift_slope_per_token'], 5)}/token; "
                         f"censored {len(c['censored'])}")
            for s in c["spikes"]:
                lines.append(f"    spike at step {s['step']}: |Δz| {s['abs_dz']:.3f}")
            if not c["identical"]:
                fd = c["fork_detail"]
                lines.append(f"    fork: reference chose {fd['ref_token']!r}, test chose {fd['test_token']!r}; "
                             f"Δz {_f(fd['dz'])}{' (censored)' if fd['censored'] else ''}")
                lines.append(f"      reference top: {fd['ref_top']}")
                lines.append(f"      test top:      {fd['test_top']}")
    for arm, lg in report.get("logs", {}).items():
        lines.append(f"\nlog {arm}: backends {[b['kind'] + ' ' + b['path'] for b in lg['backends']]}; device {lg['device']}; "
                     f"flash_attn {lg['flash_attn_setting']} -> {lg['flash_attn_resolved']}; KV {lg['kv_types']}; "
                     f"graphs reused {lg['graphs_reused']}; prompt tokens {lg['prompt_tokens']}")
    if "tie_break" in report:
        for pair, rows in report["tie_break"].items():
            for r in rows:
                lines.append(f"tie-break {pair}, prompt {r['prompt']} fork {r['fork']}: reference -> {r['reference']}")
        for arm, mae in report["mae_vs_reference"].items():
            lines.append(f"chosen-token MAE vs reference, {arm}: {_f(mae, 4)}")
    return "\n".join(lines)


# ---------------------------------------------------------------- probe (for a GPU grant)

QWEN3_TEMPLATE_SHA256 = "ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4"


def template_from_store(models_dir: str | Path, name: str, tag: str) -> str:
    """A model's chat template, read from Ollama's model store (no server)."""
    base = Path(models_dir)
    manifest = json.loads((base / "manifests" / "registry.ollama.ai" / "library" / name / tag).read_text(encoding="utf-8"))
    digests = [l["digest"] for l in manifest["layers"] if l["mediaType"].endswith(".template")]
    if not digests:
        raise AbmineError(f"{name}:{tag} has no template layer")
    raw = (base / "blobs" / digests[0].replace(":", "-")).read_bytes()
    return raw.decode("utf-8")


def render_qwen3(content: str, think: bool, template: str) -> str:
    """The prompt text qwen3's Ollama template renders for one user message, no system prompt and no tools, with
    think set: what the server feeds the model before the first generated token. The template must be the pinned
    one, because this rendering is written from it."""
    got = hashlib.sha256(template.encode("utf-8")).hexdigest()
    if got != QWEN3_TEMPLATE_SHA256:
        raise AbmineError(f"template sha256 {got} is not the pinned qwen3 template {QWEN3_TEMPLATE_SHA256}; "
                          "re-derive render_qwen3 from the new template before probing")
    flag = " /think" if think else " /no_think"
    tail = "" if think else "<think>\n\n</think>\n\n"
    return f"<|im_start|>user\n{content}{flag}<|im_end|>\n<|im_start|>assistant\n{tail}"


def replay_body(model: str, rendered: str, prefix: list[str], k: int, options: dict, keep_alive: str = "30s") -> dict:
    return {"model": model, "prompt": rendered + "".join(prefix), "raw": True, "stream": False,
            "options": {**options, "num_predict": 1}, "logprobs": True, "top_logprobs": k, "keep_alive": keep_alive}


def probe(post: Callable[[dict], dict], model: str, rendered: str, gen: Gen, positions: list[int], k: int,
          options: dict, tol: float = 1e-3) -> list[dict]:
    """Replay `gen` as prefill at each position and record the next token's top-K.

    `post` sends one /api/generate body and returns the reply. Position 0 is replayed first and must reproduce
    the recorded prompt token count and step-0 candidates (tokens in order, log-probabilities within `tol`), or
    nothing is trusted and the probe stops. Each later position must show a prompt token count one higher per
    replayed token; where it doesn't, the text re-tokenised differently, and the row says so."""
    rows = []
    for pos in [0] + [p for p in positions if p != 0]:
        if pos > len(gen.tokens):
            raise AbmineError(f"position {pos} is past the generation's {len(gen.tokens)} tokens")
        r = post(replay_body(model, rendered, gen.tokens[:pos], k, options))
        lps = r.get("logprobs") or []
        top = [(str(c.get("token")), float(c.get("logprob"))) for c in (lps[0].get("top_logprobs") or [])] if lps else []
        pec = r.get("prompt_eval_count")
        row = {"position": pos, "top": top, "prompt_eval_count": pec}
        if pos == 0:
            want = gen.top[0] if gen.top else []
            n = min(len(want), len(top))
            same_tokens = n > 0 and [t for t, _ in top[:n]] == [t for t, _ in want[:n]]
            same_lps = same_tokens and all(abs(a[1] - b[1]) <= tol for a, b in zip(top[:n], want[:n]))
            if pec != gen.prompt_eval_count or not same_lps:
                raise AbmineError(f"the replay does not reproduce step 0 (prompt tokens {pec} vs {gen.prompt_eval_count}; "
                                  f"top {top[:n]} vs {want[:n]}); nothing after it is trusted")
            row["reproduces_step0"] = True
        elif gen.prompt_eval_count is not None:
            row["retokenized"] = pec != gen.prompt_eval_count + pos
        rows.append(row)
    return rows


def replay_vs_decode(gen: Gen, replays: list[dict]) -> list[dict]:
    """On one arm: Δz between the decode step and its prefill replay at each position."""
    out = []
    for r in replays:
        p = r["position"]
        if p < len(gen.top) and not r.get("retokenized"):
            dz, why = delta_z(gen.top[p], r["top"])
            out.append({"position": p, "dz": dz, "reason": why})
    return out
