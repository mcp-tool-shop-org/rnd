# Scorecard

**Repo:** rnd
**Date:** 2026-10-07
**Type tags:** `[all]` `[cli]` `[org]`

## Pre-Remediation Assessment

| Category | Score | Notes |
|----------|-------|-------|
| A. Security | 6/10 | No secrets or telemetry and an identity scan before pushes, but no SECURITY.md and no threat model in the README |
| B. Error Handling | 7/10 | Structured `code` / `message` / `hint` errors and documented exit codes; an unexpected exception still printed a raw traceback |
| C. Operator Docs | 7/10 | README and `--help` were current; no CHANGELOG, no `--version`, and a hint pointed at a missing `docs/schema.md` |
| D. Shipping Hygiene | 3/10 | Tests existed, but there was no verify script, no CI and no version tag |
| E. Identity (soft) | 1/10 | Description only: no logo, translations, landing page, homepage or topics |
| **Overall** | **24/50** | |

## Key Gaps

1. No CI: the tests and `rnd check` ran only when someone remembered to run them.
2. No SECURITY.md or threat model for a public repo that is written to fast.
3. Unexpected errors leaked raw tracebacks.
4. No identity: no logo, landing page, handbook or translations.

## Remediation Priority

| Priority | Item | Estimated effort |
|----------|------|-----------------|
| 1 | `verify.sh` plus CI (tests, `rnd check`, coverage, Atlas check) | small |
| 2 | SECURITY.md, a README threat model, and a structured last-resort error with `--debug` | small |
| 3 | Logo, landing page, handbook, translations, metadata | medium |

## Post-Remediation

| Category | Before | After |
|----------|--------|-------|
| A. Security | 6/10 | 10/10 |
| B. Error Handling | 7/10 | 10/10 |
| C. Operator Docs | 7/10 | 10/10 |
| D. Shipping Hygiene | 3/10 | 9/10 |
| E. Identity (soft) | 1/10 | 10/10 |
| **Overall** | 24/50 | 49/50 |

D stays at 9 because there is no dependency scanner in CI: there are no runtime
dependencies to scan. The site's npm tree is covered by `shipcheck deps`.
