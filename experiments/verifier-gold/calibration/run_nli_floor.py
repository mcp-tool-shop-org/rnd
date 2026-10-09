#!/usr/bin/env python3
"""The pre-registered NLI floor for offrig's default-verifier rule (nli-floor.md, 2026-10-09).

cross-encoder/nli-deberta-v3-base @ 6c749ce3425cd33b46d187e45b92bbf96ee12ec7, through OpenVINO on the
Intel iGPU (found by name, as npu_serve.py does), batch 1, sequence 512, plain softmax argmax. No score
thresholds, no abstain gate, no prompt wrapper: premise = the claim's context texts joined "\n\n" in
record order, hypothesis = the claim text, entailment -> supported / contradiction -> unsupported /
neutral -> cannot_tell.

Runs both splits of both check types. Denominators are asserted against the prereg table before the first
claim runs; a mismatch aborts, since it means the gold moved under the prereg.

Outputs:
- --run-dir DIR: a run directory in offrig's own shape (manifest.json + verdicts.jsonl, schema from
  offrig @ 0f8b1c4, crates/offrig-core/src/calibrate_run.rs), so `offrig verify calibrate --report-only
  DIR` rescores it and its rows can be diffed against this repo's calibrate_metrics.py;
- --receipt PATH: the rnd receipt JSON: calibrate_metrics rows per leg, strata (has_doc_comment /
  self_referential / origin), truncation counts, seconds per claim, and the decision-fork inputs.

Fail loud, like npu-serve: any inference error aborts the run before anything is written. A floor report
with silent missing claims would poison the denominators. NLI legs are minutes, so there is no resume;
rerun instead.

The iGPU is the only device used (the NPU ledger is not touched, the 5090 never is). Per the prereg the
legs wait for the Publisher's card-free, so the calibration's timings stay honest.

    E:/AI/envs/npu-openvino/Scripts/python.exe -X utf8 run_nli_floor.py \
        --run-dir results/nli-floor-run --receipt results/2026-10-10-nli-floor.json
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
GOLD_ROOT = REPO_ROOT / "experiments" / "verifier-gold"
NPU_SERVE = REPO_ROOT / "experiments" / "npu-probe" / "npu_serve.py"
sys.path.insert(0, str(HERE))
import calibrate_metrics as cm

REPO = "cross-encoder/nli-deberta-v3-base"
REVISION = "6c749ce3425cd33b46d187e45b92bbf96ee12ec7"

GOLD_FILES = {"grounded": ["grounded.jsonl", "prs/grounded-prs.jsonl"],
              "reasoning": ["diffs/reasoning-diffs.jsonl"]}

# The prereg's exact denominators (nli-floor.md): (check type, split) -> label counts.
PREREG_COUNTS = {
    ("grounded", "tune"): {"supported": 127, "unsupported": 128, "cannot_tell": 15},
    ("grounded", "heldout"): {"supported": 112, "unsupported": 113, "cannot_tell": 5},
    ("reasoning", "tune"): {"supported": 102, "unsupported": 102, "cannot_tell": 19},
    ("reasoning", "heldout"): {"supported": 107, "unsupported": 108, "cannot_tell": 21},
}

# The prereg label map: the model's own id2label, lowercased, is asserted to be exactly these three.
LABEL_TO_VERDICT = {"entailment": "supported", "contradiction": "unsupported", "neutral": "cannot_tell"}
MAX_LEN = 512

# offrig calibrate_run::Line's fields, in declaration order (0f8b1c4). Kept explicit so a drift between
# this writer and the binary's reader fails a test instead of a cross-score.
LINE_FIELDS = ["claim_id", "check_type", "gold_label", "subtle", "has_doc_comment", "self_referential",
               "origin", "status", "error_code", "error", "model_verdict", "final_verdict", "reason",
               "quote_found", "needs_human", "reasoning", "evidence_quote", "evidence_order",
               "wall_seconds", "timing", "pins"]


def premise_of(claim: dict) -> str:
    """The claim's context texts joined in record order. Nothing else is added."""
    return "\n\n".join(c["text"] for c in claim["context"])


