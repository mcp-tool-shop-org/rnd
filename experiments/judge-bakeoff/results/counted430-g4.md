# Counted 430 on G4: windows, hashes and fixes

Source: Antigravity's reply of 2026-11-12 (ET) and the colab ledger of the same date.
Times in the sources are UTC; Eastern time is UTC minus 5 hours on these dates, so the
windows ran the evening of 2026-11-12 into the early hours of 2026-11-13 ET.
`[unverified]` throughout; no record here re-checked the counts.

## Windows

| Window | Card | Elapsed (s) | Units | Outcome and content |
|---|---|---:|---:|---|
| lock-check 1a, run 8 | A100 (booked before the A100 stop ruling) | 1,244.000 | 2.325589 | Stopped cleanly; the window-id fix verified; one judge hit its default 600 s child timeout at 85%; re-run moved to G4 |
| lock-check 1a, G4 run 1 | G4 | 664.000 | 1.853667 | All five judges 100/100 ok in 290.68 s; the rig's log guard falsely flagged a claim leak on one judge's raw generation (a pre-fix diagnostic) |
| lock-check 1a, G4 run 2 | G4 | 616.000 | 1.719667 | ok, rc 0; 500 anchor calls and the boot-gatekeeper goldens; golden anchor manifest hash starts `7c4d86b2`, shard manifest hash `cfd1e00d` |
| lock-check 1b, G4 run 1 | G4 | 1,422.000 | 3.969750 | ok, rc 0; 114 items x 5 judges plus low-margin reruns; `p0a` report hash starts `a3193d8f` |
| counted shard 1 of 2 | G4 | 4,086.000 | 11.406750 | ok, rc 0; 6,450 shard calls plus 500 anchor calls = 6,950; outputs-closed hash `a252d962b5cd1318a4f87d1d5ef79497b3e5990a21a54bda6ddd5701fbacca2b` |
| counted shard 2 of 2 | G4 | 4,285.000 | 11.962292 | ok, rc 0; 6,450 shard calls plus 500 anchor calls = 6,950; outputs-closed hash `97fc69ad7135ee9e6c7616af9ad02f4945a724cc38f394adaca5b51fc8b8243e` |

Booking basis: own rate per hour x elapsed seconds / 3600 (G4 10.05 per hour, A100 6.73 per
hour in this ledger). Totals recomputed here from the rows above: 29.058459 units for the
four successful G4 windows; 33.237715 for all six. The reply states 32.22 units for
"including the pre-fix diagnostic"; these rows do not reproduce that figure (29.058459 +
1.853667 = 30.912126), so the difference is unexplained here.

## Combined run

- Combined outputs hash: `3ea32d169864023ab24c1a05dab3457dfbd8bb97f37c0edab8279ce52dbe5ba4`
- Schedule hash: `c410e7fad4cf848e1a4b7beae224e34be623ea2a4786bef4e12f480f0617450d`
- Merge gates, all `ok`: anchor agreement; bijection and input-token hash; colocation;
  row-done hash; session environment and zero ECC.
- Pairwise anchor agreement across lock-check, shard 1 and shard 2 (500 anchor calls each):
  0 verdict flips, 0 output-token hash differences, 0 input-token hash differences.
- Prompt verification: 12,900 of 12,900 rows matched; 0 uncorrected ECC errors on both shards.

## Code changes the run needed (on the bake-off repo's PR 81 branch)

1. The log-claim n-gram guard now exempts the private generation and row files while still
   enforcing the key-filename and token-leak guards on every file and the full claim guards
   on logs and receipts.
2. The shard merge now handles the real-GPU tokenizer's input-token hash differing from the
   offline rig's canonical-prompt hash, and verifies the prompt hash on all 12,900 calls plus
   cross-shard and golden anchor input-token equality (3 of 3 merge-gate tests green).

## Hygiene lines the reply reports

Proxy-token hits 0, Hugging Face token hits 0, shell-history hits 0, carriage returns 0,
identity scan clean on shards, merge audit, combined directory, public summary, ledger and
the reply itself.

## Kept on the rig (not filed)

The sealed keys, the sealed score rows, per-item rows, anchor rows, generations and the
full public summary's per-judge accuracy columns.
