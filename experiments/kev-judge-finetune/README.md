# Fine-tuning Kev-4B as a judge of planted errors

**Question:** can a cheap local fine-tune turn Kev-4B into a reliable judge of
which of two long answers carries a planted error, without averaging over orders?

**Background:**
- Out of the box, Kev-4B picked option A 95% of the time on aspire-si's 127
  planted-error pairs, for 0.547 accuracy on hard choices.
- Averaging p(strong) over both orders gave 0.976. That was exploratory, and a
  pre-registered confirmation is running in aspire-si (PR #36).

Research entry: `2026-10-07-open-jev-style-decision-models`.

## Data (no overlap with either evaluation set)

| set | source | size | use |
|---|---|---|---|
| training | aspire-si fresh pairs, 279 training prompts | 543 pairs, 1,086 rows (both orders) | `train.jsonl` |
| Kev validation | 31 more training prompts | 60 pairs, 120 rows | `val.jsonl` |
| confirmation | 78 prompts held out by aspire-si's split | 149 pairs | evaluation only |
| judge set | the original 64 prompts | 127 pairs | evaluation only |

- **Planting:** the training and confirmation pairs were planted by Qwen2.5-32B
  Q4_K_M (llama.cpp). The judge set was planted by bf16 Qwen-32B. So the judge
  set is also a small transfer test between planting models.
- **Leak check:** `build_rows.py` refuses to write if any training prompt appears
  in either evaluation set. 0 leaks. Each pair becomes one row per order, so
  position carries no information.

## Run

```bash
python build_rows.py                       # Windows; writes E:/AI-Models/kev/judge-ft/
wsl bash train.sh smoke                    # memory and speed check
wsl bash train.sh full 0                   # the run (more seeds if it holds)
```

- **Training settings:**
  - LoRA rank 16 on a frozen Qwen3.5-4B-Base, plus the pointer head, from Kev-4B
    v1.0 (`--init_from`);
  - lr 2e-5, 2 epochs, batch 1 with accumulation 8, bf16 weights and autocast,
    gradient checkpointing;
  - `--perm_kl 1.0` penalises predictions that change with the option order;
  - PyTorch capped at 0.82 of the card.
- **Environment:** WSL Ubuntu, torch 2.8.0+cu128, flash-linear-attention 0.5.2
  (Kev's fused kernels), kev @ 5e42a7a.
- **Scoring:** aspire-si's own `examples/sft-experiment/judge_kev.py`, the same
  requests and statistics, on the judge set and the confirmation set:
  - hard-choice accuracy and the rate of choosing A;
  - order-averaged accuracy (mean p(strong) over both orders, favoured above
    0.5, ties count half).

## What would count

Written before the run:
- A fine-tune **helps** if its hard-choice accuracy on the confirmation set
  reaches 0.85 or more, with the rate of choosing A between 40% and 60%.
- It must also not fall below the untrained Kev-4B's order-averaged accuracy on
  the same set.
- The judge set (bf16-planted) is reported beside it as the transfer check.
- One seed is a pilot. A positive result needs three seeds, given the run-to-run
  variance seen in aspire-si's critics.

## Results

Not run yet: waiting for the 5090 (aspire-si's confirmation scoring is on it).
