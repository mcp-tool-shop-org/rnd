# rnd: how it works

Mapped at 2026-10-09 from commit 1443c84 by Atlas 1.24.0.

## What this is

The studio research bench: Markdown entries with tiered sources and checked claims, rig experiments, an instrument registry and rated catalogues, indexed and searched by the rnd CLI (Python, standard library only). (written by a person)

12 parts, mostly Python (41 files), shell (9), CSS (2), TypeScript (2), Astro (1), HTML (1) and JavaScript (1). Work enters through 4 doors; the busiest is CI, which reaches 4 parts. It publishes to PyPI. It deploys a site to GitHub Pages. People run rnd.

## What changed since 2026-10-08 (922b886)

- experiments/natural-errors/data/ is now written by experiments/natural-errors/build.py.
- experiments/natural-errors/data/baselines_p1.json is now written by experiments/natural-errors/baselines_p1.py.
- experiments/natural-errors/data/corrections.json is now written by experiments/natural-errors/build_corrections.py.
- And 15 more new writers and readers of places.
- datapacks/hymn-arrangements/datapack.json is new and belongs to no part, so atlas check fails on it against the previous map.
- datapacks/hymn-arrangements/hosted.json is new and belongs to no part, so atlas check fails on it against the previous map.
- datapacks/hymn-arrangements/spec.json is new and belongs to no part, so atlas check fails on it against the previous map.
- And 4 more new files that belong to no part.
- 109 files added and 24 changed content, across 9 parts.

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
- **experiments/natural-errors/data/** is written by experiments and read by experiments; a hand edit reaches every reader.
- **experiments/natural-errors/data/split.json** is written by experiments and read by experiments; a hand edit reaches every reader.

the repository root holds only shell files, which this map does not read, so what uses it cannot be seen.

## What tends to change together

- **rnd/cli.py** and **tests/test_rnd.py** changed together in 4 of 7 commits.

Confidence is low: fewer than 25 source files reach 10 revisions in the window.

Window: 180 days; a pair counts from 3 shared commits, since 2 source files reach 10 revisions; the floor rises to 10 when 25 do.

## What no test touches

Every code part this map reads is imported by at least one test.

the repository root holds only shell files, which this map does not read, so whether a test touches it cannot be seen.

experiments/cuda-graphs/test_graphed_heads.py runs in no workflow.

## Written but never read

- **experiments/natural-errors/data/baselines_p1.json** is written by experiments/natural-errors/baselines_p1.py and read by nothing else in this repository.
- **experiments/natural-errors/data/corrections.json** is written by experiments/natural-errors/build_corrections.py and read by nothing else in this repository.
- **instruments/** is written by mcptoolshop_rnd/cli.py and read by nothing else in this repository.

## Helpers that look duplicated

No two parts export a helper that looks alike.

## Generated, never hand-edited

- **entries/** is written by mcptoolshop_rnd/cli.py, except entries/_template.md, which it reads and people write.
- **experiments/kev-judge-finetune/results/summary.json** is written by experiments/kev-judge-finetune/summarise.py.
- **experiments/natural-errors/data/** is written by experiments/natural-errors/build.py, except experiments/natural-errors/data/answers.json, experiments/natural-errors/data/questions.json, experiments/natural-errors/data/screen.json, experiments/natural-errors/data/screen_ctx_pilot.json, experiments/natural-errors/data/screen_extra.json and experiments/natural-errors/data/selection.json, which it reads and people write.
- **experiments/natural-errors/data/baselines_p1.json** is written by experiments/natural-errors/baselines_p1.py.
- **experiments/natural-errors/data/corrections.json** is written by experiments/natural-errors/build_corrections.py.
- **experiments/natural-errors/data/split.json** is written once by experiments/natural-errors/make_split.py when absent.
- **instruments/** is written by mcptoolshop_rnd/cli.py.

## Hand-authored

People write .claude/, .github/, catalogs/, docs/ and site/; 4 writes with paths built at run time may land here.

## Where to start

mcptoolshop_rnd/cli.py → mcptoolshop_rnd/catalog.py → mcptoolshop_rnd/frontmatter.py

Read those in order to follow one run of rnd end to end. This path follows rnd (a command people run) from its entry, since CI runs only tests and checks.

## What this map cannot see

- 4 imports could not be resolved: `experiments/verifier-gold/build_grounded.py` imports a path built at run time; `rnd/__init__.py` imports a path built at run time; `tests/test_packaging.py` imports `rnd.cli`, which is no module on its import path and no declared dependency; and 1 more.
- 4 writes and 6 reads use paths built at run time and are not named here.
- 11 writes and 21 reads go to a path their caller passes, not to this repository.
- 3 reads go to the directory the command is run in (entries and instruments), not to this repository.
- 1 read goes to the directory the command is run in or a path its caller passes, not to this repository.
- 7 files belong to no part: datapacks/hymn-arrangements/datapack.json, datapacks/hymn-arrangements/hosted.json, datapacks/hymn-arrangements/spec.json and 4 more.
- Statistics confidence is low: fewer than 25 source files reach 10 revisions in the window.

Regenerate with `npx --yes @dogfood-lab/atlas map`.
