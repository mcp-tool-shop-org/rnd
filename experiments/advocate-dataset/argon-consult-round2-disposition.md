# Argon consult, round 2: the answer in R&D's words, and the disposition

**2026-10-14.** The consult is `argon-consult-round2.md` (R&D's adversarial pass, with the 1.1.8.2.3 brief inline). The Director carried it to Argon (browser, no repository access) and the Publisher summarised the answer. **Argon's verdict: hold, for six named changes, before a seat is assigned.** R&D takes all six and the eight further findings. The brief at 1.1.8.2.6 carries them.

## The six changes, and what they fix

1. **A deterministic prose-to-block verifier.** The attack: a brief that contains every block string in the right section and still flips a gate's polarity ("non-blocking"), waves a tripwire away, or overrides the action ("merge anyway"), or slips in an invented number. The fix: section-pinned containment, no unbound number or gate name, a ban on negation and minimiser tokens within five tokens of a failed gate, a tripwire or the action (the label itself excepted), and the critic's first leg re-deriving the block from the prose alone.
2. **Masked negatives by counterfactual substitution, with parity.** The attack: masking the only failed gate makes the writer honestly write "all passed"; masking empties a section so `none` appears only on negatives; each mask shortens the brief by one clause. The fix: `figure_altered` and `claim_invented` from a mutated ledger; `gate_hidden`, `ask_dropped` and `tripwire_hidden` with the masked fact replaced by a promoted immaterial note (or an immaterial note masked on positives at the same rate); a gate or tripwire masked only where the record has two or more, or the rate of `none` matched.
3. **An affine word ceiling.** The attack: 40% of a 60-word record leaves no room for the section frames; 40% of a 600-word record copies freely. The fix: min(45 + 14 × material facts, max(75, 0.45 × record words)), plus a ban on any eight-word run copied from the record.
4. **Two tiers of rules.** The attack: a decision rule printed in every record teaches that standing rules apply only when restated, and that an inline note can override them. The fix: standing rules always apply and are never overridden inline; task-local thresholds on about 60% of solvable records; at least 30% of records restate nothing; at least 12.5% of A and C are `cannot_tell` because the task-local threshold or tie-break is missing while every figure is clean.
5. **A precedence table for the action.** The attack: `hold` and `pilot_first` overlap on every un-piloted proposal. The fix: gate failed or non-spend tripwire → hold; over the cap or a paid API → hold; execution requested without a passed pilot → pilot_first; with one → proceed; nothing requested → proceed; `pilot_first` only on execution-proposing record kinds.
6. **Recombinatorial harvesting and a harder overlap gate.** The attack: cloning one incident's field tuple retells a real sequence of failures with the numbers changed; a five-word exact check misses a four-word idiom with a synonym, punctuation variants and distinctive constants. The fix: harvest marginal distributions and pairwise compatibilities only; normalise and lemmatise, then refuse any four-word run or 60% non-stopword overlap in a ten-word window, role titles and schema terms allow-listed.

## The further findings, also taken

- **Local writers:** families split 50/50 within every (kind, verdict, planted class) cell, at most 55% from one; after five failures the same family retries with a new seed, never a failover; a prose-surface gate (each section's top opening four-word run in at most 15% of a file's items) against template collapse.
- **The pack:** `rules.md` as conditional gates with a green-light clause; "longer" cut, "confident" merged into `cannot_tell`'s counterweight, "clear to proceed" and "hold under pressure" added, every trait with a counterweight.
- **The exam:** a hand-written natural exam of 48 items (12 per kind), no generator code, no model prose; R&D writes the items and keys, the Director signs off on a sample; both exams must pass.
- **The critic:** two stripped legs (prose → block; record prose + brief prose → alignment and verdict), a different family from the writer, temperature 0, JSON-constrained, calibrated on 64 items (8 split-brain) before any refusal: re-derivation ≥ 95%, false refusals ≤ 5%, false passes 0% on missed gates and tripwires and ≤ 5% overall, family difference ≤ 5 points.
- **Sentence 2 for kind B:** whether a paraphrase relayed a proposition was a matter of opinion; a unique lexical anchor per proposition makes it code.
- **Sentence 3, relationally:** every single-side probe at chance still allows "fewer numbers than the record means a hidden fact"; immaterial figures in every record and a six-feature relational probe at chance close it.

## Changed or qualified

- **Section 0a's peer-approval line** was reworded in the fold-in, at the Publisher's flag, so it cannot read as the Director's phrasing.
- **Critic models** are local or through offrig only, never a paid API. A quantised 70B is fine locally if it fits the 5090; the seat chooses from what fits.
- **The natural exam's keys** are R&D's; the Director reads a sample, not all 48, unless he wants to.

## Not taken

Nothing. Round 2 raised no finding R&D disputes.

## Pass 3

Argon reviews the revised brief for the six changes in the text without contradictions between the plan's quotas and the skeletons, and the kind B role scope table (deterministic, non-overlapping). After the free pilot, Argon reads the 16 items for the ceiling, the prose-to-block check, template collapse and retry bias.
