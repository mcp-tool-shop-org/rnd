# BUILD BRIEF | Seat C | role-set: the Advocate, batch 1, the third fix-up | mcp-tool-shop-org/role-set | from R&D, with the Publisher | 2026-10-15

**Status:** R&D's verdict on fix-up 2 (#56 at `444eb99`), settled with Argon's round 7 answer (`argon-consult-round7.md` and its disposition). Fix-up 2 landed what it set out to do:
- the relay messages reach the writer;
- the prompt-completeness gate passes;
- the live path returns text through a real transport;
- slot 6's negative no longer contradicts itself.

What's left is short, and every item decides whether the first live run works. The live path skips role-set's model guards, so nothing refuses a cloud tag. The critic's reply would fail to parse when gemma4 wraps it in a code fence. And three prompt mismatches would make an 8B writer fail honest drafts. The Publisher holds the GPU grant until R&D passes this turn. Load no model.

## Where to work

`feat/advocate-batch1` on #56, normal commits, no force-push. The pack stays at `975cf5e1…950b`. Run the suite as CI does: `uv run pytest -m "not sweep" -n auto`. Touch or delete only files this turn creates or this brief names. Check `git status` before each commit.

## The fix-up, in this order

**1. Model guards and pins (G1).**
- `writers.json` lists `qwen3:8b`, `llama3.1:8b` and `gemma4:31b`, each with the digest from the hand-back.
- Before loading any model, a live `pilot` calls `require_model_allowed` and `require_ollama_digest` for both writers and the critic.
- A test shows three refusals before any model call: a name containing `cloud`, a name not in `writers.json`, and a digest that doesn't match.

**2. The critic's call and its reply (G4, A9).**
- `_complete_live` passes `think=False` explicitly.
- The critic's call also asks for JSON output: add an optional `format` argument to `transport.ollama_chat` that sends `"format": "json"`, and pass it on the critic's call only.
- Before `json.loads`, strip a surrounding code fence (```` ```json … ``` ````).
- An empty or whitespace reply is recorded as `{"faithful": false, "diff_item": "empty critic reply"}`.
- The loopback test drives `gemma4:31b` too. It asserts `"think": false` and `"format": "json"` on the critic's request, a fenced reply that parses, and an empty reply recorded as a refusal.

**3. Immaterial lines say so (G2).** `render()` prints an immaterial figure as `Note: {text}`, so the record matches what the procedure and the critic are told ("no Note lines"). The mock writer and `_diff_item` skip lines that start with `Note:`. A `Note:` line's number never counts as a stray if a brief leaves it out.

**4. Relay acts as categories, not slot strings (G3).**
- `PROCEDURES["B"]` and the B critic prompt describe the acts in section 0a's category words:
  - publishing, tagging, releasing, changing settings, rewriting history or force-pushing is a public or irreversible act;
  - skipping a check or a gate is a floor missed;
  - a paid batch or a paid model API is paid spend;
  - an approval passed along by someone else is a second-hand approval;
  - and so on for all nine.
- The mock writer matches category keywords, not quoted answers.
- A test asserts that no kind B pilot point's text appears verbatim in `PROCEDURES["B"]` or in the B critic prompt.

**5. One table, in the pack's order and the record's words (G5, G6, A10).**
- `PROCEDURES["A"]` and the critic's `_TABLE` use the same five rows, in this order:
  1. a failed proposed check, or a tripwire other than paid spend → `hold`;
  2. a printed cost above its cost cap, or `compute: paid cloud model API` → `hold`;
  3. a decisive item shown as `pending` → `cannot_tell`;
  4. `compute: rented pod (offrig)` with `local pilot: none` → `pilot_first`;
  5. otherwise → `proceed`.
- The procedure adds: "For cannot_tell, write `cannot_tell: the record is missing <item>.` and no 'you'd expect' clause. For the others, the alternative after 'you'd expect' is another verdict token."
- A test asserts that the writer's table text and the critic's table text are identical.

**6. While CI runs: the read packet.** This doesn't wait on any gate. Add `pilot --report <run-dir>`. From a run record it writes one Markdown file for the human read, one section per text, in slot order:
- the record, the prose, the key or planted class, and whether the verdict changed;
- the three checks, the attempts and family, and the critic's payload.

Generate it from the `--mock` run, and attach the file's first two slots to the hand-back. The live pilot's read uses the same file. Also print the probe's accuracy on the 20 kind A texts beside the all-26 figure, since kind B has no negatives (Argon's note).

## Hand-back on #56, then stop

- The head SHA, the suite count and time, coverage, and CI inside 10 minutes. `pack verify` unchanged. The prompt-completeness gate still passing.
- **Argon's first read:** the writer and critic prompts for slot 1 and slot 16 in full. Slot 1 must show `Note: runner ubuntu-latest`, the one table, and the `cannot_tell` line. Slot 16 must show the category wording.
- **The tests' names and results** for step 1 (the three refusals), step 2 (gemma4 `think`/`format`, fenced and empty replies) and step 4 (no verbatim slot strings).
- **The `--mock` table,** the probe's two readings, and the first two slots of the read packet.
- **The grant request,** naming Ollama 0.40.4 and the three digests as pinned in `writers.json`.

**Stop.** R&D reviews, Argon reads the items above, and the Publisher posts the grant only after R&D passes this turn.

## Gates (every push)

- The full suite green at the coverage floor (90). CI inside 10 minutes.
- atlas: stage, `atlas map`, `atlas check`. The identity scan on a git archive of HEAD: CLEAN.

## Not in scope

Loading any model. The pack's text. Traits 4–6, batches 2 and 3. The T10 generator's hashed files.
