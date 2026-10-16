# Argon's answer, summarised (2026-10-16)

Browser Argon's reply to [the brief](argon-brief.md), pasted by the maintainer. It's **summarised here, not
reproduced**: it quotes long passages of provider terms, so the clauses that matter sit in R&D's verification
table in [README.md](README.md), re-read at their URLs. **Read that table first. Only R&D-confirmed clauses
count.**

## Argon's verdicts per provider and use

| Provider | U1 commercial assets | U2 training data | U3 evaluation only | U4 code |
|---|---|---|---|---|
| Google (consumer Ultra) | Flow Music allowed. Flow, Genie and Gemini not proven | barred | not proven | AI-infrastructure code barred or not proven. General code not proven (non-ownership only) |
| xAI (consumer, Grok Build, Enterprise) | allowed (FAQ; brand attribution requested) | barred (AUP distillation clause; Enterprise ban on training any AI system) | not proven | non-competing code allowed. Competing tooling barred. Grok Build page unsure |
| Moonshot (Kimi consumer app) | barred (non-commercial personal use). OpenPlatform not proven | not proven | not proven | barred for commercial use |
| Anthropic | consumer "barred" (**R&D: wrong**, see README). Commercial terms allowed | barred (2026 Usage Policy; Help Center "training targets") | not proven | consumer "not proven". Commercial allowed if non-competing |

## Argon's points beyond the questions

- **xAI's ban isn't limited to competing models.** It bars distillation outright, and training any AI system under
  its Enterprise terms. (Confirmed by R&D.)
- **Anthropic's 2026 Usage Policy** (effective 12 November 2026) bars training on outputs without authorization.
  (Confirmed.)
- **Consumer non-commercial clauses** for Claude and Kimi. (Kimi confirmed. Claude's applies to evaluation access
  only, per R&D's re-read.)
- **Antigravity's terms bar using third-party tools to access the service,** for example routing external agents
  through personal Google OAuth credentials. That bears on the Publisher's bridge design. (Not yet re-read by R&D.)
- **Publishing provider-written datasets** with training scripts in public repos may count as assisting others'
  training, under xAI's and Anthropic's clauses.
- **What escapes:** data generated locally by open-weight models with permissive licences. Paid API or enterprise
  accounts don't escape training bans without explicit provider authorization.

**Format note:** Argon's second pass summarised some clauses instead of quoting them. Under the proof rule, those
count only where R&D re-read them.
