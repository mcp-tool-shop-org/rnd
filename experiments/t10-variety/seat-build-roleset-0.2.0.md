# BUILD BRIEF | a seat (the Publisher assigns) | role-set: the full treatment and the 0.2.0 release | mcp-tool-shop-org/role-set | from R&D, for the Publisher | 2026-10-14

**The Director's order, 2026-10-14:** role-set gets the full treatment and a version bump, now that the T10 generator with its `if_shape` axis is on main (#55, `549a619`). This is a re-treatment: role-set shipped 0.1.0 on 2026-10-11 with shipcheck, translations, a landing page and a handbook already in place. The job is to bring every public surface up to what the repository now does, close the three ship-gate items left open at 0.1.0, and release **0.2.0**.

**Two rules that govern it:**
- The playbook's law says public surfaces are lead-authored, never delegated. The Director's order delegates this treatment to a seat, as he did for role-os v2.12.0 on 2026-10-08; that order is the override, and R&D reviews every public surface before the Publisher merges.
- The version rule of 2026-09-09: unfinished work stays 0.x. role-set is a prototype; 0.1.0 → **0.2.0** (new generator capabilities), not 1.0.0.

## Where to work

```
git -C E:/AI/role-set fetch origin
git -C E:/AI/role-set worktree add E:/AI/role-set-treat -b release/0.2.0 origin/main
```

Normal commits, no force-push. One PR at the end; the Publisher merges, tags, releases and deploys. Read first: the full-treatment and handbook playbooks in the lead's memory store (`full-treatment.md` and `handbook-playbook.md`; the Publisher hands the seat copies), `SHIP_GATE.md`, `SCORECARD.md`, `CHANGELOG.md`, `docs/generator-design.md`, `docs/role-set-design.md`, `roles/verifier/README.md`, `roles/advocate/README.md` (a draft on #56; describe it as a draft).

## Phase 0: the gates first

- `npx @mcptoolshop/shipcheck audit`. Every A–D line checked or `SKIP:` with a reason. The three open E lines from 0.1.0 (the logo URL, translations, repo metadata) are this treatment's to close, not to skip.
- The identity scan on the git-tracked tree: `python $env:USERPROFILE\.grok\bin\identity-scan.py .` must print `RESULT CLEAN`. A hit stops everything.
- Confirm the brand logo URL returns 200 (`https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/role-set/readme.png`). If brand PR 102 is still open, say so in the hand-back; the Publisher chases it.

## Phase 1: the README, final

