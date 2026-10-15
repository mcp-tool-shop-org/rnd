# EmbeddingGemma 2 multimodal design, round 3: brief for Argon

**From:** R&D. **Date:** 2026-10-15. **What we ask:** review revision 3 of `design-multimodal.md`. It changes the key and
the query sources you approved in round 2, and adds a dataset-desk stage before any freeze.

## Why

In your dataset-desk pass you flagged that salt-road's `judgment.explanation` is mostly a ruling, and that rustline's
descriptions are shared. R&D checked every candidate query source against the design's own rule: the generation
prompt is never a query.

| project | source | approved | distinct | equal to or inside the prompt | median share of words in the prompt |
|---|---|---|---|---|---|
| tallow-fen | `judgment.explanation` | 99 | 99 | 0 | 0.62 (max 0.97; 1 query ≥ 0.9; 14 at 0.8–0.89) |
| hesperia | `judgment.explanation` | 41 | 41 | 0 | 0.50 (max 0.81) |
| salt-road | `judgment.explanation` | 73 | 6 (54 are one ruling) | 0 | 0.00 |
| salt-road | `canon.subject` | 73 | 73 | 69 inside the prompt | 1.00 |
| rustline | `judgment.explanation` | 172 | 31 (one ×14) | 9 equal | 0.80 |

So salt-road has no description independent of its prompt. Its `canon.subject` is the prompt's subject clause.
Re-keying can't fix that; re-description can. The Director's direction is that the dataset desk fixes this in the
data, and finding and fixing descriptions is one of the reasons for EmbeddingGemma 2.

## What revision 3 does

- **The desk stage comes first (§2a).**
  - The desk audits every approved record in the four projects with model-free checks:
    - duplicate and near-duplicate descriptions;
    - prompt echo: equal to the prompt, inside it, or 90% or more of the words in it;
    - the source field;
    - not approved, or not current.
  - Flagged records go to re-description and review. Nothing is rewritten silently.
  - An approved re-description becomes the record's current explanation, written by style-dataset-lab's tools, with
    provenance.
- **The experiment runs only on desk-checked pools.** The harness's query gate is the same code as the desk's checks,
  and it refuses anything else. Its unit test refuses salt-road's and rustline's sets as they stand today.
- **The pool is a setting:**
  - **the default:** all four desk-checked projects, up to 385 queries. 80% power at a true gain of about +0.063, as
    in revision 2.
  - **a smaller, earlier option:** tallow-fen and hesperia, 139 queries that pass today. 80% power at about +0.071.
    Whether to run it before the desk finishes is the Director's call.
  - The setting is recorded before the freeze.
- **The fit check never selects this experiment's queries.**
  - The desk's description→image fit check uses an embedder, and EmbeddingGemma 2 is one of the two arms.
  - If its flags chose which descriptions get rewritten, or which re-descriptions are accepted, the queries arm G
    fails would be the ones improved. That's selection on the outcome.
  - So, on the four experiment projects, only the model-free checks trigger re-description before the counted run.
    The fit check runs there afterwards.

## Questions

1. **Who writes re-descriptions, and how are they kept independent of the prompt?** The candidates:
   - the Director or a reviewer, writing from the image alone with the prompt hidden;
   - a captioner (plain-sight, Florence-2) proposing and a person approving.
   The second makes the queries partly model-written, by a third model family. Is that acceptable, or should it be
   a separate, labelled stratum?
2. **The acceptance tests.** Are the gate's checks (distinct; not equal to or inside the prompt; under 0.9 of the
   words in the prompt; approved; current), plus a person's approval, the right acceptance tests for a
   re-description? Would you measure prompt independence another way, for example by content words only?
3. **The fit check.** Do you agree it must not select queries for this experiment before the counted run? If it
   should play a part, how do we stop it favouring arm G? For example, run both arms' fit checks, and act only on
   descriptions both flag.
4. **The pool setting.** Is a setting chosen before the freeze sound, or should the smaller pool be a separate,
   pre-registered study?
