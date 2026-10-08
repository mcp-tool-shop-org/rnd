"""Stage the seeds for the private Hugging Face repo mcp-tool-shop/rnd-kev-judge-4b.

    python stage_hf.py [--runs DIR] [--out DIR]

Copies each judge-4b-full-s<N> run into <out>/s<N>/ without Kev's blank model-card
template, rewrites the rig paths in training_config.json and in head.pt's copy of
the training args to names relative to the repo (refusing if any head tensor
changes), and writes README.md (the model card) from results/summary.json. Run the
identity scan over <out> before uploading.
"""

import argparse
import json
import shutil
from pathlib import Path

HERE = Path(__file__).parent
RUNS = Path("E:/AI-Models/kev/judge-ft/runs")
OUT = Path("E:/AI-Models/kev/judge-ft/hf-stage")
KEEP = ("adapter_config.json", "adapter_model.safetensors", "chat_template.jinja",
        "tokenizer.json", "tokenizer_config.json", "training_metrics.json")


def clean_head(src: Path, dst: Path, seed: int) -> None:
    """head.pt carries a copy of the training args; rewrite its paths, keep every tensor."""
    import torch
    head = torch.load(src, map_location="cpu", weights_only=False)
    clean_config(head, seed)
    torch.save(head, dst)
    again = torch.load(dst, map_location="cpu", weights_only=False)
    before = torch.load(src, map_location="cpu", weights_only=False)["head"]
    if before.keys() != again["head"].keys() or not all(torch.equal(before[k], again["head"][k]) for k in before):
        raise SystemExit(f"refusing: head tensors changed while cleaning {src}")


def clean_config(cfg: dict, seed: int) -> dict:
    cfg["args"]["out"] = f"s{seed}"
    cfg["args"]["data"] = "train.jsonl (aspire-si fresh planted pairs; not published)"
    src = cfg.get("init_source") or {}
    if "resolved" in src:
        src["resolved"] = f"{src['init_from']} snapshot {Path(src['resolved']).name}"
    return cfg


def card(summary: dict) -> str:
    rows = "\n".join(
        f"| s{r['seed']} | {r['confirm_hard']:.3f} | {r['confirm_a_rate']:.0%} | "
        f"{r['confirm_order_averaged']:.3f} [{r['confirm_order_averaged_ci'][0]:.3f}, {r['confirm_order_averaged_ci'][1]:.3f}] | "
        f"{r['judge_hard']:.3f} | {r['judge_order_averaged']:.3f} |" for r in summary["seeds"])
    return f"""---
base_model: Qwen/Qwen3.5-4B-Base
library_name: peft
tags: [kev, decision-model, judge, lora, rnd]
---

# rnd-kev-judge-4b

**Research bench, private.** Kev-4B v1.0 (`jaredpalmer/kev-4b@v1.0`) fine-tuned as a
two-option judge: given a question and two long answers that differ in one planted
error, it picks the more correct answer. One adapter plus pointer head per seed, in
`s0/`, `s1/`, `s2/`.

Experiment, rule and code: `mcp-tool-shop-org/rnd`, `experiments/kev-judge-finetune`.
Research entry: `2026-10-07-open-jev-style-decision-models`.

## Results

Scored with aspire-si's `examples/sft-experiment/judge_kev.py`. Confirmation set: 149
fresh planted pairs from 78 held-out prompts. Judge set: 127 pairs planted by a
different model (bf16 Qwen-32B), reported as a transfer check. 95% CIs are
clustered by prompt.

| seed | confirm hard choice | picks A | confirm order-averaged [CI] | judge hard choice | judge order-averaged |
|---|---|---|---|---|---|
{rows}

Untrained Kev-4B on the same 149 pairs: 0.547 hard choice, A picked 95%, 0.973
order-averaged.

**Pre-registered rule** (written before the first run): hard-choice accuracy ≥ 0.85
with A picked 40–60%, order-averaged not below 0.973, on all three seeds.
Verdict: **{summary['verdict']}**.

## Training

- aspire-si's fresh `train_pairs.jsonl` (run 2026-10-08-kev-confirm): 543 + 60
  planted pairs from 310 training prompts, planted by Qwen2.5-32B Q4_K_M, each in
  both orders. 1,086 rows trained, 120 rows (31 prompts) held out for validation.
  No prompt overlaps either evaluation set.
- LoRA rank 16 on frozen Qwen3.5-4B-Base (revision `1001bb4d`), from Kev-4B v1.0;
  lr 2e-5, 2 epochs, batch 1 × accumulation 8, bf16, `--perm_kl 1.0`,
  `--max_state 1536`. About 22 minutes per seed on one RTX 5090 (WSL), PyTorch peak
  about 10.5 GB; no row truncated or dropped.
- Exact settings: `s<N>/training_config.json`.

## Use

Download, then serve one seed with Kev's server (kev @ 5e42a7a):

```bash
hf download mcp-tool-shop/rnd-kev-judge-4b --local-dir rnd-kev-judge-4b
python -m kev.serve --run rnd-kev-judge-4b/s0
```

## Limits

- **Trained on pairs planted the same way as the confirmation set** (same planter,
  same split procedure). Only the judge set, planted by a different model, speaks
  to transfer.
- The frozen Kev-4B stays aspire-si's pre-registered reference judge. This
  fine-tune is reported beside it as a second judge, not swapped in.

- One task: single planted errors in long answers, planted by Qwen models. Not
  tested on Kev's own benchmark or on other kinds of judgement.
- Licence not yet set. The base model's licence and the terms for training on
  Qwen-generated data must be checked before this repo is made public.
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=Path, default=RUNS)
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    summary = json.loads((HERE / "results" / "summary.json").read_text(encoding="utf-8"))
    if a.out.exists():
        shutil.rmtree(a.out)
    for r in summary["seeds"]:
        src, dst = a.runs / f"judge-4b-full-s{r['seed']}", a.out / f"s{r['seed']}"
        dst.mkdir(parents=True)
        for name in KEEP:
            shutil.copy2(src / name, dst / name)
        clean_head(src / "head.pt", dst / "head.pt", r["seed"])
        cfg = json.loads((src / "training_config.json").read_text(encoding="utf-8"))
        (dst / "training_config.json").write_text(json.dumps(clean_config(cfg, r["seed"]), indent=2), encoding="utf-8")
    (a.out / "README.md").write_text(card(summary), encoding="utf-8")
    print(f"staged {len(summary['seeds'])} seeds in {a.out}")


if __name__ == "__main__":
    main()
