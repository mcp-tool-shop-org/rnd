# rnd: how it works

Mapped at 2026-10-07 from commit b1705b4 by Atlas 1.24.0.

## What this is

The studio research bench: Markdown entries with tiered sources and checked claims, rig experiments, an instrument registry and rated catalogues, indexed and searched by the rnd CLI (Python, standard library only). (written by a person)

11 parts, mostly Markdown (70 files); code in Python (13), CSS (2), TypeScript (2), shell (2), Astro (1) and JavaScript (1). Work enters through 2 doors; the busiest is CI, which reaches 3 parts. It deploys a site to GitHub Pages.

## What changed since the last map

This is the first map.

## What comes in

1. **CI.** On a pull request to main; on a push to main touching 8 paths; or by hand. Runs verify.sh and tests/.
2. **Deploy site to GitHub Pages.** On a push to main touching 2 paths; or by hand. Runs site/astro.config.mjs and site/src/.

## What happens through CI

1. The workflow runs verify.sh in the repository root and tests/ in tests.
2. That reaches rnd (7 files).
3. It writes to entries/ and instruments/.
4. It uploads coverage to Codecov.

## Who reads the results

- **entries/** is read by tests/test_rnd.py (from tests).
- **instruments/** has no reader in this repository.

## The other doors

**Deploy site to GitHub Pages** runs site/astro.config.mjs and site/src/, and deploys the site.

## What breaks what

- **rnd** is imported only from tests, by 1 part (tests), and sits on the path of 1 door.

the repository root holds only shell files, which this map does not read, so what uses it cannot be seen.

## What tends to change together

No two source files changed together often enough to name.

Window: 180 days; a pair counts from 3 shared commits, since the window holds fewer than 30 qualifying commits.

## What no test touches

- **experiments** is imported by no test.

the repository root holds only shell files, which this map does not read, so whether a test touches it cannot be seen.

## Written but never read

- **instruments/** is written by rnd/cli.py and read by nothing else in this repository.

## Helpers that look duplicated

No two parts export a helper that looks alike.

## Generated, never hand-edited

- **entries/** is written by rnd/cli.py, except entries/_template.md, which it reads and people write.
- **instruments/** is written by rnd/cli.py.

## Hand-authored

People write .claude/, .github/, catalogs/, docs/ and site/; 3 writes with paths built at run time may land here.

## Where to start

.github/workflows/ci.yml → rnd/catalog.py → rnd/frontmatter.py

Read those in order to follow one pull request end to end.

## What this map cannot see

- 3 writes and 2 reads use paths built at run time and are not named here.
- 5 writes and 8 reads go to a path their caller passes, not to this repository.
- Statistics confidence is low: fewer than 30 qualifying commits in the window, and fewer than 20 source files reach 10 revisions.

Regenerate with `npx --yes @dogfood-lab/atlas map`.