def assert_label_map(labels: list) -> None:
    got = sorted(str(x).lower() for x in labels)
    want = sorted(LABEL_TO_VERDICT)
    if got != want:
        raise SystemExit(f"model id2label lowercased is {got}; the prereg asserts exactly {want}")


def pair_token_count(tok, premise: str, hypothesis: str) -> int:
    """The untruncated pair length. The runner truncates at 512 (the tokenizer's default pair
    truncation, longest_first), so claims longer than this are counted as truncated."""
    return len(tok(premise, hypothesis)["input_ids"])


def load_gold(root: Path) -> list:
    """The three pinned gold files, in (check type, file, line) order. Unlabelled rows are out of
    scope, like the binary's skipped_unlabelled. A record whose check_type disagrees with its file
    set aborts the load."""
    gold = []
    for check_type, files in GOLD_FILES.items():
        for rel in files:
            p = root / rel
            for line in p.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                r = json.loads(line)
                if r.get("check_type") != check_type:
                    raise SystemExit(f"{p}: claim {r.get('id')} says check_type "
                                     f"{r.get('check_type')!r}, its file set is {check_type!r}")
                if not r.get("label"):
                    continue
                r["_file"] = rel
                gold.append(r)
    return gold


def check_denominators(gold: list) -> list:
    """Per-leg label counts against the prereg table, plus no claims outside the pinned legs."""
    errors = []
    for (ct, split), want in PREREG_COUNTS.items():
        got = {"supported": 0, "unsupported": 0, "cannot_tell": 0}
        for c in gold:
            if c["check_type"] == ct and c.get("split") == split and c["label"] in got:
                got[c["label"]] += 1
        if got != want:
            errors.append(f"{ct}/{split}: counts {got}, the prereg pins {want}")
    extra = sorted({f"{c['check_type']}/{c.get('split')}" for c in gold}
                   - {f"{ct}/{sp}" for ct, sp in PREREG_COUNTS})
    if extra:
        errors.append(f"claims outside the pinned legs: {extra}")
    return errors


def run_legs(nli, gold: list, splits=("tune", "heldout"), limit=None, progress=None) -> list:
    """Every (check type, split) leg in file order; one record per claim. Any inference error aborts
    the run (fail loud): nothing here is allowed to turn into a silent missing verdict."""
    records = []
    for ct in ("grounded", "reasoning"):
        for split in splits:
            leg = [c for c in gold if c["check_type"] == ct and c["split"] == split]
            if limit:
                leg = leg[:limit]
            for c in leg:
                premise = premise_of(c)
                toks = pair_token_count(nli.tok, premise, c["claim"])
                t0 = time.perf_counter()
                try:
                    got = nli.score(premise, c["claim"])
                except Exception as e:
                    raise SystemExit(f"claim {c['id']}: inference failed; nothing written: {e}") from e
                wall = time.perf_counter() - t0
                verdict = LABEL_TO_VERDICT[got["label"]]
                rec = {"id": c["id"], "check_type": ct, "split": split, "gold_label": c["label"],
                       "subtle": bool(c.get("subtle")),
                       "has_doc_comment": c.get("has_doc_comment"),
                       "self_referential": c.get("self_referential"), "origin": c.get("origin"),
                       "nli_label": got["label"], "probs": got["probs"], "verdict": verdict,
                       "wall_seconds": round(wall, 4), "pair_tokens": toks,
                       "truncated": toks > MAX_LEN}
                records.append(rec)
                if progress:
                    progress(json.dumps({"claim": c["id"], "leg": f"{ct}/{split}",
                                         "verdict": verdict, "gold": c["label"],
                                         "s": rec["wall_seconds"]}))
    return records


