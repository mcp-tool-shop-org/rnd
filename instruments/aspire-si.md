---
id: aspire-si
title: aspire-si — train a student to internalise a teacher's judgment
date: 2026-10-07
kind: instrument
relevance: reference
fields: [machine-learning, training, evaluation]
tags: [instrument, aspire, critic, lora, scalarscope]
instrument_status: shipped
invoke: "pip install aspire-si (1.2.0, MIT); aspire train … ; aspire judge … (a trained critic scores a response without calling the teacher)"
when: "Research needs a small model that judges like a large teacher, or a cheap learned critic for scoring candidate outputs."
where: "github.com/mcp-tool-shop-org/aspire-si (public), PyPI aspire-si"
---

## Summary

ASPIRE (Adversarial Student-Professor Internalized Reasoning Engine) trains a
student model through adversarial dialogue with a teacher and learns a critic
head that scores responses. Schema 1.1 exports training-dynamics geometry for
ScalarScope.

## Studio relevance

The run reports under `docs/runs/` are measured research in their own right; see
[[2026-10-07-sft-before-aspire-weakens-critic]] and
[[2026-10-07-qwen32b-judge-position-bias]].
