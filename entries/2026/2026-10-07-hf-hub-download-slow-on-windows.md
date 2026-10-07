---
id: 2026-10-07-hf-hub-download-slow-on-windows
title: huggingface_hub downloads at 2 MB/s on the Robot rig where plain curl gets 46.5 MB/s
date: 2026-10-07
kind: rig-fact
relevance: watch
fields: [ai-infrastructure, developer-tools]
tags: [huggingface-hub, xet, download, windows, curl, speed-probe]
---

## Summary

Measured by aspire-si on 2026-10-07 on the Robot rig. Downloading the same file:

| method | speed |
|---|---|
| `huggingface_hub.hf_hub_download` | 2 MB/s |
| one plain curl stream | 46.5 MB/s |

Timing the library measures the library, not the connection. The cause is
unknown; the xet transfer path on Windows is the main suspect.

## Key points

- Speed probes should use plain HTTP (curl), not the HF library.
- For large weights on this rig, a plain `curl -L` of the `resolve/main/...`
  URL is the fast path.
  - The OpenJev GGUF (16.55 GB) was fetched that way on 2026-10-07.
  - Verify against the repo's published SHA-256 afterwards.

## Studio relevance

When a model download "stalls" on this rig, test the pipe first with curl
before blaming the network or the host (the standing test-the-pipe rule). If the
library is the slow part, use curl plus checksum verification.

Open question: whether disabling xet (`HF_HUB_DISABLE_XET=1`) or using
`hf_transfer` restores speed. Not yet tested.

## Claims

- [verified] On the Robot rig, hf_hub_download measured 2 MB/s while one curl stream to the same file ran at 46.5 MB/s. (via: aspire-si measurement, reported by session A 2026-10-07)
- [unverified] The slowdown comes from the xet path on Windows.

## Sources

- [rig] aspire-si download measurement on the Robot rig, 2026-10-07, by session A
