# Offline re-score under the two agreed checker changes (2026-11-13, about 19:57 EST)

No model call. This re-scores lines already written, so that every comparison after the
narrator-fixes PR stays like for like.

## The two changes (both behind experiment arms; the game's checker is unchanged)

- **`parrot-verbatim`**: choice parroting rejects only a line that copies the whole choice label
  (two words or more) word for word in a row, or 5 or more of its words in a row. Words are
  compared lowercased and trimmed of punctuation, with no stemming. A line that names what the
  party did passes. **A one-word label is never a parrot** (R&D accepted this call).
- **`opening-three-words`**: the repeated-opening rule compares the first three words, not two,
  and a line that opens with one of the lead's own subjects is exempt. **Exempt subjects:** the
  party, a traveller, the last, the turn (every subject the lead builder emits) and the wagon
  (named in the ruling). R&D accepted this list.

Code: local branch `feat/narrator-fixes` (from rust-2.0 `a3fb14ef`), uncommitted at the time of
the re-score; debug build of the throwaway test `rescore_checker2.rs` (kept in
`fallback-runs/rescore-checker2/`, not in the repository).

## Method

Each arm's rows are walked in turn-set order. Every slot that holds a line (accepted, or rejected
by a rule) is re-checked with the arm's own checker plus the change, carrying the run's "previous
opening" memory forward from the lines the re-score accepts (reset when the run changes, as the
harness does). A slot that fell back can be rescued only by the one line its row kept (the last
candidate): the local harness did not keep earlier candidates. So "after" is a **lower bound**.
The same walk run without the change must reproduce the recorded statuses: it does exactly on
every arm that was not spliced together (0 status mismatches). "Good" is unchanged: accepted and
breaking none of rules 1a to 1e.

## Good lines, before and after (% of all lines asked)

| arm | lines | recorded | after | replay mismatches |
|---|---|---|---|---|
| s3 combo | 6,480 | 78.1% (5,059) | 78.2% (5,067) | 0 |
| s4 lead | 6,480 | 86.7% (5,615) | 87.0% (5,636) | 0 |
| s4 swh | 6,480 | 83.2% (5,390) | 85.3% (5,525) | 0 |
| s4 ship | 6,480 | 82.9% (5,374) | 85.7% (5,555) | 0 |
| Haiku 5.5 as run | 6,480 | 76.7% (4,969) | 85.4% (5,534) | 0 |
| Haiku 5.5, cut lines re-run at 300 tokens | 6,480 | 78.9% (5,115) | 87.7% (5,685) | 39 (splice) |
| ship, Standard, first 114 turns per voice | 684 | 83.8% (573) | 86.3% (590) | 0 |
| Haiku, same | 684 | 77.9% (533) | 86.1% (589) | 0 |
| Opus 5.5, same (partial arm) | 684 | 80.8% (553) | 89.8% (614) | 0 |
| ship, Fireside Brief, first 142 turns | 284 | 81.0% (230) | 85.9% (244) | 0 |
| Haiku, same | 284 | 79.2% (225) | 87.3% (248) | 0 |
| Sonnet 5.5, same (partial arm) | 284 | 82.4% (234) | 88.7% (252) | 0 |

Paired by turn against ship, both re-scored (95% interval):

| arm | after, paired vs ship (points) |
|---|---|
| ship after vs ship before | +2.8 (+2.2 to +3.4) |
| s3 combo | -7.5 (-9.8 to -5.3) |
| s4 lead | +1.3 (+0.0 to +2.5) |
| s4 swh | -0.5 (-1.0 to +0.1) |
| Haiku as run | -0.3 (-2.3 to +1.6) |
| Haiku with the 300-token re-runs | +2.0 (+0.1 to +3.9) |
| Opus, 114 Standard turns | +3.5 (-0.7 to +7.7) |
| Sonnet, 142 Fireside Brief turns | +2.8 (-2.3 to +7.9) |

Choice-parroting rejects after the change: ship 16 (was 68), Haiku 50 (was 482). Tables:
`fallback-runs/rescore-checker2/TABLES-after-full.md`, `TABLES-after-114.md`,
`TABLES-after-142.md`, `TABLES-ship-before-after.md`; per-cell counts in each arm's
`summary.json`; re-scored rows in `<arm>/before/` and `<arm>/after/`.

## Correction to the cloud record

The Haiku figure "with cut lines re-run at 300 tokens" was given as 78.7%. 26 of the cut lines'
re-runs (Fireside Rich) were never sent, because the 19:38:14 halt stopped that cell, and they had
been counted as fallbacks. Keeping those 26 lines as run gives **78.9%** (5,115 of 6,480). The
join is `2026-11-13-cloud-claude/join_supplement.py`; the 39 replay mismatches on that row come
from the splice (the opening memory across replaced and kept slots), not from the checker.

## Lead copying, measured on the s4 ship arm (accepted outcome lines)

| length | accepted | equal to the lead | contain all the lead's content words | fewer than 2 new content words |
|---|---|---|---|---|
| Brief | 948 | 582 (61.4%) | 613 (64.7%) | 683 (72.0%) |
| Standard | 953 | 2 (0.2%) | 350 (36.7%) | 2 (0.2%) |
| Rich | 906 | 0 (0.0%) | 400 (44.2%) | 0 (0.0%) |

The copying is a Brief effect (brief-by-stop keeps the first sentence, which is the lead). A
Standard/Rich rule "add at least 2 content words beyond the lead" would cost 2 and 0 lines; R&D
keeps it as a guard. Script: `fallback-runs/rescore-checker2/lead_copy_share.py`.

## Load on the rig

The re-score's one build ran 19:52:58 to 19:56:46 EST, one job, low priority, during session 5's
qwen3:8b Fireside cells; the re-score itself ran after that, about 6 s per arm, single-threaded.
