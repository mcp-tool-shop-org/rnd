# Track B: exact flaw labels — design v2

**The Director approved Track B v2, 2026-10-22** (about 31 central, 37 high, from phase 5). T10's critique window has priority for units; if Track B and T10 together would cross 150, it goes to the Publisher before launch.

v2 folds in Argon's v1 review (CONDITIONAL PASS, 2026-10-22): F1–F4, adopted in full. The changes are marked [v2].

R&D, 2026-10-22. The template is [Diagnose, then fix](rnd handbook `diagnose-then-fix.md`), which inherits every
A/B check. **The trigger:** Track A failed (PLAN-ROUND4 §4). The Director chose option 1 with Track B next,
2026-10-22. This is design only: no run and no spend until the Director approves it and Argon has reviewed it.

## Standards compliance

| Standard | Score | Evidence |
|---|---|---|
| PIN_PER_STEP | 2 | Each window pins role-set, gates, the items' sha, the card, the GGUF and the flaw-label text by sha. |
| ANDON_AUTHORITY | 2 | Rung failures, the gold-check floor and the Publisher's stops halt the study before spend. |
| NAMED_COMPENSATORS | 2 | No irreversible step beyond Colab spend. Each window has a cap and a deadline cut, and a resume replays its journal. The owner is the Publisher. |
| DECOMPOSE_BY_SECRETS | 2 | Labels (the fix) are separate from items (the banks) and from scoring (the decision rule). |
| UNCERTAINTY_GATED_HUMANS | 2 | The Director's go is needed before stage 2. Step-5-style escalation applies if the result is noise-bounded. |
| EXTERNAL_VERIFIER | n/a | No specialized claims. Argon reviews the design as usual. |

## 1. The check, in three sentences per stage

- **Stage 1 (diagnosis):** on bank D, find which trace features make Muse name a flaw on sound traces, and how noisy
  its flaw call is. Bank D is phase 4's and Track A's items, already scored, so this is free. The two Track A runs give
  one repeat each.
- **Stage 2 (verification):**
  - **Baseline:** today's labels: `FLAW_DEFINITIONS` as in Track A's old prompt, scored as Pc.
  - **Treatment:** only the pre-registered label fixes from §6.
  - Both arms run fresh on a locked bank V that neither has seen.
- **Why it answers the question:** the arms differ only in the label text, so a fall in planted-none false refusals,
  with planted-flaw catches held, is the labels' effect.

## 2. Stage 1 inputs (free)

- **Bank D:** phase 4's 80 GPU items and Track A's 102, with both Track A runs' replies.
- **The first input:** R&D's look at "guess" on sound traces
  (`rnd-local/critic-signal/track-a/guess-on-sound-traces.md`).
  - No sound trace hedges.
  - Muse calls a forced one-step inference from a stated line a "guess": arithmetic or time against a stated range,
    a direct consequence, a synonym.
  - About half the traces paraphrase.
  - The flaw label flipped between runs on 5 of 12 such items.

## 3. Planted defects (stage 1)

Bank D's planted-flaw items (guess, loop, nitpick, rubber_stamp) stand as the planted faults. A fix that stops false
"guess" calls must keep catching real guesses: "usually", "most centres", general knowledge.

## 4. A blinded read (stage 1)

- **[v2, F3] Which traces:** all 43 Track A d controls (22 planted-none and 21 planted-flaw), shuffled, with ids,
  planted flaws and the critic's labels hidden. Not only the 12 flagged ones.
- **Scripts first:** a pre-pass computes exact substring matches of at least 4 words against the material, plus lexical
  markers ("because", "this means", "so", "synonym", "usually", "typically", "most").
- **Binary tags, each a 0/1 rule, defined before the read:**
  - `verbatim_quote`: a span of at least 4 words that's a substring of the material;
  - `paraphrase`: a stated line restated without a verbatim span;
  - `forced_inference`: a one-step comparison against a stated range, time or date, a direct consequence, or a
    synonym;
  - `outside_premise`: a claim the material doesn't state, such as usual practice or general knowledge;
  - `hedge`: "doesn't say", "can't be sure", or a refusal for lack of an explicit line.
- **Who reads:** one blinded read by R&D. Argon judged a second reader unnecessary for a 43-item diagnostic table.

## 5. The split, locked

- **D:** phase 4 and Track A items, which are tuned and seen.
- **V:** fresh kind C base rows written for Track B (§8), about 48: 24 planted-none and 24 planted-flaw.
  - Slots used by neither phase 4 nor Track A, where the census allows. Otherwise the same slot id with a fresh seed,
    domain and material; D and V never share material or traces.
  - **[v2, F2] The item families:** V's base rows are expanded into the a–g families by perturb.py at seed 0, exactly
    as Track A was. That gives the d controls plus the b, e, f, g primary pool, and the offline a and c types.
  - The plan seed and slots are frozen before stage 1 ends. V isn't written until the fixes are frozen in git.
