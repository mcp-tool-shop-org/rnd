---
title: Relevance grading
description: A template for grading pooled retrieval results into an answer key that is consistent, blind to the arms, and auditable, before any retrieval metric is computed.
sidebar:
  order: 7
---

A retrieval experiment (an embedder, a reranker, a search change) gets its answer key by grading. Each query's candidate passages are pooled from every arm's top results, stripped of which arm found them, shuffled and graded on a fixed scale. Metrics such as nDCG, recall and MRR are computed only after the grades are frozen. The grades must be consistent between graders, blind to the arms, and auditable. Then a ranking difference is a model difference, not a grader difference.

Fill in every section for your experiment, and record any deviation in its design. The first draft was written by an outside model (Argon) at the Director's request, and R&D adapted it for the studio. The first use is the EmbeddingGemma 2 benchmark in `experiments/embeddinggemma-2/`.

## 1. The scale

Three grades: 0, 1 and 2. nDCG uses the gain `2^g − 1`, so a 2 is worth three times a 1. Recall@k and MRR count a 1 or a 2 as relevant. **The line between 0 and 1 moves recall and MRR. The line between 1 and 2 moves nDCG.**

| Grade | Meaning | The check |
|---|---|---|
| 2 | Answers it | The chunk holds the complete answer, or the exact code the query asks for. A reader could stop searching here. |
| 1 | Helps | On topic, and part of the answer: a strong pointer, a test or a caller, or half of an answer that needs another chunk. A reader learns something useful but must keep searching. |
| 0 | Doesn't help | Shares words, sits in the same file, or answers a neighbouring question, but gives nothing toward the intent. |

**The query's form decides what answering means:**
- **Where is X.** 2 is the definition, declaration or primary configuration. 1 is a chunk that imports, calls or references X and shows where it lives.
- **How does X work.** 2 is the implementation body, or an architecture section that explains the control flow. 1 is a signature, an interface, a summary, or a test that asserts the behaviour without showing the mechanism.
- **Why.** 2 is a design note, a decision record, a commit or PR note, or a comment that explains the decision, constraint or root cause. 1 is the code that does it without saying why.
- **Which or what.** 2 names the item or lists the items, with enough detail to confirm the condition. 1 names one instance of a wider list, or names the item without confirming the condition.

**Boundary cases:**
- **Right symbol, wrong behaviour.** The chunk holds the named function but not the edge case asked about. It's a 1 if it shows where the symbol lives, so the reader can look nearby. It's a 0 if it's only an import or a passing mention.
- **A neighbouring question.** The chunk answers a related question, such as how a thing is built when the query asks how it broke. That's a 0. Don't reward topical closeness.
- **Header only, or a table of contents.** The chunk proves a section exists elsewhere but holds none of it. That's a 0. For a "where is" query only, an index that gives the target's path is a 1.
- **Duplicates.** Grade each copy on its own text, and don't mark the second copy down. Deduplication is a design problem, not a grading one.
- **A split answer.** Half an answer that needs another chunk is a 1. If it holds the core and misses only trailing boilerplate, it's a 2.
- **A construct split across chunks.** When the logic asked about is in the chunk but the chunk's text and header don't say what it belongs to, it's a 1. It's a 2 only when the text or header identifies the enclosing function, class or section.
- **Implementation, test or doc.** For a mechanism query, the implementation, or an accurate detailed doc, is a 2, and a test or a short docstring is a 1. For a usage query ("how do I call X"), a working call, a test or a usage doc is a 2, and the internals are a 1.
- **Outdated text.** If the chunk itself marks itself as superseded, archived, deprecated or historical, it's a 0, unless the query asks for history. If it only looks current, grade what's in front of you, and flag it for corpus cleanup. A grader judges the text, not repository state the grader can't see.

## 2. What graders see

- **They see:** the query, its locked intent line (section 3), the chunk id, the chunk's header and its text.
- **They never see:** which arm found the chunk, how many arms found it, any score or rank, or another grader's grades or reasons.
- **Order:** shuffled per query with a recorded seed, so the order can be rebuilt if position bias is suspected.

## 3. Lock each query's intent first

- **Before any of a query's pool is opened, write one line saying what the query is asking.** Short keyword queries, taken from search logs, cause most disagreement, because each grader invents a different asker.
- For a keyword query, expand it into the single most plausible question for this corpus. Pick one reading, never an "or".
- **Freeze the intent table** (query id, query, intent) before grading starts. Every grader gets the same line.
- **The auditor reviews the intent table before grading starts,** so a whole query isn't graded against a misread intent.

