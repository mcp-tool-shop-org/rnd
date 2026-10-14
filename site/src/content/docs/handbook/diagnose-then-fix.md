---
title: Diagnose-then-fix studies
description: A design template for using a diagnostic tool to find why a system wastes work, changing the system, and checking that the change helped.
sidebar:
  order: 4
---
Approved by the Director, 2026-10-13.

A diagnose-then-fix study has two parts. It uses a diagnostic tool to find why a system wastes work or fails, then changes the system and checks that the change helped. It inherits every check in the [A/B experiments](../ab-experiments/) template, and adds these.

## 1. The check, in three sentences per stage

- **Stage 1 (diagnosis):** what the tool must reveal, on which runs, compared with which existing records.
- **Stage 2 (verification):** what each arm gets. The baseline is the unchanged system. The treatment is the system with only the pre-registered fixes.
- **Why stage 2's difference answers the question.**

## 2. One run, two captures (stage 1)

The diagnostic tool observes without changing the run, so each run is recorded once by both the tool and the existing logs. Before relying on that, a short pilot checks that the tool really doesn't change the run.

## 3. Planted defects (stage 1)

A detector can't be judged on runs that happen to be clean. Stage 1 mixes natural runs with a pre-registered set of planted faults, one or more per kind of waste that's being looked for. Each fault comes with what it should look like in the records.

## 4. A blinded, normalised read (stage 1)

- **First, matched scripts:** the same detection rules, written once for each record format, run over both.
- **Then, a blind human or model read** for what the scripts can't decide: both formats are normalised into the same table, the tool's names are stripped, and the cases are shuffled.

## 5. A split that is locked

- **Two banks, kept apart:** the diagnostic bank D, for finding and tuning, and the verification bank V, for scoring. They're disjoint by repository or source, not just by question.
- **V is locked:** it isn't looked at or run until the fixes are frozen in git.
- **No re-scoring D:** scoring the fixes on D measures tuning, not improvement.

## 6. A symptom-to-fix table, fixed in advance

Before stage 1 runs, write down which kind of fix each symptom permits. For example: forbidden tool calls permit pruning the prompt and gating the tool policy; oversized tool output permits output truncation.
- Fixes are general to the system, never hints for particular tasks.
- A fix that isn't in the table needs a dated amendment, before V runs.

## 7. Attribution (stage 2)

The treatment arm must show that each fix's targeted symptom actually fell, as well as better scores. If scores rose while the targeted symptom stayed flat, the gain isn't attributed to the fix.

## 8. Fresh, interleaved verification

Stage 2 runs the baseline and the treatment fresh on every V task, interleaved in a seeded order. Re-running only the worst cases from stage 1 measures regression to the mean.

## 9. Verdicts by stratum

Tasks are classified by kind before any run (for example, single-step lookups against multi-step reasoning). The decision is made per stratum, so a fix can be adopted where it works and not elsewhere.

## 10. Total cost of ownership

Alongside the effect, report:
- setup time;
- run overhead;
- the size of the records, before and after trimming;
- the code added per system;
- whether a simple native counter would give most of the value.
