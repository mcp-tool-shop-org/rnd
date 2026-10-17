# Using the dataminer's records in role-set: design note (draft)

**Status:** draft, 2026-10-16. Nothing is built. **Input:** the `generations.jsonl` record every writer and critic
call now writes, in `rnd abmine`'s format (tokens plus top-5 log-probabilities per step; handbook "the generation
record"). **Owner:** R&D for the analysis in `rnd abmine`; the Publisher for the role-set wiring. **Start:** after the
Colab pilot, which produces the first records.

## Priority 1: point the key check at uncertain items

- **Signal:** the writer's margin at the keyed decision tokens. That's the verdict word (supported, unsupported or
  cannot_tell), the ESCALATE answer and, for kind B, the answer token: the log-probability gap between the chosen
  token and the runner-up.
- **Use:** R&D's key check takes the lowest-margin items first, plus a random share (25%) so the check still
  measures the whole set. Each item's margin goes in the key-check sheet.
- **Test before relying on it:** on the pilot, compare the key-error rate in the lowest-margin quarter with the
  rest. If low margin doesn't predict errors, the ordering is dropped and the random check stays.
- **Where:** a small `rnd abmine margins` step over the record and the accepted rows, writing a ranked list.

## Priority 2: check that hosts agree

- **Signal:** Δz and the fork point (abmine's existing analysis) for one fixed prompt set, run greedy on every host
  that serves a pinned model: Colab A100, RunPod H200, B200.
- **Use:** before a host's first counted wave, a 10-prompt greedy smoke run is compared with the reference host's
  record. If the step-0 Δz isn't zero, or the forks come early, the host is held (andon) until it's explained. The
  same binary, libraries and GGUF should agree closely; a mismatch means the stack isn't what the pins say.
- **Where:** a `--wave host-check` mode in the wave scripts that writes the record; `rnd abmine analyze` reads it.

## Later

3. **Confidence-aware critic gates:** a critic refusal with a small margin at its verdict token counts as advisory
   and is logged, not a refusal. That needs the critic-control data first, to set the margin threshold.
4. **Copy detection:** a long run of near-certain tokens (for example, 12 or more tokens each with probability
   above 0.98) that also matches an exemplar or lesson span is flagged for the lesson-copy check. It's a flag, not a
   refusal, until the pilot shows its false-alarm rate.
5. **Writer fingerprinting** (dataset-builds template §6, item 5): per-writer statistics (mean entropy, margin
   distribution) as features for the generator-identity probe. It's a report.
6. **Defect evidence:** each refusal in role-set's `defects.jsonl` gets the step span where the writer's margin
   dropped, to help diagnose recurring defect classes.

## Standards

- **PIN_PER_STEP:** each analysis records the record's sha256 and the abmine version.
- **ANDON_AUTHORITY:** priority 2 can hold a host.
- **The rest are reports**, until a pilot measurement justifies gating on them.
- **EXTERNAL_VERIFIER:** n/a.
