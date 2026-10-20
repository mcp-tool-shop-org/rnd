# Dataset desk calibration: rungs 2 and 2b

These are the measurements behind the desk's duplicate thresholds, run on the RTX 5090 on 2026-10-19 and 2026-10-20.
[Newsletter issue 16](../../../site/src/content/docs/newsletter/issue-16.md) tells the story. This folder holds the
numbers only. The art and the text of the run files aren't published.

| File | What it holds |
|---|---|
| `data/rung2.json` | Rung 2: text picks for bge-m3 and EmbeddingGemma 2 run off-card, and image rules (SigLIP2, DINOv2, the mirror-aware dHash) on 500 planted copies, 986 other-project images and 1,381 same-object view pairs. Also each model's revision, peak VRAM and time. |
| `data/rung2b.json` | Rung 2b: text curves and picks for four models run through dataset-desk 25d9cdd5, all files and scripts only, with EmbeddingGemma 2 also at 512 and 256 dimensions. |
| `data/rung2b-runs.json` | Each rung 2b run: model revision, role, dimension, dtype, `max_tokens`, peak VRAM, seconds, and files over one chunk. |
| `data/mirror-dhash.json` | How far the bit-reversal shortcut for a mirror's dHash is from the real flipped image's dHash, on 300 images. |
| `data/registry-25d9cdd5.json` | The VRAM figures registered in dataset-desk's `registry.py` at 25d9cdd5. |

**Method, in short:**
- **Positives:** planted copies of known originals.
  - images: flip, 5% crop, half-size, +10% brightness, JPEG at quality 70;
  - text: 100 edited copies of public rnd-data run files.
- **Hard negatives:** files of the same type from another run under another name, and images from four other
  projects.
- **Recall** is the share of copies at or above a threshold. **FP** is the share of copies whose nearest hard
  negative is also at or above it.
- In rung 2b, every model ran through the desk's own `text_index`, with text-only EmbeddingGemma 2 and token-counted
  chunks (8,000 tokens for EmbeddingGemma 2, 8,192 for the others, at most 8 per file). bf16, at each embedder's
  default batch (4 for EmbeddingGemma 2, 8 for the others).

The run scripts are R&D's bench scripts. They read the studio's art from its local projects, so they aren't
reproducible from this repo alone.

**Status:** every threshold here is provisional. The code thresholds rest on 17 planted copies. Dataset items and
copied sections inside long files aren't measured.
