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
- **The last H2 is the daily watch,** after the last article and before anything else. See [The daily watch](#the-daily-watch).
- **Size:** `scripts/check_feed.py` fails an issue whose feed HTML is over 90,000 bytes, because Gmail clips an email
  at about 102 KB. A day with more than that splits its least urgent article into the next day's issue.

## The daily watch

Every issue ends with the daily watch: a short list of what changed since the last issue in the tools, models and
sources the studio follows, like the [weekly watch](/rnd/watch/2026-10-26/) for one day. Every morning R&D runs
`rnd watch` and the morning Argon scout, checks the reply against its sources, and drops `daily-watch-YYYY-MM-DD.md`
into the Editor's inbox. The Editor merges it, spot-checks it, logs it and owns the page.

- **Where:** the last H2, `## The daily watch`, after the last article, and the last entry of "In this issue".
- **The change line** comes first, above the bullets: `3 new, 1 updated since [issue 33](/rnd/newsletter/issue-33/).`
  "New" means the project hasn't been in an earlier daily-watch bullet; "updated" means it has, and this is a later
  version or change. Only bullets that ship count, and a correction doesn't. Leave out "0 updated". On a quiet day, or
  with no file, there is no change line.
- **Length:** 3 to 6 bullets (or fewer on a quiet day, followed by "A quiet day on the watchlist.").
- **Each bullet** is one line with one link: the name and version in bold and the release date, exactly as the source
  shows them, then what changed and what it means for us, with the link on the release page itself (never a repo root).
- **Longer items** (one that needs a paragraph, or that we acted on) become an article or go under "In brief", not
  into the watch.
- **The file's own heading** (`## Daily watch`) becomes `## The daily watch` at the build. A file for a quiet day
  ends "A quiet day on the watchlist." and that line goes in as it is.
- **No file by the build:** the heading stays, and the section says in one line that the watch had nothing new. It is
  never left blank.
- **Highlights:** the watch adds none. It is part of the issue page, so it is in the feed item, the email and the
  mirrors, and it counts toward the 90,000-byte limit.
- **The rules of every article apply.** A fix in someone else's tool appears once its release is public; no item goes
  in without R&D's check of its own source.
- **The Editor's spot-check:** before the build, the Editor opens the links of 2 or 3 bullets and checks the date, the
  version and what changed. A bullet that can't be confirmed is cut.
- **Written for a reader outside the studio:** what the thing is, why it matters, one link. No internal paths, seat
  names or studio shorthand.
- **Corrections:** when a published bullet turns out wrong, the next issue's watch ends with a one-line note:
  `Correction: <what the earlier issue said, and what is right> (<link>).`
- **The log:** the Editor keeps a short record of which bullets were used and which were cut, with a reason, so the
  watchlist can be tuned. Each used bullet also records its project name, its tag, whether it is new or updated, and
  whether we acted on it.
- **Stable releases only.** Pre-release and nightly builds don't get bullets.
- **No date, no bullet.** An item whose source gives no date, and has no recorded content change, is cut.
- **Breaking changes.** When the release notes have a backwards-incompatible section, the bullet carries a short
  "Breaking:" clause. The Editor checks it against the notes.
- **Models:** a model bullet says "licence: not checked" until its licence has been read at source.
- **A late sweep at about 16:00 UTC.** The Editor checks the same sources, GitHub releases and feeds only, for anything
  since the morning scout's run. It merges, spot-checks and logs what it adds, the same way as the morning bullets.
- **Tags:** each bullet gets one of six: `models`, `runtimes`, `gpu-stack`, `agent-tools`, `creative`, `licences`.
  A licence or terms change, a deprecation or a shutdown takes `licences`, whatever the tool. Tags appear in the
  weekly archive, not in the issue.

### The weekly archive

Each Monday watch page gets a section, `## This week's daily items`, after "From our own bench this week" and before
"How the watch works". It lists every daily-watch bullet that shipped in the issues from the previous Monday through
Sunday, grouped by tag, newest first. Each row keeps its link and adds the issue it ran in. A bullet that also appears
under the week's "What we acted on" ends `· we acted on this`. A corrected bullet is replaced in place and marked
`(corrected in issue N)`. Quiet days are listed in one closing line.

### The template

```markdown
## The daily watch

2 new, 1 updated since [issue N](/rnd/newsletter/issue-N/).

- **<Name> <version>** (<YYYY-MM-DD>): <what changed, and what it means for us> ([release notes](https://example.com/release)).
```

No file by the build:

```markdown
## The daily watch

The daily watch had nothing new since the last issue.
```

## The day

- **Cut-off: 18:00 UTC.** Work after it goes into the next day's issue.
- **Gathering:**
  - the Book Keeper: receipts, the units ledger and run records;
  - R&D: results and verdicts, and the daily watch block, checked, by the cut-off;
  - the Publisher: merged PRs, releases, and which security pieces are released and cleared;
  - the Editor: the review replies, then writes.
- **By 19:30 UTC:** one draft, to the Publisher and to Antigravity, in one ticket that covers every article's technical
  claims and the visuals.
- **Then:** fixes, the Publisher's read, and the Director's word. No email goes out without it.
- **After it's live:** `.github/workflows/newsletter-publish.yml` mirrors the published issues to the Hugging Face dataset [mcp-tool-shop/rnd-newsletter](https://huggingface.co/datasets/mcp-tool-shop/rnd-newsletter), to npm as [@rnd-news/newsletter](https://www.npmjs.com/package/@rnd-news/newsletter) and to PyPI as [mcptoolshop-rnd-newsletter](https://pypi.org/project/mcptoolshop-rnd-newsletter/) once the Pages deploy succeeds. It reads only `issue-*.md` files on main with an issue number and no `draft: true`. The npm and PyPI version is `1.<latest issue>.<revision>`; a correction to a published issue bumps the revision.
- **A quiet day gets no issue.** If one is skipped, the next issue's opening says so.

## Rules for every article

- A security finding appears only after its fix is merged and released, and never with exploit detail.
- Parked work isn't presented as active.
- Public text says "mcp-tool-shop".
- No quotes from anyone in the studio.
- Every figure is recounted from its source file, and the data is shown as a chart where a chart helps.
- The day's desk brief gives each article a list of what it must not claim.
