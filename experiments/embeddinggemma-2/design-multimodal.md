# EmbeddingGemma 2 across modalities: finding the studio's art from a description

**Status:** draft design, 2026-10-15. This is the second EmbeddingGemma 2 experiment. The first (`design.md`) tests text and code retrieval. This one tests what makes the model distinct: text, images and audio in one vector space. The Director asked that the work not stop at text. Template: [A/B experiments](https://mcp-tool-shop-org.github.io/rnd/handbook/ab-experiments/). Nothing is counted until an outside review and the Director's approval.

## 1. The check in three sentences

1. **The question:** can the studio find its own art from a plain description of it, and from a picture of it? Does EmbeddingGemma 2 do that better than SigLIP2, the image-text model the studio already runs in ai-eyes?
2. **What each arm gets:**
   - **Arm S:** SigLIP2 (`google/siglip2-so400m-patch14-384`, already cached), its text tower for descriptions and its image tower for images.
   - **Arm G:** EmbeddingGemma 2 loaded with text and vision (440M, audio left out). Descriptions carry `task: search result | query: `, and images carry no prefix, as the card says.
   - **Arm G256:** G cut to 256 dimensions and re-normalized.
   - Same images, same descriptions, cosine ranking, on the CPU.
3. **Why the difference answers it:** only the embedder changes, and the key comes by construction (each description belongs to one image). So a gap in how often the right image comes first is the gap the studio would get in an art index.

## 2. The material, and keys by construction

- **The images:** every image on disk under `style-dataset-lab/projects/*/`, pinned to a commit. That's about 2,900: approved, rejected, borderline and unreviewed work. The unapproved images stay in as distractors, because they're often variants of the same subject. That's the hard, realistic case.
- **The queries:** the 385 approved images that have a human-written review description in their record (`judgment.explanation`, median 19 words), spread across four projects: rustline 172, tallow-fen 99, salt-road 73, hesperia 41. The generation prompt is never a query: the image was made from it, so it would test recall of the prompt, not understanding of the picture.
- **The keys:** a description's relevant image is the one it describes. No grading pass is needed.
- **The secondary key:** an image in the same lineage (the same subject, a later iteration) also counts as relevant, where the record names its lineage. It's reported beside the strict key.

## 3. The tasks

- **T1, description to image** (the primary): rank all images for each description.
- **T2, image to description:** rank all 385 descriptions for each of the 385 images.
- **T3, image to image:** for the images whose records name a lineage, does the same subject's other iteration rank near the top? Descriptive only.
- **T4, audio:** **not run in this experiment.** The studio's audio on disk is a piano sample set and about 30 vocal takes, which is too little for a key. It's revisited when ai-jam-sessions or vocology build a labelled clip library. The model's audio encoder is the reason to come back.

## 4. Measures and the decision rule

- **Primary measure:** T1's mean reciprocal rank on the strict key. Paired by query, with a 10,000-resample bootstrap.
- **Secondary measures:**
  - recall@1, @5 and @10;
  - T2's MRR;
  - T1 on the lineage key;
  - each by project;
  - CPU throughput for images and text.
- **Size:** 385 paired queries. With a per-query SD of the paired MRR difference of about 0.30, the 95% half-width is about ±0.03. That resolves the +0.05 margin below.
- **The rule, written before any run:**
  - **G is the studio's art-search embedder** if T1's MRR (G − S) is at least +0.05, its one-sided 95% bootstrap lower bound is above 0, and no project's mean is below S by more than 0.05.
  - **G256 is preferred** if its paired one-sided lower bound against G is above −0.02.
  - **Otherwise S stays.** The result is recorded either way.
- **What adoption means:** an art index in style-dataset-lab (or ai-eyes) built on G. The design of that index is a separate change.

## 5. Fairness and fit

- **Each model's own runtime and preprocessing.** Images go through each model's own processor at its native resolution. Both arms run on the CPU in float32 (G's dtype gate from the text experiment applies). They're timed one at a time.
- **Text length:** descriptions are at most 53 words, under both models' limits. SigLIP2's text tower is padded to 64 tokens, so the validation step counts tokens and stops if any description is cut.
- **Leakage:** none. Neither arm sees records, prompts or lineage.

## 6. Before the first counted run

1. A harness (`harness/multimodal.py`), reviewed by an outside model with its code inline.
2. A free validation run on 20 images and 20 descriptions, which records:
   - the SigLIP2 token counts;
   - G's parameter count with vision loaded (about 440M) and without audio;
   - unit norms;
   - one manipulation record per arm.
3. The Director approves this design.

## 7. After

- **Results go in this folder:** per-query ranks, intervals by project, throughput.
- **The article** covers both experiments, text and multimodal, after a short hands-on look:
  - a few real searches across the art;
  - one image-to-canon lookup;
  - a note on what an audio test would need.
