---
id: 2026-11-24-bit-identical-parallel-scoring-for-a-game-evaluator-what-a-d
title: Bit-identical parallel scoring for a game evaluator: what a Deep Research audit found (seed 56)
date: 2026-11-24
kind: finding
relevance: act
fields: [evaluation, studio-tooling]
tags: [merchant-league, seed-56, harvest, determinism]
---

## Summary

Merchant League's decision scorer judges a move by forking the saved game at that decision and playing it to the
season's close under 16 shared random scenarios, all on the CPU. Its spec (`docs/decision-scorer.md`) leaves room for an
optional stage, S4, that would run those rollouts on several threads while keeping the output byte-identical at any
thread count. Before writing that stage we asked a Gemini Deep Research run four things:
- how to build bit-identical parallel scoring in Rust;
- what breaks it;
- how to test it;
- how to decide whether threads are worth building at all.

The report is `[aggregator]` AI output with 152 cited sources. We compared its claims with the merchant-league code at
885929c4, and none of its cited papers were read for this entry. Its main message agrees with the spec: measure before
building. Threads pay only if a real rollout costs well over a quarter of a second, and the timing bench we have today
cannot show where that time goes.

## Key points

- **Measure first.** The spec's main run is 94,080 rollouts. On one core that is about 2.6 hours at 0.10 s per
  rollout, 6.5 hours at 0.25 s and 13 hours at 0.5 s (our arithmetic). At or below a quarter of a second per rollout,
  one thread finishes overnight and parallel code buys little.
- **If threads are built, the standard library is enough.** The pattern is a scoped thread pool (`std::thread::scope`)
  that:
  - takes work from a shared atomic counter;
  - keeps results in per-worker lists;
  - writes them into pre-sized slots.

  That balances the load with no new crate. The final sum then runs in a fixed order on one thread, so the thread count
  cannot change the output bytes. The report advises against `rayon` here: it pulls in several more crates, and the
  report cites a 2026 security advisory against one of them.
- **Speedup is not the core count.** The report estimates about 6 to 7× on 8 performance cores, and less on chips that
  mix performance and efficiency cores. A cost table that divides by the core count overstates the gain.
- **Split the timing.** One number for a whole rollout cannot say which part costs most: file reads, hashing, parsing,
  the policy code or the engine step. The report wants:
  - each part timed on its own, cold and warm;
  - several process launches;
  - the decision point, not the single rollout, as the unit of the confidence interval;
  - 1 vs N threads measured on the real machine.
- **Determinism breaks hide in the engine, not in the scoring loop.** The report's list of causes:
  - hash maps with random seeds that feed tie-breaks;
  - thread-local and global counters;
  - floating-point settings that differ between threads or platforms;
  - different maths libraries.

  Its advice has three parts:
  - a lint that bans those types in the scorer;
  - an audit of the engine code a rollout reaches;
  - an optional per-turn state hash, so a future divergence can be found by bisection.
- **Each test should catch a named break.** The report's list:
  - thread counts that do and do not divide the work evenly, plus more threads than cores;
  - shuffled task order;
  - two decision points scored in one process, in both orders;
  - a worker that panics must fail the whole run;
  - the plain sequential path kept as the reference the threaded one must match.
- **Cross-machine checks.** The report wants golden output hashes on three operating systems for every change. That
  conflicts with our CI rules (one Linux runner). A one-off comparison of Windows against Linux at pilot time keeps most
  of the value, with the golden file then checked on Linux CI.

## Studio relevance

### What it contradicts in our design (read first)

| Finding | Merchant League at 885929c4 | Decision (2026-11-24) |
|---|---|---|
| Use standard-library scoped threads, not `rayon` | §6.1 of the spec adds `rayon` as one new dependency for parallel rollouts. But the scorer's dependency test allows five crates and fails if the manifest names `rayon` | Amend §6.1 to scoped threads with an atomic work counter and no new dependency. The existing test stays as the guard |
| Speedup must be measured | The spec's 8-core column divides one-core time by 8. The studio machine's CPU mixes performance and efficiency cores | The pilot measures 1 vs N threads, and the measured speedup replaces the division by 8 in the cost stop |
| File work per rollout is larger than assumed, with a gap between check and use | Every rollout reads and hashes the checkpoint's two files, then forks, and the fork reads both files again. That is four reads per rollout, about 376,000 in the main run | Check each checkpoint once before its batch and once after it, with no engine change. A fork in memory from already-checked bytes needs an engine change that the spec rules out, so it waits until the pilot shows that file work dominates |
| The timing bench cannot settle the question | The bench is skipped by default. It times five repeats of the whole rollout (check, fork and play together) per checkpoint | A pilot timing change splits read, hash, parse, policy and engine step. It times cold and warm, runs at least five processes, compares 1 vs N threads, and uses the CPU only, on a quiet machine |
| Threads before numbers | The spec calls S4 optional and already puts the pilot first | No S4 build now. The pilot's numbers decide |

### Decisions and actionables

1. S4 is not built now. The pilot timing comes first. Its change follows the checkpoint-trust change now in review,
   and reuses that change's checks for the verification before and after each batch.
