# BUILD BRIEF | Seat C | role-set: the Advocate, batch 1, the second fix-up | mcp-tool-shop-org/role-set | from R&D, with the Publisher | 2026-10-15

**Status:** R&D's verdict on the fix-up (#56 at `c10d0fd`), settled with Argon's round 6 answer (`argon-consult-round6.md` and its disposition). Argon read this brief too and found it ready, with two consistency points, both folded in: check-line numbers count as allowed, and out-of-scope relay points are phrased as the notes the drop rule names. The first fix-up landed most of round 5. Three things still stop the pilot. The relay slots' messages never reach the writer or the critic. The live path returns an object where the pilot expects text. And the checks and prompts would refuse honest prose from a real model. This turn fixes all three. Its hand-back is gated on a prompt-completeness test, so this class of defect can't come back. The Publisher holds the GPU grant until R&D passes this turn. Load no model.

## Where to work, and how to run the suite

- `feat/advocate-batch1` on #56, normal commits, no force-push. The pack stays at its approved hash, `975cf5e1…950b`.
- **Run the suite as CI does:** `uv run pytest -m "not sweep" -n auto`, about 2 minutes. A plain `uv run pytest` also rebuilds all 1,280 T10 puzzles under coverage, which takes about 45 minutes. Step 9 fixes that default.
- **File hygiene:** touch or delete only files you created in this turn or that this brief names. Check `git status` and `git diff --name-status origin/main` before every commit.

## The fix-up, in this order

**1. Records in their studio shapes, with no flag sheet (Q1, F6, F7, A7).**
- `render()` drops the lines `Over the cost cap`, `Paid model API`, `Paid run`, `Rollout`, `Pilot passed` and `Missing: none`. A record prints only what its shape carries. For example, a paid-run plan prints `printed cost $18.00`, `cost cap $40.00`, `compute: rented pod (offrig)` (or `compute: paid cloud model API`) and `local pilot: passed` (or `none`). A release record prints approval, provenance and the published-file check. The writer compares cost with cap itself. A missing decisive item still prints as `<item>: pending`.
- Immaterial lines read like studio lines (`runner ubuntu-latest`, `retries 0`), not `queue note NN`.
- **A failed check carries its own evidence on its line**, for example `check coverage floor: fail (0.71 against 0.75)`. The material figures are other metrics. `allowed_numbers()` also takes the numbers on the ledger's check lines, so a brief that reports a check's numbers never trips `stray_numbers`. B001 hides that whole line, so the hidden ledger never contradicts itself (slots 4 and 6).
- A passing reviewer verdict carries no `required changes`. Only a failing one does. Fix slot 9 and the reviewer shape in `_shape_figures`.
- Slot 9 is a pass with `coverage 0.82` against `floor 0.75`. Its B003 plant moves the coverage below the floor and fails the check. Slot 7 keeps its verdict and loses the artifact-size "cap". The negatives that change the verdict are 1, 2, 3, 6 and 9. The ones that keep it are 4, 5, 7, 8 and 10.
- A figure's metric is a natural noun (`cost`, `coverage`, `memory`, `files`, `dry run`), never the first word by default. Unit matching ignores case and accepts `h` and `hr`.

**2. Relay records are the message (F1, F5).**
- A kind B record is the message itself, in its direction's format. It names the sender and the recipient (the Director to a seat, a seat to the Director, a reviewer to a builder) and gives one line per point, out-of-scope points included. An out-of-scope point is phrased as the kind of note the procedure's drop rule names (`Budget note: redo the budget`, `Cost note: the pod would cost $30.00`, `Runner note: ubuntu-latest`), so the writer, and a mock that only reads the prompt, can apply the rule. It has no `Tripwires:` line: the writer must recognise the act.
- Slot 11's instruction becomes `rerun the suite on the patch`. `publish` is a public act.
- `PROCEDURES["B"]` states the recipient's scope rule for each direction. A builder keeps required code and check changes and drops cost notes. A seat keeps task instructions and thresholds and drops budget notes. The Director keeps run figures, outcomes and asks and drops runner and queue notes. The procedure also lists the nine tripwire phrases and the acts that cross each one, and says to answer `escalate: <phrase>` or `relay: <in-scope points>`.
- `check_scoped` also checks that every in-scope point's key phrase is in the relay, and that no out-of-scope point is, against `ledger.points` (the checks may read the ledger; only the writer and the mock writer may not).

**3. The writer's sections, and the headline (F3, A5).**
- `PROCEDURES["A"]` says what goes in each section. Section 1: the asks, or `none`. Section 2: every failed check and every tripwire phrase, or `Every check passed.` only when there are neither. Section 3: every material figure with its number and unit, and no Note lines. Section 4: every tripwire phrase, or `none`. Section 5: the verdict token before "you'd expect".
- `check_order` requires section 2 to name every failed check and every tripwire phrase, and refuses `Every check passed` when either exists. `render_brief` follows.
- `plant_exact` uses `_figure_shown` for unplanted figures and for the B003 replacement, the way `check_trace` does. Raw substring matching would refuse every natural negative.

