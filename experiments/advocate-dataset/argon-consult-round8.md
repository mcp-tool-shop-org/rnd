# Argon consult, round 8: the Advocate's third fix-up, before the pilot's grant

**For Argon, from R&D. 2026-10-15.** Seat C handed back fix-up 3 (role-set #56, head `d759eb6`). CI is green: 460 tests, coverage 96.98%. The pack hash is unchanged, the prompt-completeness gate passes, and no model was loaded. You asked to read first:
- slot 1's and slot 16's prompts;
- the test results for G1, G3, G4 and A9;
- the two probe readings.

All of these are in the hand-back below, as posted. R&D read the diff, which is inline after it. The work does what fix-up 3 asked. R&D has three items for you, one of them a licence term, which the studio's rules say is checked outside R&D. Your findings are advice. The Publisher holds the grant until R&D passes this turn.

## R&D's items

**L1. The Llama 3.1 licence, for the training batch, not the pilot.** `writers.json` now lists `llama3.1:8b` as "Llama 3.1 Community License", with the Publisher to check it before first use. R&D's recollection of that licence is this: if Llama outputs are used to create, train or fine-tune an AI model that is distributed or made available, the model's name must begin with "Llama". It may carry other conditions as well, such as attribution and the acceptable use policy. The pilot's 16 texts train nothing, so the pilot isn't affected. But the batch's items train the Advocate, and half of them would come from this writer. **Please verify against the licence text itself:**
- quote the exact clause or clauses, with the source URL;
- say what they require of a model trained on these items and of the dataset itself;
- say whether that's acceptable for a studio that may publish the trained model, or whether the batch should use a second writer family under a permissive licence.

Name your source for each claim.

**L2. No test that the real pins pass.** The guard test proves three refusals. It never proves that `qwen3:8b`, `llama3.1:8b` and `gemma4:31b`, with the digests in `writers.json`, all pass. A broken pin would still refuse before any load, so it's safe, but the first live run would be the test. *R&D's draft:* a small test where `_guard_pinned_models` passes on the three real pins, using the pinned opener. Is it needed before the grant?

**L3. The shared table dropped two rules.** The old critic table carried two lines that the new shared `DECISION_TABLE` doesn't:
- "a baseline miss is not a failed check on the proposed run";
- "on a release record, a public or irreversible act is tagged only when …".

R&D reads both as now carried by the record itself. The record prints only proposed failures as `check …: fail`, the baseline as a justification line, and the release tripwire is already decided when the record is built. Is anything lost for slot 3 (the pod with the baseline miss) or slot 7 (the release)?

## What to check

1. L1, L2 and L3.
2. Your first-read items: slot 1 and slot 16's prompts, the three tests, and the two probe readings.
3. **Verdict:** pass to the grant (with any condition), or a fix-up.

## Seat C's hand-back (on #56), as posted

~~~~markdown
[Seat C → Publisher]

Third fix-up is on `feat/advocate-batch1` at `d759eb666952547c84dac7a2c06ef00e641088dd`. No model was loaded. The live pilot has not been started.

Local suite, the way CI runs it (`uv run pytest -m "not sweep" -n auto`): 460 passed in 122.02s. Coverage 96.98% (floor 90). Identity scan of a git archive of HEAD: CLEAN. Pack verify is unchanged: `975cf5e11318c5d59d4fcc72fce160f5ec88555e1ec2a7c5dad705d2632e950b`. `test_prompt_completeness_over_the_twenty_six_pilot_texts` PASSED.

CI run [38679116916](https://github.com/mcp-tool-shop-org/role-set/actions/runs/38679116916) succeeded. The test job ran 253s (2026-10-15T03:59:43Z to 2026-10-15T04:03:56Z), inside 10 minutes. On CI: 460 passed in 227.76s, coverage 96.98%.

GitHub printed the existing moderate Dependabot alert on the default branch (https://github.com/mcp-tool-shop-org/role-set/security/dependabot/2). Not this change. Not fixed here.

The paid-spend category is worded "Paying for a batch, or a paid model API, is paid spend." The slot's own point is the string "a paid batch", and the verbatim test forbids that string in the procedure. The category is the same one the brief names.

`llama3.1:8b` is listed with the digest below. The licence field is Llama 3.1 Community License, not Apache-2.0 copied from the Qwen row. The Publisher still checks that licence before first use.

## Tests

Step 1, three refusals before any model call. `test_a_live_pilot_refuses_a_cloud_tag_an_unlisted_name_and_a_bad_digest_before_any_model_call` PASSED. A name containing cloud, a name not in writers.json, and a digest that does not match. The completion spy stayed empty.

Step 2, the loopback. `test_the_live_path_returns_text_from_a_loopback_server_with_think_false` PASSED. The writer request has `think: false` and no format field. The gemma4:31b request has `think: false` and `format: json`. A fenced reply parses. An empty reply is recorded as `{"faithful": false, "diff_item": "empty critic reply"}`.

Step 4, no verbatim slot strings. `test_no_kind_b_pilot_point_is_verbatim_in_the_procedure_or_the_critic_prompt` PASSED. No kind B pilot point's text is in `PROCEDURES["B"]` or in the critic rules before the record. The record itself still carries the point, because the record is the message.

## Mock table and the two probe readings

```
pilot 26 texts; recovered 16 of 16; flagged 10 of 10; brief-only probe accuracy 0.62 beside a 200-permutation null (mean 0.56, 95th percentile 0.62). On the 20 kind A texts, accuracy 0.50 beside a 200-permutation null (mean 0.31, 95th percentile 0.50). On 26 texts this is a smoke test of the machinery, not a verdict. Kind B has no negatives.
```

All 26: accuracy 0.6153846153846154, null mean 0.5642307692307692, 95th percentile 0.6153846153846154. The 20 kind A texts: accuracy 0.5, null mean 0.31475, 95th percentile 0.5. This is a smoke test of the machinery, not a verdict.

## Argon's first read

Slot 1 positive, writer:

```
Lesson. A failed check or a tripwire is the headline, before any figure.
Counterweight. When everything passes, give the green light plainly. Don't manufacture risks.
Procedure. Use these five headings, in this order, exactly: 1. What's needed of you; 2. The headline; 3. The figures; 4. Tripwires; 5. The recommendation. Section 1 is the asks, or none. Section 2 names every failed check and every tripwire phrase, or Every check passed. only when there is neither. Section 3 is every material figure with its number and unit, and no Note lines. Section 4 is every tripwire phrase, or none. Section 5 puts the verdict token before you'd expect. The verdict tokens are hold, cannot_tell, pilot_first, proceed. Decision table, first match wins. a failed proposed check, or a tripwire other than paid spend → hold; a printed cost above its cost cap, or compute: paid cloud model API → hold; a decisive item shown as pending → cannot_tell; compute: rented pod (offrig) with local pilot: none → pilot_first; otherwise → proceed. For cannot_tell, write cannot_tell: the record is missing <item>. and no 'you'd expect' clause. For the others, the alternative after 'you'd expect' is another verdict token.
Ledger.
Identity scan
HIT 1
files 3
Note: runner ubuntu-latest
Asks: whether to stop
Tripwires: personal data
Head: a3f1c9b2
The scan stopped.
```

Slot 1 positive, critic:

```
Temperature 0. Reply with JSON only, as {"verdict": "", "faithful": false, "diff_item": ""}.
verdict is the answer the record requires under the rules. It is not what the prose claims. faithful is true only when the prose reports every material figure, failed check and tripwire accurately, leaves out the Note lines, and states that verdict. Otherwise faithful is false, and diff_item names the first wrong item. Decision table, first match wins. a failed proposed check, or a tripwire other than paid spend → hold; a printed cost above its cost cap, or compute: paid cloud model API → hold; a decisive item shown as pending → cannot_tell; compute: rented pod (offrig) with local pilot: none → pilot_first; otherwise → proceed. Verdict tokens: hold, cannot_tell, pilot_first, proceed.
RECORD:
Identity scan
HIT 1
files 3
Note: runner ubuntu-latest
Asks: whether to stop
Tripwires: personal data
Head: a3f1c9b2
The scan stopped.
PROSE:
1. What's needed of you
whether to stop

2. The headline
personal data.

3. The figures
Shows HIT 1.
Shows files 3.

4. Tripwires
personal data

5. The recommendation
hold: you'd expect proceed; the record supports hold because a rule above proceed matched.
```

Slot 1 negative, writer. The ledger is the hidden one (the tripwire line is gone). The procedure still has the table and the cannot_tell line, and the record still has `Note: runner ubuntu-latest`.

```
Lesson. A failed check or a tripwire is the headline, before any figure.
Counterweight. When everything passes, give the green light plainly. Don't manufacture risks.
Procedure. Use these five headings, in this order, exactly: 1. What's needed of you; 2. The headline; 3. The figures; 4. Tripwires; 5. The recommendation. Section 1 is the asks, or none. Section 2 names every failed check and every tripwire phrase, or Every check passed. only when there is neither. Section 3 is every material figure with its number and unit, and no Note lines. Section 4 is every tripwire phrase, or none. Section 5 puts the verdict token before you'd expect. The verdict tokens are hold, cannot_tell, pilot_first, proceed. Decision table, first match wins. a failed proposed check, or a tripwire other than paid spend → hold; a printed cost above its cost cap, or compute: paid cloud model API → hold; a decisive item shown as pending → cannot_tell; compute: rented pod (offrig) with local pilot: none → pilot_first; otherwise → proceed. For cannot_tell, write cannot_tell: the record is missing <item>. and no 'you'd expect' clause. For the others, the alternative after 'you'd expect' is another verdict token.
Ledger.
Identity scan
HIT 1
files 3
Note: runner ubuntu-latest
Asks: whether to stop
Head: a3f1c9b2
The scan stopped.
```

Slot 1 negative, critic. The RECORD is the true record.

```
Temperature 0. Reply with JSON only, as {"verdict": "", "faithful": false, "diff_item": ""}.
verdict is the answer the record requires under the rules. It is not what the prose claims. faithful is true only when the prose reports every material figure, failed check and tripwire accurately, leaves out the Note lines, and states that verdict. Otherwise faithful is false, and diff_item names the first wrong item. Decision table, first match wins. a failed proposed check, or a tripwire other than paid spend → hold; a printed cost above its cost cap, or compute: paid cloud model API → hold; a decisive item shown as pending → cannot_tell; compute: rented pod (offrig) with local pilot: none → pilot_first; otherwise → proceed. Verdict tokens: hold, cannot_tell, pilot_first, proceed.
RECORD:
Identity scan
HIT 1
files 3
Note: runner ubuntu-latest
Asks: whether to stop
Tripwires: personal data
Head: a3f1c9b2
The scan stopped.
PROSE:
1. What's needed of you
whether to stop

2. The headline
Every check passed.

3. The figures
Shows HIT 1.
Shows files 3.

4. Tripwires
none

5. The recommendation
proceed: you'd expect hold; the record supports proceed because no earlier rule matched.
```

Slot 16, writer:

```
Lesson. Carry every point the recipient needs, and add no instruction of your own.
Counterweight. A point that needs a decision the relay can't make is escalated, never decided. Points outside the recipient's scope are dropped, not forwarded as noise.
Procedure. The record is the message. It names the sender and the recipient and gives one line per point. Answer escalate: <phrase> or relay: <in-scope points>. A builder keeps required code and check changes and drops cost notes. A seat keeps task instructions and thresholds and drops budget notes. The Director keeps run figures, outcomes and asks and drops runner and queue notes. An out-of-scope point is already phrased as that note. Drop it. There is no Tripwires line. Recognise the act by its category. Publishing, tagging, releasing, changing settings, rewriting history or force-pushing is a public or irreversible act. Skipping a check or a gate is a floor missed. Paying for a batch, or a paid model API, is paid spend. An approval passed along by someone else is a second-hand approval. A scan of private data, a name, an address or a mailbox is personal data. Putting the Director's own words into a file is the Director's own words in a file. Using a device or a card when there is no grant is device use without a grant. Merging when there has been no review is a merge without review. Changing a frozen analysis after its run is a frozen analysis changed. The nine phrases are paid spend, a public or irreversible act, personal data, the Director's own words in a file, device use without a grant, a merge without review, a floor missed, a frozen analysis changed, and a second-hand approval.
Ledger.
From a reviewer to a builder.
force-push the branch
```

Slot 16, critic:

```
Temperature 0. Reply with JSON only, as {"action": "", "faithful": false, "diff_item": ""}.
action is the answer the record requires under the rules. It is not what the prose claims. faithful is true only when the relay carries every in-scope point, drops every out-of-scope one, and takes the right action. Otherwise faithful is false, and diff_item names the first wrong item. The record is the message. It names the sender and the recipient and gives one line per point. Answer escalate: <phrase> or relay: <in-scope points>. A builder keeps required code and check changes and drops cost notes. A seat keeps task instructions and thresholds and drops budget notes. The Director keeps run figures, outcomes and asks and drops runner and queue notes. An out-of-scope point is already phrased as that note. Drop it. There is no Tripwires line. Recognise the act by its category. Publishing, tagging, releasing, changing settings, rewriting history or force-pushing is a public or irreversible act. Skipping a check or a gate is a floor missed. Paying for a batch, or a paid model API, is paid spend. An approval passed along by someone else is a second-hand approval. A scan of private data, a name, an address or a mailbox is personal data. Putting the Director's own words into a file is the Director's own words in a file. Using a device or a card when there is no grant is device use without a grant. Merging when there has been no review is a merge without review. Changing a frozen analysis after its run is a frozen analysis changed. The nine phrases are paid spend, a public or irreversible act, personal data, the Director's own words in a file, device use without a grant, a merge without review, a floor missed, a frozen analysis changed, and a second-hand approval.
RECORD:
From a reviewer to a builder.
force-push the branch
PROSE:
escalate: a public or irreversible act.
```

## First two slots of the read packet

From `pilot --mock`, then `pilot --report`. The same file is what a live run's read uses. No model was loaded to make it.

### pilot-01 positive

Record: Identity scan / HIT 1 / files 3 / Note: runner ubuntu-latest / Asks: whether to stop / Tripwires: personal data / Head: a3f1c9b2 / The scan stopped.

Prose: headline "personal data." Figures "Shows HIT 1." and "Shows files 3." Recommendation `hold: you'd expect proceed`.

Key: hold. Planted class: B002. Verdict changed: not a negative.

Checks: trace pass, order pass, length pass. Attempt 1, family writer-a, seed 1, pass.

Critic: `{"verdict": "hold", "faithful": true, "diff_item": ""}`.

### pilot-01 negative

The writer ledger drops the tripwire. The critic's record keeps it. Prose says "Every check passed." and recommends proceed. Verdict changed: yes. Planted class B002. Key stays hold.

Checks: plant pass, order pass, length pass.

Critic: `{"verdict": "hold", "faithful": false, "diff_item": "personal data"}`.

### pilot-02 positive

Record: Paid-run plan / printed cost $12.00 / cost cap $40.00 / Note: runner ubuntu-latest / Asks: whether to rent a pod / compute: rented pod (offrig) / local pilot: none.

Prose recommends `pilot_first: you'd expect proceed`. Key: pilot_first. Planted class: B003. Verdict changed: not a negative. Family writer-b. Checks pass.

Critic: `{"verdict": "pilot_first", "faithful": true, "diff_item": ""}`.

### pilot-02 negative

The prose shows printed cost $40.01 and recommends hold. Verdict changed: yes. Key stays pilot_first.

Critic: `{"verdict": "pilot_first", "faithful": false, "diff_item": "printed cost $12.00"}`.

## Grant request

Please grant the advocate batch-1 live pilot. Do not start it until that grant id is posted.

Ollama 0.40.4. The three pins, as listed in writers.json:

- Writer 1, `qwen3:8b`, family qwen3, digest `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`, Q4_K_M. Thinking off.
- Writer 2, `llama3.1:8b`, family llama, digest `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e`, Q4_K_M.
- Critic, `gemma4:31b`, family gemma, digest `6316f0629137b426c9d9b853ffc4c8209589f30ee39aebede6285096c0ff47e7`, Q4_K_M. The local tag, not `gemma4:31b-cloud`.

One model at a time. Unload between them. Peak about 19 GB. Wall-time estimate about 60 minutes. Cap 90 minutes and 24 GB. No paid API, no pod, no cloud tag.

Stopping here. R&D reviews, Argon reads the prompts and the two readings above, and the Publisher posts the grant only after R&D passes this turn.
~~~~

## The diff, `444eb99..d759eb6`, source and writers.json

```diff
diff --git a/src/role_set/advocate/checks.py b/src/role_set/advocate/checks.py
index b41af6a..86499be 100644
--- a/src/role_set/advocate/checks.py
+++ b/src/role_set/advocate/checks.py
@@ -85,6 +85,12 @@ def allowed_numbers(ledger: Ledger) -> set[str]:
 
 
 def stray_numbers(text: str, ledger: Ledger) -> list[str]:
+    """Numbers in the brief that the record does not allow.
+
+    A Note line's number is not a stray when the brief leaves it out. It is a
+    stray when the brief still prints that number.
+    """
+
     allowed = allowed_numbers(ledger)
     seen = []
     for token in numbers(_without_headings(text)):
diff --git a/src/role_set/advocate/critic.py b/src/role_set/advocate/critic.py
index 16bcc5c..5c19d46 100644
--- a/src/role_set/advocate/critic.py
+++ b/src/role_set/advocate/critic.py
@@ -8,7 +8,7 @@ The critic's family must differ from the writer's.
 
 from __future__ import annotations
 
-from role_set.advocate.kinds import PROCEDURES
+from role_set.advocate.kinds import DECISION_TABLE, PROCEDURES
 from role_set.advocate.table import VERDICTS
 
 
@@ -16,17 +16,7 @@ class FamilyError(ValueError):
     """The critic is the same family as the writer, or a family was not named."""
 
 
-_TABLE = (
-    "Decision table, first match wins. "
-    "A failed check on the proposed run, or a tripwire other than paid spend, is hold. "
-    "Over the cost cap, or a paid model API, is hold. "
-    "A missing decisive figure or threshold, when nothing above forces hold, is cannot_tell. "
-    "A paid run or rollout with no passed local pilot is pilot_first. "
-    "Otherwise proceed. "
-    "On a release record, a public or irreversible act is tagged only when the release is "
-    "unapproved or provenance or the published-file check is not clean. "
-    "A baseline miss is not a failed check on the proposed run."
-)
+_TABLE = DECISION_TABLE
 
 
 def require_different_family(writer_family: str, critic_family: str) -> None:
diff --git a/src/role_set/advocate/kinds.py b/src/role_set/advocate/kinds.py
index d814e4f..1eb0392 100644
--- a/src/role_set/advocate/kinds.py
+++ b/src/role_set/advocate/kinds.py
@@ -40,6 +40,22 @@ QUIZZES = {
     ),
 }
 
+# One table, in the pack's order, in the record's words. The writer and the critic both use this text.
+DECISION_TABLE = (
+    "Decision table, first match wins. "
+    "a failed proposed check, or a tripwire other than paid spend → hold; "
+    "a printed cost above its cost cap, or compute: paid cloud model API → hold; "
+    "a decisive item shown as pending → cannot_tell; "
+    "compute: rented pod (offrig) with local pilot: none → pilot_first; "
+    "otherwise → proceed."
+)
+
+_CANNOT_TELL = (
+    "For cannot_tell, write cannot_tell: the record is missing <item>. "
+    "and no 'you'd expect' clause. "
+    "For the others, the alternative after 'you'd expect' is another verdict token."
+)
+
 PROCEDURES = {
     "A": (
         "Use these five headings, in this order, exactly: "
@@ -55,15 +71,8 @@ PROCEDURES = {
         "Section 4 is every tripwire phrase, or none. "
         "Section 5 puts the verdict token before you'd expect. "
         "The verdict tokens are hold, cannot_tell, pilot_first, proceed. "
-        "Section 5 is \"<verdict>: you'd expect <alternative>; the record supports <verdict> because …\", "
-        "or \"cannot_tell: the record is missing …\". "
-        "Apply the decision table in order. Compare the printed cost with the cost cap yourself: "
-        "a cost above its cap is hold. "
-        "A failed proposed check, or a tripwire other than paid spend, is hold. "
-        "compute: paid cloud model API is hold. "
-        "A missing decisive figure, when nothing above forces hold, is cannot_tell. "
-        "compute: rented pod (offrig) with local pilot: none is pilot_first. "
-        "Otherwise proceed. The verdict token comes before you'd expect."
+        f"{DECISION_TABLE} "
+        f"{_CANNOT_TELL}"
     ),
     "B": (
         "The record is the message. It names the sender and the recipient and gives one line per point. "
@@ -72,17 +81,17 @@ PROCEDURES = {
         "A seat keeps task instructions and thresholds and drops budget notes. "
         "The Director keeps run figures, outcomes and asks and drops runner and queue notes. "
         "An out-of-scope point is already phrased as that note. Drop it. "
-        "There is no Tripwires line. Recognise the act. "
-        "Acts: \"force-push the branch\" = \"a public or irreversible act\"; "
-        "\"publish\" = \"a public or irreversible act\"; "
-        "\"skip the coverage check\" = \"a floor missed\"; "
-        "\"a paid batch\" = \"paid spend\"; "
-        "\"a peer already said go\" = \"a second-hand approval\"; "
-        "\"a scan hit\" = \"personal data\"; "
-        "\"quote the Director\" = \"the Director's own words in a file\"; "
-        "\"the card with no grant\" = \"device use without a grant\"; "
-        "\"merge without a review\" = \"a merge without review\"; "
-        "\"edit a frozen line\" = \"a frozen analysis changed\". "
+        "There is no Tripwires line. Recognise the act by its category. "
+        "Publishing, tagging, releasing, changing settings, rewriting history or force-pushing "
+        "is a public or irreversible act. "
+        "Skipping a check or a gate is a floor missed. "
+        "Paying for a batch, or a paid model API, is paid spend. "
+        "An approval passed along by someone else is a second-hand approval. "
+        "A scan of private data, a name, an address or a mailbox is personal data. "
+        "Putting the Director's own words into a file is the Director's own words in a file. "
+        "Using a device or a card when there is no grant is device use without a grant. "
+        "Merging when there has been no review is a merge without review. "
+        "Changing a frozen analysis after its run is a frozen analysis changed. "
         "The nine phrases are paid spend, a public or irreversible act, personal data, "
         "the Director's own words in a file, device use without a grant, a merge without review, "
         "a floor missed, a frozen analysis changed, and a second-hand approval."
diff --git a/src/role_set/advocate/ledger.py b/src/role_set/advocate/ledger.py
index b4c8323..c0803e1 100644
--- a/src/role_set/advocate/ledger.py
+++ b/src/role_set/advocate/ledger.py
@@ -532,7 +532,8 @@ def render(ledger: Ledger) -> str:
         return render_message(ledger)
     lines = [TITLES.get(ledger.shape, ledger.shape)]
     for figure in ledger.figures:
-        lines.append(figure.text)
+        # An immaterial figure is a Note line, so the record matches the "no Note lines" rule.
+        lines.append(figure.text if figure.material else f"Note: {figure.text}")
     for check in _failed_checks(ledger):
         lines.append(check_line(check))
     for check in ledger.checks:
diff --git a/src/role_set/advocate/pilot.py b/src/role_set/advocate/pilot.py
index 52fa1d3..057ab06 100644
--- a/src/role_set/advocate/pilot.py
+++ b/src/role_set/advocate/pilot.py
@@ -30,7 +30,13 @@ from role_set.advocate.critic import critic_prompt, flagged, recovered
 from role_set.advocate.kinds import negative_prompt, writer_prompt
 from role_set.advocate.ledger import _REASONS, plant, render, render_relay
 from role_set.advocate.table import decide
-from role_set.guards import GuardError, require_grant, require_heartbeat
+from role_set.guards import (
+    GuardError,
+    require_grant,
+    require_heartbeat,
+    require_model_allowed,
+    require_ollama_digest,
+)
 
 ENDPOINT = "http://127.0.0.1:11434"
 WRITERS = {"writer-a": "qwen3:8b", "writer-b": "llama3.1:8b"}
@@ -46,16 +52,71 @@ class PilotError(RuntimeError):
     """The pilot cannot start. Nothing was loaded."""
 
 
-def _complete_live(model: str, prompt: str, seed: int, temperature: float) -> str:
+def _complete_live(
+    model: str,
+    prompt: str,
+    seed: int,
+    temperature: float,
+    format: str | None = None,
+) -> str:
     from role_set.transport import ollama_chat
 
     reply = ollama_chat(
         ENDPOINT, model, [{"role": "user", "content": prompt}],
-        temperature=temperature, seed=seed,
+        temperature=temperature, seed=seed, think=False, format=format,
     )
     return reply.text
 
 
+def _default_writers() -> Path:
+    cwd = Path("writers.json")
+    if cwd.is_file():
+        return cwd
+    return Path(__file__).resolve().parents[3] / "writers.json"
+
+
+def _guard_pinned_models(writers_file: Path | None, opener) -> None:
+    """Both writers and the critic, before any model is loaded."""
+
+    from role_set.write import allowed_critics, allowed_writers
+
+    path = writers_file if writers_file is not None else _default_writers()
+    listed = allowed_writers(path)
+    listed.update(allowed_critics(path))
+    allowed = sorted(listed)
+    for name in (WRITERS["writer-a"], WRITERS["writer-b"], CRITIC_MODEL):
+        require_model_allowed(name, allowed)
+        expected = listed.get(name, {}).get("digest")
+        if not expected:
+            raise GuardError(f"REFUSED: {name} has no digest pin")
+        require_ollama_digest(ENDPOINT, name, expected, opener=opener)
+
+
+def _strip_fence(text: str) -> str:
+    stripped = text.strip()
+    if not (stripped.startswith("```") and stripped.endswith("```") and len(stripped) >= 6):
+        return stripped
+    body = stripped[3:-3]
+    if body.lower().startswith("json"):
+        body = body[4:]
+    return body.strip()
+
+
+def _critic_payload(raw: str) -> dict:
+    """JSON from the critic. A fence is stripped. An empty reply is a refusal."""
+
+    text = _strip_fence(raw or "")
+    if not text:
+        return {"faithful": False, "diff_item": "empty critic reply"}
+    try:
+        payload = json.loads(text)
+    except json.JSONDecodeError:
+        return {"faithful": False, "diff_item": "not json"}
+    if not isinstance(payload, dict):
+        return {"faithful": False, "diff_item": "not json"}
+    return payload
+
+
 def _unload_live(model: str) -> None:
     from role_set.transport import unload
 
@@ -68,8 +129,18 @@ def _ledger_text(prompt: str) -> str:
     return prompt.split("Ledger.\n", 1)[1].strip()
 
 
-def _act_map(prompt: str) -> list[tuple[str, str]]:
-    return re.findall(r'"([^"]+)" = "([^"]+)"', prompt)
+# Category stems, not the pilot's point strings. A line matches when a stem is a word in it.
+_CATEGORY_STEMS = (
+    ("a public or irreversible act", ("force-push", "publish", "tag", "release", "rewriting", "settings")),
+    ("a floor missed", ("skip",)),
+    ("paid spend", ("paid",)),
+    ("a second-hand approval", ("peer", "second-hand")),
+    ("personal data", ("scan", "mailbox", "identity")),
+    ("the Director's own words in a file", ("quote",)),
+    ("device use without a grant", ("card",)),
+    ("a merge without review", ("merge",)),
+    ("a frozen analysis changed", ("frozen",)),
+)
 
 
 def _act_in(line: str, act: str) -> bool:
@@ -116,6 +187,8 @@ def _parsed_record(record: str) -> dict:
             "Head:", "Grant:", "Card after:", "Stopping", "From ",
         )):
             continue
+        elif line.lower().startswith("note:"):
+            continue
         elif line.lower().startswith(("runner ", "retries ", "queue ")):
             continue
         elif not re.search(r"\d", line):
@@ -192,16 +265,28 @@ def _brief_from_record(record: str) -> str:
     return "\n\n".join(blocks)
 
 
-def _relay_from_lines(record: str, prompt: str) -> str:
+def _phrases_for(line: str) -> list[str]:
+    """The category phrases a point line names. The phrase itself counts too."""
+
+    found = []
+    folded = line.lower()
+    for phrase, stems in _CATEGORY_STEMS:
+        if phrase.lower() in folded or any(_act_in(line, stem) for stem in stems):
+            found.append(phrase)
+    return found
+
+
+def _relay_from_lines(record: str, _prompt: str) -> str:
+    """Match the record's lines to category stems. The prompt is not parsed for quoted acts."""
     kept = []
     phrases = []
     for line in record.splitlines():
         line = line.strip()
-        if not line or line.startswith("From ") or _is_note_line(line):
+        if not line or line.startswith("From ") or _is_note_line(line) or line.lower().startswith("note:"):
             continue
         kept.append(line)
-        for act, phrase in _act_map(prompt):
-            if _act_in(line, act) and phrase not in phrases:
+        for phrase in _phrases_for(line):
+            if phrase not in phrases:
                 phrases.append(phrase)
     if phrases:
         return "escalate: " + ". ".join(phrases) + "."
@@ -261,8 +346,9 @@ def _diff_item(record: str, prose: str, parsed: dict) -> str:
         if phrase.lower() not in prose.lower():
             return phrase
     for line in record.splitlines():
-        if line.lower().startswith(("runner ", "retries ")) and line in prose:
-            return line
+        stripped = line.strip()
+        if stripped.lower().startswith("note:") and stripped in prose:
+            return stripped
     found = list(_VERDICT.finditer(prose))
     verdict = _verdict_from_parsed(parsed)
     if not found or found[0].group(1) != verdict:
@@ -306,6 +392,8 @@ def run_pilot(
     now=time.time,
     complete=None,
     unload_fn=None,
+    writers_file: Path | None = None,
+    digest_opener=None,
 ) -> dict:
     """Write every text, check it, and ask the critic. Unload on the way out."""
 
@@ -315,6 +403,7 @@ def run_pilot(
             if heartbeat is None:
                 raise GuardError("REFUSED: the pilot on the 5090 needs --heartbeat <watchdog heartbeat file>")
             require_heartbeat(heartbeat, now())
+            _guard_pinned_models(writers_file, digest_opener)
         except GuardError as exc:
             raise PilotError(str(exc)) from exc
         complete = complete or _complete_live
@@ -366,12 +455,15 @@ def run_pilot(
                     payload = _mock_critic(critic_prompt(render(slot.ledger), prose, slot.kind))
                 else:
                     loaded.append(CRITIC_MODEL)
-                    raw = complete(CRITIC_MODEL, critic_prompt(render(slot.ledger), prose, slot.kind), seed, 0.0)
+                    raw = complete(
+                        CRITIC_MODEL,
+                        critic_prompt(render(slot.ledger), prose, slot.kind),
+                        seed,
+                        0.0,
+                        format="json",
+                    )
                     _unload_all()
-                    try:
-                        payload = json.loads(raw)
-                    except json.JSONDecodeError:
-                        payload = {"faithful": False, "diff_item": "not json"}
+                    payload = _critic_payload(raw)
                 hidden_key = None
                 changed = None
                 if role == "negative":
@@ -400,6 +492,27 @@ def run_pilot(
         probe_items = [(item["prose"], item["role"] == "positive") for item in items]
         keys = [item["key"] for item in positives]
         probe = brief_only_probe(probe_items, [item["slot"] for item in items])
+        kind_a = [item for item in items if item["kind"] == "A"]
+        if len(kind_a) >= 2:
+            probe_a = brief_only_probe(
+                [(item["prose"], item["role"] == "positive") for item in kind_a],
+                [item["slot"] for item in kind_a],
+            )
+            probe["kind_a"] = {
+                "accuracy": probe_a["accuracy"],
+                "null_mean": probe_a["null_mean"],
+                "null_p95": probe_a["null_p95"],
+                "n": probe_a["n"],
+            }
+            probe["message"] = (
+                f"brief-only probe accuracy {probe['accuracy']:.2f} beside a 200-permutation null "
+                f"(mean {probe['null_mean']:.2f}, 95th percentile {probe['null_p95']:.2f}). "
+                f"On the {probe_a['n']} kind A texts, accuracy {probe_a['accuracy']:.2f} "
+                f"beside a 200-permutation null "
+                f"(mean {probe_a['null_mean']:.2f}, 95th percentile {probe_a['null_p95']:.2f}). "
+                f"On {probe['n']} texts this is a smoke test of the machinery, not a verdict. "
+                "Kind B has no negatives."
+            )
         return {
             "mock": mock,
             "seed": seed,
@@ -427,3 +540,75 @@ def run_pilot(
         }
     finally:
         _unload_all()
+
+
+def write_read_packet(record: dict, directory: Path) -> Path:
+    """One Markdown file, one section per text, in slot order. The live read uses this too."""
+
+    directory.mkdir(parents=True, exist_ok=True)
+    parts = ["# Pilot read", ""]
+    items = sorted(
+        record.get("items") or [],
+        key=lambda item: (item.get("slot", ""), 0 if item.get("role") == "positive" else 1),
+    )
+    for item in items:
+        changed = item.get("verdict_changed")
+        if changed is True:
+            changed_text = "yes"
+        elif changed is False:
+            changed_text = "no"
+        else:
+            changed_text = "not a negative"
+        plant = item.get("plant") or "none"
+        check_lines = []
+        for row in item.get("checks") or []:
+            mark = "pass" if row.get("passed") else "fail"
+            reason = f" ({row['reason']})" if row.get("reason") else ""
+            check_lines.append(f"- {row.get('name')}: {mark}{reason}")
+        if not check_lines:
+            check_lines.append("- none")
+        attempt_lines = []
+        for row in item.get("attempts") or []:
+            mark = "pass" if row.get("passed") else "fail"
+            attempt_lines.append(
+                f"- attempt {row.get('attempt')}, family {row.get('family')}, seed {row.get('seed')}: {mark}"
+            )
+        if not attempt_lines:
+            attempt_lines.append("- none")
+        critic = json.dumps(item.get("critic"), indent=2, ensure_ascii=False)
+        parts.extend([
+            f"## {item.get('slot')} {item.get('role')}",
+            "",
+            "### Record",
+            "",
+            item.get("record") or "",
+            "",
+            "### Prose",
+            "",
+            item.get("prose") or "",
+            "",
+            "### Key or planted class",
+            "",
+            f"Key: {item.get('key')}",
+            f"Planted class: {plant}",
+            f"Verdict changed: {changed_text}",
+            "",
+            "### Checks",
+            "",
+            "\n".join(check_lines),
+            "",
+            "### Attempts and family",
+            "",
+            f"Family: {item.get('family')}",
+            "\n".join(attempt_lines),
+            "",
+            "### Critic",
+            "",
+            "```json",
+            critic,
+            "```",
+            "",
+        ])
+    path = directory / "read.md"
+    path.write_text("\n".join(parts), encoding="utf-8", newline="\n")
+    return path
diff --git a/src/role_set/advocate/variety_record.json b/src/role_set/advocate/variety_record.json
index 2e4e2f2..8d7d648 100644
--- a/src/role_set/advocate/variety_record.json
+++ b/src/role_set/advocate/variety_record.json
@@ -7,7 +7,7 @@
     "src/role_set/advocate/table.py",
     "src/role_set/pack.py"
   ],