2. The decision rule, in our numbers:
   - at or below about 0.25 s per rollout, stay on one thread;
   - between that and about 6 s, remove the repeated reads first, and add threads only if the run is still long;
   - above about 6 s, the spec's one-day stop fires, at a measured speedup near 6.5× (24 h × 6.5 ÷ 94,080 rollouts is
     about 6 s; our arithmetic, with 6.5× an assumed speedup).
3. If threads are built later, that change carries:
   - the scoped-thread pattern above;
   - the tests that each name a break;
   - a lint against hash maps and clocks in the scorer;
   - an audit of the engine code the rollout reaches;
   - the one-off Windows against Linux golden file.

   No new CI operating systems, and no `rayon`.

## Claims

- [verified] Spec §6.1 plans `rayon` as one new workspace dependency for parallel rollouts (via: `docs/decision-scorer.md:885` in mcp-tool-shop-org/merchant-league at 885929c4, read by R&D, 2026-11-24)
- [verified] The spec rules out `league-core` changes for S4 (via: `docs/decision-scorer.md:5` at 885929c4, read by R&D, 2026-11-24)
- [verified] The scorer's dependency test allows exactly five crates and fails if its `Cargo.toml` mentions `rayon` (via: `crates/league-scorer/tests/scorer_tests.rs:82-89` and `:197-208` at 885929c4, read by R&D, 2026-11-24)
- [verified] Each rollout reads and hashes the checkpoint's save and seal files, then forks, and the fork reads both files again (via: `crates/league-scorer/src/rollout.rs:47`, `:59`, `:72-84` and `:182`, and `crates/league-core/src/eval/host.rs:1195-1207`, at 885929c4, read by R&D, 2026-11-24)
- [verified] The main run is 94,080 rollouts, and the spec's 8-core column is the one-core time divided by 8 (via: `docs/decision-scorer.md:900` and `:906` at 885929c4, read by R&D, 2026-11-24)
- [verified] The timing bench is `#[ignore]`d and, after one warm-up, times five repeats of the whole `run_single_rollout` (via: `crates/league-scorer/tests/timing_bench.rs:49-50`, `:93`, `:140` and `:155-158` at 885929c4, read by R&D, 2026-11-24)
- [verified] The scenario draw hashes a domain tag, the seed, the checkpoint pair digest, the day, the scenario index and a counter, and takes no candidate input (via: `crates/league-scorer/src/scenarios.rs:21-28` at 885929c4, read by R&D, 2026-11-24)
- [verified] The scorer's source uses no `HashMap`, `HashSet`, thread-locals, `static mut`, `Instant` or `SystemTime` (via: `git grep` over `crates/league-scorer/src` at 885929c4, run by R&D, 2026-11-24)
- [verified] CI runs on `ubuntu-latest` only, builds `--locked` on a toolchain pinned to 1.100.0, and runs `cargo audit --deny warnings` (via: `.github/workflows/ci.yml:39`, `:72`, `:202` and `:229`, and `rust-toolchain.toml`, at 885929c4, read by R&D, 2026-11-24)
- [verified] The studio machine reports an Intel Core Ultra 9 285K with 24 cores (via: `Get-CimInstance Win32_Processor`, run by R&D, 2026-11-24)
- [unverified] `rayon` adds six crates, and a 2026 advisory (RUSTSEC-2026-0204) covers one of them, crossbeam-epoch (the report's reading; not checked. Not load-bearing: the dependency test rules `rayon` out either way)
- [unverified] About 6.0 to 7.3× speedup on 8 performance cores, and less on hybrid chips (the report's own estimates; its Apple figures come from press summaries)
- [unverified] Most determinism breaks in practice come from seeded hash maps, thread-local or global state, and differences in floating-point settings and maths libraries (the report's survey; the scorer crate was checked above, but the engine was not audited)

## Sources

- [aggregator] https://gemini.google.com/ — Gemini Deep Research (Gemini 4 Carbon, High), 2026-11-24: "Bit-Identical Parallel Simulation Scoring in Rust: Architecture, Failure Modes, Verification, and Pilot Decision Framework"
- [primary] https://github.com/mcp-tool-shop-org/merchant-league — the game, its decision-scorer spec (`docs/decision-scorer.md`) and the `league-scorer` crate, read at 885929c4
- [primary] https://doc.rust-lang.org/std/thread/fn.scope.html — Rust standard library, `std::thread::scope` (cited by the report; not read for this entry)
- [primary] https://rustsec.org/advisories/RUSTSEC-2026-0204 — RustSec advisory for crossbeam-epoch (cited by the report; not read)
- [primary] https://kar.kent.ac.uk/33611/45/p63-kaliber.pdf — Kalibera and Jones (2013), Rigorous Benchmarking in Reasonable Time, ISMM (cited by the report; not read)
- [primary] https://users.cs.northwestern.edu/~robby/courses/322-2013-spring/mytkowicz-wrong-data.pdf — Mytkowicz, Diwan, Hauswirth and Sweeney (2009), Producing Wrong Data Without Doing Anything Obviously Wrong!, ASPLOS (a copy on a course page; cited by the report; not read)
- [primary] https://github.com/tigerbeetle/tigerbeetle/blob/main/docs/internals/vopr.md — TigerBeetle's VOPR simulator documentation, on deterministic simulation testing (cited by the report; not read)
