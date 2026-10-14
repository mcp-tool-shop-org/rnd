# Brief 3: T10 variety across packs of the same kind, for a seat

**Status:** written 2026-10-14 on the Director's word that this is fixed before role-set#49 merges. Goes to the Publisher for review and seat assignment.
**Repository:** mcp-tool-shop-org/role-set. Start from the Publisher's local rebase of #49 onto main after #54 (`E:/AI/role-set-pub-49`, head `e6ca07e`), with its regenerated cell table for 8 packs. Coordinate the branch with the Publisher; #49 stays held until this lands.
**Template:** [diagnose-then-fix](../../site/src/content/docs/handbook/diagnose-then-fix.md) (prototype). It follows [brief 1](brief.md) and [brief 2](brief-2-trait-tested.md).
**Design input:** Argon (Gemini, by hand, 2026-10-14). The summary is in the Publisher's drafts. R&D checked it against the rebased code.

## 1. The check, in three sentences

- **Diagnosis (done, measured):** with 8 packs, six of them three-value, the three-value set stratum has a skeleton repeated 4 times on the locked seeds 41–60. That's over the floor of 3, and the claim stratum sits exactly at 3.
- **The fix:**
  - Across the packs of a value-count stratum, cells are allocated together rather than per pack.
  - Cells with no `if` clue get the fewest visits.
  - The cell table fails loudly when a stratum's builds outgrow its cells.
- **Why the re-measurement answers it:** on fresh locked seeds, every stratum must clear the same three floors as today, with no loosening, and the zero-`if` cells must carry the fewest visits.

## 2. The diagnosis

Measured by R&D on the rebase at `e6ca07e`, seeds 41–60, the six three-value packs (cups, pans, machines, trains, beds, clinics):

| Stratum | Distinct | Top repeat | Its cell (n, word, k, `if`s) | Packs on it |
|---|---|---|---|---|
| set, three-value | 108/120 | **4** | (3, at most, 2, 0) | cups, pans, beds, clinics |
| claim, three-value | 106/120 | 3 (three skeletons) | (5, =, 1, 0); (3, =, 1, 0); (5, =, 4, 0) | 3 packs each |

- **Every top repeat is a cell with no `if` clue.** Such a cell holds very few skeletons, so each visit from another pack repeats one. Argon's diagnosis holds.
- **The cause:** `cell_for` spreads one pack's seeds over that pack's own list, offset by pack. Nothing coordinates the packs, so 120 builds over 71 set cells leave some cells with 4 visits.
- **Capacity:**
  - Three-value set has 71 cells (24 with no `if`).
  - Three-value claim has 27 cells (9 with no `if`). That's every combination a claim cell can be (n 3–5, "exactly", k 1 to n−1, 0–2 `if`s), so 120 claim builds average 4.4 visits per cell.
  - Two-value strata have 40 builds each and pass today.

## 3. Rulings on Argon's proposals

- **The coupled gate is rejected.** Its "top repeat ≤ max(3, ⌈N/M⌉)" beyond 8 packs loosens the floor, and the floor only moves stricter. The floors stay: distinct ≥ 75%, top repeat ≤ 3, and no repeat within one pack's file, per stratum.
- **The balanced allocator is adopted, with Argon's caps adjusted.**
  - Argon capped zero-`if` cells at 2 visits and `if` cells at 3. That is 72 visits, short of the 120 the three-value claim stratum needs.
  - So zero-`if` cells are capped, and the remaining visits are spread evenly (minimax) over the `if` cells. A cell's real capacity is measured, not assumed (section 5, step 1).
- **The sub-cells are deferred:** the `if_shape` axis, `polarity_mode`, and the claim-role axis ("cross value", modus tollens).
  - They're the route to more same-kind packs, not to #49. The capacity gate in step 4 says when they're needed.
  - When they're taken up, each needs its own ruling:
    - `polarity_mode` reorders `is` and `is_not` only. `if` stays last, so #53's attribution is untouched. But tying polarity to pack parity puts a pack-to-clue-form regularity into the data.
    - The claim-role axis adds a second reasoning skill (modus tollens) to a lesson about size words. #54's hard assertion keeps `trait_not_tested` at 0 whatever the role.
- **`in` and `not_in`:** still Phase 2 material from brief 1, and not needed here.
- **Capping the number of packs:** rejected, as Argon says. Packs exist to add lexical variety.
- **Citations:** Yuster 2020 is unverified (Argon marked it as from search results only). Nothing here depends on it.

## 4. Symptom-to-fix table (fixed in advance)

| Symptom | Fix permitted | Not permitted |
|---|---|---|
| Packs of one kind pile onto the same cell | One deterministic allocator per (value-count stratum, question, file of 20 seeds) over the committed pack list | Any rejection of finished builds by skeleton |
| Zero-`if` cells repeat their few skeletons | Cap their visits per stratum and file (2 at most), and spread the rest minimax over the `if` cells | Dropping zero-`if` cells from the table |
| A stratum outgrows its cells as packs are added | A capacity check when the table is built and in the test, which fails with the numbers and names the next step (the sub-cells) | Loosening a floor |

