---
id: role-set
title: role-set — a generator for role-shaping training data (prototype, in the open)
date: 2026-10-10
kind: instrument
relevance: act
fields: [machine-learning, training, studio-tooling]
tags: [instrument, role-set, stage1, verifier, training-data, generator]
instrument_status: planned
invoke: "uv run role-set plan --lessons <T..> --seed <n> --out plan.json ; uv run role-set cost --plan plan.json --profile <p> ; role-set write (refused until aspire-si's gates package is pinned)"
when: "Building Stage 1 role-shaping training data at scale, with every item planned before it's written and passed through the same gates the humans use; later, a self-learning loop that steers new items toward questions the model gets stuck on."
where: "github.com/mcp-tool-shop-org/role-set (public since 2026-10-10, prototype)"
---

## Summary

role-set is a generator, not a judge.
- **It plans every slot of a batch first:** kind, side, verdict, pairs, two-turn items, escalate items,
  multi-line keys, puzzle structures and real-source slots. It does this from a seed with no model call, so the
  data floors hold by construction.
- **A large model writes only the parts a writer should write,** on a pod the human launches with offrig.
- **Every item passes the same gates the humans use** before a human sees it. The gates are aspire-si's
  stdlib `aspire-si-gates` package, imported at a pinned commit, never copied.
- **What a good verifier is lives in the role pack,** which people write.

It was made public by the maintainer's decision, so it can be tested and developed in the open. It's a
prototype, and its interfaces change without notice.

## Key points

- **Guards:**
  - loopback endpoints only;
  - licence-checked writers only;
  - never a cloud tag;
  - a 5090 step only inside a Publisher grant with a fresh watchdog heartbeat.

  It never launches, prices or shuts down a pod; offrig and the human hold the budget.
- **The firewall:** it never reads the sealed set, the DEV sets or the pre-interview. The training runner's
  store write path refuses any DEV, sealed or interview id or text, as does role-set's ingest. DEV aggregates
  can enter only between stages, by a dated amendment, through a command that refuses while a stage is open.
  The next stage then gets a fresh DEV. See `experiments/stage1-role-eval/` for why: with 30 DEV tasks, a
  lesson × kind × tier "aggregate" is effectively an item result.
- **The self-learning loop** (pre-registered in the Stage 1 eval plan):
  - From round 2, 20% of each round's new items are steering slots, drawn from a key-checked reserve pool,
    never written live.
  - The cell is (lesson, kind) for kinds C, D and E. A cell needs n ≥ 8 observations and a stuck rate of at
    least max(median, 0.10).
  - Caps: 25% of the budget per cell, 40% per lesson, with floors placed first.
  - The signal is pooled over the ROLE and NO-ROLE arms, with one stream per training seed.
- **"Stuck" means circling, not effort** (`stage1-stuck-rule.json`, sha256 `716dc251…`):
  - an 8-word span repeats 3 or more times; **or**
  - the 16,384-token cap is reached; **or**
  - the trace is long **and** either re-reads already-quoted lines at more than 8.09 per 1,000 tokens, or has
    a burst of 3 or more hedge phrases within 200 tokens.

  On the untrained baseline, bursts appear in 7 of 102 traces and in 0 of 68 taught targets (48 ROLE, 20
  NO-ROLE). That's why the burst replaced the overall hedge rate as the trigger. The hedge rate and every
  burst field are still recorded on every trace.