**4. The critic says what its fields mean (F4).**
- `"verdict"` (or `"action"` for B) is the answer the **record** requires under the rules. It is not what the prose claims.
- `"faithful"` is true only when the prose reports every material figure, failed check and tripwire accurately, leaves out the Note lines, and states that verdict. For B, it is true when the relay carries every in-scope point, drops every out-of-scope one, and takes the right action. Otherwise it is false, and `"diff_item"` names the first wrong item.
- Kind B gets the relay rule and the scope rules from step 2. It never gets kind A's table. The mock critic follows the same definitions, so on a negative it returns the record's verdict, not the prose's.

**5. The live path returns text (A8, R&D's, new this round).** `_complete_live` returns `ollama_chat(...)`, which is a `Completion` object, not a `str`. Every live draft and every critic reply would be that object. The test hides this, because it monkeypatches `ollama_chat` to return `"text"`. Return `.text`. Test the live path through the real transport against a fake Ollama HTTP server on loopback, the way interlock's relay tests do. That test asserts the request carries `"think": false`, so `qwen3:8b` emits no reasoning block. (`ollama_chat` already defaults `think` to `False`, so Argon's A6 is covered. The test keeps it that way.)

**6. The prompt-completeness gate (F2, and the Publisher's gate).**
- A test over all 26 pilot texts. Every item the reference output depends on must appear in the rendered **writer** prompt: each point text, figure, failed check with its evidence, tripwire phrase or the act that implies it, ask and missing item. Every item the critic needs must appear in the rendered **critic** prompt.
- The mock writer builds its output by parsing the prompt text. It never reads `slot.ledger`. If the prompt lacks something, the mock fails.
- **The hand-back is gated on this test passing.** It is named in the hand-back, with its count.

**7. The probe (F8, F9).** Delete `brief_only_rate` and `chance_uniform` and their tests. `brief_only_probe` holds out each slot's positive and negative together, and prints its accuracy beside a 200-permutation null (the mean and the 95th percentile). It stays a smoke test.

**8. The turn 3 amendments this turn makes.** These replace the matching lines in the first fix-up's "Turn 3, amended" section. The verdict-changing negatives are slots 1, 2, 3, 6 and 9. The verdict-stable ones are 4, 5, 7, 8 and 10. The critic's fields mean what step 4 says.

**9. While CI runs: the 0.2.0 follow-ups, on their own PR.** These don't wait on any gate, so do them in CI's idle minutes, on a separate branch and PR off `main` (`chore/followups-0.2.0`):
- `pyproject.toml` `addopts` adds `-m "not sweep"`. The CI sweep job's explicit `-m sweep` still wins, so check that the dispatch sweep still selects its tests.
- `scripts/verify.ps1` and `verify.sh` follow `addopts`.
- `generate/__init__.py`'s docstring stops naming a T11 recipe.
- `load_record()` and `scripts/t10_variety_record.py`'s docstring name seeds 101–120 as well.
- `ci.yml`'s header stops naming an identity-scan step the workflow doesn't have.

None of these touches the record's hashed files. If one does, stop and say so. Hand that PR back separately, as `[Seat C → Publisher]`.

## Hand-back on #56, then stop

- The head SHA, the suite count and time, coverage, and CI inside 10 minutes. `pack verify` unchanged.
- **The gate:** the prompt-completeness test's name and its count (26 texts, every item present).
- **Argon's first read**, in full: the rendered writer prompt, critic prompt and reference output for slot 1 (`HIT 1`, with the tripwire in section 2), slot 6 (positive and negative, with no contradiction), slot 9 (the passing review, and its negative that crosses the floor), slot 11 (`rerun the suite`) and slot 16 (`force-push`).
- **The `pilot --mock` table** over all 26 texts, with the probe's accuracy beside its permutation null.
- The live-path test against the fake server, showing `"think": false` and text returned.
- The grant request, restated.

**Stop.** R&D reviews, Argon reads the items above, and the Publisher posts the grant only after R&D passes this turn.

## Gates (every push)

- The full suite green at the coverage floor (90), with the prompt-completeness test in it. CI inside 10 minutes.
- atlas: stage, `atlas map`, `atlas check`. The identity scan on a git archive of HEAD: CLEAN.
- The variety record regenerated, with its hash and closure tests green.

## Not in scope

- Loading any model. The pack's text. Traits 4–6, batches 2 and 3. The T10 generator's hashed files.