A fix outside this table needs a dated amendment here before the locked seeds run.

## 5. Phase 1: the work

1. **Measure cell capacity.**
   - On tuning seeds, for each cell in each three-value stratum, count the distinct skeletons it yields across packs.
   - Commit those counts with the script that made them. They decide whether an `if` cell can take 5 or 6 visits without a repeat.
2. **The allocator.**
   - Replace the per-pack offset in `cell_for` with an assignment computed once per (stratum, question, file): seeds 1–20, 21–40, 41–60 and so on.
   - It works over the committed pack list in `t10_cells.json`, so it stays a pure function of the table, pack and seed. Adding a pack regenerates the table, as now.
   - **Hard rules:**
     - one pack's 20 seeds in a file take 20 different cells;
     - a zero-`if` cell takes at most 2 visits per stratum and file;
     - the remaining visits go minimax over the `if` cells, weighted by the measured capacity from step 1;
     - later files rotate the assignment, so files differ.
3. **Keep every existing check:** brief 2's gate (the trait's own reading differs, a hard assertion), one count clue, claims "exactly" only, tiered deletion, the `if` target with its retry, `MAX_IF = 2` and `SET_MAX = 4`. No pack text changes.
4. **The capacity gate.**
   - `scripts/t10_usable_cells.py` and the variety test both compute, per stratum and question, the builds per file against the allocator's capacity.
   - If the capacity is short, they fail, printing the numbers and naming the sub-cells (`if_shape`, then `polarity_mode`) as the next step.
   - Report the headroom for each stratum: how many more packs of that kind fit.
5. **Record it** in `docs/generator-design.md`: why packs of one kind share a skeleton space, the allocator, and the capacity gate.

## 6. The measurement

The locked test in `tests/test_t10_variety.py` keeps its assertions, on the new locked seeds, for all 8 packs:
- distinct ≥ 75%, top repeat ≤ 3, no repeat within a file, per stratum (set and claim, two-value and three-value);
- `trait_not_tested` = 0, and one count clue per item.

It adds:
- visits per cell, per stratum: assert no zero-`if` cell over 2;
- the top repeat's cell, reported.

## 7. Split: tuning seeds and locked seeds

- **Tuning:** seeds 1–60, which earlier work has already seen.
- **Locked:** seeds 61–80, not run until the Phase 1 code is frozen in a commit. The PR names the freeze commit.
- **#49's verdict** is read on this locked run.

## 8. Attribution

- The top repeat must fall, and its cell must no longer be a zero-`if` cell visited by 3 or more packs.
- If the floors pass and the zero-`if` visit caps hold, the allocator is credited.
- If the floors pass but the top repeat is still a zero-`if` cell, say so and don't credit the allocator.

## 9. Phase 2 (only if three-value claim misses a floor on the locked seeds)

- Add the `if_shape` axis for claim cells (for one `if`, a positive or negative antecedent; for two, a chain or a shared consequent), so the claim stratum has more than 27 cells.
- Re-run on fresh locked seeds 81–100.
- `polarity_mode` and the claim-role axis stay out of scope until R&D rules on them.

## 10. What the PR reports

