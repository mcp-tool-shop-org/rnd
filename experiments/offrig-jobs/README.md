# offrig --jobs: concurrent claims on the 5090

**Decision it informs:** whether `offrig verify calibrate --jobs N` (several claims in flight against one local Ollama)
may be used on pinned study runs, such as distill-ladder's teacher legs.

**Status: closed (2026-10-23).** Verdict: no `--jobs` above 1 on pinned studies. A single stream is byte-identical run to
run; `--jobs 2` is 1.59x faster but changes answers. Unpinned work may use 2.

- Design: [PLAN.md](PLAN.md)
- Results: [results/RESULTS.md](results/RESULTS.md)
- Runner (published copy): [scripts/run_arms.sh](scripts/run_arms.sh)
- Runs: oj1 (tooling-fault: offrig's cold-load timeout), oj2 (results), in experiment.json
