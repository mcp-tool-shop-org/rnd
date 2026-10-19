# What the critic-signal study has shown so far (2026-10-19)

A synthesis of phases 0–4 and the parked step 1 of §10, drawn from `PHASE-0-1.md`, `PHASE-2-3.md`, `PHASE-4.md` and
`DESIGN.md`. It adds no new data. The open decisions are the Director's.

**Status:**
- No critic protocol is adopted. The pipeline keeps P0, today's rules, with the flaw check advisory.
- §10's larger critic (Nemotron-3.5-Super-VL-120B at Q8_0) is converted, pinned and hosted, but nothing has been
  scored. Step 1 is parked until RunPod spending resumes. On the resume, a free check for an H200 on a CUDA 13.0 host
  runs first.

## The findings

1. **Today's rules have a real hole: the clean trace.** A kind C row whose checker trace is swapped for sound
   reasoning, but which keeps its flaw label, passes P0 every time:
   - 0 of 13 refused in phase 3, across Muse and Lightning;
   - 0 of 22 refused in phase 4, with Muse.

   A student trained on such a row learns a flaw label the trace doesn't show. The critics see the problem and say
   so. In phase 3 both answered "no flaw" on every clean trace, 13 of 13. In phase 4 Muse did on 19 of 22. P0 just
   doesn't act on that answer.

2. **The flaw gate closes the hole, and the result replicated.**
   - Phase 3: P2 beat P0 by 13 : 0 across the two critics. That missed the bar after Holm, at 0.0625, only because
     the pool held 6–7 clean traces per critic.
   - Phase 4: on fresh rows, by one pre-registered comparison, P2 beat P0 by 22 : 0, at p ≈ 5 × 10⁻⁷.
   - Every P0-to-P2 difference in phase 3 came from the flaw gate. P2's two quote rules decided no phase-3 item, and
     one phase-4 control (C9-030:d).

3. **The flaw gate's cost was hidden by the first pool.**
   - Phase 3's controls were rows the critic itself had already accepted, and P2 refused 1 of 44.
   - Phase 4's controls were fresh rows, unscreened by any critic, and P2 refused 12 of 32 (37.5%), against a 10%
     limit. That's why P2 wasn't adopted.
   - The lesson for any gate: measure its false refusals on rows the critic hasn't screened. Rows it has already
     accepted agree with it by selection.

4. **The false refusals follow the label taxonomy, not just the critic.**
   - Most of Muse's misreads in phase 4 were "loop" read as "guess": it agreed on only 2 of 7 loop slots.
   - Three of the six rows R&D excluded at the gold check were also guess/nitpick boundary cases.
   - On the natural "none" controls, Muse said "none" on 6 of 10.

   Where the labels blur, a critic gated on the exact label will refuse good rows, whatever its size.

5. **The verdict check is strong, and needs no change.**
   - Material flips (b): all refused except one Muse miss in phase 3 (an end time changed by two hours), which
     Lightning caught.
   - Can't-tell traps (e): all refused in both phases.
   - Decoy deciding lines (g): all refused, except one P0 miss in phase 4.
   - Controls: none refused on verdict in either phase.

6. **A second seed added nothing.** P3 (two Muse seeds, refusing if either refuses) matched P2 on every type in
   phase 3. It would double the critic's cost for no gain on these items.

7. **The rows the writers produce are right but easy (phase 1).**
   - R&D's blind keys agreed with 29 of 30 verdict rows (1 unclear).
   - But none of the 30 had cannot_tell as its true verdict.
   - 15 of the 51 accepted rows (kinds A and non-verdict E) get no accuracy check from the critic at all.
   - Two traces gave their own label away (defect class `trace-leaks-label`). No critic check can see that.

8. **A critic call was much faster than projected.** Muse's median call took 14–19 s across phases 3 and 4. The
   design projected 120 s an item, taken from Lightning's earlier traited runs.

## What the study cost

- **Colab:** 195.17 of the study's 300 units.
  - Phase 3: 10.79, plus 0.05 for the stub rung.
  - Phase 4: 18.18, of which 11.78 wrote the 38 fresh rows.
- **RunPod, step 1 of §10:** $8.05, with nothing scored yet.
  - A100 conversion, stopped by a timeout sized for 30B models: $3.05.
  - RTX PRO 6000 conversion, quantize and upload: $2.34.
  - Two H200 pods that failed to boot on CUDA 13.2 hosts: $1.33 each.
  - $13.95 of step 1's $22 cap is unspent.

## What we learned about running studies like this

- **A non-mock probe before any freeze.** The first confirmation items were built with mock gates and no writer
  field. A probe caught it, and the items were rebuilt before the freeze.
- **A free rung before every paid step, on the exact code path.** Step 1's three paid faults were each one a small-model
  rung would have caught:
  - a fixed timeout too short for a 120B conversion;
  - a decode crash on a conversion route not tried before;
  - a full disk on a rerun.
- **Read the tool before stating its limits.** The H200 choice depended on offrig's exact CUDA pin
  (`cuda_versions`) and on how its budget caps combine. Both were settled by reading offrig's code.
- **Hand-checks before the run pay for themselves.** Every b, e and g item was checked before scoring. The one bad b
  item (a number with a unit attached) was dropped on the record before any call.

## What this means for T10, and the options

- **The safe default for T10 is P0 plus the deterministic fixes from phase 1:**
  - slots with real difficulty (cannot_tell, multi-line deciding, multi-turn D);
  - a gate that refuses a trace naming its own flaw;
  - an accuracy check, or a bounded share, for kinds A and E.

  The clean-trace hole stays a known risk under P0. It should be stated in T10's design.
- **Options to close the hole, for the Director to choose from:**
  - **A coarser flaw gate:** refuse only when the critic's flaw-or-none answer disagrees with the label's.
    - Post hoc on phase 4's replies, it would catch 19 of 22 clean traces and refuse 4 of 32 controls (12.5%).
    - That's still over the bar, and it was found after seeing the data, so it needs its own pre-registered test on
      fresh rows. That's Colab-only, at about phase 4's cost.
  - **Tighter flaw labels,** chiefly the loop/guess boundary. It's free to draft, and it changes the writer's slots
    and the gold keys, not the critic.
  - **The larger critic (§10),** resumed when RunPod spending resumes. It tests whether size reads the labels better.
    Finding 4 suggests size alone may not fix boundary cases. The run is still the direct test of that.
- **R&D's recommendation:** run T10 on P0 with the phase-1 fixes. When RunPod resumes, run §10 on the frozen items
  as planned. Test the coarse gate on fresh rows, with a fuller definition of "none", as `PLAN-ROUND4.md` sets out.
- **Corrected 2026-10-19, after this file was first merged.**
  - This recommendation first said to test the coarse gate against tighter flaw labels.
  - Phase 4's data say otherwise. All 4 of the coarse gate's false refusals were on planted-none rows (4 of 10),
    and none was on the 22 planted-flaw rows.
  - Pc treats every flaw label as one class, so the loop/guess boundary can't cause its refusals. Its errors are at
    the none boundary, which is a different lever. See `PLAN-ROUND4.md` §1.

## Licences

- Muse-Glimmer-30B, Nemotron-3.5-Lightning and Gemma 4 31B were used as recorded in `DESIGN.md` §0.
- Nemotron-3.5-Super-VL-120B is under OpenMDW-1.1, read 2026-10-16; its outputs are unrestricted.
- Its GGUF is our own conversion. It's kept in a separate private repo with the licence agreement and notices.
