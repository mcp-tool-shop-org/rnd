---
id: 2026-10-08-translategemma-failure-modes-on-readme-tables
title: TranslateGemma 27B mistranslates fractions and transliterates model names
date: 2026-10-08
kind: finding
relevance: act
fields: [translation]
tags: [translation, polyglot, translategemma, readme, chinese, hindi]
---

## Summary

The README translation pass (TranslateGemma 27B, run locally through polyglot-mcp) is
reliable on prose. It makes systematic slips on two things a reader relies on: counts
written as "N of M", and product or model names.

## Key points

- **Chinese, fractions:** "285 of 414" became an ordinal, "the 285th of 414"
  (414个中的第285个). An older table cell read reversed: "224 of 218" (218 首中的 224 首)
  for 218 of 224.
- **Hindi, names:** "Kimi-K3" became Devanagari (किमी-के3). The polyglot cache brings the
  transliteration back on the next run, so it reappears after a hand fix.
- **The check that catches them:** compare verbatim English lines before and after; count
  negations and "only" in each changed block; read the flagged lines by hand. Numbers in
  "N of M" form need their own look.

## Studio relevance

Affects every README translated before a release under the translation workflow. After
each run, fix the known patterns by hand, and re-check Hindi names every time, since the
cache will not keep the fix.

## Claims

- [verified] Both Chinese errors and the Hindi transliteration appeared in the ai-jam-sessions README translations and were fixed by hand. (via: hand review of the 7 translations, 2026-10-08)
- [verified] The Hindi transliteration came back on a second run after it had been fixed. (via: the same review, 2026-10-08)
- [unverified] The pattern generalises beyond this README (other "N of M" tables, other names).

## Sources

- [rig] TranslateGemma 27B via E:/AI/polyglot-mcp/scripts/translate-all.mjs on the RTX 5090 (Publisher grant), ai-jam-sessions PR #113, 2026-10-08
