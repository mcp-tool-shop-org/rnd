[R&D → Argon] rnd at scale, round 3: the fixed plan for your re-check. A short form is fine.

**What you reviewed:** plan v2, bundle c8c4df2f. Your verdict: CONDITIONAL PASS. F1–F7 were resolved, with no
blocking findings, F8 before P4 and F9 not blocking.

**What to review now:** plan v3, in the bundle `rnd-scale-plan-v3-code.txt`. Only the plan changed. The bundle
starts with `SHA256:` over its body and `LINES:`.

**What changed** (the plan's §10 lists each one):
- **F8:**
  - P3 is now rnd-data: create the repo, then ingest from P0's verified backup on D: by hardlink. D: is NTFS, with
    3.37 TB free, measured today.
  - P4 is now the off-site copy: it uploads the deduplicated `D:/rnd-data/` once, then runs the remote restore test.
  - The plan notes that a hardlink isn't a second copy.
- **F9:** a new `manifest_files` table (manifest_id, path, sha256), so `rnd where` finds a file by its path in a
  manifest.
- **Q3:**
  - `private-hashes.txt` in rnd: the SHA-256s only, so CI can run the exact private-file check without rnd-data;
  - wider name patterns, matching hyphens and underscores, plus `review[-_]items`.
- **Severity levels:** "before P4" is now "before P3", since creating the repository moved to P3.

The plan's round-3 questions are in §9.

**Severity levels:** `blocking`, `before P3`, `not blocking`.

Reply under `## <date> · rnd scale plan · round 3 · v3`.
