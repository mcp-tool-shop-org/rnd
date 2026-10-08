---
license: other
license_name: mixed-see-card
pretty_name: Natural-error yardstick for critics
language:
- en
task_categories:
- text-classification
tags:
- error-detection
- llm-as-judge
- critic
- synthetic
size_categories:
- n<1K
---

# Natural-error yardstick for critics (v1)

**What this is.** 95 answers written by Llama 3.1 8B to explanatory questions in twelve topic
areas. Each answer is labelled for real mistakes (a false fact, a wrong number or unit, or a
reasoning step that does not follow) by two blind Claude passes (Claude Opus 5.5, and four Claude
Sonnet 5.5 agents), with the disagreements adjudicated.

| | |
|---|---|
| Answers with an error | 59 |
| Clean answers | 36 |
| Error sentences marked by both passes | 84 (63 clear) |
| Labeller agreement | item agreement 0.82, Cohen's kappa 0.63 |
| Correction pairs | 31 (the original answer, and a copy with its agreed clear errors rewritten) |
| Screen judges | gemma4:31b, mistral-small:24b, granite4.1:30b, muse-glimmer, nemotron-3.5-lightning |

**What it is for.** Measuring how well a critic, or an LLM judge, finds errors that a model made
while answering, as opposed to errors planted afterwards by an editing model. The correction
pairs reverse the usual set-up: the edited copy is the better one, so a critic that only notices
edits fails them.

**Read before use**
- The labels are made by models, not by people. They are useful ground truth for comparing
  judges, but they are not human-verified.
- Every answer comes from one generator (Llama 3.1 8B). A judge from the same family, such as
  muse-glimmer from Meta, may behave differently on it than on another generator's answers.
- In the v1 screens a failed judge reply is stored as an empty list. muse-glimmer had 1 such
  reply and nemotron-3.5-lightning had 39, so its v1 run is unreliable. A context-rich re-screen
  that records the reason for each failure will replace these in a later version.

**Files.** `data/questions.json`, `data/answers.json`, `data/labels_claude.json`,
`data/labels_sonnet.json`, `data/gold.json` (adjudicated), `data/corrections.json`,
`data/selection.json`, `data/screen.json` and `data/screen_extra.json` (judge flags), plus the
build scripts and the experiment README. `datapack.json` lists every file's SHA-256 and the model
pins. The pack files sit under `files/`. Check a download with `rnd datapack verify natural-errors --copy <download>/files`
(`pip install mcptoolshop-rnd`).

## Licences

This dataset mixes material under different terms, file by file (see `datapack.json`):

- **Answers, and any file quoting them** (`answers.json`, `corrections.json`, `screen*.json`):
  outputs of Llama 3.1 8B. **Built with Llama.** Llama 3.1 is licensed under the Llama 3.1
  Community License, Copyright © Meta Platforms, Inc. All Rights Reserved. Use is subject to the
  [Llama 3.1 Community License](https://www.llama.com/llama3_1/license/) and the
  [Acceptable Use Policy](https://www.llama.com/llama3_1/use-policy/).
- **Questions:** outputs of Mistral Small (an Apache-2.0 model).
- **Judge flags:** outputs of Apache-2.0 models (gemma4, mistral-small, granite4.1, muse-glimmer)
  and of nemotron-3.5-lightning (NVIDIA Open Model License), quoting answer sentences.
- **Labels, adjudication, correction sentences, scripts and README:** MIT, © mcp-tool-shop.
- Parts were written by AI models (Claude, Llama, Mistral, Gemma, Granite, Muse, Nemotron), and
  none of the data is presented as human-written.

Source: [mcp-tool-shop-org/rnd](https://github.com/mcp-tool-shop-org/rnd), `experiments/natural-errors/`.
