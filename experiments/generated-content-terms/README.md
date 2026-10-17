# Generated content: what the providers' terms allow the studio to do

**Question (2026-10-16, the maintainer).** Check the licence terms for the Google AI Ultra tools (Flow, Flow Music,
Project Genie) before anything they generate ships. The check turned up a wider question: whether the studio may
use any provider's AI output as **training data** for its own models.

**This is a reading of published terms, not legal advice.** The terms are relied on, so the standing rules call
for one different-family check ([argon-brief.md](argon-brief.md)), and any decision with commercial or legal weight
is the maintainer's.

**The rule for using generated content (the maintainer's decision, 2026-10-16, revised the same day):**
- **A use is allowed unless the provider's contract or licence restricts it.** The restriction search is
  documented: the pages, clauses and dates checked (`licences/registry.json`).
- **Commonly banned uses get the explicit clause check before they're relied on:** training on outputs,
  distillation, competing models.
- **A model's say-so isn't proof,** including Argon's, R&D's or any model's.
- **R&D re-reads every cited clause at its source** before anything relies on it.

**Split by what the output touches (the maintainer's decision, 2026-10-17, on Argon's analysis):**
- **Strict: explicit permission needed** for anything that shapes model weights or benchmark scores. That covers
  training data, evaluation and apply items, base models, and canon or images that train a style model.
- **The plain reading for code:** code the studio owns, that no model trains on and that builds no rival to the
  provider, is ordinary software, whoever wrote it. Google's "related AI technology" is read by its purpose
  (stopping extraction and distillation into a rival model), not at its widest. Antigravity-written AI tooling is
  allowed. An undefined phrase is never read at its widest to bar ordinary work.
- **Claude in the strict tier:** Anthropic's Help Center (12326764) is the explicit permission. Claude-written text
  may be used as training inputs, evaluation items and prompts for the non-competing specialized verifier, **never
  as training targets.** Gemini (including Antigravity) and Grok output stays out of training data and evaluation
  items entirely, by their explicit clauses.
- The split follows Argon's analysis of 2026-10-17, adapted by R&D and ruled by the maintainer.

*Revised the same day.* The first wording ("allowed only when the provider's documentation proves it; a missing
restriction proves nothing") counted silence as a bar. The maintainer judged that too strict. Only a contract the
studio agreed to, or copyright in the output, can restrict a use. A licence that makes no claim on outputs, or a
signed contract that is silent, leaves the use free. The verdicts below that rested on silence were revised
(`licences/registry.json`). The ones that rest on explicit clauses (Google's ML clause, xAI's distillation ban,
Anthropic's training-target rule, the Kimi app's non-commercial clause) stand.

**Status (2026-10-16): Google checked by R&D at the primary source; Argon's blanket check is back, and R&D
has re-read every load-bearing clause (below).**

## Google: Flow, Flow Music, Project Genie (consumer Google AI Ultra)

Read 2026-10-16 from Google's own pages.

| Point | What the terms say | Source |
|---|---|---|
| Which terms govern | The Google Terms of Service (effective 30 July 2026), plus any service-specific additional terms, which "will govern for that service" if they conflict. The Flow help page says "The Terms of Service govern how these tools may be used". | [Google ToS](https://policies.google.com/terms); [Flow help](https://support.google.com/flow/answer/16353333?hl=en) |
| Ownership | "Some of our services allow you to generate original content. Google won't claim ownership over that content." | Google ToS; Flow help |
| Commercial use, Flow Music | Google AI Ultra includes Flow Music's Member plan, whose listed benefits include "Commercial use rights." | [Google AI Ultra benefits](https://support.google.com/googleone/answer/16286513?hl=en) |
| Commercial use, Flow and Genie | No separate grant. They're governed by the ToS, which claims no ownership and places no commercial-use bar on generated content. Project Genie is "an experimental research prototype in Google Labs", downloadable as videos, with no terms of its own found. | Google ToS; [Project Genie post](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/project-genie/) |
| **Training on outputs** | Listed as abuse, **with no qualifier**: "using AI-generated content from our services to develop machine learning models or related AI technology". | Google ToS, "Don't abuse our services" |
| Other limits | Don't mislead people "into thinking that generative AI content was created by a human". The Generative AI Prohibited Use Policy applies. Outputs carry SynthID watermarks, and a visible watermark can be toggled in Flow. | Google ToS; Flow help |

**Antigravity** (where Argon builds): its Additional Terms incorporate the Google ToS as the "Universal Terms", and
add nothing on output use, so the clause above applies to consumer Antigravity use. Accounts used through Gemini
Enterprise or Workspace fall under their administrator's terms instead.
([Antigravity terms](https://antigravity.google/terms))

### What this means for the studio's uses of the Google tools

Under the rule above:
- **Flow Music, commercial use: proven.** Ultra's Flow Music Member plan lists "Commercial use rights" on Google's
  own page, so music beds and game audio may ship.
- **Flow (video, images) and Project Genie, commercial use: not proven, so don't use.**
  - Google claims no ownership, and no commercial-use bar was found, but that's inference from a missing
    restriction, and the rule excludes it.
  - They stay internal until Google's own documentation grants commercial use explicitly.
  - Argon's check is asked to find such a clause.
- **Caveats on anything that ships:**
  - copyright in AI output depends on the country, so "Google won't claim it" isn't "you own an enforceable
    copyright";
  - similar outputs may be given to others;
  - AI-generated work mustn't be presented as human-made.
- **Game art** stays canon-bound in any case.
- **Training data: not allowed under the plain text.** No Flow, Flow Music, Genie or Gemini output may become
  training data for a studio model: not a style LoRA, a dataset, or SFT or STaR rows.

## The wider question: AI-written training data

Stage 1's frozen training data (aspire-si `FROZEN.md` `e7b69464`) was written by:
- the Grok seats (xAI): batches through 8;
- Kimi (Moonshot): a handoff, per the 2026-10-10 handoffs;
- Antigravity Argon (Google): the 210 apply items, whose prompts STaR carries into training rows.

| Provider | Restriction on using outputs to build models | Checked how |
|---|---|---|
| Google (consumer) | Unqualified: "to develop machine learning models or related AI technology" | **Primary**, above |
| xAI, Grok (consumer) | Using the service or output to develop models or services that compete with xAI has been barred since early 2025. Later versions add a ban on distillation and, per a secondary report, "direct or indirect" competitors. | **Archived primary pages** (x.ai `previous-*` versions); the live page refused automated fetches; one secondary report |
| Moonshot, Kimi (consumer) | Bars using Kimi to develop, train or improve models "in direct or indirect competition". API and Business terms differ. | Search excerpts of kimi.com agreements; **not read in full** |
| Anthropic (Claude, consumer plan) | Not checked here. It belongs in the blanket check. | — |

**What isn't settled:**
- **Which product terms applied:** the Grok seats ran on a "Grok Build" subscription, and which Kimi product was
  used is unknown.
- **Whether "compete" covers the studio's models,** a small local verifier and role models.
- **Whether evaluation-only use** (the local-builders J1 control) counts as "developing" a model.
- **Whether Google's "related AI technology"** reaches tooling code Argon writes. It's read narrowly here as
  model-building, not coding assistance in general.

## Argon's blanket check, re-read by R&D (2026-10-16)

Argon's answer is summarised in [argon-answer.md](argon-answer.md). Under the proof rule, R&D re-read each
load-bearing clause at its live URL. A claim counts only where R&D's re-read confirms it.

| Provider | Claim | R&D's re-read | Clause (as read at the URL) |
|---|---|---|---|
| Google | Training on outputs is barred | **confirmed** (earlier) | ToS: "using AI-generated content from our services to develop machine learning models or related AI technology" |
| Google | Flow and Genie commercial use isn't proven; Flow Music's is proven | **confirmed.** The Labs FAQ answers the commercial question only by pointing to the ToS's non-ownership line | Ultra benefits: "Commercial use rights" (Flow Music only) |
| xAI | Training on Grok output is barred, competing or not | **confirmed** (AUP, effective 14 August 2026, applies to "consumers, developers and businesses") | "Scraping, harvesting or reselling any Input or Output, or distilling model data or Outputs" and "Using the Service or any Output to develop (or assist anyone in developing) machine learning models or any products or services that compete with SpaceXSI, whether directly or indirectly" |
| xAI | Enterprise terms bar training any AI system on Output | **confirmed** | "use any Output to train any foundation models, large language models, or other artificial intelligence systems except as may be expressly permitted in an Order Form" |
| Moonshot | The Kimi consumer app is non-commercial, personal research only | **confirmed** (effective 5 January 2024) | "you may only use Kimi in a non-commercial, personal research, and study manner" |
| Anthropic | Training on Claude output needs authorization | **confirmed** (Usage Policy, effective 12 November 2026) | "Use outputs to train an AI model (e.g., "model scraping" or "model distillation") without prior authorization from Anthropic" |
| Anthropic | Outputs as training targets are prohibited | **confirmed** (Help Center, 16 March 2026) | prohibited uses include "Using Outputs as training targets for models" |
| Anthropic | **"Consumer (Pro/Max) bars all commercial use"** | **wrong.** The consumer terms (effective 8 October 2025) say "Use of our Services for evaluation purposes are for your personal, non-commercial use only", which applies to evaluation access only. The terms do bar using the Services "to develop any products or services that compete with our Services", including to "develop or train any artificial intelligence or machine learning algorithms or models". | consumer terms, sections 2 and 3 |

**What the confirmed clauses mean under the proof rule:**
- **(Superseded for Anthropic, 2026-10-16:** Help Center 12326764 allows Claude outputs to train non-competing specialized tools, never as targets. The current verdicts for every page are in [`licences/registry.json`](../../licences/registry.json).)
- **Training data, U2, is barred for all four providers.** No AI-written text from Google, xAI, Moonshot or
  Anthropic may train a studio model. Stage 1's frozen training set (written by Grok and Kimi) and its apply items
  (written by Argon) can't train the student as things stand.
- **Evaluation only, U3, isn't proven for any provider.** That includes the local-builders J1 control, which is
  Argon's first-round items. That design needs a control from a documented-permissive source.
- **Commercial assets, U1, are proven only for Flow Music and Grok.** Grok's: the xAI FAQ, per Argon, still to be
  re-read by R&D before any Grok-made asset ships.
- **Code, U4:** Argon reads Google's "related AI technology" as reaching AI-infrastructure code written in
  Antigravity, and Google publishes no narrowing guidance. Under the rule that's not proven, which bears on
  Argon-built AI tooling (the governor, interlock work). It's the maintainer's call. R&D's earlier narrow reading
  was an inference, and the rule excludes inferences.
- **Publishing:** Argon flags that public repos carrying provider-written training data, with training scripts,
  may also count as "assisting" others under xAI's and Anthropic's clauses.
- **Antigravity, Section 6** (re-read 2026-10-16): "Using third party software, tools, or services to access the
  Service (e.g. using OpenClaw with Antigravity OAuth) is a breach of this Agreement." It's listed with "using the
  Service in connection with products not provided by us", and may lead to suspension of the Antigravity and Gemini
  CLI accounts. The Publisher's bridge is clear (the Gemini app by hand, the Workspace Drive connector, Google's own
  Colab CLI). The boundary: no script, agent or third-party tool ever reaches Antigravity or Gemini CLI through the
  maintainer's OAuth.
- **What escapes:** data generated locally by open-weight models whose licences put no restriction on outputs.
  Each model's licence still needs its own documented check before use.

## Recommendation (for the maintainer)

1. **Stage 1 round 1:** under the rule above, the Grok-, Kimi- and Gemini-written data trains a model only if each
   provider's documentation proves that use allowed.
   - **Barred, confirmed for all four providers:** Google's text, xAI's AUP and Enterprise terms, and Anthropic's
     Usage Policy each bar it, and Kimi's consumer terms prove no such use. So Stage 1's Grok- and Kimi-written
     training set, and the Argon-written apply items, can't train the student.
   - **The path:** regenerate the data from a source whose terms are documented to allow training: an open-weight
     local model with its licence checked (the local-builders study is the path), or written authorization from a
     provider. Evaluation-only isn't proven for any provider either.
   - The data is frozen and the round hasn't started, so nothing is lost.
2. **The Google creative tools:**
   - Flow Music is proven for commercial assets.
   - Flow and Genie are internal only until proven.
   - None of them is for training.
3. **Argon's blanket check** ([argon-brief.md](argon-brief.md)) must prove each "allowed" with the provider's
   documentation, or answer "not proven: don't use". R&D re-reads every clause it cites.
