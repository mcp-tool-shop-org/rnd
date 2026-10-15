# The dataset desk, pass 3 follow-up: brief for Argon

**From:** R&D. **Date:** 2026-10-15.

**The files:** `E:\AI\Research and Development\experiments\dataset-desk\`.

**The rules are unchanged:**
- offline tests only;
- no run on real art or a real model;
- no downloads;
- no writes outside this folder.

End with the output of `python -W error -m unittest test_desk` and `ruff check --select F,E9,B`.

## Pass 3, checked by R&D: it holds, with one gap

**Reproduced:** 35 tests pass and ruff is clean.

**Checked in the code:**
- the acceptance tests and the pinned arithmetic;
- the `canon.subject` match as a contiguous slice of words;
- `"".join(words)` for exact duplicates;
- the SigLIP2 count: lowercased, no padding, no truncation, on the cached patch14 tokenizer at `e8e48729…`;
- the stopword hash;
- the blind worksheet;
- the arm-model guards.

## 1. The drafter must be plain-sight (the gap)

`PlainSightDrafter` in `backends.py` doesn't use plain-sight. It loads `microsoft/Florence-2-large` itself:
- at revision `21a599d…`;
- with `trust_remote_code=True`;
- without `local_files_only`.

plain-sight (`E:\AI\plain-sight\src\plain_sight\engine.py`) is different:
- it pins `florence-community/Florence-2-large` at `4271c66b88cdbc05735372ec13b2360108de5317`;
- it uses the native transformers classes;
- it never sets `trust_remote_code`.

So the drafter recorded as plain-sight would be a different model, and it would run Python fetched from the hub.

**Change:**
- **The model:** the drafter runs plain-sight's model.
  - Use `plain_sight.engine.Florence2Engine`, imported lazily, when plain-sight is installed. It isn't installed in `E:\AI\envs\embedgemma` today, so a clear "install plain-sight" error is the expected outcome on this env.
  - Otherwise, mirror its pin exactly: the same repo id and revision, the native classes, and no `trust_remote_code` anywhere.
- **The task:** `<DETAILED_CAPTION>`, plain-sight's `detail="medium"`, as now.
- **No download:** load with `local_files_only=True`, or with `HF_HUB_OFFLINE=1` around the load. A missing snapshot is an error that names the repo and revision, never a download. The snapshot isn't on this rig yet; fetching it is the Director's call.
- **The record:** `drafter_id` and `drafter_revision` are the repo id and revision that actually loaded.
- **Tests, offline:**
  - with the engine or loader monkeypatched, the drafter asks for exactly plain-sight's repo and revision, offline;
  - `trust_remote_code` appears nowhere in the folder's code;
  - a missing snapshot raises the named error.

## 2. Stale wording

- `description_gate.py:471`: the reason string still says "equals or contains canon.subject". Make it "contains canon.subject as a contiguous run of words (4+ words)".
- `description_gate.py:330`: the comment says `" ".join(words(s))`. Make it `"".join(words(s))`.
- `wraps_canon_subject`'s docstring: the same correction as line 471.

## Not in this pass

- Moving the code to `mcp-tool-shop-org/dataset-desk`, which comes after this pass.
- The lite backend.
- Any real model run, C0 included.
