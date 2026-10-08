---
id: 2026-10-08-pages-cache-stitches-replaced-media
title: Replacing a media file under the same URL on GitHub Pages can break playback
date: 2026-10-08
kind: finding
relevance: act
fields: [web-ops]
tags: [github-pages, http-cache, range-requests, audio, opus]
---

## Summary

GitHub Pages serves files with `Cache-Control: max-age=600`. A browser that had part of
the old recording buffered fetched the rest from the new one at the same URL. The two
halves did not line up, and playback died about a minute in. It cleared when the cache
expired. The rule: a replaced recording gets a new filename, or a version in its URL.

## Key points

- Media elements fetch by byte range, so a partly buffered file is a cached head plus
  later ranges. Within max-age, the browser may reuse the head without revalidating.
- The new Opus file was 520 bytes longer than the old one, so its pages fell at different
  offsets and the stitched stream broke at the join.
- The live file was correct the whole time: it had the same sha256 as the repo, Chrome
  decoded it to full length, and its Ogg granules were clean. Checking the server proves
  nothing about a viewer who was mid-buffer during the swap.

## Studio relevance

Applies to every published recording (the ai-jam-sessions landing page), and to any
binary asset replaced in place on Pages.

## Claims

- [verified] Pages answered `Cache-Control: max-age=600` for the audio files. (via: curl -I on the live files, 2026-10-08)
- [verified] Right after the deploy, the replaced America the Beautiful stopped about a minute in for the Director. It later played in full with no change on the server. (via: the Director's report and a byte-for-byte check of the live file, 2026-10-08)
- [unverified] The mechanism is the browser stitching a cached old head to new ranges. It fits the size change, the timing and the self-healing, but it was not reproduced.

## Sources

- [primary] https://developer.mozilla.org/en-US/docs/Web/HTTP/Range_requests — HTTP range requests
- [rig] curl and Chrome Web Audio checks of the live ai-jam-sessions audio, 2026-10-08
- [user] The Director's report, 2026-10-08
