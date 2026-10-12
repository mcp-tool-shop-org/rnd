---
id: 2026-10-12-test-fakes-hide-the-platform
title: Test fakes that hide the platform, a recurring defect class
date: 2026-10-12
kind: finding
relevance: act
fields: [local-inference]
tags: [switchyard, test-fakes, defect-class]
---

## Summary

In two days, switchyard's live runs failed again and again for one reason: a test fake behaved the way the code assumed,
not the way the real platform does. The unit tests passed, and the live run stopped. R&D tags these
`test_fake_hides_platform`. By 2026-10-12 the class counted these instances:
- psutil's disk keys (#63);
- `num_predict` 0 read as no limit (#65);
- a search's call count (#70);
- the NLI model's flat logits;
- the live command runner that captured no output (#84);
- E4b's pilot counting tokens before its own server started (#85);
- the live seams left as stubs (#85's review).

## Key points

- **The pattern:** a test injects a seam (a transport, a runner, a sampler), and the live default is never exercised. It
  may be a stub, missing, or wired wrongly.
- **#84:** the fakes returned stdout, but a bare `subprocess.run` doesn't capture it. The pin read parsed an empty
  string, and the git read reported a clean tree with no sha. R&D required the git read to fail closed: exit codes
  checked, a 40-hex sha, and clean only on a successful empty read.
- **#85's review found more stubs and gaps in the live seams:**
  - GPU sampling returned (None, None);
  - the CPU counter and the burn were no-ops;
  - VRAM wasn't recorded;
  - HTTP had no timeout;
  - the server start didn't wait for the port.
- **Remedies, in order of strength:**
  1. real recorded exchanges for fakes (#71);
  2. one test that builds the live seams with nothing injected and asserts that none is a stub;
  3. reads that fail closed, so a missing value refuses instead of passing.
- **Cost so far:** three pilot attempts stopped at start with the card idle. No device time was lost, because each
  check ran before the server or a device started.

## Studio relevance

Any harness that injects its external calls for testing should also have a test of its live wiring, and its reads
should fail closed. A green suite says nothing about seams the tests always replace.

## Claims

- [verified] The fakes' stdout hid an uncaptured live runner, which gave an empty pin and a clean-tree result with no sha (via: switchyard #84 and the Publisher's live check, 2026-10-12)
- [verified] E4b's live seams defaulted GPU sampling to (None, None), and the CPU counter and burn to no-ops (via: R&D's read of #85 at its head, 2026-10-12)

## Sources

- [primary] https://github.com/mcp-tool-shop-org/switchyard/pull/84 — capture and the fail-closed git read
- [primary] https://github.com/mcp-tool-shop-org/switchyard/pull/85 — the prompt order and the live-gap list
- [primary] https://github.com/mcp-tool-shop-org/switchyard/pull/71 — the recorded-exchange fakes
