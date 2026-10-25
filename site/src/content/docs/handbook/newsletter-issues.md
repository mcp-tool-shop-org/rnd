---
title: Newsletter issues
description: The shape of a daily issue, the day's rhythm, and the rules every article follows.
sidebar:
  order: 11
---

From issue 30, the newsletter is one issue a day, with an article for each piece of that day's work worth reporting.
The charts and diagrams follow [Newsletter visuals](/rnd/handbook/newsletter-visuals/).

## The shape

- **One page per day:** `site/src/content/docs/newsletter/issue-NN.md`, with NN continuing the count. The feed makes
  one item per issue file, so Buttondown makes one draft a day.
- **The title** is the day and the day's articles in a line, for example "25 October: a crash test, a lab for tests
  with proven answers, and our Colab cards measured".
- **`highlights`** in the front matter has one line per article. The landing page shows them.
- **The page opens** with a sentence or two, then an "In this issue" list linking to each article's anchor.
- **Each article is an H2,** with its own sections as H3 and its own charts. Chart files are named
  `issue-NN-<article>-<name>.svg`.
- **Size:** `scripts/check_feed.py` fails an issue whose feed HTML is over 90,000 bytes, because Gmail clips an email
  at about 102 KB. A day with more than that splits its least urgent article into the next day's issue.

## The day

- **Cut-off: 18:00 UTC.** Work after it goes into the next day's issue.
- **Gathering:**
  - the Book Keeper: receipts, the units ledger and run records;
  - R&D: results and verdicts;
  - the Publisher: merged PRs, releases, and which security pieces are released and cleared;
  - the Editor: the review replies, then writes.
- **By 19:30 UTC:** one draft, to the Publisher and to Antigravity, in one ticket that covers every article's technical
  claims and the visuals.
- **Then:** fixes, the Publisher's read, and the Director's word. No email goes out without it.
- **A quiet day gets no issue.** If one is skipped, the next issue's opening says so.

## Rules for every article

- A security finding appears only after its fix is merged and released, and never with exploit detail.
- Parked work isn't presented as active.
- Public text says "mcp-tool-shop".
- No quotes from anyone in the studio.
- Every figure is recounted from its source file, and the data is shown as a chart where a chart helps.
- The day's desk brief gives each article a list of what it must not claim.
