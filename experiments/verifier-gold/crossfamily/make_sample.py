"""Draw the cross-family label sample from both gold sets. Fixed before any model sees it (2026-10-08).

120 claims: 60 grounded, 60 reasoning. Every item a human ruling touched is in (the PR set's adjudicated
items, the hard batch's split), then the rest are drawn at random by label so each label's share matches
its set. Seeded, so the sample can be rebuilt exactly. Writes sample.jsonl (gold, kept),
blind_in.json (claim and evidence only) and blind_key.json."""

import json
import random
from pathlib import Path

HERE = Path(__file__).parent
GOLD = HERE.parent
SEED = 20261008

FORCED = {  # items a ruling touched: the PR adjudication and the hard batch's split
    "grounded": ["prs-aspire-si-53-1s", "prs-aspire-si-59-3u", "prs-aspire-si-61-9s", "prs-offrig-39-15s",
                 "prs-aspire-si-61-2s"],
    "reasoning": ["diffhard-aspire-si-52-1u", "diff-offrig-24-3s", "diff-aspire-si-51-1s", "diff-offrig-8-5c",
                  "diff-offrig-3-3c"],
}
SOURCES = {
    "grounded": ["grounded.jsonl", "prs/grounded-prs.jsonl"],
    "reasoning": ["diffs/source-publisher-f3f3f66.jsonl", "diffs/source-publisher-hard.jsonl"],
}


def load(paths):
    rows = []
    for p in paths:
        rows += [json.loads(line) for line in (GOLD / p).read_text(encoding="utf-8").splitlines() if line.strip()]
    return rows


def draw(rows, forced, n, rng):
    by_id = {r["id"]: r for r in rows}
    missing = [i for i in forced if i not in by_id]
    if missing:
        raise SystemExit(f"forced ids not in the set: {missing}")
    picked = [by_id[i] for i in forced]
    rest = [r for r in rows if r["id"] not in set(forced)]
    labels = sorted({r["label"] for r in rows})
    need = n - len(picked)
    for k, lab in enumerate(labels):
        pool = [r for r in rest if r["label"] == lab]
        share = round(need * len([r for r in rows if r["label"] == lab]) / len(rows)) if k < len(labels) - 1 \
            else n - len(picked)
        picked += rng.sample(pool, share)
    return picked


def main():
    rng = random.Random(SEED)
    sample = []
    for kind in ("grounded", "reasoning"):
        sample += [dict(r, sample_stratum=kind) for r in draw(load(SOURCES[kind]), FORCED[kind], 60, rng)]
    rng.shuffle(sample)
    (HERE / "sample.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in sample),
                                       encoding="utf-8", newline="\n")
    # No ids in the blind file: their suffixes (-1s, -1u, -5c) give the label away. The key is separate.
    blind = [{"n": i + 1, "claim": r["claim"],
              "evidence": [{"source": c["source"], "text": c["text"]} for c in r["context"]]}
             for i, r in enumerate(sample)]
    (HERE / "blind_in.json").write_text(json.dumps(blind, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "blind_key.json").write_text(json.dumps({str(i + 1): r["id"] for i, r in enumerate(sample)}, indent=0),
                                         encoding="utf-8")
    from collections import Counter
    print(len(sample), Counter((r["sample_stratum"], r["label"]) for r in sample))


if __name__ == "__main__":
    main()
