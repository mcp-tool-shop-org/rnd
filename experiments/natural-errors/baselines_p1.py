"""P1 baselines on the frozen tune half (PREREG-tuning-grid.md section 0), from the v1 screens.

No GPU. Answer-level precision and recall against the gold verdicts, sentence recall on the error
sentences both labelling passes marked (and on the clear ones), with 95% bootstrap intervals over
answers (2000 resamples, seed 0). nemotron's v1 run is left out: it stored 39 failed replies as
empty lists, which cannot be told apart from "no errors".
"""
import hashlib
import json
import random
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"
JUDGES = ["gemma4:31b", "mistral-small:24b", "granite4.1:30b", "muse-glimmer:latest"]


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def stats(ids, flags, gold):
    tp = sum(bool(flags[k]) and gold[k]["verdict"] == "error" for k in ids)
    fp = sum(bool(flags[k]) and gold[k]["verdict"] != "error" for k in ids)
    fn = sum(not flags[k] and gold[k]["verdict"] == "error" for k in ids)
    hit = n = hit_c = n_c = 0
    for k in ids:
        fs = {f["sentence_index"] for f in flags[k] or []}
        for s in gold[k]["sentences"]:
            if s["by"] != "both":
                continue
            n += 1
            hit += s["s"] in fs
            if s["severity_max"] == "clear":
                n_c += 1
                hit_c += s["s"] in fs
    return {"precision": tp / (tp + fp) if tp + fp else None, "recall": tp / (tp + fn) if tp + fn else None,
            "sentence_recall": hit / n if n else None, "clear_recall": hit_c / n_c if n_c else None,
            "tp": tp, "fp": fp, "fn": fn, "sentences": n, "clear_sentences": n_c}


def ci(ids, flags, gold, key, rng):
    vals = []
    for _ in range(2000):
        v = stats([rng.choice(ids) for _ in ids], flags, gold)[key]
        if v is not None:
            vals.append(v)
    vals.sort()
    return [round(vals[int(0.025 * len(vals))], 3), round(vals[int(0.975 * len(vals)) - 1], 3)]


def main():
    split = load("split.json")
    tune = split["tune"]
    gold = load("gold.json")["items"]
    v1 = load("screen.json")["items"]
    extra = load("screen_extra.json")["items"]
    out = {"schema": "natural-errors-baselines/v1", "spec": "PREREG-tuning-grid.md section 0 (P1 baselines)",
           "split_sha256": split["sha256"], "half": "tune", "n": len(tune), "judges": {}}
    for j in JUDGES:
        src = extra if j == "muse-glimmer:latest" else v1
        flags = {k: src[k]["flags"].get(j) or [] for k in tune}
        row = stats(tune, flags, gold)
        rng = random.Random(0)
        for key in ("precision", "recall", "sentence_recall", "clear_recall"):
            row[key + "_ci"] = ci(tune, flags, gold, key, rng)
            row[key] = None if row[key] is None else round(row[key], 3)
        out["judges"][j] = row
    raw = json.dumps(out, sort_keys=True, separators=(",", ":"))
    out["sha256"] = hashlib.sha256(raw.encode()).hexdigest()
    (DATA / "baselines_p1.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    for j, r in out["judges"].items():
        print(f"{j:22s} P {r['precision']} {r['precision_ci']}  R {r['recall']} {r['recall_ci']}  "
              f"sent {r['sentence_recall']} {r['sentence_recall_ci']}  clear {r['clear_recall']}  "
              f"(tp {r['tp']} fp {r['fp']} fn {r['fn']}; {r['sentences']} sentences)")


if __name__ == "__main__":
    main()
