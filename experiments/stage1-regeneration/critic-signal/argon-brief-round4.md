[R&D → Argon] Critic-signal, round 4: audit the plan for after phase 4. A full review, please.

## What happened since round 3b

- **The §9 confirmation ran** (`PHASE-4.md`). P2 caught 22 : 0 more errors than P0, p ≈ 5 × 10⁻⁷, but refused 12 of
  32 good rows. It was not adopted.
- **§10, the larger critic,** is parked until RunPod spending resumes. The model is converted and hosted, but nothing
  has been scored.
- **`SYNTHESIS.md`** pulls the study's results together.

## What to audit

`PLAN-ROUND4.md` at the commit named in the bundle file, in the bundle `rnd-critic-signal-4452274-round4-code.txt`, in two parts (`.part1of2.txt`, `.part2of2.txt`). Each part starts with `SHA256:` over its body and `LINES:`.

The bundle also holds, for reference:
- `SYNTHESIS.md`, `PHASE-4.md` and `DESIGN.md`;
- role-set's `src/role_set/critic.py` at `89b5f2e`, the flaw prompt and its label definitions.

## Where to look hardest

1. **§1's new reading of phase 4.**
   - The coarse gate's 4 false refusals all fall on the 10 planted-none rows.
   - P2's extra errors are wrong labels on planted-flaw rows.
   - The plan corrects `SYNTHESIS.md` on this basis. Check the reading, and whether 10 rows can carry it.
2. **The decision rule in §3:** the weighted control bar, Holm across two, and the fallback to Pc-old.
3. **The prompt edit in §3,** and whether it trades catches for fewer false refusals.
4. **§3's rungs:** do they cover every new code path before the paid windows? Rung 1 has a known answer from phase 4.
5. **§2:** running T10 on P0 now, with the gold check as its safety net.

The plan's own questions are in §7. Answer them, and add anything else you find.

**Severity levels:** `blocking`, `before the write window`, `not blocking`.

Reply under `## <date> · rnd critic-signal · round 4 plan · <commit>`.
