---
id: 2026-10-07-open-jev-style-decision-models
title: Open Jev-style decision models — the landscape, checked against primary sources
date: 2026-10-07
kind: tool
relevance: watch
fields: [machine-learning, local-llm]
tags: [jev, decision-model, kev, laya, semif, nimble, von, nanojev, jevlike, openjev, modernbert]
---

## Summary

Several open projects copy the shape of TypeSafe's hosted Jev: one forward pass
returns a probability for each option, with no text generation. Two AI-search
summaries (a pasted list, then Gemini) named seven of them. A research agent then
checked each name against its GitHub README, its Hugging Face card or the GitHub
API on 2026-10-07. The summaries got most attributions right, but they mixed up the
projects called "OpenJev" and repeated some latency and benchmark figures the
primary sources do not support.

For the studio, only two are worth a local test against hosted Jev on a yes/no
task: Kev and Bespoke Nimble. SemIf's raw logits make a no-training baseline.

## Key points

- **"OpenJev" names at least four unrelated projects:**

  | name | what it is | licence |
  |---|---|---|
  | `openjev/openjev` (HF, Loop AI) | 27B on a Qwen base, GGUFs, server `loopai-hq/openjev-server`; the one tested in [[2026-10-07-openjev-and-open-jev-alternatives]] | CC BY-NC 4.0 |
  | `razorback16/openjev` (GitHub) | an API server around NVIDIA DiffusionGemma 26B-A4B (NVFP4, 24 GB+), also fronting Laya and others; no model of its own | Apache-2.0 |
  | `TheoLeeCJ/SemIf-OpenJev` | renamed from OpenJev to SemIf; reads logits from a frozen causal model | MIT |
  | `AlexWortega/openjev` (HF) | an NLI cross-encoder; cites SemIf only as a baseline | MIT |

- **The seven, by the primary source:**

  | project | what it is | size, base | licence | fits a 5090 |
  |---|---|---|---|---|
  | Kev (`jaredpalmer/kev`) | adapters plus a pointer head; serves `/v1/systemone`; fitted temperature | 0.8B / 4B / 9B adapters on Qwen3.5 Base; 27B full fine-tune of Qwen3.8-27B | Apache-2.0 | 4B, 9B (~17 GB) yes; 27B no (~66 GB) |
  | Bespoke Nimble (`bespokelabsai/nimble`) | rank-16 LoRA, open recipe, 2,676 train / 324 eval examples | Qwen3.5-9B | Apache-2.0 | yes (~18 GB) |
  | SemIf (`TheoLeeCJ/SemIf-OpenJev`) | code only: direct logits from a frozen model, user-side calibration | Qwen3.5-4B (GGUF Q4_K_M 3 GB); EXL3 27B bridge | MIT | yes |
  | Laya (`NandhaKishorM/laya`, HF `convaiinnovations/laya`) | encoder plus head; choice / noul / score; `/v1/systemone` server | 421M ModernBERT-large (322M mmBERT multilingual) | Apache-2.0 | yes |
  | Von (`wfzyx/von`) | encoder plus option-marker head, English | 395M ModernBERT-large | Apache-2.0 | yes |
  | NanoJev (`TianyuCodings/NanoJev`, HF `C-Tianyu/NanoJev`) | action distributions for games (Maze, Snake, ViZDoom), not text decisions | 0.6B, Qwen3-0.6B | MIT on GitHub | yes |
  | jevlike (`vinnylarouge/jevlike`) | research starter, option-attention head, no weights | — | MIT | n/a |

- **Evaluation quality varies a lot:**
  - **Kev** has the most honest evaluation: "new sources" it never trained on, test
    sets read once per release, and an admission that Jev's training data is
    unknown. Kev-27B scores 0.851 dev / 0.889 test vs Jev 0.857 (dev only);
    Kev-9B 0.820 / 0.852; held-out index 52.3 vs 54.0.
  - **Nimble** reports about 90% agreement with Jev on 324 held-out examples. The
    exact metric was not confirmed.
  - **Laya**'s Jev comparison uses Jev numbers it never measured. Its fine-tuned
    typed-decisions 0.766 vs 0.727 has no committed result file. The base checkpoint
    scores 0.362, below the 0.461 majority rate, and Jev wins clearly past about
    20 options (Banking77 0.425 vs 0.870).
  - **SemIf** scores only on its own fixtures. Its 0.845 modal agreement against
    Jev's 0.883 on a 102-row subset is the "0.845 vs 0.883" figure that secondary
    coverage pinned on "OpenJev".
  - **Von** ranks below Verdict on its own sealed JevBench split (11.3 vs 17.9).
- **Training on Jev outputs:** Kev and Nimble both state they did not distill from
  Jev, and none of the seven claims it. TypeSafe's Terms of Use and Acceptable Use
  Policy have no clause against training on outputs. The Master Customer Agreement
  was not seen. (autotrust/JEV-27B, which did distill, is covered in the OpenJev entry.)
