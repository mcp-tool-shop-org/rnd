# Argon's answer on pipeline code, summarised (2026-10-16)

> **Superseded (2026-10-17).** Written under the proof rule ("not proven = don't use"), which the maintainer withdrew. The clause quotes stand; the "not proven" verdicts don't. Current verdicts: `experiments/generated-content-terms/README.md` and `licences/registry.json`.

Browser Argon's reply to [the brief](argon-brief-pipeline-code.md), pasted by the maintainer. It's summarised here,
not reproduced. The clauses that count are the ones R&D re-read, recorded in `licences/registry.json`.

## Verdict

**Barred on the literal consumer text, so not proven: don't use.** The verdict rests on one clause, in the Google
Terms of Service (effective 2026-07-30), which Antigravity's terms §1 incorporate: "using AI-generated content from
our services to develop machine learning models or related AI technology".

## Argon's points, and R&D's re-read

| Point | Re-read |
|---|---|
| No consumer Google document narrows the clause to training on outputs or to competing models. The strongest case for "allowed" is its placement under "Don't abuse our services", which suggests an anti-distillation purpose. That's an inference, not a grant | Agreed. The clause itself was confirmed earlier (`google-tos`) |
| The verb "to develop" with "machine learning models or related AI technology" is broader than Anthropic's "train" or xAI's "use any Output to train". Code is "AI-generated content", and nothing restricts the phrase to prose training data | Agreed on the text |
| No definition of "related AI technology" exists | Agreed |
| Antigravity's terms add nothing: §1 makes the Google ToS govern, and §3 makes the user responsible for agent actions | Consistent with R&D's reading of `antigravity-terms` |
| **Gemini API terms** (updated 2026-04-28): "You may not use the Services to develop models that compete with the Services" | **Confirmed live** (`gemini-api-terms`) |
| **Google Cloud Service Specific Terms** (last modified 2026-10-12): "use an AI/ML Service or Generated Output to develop a similar or competing product or service" | **Confirmed live** (`google-cloud-service-terms`) |
| The API and Cloud terms are prospective: they don't cover code already written under the consumer plan | Agreed: both scope themselves to output of their own services |

## What it means

- **Argon's three pipeline pieces** (aspire-si #144 and #145, role-set #55) are re-implemented clean-room from the
  written briefs that specified them.
- **Future Google-written pipeline code is possible** only through the Gemini API or Vertex AI, whose terms bar
  only competing models. That's a paid route, for the maintainer's decision. The consumer Ultra plan stays off
  AI-pipeline work.
- **Argon notes that datasets not used for ML are fine:** for example game dialogue, lore tables and catalogues.
  **One studio caveat:** canon that feeds the style-trained diffusion model is ML training data. Gemini- or
  Flow-written canon, or images used to train a style model or LoRA, fall under the same bar.
