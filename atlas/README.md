# rnd: how it works

Mapped at 2026-10-08 from commit 922b886 by Atlas 1.24.0.

## What this is

The studio research bench: Markdown entries with tiered sources and checked claims, rig experiments, an instrument registry and rated catalogues, indexed and searched by the rnd CLI (Python, standard library only). (written by a person)

12 parts, mostly Markdown (74 files) and JSON data (25); code in Python (24), shell (5), CSS (2), TypeScript (2), Astro (1) and JavaScript (1). Work enters through 4 doors; the busiest is CI, which reaches 4 parts. It publishes to PyPI. It deploys a site to GitHub Pages. People run rnd.

## What changed since 2026-10-08 (33fa5db)

- rnd now imports mcptoolshop_rnd.
- tests now imports mcptoolshop_rnd.
- CI's push trigger now also names `mcptoolshop_rnd/**`, `pyproject.toml` and `uv.lock`.
- CI now also checks mcptoolshop_rnd/ and rnd/.
- Release (.github/workflows/release.yml) is a new door. It starts when a release is published. It runs mcptoolshop_rnd/__init__.py and verify.sh. It checks mcptoolshop_rnd/ and rnd/.
- And 1 more change to a door.
- entries/ is now also written by mcptoolshop_rnd/cli.py.
- experiments/kev-judge-finetune/results/summary.json is now written by experiments/kev-judge-finetune/summarise.py.
- instruments/ is now also written by mcptoolshop_rnd/cli.py.
- And 7 more new writers and readers of places.
- experiments was authored and is now mixed.
- mcptoolshop_rnd is a new part, drawn from `mcptoolshop_rnd/**`.
- 19 files added, 2 removed, 5 moved and 26 changed content, across 8 parts.

## What comes in

1. **CI.** On a pull request to main; on a push to main touching 13 paths; or by hand. Runs verify.sh and tests/; checks mcptoolshop_rnd/ and rnd/.
2. **Release.** When a release is published. Runs mcptoolshop_rnd/__init__.py and verify.sh; checks mcptoolshop_rnd/ and rnd/.
3. **Deploy site to GitHub Pages.** On a push to main touching 2 paths; or by hand. Runs site/astro.config.mjs and site/src/.
4. **rnd** (a command people run). Runs mcptoolshop_rnd/cli.py.

## What happens through CI

1. The workflow runs verify.sh in the repository root and tests/ in tests; it checks mcptoolshop_rnd/ in mcptoolshop_rnd and rnd/ in rnd.
2. It writes to entries/ and instruments/.
3. It uploads coverage to Codecov.

## Who reads the results

- **entries/** is read by 2 tests.
- **instruments/** has no reader in this repository.

## The other doors

**Release** runs mcptoolshop_rnd/__init__.py and verify.sh, checks mcptoolshop_rnd/ and rnd/, and publishes to PyPI.

**Deploy site to GitHub Pages** runs site/astro.config.mjs and site/src/, and deploys the site.

**rnd** (a command people run) runs mcptoolshop_rnd/cli.py and writes to entries/ and instruments/.

## What breaks what

- **mcptoolshop_rnd** is imported by 1 part (rnd), and by 1 more only from tests; it sits on the path of 3 doors.
- **rnd** is imported only from tests, by 1 part (tests), and sits on the path of 2 doors.
- **the repository root** is imported by no other part and sits on the path of 2 doors.

the repository root holds only shell files, which this map does not read, so what uses it cannot be seen.

## What tends to change together

No two source files changed together often enough to name.

Window: 180 days; a pair counts from 3 shared commits, since 1 source file reaches 10 revisions; the floor rises to 10 when 25 do.

## What no test touches

- **experiments** is imported by no test.

the repository root holds only shell files, which this map does not read, so whether a test touches it cannot be seen.

## Written but never read

- **instruments/** is written by mcptoolshop_rnd/cli.py and read by nothing else in this repository.

## Helpers that look duplicated

No two parts export a helper that looks alike.

## Generated, never hand-edited

- **entries/** is written by mcptoolshop_rnd/cli.py, except entries/_template.md, which it reads and people write.
- **experiments/kev-judge-finetune/results/summary.json** is written by experiments/kev-judge-finetune/summarise.py.
- **instruments/** is written by mcptoolshop_rnd/cli.py.

## Hand-authored

People write .claude/, .github/, catalogs/, docs/ and site/; 4 writes with paths built at run time may land here.

## Where to start

mcptoolshop_rnd/cli.py → mcptoolshop_rnd/catalog.py → mcptoolshop_rnd/frontmatter.py

Read those in order to follow one run of rnd end to end. This path follows rnd (a command people run) from its entry, since CI runs only tests and checks.

## What this map cannot see

- 3 imports could not be resolved: `rnd/__init__.py` imports a path built at run time; `tests/test_packaging.py` imports `rnd.cli`, which is no module on its import path and no declared dependency; `tests/test_packaging.py` imports `rnd.store`, which is no module on its import path and no declared dependency.
- 4 writes and 3 reads use paths built at run time and are not named here.
- 9 writes and 18 reads go to a path their caller passes, not to this repository.
- 3 reads go to the directory the command is run in (entries and instruments), not to this repository.
- 1 read goes to the directory the command is run in or a path its caller passes, not to this repository.
- Statistics confidence is low: fewer than 25 source files reach 10 revisions in the window.

Regenerate with `npx --yes @dogfood-lab/atlas map`.
