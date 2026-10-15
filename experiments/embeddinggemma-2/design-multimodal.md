# EmbeddingGemma 2 across modalities: finding the studio's art from a description

**Status:** approved design, revision 3, 2026-10-15. Argon gave it a final green light (round 3), and the Director
re-approved it the same day; it changes the key and the queries approved in revision 2.
- **Why revision 3.** Revision 2's key was "each description belongs to one image", over 385 approved
  `judgment.explanation` strings. A check of the records shows that holds for only two of the four projects. Argon
  found it in a review of the dataset desk; R&D measured it on the rig. The table is in §2.
  - **salt-road:** its explanations are 6 distinct strings over 73 images, and 54 of them are the same ruling. Its
    `canon.subject` is distinct, but it sits inside the generation prompt for 69 of 73 images, so it's the prompt's
    subject clause.
  - **rustline:** its 172 explanations are 31 distinct strings. They read like style-prefixed prompts, and 9 equal the
    record's prompt.
  - **The fix is in the data, through the dataset desk** (the Director's direction; finding and fixing descriptions
    is one of the reasons for EmbeddingGemma 2). The desk audits every description in the four projects. Records it
    flags go to re-description and review, and the experiment runs only on desk-checked pools (§2a). salt-road shows
    why re-description, not re-keying, is the fix: it has no description independent of its prompt.
  - **The new guard:** the harness refuses any query set that fails the desk's checks (§6), so a data shape like this
    can't pass again by prose.
