# The dataset desk, pass 2 addendum: the description audit

**From:** R&D. **Date:** 2026-10-15. If pass 2's brief hasn't gone in yet, this goes in with it. If it has, this is the
next instruction. The pass's rules are unchanged: offline tests only, no runs on real art or a real model, no
downloads.

## Why

Your pass 1 found that salt-road's descriptions are mostly one ruling sentence, and that rustline's are shared and
prompt-like. R&D then found that salt-road's `canon.subject` sits inside its generation prompt for 69 of 73 images.

The Director's direction is that the desk fixes this in the data; finding and fixing descriptions is one of the
reasons for EmbeddingGemma 2. The multimodal experiment (revision 3, `experiments/embeddinggemma-2/design-multimodal.md`
§2a) will run only on desk-checked pools. Its harness imports the desk's model-free checks as its query gate.

## What to build

1. **A model-free description gate,** in its own module (for example `description_gate.py`). Use the stdlib only, so
   it runs in the lite tier and the multimodal harness can import it. For each approved record it reports:
   - **Duplicates:** exact duplicates after lower-casing and trimming, and near-duplicates within a project (a
     word-set Jaccard of 0.8 or more is a starting value; say if you'd use another). The ruling repeated 54 times
     must come out as one group.
   - **Prompt echo:** the description equals its record's prompt, sits inside it, or has 90% or more of its words in
     it. Report the share for every record.
   - **Source:** where the text came from (`judgment.explanation`, `canon.subject`, or none).
   - **Status:** not approved, or not the record's current description.
2. **An embedding view, for display only:**
   - near-duplicate descriptions by EG2 text embeddings, with the clustering prefix, beside the model-free groups;
   - each description's image fit: the mid-rank of its own image among the project's images.
   Neither may gate. On `rustline`, `tallow-fen`, `salt-road` and `hesperia`, both are refused until the multimodal
   experiment's counted run, as in pass 2 item 2. Two reasons:
   - peeking at that experiment;
   - selection on the outcome: EG2 is one of that experiment's arms, so its flags must not choose which descriptions
     are rewritten.
3. **A review queue, not edits.**
   - **The files:** `description-review.jsonl` and a report section listing every flagged record: id, image link,
     source, flags and reasons, and the current text.
   - **The worksheet:** a re-description sheet in Markdown, with the image link, the current text and a blank column
     for the new description. **Don't show the generation prompt in it:** re-descriptions are written from the image
     alone.
   - **The project stays untouched.** Approved re-descriptions are applied by style-dataset-lab's own tools, with a
     provenance note.
4. **Tests:**
   - offline fixtures that mimic both shapes: one ruling string on most records, and a description that sits inside
     its prompt;
   - the gate must flag both;
   - an optional test that reads the real salt-road and rustline records when `E:\AI\style-dataset-lab` exists, and is
     skipped otherwise. It must flag both projects' current sets.

## Answer in design.md

- Should the Jaccard near-duplicate threshold be a fixed value, or calibrated per project?
- Is the gate's prompt-echo rule (equal, inside, or a word share of 0.9 or more) right for re-descriptions too?
- Where should the review queue live, so style-dataset-lab can apply approved re-descriptions: desk output, or an
  sdlab inbox?