## 4. The output

One JSON Lines row per query and chunk:

```json
{"query_id": "w012", "chunk_id": 4411, "reason": "Normalises curly quotes before the gates run.", "grade": 2}
```

- `grade` is 0, 1 or 2, nothing else.
- `reason` is at most 15 words, and says **what the chunk says about the target**, not just that the target appears. It's required for every grade from a model grader. A short reason on a 0 catches skimming and misread intents. It's optional for a human auditor's 0s.
- **Put `reason` before `grade` in the schema,** so a model states the evidence before it grades.

## 5. Graders, agreement and the audit

**Graders:**
- Model graders run as **a fresh agent per query.** No conversation carries one query's grades into the next.
- An agent reads a query's chunks **at most five at a time**, against the intent line and this rubric, never against the other chunks in the pool. That counters attention fading over a long prompt and grading by contrast.
- In this studio, model graders are agents on the Claude Code plan, never a paid per-token API.

**The audit:**
- At least 10% of queries, and at least 10. They're split evenly across query groups, and chosen for **a high share of chunks found by only one or two arms**, because that's where arms differ and edge cases cluster.
- The auditor is from a different model family from the graders. It grades every chunk in each sampled query's pool, blind.

**Agreement, computed on the audit sample before any arm metric:**

| Measure | What it guards | Gate |
|---|---|---|
| Quadratic weighted Cohen's κ over 0/1/2 | the whole scale, with a 0-versus-2 split costing four times a one-step split | ≥ 0.75 |
| Cohen's κ on 0 against {1, 2} | the line recall and MRR read | ≥ 0.80 |
| Raw disagreement | a sanity check. Pools are mostly zeros, so raw agreement flatters | ≤ 10% overall, and ≤ 2% two-step (0 against 2) |

**When it fails:**
- A pass freezes the graders' grades for the whole pool. Don't overwrite the sampled queries with the auditor's grades, or those queries would carry a different grader than the rest.
- On a fail, read the disagreements with their reasons and name the cause: an ambiguous intent, a missing boundary rule, or drift. Revise the rubric or the intents, log the revision, and regrade the whole pool from fresh orders.
- If binary κ passes and weighted κ fails on 1-versus-2 splits, tighten the query-form rules in section 1 and regrade only the chunks graded 1 or 2.

## 6. Freeze, drop and publish

- **Drop a query whose whole pool has nothing graded 1 or 2,** and report its id. Every arm scores 0 on it, and keeping it only squeezes differences toward zero.
- **Freeze the key before any arm metric is computed.** Sort it by query id and chunk id, hash it with sha256, and record the hash, the time, the rubric version and the grader setup in the experiment's record.
- **A grade changed after arm metrics have been seen voids the run.** A corrected table may be reported beside it as post-hoc, but the decision stays with the frozen key, or with a full blind regrade.
- **What's published:** query ids, chunk ids, grades, the hash and the metrics. Query text, intents, chunk text and reasons stay private when the corpus is private. Reasons quote it.

## 7. Pitfalls

| Pitfall | What happens | The check |
|---|---|---|
| Leniency drift | Over a long pool, graders grow generous or harsh. | A fresh agent per query, and the audit. |
| Anchoring | Chunk 2 looks good beside a weak chunk 1, or partial answers look worthless beside a perfect one. | Grade against the intent line and the rubric, never by comparison within the pool. |
| Word overlap | A chunk repeats the query's nouns without answering it. | The reason must say what the chunk says about the target. |
| Family preference | A grader may favour text that resembles its own training. | Graders from a different family from the arms, and an auditor from a third family. |
| Fatigue and lost-in-the-middle | Long prompts grade middle chunks worse. | At most five chunks at a time. |

## 8. Checklists

**Before anything is graded:**
- [ ] The corpus and queries are frozen and hashed.
- [ ] The pool is built per query, deduplicated, and stripped of arms, ranks and scores.
- [ ] Every query has a locked intent line, reviewed by the auditor.
- [ ] Orders are shuffled per query, with the seed recorded.
- [ ] The output schema puts `reason` before `grade`.
- [ ] The audit queries are chosen and set aside.

**While grading and after:**
- [ ] One fresh agent per query, at most five chunks at a time.
- [ ] Every row is checked: grade 0, 1 or 2, and a reason of at most 15 words.
- [ ] The auditor grades the sample blind.
- [ ] Agreement is computed before any arm metric. On a fail, revise and regrade.
- [ ] Zero-relevance queries are dropped and listed.
- [ ] The key is sorted, hashed and frozen. Private text is stripped before anything is published.
