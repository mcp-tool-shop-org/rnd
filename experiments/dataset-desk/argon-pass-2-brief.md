# The dataset desk, pass 2: brief for Argon

**From:** R&D. **Date:** 2026-10-15. **The files:** `E:\AI\Research and Development\experiments\dataset-desk\`
(`desk.py`, `backends.py`, `test_desk.py`, `design.md`, `README.md`).

**The rules for this pass are unchanged:**
- Offline tests only.
- No run on real art or a real model.
- No downloads.
- No writes outside the folder above.

Please end the pass with the test output (`python -W error -m unittest test_desk`) and a list of what you changed.

## 1. Your pass 1 findings, checked on the rig: all confirmed

| finding | checked |
|---|---|
| tallow-fen's `style_residue_prop` rejections are on-style | 54 of 54 say "style on-target" |
| salt-road's `judgment.explanation` is mostly a ruling | 73 approved records, 6 distinct strings; 54 are the same ruling; `canon.subject` holds 73 distinct descriptions |
| rustline's descriptions are shared | 172 approved, 31 distinct; one string ×14. They read like style-prefixed prompts (9 equal the record's prompt) |
| the wave files exist | 110 `generation.json`, 60 `_curation.json`; the `passed` / `failed` / `issues` layout matches your parser |

Your heads-up about the multimodal experiment was right, and it matters. Its key was "each description belongs to one
image", and that fails for about 245 of its 385 queries. R&D is revising that design separately, with you, before its
harness is written. It isn't part of this pass.

## 2. What pass 1 said it fixed, against the code

These are from R&D's read of the code. Please fix each one, or say why not.

1. **The thread caps still come after numpy loads.**
   - `desk.py` and `backends.py` import numpy at the top, and `cap_threads()` runs later, in `main()`. So numpy's BLAS
     pool sizes itself to the machine. `img @ img.T` in the analyses can then use all 24 cores, the exact class of
     the 2026-10-15 CPU incident.
   - **The fix:**
     - Set the capped env defaults at the very top of `desk.py`, before `import numpy`. Read `--threads` from argv
       there, or use a fixed default of 4 that the flag can lower.
     - `OPENBLAS_NUM_THREADS` and `MKL_NUM_THREADS` = 1 inside torch regions, as in the embed-serve disposition.
     - Guard `torch.set_num_interop_threads` so it runs once per process.
   - **A test:** importing `desk` with no env set leaves `OPENBLAS_NUM_THREADS` (and the others) capped.
2. **The peeking guard isn't in the code.** `index` embeds every description, and `report` always runs `captions()`.
   - **The fix:** add `--images-only`, for index and report. Also refuse to embed descriptions for `rustline`,
     `tallow-fen`, `salt-road` and `hesperia` unless `--allow-multimodal-pool` is passed. Recognise the projects by
     folder name, and say so in the refusal.
   - **A test:** a project folder named `salt-road` refuses without the flag.
3. **Failure modes are never loaded.** `load_records` reads `j.get("failure_mode")`, but the records hold
   `failure_modes`, a list. So C3's labels can't reach the desk. Load the list, and show it in the report beside
   rejected and borderline images.
4. **Rejection notes are embedded as descriptions.**
   - `explanation = subj or j_exp` applies to every status. So tallow-fen's rejection notes get searched as if they
     described the image, and `captions()` defaults to `approved_only=False`.
   - **The fix:** a description is `canon.subject`, or else `judgment.explanation` only when the status is approved.
     Keep the judgment note separately, for display. `captions()` and `swap_check()` use approved images only.
5. **`vision_tokens` does nothing.** It's recorded in the cache and keys the cache, but never reaches the model.
   - **The fix:** wire it into EG2's image processing, using the processor option sentence-transformers 6.1 / transformers
     5.19 actually expose. Read the installed source in `E:\AI\envs\embedgemma`; don't guess.
   - Otherwise, remove it until it can be wired.
6. **The PNG prompt parser can return the negative prompt.** It keeps the longest `CLIPTextEncode` text, and the
   studio's negative prompts are often the longer one. Follow the sampler's `positive` input to its text node instead,
   and keep the negative as `negative_prompt`.
7. **Every index run rescans everything.** Each `index` run, for each backend, recomputes the sha256, dHash, palette
   and native-resolution texture for every image. The texture statistics at up to 1,344 px are the expensive part,
   and their cost isn't measured.
   - **The fix:** a scan cache keyed by sha256 under `--out` (`scan.jsonl`), shared by the backends.
   - Record seconds per image for the look channel in `meta.json`, so C0 can state the full run's load before it
     starts.
8. **Byte-identical files with different records.** Prefer the approved record deterministically, and keep the
   collision in `problems`. Today the first one walked wins.
9. **Lint.** `ruff check --select F,E9,B` reports 10 findings: `zip()` without `strict=`, and a blind
   `assertRaises(Exception)`. Clear them.

## 3. Scope: keep v0 the review desk

Part I of your pass, the five-stage closed loop, is a good roadmap: two-LoRA tiers, medoid triage, auto-placement,
gap-driven generation through comfy-headless, and grounding-based salvage. For v0 it belongs in `design.md`'s deferred
table, each item with the trigger that would bring it in.
- **v0 stays:** index, duplicates, search, coverage, the two-channel look reading, the description check, the report.
- **Already in pass 1's code, and fine to keep:** the wave and curation provenance in the report, and multimodal
  search.

## 4. Two new questions from the Director

**A. Where the desk lives.** The repo `mcp-tool-shop-org/dataset-desk` now exists (internal, LICENSE only).
- R&D proposes that the desk move there after this pass, as a package with a CLI.
- rnd would keep the design record, the reviews and the calibration experiments.
- Is the package boundary right? Which modules?

**B. dataset-desk-lite, for machines that can't run the newest CUDA.**
- Note that the desk needs no CUDA today: it runs on the CPU build of torch. What limits an older machine is torch
  itself, plus a 440M model in float32 (about 1.8 GB of RAM) and its CPU time.
- R&D's proposal is one code base with tiers, not a fork:
  - **lite:** numpy and Pillow only, no torch. It does the hash tier, the look channel, the record and wave
    provenance, and every report section that needs no embedding.
  - **lite with a small embedder:** an optional small model on ONNX Runtime CPU.
  - **full:** the torch backends as now.
- Please answer:
  1. Are tiers right, or should lite be its own package?
  2. Which small embedder and runtime fit lite? For example: SigLIP2 base exported to ONNX; EG2 at 256 dimensions; an
     int8 quantisation. With what licence, and what RAM?
  3. Can the cache and report stay compatible across tiers?

Answer B in `design.md`. Implement only what's needed to make the lite path importable and tested without torch: a
`--backend none` that gives the report's no-embedding sections. Don't add new dependencies.

## 5. When you're done

- `python -W error -m unittest test_desk`: all pass, offline.
- `ruff check --select F,E9,B desk.py backends.py test_desk.py`: clean.
- `design.md`:
  - C3 uses your corrected labels;
  - the deferred table holds Part I;
  - §4 is answered;
  - the standards table is updated, with ANDON at 2 if `--strict` and the problems list cover unreadable files.