Keep the language bar, the logo, the badges and the footer. Rewrite the body to what role-set does now:
- the status line stays a prototype, developed in the open; nothing it writes is training data until a person checks it;
- the two role packs: the verifier (synced from aspire-si at a commit) and the Advocate (a human-written pack in the repository, drafted on #56 for the Director's approval);
- **the T10 generator**, the part that changed: puzzles proven by construction (the solver checks the model; the four readings; `trait_not_tested`); the cell map `(n, op, k, ifs)` and the claim axis `if_shape` with its seven shapes; the min-cost-flow allocator with the zero-`if` cap; the variety floors (distinct ≥ 75%, top repeat ≤ 3, none twice in a file) judged on locked seeds; the committed record with its hash closed under imports, checked in the normal CI job in minutes, and the exhaustive rebuild on `workflow_dispatch`; the capacity gate and the headroom (61 usable claim cells for three-value packs against 27; room for twelve packs);
- the commands as they are now (`plan`, `write`, `puzzle-check`, `pack verify`, `harvest`, `critic-control`, the T10 scripts), each with one line;
- the coverage floor (90, measured about 97) rather than a test count;
- the threat model and the loopback rule, as they stand.

Then hand the Publisher the translation command; the seat does not run it: `node E:/AI/polyglot-mcp/scripts/translate-all.mjs E:/AI/role-set/README.md`. Translations run on the local model and land as `README.*.md` before the release commit.

## Phase 2 and 3: the landing page and the handbook

- The landing page exists (`site/`). Update `site/astro.config.mjs` and `site/src/site-config.ts` descriptions to the README's. Do not touch `secondaryCta`.
- The handbook exists with seven pages (index, getting-started, usage, kinds, configuration, store, security). Update them to the README and add two: **`generator.md`** (the T10 generator end to end: cells, `if_shape`, the allocator, the floors, the record gate, the dispatch sweep, how to add a pack and regenerate the tables and the record) and **`roles.md`** (the two packs and their files; how a pack is served, hashed and verified). Frontmatter with numeric `sidebar.order`; `kinds.md` stays.
- `cd site && npm run build` must produce `dist/index.html`, `dist/handbook/index.html` and the pagefind index.

## Phase 4: metadata and coverage

- The Publisher runs `gh repo edit` for description, homepage and topics; the seat proposes the exact strings in the hand-back.
- The coverage badge already shows Codecov; confirm it reads the floor from `codecov.yml` (90) and that CI's `test` job stays inside its 15-minute cap (it is about 7 minutes at `549a619`).

## Phase 5: the knowledge entry

`cd E:/AI/repo-knowledge && node dist/cli.js scan E:/AI/role-set`, then the notes: thesis, architecture, at least one relationship (aspire-si for the gates and the verifier pack; rnd for the briefs and the record), a convention (keys by construction; variety floors on locked seeds; the record gate), a next step (the Advocate pilot), and the commands. `node dist/cli.js show role-set` must come back complete.

## Phase 6: the release commit

- `CHANGELOG.md`: move `[Unreleased]` into **`[0.2.0] - <date>`**, grouped Added / Changed / Fixed, with the T10 entries from #49 and #55 in plain words (the cell table and tiered deletion; the trait-clue test; the allocator; the committed record and the dispatch sweep; `if_shape` and the per-stratum capacity weights; the hash closure), and a new `[Unreleased]` heading.
- `pyproject.toml` version `0.2.0`; `uv.lock` unchanged unless a dependency changed.
- `SCORECARD.md`: a post-treatment assessment with real scores from the audit, dated.
- The identity scan on the tree again: CLEAN, or stop.
- Stage explicit paths (never `git add .`; translated READMEs by the `README.*.md` glob only). Atlas: stage, `atlas map`, `atlas check`.
- Open the PR against `main` and hand back. **Do not tag, release or publish.**

## Phase 7: after the merge (the Publisher's, listed so the hand-back names it)

The Publisher scans the tag tree, tags `v0.2.0`, creates the GitHub release with the CHANGELOG section as its notes, confirms the Pages deploy renders the landing page and the handbook with search, and re-scans what was published. PyPI only if role-set is already on PyPI under its name; otherwise no publish this release.

## Gates (every push)

- The full suite green at the coverage floor; CI's `test` job inside its cap; the `sweep` dispatch not required for a docs release unless the record changes (it must not).
- `atlas check` clean; the identity scan CLEAN on the tree and, before the tag, on the tag tree.
- `npx @mcptoolshop/shipcheck audit` exits 0 at the end, with section E genuinely done.

## Not in scope

- Any change to the generator, the packs, the tables or the record. If a surface reveals a defect, note it in the hand-back; don't fix it here.
- The Advocate build (Seat C, #56), the T10 traits 4–6, the Phase 2 and 3 Advocate batches.
- A 1.0.0 version.

## Hand-back

A `[<Seat> → Publisher]` comment on the PR: the head SHA; the shipcheck audit result and the SCORECARD scores; the identity scan result; the site build output (the three paths); the knowledge entry's `show` output; the proposed `gh repo edit` strings; the translation command handed over; the CHANGELOG section for the release notes; anything the surfaces revealed about the code. Then stop. R&D reviews every public surface; the Publisher merges and releases.
