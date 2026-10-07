# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).
Library content (entries, experiments, catalogue reviews) changes daily and is
not listed here; this log covers the `rnd` tool and the repo's structure.

## [Unreleased]

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
