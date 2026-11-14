# Escape the Valley narrator: fallback-rate sessions 1-4

**Status: sessions 1 to 4 run and filed as receipts; session 5 and the cloud comparison are filed separately.**
Template: none (a sequence of measured sessions, each answering the one before).

All figures below are copied from the sessions' own run records, filed beside this page.
Nothing here was recomputed unless a line says so. Claims are `[unverified]` unless a
line says otherwise: the counts are the harness's own output and nobody has checked them a
second time; no verifier pass was run (Standing Rule 3).

## What the narrator is

Escape the Valley (ETV) is a text survival game about a wagon party crossing a valley. The
game's engine decides what happens on each turn. A small local language model, the
narrator, only writes the prose: for each turn it is asked for two lines, a scene line and
an outcome line, in one of three voices (Chronicler, Fireside, Uncanny Bearer) at one of
three lengths (Brief, Standard, Rich). Every line goes through a rule checker (no invented
numbers or supplies, no deaths where none happened, no copying the choice label, a length
cap, and so on). A line that fails is replaced by a canned fallback line. The **fallback
rate** is the share of lines the checker rejected.

The harness (`narrator_measure`) asks the model for every slot of a fixed set of 360 turns
(the turn set, pinned by sha256 in each run record), 3 voices x 3 lengths x 2 lines, so one
arm is 6,480 lines. The model throughout is the local `qwen3:4b-instruct-2507-q4_K_M`
(Ollama, local daemon only), on the RTX 5090; session 3 also ran its unquantised (F16)
build. No cloud model is used in sessions 1 to 4.

## The question

Is the narrator's fallback rate low enough to ship, and where it is not, which rules,
prompt wording or sampling choices cause the rejections? Session 4 adds the sharper
question: does a line that passes the rules also say what happened on the turn?

## Sessions

| session | folder | date (ET) | arms | headline |
|---|---|---|---|---|
| 1 | [results/s1](results/s1/) | 2026-11-13 | plain, cited, text schemas (19,440 calls) | lines rejected on about 6 slots in 10 in every arm: plain 61.5%, cited 59.0%, text 62.1%; most rejections are the rules and the prompt disagreeing |
| 2 | [results/s2-recheck](results/s2-recheck/) | 2026-11-13 | plain, after the first fix (#85) | fallback 61.5% to 55.5%; paired by turn +5.9 points of lines accepted (95% interval +3.3 to +8.6); Rich much better, Standard worse |
| 3 | [results/s3-arms](results/s3-arms/) | 2026-11-13 | seven arms (52,771 calls) against session 2 | rulings prompt with up to three candidates and trimming: 55.5% to 8.1% (+47.4 points, interval +45.1 to +49.7); unquantised model and positive wording did not help |
| 4 | [results/s4-says-what-happened](results/s4-says-what-happened/) | 2026-11-13 | truth rules, outcome lead, repetition rules; three weak-card latency arms (32,003 calls) | 82.9% of lines pass every rule and say what happened, against 78.1% for session 3's best arm scored the same way (+4.9 points, interval +2.5 to +7.2); with part of the model off the GPU a turn takes 5 to 22 times longer |

Times in the run records are written "EST", which is Eastern time on those dates.

### Per-session arms

- **Session 1.** Three output schemas on the shipped rule wording: `plain` (a JSON object
  with the lines), `cited` (adds citations, 160-token budget), `text` (no schema).
- **Session 2.** The plain arm again after the first narrator fixes: word caps in place of
  sentence counts, unit words only after a quantity word, the typographic apostrophe read
  as plain, and 150 tokens at Rich. The turn set's `situation` text also changed (same 360
  turns, same ids), so before and after differ in prompt, checker, budget and turn text
  together.
