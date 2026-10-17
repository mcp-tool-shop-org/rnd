# The critic's known-answer set, v1

**What:** 40 keyed items for role-set's `critic-control`. They calibrate a critic before its verdicts may refuse
anything.

**Why fresh items:**
- **Not the frozen Stage 1 rows:** Grok's terms are unclear on using its output in ML development, and the Kimi
  route is unconfirmed.
- **Not DEV:** tuning the data gate on the student's own evaluation set would fit one to the other.

**Provenance:** written by Claude (the R&D session) on 2026-10-16. Anthropic's terms allow that use for a
non-competing specialized tool (`licences/registry.json`: `anthropic-help-12326764`). Keys are by construction:
each material, statement and key was written together. No real-source text is used.

**Contents:**
- 16 C items, two for each of the eight flaw types in `role_set.critic.FLAW_DEFINITIONS`, each with the other
  checker's reasoning and verdict;
- 12 D items and 12 verdict-type E items;
- verdicts: 15 supported, 15 unsupported, 10 cannot_tell.

They load through `role_set.critic_control.cases_from_rows`, and `plant_errors` breaks keys on copies, as usual.
The trait leg isn't covered here: it runs on the pilot's own rows, which come from licence-cleared writers, keyed
by their lesson.

**The bar (R&D, 2026-10-17, set before any result).** A critic passes critic-control only if it meets all of these:
- **key agreement:** at least 36 of the 40 unplanted items;
- **catch rate:** at least 80% on the planted errors (`--planted 10 --seed 0`);
- **run-to-run disagreement** for a sampling critic (Muse at its card's temperature 1.0): at most 4 of the 40
  unplanted items differ between two runs at different critic seeds (`--critic-seed 0`, then `1` with
  `--agreement-with`).

It runs at its card's values, with thinking on, at a 32768 context and `max_tokens` 16384, against one
`llama-server` slot. A critic that misses any part of the bar goes back to R&D before the pilot.

**Rebuild:** `python -I build_known_answer.py known-answer-v1.jsonl`
