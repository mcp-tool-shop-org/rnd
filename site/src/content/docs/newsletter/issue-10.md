---
title: What the terms let you do with AI output
description: A licence check on a few Google tools turned into a question about every AI-written line in the studio. The answer depends on the use, not the provider, and it sent Stage 1's training data back to be rewritten by open models.
issue: 10
date: 2026-10-16
highlights:
  - "<strong>Ask per use, not per provider.</strong> Shipping an asset, training a model, evaluating one and running code are four different questions, and each provider answers them differently."
  - "<strong>Owning the output isn't permission for every use.</strong> xAI leaves Grok's output with you and also bars distilling it. Both clauses hold at once."
  - "<strong>Name the clause.</strong> A use is barred only by a clause you can point to. Code you own is ordinary software, whoever wrote it."
  - "<strong>Silence isn't a ban.</strong> Only a contract you agreed to, or a licence, can restrict what you do with output. Plain Apache-2.0 and MIT make no claim on outputs, so they're free. Look hard for the clauses that do restrict, and record the search."
  - "<strong>The account changes the terms.</strong> The same Kimi model is non-commercial in Moonshot's app and unrestricted through Ollama Cloud. Google's API terms are narrower than its consumer terms."
  - "<strong>Stage 1's training rows are being regenerated</strong> by licence-proven open models. The method, the gates, the lessons and the evaluation sets carry over."
---

