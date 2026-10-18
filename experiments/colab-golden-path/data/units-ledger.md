# Colab units ledger: Stage 1 pilot budget

Budget: **200 units tonight** for the Publisher and R&D together (Mike, 2026-10-17: raised from 50 to 100 for a baseline night, to 150 at 19:45Z, then to 200 late in the night, given to R&D under his standing word that the budget can rise as needed). A typical day runs 25–70 units. If a window would take
the running total past 100, it doesn't start; it waits for Mike. RunPod is separate, and its top-ups are Mike's.

| Window | What | Start balance | End balance | Spent | Running total / 100 |
|---|---|---|---|---|---|
| 4 | Muse pins (A100), cap 8 | 1201.15 | 1199.76 | 1.39 | 1.39 |
| 5 | 5 conversions + Bolt fetch, smoke at ctx 32768 (A100), cap 12 | 1199.76 | 1192.18 | 7.58 | 8.97 |
| 6 | H100 (R1, Gemma, Qwen3.6): not assigned (Service Unavailable), twice | 1192.18 | 1192.18 | 0 | 8.97 |
| 7 | critic-control (A100), cap 14: both critics reproduced their pins, then stopped at the fit check (log buffered, no offload line read) | 1192.18 | 1189.18 | 3.00 | 11.97 |
| 8 + 7b | ran side by side from 1189.18: 8 = q6k, cut off by the shared cap watcher mid-Gemma (partial log only); 7b = critic-control, both critics pass R&D's bar | 1189.18 | 1178.14 | 11.04 (8 ≈ 3.8, 7b ≈ 7.2) | 23.01 |
| 9 | q6k alone (A100), cap 8: Qwen3.6, Gemma and R1-Distill Q6_K pinned and fit; Qwen3.6's reproduced window 8's | 1178.14 | 1171.51 | 6.63 | 29.64 |

