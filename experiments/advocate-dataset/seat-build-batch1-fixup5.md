# BUILD BRIEF | Seat C | role-set: the Advocate, fix-up 5: a preflight that can finish | mcp-tool-shop-org/role-set | from R&D, with the Publisher | 2026-10-15

**Status:** R&D read fix-up 4 at `824391b` line by line against the hardware gate. Most of it holds:
- `num_ctx` is sized from the prompts and sent on every call;
- `num_predict` is capped;
- truncation is checked before and after each call;
- the journal is flushed before the critic loads;
- every model is unloaded after its call and on every exit path.

Three things block a grant. A fourth is a risk R&D infers but hasn't measured. **No grant until this turn passes.**

**Amended after Argon's read (2026-10-15).** Items 1, 3 and 4 below are tightened on four points:
- the preflight reads the card while the model is loaded;
- the card-clear wait compares against the run's starting baseline;
- the shutdown path never waits or raises a second time;
- the preflight keeps its prompt check.

**Build from this amended copy.** If you started from the earlier one, apply these items before handing back.

## What R&D found

Each finding is labelled with how it is known.

1. **The preflight can't finish.** *Measured.* R&D sent the preflight's exact request (prompt `x`, `num_predict` 1, `num_ctx` 2048, `think` false, Ollama 0.40.4) to `qwen3:8b` and `granite3.3:8b` on a CPU-only Ollama, with no GPU used. Both replied `done_reason: "length"` with `eval_count` 1. `preflight()` sends that call through `_complete_live`, which calls `_refuse_if_truncated`, which raises on any `done_reason` other than `"stop"`. So the preflight stops on the first model and measures nothing. The preflight test passes only because its `complete` is a fake that never runs the check.
2. **No `keep_alive` on any call.** *From the code.* No pilot or preflight call passes `keep_alive`, so every call gets `ollama_chat`'s `"30m"` default. A hard kill would leave the critic on the card for half an hour. This is brief item 5, which reached rnd 7 minutes before your commit, so you most likely built from the earlier copy. It's re-sent here.
3. **The preflight's limit leaves out the card's baseline.** *From the code and the last hand-back.* The cap the grant enforces is the whole card's `memory.used`: the stop was 24,576 MiB, against a baseline of about 2,200 MiB before any load. `preflight()` compares the model's `size_vram` alone to 24 GiB minus 1 GiB. A critic at 22 GiB would pass the preflight and still trip the cap.
4. **Overlap while one model unloads and the next loads.** *Inferred, not measured.* `unload` returns once Ollama accepts `keep_alive: 0`, and `/api/ps` drops the model before its memory is necessarily freed. Your last hand-back saw the critic's allocation climb while `/api/ps` was empty. If a writer's memory is still held when the critic starts loading, the card briefly holds both.

## The fix-up, in this order

1. **The preflight measurement call.**
   - Keep a one-token generation, so the model loads at the run's `num_ctx`.
   - In the preflight only, accept `done_reason` `"length"` or `"stop"` when `eval_count` is at most 1 **and** `prompt_eval_count` is below `num_ctx`. A `"length"` is accepted only because `num_predict` is 1, never because the prompt filled the window. Refuse anything else.
   - The pilot's own check stays exactly as it is.
   - Test it through the loopback server, not a fake `complete`. The server answers `done_reason: "length"`, `eval_count: 1`, and the preflight must record a row. A second case answers `"length"` with `eval_count` 2, and the preflight must refuse.
2. **`keep_alive: "60s"` on every pilot and preflight call** (item 5). A loopback test asserts it on a writer request, a critic request and a preflight request.
3. **Count the baseline.**
   - Before each preflight load, read the card's `memory.used` with `nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits`. That reading is the baseline.
   - Read `memory.used` again **while the model is loaded**: right after its one-token reply, before the unload. This is `loaded_mib`. The watchdog stops on `memory.used`, and `size_vram` leaves out the CUDA context and workspaces.
   - Refuse when the larger of `loaded_mib` and baseline plus `size_vram` exceeds the cap minus 1 GiB.
   - Print the baseline, `size_vram`, `loaded_mib` and the larger figure for each model.
   - A test feeds the parser real `nvidia-smi` CSV text.
4. **Wait for the card to clear between models,** in the pilot and in the preflight. After each unload:
   - wait until `/api/ps` no longer lists the model **and** `memory.used` is within 512 MiB of `initial_baseline_mib`. That reading is taken once, before the first model loads, in `preflight()` and in `run_pilot()`, never re-taken per load, so the floor can't creep up across 52 loads. A rise from another process also stops the run, and that is the safe direction;
   - poll each second, for at most 60 seconds;
   - if the card hasn't cleared by then, stop the run as a refusal. In this order:
     1. clear `loaded`;
     2. write the refusal to `pilot.jsonl` and flush it;
     3. raise.
   - The `finally` path sends `keep_alive: 0` for whatever is still loaded. It never runs the 60-second wait and never raises, so it can't block again or hide the first error.
   - A test makes the card fail to clear. It asserts the refusal line is in `pilot.jsonl`, the unload was sent once, and the run ended within one wait.

   Test the wait with an `nvidia-smi` fake that returns CSV text the way the real tool does.

## Hand back on #56, then stop

- The head SHA, the suite count and time, coverage, and CI inside 10 minutes. `pack verify` unchanged.
- The names and results of the new tests.
- Load no model.
- **R&D's review step before any grant:** R&D runs the preflight's request path against the CPU-only Ollama, with the GPU hidden, to show the measurement call is accepted against a real server. On CPU `size_vram` is 0, so the GPU sizes still come from the preflight under the grant.

**Stop.** R&D checks the diff and runs the CPU check. Then the Publisher decides on a preflight grant, and the pilot grant comes after the preflight's measured numbers.

## Gates

- The suite green at the coverage floor (`uv run pytest -m "not sweep" -n auto`). CI inside 10 minutes. `atlas check`. The identity scan CLEAN.
- Touch only `pilot.py`, `transport.py` if needed, `cli.py`, the tests and the CHANGELOG.