def strata_rows(leg_gold: list, outcomes: dict) -> dict:
    """The calibration report's strata, scored by the same metrics() as the headline rows."""
    out = {}
    for field in ("has_doc_comment", "self_referential", "origin"):
        groups = {}
        for c in leg_gold:
            key = c.get(field)
            groups.setdefault("unknown" if key is None else str(key), []).append(c)
        rows = {}
        for key in sorted(groups):
            m = cm.metrics(groups[key], outcomes)
            if m:
                r = m[0]
                rows[key] = {"n": r["n"], "false_accept": r["false_accept"],
                             "abstain": r["abstain"],
                             "decided_balanced_accuracy": r["decided_balanced_accuracy"]}
        out[field] = rows
    return out


def build_line(rec: dict) -> dict:
    """offrig calibrate_run::Line, all 21 fields. The NLI answers every claim with one of the three
    verdict kinds, so status is always ok and the unusable fields stay null."""
    line = {"claim_id": rec["id"], "check_type": rec["check_type"], "gold_label": rec["gold_label"],
            "subtle": rec["subtle"], "has_doc_comment": rec["has_doc_comment"],
            "self_referential": rec["self_referential"], "origin": rec["origin"], "status": "ok",
            "error_code": None, "error": None, "model_verdict": rec["verdict"],
            "final_verdict": rec["verdict"], "reason": None, "quote_found": None,
            "needs_human": None, "reasoning": None, "evidence_quote": None, "evidence_order": "file",
            "wall_seconds": rec["wall_seconds"], "timing": None, "pins": None}
    assert list(line) == LINE_FIELDS, "verdicts.jsonl line drifted from calibrate_run::Line"
    return line


def build_manifest(gold_root: Path, gold: list, records: list, ir_digest: str, settings: dict) -> dict:
    infos = []
    for rels in GOLD_FILES.values():
        for rel in rels:
            p = gold_root / rel
            infos.append({"file": rel, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                          "lines": sum(1 for line in p.read_text(encoding="utf-8").splitlines()
                                       if line.strip())})
    by_id = {c["id"]: c for c in gold}
    selected = [{"id": c["id"], "check_type": c["check_type"], "label": c["label"],
                 "subtle": bool(c.get("subtle")), "has_doc_comment": c.get("has_doc_comment"),
                 "self_referential": c.get("self_referential"), "origin": c.get("origin")}
                for c in (by_id[r["id"]] for r in records)]
    return {"offrig_version": f"run_nli_floor.py ({REPO}@{REVISION[:12]} via OpenVINO, not the "
                              "offrig runner)", "started_at": int(time.time()), "resumes": [],
            "model": "nli-deberta-v3-base", "model_digest": ir_digest,
            "ollama_version": "none (OpenVINO direct)", "settings": settings, "gpu_cost_hr": 0.0,
            "gold": infos, "skipped_unlabelled": 0, "selected": selected}


