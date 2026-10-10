---
title: Research brief directory
description: One page per research question, with its findings, charts, caveats and receipts.
sidebar:
  order: 0
---

Each brief answers one question the studio put to its own machines or to the literature. Every brief follows
the same shape:

- **The question**, and why the studio asked it.
- **What we found**, in plain words, with the numbers.
- **Charts**, built only from committed receipts by `experiments/charts/make_charts.py`.
- **Caveats**: what the numbers can't be used to claim.
- **Receipts**: the repository, commit and path behind every figure.
- **Shelf status**: whether the finding has been promoted to a readouts knowledge base yet.

Status labels mean the same thing everywhere:

| label | meaning |
|---|---|
| measured | run on our machines; receipts committed; not independently checked |
| confirmed | a pre-registered check passed, such as a held-out split |
| interim | partial, or waiting on a run or a licence |
| disproved | tested and found wrong; kept so nobody rediscovers it |
| research | from published sources, not measured here |

Pre-registered and post hoc results are labelled on every chart. A post hoc result is one we went looking for
after seeing the data; it's useful, but weaker.

Start from the [newsletter](../) for what changed lately, or pick a brief from the sidebar.