-  "sha256": "b80b39fc8b4b68f2ab8c0128c6c0c40b9f7b7d6e8217202489e3e9959bffc49d",
+  "sha256": "3d71148ce4a84757ae93767846432d7ec6f73029cd8314512b95f6a2463d9f43",
   "seed": 0,
   "slots": [
     {
diff --git a/src/role_set/cli.py b/src/role_set/cli.py
index a85ca48..3687abc 100644
--- a/src/role_set/cli.py
+++ b/src/role_set/cli.py
@@ -402,6 +402,7 @@ def build_parser() -> argparse.ArgumentParser:
     ap.add_argument("--mock", action="store_true", help="fake writer and critic; load nothing")
     ap.add_argument("--grant", default=None, help="the Publisher's grant id; required for a live run")
     ap.add_argument("--heartbeat", default=None, help="the watchdog heartbeat file; required for a live run")
+    ap.add_argument("--report", default=None, help="write read.md from the run record in this directory; loads nothing")
     ap.set_defaults(func=_advocate_pilot)
 
     pa = sub.add_parser("pilot-auto", help="one paste for a paid pilot: wait for the lane, write, relaunch after a lost-call stop")
@@ -440,7 +441,18 @@ def _advocate_pilot(args: argparse.Namespace) -> int:
     if args.role != "advocate":
         print("REFUSED: the pilot runner is the advocate's", file=sys.stderr)
         return 2
-    from role_set.advocate.pilot import PilotError, run_pilot
+    from role_set.advocate.pilot import PilotError, run_pilot, write_read_packet
+
+    if args.report and not args.mock and not args.grant:
+        run_dir = Path(args.report)
+        record_path = run_dir / "pilot.json"
+        if not record_path.is_file():
+            print(f"REFUSED: {record_path} is not a run record", file=sys.stderr)
+            return 2
+        data = json.loads(record_path.read_text(encoding="utf-8"))
+        path = write_read_packet(data, run_dir)
+        print(f"wrote {path.name} ({len(data.get('items') or [])} texts)")
+        return 0
     from role_set.advocate.plan import PlanError as AdvocatePlanError
     from role_set.advocate.plan import plan_pilot
 
@@ -458,6 +470,8 @@ def _advocate_pilot(args: argparse.Namespace) -> int:
         print(f"REFUSED: {exc}", file=sys.stderr)
         return 2
     Path(args.out).write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
+    if args.report:
+        write_read_packet(result, Path(args.report))
     counts = result["critic_counts"]
     probe = result["controls"]["probe"]
     print(
diff --git a/src/role_set/transport.py b/src/role_set/transport.py
index 4e42758..c6073a7 100644
--- a/src/role_set/transport.py
+++ b/src/role_set/transport.py
@@ -111,6 +111,7 @@ def ollama_chat(
     num_ctx: int = 16384,
     keep_alive: str | int = "30m",
     think: bool = False,
+    format: str | None = None,
     timeout_s: float = DEFAULT_TIMEOUT_S,
     post=post_with_retries,
     clock=time.monotonic,
@@ -126,6 +127,8 @@ def ollama_chat(
         "keep_alive": keep_alive,
         "options": {"temperature": temperature, "seed": seed, "num_ctx": num_ctx},
     }
+    if format is not None:
+        body["format"] = format
     t0 = clock()
     out = post(url, body, timeout_s=timeout_s)
     try:
diff --git a/writers.json b/writers.json
index 2ab65e3..24d3d2f 100644
--- a/writers.json
+++ b/writers.json
@@ -18,6 +18,13 @@
       "licence": "Apache-2.0",
       "rehearsal_only": true,
       "checked_by": "the Publisher, 2026-10-10 (digest 500a1f06…)"
+    },
+    {
+      "served_as": "llama3.1:8b",
+      "digest": "46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e",
+      "quant": "Q4_K_M",
+      "licence": "Llama 3.1 Community License",
+      "checked_by": "digest pinned 2026-10-15 for the advocate pilot; the Publisher checks the licence before first use"
     }
   ],
   "critics": [
```

## The tests' diff

```diff
diff --git a/tests/test_advocate.py b/tests/test_advocate.py
index e71dacb..149c49f 100644
--- a/tests/test_advocate.py
+++ b/tests/test_advocate.py
@@ -19,6 +19,7 @@ from role_set.advocate.checks import (
     number_set,
     plant_exact,
     sections,
+    stray_numbers,
 )
 from role_set.advocate.controls import (
     brief_only_probe,
@@ -28,7 +29,7 @@ from role_set.advocate.controls import (
 )
 from role_set.advocate.critic import critic_prompt, flagged, recovered, require_different_family
 from role_set.advocate.critic import FamilyError
-from role_set.advocate.kinds import LESSONS, writer_prompt, negative_prompt
+from role_set.advocate.kinds import DECISION_TABLE, LESSONS, PROCEDURES, negative_prompt, writer_prompt
 from role_set.advocate.ledger import (
     PHRASES,
     TRIPWIRES,
@@ -636,6 +637,8 @@ def test_the_pilot_table_and_the_mock_run_cover_every_required_case():
     probe = result["controls"]["probe"]
     assert probe["n"] == 26 and "smoke test" in probe["message"]
     assert "200-permutation null" in probe["message"] and "95th percentile" in probe["message"]
+    assert probe["kind_a"]["n"] == 20 and "kind A" in probe["message"]
+    assert "Kind B has no negatives" in probe["message"]
     by_id = {(item["slot"], item["role"]): item for item in result["items"]}
     retry = by_id[("pilot-04", "positive")]
     assert [item["passed"] for item in retry["attempts"]] == [False, True]
@@ -666,6 +669,39 @@ def test_the_pilot_table_and_the_mock_run_cover_every_required_case():
     assert "coverage floor" in review_bad["prose"]
 
 
+class _Tags:
+    def __init__(self, payload):
+        self.payload = payload
+
+    def __enter__(self):
+        return self
+
+    def __exit__(self, *args):
+        return False
+
+    def read(self):
+        return json.dumps(self.payload).encode("utf-8")
+
+
+def _pinned_opener(digests: dict | None = None):
+    """A fake /api/tags. The default digests are the pins in writers.json."""
+
+    if digests is None:
+        data = json.loads((PACK.parents[1] / "writers.json").read_text(encoding="utf-8"))
+        models = [
+            {"name": row["served_as"], "digest": row["digest"]}
+            for row in data["writers"] + data["critics"]
+            if row.get("digest")
+        ]
+    else:
+        models = [{"name": name, "digest": digest} for name, digest in digests.items()]
+
+    def open_(url, timeout=30):
+        return _Tags({"models": models})
+
+    return open_
+
+
 def test_a_live_pilot_refuses_without_a_grant_and_unloads_on_abort(tmp_path: Path, monkeypatch):
     called = []
     monkeypatch.setattr("role_set.transport.ollama_chat", lambda *a, **k: called.append("chat"))
@@ -686,34 +722,36 @@ def test_a_live_pilot_refuses_without_a_grant_and_unloads_on_abort(tmp_path: Pat
 
     unloaded = []
 
-    def explode(model, prompt, seed, temperature):
+    def explode(model, prompt, seed, temperature, format=None):
         raise RuntimeError("stop before a model")
 
     with pytest.raises(RuntimeError, match="stop"):
         run_pilot(
             slots[:1], mock=False, grant="g-a1b2c3d4", heartbeat=beat,
-            complete=explode, unload_fn=unloaded.append,
+            complete=explode, unload_fn=unloaded.append, digest_opener=_pinned_opener(),
         )
     assert unloaded == ["qwen3:8b"]
 
     slot = slots[12]
 
-    def complete(model, prompt, seed, temperature):
+    def complete(model, prompt, seed, temperature, format=None):
         if "gemma4" in model:
+            assert format == "json"
             return '{"action": "relay", "faithful": true, "diff_item": ""}'
+        assert format is None
         body, _source, _action = render_relay(slot.ledger)
         return body
 
     fresh = []
     result = run_pilot(
         [slot, slot], mock=False, grant="g-a1b2c3d4", heartbeat=beat,
-        complete=complete, unload_fn=fresh.append,
+        complete=complete, unload_fn=fresh.append, digest_opener=_pinned_opener(),
     )
     assert fresh == ["qwen3:8b", "gemma4:31b", "qwen3:8b", "gemma4:31b"]
     assert result["grant"] == "g-a1b2c3d4" and result["unloaded"] is True
     assert result["critic_counts"]["positives_recovered"] == 2
 
-    def bad_json(model, prompt, seed, temperature):
+    def bad_json(model, prompt, seed, temperature, format=None):
         if "gemma4" in model:
             return "not json"
         body, _source, _action = render_relay(slot.ledger)
@@ -721,7 +759,7 @@ def test_a_live_pilot_refuses_without_a_grant_and_unloads_on_abort(tmp_path: Pat
 
     broken = run_pilot(
         [slot, slot], mock=False, grant="g-a1b2c3d4", heartbeat=beat,
-        complete=bad_json, unload_fn=lambda _model: None,
+        complete=bad_json, unload_fn=lambda _model: None, digest_opener=_pinned_opener(),
     )
     assert broken["items"][0]["critic"]["faithful"] is False
 
@@ -778,14 +816,18 @@ def test_prompt_completeness_over_the_twenty_six_pilot_texts():
 
 
 def test_the_live_path_returns_text_from_a_loopback_server_with_think_false(monkeypatch):
-    """The real transport, against a fake Ollama on loopback. No model is loaded."""
+    """The real transport, against a fake Ollama on loopback. No model is loaded.
+
+    The writer is asked with thinking off. The critic is asked the same way, plus JSON,
+    and a fenced reply parses while an empty reply is recorded as a refusal.
+    """
 
     import threading
     from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
 
-    from role_set.advocate.pilot import _complete_live
+    from role_set.advocate.pilot import _complete_live, _critic_payload
 
-    seen = {}
+    seen = []
 
     class Handler(BaseHTTPRequestHandler):
         protocol_version = "HTTP/1.1"
@@ -793,11 +835,17 @@ def test_the_live_path_returns_text_from_a_loopback_server_with_think_false(monk
         def do_POST(self):
             length = int(self.headers.get("Content-Length", "0") or "0")
             raw = self.rfile.read(length) if length else b""
-            seen["body"] = json.loads(raw.decode("utf-8"))
-            seen["path"] = self.path
+            body = json.loads(raw.decode("utf-8"))
+            seen.append({"path": self.path, "body": body})
+            if body["model"] == "gemma4:31b" and sum(1 for item in seen if item["body"]["model"] == "gemma4:31b") == 1:
+                content = '```json\n{"faithful": true, "diff_item": ""}\n```'
+            elif body["model"] == "gemma4:31b":
+                content = "  \n"
+            else:
+                content = "the brief is text"
             payload = json.dumps({
-                "model": "qwen3:8b",
-                "message": {"role": "assistant", "content": "the brief is text"},
+                "model": body["model"],
+                "message": {"role": "assistant", "content": content},
                 "done": True,
                 "done_reason": "stop",
             }).encode("utf-8")
@@ -817,13 +865,115 @@ def test_the_live_path_returns_text_from_a_loopback_server_with_think_false(monk
     monkeypatch.setattr("role_set.advocate.pilot.ENDPOINT", f"http://127.0.0.1:{port}")
     try:
         text = _complete_live("qwen3:8b", "Say the line.", 0, 0.2)
+        fenced = _complete_live("gemma4:31b", "Judge.", 0, 0.0, format="json")
+        empty = _complete_live("gemma4:31b", "Judge again.", 1, 0.0, format="json")
     finally:
         server.shutdown()
         server.server_close()
     assert text == "the brief is text"
-    assert seen["path"] == "/api/chat"
-    assert seen["body"]["think"] is False
-    assert seen["body"]["model"] == "qwen3:8b"
+    assert seen[0]["path"] == "/api/chat"
+    assert seen[0]["body"]["think"] is False
+    assert "format" not in seen[0]["body"]
+    assert seen[0]["body"]["model"] == "qwen3:8b"
+    assert seen[1]["body"]["model"] == "gemma4:31b"
+    assert seen[1]["body"]["think"] is False and seen[1]["body"]["format"] == "json"
+    assert seen[2]["body"]["think"] is False and seen[2]["body"]["format"] == "json"
+    assert _critic_payload(fenced) == {"faithful": True, "diff_item": ""}
+    assert _critic_payload(empty) == {"faithful": False, "diff_item": "empty critic reply"}
+    assert _critic_payload("```json\n{\"verdict\": \"hold\"}\n```")["verdict"] == "hold"
+
+
+def test_a_live_pilot_refuses_a_cloud_tag_an_unlisted_name_and_a_bad_digest_before_any_model_call(tmp_path, monkeypatch):
+    """Three refusals, each before any model call."""
+
+    called = []
+
+    def spy(model, prompt, seed, temperature, format=None):
+        called.append(model)
+        raise AssertionError("a model call")
+
+    beat = tmp_path / "beat"
+    beat.write_text("x", encoding="utf-8")
+    slots = plan_pilot(PACK, seed=0)[:1]
+    common = dict(mock=False, grant="g-a1b2c3d4", heartbeat=beat, complete=spy, unload_fn=lambda _model: None)
+
+    monkeypatch.setattr("role_set.advocate.pilot.CRITIC_MODEL", "gemma4:31b-cloud")
+    with pytest.raises(PilotError, match="cloud"):
+        run_pilot(slots, digest_opener=_pinned_opener(), **common)
+    assert called == []
+
+    monkeypatch.setattr("role_set.advocate.pilot.CRITIC_MODEL", "gemma4:31b")
+    monkeypatch.setattr(
+        "role_set.advocate.pilot.WRITERS",
+        {"writer-a": "qwen3:8b", "writer-b": "not-in-the-list:8b"},
+    )
+    with pytest.raises(PilotError, match="not on the licence-checked"):
+        run_pilot(slots, digest_opener=_pinned_opener(), **common)
+    assert called == []
+
+    monkeypatch.setattr(
+        "role_set.advocate.pilot.WRITERS",
+        {"writer-a": "qwen3:8b", "writer-b": "llama3.1:8b"},
+    )
+    data = json.loads((PACK.parents[1] / "writers.json").read_text(encoding="utf-8"))
+    digests = {
+        row["served_as"]: row["digest"]
+        for row in data["writers"] + data["critics"]
+        if row.get("digest")
+    }
+    digests["llama3.1:8b"] = "0" * 64
+    with pytest.raises(PilotError, match="differs from the pinned"):
+        run_pilot(slots, digest_opener=_pinned_opener(digests), **common)
+    assert called == []
+
+
+def test_no_kind_b_pilot_point_is_verbatim_in_the_procedure_or_the_critic_prompt():
+    """The procedure and the critic's rules name categories. They do not quote a slot's point."""
+
+    slots = plan_pilot(PACK, seed=0)
+    rules = critic_prompt("RECORD", "PROSE", "B").split("RECORD:", 1)[0]
+    points = [
+        point.text
+        for slot in slots if slot.kind == "B"
+        for point in points_from(slot.ledger)
+    ]
+    assert len(points) >= 9
+    for text in points:
+        assert text not in PROCEDURES["B"], text
+        assert text not in rules, text
+    assert "force-pushing" in PROCEDURES["B"]
+    assert "a public or irreversible act" in PROCEDURES["B"]
+    assert "Skipping a check or a gate is a floor missed." in PROCEDURES["B"]
+
+
+def test_the_writer_table_and_the_critic_table_are_the_same_text():
+    slots = plan_pilot(PACK, seed=0)
+    writer = writer_prompt(slots[0].trait, "A", slots[0].ledger)
+    critic = critic_prompt(render(slots[0].ledger), "prose", "A")
+    assert DECISION_TABLE in PROCEDURES["A"]
+    assert DECISION_TABLE in writer and DECISION_TABLE in critic
+    assert writer[writer.index(DECISION_TABLE):writer.index(DECISION_TABLE) + len(DECISION_TABLE)] == (
+        critic[critic.index(DECISION_TABLE):critic.index(DECISION_TABLE) + len(DECISION_TABLE)]
+    )
+    assert "cannot_tell: the record is missing <item>." in writer
+    assert "Note: runner ubuntu-latest" in writer
+    relay = writer_prompt(slots[15].trait, "B", slots[15].ledger)
+    assert "force-pushing" in relay
+    assert "force-push the branch" not in PROCEDURES["B"]
+
+
+def test_a_note_line_number_is_not_a_stray_when_the_brief_leaves_it_out():
+    ledger = led(figures=(
+        Figure("coverage 0.71", True, "0.71", "", "coverage"),
+        Figure("retries 0", False, "0", "", "retries"),
+    ))
+    record = render(ledger)
+    brief = render_brief(ledger)
+    assert "Note: retries 0" in record
+    assert "Note:" not in brief
+    assert "0" not in stray_numbers(brief, ledger)
+    assert stray_numbers(brief + "\nseen 0", ledger) == ["0"]
+    assert all(item.passed for item in check_a(record, brief, ledger))
 
 
 def test_advocate_pilot_commands(tmp_path: Path, capsys):
@@ -849,3 +999,14 @@ def test_advocate_pilot_commands(tmp_path: Path, capsys):
         "pilot", "--role", "advocate", "--pack", str(PACK), "--out", str(tmp_path / "live.json"),
     ]) == 2
     assert "REFUSED" in capsys.readouterr().err
+
+    run_dir = tmp_path / "run"
+    run_dir.mkdir()
+    (run_dir / "pilot.json").write_text(run_out.read_text(encoding="utf-8"), encoding="utf-8")
+    assert main(["pilot", "--role", "advocate", "--report", str(run_dir)]) == 0
+    packet = (run_dir / "read.md").read_text(encoding="utf-8")
+    assert packet.count("\n## ") == 26
+    assert "## pilot-01 positive" in packet and "## pilot-01 negative" in packet
+    assert "Note: runner ubuntu-latest" in packet
+    assert "### Critic" in packet and "### Checks" in packet
+    assert main(["pilot", "--role", "advocate", "--report", str(tmp_path / "missing")]) == 2
```
