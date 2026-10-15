# Grader brief, version 2: one query's pool, EmbeddingGemma 2 benchmark

Version 2 is the round 2 regrade. Version 1 (`grader-brief.md`) stays as the record of round 1. This version adds the boundary rules from the round 1 audit's adjudication (`argon-consult-audit-round2.md`). Where a boundary rule and the scale below differ, the boundary rule wins.

You are grading retrieval results for one query, under the studio's relevance-grading rubric. You are one fresh grader for one query. Grade every chunk on its own text, against the query's locked intent. Never compare chunks with each other, and never guess which search system found a chunk: you aren't told, and it mustn't matter.

## Your input

`E:/AI/eg2-bench/grading/<QID>.jsonl` is private. Each line is one chunk:
- `qid`, `group` (code or prose), `query`;
- `intent`, the locked one-line reading of the query, which is what you grade against;
- `note`, a grading note, sometimes empty;
- `n`, `chunk_id`;
- `text`, the chunk itself. Its first line is a header `[path · kind · title]`. The title can name the definition *before* the chunk's text rather than the one in it, so judge by the text.

**First count the packet's lines:** `grep -c . E:/AI/eg2-bench/grading/<QID>.jsonl` (Bash). Call that N. Every one of the N chunks gets a grade.

**Then read it five lines at a time** with Read, `limit: 5` and `offset` 1, 6, 11, 16 … (offset is the 1-based line number to start from). Grade those five, then read the next five, until you have read line N. Don't read the whole file at once.

## The scale

- **2, answers it.** The chunk holds the complete answer to the intent, or the exact code it asks about. A reader could stop here.
- **1, helps.** On topic and part of the answer: a strong pointer, or half of an answer that needs another chunk.
- **0, doesn't help.** Shares words, sits in the same file, or answers a neighbouring question, but gives nothing toward the intent.

**The query's form decides what answering means:**
- **"Where":** the definition or implementation is 2. A reference that shows its location is 1.
- **"How":** the implementation body is 2. A summary or test that doesn't show the mechanism is 1. On a code query, see R2 for docs.
- **"Why":** see R6.
- **"Which" or "what":** naming the item, with enough to confirm it, is 2. One instance of a wider list, or a name without confirmation, is 1.

## Boundary rules

- **R1. Same pattern, wrong target: 0.** Code or prose in another repository, crate, module or role that solves an analogous problem is 0. So is a later artifact explicitly modelled on the target. The exception is a query that asks for that pattern across repositories.
- **R2. Prose docs, tool descriptions and tests on a code query: at most 1.**
  - On a query whose `group` is code, only the implementation earns 2, together with the comments and docstrings inside that implementation.
  - External prose (research entries, instrument notes, READMEs), CLI or MCP tool descriptions, and unit tests earn 1 when they state or demonstrate the queried mechanism.
  - They earn 0 when they report only counts, metrics or motivation without saying how the mechanism works.
- **R3. An implementation split across chunks: 2 on each load-bearing half.**
  - When one mechanism is split across two chunks of the implementation, each half a reader needs earns 2. That covers two halves of one function, or a rule, regex or constant table and the function that applies it.
  - A comment in another module that describes or points to the behaviour earns 1.
  - So does a caller that performs one step of a multi-step mechanism.
  - A generic helper the mechanism happens to use earns 1 at most.
- **R4. A prompt string that instructs a model is 0** when the query asks how code checks, parses or enforces something.
- **R5. Bare call sites, cut-off chunks, imports and other pipeline stages: 0.** That covers:
  - a chunk that only calls the target without showing its logic;
  - a chunk that stops at a signature, module header or section comment before the relevant code begins;
  - one that defines unrelated types or helpers in the same file;
  - one that implements an earlier or later stage of the pipeline.
- **R6. "Why" queries.**
  - A chunk stating the reason earns 2.
  - One stating the full rule or contrast without the reason earns 1.
  - One that only names or links the artifact, applies it elsewhere, or states a gate or limit without explaining it earns 0.
- **R7. Bibliographies and source lists: 0.** A source entry whose inline summary states a relevant finding earns 1.
- **R8. Queries pinned to a specific round, review or event.**
  - A chunk that attributes the change to that round and states the change earns 2.
  - A raw proposal before its disposition, or the resulting design without naming the round, earns 1.
  - A chunk about a different round, or a later artifact that only uses the result, earns 0.
- **R9. Incident queries ("what went wrong in run X").**
  - A chunk that narrates the incident earns 2.
  - Code, constants or tests written to handle that class of fault earn 0, unless their comments recount the incident.
- **R10. "What the studio found" research queries.**
  - The studio's own measurements earn 2, and so does its synthesis of the literature when it answers the research question.
  - A downstream table that applies those findings to something else earns 1.
- **R11. Two-part queries.** A chunk that completely answers one named half of an "A and B" or "A or B" query earns 1, unless the `note` says otherwise.
- **R12. A query whose premise doesn't match the code:** grade against the mechanism the intent targets, as the code actually has it. Don't grade the real implementation 0 because the query described it slightly wrongly.

**Unchanged from version 1:**
- A header-only chunk or a table of contents is 0. For a "where" query only, an index giving the path is 1.
- Duplicates: grade each one on its own text.
- Text that marks itself as superseded, archived or historical is 0, unless the query asks for history.
- **Keyword queries** (two or three words) are graded against the intent line, not against the bare words.
- If the `note` field says how to grade a partial answer, follow it. It overrides R11.

## Your output

Write `E:/AI/eg2-bench/grades-r2/<QID>.jsonl` **with the Write tool, not a shell heredoc**. One line per chunk, every chunk in the file, with `reason` before `grade`:

```json
{"query_id": "<QID>", "chunk_id": 99999, "reason": "Shows the RRF fusion of BM25 and cosine top 50.", "grade": 2}
```

`reason` is 3 to 15 words. **Count them:** 16 words is refused at the merge. It says **what the chunk says about the target**, not just that a word appears. Give a reason for 0s too ("about pod pricing, not the watchdog"). When a boundary rule decides the grade, start the reason with its number, such as "R5: signature only, cut off before the check."

**Before you reply, check your output:** `grep -c . E:/AI/eg2-bench/grades-r2/<QID>.jsonl` must equal N. If it's short, find the missing chunk ids, grade them, and check again. A pool where every chunk is 0 is a valid result: grade them all.

## Rules

- Open only your own packet. Don't open other packets, the pool, any grades (round 1's included), the audit files, or any repository.
- Write only your output file.
- Then reply with:
  - the counts of 0, 1 and 2;
  - any chunk you were unsure about, with its id and one line on why;
  - a short debrief: anything slow or confusing in this brief.
