"""Calibration metrics: a pure-Python reproduction of `calibrate::metrics` from offrig @ 0f8b1c4
(crates/offrig-core/src/calibrate.rs). Pure functions over gold claims and the verdicts a model gave;
no files, no devices. Pinned semantics, including the R&D review's scoring of gold cannot_tell:

- primary false-accept: (gold unsupported + gold cannot_tell) judged supported, over all of them;
- abstain: answered `cannot_tell` over gold supported + unsupported only;
- decided balanced accuracy: supported right / supported decided, averaged with not-supported right /
  not-supported decided, where a gold cannot_tell claim counts as decided only when judged `supported`
  (wrong) or `unsupported` (right); answering `cannot_tell` to one is neither decided nor an abstain.

tests/test_calibrate_metrics.py runs the Rust suite's hand-computed cases against this file. When the two
ever disagree, calibrate.rs wins and this file is fixed.
"""

import math

# The z value for a 95% interval, and the default rule's thresholds.
Z95 = 1.959963984540054
MAX_FALSE_ACCEPT_UPPER = 0.10
MAX_ABSTAIN = 0.20
MIN_BALANCED_ACCURACY = 0.80
MIN_UNSUPPORTED = 100

CHECK_ORDER = ("grounded", "reasoning", "knowledge")


def wilson_ci(x: int, n: int) -> tuple[float, float]:
    """The Wilson score interval for `x` successes in `n` trials. With no trials nothing is known,
    so it is the whole range."""
    if n == 0:
        return (0.0, 1.0)
    n = float(n)
    p = x / n
    z2 = Z95 * Z95
    denom = 1.0 + z2 / n
    centre = (p + z2 / (2.0 * n)) / denom
    half = Z95 * math.sqrt(p * (1.0 - p) / n + z2 / (4.0 * n * n)) / denom
    return (max(centre - half, 0.0), min(centre + half, 1.0))


def _rate(hits: int, of: int) -> dict:
    low, high = wilson_ci(hits, of)
    return {"hits": hits, "of": of, "rate": (hits / of) if of else None, "low": low, "high": high}


def metrics(gold: list[dict], outcomes: dict[str, str]) -> list[dict]:
    """Per check type metrics for `outcomes` (claim id -> verdict) against `gold`, in a stable order
    (grounded, reasoning, knowledge). Gold claims without a label are not scored; an outcome for a claim
    not in the gold set is ignored."""
    rows = []
    for ct in CHECK_ORDER:
        claims = [c for c in gold if c.get("check_type") == ct and c.get("label")]
        if claims:
            rows.append(_row(ct, claims, outcomes))
    return rows


def _row(check_type: str, gold: list[dict], said: dict[str, str]) -> dict:
    n = supported_n = unsupported_n = ct_n = missing = 0
    fa_unsup = subtle_n = subtle_fa = abstained = 0
    ct_fa = ct_said_ct = ct_said_unsup = 0
    sup_right = sup_decided = neg_right = neg_decided = 0  # decided claims: (right, decided) per side
    for c in gold:
        v = said.get(c["id"])
        if v is None:
            missing += 1
            continue
        n += 1
        truth, subtle = c["label"], bool(c.get("subtle"))
        if truth == "supported":
            supported_n += 1
            if v == "cannot_tell":
                abstained += 1
            else:
                sup_decided += 1
                sup_right += v == "supported"
        elif truth == "unsupported":
            unsupported_n += 1
            if subtle:
                subtle_n += 1
            if v == "cannot_tell":
                abstained += 1
            else:
                neg_decided += 1
                if v == "supported":
                    fa_unsup += 1
                    subtle_fa += subtle
                else:
                    neg_right += 1
        elif truth == "cannot_tell":
            ct_n += 1
            if v == "cannot_tell":
                ct_said_ct += 1
            else:
                neg_decided += 1
                if v == "supported":
                    ct_fa += 1
                else:
                    ct_said_unsup += 1
                    neg_right += 1
    false_accept = _rate(fa_unsup + ct_fa, unsupported_n + ct_n)
    abstain = _rate(abstained, supported_n + unsupported_n)
    balanced = None
    if sup_decided and neg_decided:
        balanced = (sup_right / sup_decided + neg_right / neg_decided) / 2.0
    passes = (missing == 0
              and unsupported_n >= MIN_UNSUPPORTED
              and false_accept["high"] < MAX_FALSE_ACCEPT_UPPER
              and abstain["rate"] is not None and abstain["rate"] <= MAX_ABSTAIN
              and balanced is not None and balanced >= MIN_BALANCED_ACCURACY)
    return {
        "check_type": check_type,
        "n": n,
        "supported_n": supported_n,
        "unsupported_n": unsupported_n,
        "cannot_tell_n": ct_n,
        "missing": missing,
        "false_accept": false_accept,
        "false_accept_unsupported_only": _rate(fa_unsup, unsupported_n),
        "subtle_false_accept": _rate(subtle_fa, subtle_n),
        "cannot_tell_gold": {
            "n": ct_n,
            "false_accept": _rate(ct_fa, ct_n),
            "said_cannot_tell": _rate(ct_said_ct, ct_n),
            "said_unsupported": ct_said_unsup,
        },
        "abstain": abstain,
        "decided_balanced_accuracy": balanced,
        "passes_default_rule": passes,
    }


def passes_default(rows: list[dict]) -> bool:
    """True when the model earns the default: both grounded and reasoning pass the rule.
    knowledge is reported but is not part of it."""
    passed = {r["check_type"] for r in rows if r["passes_default_rule"]}
    return "grounded" in passed and "reasoning" in passed
