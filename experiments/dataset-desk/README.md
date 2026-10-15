# The dataset desk: the design record

One desk for making and reviewing the studio's visual datasets: the `style-dataset-lab` sets that train its style
LoRAs, and the query pools of the EmbeddingGemma 2 multimodal benchmark.

**The code lives in [mcp-tool-shop-org/dataset-desk](https://github.com/mcp-tool-shop-org/dataset-desk)** (public,
v0.1.0, 2026-10-15). It left this folder after Argon's pass 3 and its follow-up. The repo's first commit is that code,
laid out as a package. This folder keeps what belongs in the library:

| file | what it is |
|---|---|
| [design.md](design.md) | the design: research grounding, the C0–C3 calibrations, the description gate's contract shared with [design-multimodal.md](../embeddinggemma-2/design-multimodal.md), the `author_kind` importer contract, and the pass 1–3 dispositions |
| [argon-pass-2-brief.md](argon-pass-2-brief.md), [argon-pass-2-addendum.md](argon-pass-2-addendum.md) | pass 2's brief and addendum |
| [argon-pass-3-brief.md](argon-pass-3-brief.md), [argon-pass-3-addendum.md](argon-pass-3-addendum.md) | pass 3: revision 3's acceptance tests, the blind worksheet, the drafter, the arm-model guard |
| [argon-pass-3-followup-brief.md](argon-pass-3-followup-brief.md) | the follow-up: the drafter on plain-sight's own pin, offline |

**Status, 2026-10-15:**
- **Reviewed:** three Argon passes and a follow-up, each checked by R&D against the code.
- **Tested:** 142 offline tests at 96% line coverage, in the repo's CI (floor 90).
- **Not run:** nothing has run on real art or a real model. C0 (a 20-image CPU smoke run) comes first, under the rig's
  preflight. Then comes the desk stage on the four benchmark projects, before that experiment's manifest is frozen.
