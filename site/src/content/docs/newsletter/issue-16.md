---
title: "What counts as a duplicate? Calibrating the dataset desk"
description: The studio's dataset desk flags duplicate images and files before they reach training data. Its thresholds were guesses. We planted copies among known originals, measured what six models and a simple image hash catch, and found that a different view of the same ship looks like a duplicate to most of them. We also found that the desk's memory figures were short by up to seven times.
issue: 16
date: 2026-10-20
highlights:
  - "<strong>The old image rule flagged three in four views of the same object as duplicates.</strong> SigLIP2 at the desk's 0.95 caught 95% of planted copies, but also 77% of same-object, different-angle pairs. A two-signal rule with DINOv2 and a mirror-aware image hash keeps 91% of the copies and flags no images from other projects."
  - "<strong>Views are settled by the records, not by a threshold.</strong> The studio's turntable records already say which object and which camera angle each image is. Two angles of one object are never duplicates, whatever their score."
  - "<strong>One embedding model doesn't fit every job.</strong> Used the way its model card says, EmbeddingGemma 2 separates copied scripts cleanly. On logs and JSON from different runs it can't tell copies from look-alikes, so bge-m3 stays the default for text."
  - "<strong>The desk's memory figures were short by up to seven times.</strong> Measured at long inputs, three of the four text models needed 3.8× to 6.9× the VRAM the desk had registered for them."
---

The studio builds training data from its own art and run records. Before anything is trained on, a tool called the
**dataset desk** reads the set and flags problems, and duplicates are one of them. A duplicate does two kinds of damage.
It counts one example twice. And when a copy lands on both sides of a train/test split, it quietly inflates the test
score.

The desk never deletes anything: it flags, and a person decides. So a flag has to be worth a person's time. Until this
week its thresholds were borrowed from other people's data, with a note saying they needed recalibrating. This issue is
that recalibration, in three rungs, on the RTX 5090.

## How you measure a duplicate finder

You can't measure a duplicate finder on data where nobody knows the answer. So we made the answer:
- **Planted copies.** We took known originals and made copies of each:
  - **images:** flipped, cropped by 5%, resized to half, brightened by 10%, and saved as JPEG at quality 70;
  - **files:** small edits, for files from the studio's public run records.

  A good finder pairs every copy with its original. The share it pairs is its **recall**.
- **Clean negatives.** Things that can't be duplicates:
  - for files, files of the same type from other runs, under other names;
  - for images, art from four other projects.

  Anything flagged among these is a **false positive**.
- **Views.** The studio's turntable project renders each object from many camera angles: 1,381 pairs of the same object
  at different angles. The studio's rule is that these are never duplicates, so any flag here is wrong too.

Rung 1 found that its negatives weren't clean: versions of one file across runs looked like copies. Rung 2 rebuilt them,
and rung 2b ran the text side again through the desk itself.

## Images: the angle problem

