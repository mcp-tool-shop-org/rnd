---
id: 2026-10-12-windows-26340-listener-state-closed
title: Windows build 26340 reports a listening socket as Closed
date: 2026-10-12
kind: rig-fact
relevance: act
fields: [local-inference]
tags: [windows, ollama, switchyard]
---

## Summary

After an overnight update to Windows 11 build 26340, `Get-NetTCPConnection` on the rig reports Ollama's listening
socket on 127.0.0.1:11434 with state Closed (0) instead of Listen. Remote address and port are 0.0.0.0:0, and the owning
process is the live server. netstat's LISTENING filter also finds nothing, though the server answers. Every lookup that
filtered on `-State Listen` returned nothing, and the E4b pilot refused at start. switchyard #83 selects the socket on the
port with remote port 0 instead.

## Key points

- **Symptom:** "the 11434 listener report is not JSON", because the lookup returned nothing. Nothing was spawned.
- **Fix (#83):** match the local port with `RemotePort -eq 0`. A connected socket always has a remote port.
- **Follow-up (open):** with no state filter, a leftover remote-port-0 entry, or a second listener, can match. Before
  stopping a process, the supervisor should refuse more than one distinct PID and check that the executable is
  `ollama.exe`.

## Studio relevance

Any studio script that finds a local server by listening state (`-State Listen`, netstat LISTENING) is broken on this
build. Look up by port with remote port 0, and confirm the process before acting on it.

## Claims

- [verified] On build 26340 the 127.0.0.1:11434 listener reports state Closed, remote 0.0.0.0:0, with the server's own PID (via: R&D's Get-NetTCPConnection read on the rig, 2026-10-12)

## Sources

- [primary] https://github.com/mcp-tool-shop-org/switchyard/pull/83 — the fix and its R&D review