- The verdict per stratum on the locked seeds, with the baseline (`e6ca07e`'s code on the same seeds) beside it.
- Cell capacity per stratum, visits per cell, and the headroom in packs.
- Lines of code added, and the change in build time and suite time.
- No pack or check changes. If one was needed, stop and ask.

## Amendment 1, 2026-10-14 (R&D, after Seat A's stop on role-set#49)

**What Seat A found.** Brief 3's rules can't be met on the committed table for three-value claims. That was measured, not projected:
- a pack's 20 seeds need 20 different cells, and a zero-`if` cell takes at most 2 visits;
- clinics has 14 claim cells with an `if`, so it needs 6 zero-`if` visits, and the other five packs need 4 each;
- that's 26 zero-`if` visits, against 9 cells × 2 = 18. A max-flow check places 112 of 120.

The other three strata place every build. The shortfall is in how many claim cells have an `if`, not in the cap. Brief 3 said it would be found as a projection; it was found as a fact.

**Ruling: option 3.**
- **`if_shape` moves from Phase 2 into Phase 1, for claim cells only:**
  - for one `if`, the antecedent is positive (`is`) or negative (`is_not`);
  - for two `if`s, the shape is a chain (one consequent's entity is the other's antecedent) or a shared consequent;
  - a shape that won't build at a given n is simply absent from the probe list.
- **The zero-`if` cap stays at 2,** and the floors are unchanged.
- **Set cells are unchanged.**
- **`polarity_mode` and the claim-role axis stay out of scope.**

**Why not the alternatives:**
- **A cap of 3 on zero-`if` cells (option 2)** passes only at the floor, by construction. Those cells hold about one skeleton each, so the stratum would carry three copies of several skeletons permanently, with no headroom for another pack.
- **Allowing repeated cells within a file** for packs short of `if` cells would bring back within-file repeats. That's a floor brief 3 keeps.

**What this changes in the work:**
- `scripts/t10_usable_cells.py` probes claim cells with the `if_shape` axis. The builder honours the shape:
  - `_addition_order` offers only `if` clues of the cell's shape;
  - a build whose reduced puzzle doesn't keep the shape retries inside the seed, as the `if` count already does.
- **Before the freeze,** the capacity gate must pass on the regenerated table for every stratum: zero-`if` demand at or under the cap, and every pack with at least 20 claim cells. Report each pack's cells with an `if`, and the zero-`if` demand.
- **#54's hard assertion still applies to every item:** the trait's own reading differs. The `if_shape` axis changes how the `if` clues connect, not the count.
- **The locked seeds stay 61–80,** not yet run. #49's verdict is read there. Section 9's Phase 2 is now `in` and `not_in` for three-value claims, only if a claim stratum still misses a floor.

## Amendment 2, 2026-10-14 (R&D): option 2. This supersedes amendment 1

Amendment 1 chose `if_shape` now. Argon, consulted by the Director on the same stop, chose option 2. R&D has weighed the two and changes its ruling to **option 2**. Amendment 1 stays above as the record.

**The ruling:**
- In the **three-value claim stratum only,** the zero-`if` cap is **3** visits per file. Supply is 9 × 3 = 27, against a demand of 26.
- **Every other stratum keeps the cap at 2.**
- **The floors are unchanged.**
- **No new cell axis:** set and claim cells are as committed.

**Why:**
- **Brief 3 defers new cell axes until a measured need.** At a cap of 3 the table fits, so the need isn't there yet.
- **A cell's skeletons can't outnumber its visits.** A skeleton fixes its cell (n, k, the count word and the number of `if`s are all in it). With at most 3 visits, no zero-`if` claim skeleton can pass 3 copies by construction.
- **These cells aren't one-skeleton cells.** On seeds 41–60 the busiest zero-`if` claim cells took 6 visits each and topped out at 3 copies of one skeleton. So 3 visits will usually give fewer than 3 copies, not exactly 3. The locked run will show it.
- **It's the smaller change before #49 merges.**

**What stays from amendment 1 and brief 3:**
- **The capacity gate** still runs in `scripts/t10_usable_cells.py` and the test, with the per-stratum caps above.
  - It reports, per stratum, supply, demand and headroom: each pack's `if` cells and its zero-`if` demand.
  - It fails loudly, with the numbers, when a stratum can't be placed. A seventh three-value pack will fail it.
  - It's a check on the table, not a raise inside `cell_for`.
- **Phase 2 is `if_shape` for claim cells,** as amendment 1 described it. It runs only if a claim stratum misses a floor on the locked seeds 61–80, or before another three-value pack is added.
- **`polarity_mode` and the claim-role axis stay out of scope.**
- **#54's hard assertion,** the allocator's other rules, and the locked seeds 61–80 are unchanged.

## Outcome, 2026-10-14: landed in role-set `787ccf8` (#49)

Seat A (Grok, then Argon from the CI round) built brief 3 with amendment 2. R&D reproduced the locked-seed table independently in clean worktrees, then passed #49 at `68a0f0d`.

| Stratum (locked seeds 61–80) | Distinct | Top repeat | Before the allocator |
|---|---|---|---|
| set two | 40/40 | 1 | 40/40 |
| set three | 120/120 | 1 | 110/119, one seed refused to build |
| claim two | 40/40 | 1 | 38/40, top 2 |
| claim three | 108/120 | 3, on cell (3, =, 1, 1) | 106/120, top 4 |

Every stratum clears the floors. claim three sits exactly on the top-repeat floor, the known limit of the zero-`if` cap of 3; Phase 2 `if_shape` is the relief before a seventh three-value pack, and the capacity gate fails loudly if one arrives first.

**How the floors are enforced in CI** (R&D's ruling after the suite outgrew the 15-minute job; the committed-record fallback applied once Argon's plan missed the 10-minute budget):
- A committed record, `src/role_set/generate/t10_record.json`, holds every build on seeds 1–20 and 61–80 for every pack and both questions: built, cell, tries, canonical skeleton. It carries a sha256 over every file that decides a build, closed under the package's imports.
- The normal job recomputes the hash, fails a mismatch by naming the regenerate command, asserts every entry built, and computes the floors from the stored skeletons. It runs in about four minutes.
- The exhaustive rebuild runs only on `workflow_dispatch`, without coverage, and must reproduce the record exactly. Any PR that changes the record needs a green dispatch run on its head before an R&D pass.
- A try cap, or dropping costly cells, stays refused: either changes which puzzles get built.

**Scheduling view sent to the Publisher:** Phase 2 waits for the next three-value pack request; the two-value claim gap is structural (brief 2) and needs no work.

