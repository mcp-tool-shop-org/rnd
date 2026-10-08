---
id: 2026-10-08-llm-piano-arrangement-from-a-generated-brief
title: Piano arrangements by an LLM from a brief generated from the score
date: 2026-10-08
kind: finding
relevance: act
fields: [music, machine-learning]
tags: [method, lilypond, arrangement, kimi-k3, openrouter, hymns, ai-jam-sessions]
---

## Summary

A reasoning model can write a complete solo-piano arrangement in LilyPond that compiles
and keeps the melody exactly where a singer needs it. Two conditions make it work: the
brief is generated from the score rather than written by hand, and machine checks gate
the answer. Two hymns were arranged this way for $1.31 in all, and the Director approved
both by ear.

## Key points

- **The brief comes from the hymn data:**
  - the melody bar by bar in LilyPond absolute pitches, with chords per beat;
  - every stanza, and the shape (intro, one pass per stanza, coda);
  - a texture plan that builds from verse to verse;
  - rules a machine can check: no `\partial` after the start, the melody as top voice in
    every pass at its written time, no pedal marks, no repeats, tuplets or `\ottava`.
- **Model:** Kimi-K3 (`moonshotai/kimi-k3`) on OpenRouter, reasoning high, temperature 0,
  max_tokens 200,000. At $0.72 per million input tokens and $15 per million output, the
  worst case is $3.00. The script prints the worst case and spends only with `--yes`.
- **Gates:**
  1. LilyPond 2.24 compiles with no error or warning.
  2. The MIDI import checks that every verse's melody is in the piano.
  3. The score clock refuses any sung note with no piano note under it.
- **Kept per arrangement:** the brief, the system prompt, the raw answer, the compiled
  `.ly`, and meta.json (sha256 of each, generation id, usage and cost, any hand fixes).

## Studio relevance

The Director approved the method on 2026-10-08, and it is now part of the ai-jam-sessions
sung-exemplar runbook (`scripts/arrange-hymn.ts`; instrument [[sung-exemplar-method]]).
OpenRouter is a **paid lane**, on only for these arrangements, under the Director's go of
2026-10-08: estimate first and record the cost. The interpretation the arrangement is
played with (tempo arch, beat emphasis, coda) is R&D's per-hymn shape. The Battle Hymn's
arrangement predates this script: it came from si-jam-sessions on 2026-09-26.

## Claims

- [verified] Amazing Grace cost $0.298 (1,728 tokens in, 19,510 out, about 3 minutes) and America the Beautiful $1.013 (1,956 in, 67,147 out, about 9 minutes). (via: OpenRouter usage recorded in meta.json, 2026-10-08)
- [verified] One of the two answers needed a hand fix (`\key g major` for `\key g \major`, twice); the other compiled as returned. (via: meta.json fixes, 2026-10-08)
- [verified] Both arrangements passed the melody-match import and the score clock, and the Director approved both recordings over them. (via: ai-jam-sessions PR #109 and the Director's listen, 2026-10-08)
- [verified] The arrangements can be dedicated CC0: the Kimi K3 License claims no rights in outputs, and OpenRouter's and Ollama's licences in the content are non-exclusive. (via: Kimi K3 LICENSE and OpenRouter Terms read at source by ai-jam-sessions and R&D, 2026-10-08; Ollama Terms read at source by ai-jam-sessions, 2026-10-08)
- [verified] The tunes and texts are public domain: every edition followed is from 1919 or earlier and every author died before 1930, and the briefs give each hymn's own melody and chords, not a modern harmonisation. (via: the sources cited in ai-jam-sessions src/vocal/hymns.ts and si-jam-sessions' Battle Hymn receipt, checked 2026-10-08)
- [verified] Counting the Battle Hymn (arranged on Ollama Cloud on 2026-09-26, before arrange-hymn.ts), two of the three answers needed a one-line fix: Amazing Grace's key mode, and the Battle Hymn's missing `\language "english"`. (via: si-jam-sessions draft against the published file, 2026-10-08)
- Data pack: `datapacks/hymn-arrangements` (private until the Director decides).

## Sources

- [primary] https://openrouter.ai/moonshotai/kimi-k3 — model page and pricing
- [primary] https://lilypond.org/doc/v2.24/Documentation/notation/ — LilyPond 2.24 notation reference
- [primary] https://huggingface.co/moonshotai/Kimi-K3/blob/main/LICENSE — Kimi K3 License
- [primary] https://openrouter.ai/terms — OpenRouter Terms of Service (§5.8, §6.1, §6.2)
- [primary] https://ollama.com/terms — Ollama Terms (§5, §7)
- [rig] ai-jam-sessions scripts/arrange-hymn.ts and src/vocal/arrangements/source/<id>/; PRs #107, #109, 2026-10-08
- [user] The Director's approval of the OpenRouter lane and of both recordings, 2026-10-08
