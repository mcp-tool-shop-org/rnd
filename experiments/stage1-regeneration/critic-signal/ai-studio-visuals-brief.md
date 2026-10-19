[R&D → AI Studio] Consult brief: build the data-visualized pages for one study, from our data only.

Paste this whole brief in. Everything you need is in it. You have no other knowledge of our studio, so don't add any.

## 1. Who you're working for

You're building for the R&D seat of a small game studio that runs its own AI research and publishes the results as a
public newsletter. Readers are curious non-specialists. Every figure we publish has to be traceable to a committed data
file. Being wrong in public costs us more than a missing chart.

## 2. Hard rules (break one and the work is unusable)

1. **Use only the numbers, ids, names and dates in section 4.** Don't invent:
   - counts, rates, costs, timings, item ids, slot ids, commit hashes or run names;
   - item categories, critics, or test families.
2. **If a visual needs a number that isn't in section 4,** show a visible placeholder (`DATA NEEDED: <what>`). Don't
   estimate it.
3. **Make no claims about software, versions, releases or deprecations.** Name no library as "the 2026 standard". Our
   data is a few hundred rows; it needs no GPU dataframe engine.
4. **Units as given:**
   - compute cost is in **Colab compute units** (`units`), never dollars, except where section 4 gives dollars;
   - call time is in **seconds**.
5. **Every rendered number carries its source key** from section 4, for example `phase3.muse.P2.f`, in a tooltip or a
   Sources panel.
6. **Measured and illustrative are kept apart.** If you show any made-up data (for example a "what if" toggle), it gets
   an "ILLUSTRATIVE, not our data" banner.

## 3. The story, in plain words

A **critic** is an AI model that checks the training rows another AI model writes. We tested whether two critics,
**Muse** (Muse-Glimmer-30B) and **Lightning** (Nemotron-3.5-Lightning), catch rows we broke on purpose. We compared two
rule sets on the same critic replies:
- **P0** is today's rules, where the flaw check is advisory;
- **P2** makes the flaw check count, plus two quote rules.

**The broken-copy types** (each one should be refused):

| Code | Name | What changed |
|---|---|---|
| b | material flip | a number in the deciding line was changed |
| e | can't-tell trap | the deciding line was removed |
| f | clean trace | the checker's flawed reasoning was replaced with sound reasoning, but the flaw label was kept |
| g | decoy deciding line | the answer's deciding line was swapped for a non-deciding one (scored offline) |
| a | verdict flip (key only) | the answer key's verdict was flipped; deterministic, reported apart |
| c | flaw relabel (key only) | the answer key's flaw label was changed; deterministic, reported apart |

**d** is an unchanged good row: refusing it is a mistake.

