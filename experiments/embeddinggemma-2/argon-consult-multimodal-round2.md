# CONSULT | Argon | EmbeddingGemma 2 across modalities: round 2, the revised design | from R&D | 2026-10-15

**Status:** R&D took your five changes. Two of them met facts on the rig that change their form, and two facts in R&D's round 1 were wrong. All the counts below are R&D's measurements on 2026-10-15.

## The two corrected facts

1. **The pool is smaller than R&D said.** The four query projects hold 2,104 image files, not about 2,900. 1,451 of them are generation outputs in `outputs/<folder>/`. 1,246 remain once byte-identical copies are merged.
2. **No record names a lineage.** `iteration` is null in all 385 query records. The only `lineage` objects are on 60 star-freight records, with null fields. Ids don't help either: one id stem covers 54 different salt-road images from a single wave.

## How R&D ruled on your changes

1. **Pool: amended.**
   - **Recorded images only would leave 369 distractors.** rustline would have none except its own other queries: all 172 of its records on disk are queries.
   - **Your concern held, though.** Unrecorded files do hold copies of targets. 172 targets, all of rustline's, have a byte-identical copy in a wave folder, and the top of `outputs/` holds contact sheets.
   - **So the pool is generation outputs only.** It's every file in an `outputs/` subfolder, with byte-identical copies merged (the recorded copy is kept) and pinned by a sha256 manifest, since the images aren't in git.
   - **Near-duplicates of each target are masked:** dHash Hamming distance ≤ 10 of 256, which hits 10 targets.
   - **Left out:** top-level composites, `training/`, `exports/`, `inbox/` and `inputs/`.
   - **The result:** 385 targets and 861 distractors.
2. **Filtered key: not possible as written.** There's no lineage to filter by, so the strict key stays primary. A different generation of the same subject remains a distractor. That noise falls on both arms equally. Masked and unmasked MRR, recall@k and an approved-only pool are reported.
3. **T2 prefix: accepted, and locked to the document prefix.** No comparison run, because that would be a forking path.
4. **Token counts on all 385, with fixed padding at 64: accepted.**
5. **Per-project rule: your upper-bound form.** A project vetoes only when its one-sided 95% upper bound on (G − S) is below 0.
6. **G256 is out of the rule.** 768 matches the text decision, and 512 and 256 are a descriptive curve.

Your power note goes to the Director as you wrote it: +0.05 is a bar on the sample mean, and 80% power needs a true gain of about +0.063.

## Asked of you

1. **The pool.** Is "generation outputs, byte-deduplicated, near-duplicates masked" sound, or does something in it still tilt the strict key?
2. **The near-duplicate threshold.** Is dHash ≤ 10 of 256 the right kind of mask, or would you set it differently? It's frozen in the manifest before any run.
3. **No lineage.** Do you accept the strict key with same-subject siblings left in as distractors? Or is there a neutral sibling rule that needs no record data and no learned model?
4. **Verdict:** "approve as written", or the exact changes. If you change anything, R&D revises and sends it back before the harness is written.

## The design, revision 2 (rnd `experiments/embeddinggemma-2/design-multimodal.md`)

# EmbeddingGemma 2 across modalities: finding the studio's art from a description

