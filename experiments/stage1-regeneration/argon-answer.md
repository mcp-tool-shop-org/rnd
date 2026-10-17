# Argon's answer, summarised (2026-10-16)

> **Superseded (2026-10-17).** Written under the proof rule ("not proven = don't use"), which the maintainer withdrew. The clause quotes stand; the "not proven" verdicts don't. Current verdicts: `experiments/generated-content-terms/README.md` and `licences/registry.json`.

Browser Argon's reply to the Publisher's consult brief on the regeneration, pasted by the maintainer. It's
**summarised here, not reproduced:** it quotes licence text at length. The clauses that count are the ones R&D
re-read, in [PLAN.md](PLAN.md) section 1.

## Argon's claims, and R&D's re-read

| Argon's claim | R&D's re-read (2026-10-16) |
|---|---|
| Muse-Spark-Open-816B-A42B is proven: its card lists synthetic data generation | **Confirmed, with conditions Argon didn't mention.** The Muse Model License makes a model trained on its outputs a "Derivative". A Derivative must carry the notice, the licence and the Usage Policy, and display "Built with Muse Spark Open". The repo is gated. |
| DeepSeek-R1 and R1-0528 are proven: MIT, "distillation for training other LLMs" | **Confirmed.** R1-0528's card words it differently: "supports commercial use and distillation". |
| Nemotron-3-Ultra-550B is proven: OpenMDW-1.1 | **Confirmed** (the governing-terms line; released 2026-06-04) |
| Nemotron-3.5-Super-VL-120B is proven: OpenMDW-1.1 | **Confirmed** (released 2026-10-15) |
| R1-Distill-Qwen-32B is proven by the R1 clause | **Confirmed on its own card.** Its Qwen2.5-32B base is plain Apache-2.0, so it rests on DeepSeek's grant alone. |
| Nemotron-4-340B and Nemotron-3-Super (Dec 2025) are not proven: NVIDIA OML | Agreed. |
| The Llama licence bars training non-Llama models | **Wrong.** Llama 3.3's Section 1.b.i permits it, on condition that the model's name begins with "Llama". The exclusion stands on that condition. |
| Apache-2.0: no documentation settles output use | Agreed. It stays not proven. |

## Argon's plan findings, and R&D's rulings

1. **The A100 has no FP8; use llama.cpp Q8_0 on Colab** (blocking). **Accepted, and widened.** llama.cpp, built
   with CUDA 13.4, serves on every host, pods included, because vLLM and SGLang have no 13.4 build (the
   maintainer's 13.4 rule).
2. **role-set write must batch, or the run takes about 20 A100-hours** (blocking). **Reframed.** role-set already
   runs slots concurrently (`--concurrency`; pilot 2 ran at 8). The real blocker is the inline critic call per
   slot, which forces the writer and critic onto one card at the same time. The fix is a wave mode, which also
   enables a pod writer with a Colab critic.
3. **The provenance inventory must cover the prompt templates, few-shots, lesson drafts and puzzle generators**
   (blocking). **Accepted.**
4. **Four deterministic guards before the pilot** (blocking): domain and frame table, solve-first puzzles,
   cross-batch exclusion state, inline freeze checks. **Accepted.** The inventory records which ones role-set
   already has.
5. **The pilot spans kinds A–E plus apply twins** (non-blocking). **Accepted.**

**Argon's control suggestion** (16 items written by the maintainer, plus a slot-matched tournament) is advisory.
J1's control is role-set itself (local-builders amendment A). The maintainer's set stays an option.

**Argon's tiers and costs** were estimates. The live offers and the sizing against the RunPod balance are in
PLAN.md section 5.