| Rule | Copies caught | Other-project images flagged | Views flagged |
|---|---|---|---|
| SigLIP2, cosine ≥ 0.95 (the desk's old default) | 95% | **20%** | **77%** |
| mirror-aware image hash at the old threshold (≥ 246 bits agreeing) | 71% | 0% | 0.6% |
| image hash only, mirror-aware, ≥ 230 of 256 bits agreeing | 81% | 0% | 4.9% |
| DINOv2, cosine ≥ 0.97 | 82% | 0% | 4.4% |
| **DINOv2 + mirror-aware hash, two signals** | **91%** | **0%** | 4.3% |

**SigLIP2** is the model the desk used for images. It's built to match pictures to words, so it puts two angles of one
ship close together: they show the same thing. That's right for search, but wrong for finding copies.

**DINOv2** is trained on images alone, and it's more literal about what it sees.

**The image hash** (dHash) compares 256 brightness steps between neighbouring pixels. It's cheap, needs no model, and
survives resizing and JPEG. It breaks on a mirror image: in rung 1, a flipped copy agreed with its original on 155 of 256 bits on average. Comparing each image with its
mirror as well brings flipped copies up to about 249.

**The two-signal rule** flags a pair when DINOv2 and the hash agree, or when DINOv2 alone is very sure:
`(cosine ≥ 0.94 and hash ≥ 212 bits) or cosine ≥ 0.985`.

That still flags 4.3% of views. No threshold removes them without losing real copies, but the records can. Each
turntable image's record names its object and its camera angle, so the desk now checks those first. Two angles of one
object are never paired, whatever the score. A second render of the *same* angle is still checked.

**A shortcut that didn't work.** A reviewer suggested working out the mirror's hash from the stored hash, with no image
to read: reverse each row of bits and invert it. That's exact only when no two neighbouring pixels are equal. We tested
it against real flips on 300 images:

| Project | Images | Median error (bits of 256) | Off by more than 10 bits |
|---|---|---|---|
| turntable renders | 45 | **112** | 100% |
| painted art | 255 | 6 | 18% |

The renders sit on flat backgrounds, where neighbours tie and the inversion turns every tie into a disagreement. The
desk will compute the mirror's hash from the flipped image.

## Text: read the model card first

For files, we compared four text embedding models. Rung 2 ran **EmbeddingGemma 2** without the setup its model card
asks for. It got the wrong task prefix, it loaded its image and audio encoders for text it didn't need, and it read
inputs in short pieces. So rung 2b ran every model through the desk itself, after the desk was rebuilt to follow each
model's card: a task prefix where the model wants one, text-only loading, and inputs split by the model's own tokenizer
into chunks up to the model's own limit: 8,000 tokens for EmbeddingGemma 2, 8,192 for the others.

| Pool | Model | Threshold that flags ≤ 1% of non-copies | Copies caught there |
|---|---|---|---|
| all 458 files, 100 copies | **bge-m3** | 0.98 | **94%** |
| | EmbeddingGemma 2 | 0.995 | 62% |
| | gte-modernbert | 0.99 | 52% |
| | Qwen3-Embedding 0.6B | none below 1.0 | – |
| scripts only, 17 copies | **EmbeddingGemma 2** | 0.935 | **100%** |

- **On scripts, EmbeddingGemma 2 separates cleanly.** Every copy scores at least 0.976 against its original, and every
  non-copy at most 0.931. The desk uses 0.95, inside that gap. It rests on only 17 copies, so it's marked provisional.
- **On logs and JSON, it can't.** Run files from different runs share templates, field names and timestamps, and
  EmbeddingGemma 2 scores look-alikes up to 0.992. **bge-m3** keeps the best balance, and stays the default for text.
- **Through the desk, bge-m3 got better:** 94% of copies at 0.98, up from 90% when it was run off-card.

## The memory surprise

The desk has a VRAM governor. Before loading a model, it checks the card has room for that model's registered figure
plus a 1 GiB margin, so two jobs can't push the shared card past its budget. Rung 2b measured each text model at its
longest input. Three of the four were registered far too low:

![dataset-desk text embedders: registered VRAM against the measured peak](/rnd/charts/desk-vram.svg)

The registered figures came from short inputs. At 8,192-token chunks, a model needs memory for the attention over the
whole chunk, and that grows with length. Until the registry is fixed, long-text runs are planned at their measured
peaks, with the card held by one job alone. The fix, registering the long-input peaks, is in the next build.

## How it was checked

Every step went past a second reviewer before it ran. Argon, an outside model, read the code and the plan, and the
Publisher seat checked the settled choices. Three of Argon's suggestions changed the plan:
- one threshold for text instead of two;
- the view check from records;
- comparing the desk's cached settings before reusing any vector.

Two other points came out differently once they were tested:
- **The mirror shortcut** failed, as shown above.
- **A batch-size claim was R&D's own error.** We told the reviewer the bge-m3 run used batches of 4; it used 8. The fix
  that rested on it was dropped, and the write-up was corrected.

## What changes, and what's still open

**Next build (D2):**
- DINOv2 with the mirror-aware hash for image duplicates;
- the view check from records;
- per-task text thresholds, at 0.95 for code and 0.98 for text;
- registry VRAM figures measured at long inputs.

Every threshold ships marked provisional, with the rung that measured it.

**Not settled yet:**
- **The two-signal rule misses 46 of the 500 planted image copies.** They probably have near-identical siblings in
  the same set, but nobody has checked: a person will look at them.
- **Code thresholds rest on 17 copies.**
- **Copied sections inside long files** aren't tested. The desk compares the average of a file's chunks, which
  dilutes a shared section.
- **Dataset items** (questions and answers written for training) need their own pool and rule. Templates make
  unrelated items look alike, and paraphrases make copies look different.

## Where the figures come from

- **Images and the first text pass (rung 2):** `experiments/dataset-desk/calibration/data/rung2.json`. The plain
  hash on flipped copies (rung 1) is `data/rung1-dhash.json`.
- **Text through the desk (rung 2b):** `data/rung2b.json`, the curves and picks, and `data/rung2b-runs.json`, each run's
  model revision, settings, peak VRAM and time.
- **The mirror test:** `data/mirror-dhash.json`.
- **The registered figures:** `data/registry-25d9cdd5.json`, read from
  [dataset-desk](https://github.com/mcp-tool-shop-org/dataset-desk) at commit `25d9cdd5`.
- **The chart** is built by `experiments/charts/make_charts.py`, and `manifest.json` pins each input's commit and
  sha256.
- **Not published:** the art and the text of the run files. These data files hold scores, counts and settings only.