**Status:** draft design, revision 2, 2026-10-15.
- This is the second EmbeddingGemma 2 experiment. The first (`design.md`) tests text and code retrieval, and adopted EmbeddingGemma 2 at 768 dimensions (`results.md`). This one tests what makes the model distinct: text, images and audio in one vector space. The Director asked that the work not stop at text.
- Template: [A/B experiments](https://mcp-tool-shop-org.github.io/rnd/handbook/ab-experiments/).
- Revision 2 takes Argon's round 1 review (`argon-consult-multimodal-round1-disposition.md`) and corrects two facts revision 1 got wrong. It said about 2,900 images were on disk, and that records name a lineage.
- Nothing is counted until Argon approves this revision and the Director approves the design.

## 1. The check in three sentences

1. **The question:** can the studio find its own art from a plain description of it, and from a picture of it? Does EmbeddingGemma 2 do that better than SigLIP2, the image-text model the studio already runs in ai-eyes?
2. **What each arm gets:**
   - **Arm S:** SigLIP2 (`google/siglip2-so400m-patch14-384`, already cached), its text tower for descriptions and its image tower for images.
   - **Arm G:** EmbeddingGemma 2 loaded with text and vision (440M, audio left out), at 768 dimensions. Images carry no prefix, as the card says.
   - Same images, same descriptions, cosine ranking, on the CPU.
3. **Why the difference answers it:** only the embedder changes, and the key comes by construction (each description belongs to one image). So a gap in how often the right image comes first is the gap the studio would get in an art index.

## 2. The material, and keys by construction

Measured on 2026-10-15 in style-dataset-lab (working tree at `80f3cb6`).

- **The queries:** 385 approved images whose record holds a human-written review description (`judgment.explanation`, median 19 words, at most 53).

  | Project | Queries |
  |---|---|
  | rustline | 172 |
  | tallow-fen | 99 |
  | salt-road | 73 |
  | hesperia | 41 |

  The generation prompt is never a query. The image was made from it, so it would test recall of the prompt, not understanding of the picture.
- **The pool:** every image file under `projects/<project>/outputs/<folder>/` in those four projects, de-duplicated by content.
  - That's 1,451 files, 1,246 after de-duplication: the 385 targets plus 861 distractors.
  - The distractors are 496 unrecorded generation outputs (earlier waves and variants), 202 rejected, 104 unreviewed and 59 borderline.
  - **Byte-identical copies are merged before ranking.** 172 targets, all of rustline's, have a byte-identical copy in a wave folder. Ranking both would turn the strict key into a coin-flip tie between identical vectors. The recorded copy is kept, and no merged group holds two targets.
  - **Left out:** files at the top of `outputs/`, which are contact sheets and composites that contain targets; `training/` and `exports/`, which are copies and crops; and `inbox/` and `inputs/`, which are references.
  - **Pinned:** the images aren't in git, so the pool is pinned by a manifest of every file's sha256, frozen before any run.
- **The key:** a description's relevant image is the one it describes. No grading pass is needed.
- **Near-duplicates are masked.** A pool image within a dHash Hamming distance of 10 (of 256 bits) of the target is left out of that query's ranking. That's a non-learned image hash, neutral to both arms.
  - 10 targets have one to three such images.
  - The masked pairs are listed in the frozen manifest.
- **No lineage key.** No record among the 385 names a lineage: `iteration` is null in every record, and the 60 records with a `lineage` object are star-freight's, with null fields. Record ids don't give a reliable proxy either: one id stem covers 54 different salt-road images from a single wave. So a different generation of the same subject stays in the pool as a distractor. That adds noise equally to both arms and can't favour either.

## 3. The tasks

- **T1, description to image** (the primary): rank the pool for each description.
- **T2, image to description:** rank all 385 descriptions for each target image.
- **T3, audio:** **not run in this experiment.** What a real audio test would need is recorded in the disposition, for when ai-jam-sessions or vocology build a labelled clip library.

Revision 1's image-to-image task needed lineage, and is dropped.

**Prefixes for arm G:**
- In T1 the description is the query: `task: search result | query: {description}`.
- In T2 the descriptions are the documents: `title: none | text: {description}`.
- Images take no prefix in either task.

## 4. Measures and the decision rule

- **Primary measure:** T1's mean reciprocal rank on the strict key, with near-duplicates masked. Paired by query, with a 10,000-resample bootstrap.
- **Secondary measures:**
  - recall@1, @5 and @10;
  - T2's MRR;
  - T1 with no near-duplicate masking;
  - T1 with only the 385 approved images as the pool (a canon lookup);
  - each by project;
  - CPU throughput for images and text;
  - G cut to 512 and 256 dimensions, as a descriptive curve only.
- **Size:** 385 paired queries. Take σΔ, the per-query SD of the paired MRR difference, as about 0.30.
  - The SE is 0.015, and the one-sided 95% margin is 0.025.
  - So the +0.05 bar below is the binding test: any result that clears it also clears a lower bound above 0.
  - It's a bar on the sample mean, not a test against +0.05. A true gain of +0.05 clears it half the time. Clearing it with 80% power needs a true gain of about +0.063.
- **The rule, written before any run:**
  - **G is the studio's art-search embedder, at 768 dimensions,** when all of these hold:
    - T1's MRR (G − S) is at least +0.05;
    - its one-sided 95% bootstrap lower bound is above 0;
    - no project's one-sided 95% upper bound on (G − S) is below 0, meaning no project is significantly worse.
  - **Otherwise S stays.** The result is recorded either way.
  - Dimensions aren't part of the rule. Text adopted 768, so images match it and one index can hold both.
- **What adoption means:** an art index in style-dataset-lab (or ai-eyes) built on G. The design of that index is a separate change.

## 5. Fairness and fit

- **Each model's own runtime and preprocessing.** Images go through each model's own processor at its native resolution. Both arms run on the CPU in float32 (G's dtype gate from the text experiment applies). They're timed one at a time.
- **SigLIP2's text side** uses the fixed padding it was trained with: `padding="max_length", max_length=64`. Lowercasing is whatever its processor does by default, recorded.
- **Text length:** all 385 descriptions are token-counted with SigLIP2's tokenizer before any run, and the run stops if any is cut. That reads lengths only, so it leaks nothing.
- **Leakage:** none. Neither arm sees records, prompts or paths.

## 6. Before the first counted run

1. The pool manifest (sha256 per file, de-duplication groups and masked near-duplicate pairs) is frozen and committed. It holds ids and hashes only, no images.
2. A harness (`harness/multimodal.py`), reviewed by an outside model with its code inline.
3. A free validation run on 20 images and 20 descriptions, which records:
   - SigLIP2's token counts for all 385 descriptions;
   - G's parameter count with vision loaded (about 440M) and without audio;
   - unit norms;
   - one manipulation record per arm, for each task's prefix.
4. The Director approves this design.

## 7. After

- **Results go in this folder:** per-query ranks, intervals by project, throughput.
- **The article** covers both experiments, text and multimodal, after a short hands-on look:
  - a few real searches across the art;
  - one image-to-canon lookup;
  - a note on what an audio test would need.
