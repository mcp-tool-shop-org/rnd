# Claude + Colab: the golden path

**What this is.** The record behind the studio's way of running model work on rented Colab GPUs from Claude Code,
built over the Stage 1 writer pilot (2026-10-16 to 2026-10-18). The path itself is the handbook page
[Rented GPU windows](../../site/src/content/docs/handbook/rented-gpu-windows.md). The story, with the numbers, goes
in newsletter issue 13 once the pilot's last windows have run.

- [`data/`](data/): one row per window (44 so far) with its card, spend, outcome and the reason, the small records
  each window left, and a manifest that hashes every receipt file, including the tars and logs that stay private.
- [`scripts/colab/collect_windows.py`](../../scripts/colab/collect_windows.py) rebuilds `data/` from the Publisher's
  receipts folder. Nothing in `data/` is edited by hand.

The working window code lives in role-set (`scripts/colab/`): `smoke_window.sh`, `pin_window.py`, `vm_gate.py`, and
the fake CLI in `tests/fake_colab/`.

**Status.** Interim. The collector is rerun before issue 13 ships, so the final manifest includes the prebuild
windows and W-A.
