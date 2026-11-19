---
id: 2026-11-19-private-messages-at-a-shared-screen-what-a-deep-research-rep
title: Private messages at a shared screen: what a Deep Research report says for hot-seat play (seed 38)
date: 2026-11-19
kind: finding
relevance: act
fields: [game-design, privacy]
tags: [merchant-league, hot-seat, seed-38, harvest]
---

## Summary

Merchant League's offline Club Mode is hot-seat: four to six players share one terminal and take turns at the
keyboard, with a full-screen curtain between seats. The design called for private player-to-player messages
("whispers"), and nobody had worked out how those can stay private when everyone can see the screen. R&D put the
question to a Gemini Deep Research run. The report is `[aggregator]` AI output. Its sources are mostly manuals, forum
threads and repository issues; three arXiv identifiers were checked for existence and nothing else was.

The report's answer changed the plan. Whispers are deferred past v0.1.0. Private notes ship. The design to build
afterwards is a separate private pass, described below. Several cheap terminal habits from the report go into the
next build card regardless.

## Key points

- **The text is not the main leak.** In a negotiation game the valuable secret is who is dealing with whom. The
  report ranks what an onlooker can pick up: the sender and recipient (critical), that a message exists at all and
  any unread badge (high), its length and how long the recipient sits reading (medium to high).
- **Typing gives a message away.** A player tapping single keys is placing orders; a player typing prose for two
  minutes is writing to someone. The report's fix is cover traffic: put private notes and messages in one editor, so
  typing does not say which one it is.
- **Its recommended design is a separate private pass.** Each round starts with every seat, in order, getting the same
  fixed time (it suggests 45 to 60 seconds) at one desk that holds the secret goal, notes, inbox and composer. All
  messages are delivered together at the end of the pass. The public turn then shows no private state at all. The
  uniform timer is the point: a player with nothing to send looks the same as one who is writing.
- **The cheaper design is slow.** Messages written on your own turn and read on the recipient's next turn add no
  hand-offs. By the report's own arithmetic from seat order, one offer and counter-offer then takes one to two and a
  half rounds.
- **Swapping seats mid-turn to deliver a message is the worst option.** It shows the room who messaged whom and when,
  and adds two hand-offs per message.
- **Published games mostly avoided the problem.** By the report's account, hot-seat modes either have no private
  messages, queue them to the next turn, or were dropped: it says one strategy game disabled its chat in hot-seat,
  and that the makers of two others left hot-seat out because hidden information could not be kept off a shared
  screen. These are the claims in the report most likely to be wrong in detail, and none was checked.
- **It rejects two tempting patterns.** Reveal-while-a-key-is-held, because a terminal's standard input does not
  report key releases portably; and read-once messages, because players would retype what they read into their
  notes, which adds typing noise.
- **Terminal habits it lists.** Run in the alternate screen; at each hand-off overwrite the cells, then clear the
  screen and the scrollback; discard pending input and ignore keys for a short moment so a double key press cannot
  skip the next curtain; never write private text to the window title or the clipboard; never ring the bell on mail;
  restore the terminal on a crash.
- **What it asks that we had not.** Whether talking aloud at the table is allowed; whether a message can be
  forwarded with proof it is real (it advises against); and that a computer seat which replies instantly gives
  itself away, which batched delivery also fixes.
- **It found no study of this exact case.** No playtest or measurement of private messages on one shared terminal
  was cited. Its timings and contrast figures are its own estimates.

## Studio relevance

### What it contradicts in our design (read first)

| Finding | Merchant League today | Decision |
|---|---|---|
| Who messages whom leaks through typing, timing and unread counts, even when the text is hidden | The design listed a "Diplomatic Desk" tab on the normal turn screen for whispers of up to 120 words | Whispers are deferred past v0.1.0. The tab stays disabled. Decided by the Director, 2026-11-19 |
| A private pass with a uniform timer hides who is writing | The turn has two public passes and a curtain; the turn clock is 210 seconds | Recorded as the design for the version after v0.1.0. It adds a pass per round, so the turn clock is revisited then |
| Notes and messages in one editor give cover | Notes did not exist | Private notes ship in v0.1.0. They have no recipient, so the only thing an onlooker learns is that a player is typing |
| A double key press can skip the next player's curtain | The curtain lifts on Space then Enter; input was not flushed | The next build card discards pending input at each curtain and ignores keys for a short dead time |
| Reveal-while-held is not portable | Not built | Not built. On Windows our terminal library does report key releases, so the behaviour would differ by platform |

### Decisions and actionables

1. v0.1.0 ships private notes and no whispers.
2. The next Merchant League build card carries the input flush, the dead time, and "nothing private in the window
   title or clipboard, no bell".
3. The design document records the private-pass design in one paragraph, marked as not built.
4. Before the private pass is built: a playtest plan, since the report found no measurement of any of these patterns.

### One claim in the report that is wrong for us

The report says terminals do not report key releases. Our terminal library does on Windows: an independent review of
the turn-screen code found that key releases were being handled as presses, so that the Enter release after the
curtain placed an order for the next player. That fault is fixed. The report's conclusion still holds, for the
reason given in the table.

## Claims

- [unverified] In casual shoulder surfing, the observed person noticed in about 7% of reported incidents (Eiband et al. 2017, as cited by the report; paper not read by R&D)
- [unverified] Bystanders read more from a larger display even when the text subtends the same visual angle (Tan and Czerwinski 2003, as cited by the report; not read)
- [unverified] One strategy game disabled its chat in hot-seat play, and two others left hot-seat out because of hidden information on a shared screen (the report's reading of manuals and developer posts; not checked)
- [unverified] A turn-queued inbox costs one to two and a half rounds per offer and counter-offer in a six-seat ring (the report's own derivation from seat order)
- [unverified] A private pass of 45 to 60 seconds per seat is enough to read and write a short message (the report's estimate; no measurement cited)
- [verified] On Windows, the terminal library Merchant League uses delivers key-release events, and handling them as presses placed an order after the curtain (via: independent review of merchant-league pull request 82 by a model from another family, with a probe through the real input loop, 2026-11-19; fixed before merge)
- [verified] The three arXiv identifiers the report gives for vision and coalition papers exist with matching titles (via: arXiv index lookup of 2303.13307, 2601.18497 and 2502.16339, 2026-11-19; findings not read)

## Sources

- [aggregator] https://gemini.google.com/ — Gemini Deep Research (Gemini 4 Carbon), 2026-11-19: "Designing Private Messaging and Notes for a Shared-Terminal Hot-Seat Negotiation Game"
- [primary] https://github.com/mcp-tool-shop-org/merchant-league/pull/82 — Merchant League, the turn screens and the key-release fix
- [primary] https://arxiv.org/abs/2303.13307 — Zhang, Ma and Wang 2023, Don't Peek at My Chart (existence checked)
- [primary] https://arxiv.org/abs/2601.18497 — Cheng, Zhang, Ma and Wang 2026, BAIT (existence checked)
- [primary] https://arxiv.org/abs/2502.16339 — Kulkarni, Liu, Gaglione and Fried 2025, Dynamic Coalition Structure Detection in Natural Language-based Interactions (existence checked)
