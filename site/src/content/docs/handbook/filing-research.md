---
title: Filing research
description: The entry format, source tiers, claim confidence and links.
sidebar:
  order: 2
---

One entry per topic. Scaffold it, fill the sections in your own words, then
validate.

```bash
python -m rnd new "Singing pitch trackers" --kind finding --field audio --tag pitch
# edit entries/2026/2026-10-07-singing-pitch-trackers.md
python -m rnd check
```

## The file

```markdown
---
id: 2026-10-07-cuda-graphs        # defaults to the file name
title: CUDA Graphs
date: 2026-10-07
kind: concept
relevance: reference              # act | watch | reference
status: active                    # active | draft | superseded (optional)
fields: [gpu-computing]           # at least one; open vocabulary
tags: [cuda-graphs, pytorch]
---

## Summary
## Key points
## Studio relevance
## Claims
- [unverified] A checkable statement.
- [verified] A checked statement. (via: what checked it, date)
## Sources
- [primary] https://… — publisher
```

Frontmatter is a small YAML subset: scalars, inline `[a, b]` lists, block lists,
lists of maps and block scalars.

## Kinds

| kind | for |
|---|---|
| `finding` | a fact or result learned from a source |
| `concept` | an idea, technique or principle worth knowing |
| `release` | a product, toolkit or library release |
| `paper` | a paper or formal study |
| `tool` | an external tool, library or catalogue item |
| `catalog` | a pointer to an ingested catalogue |
| `rig-fact` | a measured fact about our own machines |
| `event` | a talk, webinar or conference |
| `question` | an open question being tracked |
| `decision` | a decision taken on the strength of research |
| `instrument` | a studio tool the seat can use (lives in `instruments/`) |

## Two questions, kept apart

**What is it?** Summary and Key points describe the knowledge as it stands,
with no studio framing.

**What does it mean for us?** Studio relevance says what to do with it, and the
`relevance` field sums that up:

- `act`: something should change because of this.
- `watch`: it may matter; revisit when it moves.
- `reference`: worth knowing; nothing to do.

## Source tiers

Every source line starts with its tier.

| tier | means | needs a URL |
|---|---|---|
| `primary` | vendor docs, papers, repos, model cards | yes |
| `secondary` | reputable write-ups of primary material | yes |
| `aggregator` | summary sites, AI search output | yes |
| `user` | supplied by a person: slides, notes, pasted text | no |
| `rig` | measured on our own machines | no |

Pasted AI-search output is `aggregator` or `user`, never `primary`. If a claim
matters, find its primary source.

## Claim confidence

| tag | means |
|---|---|
| `[unverified]` | not checked yet (the default) |
| `[verified]` | checked; must end with `(via: …)` naming what checked it and when |
| `[disputed]` | sources conflict |
| `[wrong]` | checked and false; must say what showed it, with `(via: …)` |

Verification is proportional. Check a claim when it looks wrong, when sources
conflict, or when a decision depends on it. Do not run a verifier over every
entry by default.

Interim results are fine. Say they are interim in the title and the claim, and
update the entry when the rest lands.

## Links

`[[entry-id]]` links one entry to another. `rnd show` lists each entry's
backlinks, and `rnd check` warns about a link that points at no entry.

## What `rnd check` enforces

Errors (exit 1): unreadable frontmatter, a bad `id`, a missing `title`, a
`date` not in `YYYY-MM-DD`, an unknown `kind`, `relevance` or `status`, no
`fields`, an unknown source tier, a URL-less `primary`/`secondary`/`aggregator`
source, an unknown claim tag, a `verified`/`wrong` claim without `(via: …)`, a
duplicate `id`, and an instrument missing `instrument_status` or `invoke`.

Warnings: an entry with no sources (except rig-facts and instruments), and a
`[[link]]` to no entry.

## Writing rules

- Your own words. Never paste copyrighted text into an entry.
- No home-directory paths, secrets or anything that is not ours to publish. The
  repo is public.
