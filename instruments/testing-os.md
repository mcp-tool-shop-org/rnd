---
id: testing-os
title: testing-os — dogfood records, findings and the swarm control plane
date: 2026-10-13
kind: instrument
relevance: reference
fields: [studio-tooling, agent-orchestration]
tags: [instrument]
instrument_status: shipped
invoke: "swarm <cmd> (dogfood-swarm), dogfood-verify, dogfood-report, dogfood-init, findings  (npm @dogfood-lab/*, lockstep 1.26.0); Atlas has its own instrument"
when: "A question needs a repo's recorded dogfood verdicts, evidence-bound findings, or a mechanically coordinated multi-agent pass over a repo."
where: "E:/AI/testing-os · github.com/dogfood-lab/testing-os · dogfood-lab.github.io/testing-os/"
---

## Summary

The flagship monorepo of the dogfood-lab org: eight `@dogfood-lab/*` packages, seven of them published.

- **schemas:** eight JSON Schema 2020-12 contracts (record, finding, pattern, recommendation, doctrine, policy, scenario, submission).
- **verify:** checks a submission against the schemas and the repository's policy.
- **ingest:** dispatch, then verify, then persist, then indexes.
- **report:** builds the submission a consumer sends.
- **findings:** validates, derives and reviews evidence-bound findings.
- **dogfood-swarm:** the `swarm` CLI over a SQLite control plane, with domain ownership, finding dedup, wave receipts, resumability and the `swarm verify` gate.
- **portfolio (private):** the cross-repo report.
- **atlas:** see `atlas`.

## Studio relevance

Consumer repos send their CI verdicts through a public dispatch. The ingest workflow verifies each one and commits it under `records/`, with indexes under `indexes/`. repo-knowledge and shipcheck read those paths through raw GitHub URLs, so the paths are a public API.

## What it measures

- **A repo's own verdict:** whether its dogfood run passed under its policy, with provenance (`github`, `gitlab` or `stub`) and an integrity hash chain over the records.
- **Findings:** each one carries its evidence and has a review state.
- **A swarm run's state:** waves, ownership, open and fixed findings, and the verify gate's result.

## What it does not measure

- **Product behaviour:** a record says a repo's own checks passed under its policy, not that the product works for a user.
- **The truth of a submission's claims:** `verify` checks shape and policy only.
- **External verification:** since 2026-09-29 the swarm runs no verifier pass by default; `swarm verify` (the test suite) is the gate.

## In build (R&D ruling, 2026-10-13)

A static check for the `test_fake_hides_platform` class found in interlock:
- a `run` or `subprocess.run` called without capturing output, whose `.stdout` is then read;
- a live builder whose injectable seam defaults to a constant `None`.

What counts as a finding is pre-registered first. Then it runs over the fleet, and R&D judges precision against interlock's history.
