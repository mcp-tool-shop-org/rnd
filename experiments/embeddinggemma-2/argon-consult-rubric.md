# Argon consult: draft the relevance-grading rubric, as a reusable handbook template

**For Argon, from R&D, at the Director's request. 2026-10-15.** The Director wants the grading rubric for the EmbeddingGemma 2 benchmark written as a template, one that this studio and others can reuse for any pooled relevance judgement: embedder, reranker or search changes. He asked for you to draft it first. R&D will turn your draft into a handbook page, apply it to this benchmark, and record what was changed and why. You have no repository access, so everything you need is below.

## What the template is for

Grading is how a retrieval experiment gets its answer key. Each query's candidate passages are pooled from every arm's top results, shuffled, and stripped of which arm found them. Then each passage is graded for how well it answers the query. Scores like nDCG, recall and MRR are computed only after the grades are frozen. The template has to make those grades **consistent between graders, blind to the arms, and auditable**, so that a ranking difference is a model difference and not a grader difference.

## How this benchmark will use it (the first application)

- **The pool:** 100 queries (50 about code, 50 about prose) over 11,525 chunks of studio documents and source code. A chunk is at most about 2,200 characters, and starts with a header line `[source · kind · title]`. Each query's pool is the deduplicated union of the top 10 from every run: two embedders, a 256-dimension cut, dense and hybrid readings, and a code-prefix diagnostic. That's expected to come to roughly 15–20 chunks per query, 1,500–2,000 in total.
- **The scale is 0, 1 or 2,** fixed by the approved design. nDCG uses gain `2^g − 1`, so a 2 is worth three times a 1. Recall@5 and MRR count any chunk graded 1 or more as relevant. The line between 1 and 2 therefore moves nDCG, and the line between 0 and 1 moves recall and MRR.
- **The graders:** Sonnet agents grade the full pool under the rubric, and R&D spot-checks them.
- **The audit is you:** a stratified sample of 10 queries (5 prose, 5 code), with every pooled chunk graded blind, about 180 chunks pasted in two packets. If you and the graders disagree on more than about 10% of that sample, the whole pool is regraded.
- **Privacy:** most chunks come from a private knowledge base. Graders see chunk text, and nothing graded is published except ids and numbers.
- **One rule already decided:** a query whose pool has nothing graded 1 or 2 is dropped from the analysis and reported, because every arm scores 0 on it.

## What the template must contain

Write it the way the studio's other design templates read (A/B experiments, dataset builds, diagnose-then-fix):
- numbered sections;
- plain, short sentences;
- rules stated as checks a reader can apply;
- a "before anything is graded" checklist;
- a "while grading and after" section.

It must cover at least:

1. **The scale, with operational definitions and boundary cases for each step.**
   - What makes a chunk a 2 (it answers the query) versus a 1 (on topic, or a partial or indirect answer) versus a 0.
   - Worked boundary cases: a chunk that names the right function but not the behaviour asked about; a chunk that answers a neighbouring question; a chunk that is only the header or a table of contents; duplicate or near-duplicate chunks; a chunk that answers only in combination with another; code that implements the behaviour versus a test or a doc that describes it; an outdated passage that answered it once.
   - How the query's form (where, how, why, which) changes what counts as answering.
2. **What graders see, and what they must not see.**
   - The query, the chunk text and its header. Nothing about which arm found it, its rank, or how many arms found it. Never the other graders' grades.
   - The order is shuffled per query.
   - What to do about keyword-only queries (two or three words, from search logs), whose intent has to be inferred.
3. **How to read a query's intent once, before grading its pool,** so all of its chunks are judged against the same reading. Record that reading in one line.
4. **The output format:** one row per chunk, with query id, chunk id, grade, and a reason of at most 15 words for every 1 and 2. Also say whether a reason for a 0 is useful.
5. **Agreement and audit.**
   - How the audit sample is drawn (stratified by group, and by how many arms found a chunk).
   - The agreement statistic and its threshold. Is raw percent agreement enough at three levels, or should it be weighted kappa? Give the number.
   - Is a 1-versus-2 disagreement treated differently from 0-versus-something?
   - What triggers a regrade, and how disagreements on the sample are adjudicated.
6. **Freezing and reporting:** when the key file is frozen, its hash, and what is published (ids and grades, never private text). How a grade changed after freezing voids the run.
7. **Pitfalls to name:** leniency drift over a long pool, anchoring on the first chunk, rewarding keyword overlap instead of meaning, the grader's own model family having been trained on similar data, and fatigue.

## What to reply with

1. **The template text in full,** ready to become a handbook page: Markdown with a title line and numbered sections.
2. **A filled example:** the boundary cases in item 1 above, each with its grade, worked against one invented code query and one invented prose query.
3. **Anything in this benchmark's setup** (the pool, the scale, the audit size, the threshold) that you'd change, and why.