**Phase 3 result** (the study's first test):
- P2 beat P0, 6 to 0 with Muse and 7 to 0 with Lightning. Every difference was on the clean traces (f).
- The pre-registered correction across 4 comparisons put the best result at p = 0.0625, against a bar of 0.05, so
  nothing was adopted.

**Phase 4, a confirmation on fresh rows** (Muse only, one pre-registered test):
- P2 caught 22 more broken items than P0, with 0 the other way (p ≈ 5 × 10⁻⁷).
- But P2 also wrongly refused **12 of 32** good rows, against a limit of 10%. So again it was not adopted.
- The confirmation's rows came from a slot list. An outside reviewer found the first draft's list held only 12 of its
  38 slots able to make a clean-trace copy. The fix used all 27 eligible slots plus 11 controls, still 38.

## 4. The data (the only numbers you may use)

`refused` counts items refused out of `n`. For broken types (b, e, f, g, a, c), refused is a catch. For d, refused is
a mistake. Dropped items are already removed.

```json
{
 "phase3": {
  "muse":      {"P0": {"d":[0,22],"b":[5,6],"e":[17,17],"f":[0,6],"g":[17,17],"a":[22,22],"c":[0,10]},
                "P2": {"d":[1,22],"b":[5,6],"e":[17,17],"f":[6,6],"g":[17,17],"a":[22,22],"c":[10,10]}},
  "lightning": {"P0": {"d":[0,22],"b":[9,9],"e":[17,17],"f":[0,7],"g":[17,17],"a":[22,22],"c":[0,11]},
                "P2": {"d":[0,22],"b":[9,9],"e":[17,17],"f":[7,7],"g":[17,17],"a":[22,22],"c":[11,11]}},
  "format": "[refused, n]",
  "tests": {"muse_P2_vs_P0": {"discordant": "6:0", "p": 0.031},
            "muse_P3_vs_P0": {"discordant": "6:0", "p": 0.031},
            "lightning_P2_vs_P0": {"discordant": "7:0", "p": 0.016},
            "holm_family_size": 4, "holm_adjusted_smallest_p": 0.0625, "alpha": 0.05, "adopted": false}
 },
 "phase4_muse": {
  "P0": {"d":[0,32],"b":[5,5],"e":[20,20],"f":[0,22],"g":[18,19],"a":[32,32],"c":[0,32]},
  "P2": {"d":[12,32],"b":[5,5],"e":[20,20],"f":[21,22],"g":[19,19],"a":[32,32],"c":[29,32]},
  "test": {"discordant": "22:0", "p": "about 5e-7", "control_refusal_limit": 0.10,
           "control_refusal_P2": "12/32", "adopted": false}
 },
 "slots": {
  "lessons": ["T02","T03","T06","T07","T08","T09","T10","T11","T15","T18"], "slots_per_lesson": 8,
  "used_before": ["T02-C-01","T02-C-08"],
  "f_eligible": ["T02-C-03","T02-C-05","T02-C-07","T03-C-01","T03-C-05","T03-C-07","T06-C-05","T06-C-07","T07-C-01","T07-C-03","T08-C-01","T08-C-07","T09-C-01","T09-C-03","T09-C-05","T09-C-07","T10-C-01","T10-C-03","T10-C-07","T11-C-03","T11-C-05","T11-C-07","T15-C-03","T15-C-05","T18-C-01","T18-C-03","T18-C-05"],
  "controls": ["T02-C-06","T03-C-02","T03-C-04","T03-C-08","T06-C-02","T06-C-06","T06-C-08","T07-C-02","T07-C-04","T07-C-08","T08-C-04"],
  "draft_slot_count": 38, "draft_eligible_count": 12,
  "rule": "odd-numbered slots plant a flaw; even-numbered slots plant none; a clean-trace copy needs a planted flaw and a decided answer"
 },
 "runs": [
  {"window": "13v", "what": "free test ladder (CPU)", "units": 0.05},
  {"window": "13w try 1", "what": "launch mistake, failed in 27 s, nothing scored", "units": 0.24},
  {"window": "13w", "what": "Muse, seed 0", "units": 3.10, "projected_units": "2.83 to 10.43"},
  {"window": "13x", "what": "Muse, seed 1", "units": 3.17, "projected_units": "about 2.69"},
  {"window": "13y", "what": "Lightning, seed 0", "units": 4.52, "projected_units": "3.82 to 8.83"},
  {"window": "14a", "what": "38 new rows written (Gemma 4, no critic)", "units": 11.78},
  {"window": "14b", "what": "confirmation, Muse, seed 0", "units": 6.40}
 ],
 "call_seconds": {
  "13w muse verdict": {"n":62,"median":14.9,"p90":25.5,"max":41.2,"median_thinking_tokens":457.5},
  "13w muse flaw":    {"n":27,"median":21.3,"p90":38.2,"max":58.4,"median_thinking_tokens":706},
  "13x muse verdict": {"n":62,"median":13.7,"p90":24.6,"max":48.4,"median_thinking_tokens":432},
  "13x muse flaw":    {"n":27,"median":20.0,"p90":32.5,"max":63.0,"median_thinking_tokens":662},
  "13y lightning verdict": {"n":63,"median":11.6,"p90":19.3,"max":37.0,"median_thinking_tokens":1140},
  "13y lightning flaw":    {"n":30,"median":16.7,"p90":42.2,"max":85.3,"median_thinking_tokens":1737},
  "14b muse verdict": {"n":80,"median":17.8,"p90":30.6,"max":45.5,"median_thinking_tokens":550},
  "14b muse flaw":    {"n":80,"median":22.9,"p90":53.5,"max":89.6,"median_thinking_tokens":754.5},
  "note": "Lightning had one more call (an empty reply that hit the 16,384-token cap after 160.4 s, retried). P0 and P2 re-score the same replies, so they have no timing difference."
 }
}
```

## 5. What to build: one form per point, no chart factory

1. **The main result: a table** of item type × rule (P0, P2) × critic, for phase 3.
   - In the f row, show each clean-trace item as a glyph: ○ missed, ● caught.
   - Put the d row (good rows wrongly refused) in the same view, so catch and cost are read together.
   - A footnote gives the Holm result in section 4's words.
2. **The confirmation: the same table form for phase 4.** Make the 12-of-32 control refusals impossible to miss. That
   cost is the reason P2 wasn't adopted.
3. **The slot map:** 10 lessons × 8 slots.
   - Mark f_eligible, controls and used_before, and leave the rest plain.
   - Add a note on the review that changed the draft (12 of 38 eligible), with the numbers from section 4 only.
4. **Cost:** a simple table or bullet list of `runs`, with projections where given. No timeline invented beyond these
   rows.
5. **Call time:** only if it earns its place. A compact strip per row of `call_seconds` (median, p90, max) is enough.
   Don't draw distributions you don't have the raw data for.

## 6. Output

- One self-contained page, React or plain HTML.
- A **Sources** panel listing every number shown and its section-4 key.
- A test that loads the section-4 JSON and checks that every number rendered on the page appears in it.
- No sign-in, release-gate or publishing controls. Publishing is our decision, outside your page.

## 7. How we'll check your work

1. Every number on the page traces to section 4.
2. Nothing is invented: no item categories, commits, dollar costs, millisecond timings or test families.
3. Each placeholder names the missing data.
4. The phase-4 control refusals (12/32) are visible beside P2's catches.
