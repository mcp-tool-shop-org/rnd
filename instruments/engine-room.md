---
id: engine-room
title: engine-room — provision local AI engines
date: 2026-10-07
kind: instrument
relevance: reference
fields: [studio-tooling, gpu-computing, local-llm]
tags: [instrument]
instrument_status: shipped
invoke: "npx @mcptoolshop/engine-room <cmd>  (v1.0.0 on npm; the 'er' command is not on PATH on this rig)"
when: "Research needs a local inference engine stood up, measured, or rolled back on this rig."
where: "E:/AI/engine-room · recipes in readouts/tensor-engine-knowledge"
---

## Summary

Recipe-driven provisioner: browse verified recipes → resolve against the live rig → provision / launch / measure / roll back. Dry-run by default.

## Studio relevance

Use it instead of improvising engine installs when an experiment needs one.
