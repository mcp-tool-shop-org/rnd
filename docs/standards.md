# Standards compliance

Scored against the studio's six workflow standards (0 missing · 1 partial ·
2 present · 3 exemplary). The workflow is: file entries → `rnd check` →
`rnd build` / auto-rebuild → search; and `rnd catalog sync` for catalogues.

| Standard | Score | Evidence |
|----------|-------|----------|
| PIN_PER_STEP | 2 | Each catalogue snapshot records the upstream commit SHA it was synced from (`catalog.json: ref`), and every item URL is pinned to that SHA. Entries are plain files in git, so the index is reproducible from any commit. No model sits in the pipeline, so there is no model or prompt to pin. Not 3: no test replays a sync against a recorded upstream. |
| ANDON_AUTHORITY | 3 | `rnd check` and `rnd build` halt on any error: bad enum, missing field, duplicate id, `verified` claim without `(via: …)`, invalid review fit. A failed build keeps the previous good index instead of writing a partial one (temp file + atomic replace). Tests cover both halts (`test_errors_keep_previous_index`, `test_rejects_bad_enums_and_unsourced_verdicts`). |
| NAMED_COMPENSATORS | 2 | The tool makes no irreversible calls: it reads GitHub over `gh api`, writes only local files, and the index is disposable. See the table below for the repo-level actions. |
| DECOMPOSE_BY_SECRETS | 2 | Volatile, human-curated content (entries, instruments, review.json) is kept apart from generated content (catalog.json, rnd.db) and from code (`rnd/`). Parsing, the index and catalogue sync are separate modules. |
| UNCERTAINTY_GATED_HUMANS | 2 | Uncertainty is carried in the data: claim confidence (`unverified`/`verified`/`disputed`/`wrong`) and source tiers. Human decisions are flagged by `relevance: act`. Installing external skills, and anything paid, is left to the Director by the instruments' `invoke` text. |
| EXTERNAL_VERIFIER | n/a | No specialized claims are produced by the tool itself. Individual entries that become load-bearing for a decision get a targeted check per Standing Rule 3. |

## Compensators (repo-level irreversible actions)

| Action | Undo | State after undo | Owner |
|--------|------|------------------|-------|
| `git push` to `origin/main` | `git revert <sha>` and push | History keeps the revert; content restored | Advisor session that pushed |
| `gh repo create` (public) | `gh repo edit --visibility private`, or `gh repo delete` (Director only) | Repo hidden or removed | Director |
| `rnd catalog sync` | `git checkout -- catalogs/<name>/catalog.json` | Previous pinned snapshot | Whoever ran the sync |