Plan (R&D's split):
- window 5: the conversions and smoke serves, cap 12;
- the pilot's 8 arms: from what's left;
- about 5 held in reserve for a rerun;
- left over after the tasks: Mike's OK (2026-10-17) to test and troubleshoot, to get our bearings.

Earlier windows, outside this budget: window 2 spent 2.22 and window 3 spent 1.93.
| 10 | pilot arm 1 (A100): failed at start, PIN_RND_COMMIT not forwarded to the VM | 1171.51 | 1171.07 | 0.44 | 30.08 |
| 10b | pilot arm 1 (A100): Colab dropped the VM mid-download of Muse (~14:15); exec hung until killed | 1171.07 | 1168.81 | 2.26 | 32.34 |
| 10c | pilot arm 1 (A100): both conversions reproduced, then the first wave failed (rnd's package lacks the proxy module) | 1168.81 | 1166.22 | 2.59 | 34.93 |
| 11a | R1-Distill BF16 → Q6_K (A100), cap 6: stopped after the BF16 conversion, before the Q6_K. The cap counted 10.6/hr, both 11a's and 11b's sessions, because they opened together (mistakes #29; fixed in role-set 9402a8e) | 1165.42 | (shared, see below) | ≈ 3.0 (34 min × 5.3) | ≈ 37.9 |
| 11b | Qwen3.6 and Gemma Q8_0 fit at 32768 (A100), cap 7: Qwen3.6 fits (42/42 layers, peak 36022 of 40960 MiB, 89.7 tok/s, reproduces b7c0c8eb); stopped while hashing Gemma's Q8_0, same cap fault | 1165.42 | (shared) | ≈ 3.5 (40 min × 5.3) | ≈ 41.4 |

11a, 11b and 10d overlap; balance 1166.22 at 10d's start, 1155.35 at 16:08 with 10d still running. 11a and 11b are estimated from their own runtimes, then reconciled with the balance when 10d ends.
| 11c | R1-Distill BF16 → Q6_K rerun (A100), cap 6: the exec lost its connection at its first command; nothing ran on the VM, and the hung exec held the session ~35 min until I killed it (mistakes #30) | 1155.35 | (shared) | ≈ 3.2 (36 min × 5.3) | ≈ 44.6 |
| 11d | Gemma Q8_0 fit at 32768 (A100), cap 3.5: fits. 61/61 layers, projected 35070 MiB with 4943 free, 27.8 tok/s, reproduces e357a450, 1 slot × 32768 | 1155.35 | 1149.64 (its own end read) | ≈ 1.6 (18 min × 5.3) | ≈ 46.2 |

Balance 1146.99 at 16:51Z (12a's start), with 10d still running: 54.16 spent from 1201.15 across every window, 10d's part included.
| 10d | pilot arm 1, Qwen3.8 + Muse (A100), cap 14: hit its cap at 17:57 with w0 unfinished (no checkpoint); the rig log stopped receiving the exec's output at 15:46 while the job ran on (server log read at 16:09, dataminer file at 16:38) | 1166.22 | (shared) | 14.03 | ≈ 60.2 |
| 12a | w0 screen, Qwen3.6 + Lightning + Bolt around Muse (A100), cap 17: the exec's output stopped reaching the rig at 17:42 (hashing Lightning); Colab pruned the session at 18:10 (its history: session_terminated, reason pruned). Nothing came back (mistakes #31) | 1146.99 | 1134.18 | 12.81 | ≈ 73.0 |

Balance 1134.18 at 18:11Z with no session open: 66.97 spent from 1201.15 across every window. The per-window rows above sum higher because 11a/11b are estimates; the balance is the measure.
| 12p | watcher preflight (CPU, 0.08/hr), cap 1: mock job silent on the stream for 15 min; job.log followed, 7 BUSY readings, no stall, result fetched; the exec returned before the watcher's next look | 1134.18 | 1134.16 | 0.02 | ≈ 66.99 |
| 12q | watcher preflight (CPU), cap 1: mock job 5 min then hangs; JOB DONE from job.log at 18:57:58, exit fetch 2 s, session stopped | 1134.16 | 1134.15 | 0.01 | ≈ 67.00 |

Budget raised to 150 at 19:45Z (Mike). Balance 1130.49 at 19:44Z: 70.66 spent, 79.34 left of 150, with 12b (Granite, cap 11) in flight.
| 12b | Granite screen (A100), cap 11, from 53cb800 | 1134.15 | (open) | | |
| 12c | W2: Qwen3.6 then Bolt, Muse critic, 4 waves (A100), cap 14, from 53cb800 (eager setup) | ~1128.7 | (open) | | |
| 12d | W3: Lightning then Muse, each critiquing the other, 4 waves (A100), cap 15, from 8b12692 (lazy setup). A critic setup failure now shows only after the writers have run, and a resume then pays only the critic's setup (R&D) | ~1128.7 | (open) | | |
| 12s | v2 stub run (CPU, 0.08/hr), cap 1: refused at start, PIN_RND_COMMIT given as a short sha (my input error; the job's check was right) | 1091.52 | 1091.52 | 0.00 | |
| 12s2 | v2 stub run (CPU): failed before any wave, NameError __file__ (colab exec runs the script in the kernel); fixed in 38e8497 | | | ~0.00 | |
| 12s3 | v2 stub run (CPU) at 38e8497: PASS. STUB header, ok true, 2 arms x write+critique through the proxy (90 calls, 4 wave checkpoints), pilot-out.tar back in 2 s; extract and resume_from refuse stub drafts without PIN_STUB=1 | | | ~0.00 | |
| 12g | critique-only (A100) from 516ccd2, cap 7: hit the cap at 6.74 after 74 min (Muse's setup 15 min; Muse critiques about 29 min per writer). Granite's and Bolt's critiques finished and checkpointed (Granite 7 accepted / 1 rewrite; Bolt 7 accepted); Lightning's and Muse's arms not reached. No pilot-out.tar: the cap stop kills the job before its finally (Argon #1, open). | 1100.18 | 1087.05 (12f open) | ~6.6 | |

Projection error (12g): the critique-only window was projected at about 5 units (55 min) from critic-control's 20 s per item; it took 74 min and its cap. Critic-control items are one-shot; a critique wave runs about 4 critic calls a draft, each with the critic's full thinking (Muse about 86%). Measured: about 29 min per 8 drafts under Muse. Later critique projections use that.

**2026-10-18 (the morning order, step 6).** About 100 units arrived on the account at about 04:15Z (the Colab Pro plan). The study budget stays 200 (Mike's), so spend is counted as rate × runtime, checked against the balance less the top-up.
| 12s5a/b, 12s6a/b | CPU stub rungs (resume + chain), 4 sessions | 1071.67 | 1071.67 | 0.00 | 129.48 |
| cpu-measure | CPU default + high-mem gate reads, 2 sessions of about 20 s | | | ~0.00 | 129.48 |
| 13b | W-B (A100), cap 8.8, role-set c1cf4ae: Muse T02-C-08 rewrite via the card-pin chain, then Lightning's critique (8 accepted); twins for both. Lightning's twin write dropped both slots, and the critique after it was refused (a pin_window defect; ok false). Exec wall 5241 s | 1071.67 | 1163.79 (after the +100) | 7.95 by 1.50 h × 5.3 (7.88 by balance less 100) | 137.43 |

**Night one's open rows closed (2026-10-18, R&D's request).** Own rate (5.3/hr) × each session's time, from the rig's start reading to the job's end, plus the exit fetch and stop. These overlap, so the balance can't split them.
| 12b | Granite screen, cap 11 | 1134.15 | | 10.04 (rate × runtime) | |
| 12c | W2 Qwen3.6 + Bolt, cap 14 | ~1128.7 | | 10.88 (rate × runtime) | |
| 12d | W3 Lightning + Muse, cap 15 | ~1128.7 | | 8.45 (rate × runtime) | |
| 12e | stalled: job.log empty 10 min after the exec started | | | 1.29 (rate × runtime) | |
| 12f | Qwen3.8 + Gemma, w0 + w1 | 1111.70 | | 17.59 (rate × runtime) | |
| 12g | critique-only, cap 7 | 1100.18 | | 6.72 (rate × runtime; the cap read 6.74) | |
| 12h | Lightning + Muse critique each other | 1086.19 | 1071.67 | 8.90 (rate × runtime) | |
Reconciliation: 12b–12h total 63.87 by rate × runtime. Spent before 12b was ≈67.00, so night one comes to ≈130.87, against 129.48 by the balance. The 1.39 difference is within the earlier estimated rows (11a–11c, 12a). The balance (129.48) stays the measure. Each window's folder now holds an outcome.json with its window, card, cap, spent, basis, outcome and why.
