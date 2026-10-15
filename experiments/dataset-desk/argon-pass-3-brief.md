# The dataset desk, pass 3: brief for Argon

**From:** R&D. **Date:** 2026-10-15.

**The files:** `E:\AI\Research and Development\experiments\dataset-desk\`.

**The rules are unchanged:**
- offline tests only;
- no run on real art or a real model;
- no downloads;
- no writes outside this folder.

End the pass with the output of `python -W error -m unittest test_desk` and `ruff check --select F,E9,B`, and a list of what you changed.

## Pass 2, checked by R&D: it holds

- **The tests and lint, reproduced:** 28 tests pass and ruff is clean.
- **Pass 1's gaps are fixed in the code, not just described:**
  - the thread caps run before numpy loads (import order checked);
  - the interop guard;
  - `failure_modes` loaded as a list;
  - rejection notes are never searchable;
  - the PNG prompt parser follows the sampler's positive and negative links;
  - the shared scan cache;
  - an approved record wins a byte-identical collision;
  - the peeking guard, with its test.
- **The `vision_tokens` wiring matches the installed source:**
  - `EmbeddingGemma2Processor(image_seq_length=…)`;
  - Gemma 4's image kwargs `max_soft_tokens` ∈ {70, 140, 280, 560, 1120};
  - sentence-transformers' `processor_kwargs`.

  Whether it changes the token count at run time shows only in the C0 smoke run.

## Settled since pass 2

These come from the multimodal design, revision 3: the desk's gate is that experiment's query gate, and it's the
same code.
- **One counted run on all four projects,** after the desk stage.
- **Re-descriptions go through the desk's pipeline:**
  - plain-sight (Florence-2) drafts each one blind, from the pixels alone;
  - a person edits the draft into search prose of 12–45 words. They rewrite it, not click it through.
- **Every description carries `author_kind`:** `human` (the existing tallow-fen and hesperia texts) or
  `captioner_assisted` (every re-description).
- **On `rustline`, `tallow-fen`, `salt-road` and `hesperia`, before that experiment's counted run, no model that
  measures one of its arms accepts or rejects a description.** EmbeddingGemma 2 is arm G, and ai-eyes is SigLIP2,
  which is arm S. The only acceptance tests there are the model-free gate and the person's edit.
- **The benchmark's query is the edited search prose,** stored by style-dataset-lab as the record's
  `judgment.explanation`. LoRA training captions (the trigger plus content, with canon style words stripped) are a
  separate product, and the desk never writes them into review or import files.

## What to change

### 1. The gate becomes revision 3's acceptance tests

Replace the gate's current rules (a word-set Jaccard of 0.80, and an all-word share of 0.90 only), and drop pass 2's
short-prompt exemption: one rule set, with no extra degrees of freedom.

**A description fails if:**
- **it echoes its prompt:**
  - it equals the record's generation prompt, or sits inside it;
  - it shares a contiguous run of 6 or more words with the prompt;
  - 90% or more of its words appear in the prompt;
  - 80% or more of its content words appear in the prompt;
- **it wraps `canon.subject`:** the words of the record's `canon.subject`, when there are 4 or more, appear as a
  contiguous slice of the description's words;
- **it's too short:** fewer than 8 words, or fewer than 5 content words;
- **it duplicates another description in the pool:** for any pair across the whole pool,
  `"".join(words(a)) == "".join(words(b))`, or a Jaccard of 0.85 or more between the two content-word sets;
- **it's too long for SigLIP2:** more than 64 tokens, counted as `len(tokenizer(s.lower(), padding=False,
  truncation=False)["input_ids"])` on the cached `siglip2-so400m-patch14-384` tokenizer, special tokens included. The
  processor's defaults pad and truncate to 64, so a count through them could never fail.

**Pinned arithmetic:**
- **Words** are `re.findall(r"\w+", s.lower())`.
- **A content word** is a word not in the stopword list. Commit the list as its own file in this folder, and have
  the gate expose its sha256.
- **A share** is the number of the description's words (counting repeats) that occur anywhere in the prompt, over
  the description's word count; the same for content words.
- **Contiguous runs, and the `canon.subject` slice,** are matched on these word sequences.
- **The Jaccard** is over content-word sets, for every pair across the whole pool.

**The token count is the one test that needs a library** (SigLIP2's tokenizer).
- Keep the gate's core in the standard library.
- Put the token count in a separate function that imports the tokenizer lazily.
- A record whose count wasn't computed is "unchecked", and can't be marked as passing.

**Tests:**
- each test at its boundary, one just passing and one just failing;
- the stopword-file hash;
- salt-road's ruling repeated 54 times, and a description that sits inside its prompt;
- the optional real-records test: it must still flag salt-road and rustline today.

### 2. The worksheet must not show the prompt by another route

The "current text" column today shows `canon.subject` when there is one. On salt-road that's the prompt's own subject
clause (it sits inside the prompt for 69 of 73 images), and rustline's texts are prompt-like. So a re-describer would
read the prompt.

**For every flagged record, the worksheet shows:**
- the id;
- the target image;
- 3 to 5 sibling images, chosen model-free: from the same project folder, nearest by dHash;
- the instruction: "describe this picture in 15–35 words so a person could pick it out from the siblings shown";
- a column for the Florence-2 draft;
- a column for the edited text.

**It doesn't show:** the current text, `canon.subject`, or the prompt. `description-review.jsonl` may keep them,
for the importer. It isn't shown to the writer.

### 3. The drafting stage, with a fake drafter in the tests

- Add the step that asks plain-sight for a draft of each flagged record. Give it the image path only: never the
  prompt, `canon.subject` or the current text.
- Record each draft with `author_kind: captioner_assisted`, the drafter's id and its pinned revision.
- Test it with a fake drafter. Running Florence-2 for real is a later run, under the rig's preflight.

### 4. A guard for anything that would measure an arm

- Put any acceptance step that uses EG2 embeddings or ai-eyes (SigLIP2, e.g. `image_contains`) behind one guard
  function.
- That function refuses on the four projects unless `--allow-multimodal-pool` is passed (after the counted run).
  Reuse `check_multimodal_pool`, or extend it.
- No ai-eyes step exists yet, so add the guard now, with a test that a stub ai-eyes step is refused on `salt-road`.
  Whenever the step is built, it's guarded already.

### 5. `author_kind` in the outputs

- `description-review.jsonl` and the worksheet carry `author_kind` per record: `human` for an existing text that
  passes, and `captioner_assisted` for a drafted one.
- The importer contract (in `design.md`) says style-dataset-lab writes it into the record's provenance with the
  approved text.

## Not in this pass

- Moving the code to `mcp-tool-shop-org/dataset-desk` (the Director's call, after this pass).
- The lite ONNX backend (it needs a model download, which needs the Director's go).
- Any real model run, C0 included.
- The `sdlab descriptions import` command, which lives in style-dataset-lab.

## When you're done

- The tests and ruff, as above.
- `design.md`:
  - the gate section lists the acceptance tests and the pinned arithmetic exactly as above;
  - the worksheet and drafting stages are described;
  - the arm-model guard is stated.
