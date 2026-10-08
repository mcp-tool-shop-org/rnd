"""Turn aspire-si's fresh planted-error pairs into Kev training rows.

    python build_rows.py [--fresh DIR] [--judge-set FILE] [--out DIR]

Each {prompt, strong, flawed} pair becomes two `choice` rows, one per order, so
the answer's position carries no information. The rows use the same state and
instructions as aspire-si's judge_kev.py, the request the model is scored with.
About 10% of the training prompts are held out as Kev's own validation file. The
build refuses to write anything if a training prompt also appears in the
confirmation set or the 127-pair judge set.
"""

import argparse
import json
import random
from pathlib import Path

INSTRUCTIONS = (
    "Two answers to the question are given as options A and B. They may differ in only one "
    "sentence. Which answer is more correct? Judge the correctness of facts, numbers and "
    "reasoning, not style or length."
)
FRESH = Path("E:/AI/aspire-si-runs/2026-10-08-kev-confirm/fresh")
JUDGE_SET = Path("E:/AI/aspire-si-runs/2026-10-07-sft/a3/data/judge_set.json")   # the 127 planted pairs
OUT = Path("E:/AI-Models/kev/judge-ft")


def rows_for(pair: dict) -> list[dict]:
    """Both orders of one pair, labelled with the strong answer's option."""
    out = []
    for first, second, label in ((pair["strong"], pair["flawed"], "A"), (pair["flawed"], pair["strong"], "B")):
        out.append({"state": pair["prompt"],
                    "questions": {"better": {"type": "choice", "instructions": INSTRUCTIONS,
                                             "criteria": {"A": first, "B": second}, "label": label}}})
    return out


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def prompts_of(pairs) -> set[str]:
    return {p["prompt"].strip() for p in pairs}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fresh", type=Path, default=FRESH)
    ap.add_argument("--judge-set", type=Path, default=JUDGE_SET)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--val-frac", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()

    train = [json.loads(l) for l in (a.fresh / "train_pairs.jsonl").read_text(encoding="utf-8").splitlines()]
    split = load_json(a.fresh / "split.json")
    confirm = load_json(a.fresh / "confirm_set.json")
    judge = load_json(a.judge_set)
    confirm_pairs = confirm if isinstance(confirm, list) else confirm.get("pairs", [])
    judge_pairs = judge if isinstance(judge, list) else judge.get("pairs", [])

    allowed = set(split["train"])
    stray = [p["pair_id"] for p in train if p["prompt_id"] not in allowed]
    leak_confirm = prompts_of(train) & prompts_of(confirm_pairs)
    leak_judge = prompts_of(train) & prompts_of(judge_pairs)
    if stray or leak_confirm or leak_judge:
        raise SystemExit(f"refusing: {len(stray)} pairs outside the training split, "
                         f"{len(leak_confirm)} prompts shared with the confirmation set, "
                         f"{len(leak_judge)} with the judge set")

    ids = sorted({p["prompt_id"] for p in train})
    rng = random.Random(a.seed)
    val_ids = set(rng.sample(ids, max(1, round(a.val_frac * len(ids)))))
    a.out.mkdir(parents=True, exist_ok=True)
    counts = {}
    for name, keep in (("train", lambda p: p["prompt_id"] not in val_ids), ("val", lambda p: p["prompt_id"] in val_ids)):
        rows = [r for p in train if keep(p) for r in rows_for(p)]
        rng.shuffle(rows)
        (a.out / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        counts[name] = {"rows": len(rows), "prompts": len({p["prompt_id"] for p in train if keep(p)})}
    meta = {"pairs": len(train), **counts, "confirm_pairs": len(confirm_pairs), "judge_pairs": len(judge_pairs),
            "leaks": 0, "instructions": INSTRUCTIONS, "seed": a.seed}
    (a.out / "build.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