5. Anything else that would make revision 3 not ready.

## The diff, revision 2 to revision 3

```diff
diff --git a/experiments/embeddinggemma-2/design-multimodal.md b/experiments/embeddinggemma-2/design-multimodal.md
index 9bef022..b03f40b 100644
--- a/experiments/embeddinggemma-2/design-multimodal.md
+++ b/experiments/embeddinggemma-2/design-multimodal.md
@@ -1,10 +1,25 @@
 # EmbeddingGemma 2 across modalities: finding the studio's art from a description
 
-**Status:** draft design, revision 2, 2026-10-15.
+**Status:** draft design, revision 3, 2026-10-15. It needs Argon's review and then the Director's re-approval, because
+it changes the key and the queries he approved in revision 2.
+- **Why revision 3.** Revision 2's key was "each description belongs to one image", over 385 approved
+  `judgment.explanation` strings. A check of the records shows that holds for only two of the four projects. Argon
+  found it in a review of the dataset desk; R&D measured it on the rig. The table is in §2.
+  - **salt-road:** its explanations are 6 distinct strings over 73 images, and 54 of them are the same ruling. Its
+    `canon.subject` is distinct, but it sits inside the generation prompt for 69 of 73 images, so it's the prompt's
+    subject clause.
+  - **rustline:** its 172 explanations are 31 distinct strings. They read like style-prefixed prompts, and 9 equal the
+    record's prompt.
+  - **The fix is in the data, through the dataset desk** (the Director's direction; finding and fixing descriptions
+    is one of the reasons for EmbeddingGemma 2). The desk audits every description in the four projects. Records it
+    flags go to re-description and review, and the experiment runs only on desk-checked pools (§2a). salt-road shows
+    why re-description, not re-keying, is the fix: it has no description independent of its prompt.
+  - **The new guard:** the harness refuses any query set that fails the desk's checks (§6), so a data shape like this
+    can't pass again by prose.
 - This is the second EmbeddingGemma 2 experiment. The first (`design.md`) tests text and code retrieval, and adopted EmbeddingGemma 2 at 768 dimensions (`results.md`). This one tests what makes the model distinct: text, images and audio in one vector space. The Director asked that the work not stop at text.
 - Template: [A/B experiments](https://mcp-tool-shop-org.github.io/rnd/handbook/ab-experiments/).
 - Revision 2 takes Argon's round 1 review (`argon-consult-multimodal-round1-disposition.md`) and corrects two facts revision 1 got wrong. It said about 2,900 images were on disk, and that records name a lineage.
-- Argon approved revision 2 as written (round 2, 2026-10-15) and added two harness guards, now in step 6. The Director approved the design on 2026-10-15. Next: the harness, its outside review, and the free validation run, which is CPU work under the rig's preflight (a thread cap, the expected load told before it starts).
+- Argon approved revision 2 as written (round 2, 2026-10-15) and added two harness guards, now in step 6. The Director approved revision 2 on 2026-10-15. Next, for revision 3: Argon's review, then the Director's re-approval. After that, the harness, its outside review, and the free validation run. That run is CPU work under the rig's preflight (a thread cap, the expected load told before it starts).
 
 ## 1. The check in three sentences
 
@@ -19,32 +34,71 @@
 
 Measured on 2026-10-15 in style-dataset-lab (working tree at `80f3cb6`).
 
-- **The queries:** 385 approved images whose record holds a human-written review description (`judgment.explanation`, median 19 words, at most 53).
-
-  | Project | Queries |
-  |---|---|
-  | rustline | 172 |
-  | tallow-fen | 99 |
-  | salt-road | 73 |
-  | hesperia | 41 |
-
-  The generation prompt is never a query. The image was made from it, so it would test recall of the prompt, not understanding of the picture.
-- **The pool:** every image file under `projects/<project>/outputs/<folder>/` in those four projects, de-duplicated by content.
-  - That's 1,451 files, 1,246 after de-duplication: the 385 targets plus 861 distractors.
-  - The distractors are 496 unrecorded generation outputs (earlier waves and variants), 202 rejected, 104 unreviewed and 59 borderline.
-  - **Byte-identical copies are merged before ranking.** 172 targets, all of rustline's, have a byte-identical copy in a wave folder. Ranking both would turn the strict key into a coin-flip tie between identical vectors. The recorded copy is kept, and no merged group holds two targets.
+- **The queries:** approved images whose record holds a distinct, human-written review description that isn't
+  copied from its generation prompt. The prompt is never a query: the image was made from it, so it would test
+  recall of the prompt, not understanding of the picture. Revision 3 checked every candidate source against that
+  rule (measured 2026-10-15, read-only):
+
+  | Project | Source | Approved | Distinct | Equal to or inside the prompt | Median share of words in the prompt | Pass the gate today |
+  |---|---|---|---|---|---|---|
+  | tallow-fen | `judgment.explanation` | 99 | 99 | 0 | 0.62 | 98 (one query at 0.97 excluded) |
+  | hesperia | `judgment.explanation` | 41 | 41 | 0 | 0.50 | 41 |
+  | salt-road | `judgment.explanation` | 73 | 6 (54 are one ruling) | 0 | 0.00 | 0 |
+  | salt-road | `canon.subject` | 73 | 73 | 69 inside | 1.00 | 0 |
+  | rustline | `judgment.explanation` | 172 | 31 (one ×14) | 9 equal | 0.80 | 0 |
+
+  - **Today 139 pass,** tallow-fen's and hesperia's. Median length: 31 words for tallow-fen, 18 for hesperia.
+  - **The gate's prompt rule:** a description fails if it equals or sits inside its record's prompt, or if 90% or more
+    of its words appear there.
+  - **The 0.80–0.89 band** (14 tallow-fen queries and 1 hesperia) passes. A secondary measure drops it (§4).
+
+### 2a. The desk stage, before any freeze
+
+1. **The desk audits every approved record in the four projects.** It runs the gate's checks, which are model-free
+   and string-based, the same code the harness runs:
+   - duplicate or near-duplicate descriptions in a project, with the ruling repeated 54 times shown as one group;
+   - a description that echoes its prompt (the rule above);
+   - the source of the text (`judgment.explanation`, `canon.subject` or none);
+   - not approved, or not the record's current description.
+2. **Flagged records go to re-description and review on the desk.** Nothing is rewritten silently, and the desk
+   never writes into a project.
+   - An approved re-description becomes the record's current `judgment.explanation`, written by style-dataset-lab's
+     own tools, with a provenance note: who wrote it, when, and from what.
+   - On today's numbers, that's salt-road's 73 and most of rustline's 172.
+3. **How a re-description is written:**
+   - from the image alone, with the generation prompt and the other records out of view;
+   - it must pass the gate;
+   - a person approves it.
+   Who writes it (the Director, a reviewer, or a captioner such as plain-sight with a person approving) is an open
+   question for this round (see the round-3 brief).
+4. **The fit check never selects this experiment's queries.**
+   - The desk also checks whether each description picks out its own image among its siblings, through an
+     embedding. But EmbeddingGemma 2 is one of this experiment's two arms.
+   - If its fit check chose which descriptions are rewritten or accepted, the queries it fails would be the ones
+     improved. That's selection on the outcome, and it would tilt the comparison toward arm G.
+   - So, on the four experiment projects, only the model-free checks trigger re-description before the counted run.
+   - The fit check runs there after the counted run, which also keeps the desk's peeking guard. Elsewhere it's free
+     to use.
+- **The pool:** every image file under `projects/<project>/outputs/<folder>/` in all four projects, de-duplicated by
+  content. rustline's and salt-road's images stay as distractors.
+  - That's 1,451 files, 1,246 after de-duplication. On the smaller pool setting, that's 139 targets plus 1,107 distractors; on the default, up to 385 targets plus 861.
+  - The distractors are:
+    - 496 unrecorded generation outputs (earlier waves and variants);
+    - 202 rejected, 104 unreviewed and 59 borderline;
+    - 246 approved images that aren't queries: rustline's 172, salt-road's 73, and the one excluded tallow-fen image.
+  - **Byte-identical copies are merged before ranking.** rustline's 172 approved images each have a byte-identical copy in a wave folder. They're distractors now, but merging still stops two identical vectors from both entering a ranking. The recorded copy is kept, and no merged group holds two targets.
   - **Left out:** files at the top of `outputs/`, which are contact sheets and composites that contain targets; `training/` and `exports/`, which are copies and crops; and `inbox/` and `inputs/`, which are references.
   - **Pinned:** the images aren't in git, so the pool is pinned by a manifest of every file's sha256, frozen before any run.
 - **The key:** a description's relevant image is the one it describes. No grading pass is needed.
 - **Near-duplicates are masked.** A pool image within a dHash Hamming distance of 10 (of 256 bits) of the target is left out of that query's ranking. That's a non-learned image hash, neutral to both arms.
-  - 10 targets have one to three such images.
+  - Revision 2 counted 10 of its 385 targets with one to three such images. Revision 3's targets are recounted when the manifest is frozen.
   - The masked pairs are listed in the frozen manifest.
-- **No lineage key.** No record among the 385 names a lineage: `iteration` is null in every record, and the 60 records with a `lineage` object are star-freight's, with null fields. Record ids don't give a reliable proxy either: one id stem covers 54 different salt-road images from a single wave. So a different generation of the same subject stays in the pool as a distractor. That adds noise equally to both arms and can't favour either.
+- **No lineage key.** No approved record in the four projects names a lineage: `iteration` is null in every record, and the 60 records with a `lineage` object are star-freight's, with null fields. Record ids don't give a reliable proxy either: one id stem covers 54 different salt-road images from a single wave. So a different generation of the same subject stays in the pool as a distractor. That adds noise equally to both arms and can't favour either.
 
 ## 3. The tasks
 
 - **T1, description to image** (the primary): rank the pool for each description.
-- **T2, image to description:** rank all 385 descriptions for each target image.
+- **T2, image to description:** rank every query description in the chosen pool for each target image.
 - **T3, audio:** **not run in this experiment.** What a real audio test would need is recorded in the disposition, for when ai-jam-sessions or vocology build a labelled clip library.
 
 Revision 1's image-to-image task needed lineage, and is dropped.
@@ -61,19 +115,27 @@ Revision 1's image-to-image task needed lineage, and is dropped.
   - recall@1, @5 and @10;
   - T2's MRR;
   - T1 with no near-duplicate masking;
-  - T1 with only the 385 approved images as the pool (a canon lookup);
+  - T1 with only the approved images of the four projects (385) as the pool, a canon lookup;
+  - T1 without the queries in the 0.80–0.89 prompt-overlap band (§2);
   - each by project;
   - CPU throughput for images and text;
   - G cut to 512 and 256 dimensions, as a descriptive curve only.
-- **Size:** 385 paired queries. Take σΔ, the per-query SD of the paired MRR difference, as about 0.30.
-  - The SE is 0.015, and the one-sided 95% margin is 0.025.
-  - So the +0.05 bar below is the binding test: any result that clears it also clears a lower bound above 0.
-  - It's a bar on the sample mean, not a test against +0.05. A true gain of +0.05 clears it half the time. Clearing it with 80% power needs a true gain of about +0.063.
+- **Size: the pool is a setting.** Take σΔ, the per-query SD of the paired MRR difference, as about 0.30.
+  - **The default** is all four desk-checked projects: up to 385 queries once salt-road and rustline are
+    re-described. That gives an SE of about 0.015 and a one-sided margin of 0.025, and 80% power needs a true gain
+    of about +0.063, as in revision 2.
+  - **The smaller, earlier option** is tallow-fen and hesperia only: 139 queries, which pass the gate today. That
+    gives an SE of 0.025 and a margin of 0.042, and 80% power needs about +0.071. By project, hesperia's 41 queries
+    (SE about 0.047) can only catch a large deficit. Whether to run it before the desk stage finishes is the
+    Director's call.
+  - Either way, the +0.05 bar below is the binding test: any result that clears it also clears a lower bound above 0.
+    It's a bar on the sample mean, not a test against +0.05; a true gain of +0.05 clears it half the time.
+  - The pool setting is chosen and recorded before the manifest is frozen, never after a result.
 - **The rule, written before any run:**
   - **G is the studio's art-search embedder, at 768 dimensions,** when all of these hold:
     - T1's MRR (G − S) is at least +0.05;
     - its one-sided 95% bootstrap lower bound is above 0;
-    - no project's one-sided 95% upper bound on (G − S) is below 0, meaning no project is significantly worse.
+    - no project's one-sided 95% upper bound on (G − S) is below 0, meaning no project in the chosen pool is significantly worse.
   - **Otherwise S stays.** The result is recorded either way.
   - Dimensions aren't part of the rule. Text adopted 768, so images match it and one index can hold both.
 - **What adoption means:** an art index in style-dataset-lab (or ai-eyes) built on G. The design of that index is a separate change.
@@ -82,21 +144,31 @@ Revision 1's image-to-image task needed lineage, and is dropped.
 
 - **Each model's own runtime and preprocessing.** Images go through each model's own processor at its native resolution. Both arms run on the CPU in float32 (G's dtype gate from the text experiment applies). They're timed one at a time.
 - **SigLIP2's text side** uses the fixed padding it was trained with: `padding="max_length", max_length=64`. Lowercasing is whatever its processor does by default, recorded.
-- **Text length:** all 385 descriptions are token-counted with SigLIP2's tokenizer before any run, and the run stops if any is cut. That reads lengths only, so it leaks nothing.
+- **Text length:** every description in the chosen pool is token-counted with SigLIP2's tokenizer before any run, and the run stops if any is cut. That reads lengths only, so it leaks nothing. tallow-fen's median is 31 words, so this gate matters more than it did in revision 2.
 - **Leakage:** none. Neither arm sees records, prompts or paths.
 
 ## 6. Before the first counted run
 
+0. The desk stage (§2a) is done for the chosen pool setting. Every record in the pool passes the desk's model-free
+   checks, or is excluded and listed.
 1. The pool manifest (sha256 per file, de-duplication groups and masked near-duplicate pairs) is frozen and committed. It holds ids and hashes only, no images.
 2. A harness (`harness/multimodal.py`), reviewed by an outside model with its code inline. It carries the two guards from Argon's round 2:
    - **Ties never follow file order.** Reciprocal rank uses mid-rank, so a tie can't be broken by the order of the manifest.
    - **The token gate halts before any embedding.** If any description is over 64 SigLIP2 tokens, it logs the query ids and their counts and stops.
+   - **The query gate refuses a bad query set before any embedding.** This guard is new in revision 3. It's the same
+     code as the desk's model-free checks (§2a), and it recomputes from the records. It refuses to run if any frozen
+     query:
+     - repeats another query, after lower-casing and trimming;
+     - equals its record's generation prompt, or appears inside it;
+     - has 90% or more of its words in that prompt.
+     It also refuses if a manifest query isn't approved, or isn't the record's current `judgment.explanation`.
+     Its unit test feeds it salt-road's and rustline's real query sets as they stand today, and it must refuse both.
 3. A free validation run on 20 images and 20 descriptions, which records:
-   - SigLIP2's token counts for all 385 descriptions;
+   - SigLIP2's token counts for every description in the chosen pool;
    - G's parameter count with vision loaded (about 440M) and without audio;
    - unit norms;
    - one manipulation record per arm, for each task's prefix.
-4. The Director approves this design.
+4. Argon reviews revision 3, and the Director re-approves it.
 
 ## 7. After
 
```
