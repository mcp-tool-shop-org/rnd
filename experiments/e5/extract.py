"""Trim interlock's E5 receipts down to the numbers the library publishes.

E5 asks, for each local model on the RTX 5090, the largest context window that stays fully on the card. The
interlock receipts carry paths, adapter ids and server log details. rnd is public, so this keeps only the result,
the conditions it was measured under, and the search trace that produced it. Run through `rnd collect e5`.

Left out on purpose:
- decode_tok_s and latency.throughput: each confirm generates one token, so the receipts' 1,000,000 tok/s
  is not a rate;
- adapter ids, backend paths, log sources, grants and notes: machine details, not results.

The spec's thresholds are read from interlock at the receipt's own harness commit, so each record states the
rule it was measured under.
"""

import hashlib
import json
import re
import subprocess

REPO_NAME = "mcp-tool-shop-org/interlock"
SPEC_PATH = "experiments/e5/spec.yaml"
SPEC_KEYS = ("abort_mib", "grain", "spill_shared_mib", "spill_prompt_ratio", "shared_gate_from_mib")
TEXT = re.compile(r"^[A-Za-z0-9 _.:+-]{1,80}$")
SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
CALL_KINDS = ("load", "confirm")


def text(value, what):
    if not isinstance(value, str) or not TEXT.match(value):
        raise SystemExit(f"{what} is not plain text: {value!r}")
    return value


def number(value, what):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SystemExit(f"{what} is not a number: {value!r}")
    return value


def optional(value, what):
    return None if value is None else number(value, what)


def spec_rule(clone, commit):
    got = subprocess.run(["git", "-C", str(clone), "show", f"{commit}:{SPEC_PATH}"], capture_output=True)
    if got.returncode != 0:
        raise SystemExit(f"{SPEC_PATH} is not readable at {commit[:7]}")
    spec = got.stdout.decode("utf-8")
    rule = {}
    for key in SPEC_KEYS:
        found = re.search(rf"^{key}:\s*([0-9.]+)\s*$", spec, re.M)
        rule[key] = json.loads(found.group(1)) if found else None
    if rule["abort_mib"] is None or rule["grain"] is None:
        raise SystemExit(f"{SPEC_PATH} at {commit[:7]} has no abort_mib or grain")
    return rule


def call(row, where):
    if not isinstance(row, list) or len(row) != 6 or row[0] not in CALL_KINDS:
        raise SystemExit(f"{where} is not a [kind, ctx, peak, shared, prompt rate, verdict] row")
    kind, ctx, peak, shared, rate, verdict = row
    return [kind, number(ctx, where), number(peak, where), optional(shared, where),
            None if rate is None else round(number(rate, where), 1), text(verdict, where)]


def trim_model(row):
    s = row.get("settings") or {}
    m = row.get("model") or {}
    tag = text(m.get("repo_or_tag"), "model tag")
    digest = m.get("revision_or_digest")
    if not isinstance(digest, str) or not DIGEST.match(digest):
        raise SystemExit(f"{tag}: the digest is not a sha256")
    out = {
        "model": tag,
        "quant": text(m.get("quant"), f"{tag} quant"),
        "digest": digest,
        "result": {
            "max_resident_ctx": optional(s.get("max_resident_ctx"), f"{tag} max_resident_ctx"),
            "limit": text(s.get("limit"), f"{tag} limit"),
            "peak_mib": number(s.get("peak_mib"), f"{tag} peak"),
            "shared_mib": optional(s.get("shared_mib"), f"{tag} shared"),
            "prompt_tok_s": round(number(s.get("prompt_tok_s"), f"{tag} prompt rate"), 1),
        },
        "trained_cap": number(s.get("num_ctx"), f"{tag} num_ctx"),
        "floor": {
            "ctx": number(s.get("baseline_ctx"), f"{tag} floor"),
            "shared_mib": number(s.get("baseline_shared_mib"), f"{tag} floor shared"),
            "prompt_tok_s": round(number(s.get("baseline_prompt_tok_s"), f"{tag} floor rate"), 1),
            "cuda_host_sum_mib": number(s.get("cuda_host_sum_mib"), f"{tag} CUDA_Host"),
            "check": text(s.get("baseline_check"), f"{tag} baseline check"),
        },
        "weights_mib": number(s.get("weights_mib"), f"{tag} weights"),
        "idle_mib": number(s.get("idle_baseline_mib"), f"{tag} idle"),
        "flash_attention": text(s.get("flash_attention"), f"{tag} flash attention"),
        "kv_cache_type": text(s.get("kv_cache_type"), f"{tag} kv cache"),
        "search": [call(c, f"{tag} search call {i}") for i, c in enumerate(s.get("search_calls") or [])],
    }
    if "aborted_windows" in s:
        out["aborted_windows"] = [number(x, f"{tag} aborted window") for x in s["aborted_windows"]]
    if "slope_predictions" in s:
        out["slope_predictions"] = [{"ctx": number(p.get("ctx"), f"{tag} prediction"),
                                     "mib": number(p.get("mib"), f"{tag} prediction"),
                                     "from": [number(p.get("left_ctx"), tag), number(p.get("right_ctx"), tag)]}
                                    for p in s["slope_predictions"]]
    if "window_gates" in s:
        out["shared_gate_applied_from"] = min(
            (g["ctx"] for g in s["window_gates"] if g.get("shared_gate_applied")), default=None)
    return out


def collect_receipt(raw, ctx):
    """`rnd collect e5` entry point (collect.json)."""
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if not rows:
        raise SystemExit("the receipt has no records")
    prov = rows[0].get("provenance") or {}
    run_id, commit = text(prov.get("run_id"), "run id"), prov.get("git_sha")
    if not isinstance(commit, str) or not SHA.match(commit):
        raise SystemExit("the receipt's harness commit is not a full sha")
    first = rows[0].get("settings") or {}
    for row in rows:
        p = row.get("provenance") or {}
        if p.get("run_id") != run_id or p.get("git_sha") != commit or p.get("clean_tree") is not True:
            raise SystemExit("every record must share the run id and harness commit, from a clean tree")
    return {
        "provenance": {"repo": REPO_NAME, "source": ctx.source, "sha256": hashlib.sha256(raw).hexdigest(),
                       "receipt_commit": ctx.commit, "harness_commit": commit, "run_id": run_id},
        "date": text(rows[0].get("date"), "date"),
        "device": text(rows[0].get("device"), "device"),
        "engine": {"ollama": text(first.get("ollama_version"), "ollama version"),
                   "nvidia_driver": text(first.get("nvidia_driver"), "driver"),
                   "cuda": text(first.get("cuda_backend"), "cuda backend")},
        "rule": spec_rule(ctx.clone, commit),
        "models": [trim_model(r) for r in rows],
    }


def assert_public(doc_text, name):
    if "\\" in doc_text or re.search(r"[A-Za-z]:/", doc_text) or "@" in doc_text:
        raise SystemExit(f"{name} carries a path or an address")
    if re.search(r"(?i)users|appdata|luid|grant", doc_text):
        raise SystemExit(f"{name} carries a machine detail")
