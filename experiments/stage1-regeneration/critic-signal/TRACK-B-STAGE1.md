# Track B stage 1: the blinded read (2026-10-22)

**The method:** design §4. All 43 Track A d controls (22 planted-none, 21 planted-flaw) were shuffled with their ids,
planted flaws and the critic's labels hidden.
- A pre-pass marked `verbatim_quote`: an exact span of at least 4 words that's a substring of the material.
- R&D tagged `paraphrase`, `forced_inference`, `outside_premise` and `hedge` by the binary rules, and committed the tags
  before unsealing the key.
- **A disclosure:** R&D had written the "guess" note on 12 of these traces, so the read wasn't blind to those 12 for
  the reader. The pre-pass tag is mechanical.

Item text stays private. These are counts.

## Planted-none controls (sound traces)

12 of the 22 drew a flaw label in at least one Muse run.

| Feature | Flagged with it | Flagged without it |
|---|---|---|
| outside_premise | 0/0 (no sound trace has one) | 12/22 |
| hedge | 0/0 (none has one) | 12/22 |
| forced_inference | 7/11 | 5/11 |
| verbatim_quote | 11/18 | 1/4 |
| paraphrase | 7/15 | 5/7 |

- **Forced inference raises the rate a little.** Neither quoting nor paraphrase explains it: quoting traces are flagged
  as often as paraphrasing ones.
- **The over-call is broad:** Muse names "guess" on about half the sound traces, whatever their form.

## Planted-flaw controls

- **Planted guess:** 6 of the 7 traces have an `outside_premise`, and Muse labels all 7 guess in at least one run.
- **Planted loop:** all 6 have a `hedge`; one has an outside premise and draws "guess".
- **Planted nitpick:** 5. **Planted rubber_stamp:** 3, one with an outside premise.
- **Under coarse Pc,** only one planted-flaw control was ever labelled "none": one loop trace, in run 2.

## What it means for the fix (inside design §6)

- **The one feature that separates sound traces from planted guesses is an outside premise:** 0 of 22 sound traces
  against 6 of 7 guesses.
- **So the treatment defines "guess" by that feature alone:** a claim, premise or assumption the material doesn't
  state. It says outright that a conclusion drawn only from stated lines, whether by quote, faithful restatement,
  comparison against a stated range, time or date, direct consequence, or plain synonym, is never a guess. That's §6's
  rows 1–3 written as one definition.
- **The rubber_stamp and reject_by_default rows** stay as §6 sets them.
- **The 3-vote** stays, for the flaw call's noise: the label flipped between runs on 5 of the 12 flagged sound traces.