- **No re-scoring of D** as evidence.

## 6. The symptom-to-fix table, fixed before stage 1 reads

| Symptom | Permitted fix (labels only) |
|---|---|
| A forced inference from a stated line is called "guess" | "guess" excludes a step the stated line forces: comparison against a stated range, direct consequence, plain synonym. "none" says so explicitly. |
| A faithful paraphrase is called "guess" | "none" allows a faithful restatement of a stated line as well as a verbatim quote. The inner checker isn't required to quote (Argon Q1). |
| [v2, F4] A paraphrasing approval is called "rubber_stamp" | rubber_stamp's "quoted no line of the material" becomes "cited or restated no line of the material". |
| [v2, F4] A contradiction by a stated time, date, range or rule is called "reject_by_default" | "none" states that concluding unsupported when a stated time, date, range or rule contradicts the statement is sound, not reject_by_default. |
| An outside premise is not called "guess" | Keep and sharpen "guess" = a premise the material doesn't state (usual practice, general knowledge, an assumption). |
| The flaw call is unstable on sound traces | Scoring change, not label: the flaw call is sampled 3 times at the card (seeds 0, 1, 2). **[v2, F3] The vote is binary:** the flaw leg refuses if and only if at least 2 of the 3 return a label other than "none". Exact-label diagnostics need 2 of 3 matching labels. Fixed sampling is excluded (the card). |

Any fix not in this table needs a dated amendment, before V is written.

**Scope (for Argon):** the labels appear in two places, the critic's flaw prompt and the lessons that teach the flaw
names (gold keys and slots). Stage 2 tests the critic-prompt labels only. Rolling them into the lessons is a separate,
later change, made only if stage 2 adopts them.

## 7. Attribution (stage 2)

The treatment must show the targeted symptom fell: planted-none false refusals naming "guess", by the trace feature
tagged in §4. A better score with "guess" on forced inferences flat isn't attributed to the labels.

## 8. Stage 2, fresh and interleaved

- **Write:** one Gemma write window for bank V's about 48 kind C base rows, at Track A's measured rate. About 13 units.
- **[v2, F4] Critic:** the P0 verdict leg runs once per V item, about 6.3 units. Then 3 flaw samples per item run for
  the baseline (old labels), about 5.7 units, and 3 for the treatment (Track B labels), about 5.7 units. That's about
  18 for the critic in all.
- **Order:** the flaw samples are interleaved in a seeded order. Both arms share the one verdict leg.
- **Total:** about 31 central, high about 37. Phase 5 has about 150 − 30.3 (Track A) − ~52 (T10) ≈ 68 left.
- **Code:** stage 2 needs role-set to sample a flaw call 3 times and score the binary vote, and the Track B label text as
  a setting (like `--flaw-prompt`). That's a build PR with an Argon code round before any window.

## 9. The verdict, by stratum (pre-registered)

As Track A, with the shared verdict leg:
1. **[v2, F1] Both 3-vote arms against the shared P0:** Pc-trackB and Pc-old, by exact McNemar on the primary pool,
   with Holm over the 2 tests.
2. **[v2, F2] The control bar, per stratum,** on the **flaw leg's** false refusals: at most 10%, so at most 2 of 24
   on planted-none and at most 2 of 24 on planted-flaw. The shared P0 verdict leg doesn't count against it, because
   it's identical in both arms. Total Pc false refusals are reported beside it.
3. **[v2, F1] Adoption:**
   - If one 3-vote arm qualifies, adopt it.
   - If both qualify, adopt Pc-trackB when its worse stratum, max(r_none, r_flaw), is strictly lower than Pc-old's. If
     they tie there, adopt Pc-trackB only if it is strictly better on total control false refusals or on primary
     catches. Otherwise adopt Pc-old (3-vote), by parsimony.
   - **Fixed precedence** (Argon round 2): the tie-break is evaluated lexicographically as (max(r_none, r_flaw),
     r_none + r_flaw, −primary catches).
   - If neither qualifies, nothing is adopted, and the options go to the Director.
   - The 1-vote slice (seed 0) of both arms is scored as secondary attribution.
   - With one verdict leg by construction, Track A's concordance split can't arise.
4. **Reported beside it:**
   - the noise floor: how often the 3 flaw samples disagree;
   - catches by planted flaw;
   - the symptom table's attribution.

## 10. Total cost of ownership

Report:
- the label text's length change;
- the extra flaw calls (×3);
- the units spent;
- whether a simpler rule would give most of the value. **[v2]** A deterministic "forced inference" scorer carve-out is
  scored post hoc here, at no cost, and never as an arm. Argon warned it would overfit D and open a hole for planted
  guesses.

## Questions for Argon

v1's questions were answered in Argon's review of 2026-10-22, and v2 adopts the answers. Argon's round 2 (2026-10-22) found F1–F4 resolved, with no findings: PASS.
