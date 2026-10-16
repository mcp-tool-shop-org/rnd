# Local builders

**Question.** Which local models (Ollama, no cloud) can do the studio's build jobs well enough to take them on?
Every run is recorded and mined, so each kind of job gets its best local model. The work is public, so people
without a subscription can use the results. The audits still gate every merge.

**Status (2026-10-16):** Wave 1's design is filed ([DESIGN.md](DESIGN.md)), drafted against the
[model comparisons](https://mcp-tool-shop-org.github.io/rnd/handbook/model-comparisons/) template, with R&D's
review changes. **Amendment A** (2026-10-16) makes role-set itself J1's control, under the proof rule. **Nothing
has run.** Next: Argon reviews the design, then the maintainer approves it, including Wave 1's unit cap.

**In short:**
- **Two job kinds:** J1 (Stage 1-style apply items written inside role-set, against role-set's incumbent
  licence-proven writer and critic pair; it selects the Stage 1 regeneration's writer) and J2 (real bug fixes,
  through Aider).
- **Candidates:** six for J2. J1 takes licence-proven writers only, which is two today, pending the maintainer's
  Apache-2.0 ruling.
- **Wave 1 is a screen** on one pinned Colab A100-40GB. J2 runs with the usable budget set to the 5090's 26 GB plan
  cap. J1 runs at the regeneration's own placement. It crowns no winner.
- **Wave 2** runs the confirmatory comparisons on the 5090, and the card sub-study on real Colab cards.

**Related:**
- `instruments/colab.md`;
- `experiments/colab-bottlenecks`;
- the model-comparisons template;
- the thinking-effort study, queued, which reuses these receipts.
