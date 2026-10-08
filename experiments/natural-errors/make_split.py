"""Freeze the tune/report split of the 95 adjudicated answers (PREREG-tuning-grid.md section 0).

    python make_split.py create   # write data/split.json (refuses to overwrite)
    python make_split.py check    # recompute from current inputs; fail if not exactly reproducible
    python make_split.py status   # print the strata table and half sizes

Stratified by topic x gold verdict x error-sentence band (0 / 1 / 2+), with the 10 blind
re-label items pinned to the report half. Deterministic: one fixed seed, and each cell's
shuffle is derived from the seed plus the cell key, so rerunning reproduces the same
assignment on any machine. Inputs are answers.json (topics), gold.json (verdicts and
sentence counts), selection.json (re-label pins); the 31 correction pairs are not an
input and stay fully held out.
"""

import argparse
import datetime
import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = DATA / "split.json"
SEED = 20261008
N_ITEMS = 95


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def file_sha(name):
    return hashlib.sha256((DATA / name).read_bytes()).hexdigest()[:16]


def band(n_sentences):
    return "2+" if n_sentences >= 2 else str(n_sentences)


def cell_seed(key):
    raw = "{}|{}".format(SEED, "|".join(key)).encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def compute_split():
    """Returns (tune, report, pins, strata) — all id sets sorted, strata a list of dicts."""
    answers = load("answers.json")
    items = answers.get("items") or answers.get("answers")
    topic = {x["id"]: x["topic"] for x in items}
    gold = load("gold.json")["items"]
    pins = sorted(load("selection.json")["relabel_later"])
    pinset = set(pins)
    assert len(pins) == 10, pins

    ids = sorted(gold)
    assert len(ids) == N_ITEMS and ids[0] == "n000" and ids[-1] == "n094", (ids[0], ids[-1], len(ids))
    assert set(ids) == set(topic), "gold and answers disagree on the item ids"
    bad = [i for i in ids if gold[i]["verdict"] not in ("error", "clean")]
    assert not bad, ("non-binary gold verdicts:", bad)
    assert pinset <= set(ids), "a re-label pin is not in the gold set"

    cells = {}
    for i in ids:
        key = (topic[i], gold[i]["verdict"], band(len(gold[i].get("sentences") or [])))
        cells.setdefault(key, []).append(i)

    # Per cell: tune takes ceil(n/2), capped by the items not pinned to report; the pins
    # themselves always sit in report. Shuffling is per-cell so the assignment of one
    # cell never depends on another cell's composition.
    tune, report = set(), set(pins)
    strata = []
    for key in sorted(cells):
        members = cells[key]
        free = sorted(m for m in members if m not in pinset)
        n_tune = min(len(members) - len(members) // 2, len(free))
        rng = random.Random(cell_seed(key))
        rng.shuffle(free)
        for j, m in enumerate(free):
            (tune if j < n_tune else report).add(m)
        strata.append({
            "topic": key[0], "verdict": key[1], "band": key[2], "n": len(members),
            "tune": n_tune, "report": len(members) - n_tune,
            "pinned": sum(1 for m in members if m in pinset),
        })

    assert not (tune & report), "an item is in both halves"
    assert tune | report == set(ids), "the halves do not cover all items"
    assert pinset <= report, "a pinned item escaped the report half"
    return sorted(tune), sorted(report), pins, strata


def body(tune, report, pins, strata):
    return {
        "schema": "natural-errors-split/v1",
        "registered": "2026-10-08",
        "spec": "PREREG-tuning-grid.md section 0",
        "seed": SEED,
        "rule": "stratified by topic x gold verdict x error-sentence band (0/1/2+); "
                "the 10 blind re-label items are pinned to the report half; per-cell "
                "shuffle derived from the seed, so the split is exactly reproducible",
        "inputs": {"answers.json": file_sha("answers.json"),
                   "gold.json": file_sha("gold.json"),
                   "selection.json": file_sha("selection.json")},
        "pinned_to_report": pins,
        "tune": tune,
        "report": report,
        "strata": strata,
    }


def seal(body_dict):
    """The self-hash convention from build_corrections.py."""
    raw = json.dumps(body_dict, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    body_dict["sha256"] = hashlib.sha256(raw.encode()).hexdigest()
    return body_dict


def print_strata(strata, tune_n, report_n):
    print("{:<22} {:<6} {:>3} {:>3} {:>5} {:>6} {:>6}".format(
        "topic", "verdict", "band", "n", "tune", "report", "pinned"))
    for s in strata:
        print("{:<22} {:<6} {:>3} {:>3} {:>5} {:>6} {:>6}".format(
            s["topic"], s["verdict"], s["band"], s["n"], s["tune"], s["report"], s["pinned"]))
    print("totals: tune", tune_n, "/ report", report_n, "of", tune_n + report_n)


def cmd_create(a):
    if OUT.exists():
        sys.exit("{} exists; refusing to overwrite a registered split (use check/status)".format(OUT.name))
    tune, report, pins, strata = compute_split()
    b = seal(body(tune, report, pins, strata))
    OUT.write_text(json.dumps(b, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8", newline="\n")
    print("->", OUT.name, b["sha256"][:12])
    print_strata(strata, len(tune), len(report))


def cmd_check(a):
    if not OUT.exists():
        sys.exit("{} is missing; run create first".format(OUT.name))
    have = json.loads(OUT.read_text(encoding="utf-8"))
    ok = True

    for name, sha in have["inputs"].items():
        now = file_sha(name)
        status = "ok" if now == sha else "CHANGED"
        ok &= now == sha
        print("input {:<16} {} ({}..)".format(name, status, sha[:8]))

    tune, report, pins, _ = compute_split()
    for field, want in (("tune", tune), ("report", report), ("pinned_to_report", pins)):
        match = sorted(have[field]) == sorted(want)
        ok &= match
        print("field {:<16} {}".format(field, "ok" if match else "MISMATCH"))

    raw = dict(have)
    stored = raw.pop("sha256")
    recomputed = seal(raw)["sha256"]
    ok &= recomputed == stored
    print("self-hash           {}".format("ok" if recomputed == stored else "MISMATCH"))

    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


def cmd_status(a):
    if not OUT.exists():
        sys.exit("{} is missing; run create first".format(OUT.name))
    have = json.loads(OUT.read_text(encoding="utf-8"))
    print_strata(have["strata"], len(have["tune"]), len(have["report"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["create", "check", "status"])
    a = ap.parse_args()
    {"create": cmd_create, "check": cmd_check, "status": cmd_status}[a.step](a)


if __name__ == "__main__":
    main()
