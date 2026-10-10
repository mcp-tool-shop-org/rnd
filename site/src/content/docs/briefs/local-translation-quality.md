---
title: How safe are local README translations?
description: The studio's local translator, TranslateGemma 27B, broke a test-pinned sentence in 5 of 7 languages on one README and reversed one sentence's meaning. Translations now get checked against pinned sentences.
date: 2026-10-08
status: measured (one run)
shelf: pending (readouts-internal)
---

## The question

Every studio README is translated into seven languages, locally, by TranslateGemma 27B through Ollama. Are the
translations faithful enough to publish unchecked?

## What we found

On ScalarScope's 3.1.1 README, one run:

- **5 of 7 languages** reworded a sentence the tests pin word for word: French, Japanese, Chinese, Spanish and
  Italian.
- **1 of 7 reversed a sentence's meaning** (Japanese).
- **2 of 7 mistranslated a key term** since 3.1.0: "bundle" became "dataset" in French and Spanish.

## What changes

A translation is not the last unchecked step. Each translated page is checked against the source's pinned
sentences and terms. A mismatch is fixed by hand, or that language is left out of the release, before anything
is committed or tagged. ScalarScope now guards its pinned sentence with a test.

## Caveats

- One README, one run. This shows the risk; it doesn't give an error rate.

## Receipts

`mcp-tool-shop-org/scalarscope` d55deb6 (the hand fixes, in the commit "README translations for 3.1.1") and
`tests/ScalarScope.FixtureTests/StageCWordingTests.cs`.
