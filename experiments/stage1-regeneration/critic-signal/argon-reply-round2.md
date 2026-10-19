ARGON REPLY | critic-signal v2 | to R&D | 2026-10-19 — PASS
(Filed verbatim from the Director's paste. Brief argon-brief-critic-signal-r2.md sha256 8658c405; bundle critic-signal-r2-part1.txt,
header SHA256 7f788788af16712d14fd4da03f708ca4a1761b85db1d9cd257b85a09756a80ae, 287 lines.)

ARGON REPLY | critic-signal v2 | to R&D | 2026-10-19
Verified header: `critic-signal-r2-part1.txt` (`SHA256: 7f788788af16712d14fd4da03f708ca4a1761b85db1d9cd257b85a09756a80ae`, `LINES: 287`).
Status of Consult Items in `DESIGN.md` (v2)

* Q1 (Blind spots in Section 2) — Closed (`DESIGN.md:61-73`). Section 2 names all three gaps—uninspected writer reply / `ESCALATE` line and uncritiqued Kind A (`62-64`), unchecked `cd` on `cannot_tell` (`65-66`), and over-long quotes passing `critic_mismatch` (`67-68`)—and notes that verbatim checking is already in P0 (`69-70`).
* Q2 (Phase 1 gold check) — Closed (`DESIGN.md:116-125, 131-132, 181-182`). R&D blind-names Kind C's `planted_flaw` (`117-118`), audits the writer's reply and `ESCALATE` line (`119-120`), counts `unclear` rows as failures toward the $\ge 3$ screen-reopening threshold while excluding them from Phase 2 (`122-124, 131-132, 181-182`), and sends any row where R&D yields to the key to a second seat (`125`).
* Q3 (Perturbations) — Closed (`DESIGN.md:132-147, 204-205`). Only input-altering perturbations—`(b) material flip`, `(e) cannot_tell trap`, `(f) clean trace`, and `(d) controls`—run on the GPU (`135-143`); key-only changes `(a)`, `(c)`, and `(g)` are scored offline from control `(d)` replies (`144-147`).
* Q4 (Protocols) — Closed (`DESIGN.md:156-162, 190, 204-205`). P1 is folded into P2 (`162`), P2 re-scores P0's replies with `flaw_gate` on, empty `deciding` required on `cannot_tell`, and `len(cd) <= len(key_deciding) + 1` on `supported`/`unsupported` (`157-159`), and P3 runs P2 at a second seed with any-refuse (`160`).
* Q5 (Decision rule, power, and budget) — Closed (`DESIGN.md:153-155, 164-182, 191-199`). Trait votes are excluded from Phase 3 (`153-155`), P2 and P3 are tested against P0 by exact McNemar with Holm correction (`164-165`), and the worst-case budget (`~92 u` across both critics) fits inside the `134.15 u` remaining (`194-199`).
* Q6 (T10 carry-overs) — Closed (`DESIGN.md:207-208, 223, 229-244`). The multi-line share is scoped per lesson over `supported` and `unsupported` with one buffer slot per quota (`233-237`), `torch`/`numpy`/`gguf`/`safetensors` and `huggingface_hub` (`1.33.0` / `0.36.2`) are pinned (`238-240`), P3 doubles the T10 critic projection (`241`), and the Xet heartbeat fix is gated on the live probe (`207-208, 223, 242-243`).

Anything v2 Breaks or Misses
Nothing blocking. One statistical note for `DESIGN.md:164-168`: because offline types `(a)`, `(c)`, and `(g)` are deterministic re-evaluations of the same `(d)` control reply rather than independent critic draws, compute the primary McNemar p-value over the ~70 independent GPU-perturbed items (`b`, `e`, `f`) + offline `(g)` (without pooling `(a)` and `(d)` as separate independent trials of the same reply), and report each perturbation type's catch rate separately (`DESIGN.md:150`).
Answers to the Three Questions

1. Is the offline scoring of key-only types sound? Yes. Because `verdict_messages` and `flaw_messages` never pass `key_verdict`, `key_deciding`, or `planted_flaw` (`DESIGN.md:48-52, 132`), the critic's completion on `(a)`, `(c)`, and `(g)` is invariant to the key change. In particular, `(g) decoy deciding` directly tests whether P2's `len(cd) <= len(key_deciding) + 1` cap catches over-long quotes that P0's `critic_mismatch` (`critic.py:194-195`) lets through, and `(c)` directly measures `flaw_gate` (`critic.py:203-204`).
2. Do `(e) cannot_tell trap` and `(f) clean trace` risk leaking the answer through script wording?
They can if the script inserts stock boilerplate phrases. To prevent surface cues during the Phase 8 spot-read (`DESIGN.md:221`):
   * For `(e)`, prefer deleting the deciding clause/value or swapping the subject identifier in the deciding line to another entity already present in the passage, rather than appending templated qualifiers (`"if approved"`, `"allegedly"`).
   * For `(f)`, build the sound trace directly from the item's own key (`key_deciding` quote + true `key_verdict`, updating `row["checker_verdict"]` to match `key_verdict`) so the trace uses the passage's native wording and contains no reasoning flaw.
3. Is ~120 s per item (`296 s × 2/5`) with `+30%` reasonable before timing? Yes. Removing the 3 `trait` votes drops call count per item from ~4.3 calls to ~1.3 calls (`~30%` of calls) (`DESIGN.md:191-193`). Assuming `verdict` and `flaw` calls think slightly longer than `trait` calls `[Assumption]`, `2/5` (`120 s`) plus `+30%` (`156 s/item`, `23 u` for 100 items) is a safe ceiling for Step 1, which then re-anchors Step 2 (`DESIGN.md:194-198`).

PASS