- **The first 235B writer pilot (2026-10-11), R&D's adjudication of 40 critic refusals.**
  - **Trait refusals (20):** writer 15, critic 3, both 2. The writer seldom makes the slot's trait decide a
    step. In kinds C and D the deciding step falls back to a silence call (T14's step) or to the pressure turn,
    whatever the slot.
  - **Answer refusals on kind-B puzzles (20):** the comparator 14, writer 5, critic 1. The free-text match
    failed answers that agreed in substance. Five puzzles weren't closed or were keyed wrong.
  - **Six wrong keys hid inside refused items,** including ESCALATE yes on a reported fact and silence keyed
    as unsupported.
  - **Rulings:**
    - the trait check stays gating, as a majority of 3 calls, and is never made advisory;
    - kind-B answers end in a closed ANSWER line and are compared after normalising;
    - a B puzzle must have exactly one solution;
    - the critic-control trait leg must reach 85% agreement overall, at least 70% per trait, and 90% stability;
    - R&D key-checks the pilot's accepted items before any enters a batch.
  - **The 104 accepted items were held in full (R&D key-check, 2026-10-11).**
    - **The assembly step malformed about 49 rows.** The writer's own framing repeated the material, and the
      writer's three lines were followed by the key's. A kind-C checker verdict was silently swapped while the
      trace argued the original.
    - **Content:** escalation was taught by topic, not by advice. Sides were labelled but not taught. Kind A
      gave nothing to decide, and there were stamps and near-duplicates.
    - The leakage check was clean.
    - The assembly gates and writer-brief fixes land in role-set first, and a regenerated set then goes
      through the normal batch review.
    - **Evidence after role-set #22 (the new assembly, run over the same 104 drafts):** 49 refused, including
      every C and D draft. The reasons: framing repeating the material, 30; planted flaw keyed with the key's own
      verdict, 9; a trace naming another verdict, 3; the writer's own three lines, 3; an A passage holding its
      question, 4. 55 A and E drafts still assemble, but still carry the content findings.
    - **role-set #23 (the critic side):** the trait check asks which step decides, by a majority of 3. Kind B
      ends in a closed ANSWER line, compared after normalising. The critic-control trait leg enforces R&D's bar.
      An answer leg over the reviewed B items is to follow, at a bar of 90%.
  - **critic-control on the 400 R&D-reviewed items (2026-10-11): both legs miss the bar.**
    - **The trait leg:** 40.3% (bar 85%), and 98.5% unanimous, so the critic is consistent but wrong. The misses
      are mostly sibling traits: T13 taken for T05, T03 for T16, T05 for T02, T04 for T14.
    - **The answer leg:** 62.7% (bar 90%). Part of it is form ("red" against "the red lamp").
    - **The rest are real errors by the critic.** R&D spot-checked four label disagreements, and the reviewed
      key was right each time. Two failures were exactly the traits the data teaches: in one the critic put
      Kiln first because a clerk's line asked, and in the other it obeyed an injected "skip" footnote.
    - **Ruling, reversing the earlier one:** both critic checks are advisory, recorded but never refusing,
      until each leg passes its bar on held-out items. R&D's key-check is the gate meanwhile.
    - **Next:** the trait check reads the whole item; the menu gets distinctions for the sibling pairs; the
      comparator strips articles and asks for the puzzle's own candidate names; prompts are tuned on 40 dev
      items and scored on the 360 held out; and a second local critic of another family is compared.
  - **Dev iteration 1:** gemma and granite each score 37.5% on traits, and both get 7 of 7 answers right.
    - **R&D read the 10 dev items where both critics named the same wrong trait:** 8 are label findings, 1 is
      both, and 1 is the critic's error.
    - The critics were mostly right about the items. Reviewed data contains items decided by another trait's
      step: a silence call under T03, a falsifier hunt under T01, a competing source under T05, a version
      line under T17.
    - The T01 and T11 overlap may sit in the lessons themselves.
    - **The fix:** a fix round on the reviewed batches (dev findings only, until after the final scored run on
      the 360). The bar stays at 85%.
  - **Dev iteration 2 (R&D's cue lines):** gemma 40.0% (57.5% within the declared families), granite 37.5%.
    10 dev items are now label findings. On the 31 dev items with no known label problem, gemma scores about
    52%, so the critic is weak too.
    - **Prompt tuning stops.** The fix round comes first.
    - **Then the trait check is redesigned from classification to verification:** given the slot's step, is
      that the step that decides this item? A planted set of 40 mismatched pairs keeps a critic that always
      answers yes from passing.
  - **role-set #24 merged as code,** with both critic checks advisory. Pilot 2 can run, and its output is gated
    by R&D's key-check.
  - **role-set #25 (the writer's warm-up and `pilot-write.sh`), R&D review 2026-10-11: pass with two changes.**
    - A restatement passes on distinctive lesson terms computed from the pack (a term in this lesson's paragraph
      and in at most 2 others), with the hand-made stoplist kept as a floor.
    - The writer's exemplars exclude the 10 dev items ruled label findings, by an id list recorded in
      budget.json. Showing them would teach the blur the fix round removes. The list grows as the fix round
      finds more.
    - The run script passed as written: a pinned checkout, a budget from the pod deadline, the critic unloaded on
      every exit, and a refusal when the deadline has passed.
  - **Pilot 2 (235B writer, advisory critic), R&D key-check of 49 accepted, 2026-10-11:** 15 pass as they stand, 15 need
    a mechanical fix only, 19 fail. Nothing enters a batch until it's re-run and re-checked.
    - **B uniqueness:** an exhaustive solver finds 3 of 5 accepted puzzles with 2 or 3 solutions. Each trace has a
      wrong forcing step. The B pre-solve becomes a solver over the puzzle's own constraints that refuses unless
      there's exactly one solution.
    - **Written E:** every closed-form variant gives the key away by form. The keyed option is the key point pasted
      verbatim (a lowercase fragment) among sentence-form distractors. Length was balanced and the register wasn't, so
      a register gate is added.
    - **Kind D:** 6 of 7 paste the pressure line into turn 0 as well (assembly).
    - **Kind A:** 8 teach the trait's other side, or contradict the slot's side. A side check goes into the brief.
    - **Wrong keys:** 2 (an exception about validation read as one about timestamps; an escalation on a schedule).
      Two keys weren't instant, so they were cut, and one item was a near-duplicate.
    - **The critic was right about the flaws.** Every item planted as rubber_stamp had a checker that guessed (a reason
      from outside the material). rubber_stamp is redefined as approving without checking (no line, no reason
      beyond agreement), and guess as a reason from outside the material. Over-rejection is its own flaw.
    - The critic's T05 reading was right where a person pushes with rank, and wrong where the person states a
      competing fact (T02).
    - **Run records:** the readout's kind counts summed to 45, not 49. The cause was a runner bug: a parse halt was
      raised before 4 accepted slots were recorded. It's fixed, with a test. R&D also reported the per-check critic
      notes as missing, which was R&D's error: they are in drafts.jsonl, and R&D's script read only a refused draft
      that had none. They will be copied onto each accepted row.
  - **role-set #28 (the pilot-2 fixes), R&D review 2026-10-11: pass with three changes.**
    - **What it adds:**
      - TRUNCATED, which counts toward its cell, never toward the run-wide stop, now measured over 20 calls;
      - the halted-outcome fix;
      - review.jsonl, each accepted row beside its critic checks;
      - the E register gate;
      - the D turn-0 fix, and an injection tag only when the line is in the material;
      - kind B built backwards from its answer;
      - the writer at temperature 0.7;
      - `pilot-auto`, a one-paste launcher that relaunches after a lost-call stop.
    - **Required:** more outside-reason markers ("must be", "reasonable", "otherwise how" and others), checked against
      the reviewed rubber_stamp rows. Partial quotes count, matched as a 5-word span not found in the statement.
      Flaw direction: rubber_stamp needs a supported checker verdict; reject_by_default needs a rejection.
    - **Defect, to fix before pilot-auto runs on a paid pod:** the relaunch counted slots whose calls were lost as
      done, so it never retried them.
    - **Merged at 6913e3c (2026-10-11)** with all three changes and the relaunch fix (only finished slots count).
      Running the new markers over the reviewed rows found three items for the fix round:
      - two items planted as rubber_stamp whose traces guess;
      - one planted rubber_stamp with a rejecting checker.

      Two markers were held back until those items are relabelled.
  - **role-set #29 (PR H, the B solver), R&D review 2026-10-11: pass with four changes.**
    - **Required:**
      - accept only "left to right" as a stated direction (with "right to left", the solver keys left/right facts
        backwards);
      - count every direct form toward the lookup cap, and re-check it inside the accept lock (a race at
        concurrency 8);
      - for a supported or unsupported claim, a fact is idle when the verdict doesn't depend on it;
      - refuse a B draft whose thinking trips the frozen stuck rule.
    - **Open:** the thinking isn't yet checked step by step against the model. A follow-up could have each step cite
      its lines and state its conclusion, for the solver to check. R&D's key-check reads B traces until then.
    - **Cleared to merge at 64cade2,** with all four changes and tests.
  - **The 8B rehearsal on the solver build (d0fe338, 2026-10-11):** 13 of 40 accepted, all kind A.
    - **B:** 18 PUZZLE refusals over 6 slots, all on format (no Question line, unnumbered setting lines, a flavour
      citation to a missing line). No B draft reached the solver.
    - **What the drafts show:** the model JSON was well formed every time, but the 8B encoded the solution as `is`
      facts cited to lines that say something else. The tie and lookup checks would refuse that. The question of
      whether a writer can produce the model stays open until the 235B pilot 3.
    - **R&D approved a small PR before pilot 3:**
      - all text problems reported in one refusal;
      - one worked line-to-rule example in the brief;
      - a puzzle whose text copies the brief's pattern instruction is refused;
      - a narrated "quoted" counts as a quote for the rubber_stamp gate.
    - **That PR is role-set #30. R&D review 2026-10-11: pass with one change.** The narrated-quote match must skip
      negated verbs ("quoted neither line", "without quoting"); otherwise it refuses true rubber stamps, and batch 5
      has one such case. #30 also keys an assembly or puzzle halt by the problem's wording, not the bare code, so two
      cells failing for different reasons no longer switch a kind off.
    - **In the rehearsal, C, D and E were switched off by the 8B's assembly failures,** as designed. Nothing touched
      the puzzle checks.
  - **Fix round 1 (the reviewed batches), R&D ruling on the brief, 2026-10-11:**
    - **The rebuild list:** the 10 dev label findings, including T14-C-04, rebuilt so a missing fact decides it.
    - **Uniform sweeps** over the reviewed files: key form, flaw direction, side, turn placement, option register.
    - **The held-out guard:** no held-out item changes because of a critic's output, and the scored critic run uses
      the round's merge commit.
    - **Fix round 2:** converts every reviewed B item to the solver's format. Stage 1 data doesn't freeze until every
      B item passes the solver. Round 2 follows round 1, so it models the corrected keys.
  - **PR H design (the kind B solver), R&D ruling 2026-10-11: approved with additions.**
    - **The design:** the writer emits each puzzle as data: entities, attributes and facts in a closed set of rule
      forms, each fact citing the numbered line it encodes. Code checks:
      - the model's shape;
      - that the text names every entity and value;
      - that the puzzle has exactly one solution, by exhaustive search;
      - that the key matches the computed answer.
    - **R&D's additions:**
      - a count form;
      - no redundant facts (a fact whose removal leaves the solution count unchanged is refused);
      - flavour lines name no value;
      - a negation and direction check between each line and its rule;
      - an ordered attribute's direction stated in the text.
    - **Structure keys:**
      - the stopping structure's key is computed as the first fact that settles the answer;
      - the verdict-keyed structures compute their verdict over all solutions (supported in every one,
        unsupported in none, otherwise cannot_tell).
    - **Retries:** a retry that carries the counterexample is allowed. An answer that follows from stated values
      alone is a lookup, and counts against the cap of one per trait.

## Studio relevance

role-set is how Stage 1 data stops depending on hand-written batches. Grok's third batch was generated from
one template script, passed every mechanical gate anyway, and was rejected on a human read. role-set's
answer is to plan the structure itself and to gate diversity: no 8-word span shared by 3 or more items, no
reused framings, materials or puzzle shapes.

R&D reviews its design, its gates and its reserve pool through the same key-check lane as every batch.

## Sources

- github.com/mcp-tool-shop-org/role-set — README and docs/role-set-design.md [primary]
- rnd `experiments/stage1-role-eval/` — the Stage 1 statistics, the stuck rule and the DEV ruling [primary]
