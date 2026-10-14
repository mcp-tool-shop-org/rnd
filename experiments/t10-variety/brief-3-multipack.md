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
