---
id: 2026-11-24-two-languages-one-state-digest-what-a-deep-research-audit-fo
title: Two languages, one state digest: what a Deep Research audit found (seed 57)
date: 2026-11-24
kind: finding
relevance: act
fields: [software-design, testing]
tags: [ai-rpg-engine, ai-rpg-stage, seed-57, harvest, determinism]
---

## Summary

The studio's RPG engine (TypeScript, the authority) and its Godot client (GDScript) are meant to agree on one hash of the
game state. That way the client can prove that its copy of the world matches the engine's. We asked a Gemini Deep Research
run how two languages can produce a byte-identical state digest, and how a client should verify and recover when they
disagree.

The report is `[aggregator]` AI output with 119 cited sources. We compared it with the engine at `03342f5` and the stage
client at `c25ed2b`; its cited papers were not read for this entry.

Our own reading found a real bug. The engine keeps keys whose value is null in the hash's input, while the GDScript copy
drops them, so any state with a null field hashes differently in the two languages. Nothing caught this, because the only
"Godot" test runs JavaScript against a JavaScript imitation of Godot.

## Key points

- **Never hash text from a float formatter.** Each runtime prints floating-point numbers its own way, so the report's
  advice is to keep formatter output out of the digest's input altogether. Our digest formats six decimals in both
  languages: `toFixed` in JavaScript, and a C-style `%.*f` in GDScript.
- **Rounding differs on negative ties.** JavaScript's `Math.round` sends ties toward +infinity, while GDScript's `round`
  sends them away from zero. Before formatting, both sides round to six decimals, so a negative exact tie gives different
  digits. The report missed this one; our harvest found it.
- **Nulls must be kept on both sides.** The authority's form keeps them, so the client must too.
- **Pin the key order and the character set.** JavaScript sorts keys by UTF-16 code units and GDScript by code points.
  They differ only on rare characters, so the simple rule is ASCII-only keys in authoritative state, checked by the
  authority.
- **Shared test vectors are the real test.** One file of inputs, expected pre-images and expected hashes should be run by
  both languages, with real GDScript under headless Godot, on Linux and Windows.
- **One name, one version.** Two functions called `canonicalStateHash` hash different inputs. The digest's format should
  carry a version in the handshake.
- **Verify, then recover.** The client should recompute the digest on its own copy after each move. On a mismatch it should
  take a full snapshot, check it again at once, cap the retries, and report the first byte where the inputs differ.

## Studio relevance

### What it contradicts in our design (read first)

| Finding | ai-rpg-engine `03342f5` / ai-rpg-stage `c25ed2b` | Decision (2026-11-24) |
|---|---|---|
| Nulls must be kept | The authority writes `null`; the GDScript `_quantize` skips null values | GDScript keeps nulls, as the authority does |
| No formatter text in the digest | `toFixed(6)` in JavaScript, `%.*f` in GDScript | Every number is written as an integer: the value times 10^6, rounded half away from zero, with an explicit sign-aware round in JavaScript. The authority refuses values whose scaled form is beyond 2^53 - 1 |
| One cross-language test needed | The "Godot" test compares JavaScript with a JavaScript imitation | A shared vector file, run in vitest and in real headless Godot in CI, plus one run on Windows |
| One digest, one name | Two `canonicalStateHash` functions with different inputs | Rename the core alias; add `digest_spec_version` to the handshake |
| The client verifies its copy | The stage's handshake does not ask for the canonical hash, and `verify_position` runs only in tests | After each move the stage checks its copy against the engine's digest. On a mismatch it resyncs from a full snapshot, with a cap of 3 in a row, and play stops past the cap |

### Decisions and actionables

1. The engine changes (nulls, integer numbers, ASCII keys, one name, a version field, shared vectors run in real Godot)
   are one build, now in progress.
2. The stage then requests the canonical hash, verifies after every move from play, and resyncs with a cap. That is a
   second build, after the first merges.
3. **Filler for now:** Merkle or two-tier digests, homomorphic multiset hashes, deterministic CBOR and schema code
   generation. Each is sound for larger states than ours, and none is needed here.

## Claims

- [verified] The authority's canonical writer emits `null` for null values and skips only `undefined` (via: `packages/sidecar/src/serializer.ts:249-250` and `:271` in mcp-tool-shop-org/ai-rpg-engine at 03342f5, read by R&D, 2026-11-24)
- [verified] The GDScript client skips null values when it quantizes (via: `packages/sidecar/gdscript/sidecar_client.gd:393-397` at 03342f5, read by R&D, 2026-11-24)
- [verified] JavaScript quantizes with `Math.round(value * factor) / factor` and formats with `toFixed`, while GDScript quantizes with `round` and formats with `"%.*f"` (via: `serializer.ts:27-33` and `:257`, `sidecar_client.gd:377-383` and `:414` at 03342f5, read by R&D, 2026-11-24)
- [verified] Two exported functions are named `canonicalStateHash` and hash different inputs (via: `packages/core/src/state-hash.ts:39-47` and `packages/sidecar/src/serializer.ts:284` at 03342f5, read by R&D, 2026-11-24)
- [verified] The only cross-language hash test compares JavaScript against a JavaScript fixture that mimics Godot (via: `packages/sidecar/src/serializer.test.ts:46-57` at 03342f5, read by R&D, 2026-11-24)
- [verified] The stage's handshake asks for notifications, hashes and audio, not the canonical hash, and `verify_position` is called only from a test (via: `client/network_client.gd:144` and `:268`, `tests/test_wire_session.gd:67` and `:77` in mcp-tool-shop-org/ai-rpg-stage at c25ed2b, read by R&D, 2026-11-24)
- [unverified] A Godot issue filed in November 2026 reports float misprinting on Windows in 11,747 of 200,000 cases (the reporter's figure, cited by the report; not reproduced, and the issue was closed with its cause unconfirmed)
- [unverified] `Math.round` and GDScript `round` differ on negative exact ties at six decimals (from each language's documented rounding rule; to be confirmed by the shared vectors)

## Sources

- [aggregator] https://gemini.google.com/ — Gemini Deep Research (Gemini 4 Carbon, High), 2026-11-24: "Cross-Language State Digest Specification and Verification Architecture for Node.js and Godot"
- [primary] https://github.com/mcp-tool-shop-org/ai-rpg-engine — the engine and its sidecar serializer, read at 03342f5
- [primary] https://github.com/mcp-tool-shop-org/ai-rpg-stage — the Godot client, read at c25ed2b
- [primary] https://www.rfc-editor.org/rfc/rfc8785 — Rundgren, Jordan and Erdtman (2020), JSON Canonicalization Scheme (RFC 8785) (cited by the report; its key-sort and number rules were read at source during our harvest, not re-read for this entry)
