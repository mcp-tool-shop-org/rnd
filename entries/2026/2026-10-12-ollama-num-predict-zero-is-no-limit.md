---
id: 2026-10-12-ollama-num-predict-zero-is-no-limit
title: Ollama 0.35.1 reads num_predict 0 as no limit
date: 2026-10-12
kind: rig-fact
relevance: act
fields: [local-inference]
tags: [ollama, switchyard, test-fakes]
---

## Summary

On Ollama 0.35.1, a generate request with `num_predict` 0 is treated as having no completion limit. The model keeps
generating until its context fills, so it never returns a single empty step. switchyard's token count (#60) sent 0,
on the assumption that it meant "no completion, just count the prompt". E4's first live run held the 5090 at about
575 W for about 12 minutes and wrote no row. The tests had passed because a fake server accepted 0 as the count
assumed.

## Key points

- **Failure:** every token count in E4's first run became a full generation until the 40K-token context filled.
- **Evidence (on the rig):** `num_predict` 0 gave no reply within 90 s, and `num_predict` 1 returned
  `prompt_eval_count` 221 in 3.0 s.
- **Fix (switchyard #65):**
  - the count always asks for one token, and the zero-then-retry path is removed;
  - `generate_body` refuses a `num_predict` that is 0, null, missing, a bool or not a positive whole number, before any
    request is made;
  - the fill-card spec refuses `confirm_num_predict` below 1;
  - the test fake fails any test that sends 0.
- **Prevention (switchyard #71, in review):** fakes may imitate only recorded real exchanges, one per adapter
  parameter. A parameter whose recording never answers is refused by the fake, and a test fails if the adapter can
  send an option with no recording. The count call also gets a time budget.
- **Defect class:** `test_fake_hides_platform`, second instance (the first was psutil's disk keys in #63).
- **Handling:** E4 was stopped under the Publisher's grant, and no rows were written.

## Studio relevance

Any studio code that calls Ollama must send a positive `num_predict`. A missing or null value means the same as 0 to
the server. It also shows why a fake has to be built from what the real server does, not from what the code assumes.
See [[2026-10-12-prefix-fit-count-cost]] for the third instance the same day.

## Claims

- [verified] On Ollama 0.35.1 on the 5090 rig, `num_predict` 0 gave no reply within 90 s, and `num_predict` 1 returned a prompt count of 221 in 3.0 s (via: the Publisher's direct calls on the rig, 2026-10-12)
- [verified] E4's first live run sat at about 575 W for about 12 minutes with no row (via: the Publisher's run log, 2026-10-11)
- [unverified] A missing or null `num_predict` behaves the same as 0. That follows from the server's defaults and is what #71's recording will measure.

## Sources

- [primary] https://github.com/mcp-tool-shop-org/switchyard/pull/65 — the fix and its R&D review
- [primary] https://github.com/mcp-tool-shop-org/switchyard/pull/71 — the recorded-exchange fakes
- [primary] https://github.com/mcp-tool-shop-org/switchyard/pull/60 — the token count that introduced 0
