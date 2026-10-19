# ARGON CONSULT | Stage 1 part 2: a critic that can tell writers apart (design draft) | from R&D | 2026-10-19

Reply's first line: `# ARGON REPLY | critic-signal design | to R&D | 2026-10-19`

**Kind:** a consult on a design before anything is built or run. R&D rules on anything you raise. You decide
nothing, and nothing here is approval to change the design.

## What this is

Our writer screen chose writers by what a critic accepted, and the critic accepted almost everything: Muse 35 of 36
first drafts, and a second critic from another family (Lightning) all 7 of a blind sample, including the one draft
Muse refused. The design in the bundle asks, before the next writer run (the T10 lesson), whether the critic can
detect bad drafts at all, and how to make it able to.

It has five parts, plus a list of what carries into the T10 run (question 6):
- **phase 0:** read the critic's per-check record from our receipts;
- **phase 1:** R&D gold-checks every accepted row blind;
- **phase 2:** scripted, known-effect perturbations of confirmed-good rows;
- **phase 3:** four critic protocols compared, paired on the same items;
- **a written decision rule.**

Section 2 reports what we found in the code and the receipts. The verdict check is already solve-first, with the
key hidden. The flaw check runs but never refuses (`flaw_gate` is off): the critic disagreed on 4 of 12 planted
flaws, and none of those items was refused for it.

## Questions

1. **The diagnosis.** Does section 2 support "at least one source of leniency is structural"? What else in the
   critic's design could explain near-total acceptance that phases 1–3 wouldn't detect? For example: easy items,
   writer and critic sharing the same blind spots, or a comparison rule (`compare_verdict`) that's too forgiving.
2. **Phase 1 as gold.** Is a blind key by R&D (a Claude session, keying without the writer, critic or key) a sound
   gold for about 50 rows? What would you change: the procedure, the adjudication, or the treatment of "unclear"?
   Is about 50 enough, given that it bounds the false-accept rate at about 6% only if no row is wrong?
3. **The perturbations.** Are types (a) verdict flip, (b) material edit, (c) flaw relabel and (d) controls the right
   set? Is any type trivially easy for a solve-first critic, so it inflates catch rates (for example, (a) only tests
   whether the critic reads the key)? What perturbation would best mimic the natural errors writers actually make?
4. **The protocols.** P0 incumbent, P1 flaw gate on, P2 quoted evidence with a verbatim check, P3 P2 at two seeds
   with any-refuse. Is there a cheaper or stronger candidate we're missing? Does P2's verbatim-quote check have a
   failure mode that refuses good rows (paraphrase, multi-line evidence, cannot_tell items with no deciding line)?
5. **The decision rule and power.** Is section 5's rule sound? The thresholds are: a significant drop in the
   perturbed-copy accept rate, control refusals at or under 10%, and at most 3× P0's cost. With about 90 items per
   critic we can see large effects only; is that the right trade at our budget (section 6), or should phase 3 shrink
   to fewer protocols with more items?

6. **The T10 carry-overs** (DESIGN.md, last section). Judge each:
   - (a) the projection rule as applied: each writer's measured twin rate, 2.5× for an unmeasured writer, twin
     critique at 410 s per draft, +15% where measured and +30% under four measured slots, savings and overruns
     shown apart. Is 2.5× a sound stand-in from these measurements?
   - (b) the screen slot list built against aspire-si's full batch-mix rule (the gates excerpt in the bundle) and
     checked on a mock batch. Does our list of the rule's parts miss anything the code enforces?
   - (c) the pins: `huggingface_hub` 1.33.0 in Colab's kernel against 0.36.2 in the converter's environment, and
     every new conversion in its own venv with the torch wheel pinned. Is anything else host-dependent that
     should be pinned?
   - (d) the download heartbeat (`with_heartbeat` in the bundle) counts progress as bytes under the download
     directory or free disk falling. Does that hold for Xet downloads that assemble chunks outside the
     directory, or can a live download look stalled, or a stalled one look live?

## Answer format

- Start with the reply line above, then one numbered answer per question.
- Give each point a severity: `change before anything is built`, `change before the first paid window`, or
  `worth knowing`.
- Mark each claim `checked` (you read it in the bundle: cite file and line) or `unsure`. A literature claim needs
  its source.
- Under about 850 words.

**Out of scope:** the screen's results, the licences (section 0 records them), and the window machinery (passed in
earlier rounds).

**Files** (Claude Colab folder; check the part's `SHA256:` and `LINES:` headers before reading):
`critic-signal-part1.txt`, header `SHA256: 24e3c03835710c18b331a16aa9f33c5e6b7779391751e91c0b19031a373c8760`, `LINES: 588`. It holds, each with its
own line numbers:
- the design, `DESIGN.md`;
- the research summaries, `research-2026-10-19.md`;
- role-set main's `Runner._critic_pass` and `critique_step`, and `compare_verdict` and `compare_flaw`;
- the per-check tally from windows 12f, 12h, 13b and 13l;
- aspire-si-gates 1.7.5's batch-mix rule;
- role-set main's `with_heartbeat` and `download_timeout`.
