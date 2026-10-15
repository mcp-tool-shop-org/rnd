---
id: dataset-desk
title: dataset-desk — review a visual dataset before it trains or tests anything
date: 2026-10-15
kind: instrument
relevance: act
fields: [studio-tooling, image-generation, embeddings]
tags: [instrument, datasets, lora, siglip2, embeddinggemma]
instrument_status: shipped
invoke: "dataset-desk index|dupes|search|coverage|report --project P --backend none|siglip2|eg2 --out O"
when: "Before training a style LoRA or freezing a retrieval benchmark: find duplicates and outliers, and check that every description describes its image rather than echoing its prompt."
where: "github.com/mcp-tool-shop-org/dataset-desk (v0.1.0); design record in experiments/dataset-desk"
---

## Summary

A Python CLI that reads a style-dataset-lab project and writes a report and a review queue, without changing the
project. It finds three tiers of duplicates (sha256, dHash, embedding cosine) and ranks outliers by content and by a
30-number look channel. It searches by words or picture. Its model-free description gate is the same code as the
EmbeddingGemma 2 multimodal benchmark's query gate. The lite tier (`--backend none`) needs only numpy and Pillow.

## Studio relevance

It's the first step of the desk stage in the EmbeddingGemma 2 multimodal design (revision 3): every query pool passes
its gate before the manifest is frozen. It's also the pre-training check for any style LoRA set. CPU by default, under
the rig's thread caps; a GPU needs a Publisher grant (`--grant`).