- **Session 3.** `rulings` (the prompt rulings), `modelcard` (the model card's sampling),
  `cand-modelcard` (up to three candidates, trimmed to the cap), `combo` (rulings plus
  model-card sampling plus candidates plus trim; added mid-run), `briefstop` (Brief ended
  by a stop sequence), `fp16` (unquantised model), `positive` (positively worded rules).
- **Session 4.** `lead` (the outcome line must carry the turn's main fact), `swh`
  (says-what-happened truth rules, outcome lead, no repeated opening, no event-text copy),
  `ship` (swh plus brief-by-stop), and latency arms `lat-half`, `lat-quarter`, `lat-cpu`
  (18, 9 and 0 of the model's 36 blocks on the GPU).

## What each session folder holds

- `RUN-RECORD.md`: the run record as written at the time (grant, times, code sha, model
  digest, andon, VRAM, reading of the result, what was not shown).
- The session's summary tables (`SUMMARY-tables.md`, `COMPARE-tables.md`,
  `SUMMARY-all-rules.json`, `ARM-tables.md`), and the later offline re-scores
  (`RESCORE-*.md`, `RECHECK-OFFLINE-checker-only.txt`) where the session has one.
- `reports.json`: every per-cell report the harness wrote (`etv-fallback-measure-1`),
  bundled into one object keyed by `<arm>/<cell>` and otherwise unmodified. A cell is one
  voice at one length, 720 calls.
- `KEPT-ON-RIG.tsv`: the files that stayed on the rig and were not committed, by relative
  name, byte size and sha256. They are the per-cell **raw row files** (everything the
  model wrote, the request and seed, the verdict and reason code per slot, about 348 MB for
  the four sessions), plus scripts, logs and VRAM readings. Each cell's `stdout.txt`
  repeats its report and its `stderr.txt` is empty, so neither is listed.

Not filed here: the reading samples (a hand reading of accepted lines, filed separately),
the per-row re-score JSONs, session 5 (larger local models) and the Claude comparison.
Where a run record or the session 4 re-score names them, read those references as pointing
at records not yet filed in this repository.

## Results, in order

1. **Session 1:** the checker and the prompt disagreed. The Chronicler is told to write
   short declarative sentences and then rejected for length (91% fallback at Brief);
   `step`, `foot` and `turn` were read as units; the typographic apostrophe was not
   accepted (176 rejections); Rich answers were cut off at 110 tokens (170 bad JSON). Level-1
   turns have no weirdness allowance of their own, and the Uncanny Bearer's voice asks for
   weirdness, so its band vocabulary rejections are that collision, not a model fault.
2. **Session 2:** Rich went from 14.2% to 46.0% lines accepted (paired by turn), Standard
   from 58.5% to 42.8% because told "at most 45 words" the model wrote to the cap. The
   quantifier rule became the largest reject (174 to 1,001): the prompt offered "one, both,
   pair" and the checker rejected them on gear.
3. **Session 3:** the prompt rulings did 55.5% to 25.4%, candidates 56.2% (one call) to
   20.4% (three) at 1.76 calls per line, and together 8.1% at 1.39 calls per line. Model-card
   sampling alone changed nothing (-0.7 points) but widened the openings; the unquantised
   model was worse (66.8%) at twice the latency; positive wording was worse (63.7%). The
   run record warns that 8.1% counts lines that pass the rules, and a reading of 29 accepted
   lines from the best arm found 7 that contradict their turn's facts.
4. **Session 4:** with truth rules on, no accepted line states a false supply fact, copies
   the event text or repeats the previous opening, and the outcome line carries the turn's
   main fact on every accepted line where one is required. The price is the pass rate,
   91.9% to 82.9%. Fireside still mentions the oxen in 15.4% of accepted lines overall
   (69.3% at Rich). With 18, 9 and 0 blocks on the GPU the turn p50 was 3,557, 4,416 and
   8,277 ms at Standard against 429 ms with the whole model on the GPU.
   An offline re-score under two checker changes (parroting only for verbatim copies of
   the choice label, three-word repeated openings with the lead's own subjects exempt)
   moves the ship arm's good lines from 82.9% to 85.7% (a lower bound, because the harness
   kept only the last candidate); the cloud rows in that file belong to a later record.

## Cloud comparison: the Claude API (2026-11-13)

The same shipping shape and the same 360 turns, run through the Claude API to see whether
a larger model beats the local 4B one. Filed in [cloud-claude](cloud-claude/):
`RUN-RECORD.md`, the per-arm tables (`HAIKU-tables.md`, `STANDARD-360-tables.md`,
`SONNET-tables.md`, `OPUS-tables.md` and the two partial tables), `ledgers.json` (every
cost ledger plus totals per stage), `reports.json` (every per-cell report, bundled as for
sessions 1 to 4) and `KEPT-ON-RIG.tsv`.

- **Models and cells:** Haiku 5.5 on all nine cells and a 300-token re-run of its cut lines;
  Sonnet 5.5 on Fireside Brief; Opus 5.5 and Fable 5.2 on the three Standard cells.
- **Money:** $66.31 spent (the sum of the ledgers recomputes to $66.3119) against a cap of
  $75 set by the Director. The run halted once, at 19:38:14 EST, on the account's own spend
  limit, and resumed at 19:47 EST after the Director raised that limit. The key was deleted
  after the run and the test is closed; the run record carries that line.
- **Headline (the run record's figures):** on the three Standard cells every Claude model
  writes fewer lines that pass the rules as they stand than the local model (local 84.1%,
  Fable 5.2 80.7%, Opus 5.5 78.8%, Haiku 5.5 76.2%), mostly by the choice-parroting rule.
  Under the two checker changes of the session 4 re-score the order turns over (local 86.1%,
  Fable 91.5%, Opus 89.3%, Haiku 85.6%), at 9 to 19 times the local latency per turn. On
  Fireside Brief, Sonnet 5.5 is level with the local model (81.5% against 80.6%).
- **Not replayable byte for byte:** the API takes no seed and no sampling settings; instead
  every raw response is kept on the rig with its request id.
- **Left out of the repository:** the call logs and row files (raw Claude completions), halt
  files and stdout/stderr, the reading samples, scripts and logs. All are listed in
  `KEPT-ON-RIG.tsv` by relative name, bytes and sha256.
- **Ledger counts:** `ledgers.json` sums to 21,590 requests against the record's 21,464
  answered calls; the 126 extra are the 125 requests that never left the machine (TLS trust
  store, $0) and one halted request. Dollars agree.
- **Key hygiene:** the files filed here were searched for key strings; the only matches are
  the header name `x-api-key` in the run record's prose, never a key value.
- `[unverified]`: figures are the run record's own; no second check was run.

## Caveats the run records carry

- The all-rules counts for `draft_animal_species` in the two session 3 arms with the
  rulings prompt are an artefact (the harness re-checks with the shipped checker, which
  does not allow Fireside's "oxen"); the first-rule counts and the rates are not affected.
- Session 3's combination arm sampled at the model card's 0.7, not 0.15, and session 4
  re-scored its rows with new rules (a re-score, not a re-run).
- Session 4's latency arms overlapped other work on the machine; only the ship arm's
  and the CPU-only arm's latency figures are the clean ones.
- Session 1's request and seed in the rows were rebuilt after the fact by replaying the
  harness's own code with a recording transport; later sessions capture them as sent.
- The rates count rule passes. They do not say whether a line reads well.

## Studio relevance

relevance: `reference`. The result is for the ETV game's narrator build, and the
method (per-cell reports plus paired-by-turn differences against a pinned baseline) is
reusable. The decision the game side took from it sits in the run records' final sections.

Promoted: not yet.
