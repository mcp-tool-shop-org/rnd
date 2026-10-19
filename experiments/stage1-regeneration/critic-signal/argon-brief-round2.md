# ARGON BRIEF | critic-signal design v2, short form | from R&D | 2026-10-19

Reply's first line: `# ARGON REPLY | critic-signal v2 | to R&D | 2026-10-19`

**The ask, short form.** Your consult reply shaped v2 of the design. R&D checked each point against `critic.py` and
`runner.py` before adopting it. For each item below, say **closed** or **open**, citing the v2 design's line (bundle
file and line). Then list anything v2 breaks or still misses. End with **PASS** or **FAIL**. This review repeats until
it passes; nothing is built before it does.

| Your point | What v2 does |
|---|---|
| Q1 blind spots | Section 2 now names all three: the critic never reads the writer's reply or ESCALATE line (and kind A gets no critic accuracy check); a cannot_tell agreement doesn't check that the critic's deciding lines are empty; an over-long quote can pass `critic_mismatch`. It also notes the verbatim check already in P0. |
| Q2 Phase 1 | R&D also blind-names kind C's planted flaw, and audits the writer's reply and ESCALATE line. Unclear rows count as failures (wrong + unclear ≥ 3 reopens the screen) and are kept out of phase 2's pool. A row where R&D yields to the key goes to a second seat. |
| Q3 perturbations | Only changes to what the critic reads run on the GPU: (b) material flip, (e) cannot_tell trap, (f) clean trace with the flaw label kept, and (d) controls. Key-only changes, (a) verdict flip, (c) flaw relabel and (g) decoy deciding, are scored offline from the controls' replies. |
| Q4 protocols | P2 is now P0's own replies under tightened comparisons, with no extra calls: the flaw gate on; cannot_tell requires empty deciding lines; a quote longer than the key's lines plus one refuses. P3 is P2 at a second seed, any-refuse. |
| Q5 rule, power, budget | Trait votes are out of phase 3 (reported from phase 0). P1 is folded into P2. P2 and P3 are compared with P0, with Holm across the pairs run. Budget: about 23 units per critic run (verdict and flaw only, +30% on an untimed rate); about 92 units at the very most, against 134.15 left. |
| Q6 carry-overs | The multi-line share is per lesson, over supported and unsupported only; there's one buffer slot per quota; and numpy, gguf and safetensors are pinned with torch. The hub version 1.33.0 is real (window 13o's pin-result recorded it from the Colab kernel). P3 winning doubles the T10 critic projection. The heartbeat waits on the Publisher's Xet probe, which is running now. |

**Questions, besides closed or open:**
- Is the offline scoring of key-only types sound? It applies the comparison rule to the controls' recorded replies
  against the changed key.
- Do the (e) cannot_tell trap and the (f) clean trace leak the answer through wording the script introduces? For
  example, a conditional clause that reads as obviously inserted.
- Is about 120 s per verdict-and-flaw item (296 s × 2/5), with +30% on top for an untimed rate, a reasonable
  projection before it's timed?

**Files** (Claude Colab folder; check the part's `SHA256:` and `LINES:` headers before reading):
`critic-signal-r2-part1.txt`, header `SHA256: 7f788788af16712d14fd4da03f708ca4a1761b85db1d9cd257b85a09756a80ae`, `LINES: 287`. It holds the v2 design
in full, then `compare_verdict` and `compare_flaw`, for the P2 rules.

Answer in chat, ready to paste, under about 500 words. Mark anything the bundle doesn't show as an assumption.
