# rnd: how it works

Mapped at 2026-10-07 from commit 485feea by Atlas 1.24.0.

## What this is

The studio research bench: Markdown entries with tiered sources and checked claims, rig experiments, an instrument registry and rated catalogues, indexed and searched by the rnd CLI (Python, standard library only). (written by a person)

11 parts, mostly Markdown (71 files) and JSON data (18); code in Python (18), shell (3), CSS (2), TypeScript (2), Astro (1) and JavaScript (1). Work enters through 2 doors; the busiest is CI, which reaches 3 parts. It deploys a site to GitHub Pages.

## What changed since 2026-10-07 (cc7a041)

- CI's push trigger now also names `.coveragerc` and `codecov.yml`.
- CHANGELOG.md is now read by tests/test_cli.py.
- README.md is now read by tests/test_cli.py.
- entries/_template.md is now also read by tests/test_cli.py.
- And 1 more new writer or reader of a place.
- 3 files added and 4 changed content, across 4 parts.

## What comes in

1. **CI.** On a pull request to main; on a push to main touching 10 paths; or by hand. Runs verify.sh and tests/.
2. **Deploy site to GitHub Pages.** On a push to main touching 2 paths; or by hand. Runs site/astro.config.mjs and site/src/.

## What happens through CI

1. The workflow runs verify.sh in the repository root and tests/ in tests.
2. That reaches rnd (8 files).
3. It writes to entries/ and instruments/.
4. It uploads coverage to Codecov.

## Who reads the results

- **entries/** is read by rnd/release.py, and by 2 tests.
- **instruments/** is read by rnd/release.py.

## The other doors

**Deploy site to GitHub Pages** runs site/astro.config.mjs and site/src/, and deploys the site.

## What breaks what

- **rnd** is imported only from tests, by 1 part (tests), and sits on the path of 1 door.
- **entries/** is written by rnd and read by rnd, and by 2 tests; a hand edit reaches every reader.

the repository root holds only shell files, which this map does not read, so what uses it cannot be seen.

## What tends to change together

No two source files changed together often enough to name.

Window: 180 days; a pair counts from 3 shared commits, since the window holds fewer than 30 qualifying commits.

## What no test touches

- **experiments** is imported by no test.

the repository root holds only shell files, which this map does not read, so whether a test touches it cannot be seen.

## Written but never read

Every written place has a reader.

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

- 3 writes and 3 reads use paths built at run time and are not named here.
- 8 writes and 16 reads go to a path their caller passes, not to this repository.
- 1 read goes to the directory the command is run in or a path its caller passes, not to this repository.
- Statistics confidence is low: fewer than 30 qualifying commits in the window, and fewer than 25 source files reach 10 revisions.

Regenerate with `npx --yes @dogfood-lab/atlas map`.