- **Stars:** Laya's repo shows 31,415 stars (created 2026-09-18). The "19,301 stars"
  in a Medium headline matches an earlier pinggy listing. The count is real as an API
  figure; whether it is organic is unknown.

## Studio relevance

sense-si and ai-jam-sessions want a free local stand-in for hosted Jev. The local
test of `openjev/openjev` showed the decision model is not the bottleneck on the
phrase-clean question: neither model beat the base rate
([[2026-10-07-openjev-and-open-jev-alternatives]]). So a new model is worth trying
only for cost or speed, or for a question where Jev itself does well.

If that need arises, the order is:

1. **Kev-9B**, plus Kev-4B as a cheap pair: Apache-2.0, fits the 5090, and the
   only held-out evaluation near Jev.
2. **Bespoke-Nimble-9B**, then **SemIf** on Qwen3.5-4B as a no-training baseline.
3. **Laya** only for latency: it is cheap to run, but its base is near chance.

Skip Von, NanoJev and jevlike for text decisions. Kev and Nimble are Apache-2.0,
which removes the non-commercial limit on `openjev/openjev`.

AI-search summaries in this area mix up the same-named projects. Gemini's "SemIf is
not OpenJev" was wrong, and the first summary's "SemIf (OpenJev)" pointed at the
wrong repo. Always resolve by GitHub or Hugging Face handle.

## Claims

- [verified] "OpenJev" names at least four unrelated projects: openjev/openjev (Loop AI, CC BY-NC), razorback16/openjev (a DiffusionGemma server), TheoLeeCJ/SemIf-OpenJev (renamed to SemIf) and AlexWortega/openjev (an NLI cross-encoder). (via: research agent reading each GitHub README / HF card, 2026-10-07)
- [verified] Kev ships 0.8B/4B/9B adapters with a pointer head on Qwen3.5 Base and a full-weight 27B on Qwen3.8-27B, serves /v1/systemone, is Apache-2.0, and states no Jev outputs were used for training. (via: jaredpalmer/kev README and HF cards, read by research agent 2026-10-07)
- [verified] Laya is a 421M ModernBERT-large model from Convai Innovations, Apache-2.0, at about 33–40 ms per decision on a T4 or Apple MPS. (via: NandhaKishorM/laya README, read by research agent 2026-10-07)
- [wrong] Laya runs under 10 ms on an M5 Max. (via: Laya README gives Apple MPS about 33 ms, read by research agent 2026-10-07; claim came from Gemini)
- [wrong] SemIf is a separate project from OpenJev. (via: TheoLeeCJ/SemIf-OpenJev README, renamed from OpenJev, read by research agent 2026-10-07; claim came from Gemini)
- [unverified] Kev-27B scores 0.851 dev / 0.889 test against Jev's 0.857 (dev) on sources it never trained on (self-reported).
- [unverified] Bespoke-Nimble-9B matches about 90% of Jev's answers on 324 held-out examples (self-reported; exact metric not confirmed).
- [unverified] Laya's typed-decisions checkpoint scores 0.766 against Jev's 0.727 (self-reported, no committed result file; Jev figure not measured by the authors).
- [verified] TypeSafe's Terms of Use and Acceptable Use Policy contain no clause against training on Jev outputs; the Master Customer Agreement was not checked. (via: research agent reading TypeSafe's published terms, 2026-10-07)

## Sources

- [primary] https://github.com/jaredpalmer/kev — Kev (Jared Palmer)
- [primary] https://huggingface.co/jaredpalmer/kev-4b — Kev-4B card
- [primary] https://github.com/bespokelabsai/nimble — Bespoke Nimble
- [primary] https://huggingface.co/bespokelabs/Bespoke-Nimble-9B — Bespoke-Nimble-9B card
- [primary] https://github.com/TheoLeeCJ/SemIf-OpenJev — SemIf (formerly OpenJev)
- [primary] https://github.com/NandhaKishorM/laya — Laya (Convai Innovations)
- [primary] https://huggingface.co/convaiinnovations/laya — Laya card
- [primary] https://github.com/wfzyx/von — Von
- [primary] https://github.com/TianyuCodings/NanoJev — NanoJev
- [primary] https://github.com/vinnylarouge/jevlike — jevlike
- [primary] https://github.com/razorback16/openjev — razorback16/openjev (DiffusionGemma server)
- [primary] https://github.com/loopai-hq/openjev-server — Loop AI's OpenJev server
- [aggregator] https://pinggy.io/blog/best_open_source_jev_alternatives_self_hosted_decision_models/ — used only to find links
- [aggregator] https://www.latent.space/p/ainews-here-are-6-clones-of-jev-in — used only to find links
- [user] AI-search summary and a Gemini summary pasted by the Director, 2026-10-07
