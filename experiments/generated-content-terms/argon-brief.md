# Argon consult: what AI providers' terms allow the studio to do with generated content (2026-10-16)

> **Superseded (2026-10-17).** Written under the proof rule ("not proven = don't use"), which the maintainer withdrew. The clause quotes stand; the "not proven" verdicts don't. Current verdicts: `experiments/generated-content-terms/README.md` and `licences/registry.json`.

**From:** R&D, for Browser Argon. **Kind:** a consult on published terms. It's a different-family check of
licence terms that will be relied on. No bundle: R&D's reading so far is in `README.md` in this folder.

**Answer format:**
- `## 2026-10-16 · rnd · generated-content terms · experiments/generated-content-terms`
- then a table per provider: rows are the four uses below; the columns are **allowed / barred / unclear**, the
  **exact quoted clause** (short), the **URL of the live page**, and its **effective date**;
- then "what R&D got wrong", and anything we didn't ask but should have.

Mark each answer `checked` (you read the live primary page) or `unsure`. Quote the clause, never paraphrase it.

**Burden of proof** (the maintainer's rule, 2026-10-16): **a use counts as allowed only when you prove it from the
provider's own documentation.**

**What counts as proof:**
- the URL of the provider's live terms, policy or official help page;
- the **exact clause quoted**;
- the page's effective or last-updated date.

**What doesn't count:** secondary sources (blogs, news, forums, reseller pages), model knowledge, inference from a
missing restriction, and "probably fine".

Any use you can't prove allowed this way must be answered **"not proven: don't use"**, even if you think it's
likely allowed. If documents conflict, quote both. The more restrictive one stands until the provider's own text
resolves it. R&D re-reads every quoted clause at its URL before anything relies on it.

## The studio's four uses

- **U1. Commercial assets:** store art, trailers, music beds and game audio in a sold game or public page.
- **U2. Training data:** AI-written text used to train the studio's own models. That covers SFT rows, and STaR
  rows whose prompts were AI-written and whose answers are the student's. The student is a small local verifier
  (Qwen3-8B with LoRA).
- **U3. Evaluation only:** AI-written items used as a test set or as a control to compare local models against.
  Never trained on.
- **U4. Code:** code an AI agent wrote for the studio's tools, some of which are AI infrastructure (a model
  router, a GPU safety governor).

## Providers and products

1. **Google, consumer (Google AI Ultra):** Gemini app (Browser Argon), Antigravity (Argon builds), Flow, Flow
   Music, Project Genie. **R&D's reading:**
   - the Google ToS (effective 2026-07-30) bars "using AI-generated content from our services to develop machine
     learning models or related AI technology", unqualified;
   - Google claims no ownership of outputs;
   - Flow Music's Member plan on Ultra lists "Commercial use rights".

   Verify, and say whether any service-specific terms for Flow, Flow Music, Genie or Antigravity change it.
2. **xAI, Grok:** the consumer terms, **and** whatever terms cover the "Grok Build" subscription the studio's
   build seats used. Read the live page: R&D's fetch was refused.
3. **Moonshot, Kimi:** the consumer agreement, and the Open Platform (API) terms. Say which one likely applies to
   a handoff written in the Kimi app.
4. **Anthropic, Claude:** the consumer terms covering a Pro or Max plan used through Claude Code.

## Questions

**Q1.** For each provider and each use, U1–U4: allowed, barred or unclear, with the clause.

**Q1b.** For Google Flow (video and images) and Project Genie: is there any Google document that **explicitly
grants** commercial use of their outputs, as the Ultra benefits page does for Flow Music ("Commercial use rights")?
Quote it. If none exists, answer "not proven: don't use" for U1. A missing restriction isn't a grant.

**Q2.** The "compete" wording:
- where a clause bars only *competing* models (xAI, Moonshot, possibly Anthropic), does a small task-specific
  local verifier count?
- quote any definition of "compete" or "competing".

**Q3.** Does any provider's terms treat **evaluation-only** use (U3) differently from training?

**Q4.** For Google's "related AI technology": is there any official guidance or FAQ on its scope? Does it reach
code written by Antigravity for AI tooling (U4)?

**Q5.** Which account types escape the restriction, and how: Workspace or Gemini Enterprise, paid API terms, an
enterprise agreement?

**Q6.** Anything else that bears on a public research repo publishing AI-written datasets.