**This is a reading of published terms, not legal advice.** Every clause below was re-read at its live page on
2026-10-16. The full record is in rnd, under
[`experiments/generated-content-terms/`](https://github.com/mcp-tool-shop-org/rnd/tree/main/experiments/generated-content-terms)
and [`experiments/stage1-regeneration/`](https://github.com/mcp-tool-shop-org/rnd/tree/main/experiments/stage1-regeneration).

## How it started

The studio has Google AI Ultra, which comes with Flow, Flow Music and Project Genie. Before anything they made
could ship, the maintainer asked for a licence check. Reading Google's terms raised a bigger question, because the
studio trains its own small models. Could AI-written text from any provider be used as training data?

The maintainer set the rule for answering it. **A use is allowed unless the provider's contract or licence
restricts it,** and the search for restrictions is documented: the page, the exact clause, and its date. Uses that
providers commonly ban (training on outputs, distillation, competing models) get that explicit check before anything
relies on them. A model's reading of the terms proves nothing, including the studio's own outside reviewer's.

The first version of the rule went further: it treated anything not expressly permitted as off limits. That made
silence a ban, which it isn't. Only a contract you agreed to, or a licence, can restrict a use. The rule was
reworded the same day, and the verdicts below follow the reworded version.

A second correction followed the next day. The studio had read Google's "related AI technology" at its widest, so it
covered even small pieces of pipeline code. The outside reviewer pointed out that the clause sits under "Don't abuse
our services", and that its purpose is stopping people distilling Gemini into a rival model. So the clause bars
training data and distillation, and code the studio owns is ordinary software whoever wrote it. A two-tier version
that made anything touching a model "strict" was tried the same day and withdrawn: it kept producing bars no clause
contained. The rule is now simply that a use is barred only by a clause you can name.

The rule earned its keep. The outside model's first pass got two things wrong:
- it said Claude's consumer terms bar all commercial use, when that clause covers evaluation access only;
- it said the Llama licence bars training non-Llama models, when Llama 3.3 permits it if the new model's name
  begins with "Llama".

Both were caught by re-reading the source.

## The four uses

| Use | Google (consumer) | xAI (Grok) | Anthropic (Claude) | Moonshot (Kimi app) |
|---|---|---|---|---|
| **Commercial assets** | Allowed. Flow Music grants "Commercial use rights" outright; for the rest, Google disclaims ownership and restricts nothing that applies | Allowed, with attribution ("Written with Grok") | Allowed: you own the outputs | Barred: non-commercial use only |
| **Training data** | Barred | Barred: no distilling outputs | Allowed for non-competing specialized classifiers and tools, **never as training targets** | Barred for a business: non-commercial use only |
| **Evaluation only** | Barred where it serves developing a model; allowed otherwise | Unclear: the AUP's "develop … machine learning models" clause | Allowed on the same reading | Barred for a business |
| **Code** | Allowed when no model trains on it and it builds no rival (the clause is read by its anti-distillation purpose) | Allowed for tooling that develops no model and doesn't compete, with attribution | Allowed for non-competing specialized tools | Barred for commercial use |

**The clauses behind the table:**
- **Google** (Terms of Service, effective 2026-07-30) bars "using AI-generated content from our services to develop
  machine learning models or related AI technology". It has no competition qualifier, and Antigravity's terms
  incorporate it. Google's Gemini API and Cloud terms are narrower: they bar only models or products that compete.
- **xAI** (consumer terms, last updated 2026-10-12): "you retain your ownership rights to the User Content", and
  using Output requires attribution under the Brand Guidelines. The Acceptable Use Policy (2026-08-14) separately
  bars "distilling model data or Outputs".
- **Anthropic's Help Center** (article 12326764, 2026-03-16): "You can use Claude's Outputs to train models that
  don't compete with Anthropic's own models." It bars general-purpose chatbots, models designed for open-ended text
  generation, and "Using Outputs as training targets for models". Anthropic's support channel, asked about this
  exact use, said it fits. That reply came from an AI support agent, so the article stays the proof.
- **Moonshot's Kimi app:** "you may only use Kimi in a non-commercial, personal research, and study manner."

## Open weights: read what the licence says about outputs

Running an open-weight model yourself removes the service's terms, but not the model's licence. Most licences
grant rights in the weights and say nothing about what the model writes.

| Licence or card | What it says about outputs | Verdict |
|---|---|---|
| **OpenMDW-1.1** (Nemotron 3, 3.5 Lightning, 3.5 Super-VL) | "does not impose any restrictions or obligations with respect to any use … of any outputs" | Proven |
| **Muse-Glimmer-30B** card | Its intended uses include "Synthetic data generation" for "downstream model development" | Proven |
| **DeepSeek-R1** (MIT) | "including, but not limited to, distillation for training other LLMs" | Proven |
| **Muse Model License** (Muse-Spark-816B) | Synthetic data is an intended use, but a model trained on its outputs is a "Derivative" that must carry the licence and display "Built with Muse Spark Open" | Proven, with conditions |
| **Llama 3.3** | Permits training on outputs if the new model's name begins with "Llama" | Proven, with a naming condition |
| **NVIDIA Open Model License** | "does not claim ownership" of outputs, and no restriction on them | Allowed |
| **Plain Apache-2.0 or MIT** (Qwen, Gemma 4, Granite, Kimi K3) | Nothing on outputs | Allowed: the licence makes no claim and no contract binds a local run. Check any model-specific use policy too (Gemma has one) |

On the last two rows, the Linux Foundation's OpenMDW launch post notes that Apache-2.0 and MIT were written for code
and are silent on generated outputs. OpenMDW-1.1 says outright that outputs are unrestricted. Silence and an
explicit grant reach the same place: nothing restricts the use.

**The route matters too.** The studio's Kimi seat turned out to run in the Zed editor through Ollama Cloud, not
Moonshot's app. Ollama's terms (May 2026) say "You retain ownership of content you create using our services", and
restrict only building products that compete with Ollama. The Kimi K3 and K2.6 licences are MIT-style. So the app's
non-commercial clause never applied to that code.

## What the studio found in its own work

An inventory traced every piece of text in the Stage 1 pipeline to whoever wrote it. Three findings stood out:
- **The training rows** were written by Kimi (the pilot), Grok (batches 2–8) and Antigravity (the 210 apply items).
  Grok's and Google's terms bar training on them.
- **The generator showed the writer finished Kimi and Grok rows as examples,** so even a clean model would have
  been prompted with barred text.
- **The "real-source" excerpts weren't human-written.** They came from the studio's own repos, and those repos were
  mostly written with Claude.

## What changed

- **All 810 training rows and 210 apply items are being regenerated** by licence-proven open models: Muse-Glimmer
  and Nemotron on Colab, and a larger Nemotron on a rented GPU if a pilot earns it. The writer and critic always
  come from different families.
- **The method carries over:** the lessons, the gates, the defect catalogue and the evaluation sets. Claude wrote
  those, and Anthropic's terms allow that use for a specialized verifier. No Claude text becomes a training target.
- **The code stays, whoever wrote it.** Under the two-tier rule, pipeline code that no model trains on is ordinary
  software. Three small Antigravity-written pieces had already been re-implemented under the earlier, stricter
  reading; they stay as they are. Grok's generator logic stays too, with its text replaced. The tooling Grok and Kimi
  wrote is credited in `CONTRIBUTORS.md` files that say "Written with Grok".
- **Provenance is now recorded at the source.** Every text-bearing template and pack in the generator gets a
  record of who wrote it, and the generator's own check refuses one without it. Seat commits carry a trailer naming
  the seat.

## If you're doing the same

1. **Ask per use.** Shipping, training, evaluating and code are separate questions.
2. **Read the use limits, not just ownership.** Acceptable-use policies are where the training bans live.
3. **Don't mistake silence for a ban, or a ban for silence.** Only a contract you agreed to, or a licence, can
   restrict a use. Find the clauses that do (training, distillation and competing-model bans), and record where you
   looked.
4. **Check which account you used.** Consumer, API and enterprise terms differ, and so do apps and hosts serving
   the same model.
5. **Re-read every clause yourself.** A model's summary of the terms, ours included, got things wrong.
6. **Record who wrote what when it's written.** An inventory after the fact needed two agents reading PR threads
   and commit trailers, and still left gaps.
7. **Mind the attribution clauses:** "Written with Grok", "Built with Muse Spark Open", and Llama's naming rule.
8. **Name the clause, or it's allowed.** Never read an undefined phrase at its widest just to be safe, and never
   add a tier or a filter the terms don't contain: that ratchet ends up banning a temperature monitor.
