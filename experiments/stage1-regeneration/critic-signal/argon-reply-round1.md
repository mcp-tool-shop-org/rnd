ARGON REPLY | critic-signal design | to R&D | 2026-10-19
(Filed verbatim from the Director's paste. Brief argon-consult-critic-signal.md sha256 9c1cee6b; bundle critic-signal-part1.txt,
header SHA256 24e3c03835710c18b331a16aa9f33c5e6b7779391751e91c0b19031a373c8760, 588 lines.)

ARGON REPLY | critic-signal design | to R&D | 2026-10-19
Verified bundle header: `SHA256: 24e3c03835710c18b331a16aa9f33c5e6b7779391751e91c0b19031a373c8760`, `LINES: 588` (`checked`, `critic-signal-part1.txt:1-2`).
1. The Diagnosis

* Section 2's structural claim holds (`worth knowing`): `self.flaw_gate` is off (`checked`, `runner.py:727-732`), so 4 of 12 Kind C flaw mismatches (`33%`) were logged as `flaw_advisory` and accepted (`checked`, `DESIGN.md:51-54`, `Per-check tally` lines 489–494).
* Three blind spots in today's critic that Phases 1–3 as written won't catch (`change before anything is built`):
   1. The critic never reads the writer's reply or `ESCALATE` line on C, D, or E (`checked`, `runner.py:697-721`, `critic.py:173-196`): `verdict_messages(seen_material, statement)` (`runner.py:712`) passes only `(seen_material, statement)`. A writer can hallucinate or contradict itself in the assistant explanation—or get `ESCALATE` wrong—and `_critic_pass` never sees it (save indirectly in `trait_messages`, which only classifies the lesson ID `T01..T21`, `runner.py:746`). Kind A gets no accuracy check at all (`runner.py:697, 733, 744`).
   2. Asymmetry on `cannot_tell` and superset coverage in `compare_verdict` (`checked`, `critic.py:189-195`): When `key_verdict == "cannot_tell"`, `critic.py:189-190` returns `AGREE` immediately without checking whether `cd` (`deciding`) is empty. For `supported`/`unsupported`, `critic_mismatch` (`critic.py:194-195`, `"neither covers the other"`) accepts a critic that quotes a multi-line block containing the key's line even if it relied on the wrong clause (`unsure` on `critic_mismatch` internals; call site `checked`).
   3. Silent two-try `VOID` loop (`checked`, `runner.py:711-717, 734-740`): Unparsed replies or non-verbatim `DECIDING` quotes (`VOID`, `critic.py:178, 186`) get a silent second try before counting.

2. Phase 1 as Gold

* Expand Phase 1 to audit Kind C flaws and writer explanations (`change before anything is built`): Keying only `(material, statement)` (`checked`, `DESIGN.md:105`) leaves Kind C's `planted_flaw` (`runner.py:723-725`) without a gold label when evaluating P1 (`flaw_gate`), and misses bad reasoning in the writer's assistant turn. Have R&D also blind-key `planted_flaw` on Kind C items and audit the writer's reply text after keying `(verdict, deciding)`.
* Count `"unclear"` rows as failures and separate adjudication (`change before anything is built`): Marking unsettled rows `"unclear"` and `"never counted as wrong"` (`checked`, `DESIGN.md:108-109, 153`) creates a loophole: an ambiguous verifier training item where `supported` vs `cannot_tell` cannot be settled from the material is defective training data. Count `wrong + unclear >= 3` toward reopening the writer screen (`DESIGN.md:153`), exclude `"unclear"` rows from Phase 2's confirmed-good pool (`DESIGN.md:115`), and have a second seat review any disagreement where R&D yields to the row's key.
* Sample size (`worth knowing`): Because ~50 is the entire accepted census (`checked`, `DESIGN.md:103-104`), $0/50$ gives a $5.8\%$ one-sided 95% Clopper-Pearson upper bound (`checked`, `research-2026-10-19.md:50-54`, Clopper & Pearson 1934), which is sufficient for a pre-T10 gate.

3. The Perturbations

* Types (a) and (c) do not change the critic's input prompt and need zero GPU calls (`change before anything is built`):
   * In `(a) verdict flip` (`checked`, `DESIGN.md:117-118`), `material` and `statement` are untouched. Because `verdict_messages(seen_material, statement)` (`checked`, `runner.py:712`) hides `key_verdict`, the critic receives the exact same prompt as control `(d)`. Any critic call that agrees with the key on `(d)` (`28/30` in Phase 0, `DESIGN.md:50`) will tautologically disagree with the flipped key in `compare_verdict` (`critic.py:187`).
   * Likewise, in `(c) flaw relabel` (`checked`, `DESIGN.md:121`), `flaw_messages(material, statement, fields["checker_trace"], row["checker_verdict"])` (`checked`, `runner.py:723`) hides `row["planted_flaw"]`.
   * Fix: Never run separate GPU calls for `(a)` or `(c)`—score them offline from the control `(d)` completions, and replace their GPU slots with perturbations that actually alter the critic's input:
      1. Over-inference (`cannot_tell` trap): Replace the deciding fact in `material` with a tangential or conditional clause so the true verdict becomes `cannot_tell` while the key stays `supported`/`unsupported`.
      2. Decoy `key_deciding`: Keep `verdict` right, but swap `key_deciding` to a plausible non-deciding line in `material` (tests `EVIDENCE_MISMATCH`, `critic.py:194`).
      3. Clean/mismatched `checker_trace` in Kind C: Replace `checker_trace` with a sound trace while keeping `planted_flaw` set (tests whether the critic says `"none"`, `critic.py:201`, vs rubber-stamping, Tyen et al. 2023, `arXiv:2311.08516`).

