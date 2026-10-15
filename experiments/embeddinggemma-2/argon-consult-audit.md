# CONSULT | Argon | EmbeddingGemma 2 text benchmark: the grading audit and one scoring rule | from R&D | 2026-10-15

**Status:** all 100 queries are graded. That is 2,470 pooled chunks, one fresh Sonnet grader per query, every file complete and checked. The merged key is frozen at sha256 `c4c35891…`. No score has been computed. The arms' rankings stay sealed until this consult is answered.

**How this works:** the Director pastes Part A with the four private audit packets. **Grade Part A before you read Part B,** so the questions can't steer your grades.

## Part A: the blind audit (amendment 2)

- Four packets cover 16 queries and every chunk in each one's pool. The queries were chosen by the share of pooled chunks that two or fewer decision runs returned in their top 10.
- Grade each chunk 0, 1 or 2 against the query's locked intent, using the relevance-grading template on the rnd site (`handbook/relevance-grading`).
- Reply in JSON Lines, one row per chunk, in packet order: `{"query_id", "chunk_id", "reason" (at most 15 words), "grade"}`.
- You see no Sonnet grade.

R&D then runs `grading.py agree`. The bars are fixed in advance:

| Measure | Bar |
|---|---|
| Quadratic weighted κ | ≥ 0.75 |
| Binary κ (relevant or not) | ≥ 0.80 |
| Raw disagreement | ≤ 10% |
| Two-step disagreement (0 against 2) | ≤ 2% |

A miss stops the scoring. The disagreements then go back to you query by query, before anything is regraded.

## Part B: read after Part A

### Question 1: queries with no relevant chunk (a scoring rule, settled before any score)

- **The cases:** four of the 100 queries have no chunk graded above 0. One is a logged one-word search; three were written from commit and PR text with the corpus closed, as the design required.
- **What R&D checked:** a term search over all 11,525 chunks, not only the pools, found no answer to any of the four.
  - Two ask about events that no file in the corpus's sources records.
  - One asks about a design document. It lives in offrig's `docs/`, which the corpus excludes by design (offrig contributes `crates/*/src` only).
  - The logged one-word search names a term that appears nowhere in the corpus.
  - So these are queries the corpus can't answer, not pool misses. A term search is not a full read, and that limit is stated here.
- **The problem:** `ndcg_at` returns 0.0 when no chunk is relevant. Each such query then adds a 0 to every paired difference and pulls the mean toward 0. That works against adoption without measuring anything.
- **R&D proposes:** drop queries with no relevant chunk from every mean, bootstrap and group floor. Report their count and ids, and report stage 1 on what remains (96 if the count holds at 4). This is TREC's usual handling.
- **Asked of you:**
  1. Agree, or rule otherwise.
  2. Do the stage 1 thresholds (+0.03 mean, group floors of −0.015) stand at 96 queries, or does the smaller set change the bootstrap's power enough to matter?

### Question 2: gaps in the template the graders reported (for its next version, not this run)

The brief's scale and rules stayed exactly as committed before grading, so every query was judged under one rule set. Its procedure lines (counting the packet, the reading cadence, an output check) were tightened during wave 1, after 8 grade files were written. Graders flagged these recurring gray areas and handled them inconsistently:

1. Code in another repo or subsystem that does the same thing as the query's target. Mostly graded 0, sometimes 1.
2. A helper, call site or orchestrator around the answer. Graded 1 under the split-answer rule, which doesn't name this case.
3. A chunk that fully answers one branch of an "A or B" query.
4. An answer split across adjacent chunks, the mechanism in one and its constants in the next. Graded 2 and 2, or 2 and 1, inconsistently.
5. Prompt text or policy that states the rule. Graded 0, 1 or 2 depending on the query.
6. An analogue explicitly modelled on the queried thing.
7. Tests whose comments narrate the behaviour. These were applied consistently at 1.
8. A document or tool description that states the whole rule but isn't the implementation. Graded 2 in some queries and 1 in others. This is the likeliest source of audit disagreement.

Also seen:
- **Queries whose premise is false** for the code (one case).
- **Rule without reason:** "why" queries where the pool holds the rule but never the reason.

**Asked of you:**
- Which of these does your Part A grading resolve one way or the other?
- Which deserve a line in the template's next version?

R&D drafts that version only after the audit, so it can't touch this run.

### Something R&D noticed, for the write-up (no ruling needed)

offrig's chunker titled two chunks with the previous definition's name. A doc comment that precedes a function was cut off from it, and the chunk took the earlier item's title. Both arms embed the same text, title included, so the comparison is unaffected. It misleads anyone reading a hit, and goes to offrig as an issue.
