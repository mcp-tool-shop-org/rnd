---
id: 2026-10-12-prefix-fit-count-cost
title: Prefix fitting cost one count per seed repeat
date: 2026-10-12
kind: finding
relevance: act
fields: [local-inference]
tags: [switchyard, ollama, test-fakes]
---

## Summary

E5 builds each confirmation prompt by repeating a seed sentence until the served model counts a target number of
tokens. For llama3.1:8b's full 131K window, that target is about 118k tokens. `fit_prompt_words` added one seed and
counted again on each step, which took thousands of counts. Each count re-read the whole growing prompt. E5 spent
over 30 minutes on that model and wrote no row, though Ollama itself prefilled 122k tokens in 19.6 s. switchyard #70
estimates the repeats from the seed's own count and bisects only the remaining tail. It takes 25 counts or fewer at
118k, and the output is unchanged.

## Key points

- **Failure:** the cost of the search grew with the target, one count per repeat. It was harmless at E4's 256 tokens
  and ruinous at 118k.
- **Evidence:** the server was not slow. A direct call prefilled 122k tokens in 19.6 s. The time went into the number
  of counts.
- **Fix (#70):**
  - estimate the repeats from the seed's count, and check one repeat below for a known-short prefix;
  - top up in proportion, then bisect the word cuts past the known-short prefix only.

  It is the same shortest word-boundary prefix as before, and a test bounds 118k at 25 counts.
- **Result:** on the re-run, llama3.1:8b finished in about 25 minutes.
- **Watch:** the trim now counts shorter prefixes of a prompt the server just evaluated. The cold re-count of the
  final prefix stays the guard against prompt-cache undercounting.
- **Prevention:** a count budget per fit is now part of the fakes' contract. Fakes take no time, so a cost test has to
  count calls.
- **Defect class:** `test_fake_hides_platform`, third instance. The fakes never measured cost, so a 10,000-count
  search looked the same as a 25-count one.

## Studio relevance

Any search against a live model should be tested for how many calls it makes, not just for its answer. See
[[2026-10-12-ollama-num-predict-zero-is-no-limit]] for the second instance of the same class.

## Claims

- [verified] Ollama prefilled 122k tokens in 19.6 s on the rig (via: the Publisher's direct call, 2026-10-12)
- [verified] After #70, llama3.1:8b's E5 run finished in about 25 minutes (via: the Publisher's run report, 2026-10-12)

## Sources

- [primary] https://github.com/mcp-tool-shop-org/switchyard/pull/70 — the fix and its R&D review
