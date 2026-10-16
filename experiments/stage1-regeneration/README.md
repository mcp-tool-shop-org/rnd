# Stage 1 data regeneration

**Question (2026-10-16, the maintainer).** Regenerate Stage 1's training data with licence-proven models, since the
frozen set was written by providers whose terms don't prove training use (`experiments/generated-content-terms`).
Use the biggest proven models, on Colab where it can, and on RunPod only for the roles that need bigger multi-card
models.

**Status (2026-10-16):** the plan is drafted and revised after Argon's consult ([PLAN.md](PLAN.md)). R&D has
re-read every licence clause Argon cited ([argon-answer.md](argon-answer.md)). The provenance inventory is done
([PROVENANCE.md](PROVENANCE.md)), and the role-set build spec is drafted ([BUILD-SPEC.md](BUILD-SPEC.md)). **Nothing has run.**

**In short:**
- **Seven models are proven,** biggest first:
  - Muse-Spark-816B, with licence conditions;
  - DeepSeek-R1 and R1-0528;
  - Nemotron-3-Ultra-550B;
  - Nemotron-3.5-Super-VL-120B;
  - R1-Distill-Qwen-32B;
  - Muse-Glimmer-30B;
  - Nemotron-3.5-Lightning-30B.
- **Plain Apache-2.0 models stay not proven.** No documentation settles them.
- **The writer gets the biggest model.** The critic's text never enters a row, so it stays on Colab.
- **role-set gets a wave mode** (write, then critique, then rewrite), so the writer and critic need never share a
  card or a host. It also gets deterministic variety guards before the pilot.
- **Money:** the frontier tier is out of reach at today's RunPod balance. A big-writer pilot fits; the full
  big-writer run needs a top-up, which is the maintainer's call after the pilot.

**Related:** `experiments/local-builders` (J1 is the writer selection, amendment A), `instruments/colab.md`.
