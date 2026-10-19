[R&D → Argon] rnd at scale, round 2: the fixed plan for your re-check. A short form is fine.

**What you reviewed:** plan v1, bundle 6ce3076e. Your verdict: CONDITIONAL PASS, with 3 blocking findings (F1–F3),
3 before P4 (F4–F6) and 1 not blocking (F7).

**What to review now:** plan v2, in the bundle `rnd-scale-plan-v2-code.txt`. Only the plan changed. The reference
files (rnd README sections, `store.py`'s schema, the natural-errors spec) are the same as round 1's. The bundle
starts with `SHA256:` over its body and `LINES:`.

**What changed:** §10 of the plan maps each finding to where v2 takes it in. In short:
- **F1:** backups to D: are now P0, before any coding, and include rnd-watch.
- **F2:** costs carry a cost unit, budgets are kept per unit, and runs carry the raw manifest id.
- **F3:** model weights hosted upstream are not stored. Builds we made are stored once, by SHA-256, in a blob
  store.
- **F4:** P3 sets up the off-site copy with a scripted restore test. P5 removes the Publisher's 58 tracked
  receipts. P6 deletes an E: copy only after both copies verify, the restore test passes and the Director gives
  the go.
- **F5:**
  - runs from any venue, the rig included;
  - a gitignored `staging/` for data-pack builds;
  - `results/` added to the layout;
  - published gold labels separated from sealed gold keys;
  - a private-file rule in `rnd check`.
- **F6:** a public flip and a T5 leak are added to the compensators. The existing packs stay at their cited URLs.
- **F7:** cut the rnd-private repo, the second database, the inventory script and the verifier-gold move.
  artifacts/uses are replaced by `files` and `copies`.
- **Your answers to Q1–Q6** are taken in: the content rule for tiers, T5 in rnd-data, the four off-site criteria, the
  namespace, runs written by tools, and licences from a `models` list in each manifest.

The plan's own round-2 questions are in §9.

**Severity levels:** `blocking`, `before P4`, `not blocking`.

Reply under `## <date> · rnd scale plan · round 2 · v2`.
