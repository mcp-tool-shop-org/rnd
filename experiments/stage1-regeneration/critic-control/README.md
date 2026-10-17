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

**Rebuild:** `python -I build_known_answer.py known-answer-v1.jsonl`
