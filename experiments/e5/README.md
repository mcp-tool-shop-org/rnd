# E5: how much context each local model holds on the 5090

E5 is one of interlock's pre-registered experiments. For each local model on the RTX 5090, it finds the largest
context window (`num_ctx`) that stays fully on the card, stays under 30500 MiB, and doesn't spill into system memory.

The records here are trimmed copies of interlock's receipts. `rnd collect e5` makes them, from the commits and hashes
pinned in `collect.json`:

| File | Receipt | Harness | Models |
|---|---|---|---|
| `results/run-b.json` | `receipts/e5-2026-10-13b.jsonl` at 6e8cab6 | d899ac0 | all six; three valid at their trained caps |
| `results/run-c.json` | `receipts/e5-2026-10-13c.jsonl` at cc91aed | 0db35c8 | gemma4:31b, granite4.1:30b, llama3.1:8b, after a dated amendment |

Each record keeps:
- the result and its `limit`;
- the trained cap;
- the floor window's readings;
- the engine versions;
- the spec thresholds at the harness commit;
- every search call: kind, window, peak MiB, shared MiB, prompt rate and verdict.

It leaves out machine details, and the receipts' decode rate: each confirm generates one token, so that number is
not a rate.

R&D's ruling on each model, and the defects found on the way, are in
[the E5 entry](../../entries/2026/2026-10-13-e5-fill-card.md).

To recollect, and to check the committed copies against the receipts:

```bash
python -m rnd collect e5 --clone <interlock checkout>
python -m rnd collect e5 --clone <interlock checkout> --check
```