- This is the second EmbeddingGemma 2 experiment. The first (`design.md`) tests text and code retrieval, and adopted EmbeddingGemma 2 at 768 dimensions (`results.md`). This one tests what makes the model distinct: text, images and audio in one vector space. The Director asked that the work not stop at text.
- Template: [A/B experiments](https://mcp-tool-shop-org.github.io/rnd/handbook/ab-experiments/).
- Revision 2 takes Argon's round 1 review (`argon-consult-multimodal-round1-disposition.md`) and corrects two facts revision 1 got wrong. It said about 2,900 images were on disk, and that records name a lineage.
- Argon approved revision 2 as written (round 2, 2026-10-15) and added two harness guards, now in step 6. The Director approved revision 2 on 2026-10-15. Argon reviewed revision 3 (round 3, 2026-10-15): ready once the acceptance tests, the fit-check rule and the pool path were locked in the text, which this revision does; he then gave it a final green light. The Director re-approved revision 3 on 2026-10-15. Next, in order: the desk stage for all four projects (§2a), finished before the manifest is frozen; the harness and its outside review; and the free validation run. That run is CPU work under the rig's preflight (a thread cap, the expected load told before it starts).

## 1. The check in three sentences

1. **The question:** can the studio find its own art from a plain description of it, and from a picture of it? Does EmbeddingGemma 2 do that better than SigLIP2, the image-text model the studio already runs in ai-eyes?
2. **What each arm gets:**
   - **Arm S:** SigLIP2 (`google/siglip2-so400m-patch14-384`, already cached), its text tower for descriptions and its image tower for images.
   - **Arm G:** EmbeddingGemma 2 loaded with text and vision (440M, audio left out), at 768 dimensions. Images carry no prefix, as the card says.
   - Same images, same descriptions, cosine ranking, on the CPU.
3. **Why the difference answers it:** only the embedder changes, and the key comes by construction (each description belongs to one image). So a gap in how often the right image comes first is the gap the studio would get in an art index.

## 2. The material, and keys by construction

Measured on 2026-10-15 in style-dataset-lab (working tree at `80f3cb6`).

- **The queries:** approved images whose record holds a distinct, human-written review description that isn't
  copied from its generation prompt. The prompt is never a query: the image was made from it, so it would test
  recall of the prompt, not understanding of the picture. Revision 3 checked every candidate source against that
  rule (measured 2026-10-15, read-only):

  | Project | Source | Approved | Distinct | Equal to or inside the prompt | Median share of words in the prompt | Pass the gate today |
  |---|---|---|---|---|---|---|
  | tallow-fen | `judgment.explanation` | 99 | 99 | 0 | 0.62 | 98 (one query at 0.97 excluded) |
  | hesperia | `judgment.explanation` | 41 | 41 | 0 | 0.50 | 41 |
  | salt-road | `judgment.explanation` | 73 | 6 (54 are one ruling) | 0 | 0.00 | 0 |
  | salt-road | `canon.subject` | 73 | 73 | 69 inside | 1.00 | 0 |
  | rustline | `judgment.explanation` | 172 | 31 (one ×14) | 9 equal | 0.80 | 0 |

  - **Today about 139 pass the all-word rule,** tallow-fen's and hesperia's. Median length: 31 words for tallow-fen, 18
    for hesperia. Revision 3's full acceptance tests (§2a) are run by the desk, and the count that passes them is
    recorded before the freeze.
  - **Records the gate flags in tallow-fen or hesperia,** such as the one tallow-fen record at 0.97, are re-described
    at the desk like the others. Up to 385 queries are then possible.
  - **The 0.80–0.89 all-word band** (14 tallow-fen queries and 1 hesperia) passes if the other tests pass. A secondary
    measure drops it (§4).

### 2a. The desk stage, before any freeze

1. **The desk audits every approved record in the four projects.** Its checks are model-free and string-based, and
   they're the same code the harness runs. It shows the ruling repeated 54 times as one group, and the source of each
   text (`judgment.explanation`, `canon.subject` or none). It flags any record that isn't approved, or whose text isn't
   the record's current description.

   The acceptance tests (Argon, round 3), the same code in the desk and the harness gate (§6). A description fails if:
   - **it echoes its prompt:**
     - it equals the record's generation prompt, or sits inside it;
     - it shares a contiguous run of 6 or more words with the prompt;
     - 90% or more of its words appear in the prompt;
     - 80% or more of its content words appear in the prompt;
   - **it wraps `canon.subject`:** the words of the record's `canon.subject`, when there are 4 or more, appear as a
     contiguous slice of the description's words;
   - **it's too short:** fewer than 8 words, or fewer than 5 content words;
   - **it duplicates another query in the pool:** for any pair across the whole pool, `"".join(words(a)) ==
     "".join(words(b))`, or a Jaccard of 0.85 or more between the two content-word sets;
   - **it's too long for SigLIP2:** more than 64 tokens, counted as `len(tokenizer(s.lower(), padding=False,
     truncation=False)["input_ids"])` on the cached `siglip2-so400m-patch14-384` tokenizer, special tokens included.
     The processor's defaults pad and truncate to 64, so a count through them could never fail. This is checked when
     the desk approves the text, so the harness's token gate can't trip later.

   **Pinned arithmetic:**
   - **Words** are `re.findall(r"\w+", s.lower())`.
   - **A content word** is a word not in the frozen stopword list. The list is committed with the gate, and its sha256 is
     recorded in the manifest.
   - **A share** is the number of the description's words (counting repeats) that occur anywhere in the prompt, over
     the description's word count; the same for content words.
   - **A contiguous run, and the `canon.subject` slice,** are matched on these word sequences.
   - **The Jaccard** is over content-word sets, for every pair of queries across the whole pool.
2. **Flagged records go to re-description and review on the desk.** Nothing is rewritten silently, and the desk
   never writes into a project.
   - An approved re-description becomes the record's current `judgment.explanation`, written by style-dataset-lab's
     own tools, with a provenance note: who wrote it, when, and from what.
   - On today's numbers, that's salt-road's 73 and most of rustline's 172.
3. **How a re-description is written:**
   - from the image alone, with the generation prompt, `canon.subject` and the other records out of view;
   - it must pass the acceptance tests above;
   - a person approves it.

   **Who writes it (the Director's choice): the desk's own pipeline, captioner-assisted.** This is Argon's
   captioner-assisted path, under his round-3 conditions.
   - **plain-sight (Florence-2) drafts** each re-description blind, from the pixels alone.
   - **A person edits** the draft into studio search prose of 12–45 words. They rewrite it, not click it through. The
     desk shows the target beside 3 to 5 sibling images, so the text picks out its own picture.
   - **`author_kind` is recorded on every query:** `human` for tallow-fen's and hesperia's existing descriptions, and
     `captioner_assisted` for every re-description (salt-road's, rustline's, and any tallow-fen or hesperia records flagged by the §2a.1 gate and re-described at the desk). §4
     reports the strata.
   - **No model that measures an arm accepts or rejects a re-description before the counted run.** ai-eyes is SigLIP2,
     the same model as arm S, so its noun checks (`image_contains`) are held like the EG2 fit check (point 4 below).
     Argon's warning applies: rewrites accepted through the towers would be "text specifically tuned to current
     vision-text towers". On these four projects, the only acceptance tests before the counted run are the model-free
     tests above and the person's edit. ai-eyes and EG2 run there after the counted run.
   - **The query is the search prose, not a training caption.** The approved re-description becomes the record's
     current `judgment.explanation`, and that's the text the benchmark reads. Style-LoRA training captions (the
     project's trigger plus content, with canon style words stripped) are made separately, by caption surgery, and
     stored apart. The benchmark never reads them, so no query carries a project-wide trigger prefix that would blur
     the prompt-echo and contiguous-run tests.
4. **The fit check never selects this experiment's queries.**
   - The desk also checks whether each description picks out its own image among its siblings, through an
     embedding. But EmbeddingGemma 2 is one of this experiment's two arms.
   - If its fit check chose which descriptions are rewritten or accepted, the queries it fails would be the ones
     improved. That's selection on the outcome, and it would tilt the comparison toward arm G.
   - So, on the four experiment projects, only the model-free checks trigger re-description before the counted run.
   - The fit check runs there after the counted run, which also keeps the desk's peeking guard. Elsewhere it's free
     to use.
   - **No "both arms flag it" variant either** (Argon, round 3). Acting only on descriptions that both arms' fit checks
     flag would cut the tail of hard queries and leave only the arms' disagreements. That changes N and the SE
     selectively.
- **The pool:** every image file under `projects/<project>/outputs/<folder>/` in all four projects, de-duplicated by
  content.
  - That's 1,451 files, 1,246 after de-duplication: up to 385 targets plus 861 non-approved distractors.
  - The distractors are 496 unrecorded generation outputs (earlier waves and variants), 202 rejected, 104 unreviewed
    and 59 borderline.
  - **Byte-identical copies are merged before ranking.** Each of rustline's 172 approved images has a byte-identical copy in a wave folder; merging stops two identical vectors from both entering a ranking. The recorded copy is kept, and no merged group holds two targets.
  - **Left out:** files at the top of `outputs/`, which are contact sheets and composites that contain targets; `training/` and `exports/`, which are copies and crops; and `inbox/` and `inputs/`, which are references.
  - **Pinned:** the images aren't in git, so the pool is pinned by a manifest of every file's sha256, frozen before any run.
- **The key:** a description's relevant image is the one it describes. No grading pass is needed.
- **Near-duplicates are masked.** A pool image within a dHash Hamming distance of 10 (of 256 bits) of the target is left out of that query's ranking. That's a non-learned image hash, neutral to both arms.
  - Revision 2 counted 10 of its 385 targets with one to three such images. Revision 3's targets are recounted when the manifest is frozen.
  - The masked pairs are listed in the frozen manifest.
- **No lineage key.** No approved record in the four projects names a lineage: `iteration` is null in every record, and the 60 records with a `lineage` object are star-freight's, with null fields. Record ids don't give a reliable proxy either: one id stem covers 54 different salt-road images from a single wave. So a different generation of the same subject stays in the pool as a distractor. That adds noise equally to both arms and can't favour either.

## 3. The tasks

- **T1, description to image** (the primary): rank the pool for each description.
- **T2, image to description:** rank every query description in the chosen pool for each target image.
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
  - T1 with only the approved images of the four projects (385) as the pool, a canon lookup;
  - T1 without the queries in the 0.80–0.89 prompt-overlap band (§2);
  - each by project;
  - CPU throughput for images and text;
  - G cut to 512 and 256 dimensions, as a descriptive curve only.
- **One counted run on all four desk-checked projects** (the Director's choice, Path A).
  - That means one freeze and one decision rule.
  - There's no earlier run on the 139 that pass today. Running 139 first and then the full pool under one rule would
    be an unadjusted two-look test. A separate study on a disjoint pool (Argon's Path B) wasn't chosen.
- **Size:** up to 385 queries, once salt-road's, rustline's, and any tallow-fen or hesperia records flagged by the §2a.1 gate and re-described at the desk, are re-described and pass
  the acceptance tests. Take σΔ, the per-query SD of the paired MRR difference, as about 0.30.
  - At 385, the SE is about 0.015 and the one-sided 95% margin is 0.025. 80% power needs a true gain of about +0.063,
    as in revision 2.
  - If fewer queries pass, the count and the power are recomputed and recorded before the freeze. The rule doesn't
    change.
  - The +0.05 bar below is the binding test: any result that clears it also clears a lower bound above 0. It's a bar on
    the sample mean, not a test against +0.05; a true gain of +0.05 clears it half the time.
  - T1 is also reported by `author_kind` (§2a.3), descriptively. Author is almost fully confounded with project:
    `human` is tallow-fen and hesperia, and `captioner_assisted` is salt-road, rustline, and any tallow-fen or hesperia records flagged by the §2a.1 gate and re-described at the desk.
    So the strata are a disclosure, not a test of who writes better queries.
- **The rule, written before any run:**
  - **G is the studio's art-search embedder, at 768 dimensions,** when all of these hold:
    - T1's MRR (G − S) is at least +0.05;
    - its one-sided 95% bootstrap lower bound is above 0;
    - no project's one-sided 95% upper bound on (G − S) is below 0, meaning no project in the chosen pool is significantly worse.
  - **Otherwise S stays.** The result is recorded either way.
  - Dimensions aren't part of the rule. Text adopted 768, so images match it and one index can hold both.
- **What adoption means:** an art index in style-dataset-lab (or ai-eyes) built on G. The design of that index is a separate change.

## 5. Fairness and fit

- **Each model's own runtime and preprocessing.** Images go through each model's own processor at its native resolution. Both arms run on the CPU in float32 (G's dtype gate from the text experiment applies). They're timed one at a time.
- **SigLIP2's text side** embeds with the fixed padding it was trained with: `padding="max_length", max_length=64`, truncation on. Lowercasing is whatever its processor does by default, recorded. The token gate (§2a.1, §6) counts separately, without padding or truncation.
- **No prompt template:** ai-eyes passes the query text to the processor as is, with no wrapping such as "a photo of" (checked in `ai_eyes_mcp/engine.py`), so arm S does the same.
- **Text length:** every description in the chosen pool is token-counted with SigLIP2's tokenizer before any run, and the run stops if any is cut. That reads lengths only, so it leaks nothing. tallow-fen's median is 31 words, so this gate matters more than it did in revision 2.
- **Leakage:** none. Neither arm sees records, prompts or paths.

## 6. Before the first counted run

0. The desk stage (§2a) is done for all four projects. Every record in the pool passes the acceptance tests, or is
   excluded and listed.
1. The pool manifest (sha256 per file, de-duplication groups and masked near-duplicate pairs) is frozen and committed. It holds ids and hashes only, no images.
2. A harness (`harness/multimodal.py`), reviewed by an outside model with its code inline. It carries the two guards from Argon's round 2:
   - **Ties never follow file order.** Reciprocal rank uses mid-rank, so a tie can't be broken by the order of the manifest.
   - **The token gate halts before any embedding.** If any description is over 64 SigLIP2 tokens, counted as in §2a.1 (no padding, no truncation, special tokens included), it logs the query ids and their counts and stops.
   - **The query gate refuses a bad query set before any embedding.** This guard is new in revision 3. It's the same
     code as the desk's acceptance tests (§2a.1), with the same pinned arithmetic, and it recomputes from the records.
     - It refuses to run if any frozen query fails any acceptance test.
     - It also refuses if a manifest query isn't approved, or isn't the record's current `judgment.explanation`.
     - It also refuses if the stopword list's sha256 differs from the manifest's.
     - Its unit test feeds it salt-road's and rustline's real query sets as they stand today, and it must refuse both.
3. A free validation run on 20 images and 20 descriptions, which records:
   - SigLIP2's token counts for every description in the chosen pool;
   - G's parameter count with vision loaded (about 440M) and without audio;
   - unit norms;
   - one manipulation record per arm, for each task's prefix.
4. Argon reviews revision 3, and the Director re-approves it.

## 7. After

- **Results go in this folder:** per-query ranks, intervals by project, throughput.
- **The article** covers both experiments, text and multimodal, after a short hands-on look:
  - a few real searches across the art;
  - one image-to-canon lookup;
  - a note on what an audio test would need.
