# Fine-tuning Kev-4B as a judge of planted errors

**Question:** can a cheap local fine-tune turn Kev-4B into a reliable judge of
which of two long answers carries a planted error, without averaging over orders?

**Background:**
- Out of the box, Kev-4B picked option A 95% of the time on aspire-si's 127
  planted-error pairs, for 0.547 accuracy on hard choices.
- Averaging p(strong) over both orders gave 0.976. That was exploratory; aspire-si's
  pre-registered confirmation (PR #36) then measured 0.973 on 149 fresh pairs.

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
wsl bash score.sh judge-4b-full-s0         # serve it and score with judge_kev.py
python summarise.py                        # apply the rule across seeds
python stage_hf.py                         # stage the weights for Hugging Face
```

- **Training settings:**
  - LoRA rank 16 on a frozen Qwen3.5-4B-Base, plus the pointer head, from Kev-4B
    v1.0 (`--init_from`);
  - lr 2e-5, 2 epochs, batch 1 with accumulation 8, bf16 weights and autocast,
    gradient checkpointing;
  - `--perm_kl 1.0` penalises predictions that change with the option order;
  - `--max_state 1536` raises Kev's training limits (2,176 tokens per question,
    3,200 per record), so every row is kept whole. The frozen reference judged
    untruncated answers through `judge_kev.py` (no truncation at aspire-si
    c94fc93; Kev's server accepts up to 65,536 tokens), so training sees answers
    the same way. The longest row is 1,974 question tokens. The default limits
    dropped 964 of 1,086 rows in the first smoke run;
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

**The fine-tune helps: all three seeds pass the rule** (`python summarise.py`,
`results/summary.json`).

| seed | confirm hard choice | picks A | confirm order-averaged [95% CI] | judge hard choice | judge order-averaged |
|---|---|---|---|---|---|
| 0 | 0.963 | 50% | 0.980 [0.954, 1.000] | 0.969 | 0.992 |
| 1 | 0.956 | 50% | 0.987 [0.966, 1.000] | 0.969 | 0.992 |
| 2 | 0.960 | 49% | 0.980 [0.954, 1.000] | 0.965 | 1.000 |
| frozen Kev-4B | 0.547 | 95% | 0.973 [0.946, 0.993] | 0.547 | 0.976 |

- **What changed:** the position bias is gone. A single hard choice is now about
  as good as averaging over both orders.
- **What did not:** order-averaged accuracy is level with the frozen model; the
  CIs overlap, so this is not a measured improvement there.
- **Transfer:** the training pairs were planted the same way as the confirmation
  set, so only the judge set (bf16-planted) speaks to transfer. It holds there too.
- **Cost:** about 22 minutes per seed on the 5090 under WSL, PyTorch peak about
  10.5 GB, no row truncated or dropped. Scoring takes a few minutes per seed.
- **Use:** aspire-si keeps the frozen Kev-4B (v1.0, snapshot 6cfce5c2) as its
  pinned reference judge; the fine-tune appears beside it in its next critic
  comparison as "Kev-4B judge fine-tune (rnd, 51beba99, s0–s2)", never swapped in
  (agreed with session A, 2026-10-07).
- **Same scorer as the reference:** the seeds were scored with `judge_kev.py` from
  aspire-si ca5b915; the frozen reference used c94fc93. The file is identical in
  both (`git diff c94fc93 ca5b915` on it is empty), so the comparison is like for like.
- **Open:** the logged order-consistency KL differed between seeds at the
  sampled steps (about 0.001 in seed 1, 0.7–0.8 in seed 2) with the same
  outcome. Not investigated.

**Weights:** `stage_hf.py` stages the three adapters (rig paths stripped from the
configs and from `head.pt`, tensors checked unchanged). Uploaded to the private
Hugging Face repo `mcp-tool-shop/rnd-kev-judge-4b` at revision `51beba99`
(identity scan clean on the staged folder; Director's go, 2026-10-07).

## Transfer to a different planter (2026-10-08)

aspire-si built 47 pairs on 24 unseen prompts with errors planted by **gemma4:31b**
(Qwen-written strong answers, the same request and filters; median edit 8 characters
against Qwen's 5). Scored with `score_set.sh`, on a GPU slot granted by the Publisher.

| | single choice | picks A | order-averaged [95% CI] |
|---|---|---|---|
| frozen Kev-4B | 0.521 | 98% | 1.000 (47 of 47) |
| fine-tune s0 / s1 / s2 | 0.989 each | 51% | 0.989 [0.967, 1.000] |

- **The fine-tune transfers:** trained only on Qwen-planted pairs, it is as good or
  better on Gemma's plants (0.956–0.963 single choice on Qwen's). It learned errors, not
  Qwen's editing style, at least as far as one other planter shows.
- **The frozen model still shows the position bias** (A picked 98%), and is perfect
  once both orders are averaged.
- **Caveats:**
  - 47 pairs give wide intervals;
  - Gemma's edits are larger (1.6×, inside the 2× line), so these errors may simply be
    easier;
  - the three seeds give identical scores here.
