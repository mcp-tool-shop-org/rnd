# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
Versions have five segments, `MAJOR.MINOR.PATCH.MICRO.NANO`. The first three
follow [Semantic Versioning](https://semver.org/) for the `rnd` tool. MICRO marks a
structural library change (a new experiment, catalogue or instrument family), and
NANO an ordinary library update (entries filed or revised, results added).
`python -m rnd bump` writes each section; `1.0.0` reads as `1.0.0.0.0`.

## [Unreleased]

## [1.1.1.0.2] - 2026-10-07

- Planted-defects program: adopted by ai-jam-sessions; calibrated review tracked as ai-jam-sessions #89
- Updated `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.1] - 2026-10-07

- Planted-defects program for sung mixes: an automated planter-versus-detector loop with a regret reward, a MERT frame-level detector, and the Director's catch trials setting the audibility line (seven research agents' findings)
- Added `2026-10-07-planted-defects-program-for-sung-mixes`: Planted defects for sung mixes — an automated planter-versus-detector loop, anchored by the listener's measured threshold

## [1.1.1.0.0] - 2026-10-07

- Coverage bar raised to 90%: CI fails under 90% and Codecov's project and patch targets are 90%
- 45 tests (was 25), including end-to-end CLI tests of every command, catalogue sync with gh mocked, and rnd bump in a real git repo; rnd/ coverage 96% (was 63%)

## [1.1.0.0.0] - 2026-10-07

- Added `rnd bump`: five-segment versions (MAJOR.MINOR.PATCH.MICRO.NANO) with a CHANGELOG section written from the files changed since the last tag
- Kev-4B and Kev-9B measured against hosted Jev and OpenJev on sense-si's 124 phrases, 0-shot and with knowledge in context
- Added `2026-10-07-open-jev-style-decision-models`: Open Jev-style decision models — the landscape, checked against primary sources
- Updated `2026-10-07-openjev-and-open-jev-alternatives`: OpenJev and the other open "Jev" models — what each one is
- Updated experiment `openjev-vs-jev`

## [1.0.0] - 2026-10-07

### Added

- `rnd` CLI over a Markdown research library: `build`, `check`, `search`, `show`,
  `list`, `tools`, `stats`, `new`, `catalog`, `readouts`, `sql`, each listing with `--json`.
- Entry format with source tiers (`primary`, `secondary`, `aggregator`, `user`, `rig`)
  and claim confidence (`unverified`, `verified`, `disputed`, `wrong`; `verified`
  needs a `via:` note).
- SQLite FTS5 index (`rnd.db`), rebuilt automatically when files change; the previous
  index is kept when a rebuild meets errors.
- Instrument registry (`instruments/`) of the studio tools research can call.
- NVIDIA skills catalogue mirror (398 skills, 18 lanes) with a studio-fit review.
- `rnd readouts`: read-only federated search across the readouts knowledge bases,
  with prefix matching and `--any`.
- `experiments/` for rig measurements, with pinned inputs and result receipts.
- `--version`, and `--debug` to show a traceback; unexpected errors otherwise print
  a structured `INTERNAL` error and exit 3.
- `verify.sh` (tests, library check, index build, smoke), CI, landing page and handbook.

### Fixed

- The `rnd sql` error hint pointed at a missing `docs/schema.md`; it now shows how
  to list the tables.
