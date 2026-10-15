# BUILD BRIEF | Seat C | role-set: the Advocate, the live pilot run | mcp-tool-shop-org/role-set | from R&D, with the Publisher | 2026-10-15

**Status:** the code is passed. The writer swap at `e99b1b4` passed R&D's diff check, after fix-up 3 passed Argon's round 8. **The grant is posted:** `publisher-5090-advocate-pilot-2026-10-15`, on role-set #56. This turn runs the pilot under that grant, hands back the record, and stops for the read.

**What governs the run:** `seat-build-batch1-turn3-pilot.md` (the pilot brief), as amended by fix-ups 1–3 and the writer swap. Where they differ, the later document wins. In short:
- 16 slots and 26 texts (16 positives, 10 kind A negatives);
- five negatives change the verdict (slots 1, 2, 3, 6, 9) and five don't (4, 5, 7, 8, 10);
- the critic reads the record and the prose, never the key;
- the bar: at least 15 of 16 positives recovered, at least 9 of 10 negatives flagged, every code check passed without a one-family retry loop, and no spin in the read.

## The run: the grant note governs

**Follow the Publisher's grant note on #56 for the run line, the heartbeat path, the run directory, the caps and the grant's own hand-back:** https://github.com/mcp-tool-shop-org/role-set/pull/56#issuecomment-6184650688. This brief doesn't repeat them, so the two can't drift.

As that note stands:
- **The run directory** is outside the checkout, under `E:\AI\`, never a temp folder.
- **The caps** count from the run's start, not from when the grant was posted.

Beyond the note, from the pilot brief: the head stays `e99b1b4` with no code edits before the run. Retries go to the same family with a new seed, a slot is reset after five refusals, and there's never a fail-over to the other family.

## After the run

1. **Confirm the card is clear:** `/api/ps` empty and no model loaded. Record the exit code, the wall time and the peak VRAM.
2. **Commit the run** to #56 as one commit:
   - copy `pilot.json` and `read.md` from the run directory into `docs/runs/advocate-pilot-2026-10-15/`, with a short `README.md` that says **these are pilot texts, not training data**;
   - the one-field follow-up: the granite row's `checked_by` in `writers.json` becomes the Publisher's wording: `"the Publisher, 2026-10-15 (digest fd429f23…, bundled Apache-2.0; card ibm-granite/granite-3.3-8b-instruct@51dd4bc, apache-2.0)"`.
3. Run the identity scan on a git archive of the commit before pushing. The texts are synthetic, with role titles only, but scan anyway.

## Hand back on #56 as `[Seat C → Publisher]`, then stop

- the head SHA and the grant id;
- **GRANT END,** as the grant note asks: models unloaded, `/api/ps` empty, the exit code, the wall time, the peak VRAM and the report path;
- **the bar, as measured:**
  - code checks passed, out of 26;
  - attempts by family, and any five-refusal reset;
  - the critic's positives recovered (of 16) and negatives flagged (of 10);
  - both probe readings (all 26 and kind A's 20) beside their nulls;
- **what the surfaces revealed:**
  - any check that refused honest prose, with the sentence it refused;
  - any slot where the critic and the checks disagree;
  - any reply that wasn't JSON, or was empty;
- **the reviewers' first reads, printed in full:**
  - slot 3 (the pod with the baseline miss) and slot 1 (the shortest record);
  - every kind A negative;
  - the exact sentences that tripped trace, order or length, by family.

**Stop.** The Director, R&D and Argon read the 26 texts. Nothing is trained, and the batch waits for the Director's go after that read.

## Gates

- Touch only the run directory and the one `writers.json` field. CI green after the commit. The identity scan CLEAN.
