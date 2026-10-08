"""Measure CUDA graphs on aspire-si's critic heads, and gate them on correctness.

Runs three ways for each (role, pooling) form on the real cache (train.plain → confirm.plain):
  original  aspire-si's own train_head + score_set, unchanged (CPU features, per-pair scoring)
  fast      graphed_heads with graphs off (GPU-resident features, batched scoring)
  graphed   graphed_heads with the CUDA-graph training step

Gates (written before the run, in README.md):
  exact     dropout 0, seed 42: per-step losses of fast vs graphed, and confirm scores of all three,
            agree within tolerance, and every pair's win/loss is the same.
  outcome   dropout as trained (0.1), seeds 42-44: graphed's seed-mean confirm pair-win rate lies
            inside original's prompt-clustered 95% bootstrap interval.

GPU only after the Publisher grants it. Usage (aspire-cu134 env):
  python bench.py --aspire E:/AI/aspire-si --cache <cache>/llama --out results/<name>.json
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOL_SCORE = 1e-3  # scores are 0-10; the measured scoring noise between cards was 0.002
TOL_LOSS = 1e-4


def timed(fn):
    import torch

    torch.cuda.synchronize()
    t = time.perf_counter()
    out = fn()
    torch.cuda.synchronize()
    return out, time.perf_counter() - t


def busy_fraction(fn, repeat: int = 20) -> dict:
    """Share of wall time the GPU spends running kernels while `fn` repeats. Near 1: compute-bound,
    graphs cannot help much. Well below 1: the GPU waits on the CPU (launches, syncs, copies)."""
    import torch
    from torch.profiler import ProfilerActivity, profile

    fn()
    torch.cuda.synchronize()
    with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
        t = time.perf_counter()
        for _ in range(repeat):
            fn()
        torch.cuda.synchronize()
        wall = time.perf_counter() - t
    kernel_us = sum(
        e.device_time for e in prof.events() if getattr(e, "device_type", None) == torch.autograd.DeviceType.CUDA
    )
    return {"wall_s": wall, "kernel_s": kernel_us / 1e6, "busy": kernel_us / 1e6 / wall if wall else None}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aspire", type=Path, required=True)
    ap.add_argument("--cache", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--forms", default="auditor:mean,auditor:attention,advocate:mean,advocate:span,auditor:mid")
    ap.add_argument("--seeds", default="42,43,44")
    args = ap.parse_args()

    sys.path[:0] = [str(args.aspire), str(args.aspire / "examples" / "sft-experiment"), str(HERE)]
    import torch
    from critic_heads import HPARAMS, boot, pair_wins, role_scores, score_set, train_head
    from critic_heads_run import _features, _load

    from graphed_heads import score_set_fast, stack_features, train_head_fast

    seeds = [int(s) for s in args.seeds.split(",")]
    report = {
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cache": args.cache.name,
        "hparams": HPARAMS,
        "tolerance": {"score": TOL_SCORE, "loss": TOL_LOSS},
        "load_s": {},
        "forms": {},
    }
    (train, report["load_s"]["train"]) = timed(lambda: _load(args.cache, "train", "plain", "cpu"))
    (conf, report["load_s"]["confirm"]) = timed(lambda: _load(args.cache, "confirm", "plain", "cpu"))
    pairs, states, spans, mids = train
    p2, s2, sp2, mid2 = conf
    index = [(2 * i, 2 * i + 1) for i in range(len(pairs))]
    cindex = [(2 * i, 2 * i + 1) for i in range(len(p2))]
    prompt_ids = [p["prompt_id"] for p in p2]
    no_dropout = {**HPARAMS, "dropout": 0.0}

    for form in args.forms.split(","):
        role, pooling = form.split(":")
        row: dict = {}
        (feats, masks), row["features_s"] = timed(lambda: _features(states, spans, pooling, mids))
        f2, m2 = _features(s2, sp2, pooling, mid2)
        (stacked, row["stack_s"]) = timed(lambda: (stack_features(feats, masks), stack_features(f2, m2)))
        (x, m, lens), (cx, cm, clens) = stacked
        row["stack_gb"] = (x.numel() * x.element_size() + cx.numel() * cx.element_size()) / 1e9

        def run(mode: str, seed: int, hp: dict):
            if mode == "original":
                head, t_train = timed(lambda: train_head(role, pooling, seed, feats, masks, index, None, "cuda", hp))
                (sc, t_score) = timed(lambda: score_set(head, f2, m2, cindex, "cuda"))
                return {"train_s": t_train, "score_s": t_score, "scores": sc, "losses": None}
            (head, losses), t_train = timed(
                lambda: train_head_fast(role, pooling, seed, x, m, lens, index, None, hp, graphs=mode == "graphed")
            )
            (sc, t_score) = timed(lambda: score_set_fast(head, cx, cm, clens, cindex))
            return {"train_s": t_train, "score_s": t_score, "scores": sc, "losses": losses}

        # Gate 1: exactness at dropout 0.
        ex = {mode: run(mode, 42, no_dropout) for mode in ("original", "fast", "graphed")}

        def max_diff(a, b):
            return max(abs(u - v) for u, v in zip(a[0] + a[1], b[0] + b[1]))

        def wins(sc):
            return pair_wins(*role_scores(role, *sc))

        exact = {
            "score_diff_fast": max_diff(ex["original"]["scores"], ex["fast"]["scores"]),
            "score_diff_graphed": max_diff(ex["original"]["scores"], ex["graphed"]["scores"]),
            "loss_diff_fast_vs_graphed": max(abs(a - b) for a, b in zip(ex["fast"]["losses"], ex["graphed"]["losses"])),
            "win_flips_graphed": sum(a != b for a, b in zip(wins(ex["original"]["scores"]), wins(ex["graphed"]["scores"]))),
        }
        exact["pass"] = (
            exact["score_diff_fast"] <= TOL_SCORE
            and exact["score_diff_graphed"] <= TOL_SCORE
            and exact["loss_diff_fast_vs_graphed"] <= TOL_LOSS
            and exact["win_flips_graphed"] == 0
        )
        row["exact"] = exact
        row["loss_curve_dropout0"] = {k: ex[k]["losses"] for k in ("fast", "graphed")}

        # Gate 2: outcome with dropout on, seed-mean pair wins.
        outcome, timing = {}, {}
        for mode in ("original", "fast", "graphed"):
            runs = [run(mode, s, HPARAMS) for s in seeds]
            per_seed = [wins(r["scores"]) for r in runs]
            mean_wins = [statistics.fmean(w[i] for w in per_seed) for i in range(len(prompt_ids))]
            point, ci = boot(mean_wins, prompt_ids)
            outcome[mode] = {"point": point, "ci": ci, "per_seed": [statistics.fmean(w) for w in per_seed]}
            timing[mode] = {
                "train_s": [r["train_s"] for r in runs],
                "score_s": [r["score_s"] for r in runs],
            }
        lo, hi = outcome["original"]["ci"]
        outcome["pass"] = lo <= outcome["graphed"]["point"] <= hi and lo <= outcome["fast"]["point"] <= hi
        row["outcome"] = outcome
        row["timing"] = timing
        base = statistics.median(timing["original"]["train_s"])
        row["speedup_train"] = {k: base / statistics.median(v["train_s"]) for k, v in timing.items()}
        sbase = statistics.median(timing["original"]["score_s"])
        row["speedup_score"] = {k: sbase / statistics.median(v["score_s"]) for k, v in timing.items()}

        # Where the time goes: GPU-busy share of one eager training step on stacked features.
        from graphed_heads import _forward, pair_loss

        head, _ = train_head_fast(role, pooling, 42, x, m, lens, index[:8], None, {**HPARAMS, "epochs": 1})
        head.train()
        opt = torch.optim.AdamW(head.parameters(), lr=HPARAMS["lr"])
        idx = torch.arange(16, device=x.device)

        def step():
            loss = pair_loss(role, _forward(head, x, m, idx, max(lens[:16])))
            opt.zero_grad()
            loss.backward()
            opt.step()

        row["eager_step_busy"] = busy_fraction(step)
        row["peak_vram_gb"] = torch.cuda.max_memory_allocated() / 1e9
        report["forms"][form] = row
        print(form, "exact", exact["pass"], "outcome", outcome["pass"], "train x", row["speedup_train"], flush=True)
        del x, m, cx, cm, stacked
        torch.cuda.empty_cache()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print("BENCH-OK", args.out)


if __name__ == "__main__":
    main()