4. The Protocols

* P2's verbatim quote check is already in P0 (`change before anything is built`): `compare_verdict` (`checked`, `critic.py:176-186`) already extracts `cd = _lines(parsed.get("deciding"))` and checks `any(n(x) not in flat for x in cd)` using `gates.norm` (which strips whitespace and `**`/`__` emphasis after Window A voided three good answers on raw matching, `critic.py:179-180`).
* P2's false-reject traps (`change before anything is built`):
   1. `cannot_tell` items (`checked`, `critic.py:189-190`): Valid `cannot_tell` items have no deciding line (`cd == []`). If P2 enforces `"A missing or invented quote refuses"` (`DESIGN.md:132`) without exempting `cannot_tell`, P2 will refuse 100% of valid `cannot_tell` controls. Instead, require `bool(cd)` on `supported`/`unsupported` and `not cd` on `cannot_tell`.
   2. Drop the 2-try `VOID` loop (`checked`, `runner.py:711`) or require exact line-count matching: Make P2 require the critic to extract the target entity's exact claim from `material` before stating a verdict, and refuse in `compare_verdict` if `len(cd) > len(key_deciding) + 1` (preventing whole-paragraph quoting from gaming `critic_mismatch`).

5. The Decision Rule and Power

* Isolate `verdict` + `flaw` in Phase 3, and fix the budget math (`change before anything is built`):
   1. Skip `trait` votes in Phase 3 (`checked`, `runner.py:744-751`, `Per-check tally` line 493): `trait` runs 3 calls per item (`75%` of calls) and disagreed on `15/39` (`38.5%`) of items—which would push control refusals above the `10%` ceiling (`DESIGN.md:147`) on a check P0–P3 never vary. Running only `verdict` + `flaw` cuts Phase 3 cost by ~70%.
   2. P1 alone cannot pass Holm-adjusted McNemar (`checked`, `DESIGN.md:124, 135-137`): `flaw_gate` affects only Kind C (~7–8 rows in 30). With 6 Holm tests ($p < 0.0083$), $\le 7$ discordant pairs can never reach significance ($2 \times 0.5^7 = 0.0156$). Fold `flaw_gate` into P2 and compare P2 and P3 vs P0 on 60+ input-perturbed items.
   3. Budget cap (`checked`, `DESIGN.md:166-173`): `165.85 of 300 units spent` leaves `134.15 u`, so Step 1 (`45 u`) + Step 2 (`120 u`) = `165 u` exceeds the ceiling unless `trait` calls and duplicate `(a)`/`(c)` calls are cut.

6. The T10 Carry-Overs

* (a) Projection rule (`worth knowing` / `change before the first paid window`): `2.5×` is sound across the 5 non-QAT writers (`1.98×–2.92×`, mean `2.30×`; `checked`, `DESIGN.md:200-202`), but multiply T10's critic rate (`296 s` / `410 s`) by `2×` if P3 wins.
* (b) Screen slot list (`change before anything is built`): In `check_multi_line_share` (`checked`, `gates.py:135-143`), the `25%` multi-line denominator is only `supported` + `unsupported` items (excluding `cannot_tell`), enforced per lesson. Also add +1 buffer slot per quota so 1–2 funnel drops don't make the surviving batch fail `check_batch`.
* (c) Pins (`worth knowing`): Verify whether `huggingface_hub 1.33.0` (`DESIGN.md:207`) is a typo (PyPI is `0.x`/`1.x`; `0.36.2` ran in 13j/13k). Pin `numpy`, `gguf`, and `safetensors` alongside `torch` in the converter venv.
* (d) `with_heartbeat` (`change before the first paid window`, `checked`, `pin_window.py:219, 233-238`): Two bugs: (1) when Xet downloads to `~/.cache/huggingface/xet` (`last_free - free` grows while `nbytes == 0`) and then moves the file into `watch` (`nbytes - last_bytes` jumps by the full file size), `grew = max(nbytes - last_bytes, last_free - free)` double-counts the file and logs a false `mbps` spike (`pin_window.py:234-237`); (2) if Xet `fallocate`s the file up front, `st_size` and `free` stop changing and a live download looks stalled. Point `HF_XET_CACHE` inside `watch` and measure `st_blocks * 512`.
