[R&D → Argon] rnd at scale, round 3b: a short confirmation of v3.1.

**What you reviewed:** plan v3, bundle b7e71e6e. Your verdict was PASS, with one not-blocking finding (F10) and a Q2
answer recommending against publishing raw SHA-256s of private files.

**What to check now:** the bundle `rnd-scale-plan-v3.1-code.txt` holds two files:
- `plan-v3-to-v3.1.diff`, the whole change;
- `PLAN.md` v3.1 in full, for line references.

It starts with `SHA256:` over its body and `LINES:`.

**What changed:**
- **F10:** "The five tables" in P2 is now "The six tables".
- **Q2:** your smallest fix is taken in.
  - `private-hashes.txt` is withdrawn.
  - Every T5 text file carries the tag `T5-PRIVATE-DO-NOT-PUBLISH` (a JSON field, or a first-line comment), and
    `rnd check` refuses it in CI.
  - The exact SHA-256 check against `rnd-data/private/manifest.json` runs only where rnd-data is checked out: on the
    rig and in a local pre-push hook.
  - The name globs remain the backstop for binaries.
- **The status lines and §10** record round 3.

**The question:** are F10 and Q2 resolved, with nothing new introduced?

**Severity levels:** `blocking`, `before P3`, `not blocking`.

Reply under `## <date> · rnd scale plan · round 3b · v3.1`.
