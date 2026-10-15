# Grader brief: one query's pool, EmbeddingGemma 2 benchmark

You are grading retrieval results for one query, under the studio's relevance-grading rubric. You are one fresh grader for one query. Grade every chunk on its own text, against the query's locked intent. Never compare chunks with each other, and never guess which search system found a chunk: you aren't told, and it mustn't matter.

## Your input

`E:/AI/eg2-bench/grading/<QID>.jsonl` is private. Each line is one chunk:
- `qid`, `group` (code or prose), `query`;
- `intent`, the locked one-line reading of the query, which is what you grade against;
- `note`, a grading note, sometimes empty;
- `n`, `chunk_id`;
- `text`, the chunk itself. Its first line is a header `[path · kind · title]`.

**Read the file at most five lines at a time** (Read with `offset` and `limit: 5`). Grade those five, then read the next five. Don't read the whole file at once.

## The scale

- **2, answers it.** The chunk holds the complete answer to the intent, or the exact code it asks about. A reader could stop here.
- **1, helps.** On topic and part of the answer: a strong pointer, a test or a caller, or half of an answer that needs another chunk. Or the right function without the specific behaviour asked about, when the chunk shows where that function lives.
- **0, doesn't help.** Shares words, sits in the same file, or answers a neighbouring question, but gives nothing toward the intent.

**The query's form decides what answering means:**
- **"Where":** the definition or implementation is 2, and a call or reference that shows its location is 1.
- **"How":** the implementation body, or a doc that explains the control flow, is 2. A signature, summary or test that doesn't show the mechanism is 1.
- **"Why":** a note, decision record, commit text or comment that explains the reason is 2. The code alone, without the reason, is 1.
- **"Which" or "what":** naming the item, with enough to confirm it, is 2. One instance of a wider list, or a name without confirmation, is 1.

**Boundary rules:**
- A header-only chunk or a table of contents is 0. For a "where" query only, an index giving the path is 1.
- Duplicates: grade each one on its own text.
- A split answer, half an answer that needs another chunk, is 1.
- **Split code:** if the logic asked about is in the chunk, but neither the chunk's text nor its header says which function, class or section it belongs to, it's 1. It's 2 only when the enclosing construct is identified.
- Text that marks itself as superseded, archived or historical is 0, unless the query asks for history.
- **Keyword queries** (two or three words) are graded against the intent line, not against the bare words.
- If the `note` field says how to grade a partial answer, follow it.

## Your output

Write `E:/AI/eg2-bench/grades/<QID>.jsonl`, one line per chunk, every chunk in the file, with `reason` before `grade`:

```json
{"query_id": "<QID>", "chunk_id": 1234, "reason": "Shows the RRF fusion of BM25 and cosine top 50.", "grade": 2}
```

`reason` is 3 to 15 words. It says **what the chunk says about the target**, not just that a word appears. Give a reason for 0s too ("about pod pricing, not the watchdog").

## Rules

- Open only your own packet. Don't open other packets, the pool, the grades of other queries, or any repository.
- Write only your output file.
- Then reply with:
  - the counts of 0, 1 and 2;
  - any chunk you were unsure about, with its id and one line on why;
  - a short debrief: anything slow or confusing in this brief.