def write_run_dir(run_dir: Path, manifest: dict, records: list) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    with (run_dir / "verdicts.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for rec in records:
            f.write(json.dumps(build_line(rec)) + "\n")


def _sec_stats(walls: list) -> dict:
    return {"mean": round(sum(walls) / len(walls), 4) if walls else None,
            "max": max(walls) if walls else None}


def build_receipt(records: list, gold: list, device: str, ir_digest: str, ov_version: str,
                  limit, started: float) -> dict:
    legs = {}
    leg_gold = {}
    for r in records:
        key = (r["check_type"], r["split"])
        if key not in leg_gold:
            leg_gold[key] = [c for c in gold if c["check_type"] == key[0] and c["split"] == key[1]]
            legs[key] = []
        legs[key].append(r)
    legs_out = {}
    for key in legs:
        scored = legs[key]
        leg_claims = leg_gold[key]
        outcomes = {r["id"]: r["verdict"] for r in scored}
        row = cm.metrics(leg_claims, outcomes)[0]
        walls = [r["wall_seconds"] for r in scored]
        legs_out["%s/%s" % key] = {
            "scored_n": len(scored), "truncated_n": sum(1 for r in scored if r["truncated"]),
            "sec_per_claim": _sec_stats(walls),
            "metrics": row, "strata": strata_rows(leg_claims, outcomes)}
    gt = legs_out.get("grounded/tune", {}).get("metrics", {})
    return {"date": time.strftime("%Y-%m-%d"), "kind": "verifier-gold calibration: NLI floor",
            "prereg": "experiments/verifier-gold/calibration/nli-floor.md",
            "smoke": limit is not None, "limit": limit,
            "model": {"name": "nli-deberta-v3-base", "repo": REPO, "revision": REVISION,
                      "device": device, "ir_digest": ir_digest,
                      "label_map": LABEL_TO_VERDICT, "batch": 1, "seq": MAX_LEN},
            "openvino": ov_version, "denominators": "matched the prereg table before the first claim",
            "legs": legs_out, "wall_seconds_total": round(time.time() - started, 1),
            "decision_inputs": {"nli_grounded_tune_passes": gt.get("passes_default_rule"),
                                "nli_grounded_tune_decided_balanced_accuracy":
                                    gt.get("decided_balanced_accuracy")},
            "cross_scoring": {"how": "offrig verify calibrate --report-only <run-dir>",
                              "scorer": "calibrate_metrics.py beside this file"}}


def load_nli():
    """The pinned cross-encoder through npu_serve's NLI class, on the Intel iGPU found by name."""
    spec = importlib.util.spec_from_file_location("npu_serve", NPU_SERVE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    import openvino as ov
    core = ov.Core()
    device = mod.intel_igpu(core)
    return mod.NLI(core, device), device, getattr(ov, "__version__", "unknown")


def main() -> None:
    ap = argparse.ArgumentParser(description="The pre-registered NLI floor (nli-floor.md).")
    ap.add_argument("--run-dir", required=True, type=Path,
                    help="offrig-shaped run directory (manifest.json + verdicts.jsonl)")
    ap.add_argument("--receipt", required=True, type=Path, help="the rnd receipt JSON")
    ap.add_argument("--gold-root", type=Path, default=GOLD_ROOT)
    ap.add_argument("--splits", default="tune,heldout", help="comma list; the prereg runs both")
    ap.add_argument("--limit", type=int, default=None,
                    help="first N claims per leg; marks the receipt and run-dir as a smoke")
    a = ap.parse_args()
    splits = tuple(a.splits.split(","))
    gold = load_gold(a.gold_root)
    errors = check_denominators(gold)
    if errors:
        raise SystemExit("the gold does not match the prereg denominators; refusing to run:\n"
                         + "\n".join("  " + e for e in errors))
    nli, device, ov_version = load_nli()
    assert_label_map(nli.labels)
    print(f"loaded {REPO}@{REVISION[:12]} on {device}; prereg denominators matched", flush=True)
    started = time.time()
    records = run_legs(nli, gold, splits=splits, limit=a.limit, progress=print)
    settings = {"batch": 1, "seq": MAX_LEN, "argmax": "plain softmax", "truncation": "longest_first",
                "prompt_wrapper": None, "thresholds": None, "splits": list(splits)}
    write_run_dir(a.run_dir, build_manifest(a.gold_root, gold, records, nli.ir_digest, settings),
                  records)
    receipt = build_receipt(records, gold, device, nli.ir_digest, ov_version, a.limit, started)
    a.receipt.parent.mkdir(parents=True, exist_ok=True)
    a.receipt.write_text(json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {a.run_dir} and {a.receipt}")
    for leg, d in receipt["legs"].items():
        m = d["metrics"]
        fa = m["false_accept"]
        bal = m["decided_balanced_accuracy"]
        print(f"{leg}: n={m['n']} fa={fa['hits']}/{fa['of']} (upper {fa['high']:.3f}) "
              f"abstain={m['abstain']['hits']}/{m['abstain']['of']} "
              f"balanced={bal if bal is None else round(bal, 3)} passes={m['passes_default_rule']}")
    di = receipt["decision_inputs"]
    print(f"decision inputs: grounded/tune passes={di['nli_grounded_tune_passes']}, "
          f"balanced={di['nli_grounded_tune_decided_balanced_accuracy']}")


if __name__ == "__main__":
    main()
