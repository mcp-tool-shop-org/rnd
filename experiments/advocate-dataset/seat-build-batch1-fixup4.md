# BUILD BRIEF | Seat C | role-set: the Advocate, fix-up 4: size the context, keep the record | mcp-tool-shop-org/role-set | from R&D, with the Publisher | 2026-10-15

**Status:** the pilot under `publisher-5090-advocate-pilot-2026-10-15` stopped at the 24 GiB VRAM cap when the critic loaded. It left no record (hand-back on #56). R&D's diagnosis, from the code at `e99b1b4`:
- **The context:** the pilot never passes `num_ctx`, so every call uses `transport.ollama_chat`'s default of 16,384 tokens.
- **The writers:** at that context the 8B writers sat at about 10 GB each, about twice their weights.
- **The critic:** `gemma4:31b` measured 20.3 GB at a 2,048 context in the Publisher's 0.40.4 smoke. At 16,384 its key-value cache pushed it past the cap before it replied.
- **The record:** the pilot writes `pilot.json` only at the end, so a stop leaves nothing to read.
- **R&D's miss:** the grant was sized from the model weights alone, and R&D missed the default context in review.

This turn fixes all of it. Load no model. The next grant's preflight measures the critic once.

## The fix-up, in this order

1. **Size the context to the prompts.**
   - Add `num_ctx` to `_complete_live` and pass it on every call.
   - Compute it from the pilot, not by guessing. Take the longest rendered writer prompt and the longest rendered critic prompt over all 26 texts, at a conservative 3 characters per token. Add each call's output budget: a brief of at most 130 words, or a critic JSON reply. Round up to a power of two, at least 2,048.
   - Record the two values (writer, critic) in the run record.
   - A test asserts that every pilot prompt plus its output budget fits its `num_ctx` by that estimate.
2. **Catch silent truncation.**
   - Ollama cuts a prompt longer than `num_ctx` without an error. After every live call, compare the reply's `prompt_tokens` with `num_ctx`.
   - If the prompt filled the window (at least `num_ctx` minus the output budget), stop the run and record it as a truncation, never as a draft.
   - Test it through the loopback server, with a reply that reports a full window.
3. **Keep the record as you go.**
   - Append each finished text's full record (ledger, prose, checks, attempts, critic payload) to `pilot.jsonl` in the run directory, flushed, as soon as it's done.
   - `pilot.json` and `read.md` are still written at the end, from that file.
   - `pilot --report <run dir>` works from `pilot.jsonl` alone, so a stopped run can still be read.
   - Test it: a run made to stop partway leaves a readable `pilot.jsonl` and a `read.md` built from it.
4. **A preflight the grant can use.** Add `pilot --role advocate --preflight --grant <id> --heartbeat <file>`. It doesn't write anything or call a writer. In turn, with nothing else loaded, it:
   - runs each of the three models once, at its computed `num_ctx`, on a one-token prompt;
   - reads `size_vram` from `/api/ps`;
   - unloads it.

   It prints the three sizes and refuses if any is above the grant's VRAM cap minus 1 GiB. The Publisher sizes the next grant from those measured numbers, not from weights.
5. **The granite `checked_by`,** now, since there's no run record to wait for: `"the Publisher, 2026-10-15 (digest fd429f23…, bundled Apache-2.0; card ibm-granite/granite-3.3-8b-instruct@51dd4bc, apache-2.0)"`.

## Hand back on #56, then stop

- The head SHA, the suite count and time, coverage, and CI inside 10 minutes. `pack verify` unchanged.
- The computed `num_ctx` for writers and critic, with the longest prompt's estimated tokens for each.
- The four new tests' names and results.
- **The grant request, restated:**
  - the same three models and pins, one at a time;
  - the preflight runs first under the grant, and the peak is taken from what it measures;
  - the caps stay 90 minutes and 24 GiB unless the preflight shows the critic needs more, in which case the request names the measured figure and the Publisher decides.

**Stop.** R&D checks the diff, the Publisher posts a new grant, the preflight runs under it, and then the pilot runs.

## Gates

- The suite green at the coverage floor (`uv run pytest -m "not sweep" -n auto`). CI inside 10 minutes. `atlas check`. The identity scan CLEAN.
- Touch only the files this brief names: `pilot.py`, `transport.py` if needed, `cli.py`, `writers.json`, the tests and the CHANGELOG.
