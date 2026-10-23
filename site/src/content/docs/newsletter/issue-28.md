---
title: "Why our critic refuses good drafts"
description: "Our training-data critic sometimes refuses drafts that are fine. In one day we found three separate causes. The critic is never told what its three verdict labels mean. The planner sometimes hands the writer a brief that contradicts itself. And some refusals are the critic being right. Here's how we found each one, and what we're measuring next."
issue: 28
date: 2026-10-23
highlights:
  - "<strong>The writer gets definitions, the critic doesn't.</strong> The writer is told what each verdict label means. The critic is given only the three names. When two runs of the same critic disagreed, 6 of the 7 flips were between the same two labels."
  - "<strong>A brief that contradicts itself.</strong> The planner asked for 7 items whose material must be silent, while also asking that the material match the statement through an equivalent wording. On 6 of the 7 the critic said the item teaches a different lesson."
  - "<strong>Sometimes the critic is right.</strong> Graded blind, 7 of 30 test items were ambiguous. One refused draft named a product the material never mentions."
  - "<strong>Found in a dialogue.</strong> These came out of an open research conversation with an outside model, not a checklist review."
---

:::caution[Correction, 2026-10-23]
The first version of this issue said all 10 writers given the contradictory side were told to keep the material
silent. Only the 7 cannot_tell writers were. It also gave the guest-cap item as a clean example of an unmentioned
detail, though the blind grading below found that item ambiguous; it's replaced by one graded sound. The tea label's
wording is also made exact. No figure changed. The same day, the issue gained six new charts and diagrams, and a
redrawn slot chart, designed by Antigravity and checked against the data by the newsletter desk.
:::

The studio builds training data with local language models. A **writer** model drafts each item, and a **critic**
model checks it. Many items end in a verdict about a short piece of **material** (a notice, a label, a code snippet)
and a **statement** about it. There are three labels:
- **supported:** the material shows the statement is true;
- **unsupported:** the material rules it out;
- **cannot_tell:** the material says nothing either way.

The writer is told which label its item should carry. The critic reads the material and the statement and gives its
own label. When they disagree, the draft is refused. Each refusal costs a rewrite, and a refusal of a good draft also
throws away a good item. In [issue 21](/rnd/newsletter/issue-21/) the critic refused too many good items. This issue
follows the refusals, and finds three causes.

![A pipeline of planner, writer, critic and refusal, with each of the three causes marked where it enters: the contradictory brief at the planner and writer, the missing definitions at the critic, and the right refusals at the refusal itself](/rnd/charts/issue-28-causes-map.svg)

## Cause 1: the critic is never told what the labels mean

The writer's instructions spell out what cannot_tell means. For a cannot_tell item, the writer reads: "The material
must be silent on the statement: it neither shows it nor rules it out."

The critic's instructions name the three labels and nothing more. Its verdict request holds that instruction, the
material and the statement. So where "silent" ends and "rules it out" begins is left to the critic's own reading.

That's the line where its answers wobble. An earlier study, Track A, ran the critic twice over the same 102 items on
the same kind of GPU. As [issue 27](/rnd/newsletter/issue-27/) found, the seed never reached the model in those runs,
so each run sampled differently. The two runs disagreed on **7 of 102** verdicts, and **6 of the 7** were between
unsupported and cannot_tell. The seventh went from unsupported to supported.

Track A also has 43 **intact items**, which the study's design left unchanged as controls. Over the two runs, the critic refused 3 of them at least once. Two of those refusals happened in one
run only, which is noise. The third was refused both times.

![The three labels on a line. Over two runs, 28 supported, 41 unsupported and 26 cannot_tell verdicts stayed the same; 6 of the 7 flips crossed between unsupported and cannot_tell, 1 between unsupported and supported, and none between supported and cannot_tell. Of the 43 intact items, 40 were accepted both times, 2 were refused in one run and 1 in both](/rnd/charts/issue-28-track-a-flips.svg)

## Cause 2: a brief that contradicts itself

T10, the lesson in our pilot, teaches one thing: when a size, quantity or scope word in the statement differs from
the material ("at least", "exactly", "every"), check the exact size the statement claims. Each slot in the plan also
gets a **side** of that lesson to teach. One is "judges the exact size". Another is "an equivalent wording still
matches": the statement says the same thing, phrased differently.

That second side can't go with cannot_tell. If an equivalent wording in the material matches, the answer is
supported. Yet in one writing wave of 60 slots, the planner gave that side to **7 cannot_tell slots and 3 unsupported
slots**. Each of the 7 cannot_tell writers was told both to show a match and to keep the material silent. The 3
unsupported writers weren't given the silence line, and the critic voted their items T10 every time.

![How the brief contradicts itself: the side asks the writer to show a match, the verdict asks for material that is silent, and the writer escapes by asking about an unmentioned detail; on 6 of the 7 slots the critic voted T14 three times out of three, and on none did it vote T10](/rnd/charts/issue-28-contradictory-brief.svg)

The critic also votes three times on which lesson an item teaches. Here's what it said about the 12 cannot_tell slots:

![The 12 cannot_tell slots by planned side. With "an equivalent wording still matches", 6 of 7 were voted T14 and 1 had no majority. With "judges the exact size", 3 of 5 were voted T10, 1 T14, and 1 had no majority](/rnd/charts/issue-28-slot-sides.svg)

- **Planned with "an equivalent wording still matches":** on 6 of the 7, all three votes said T14, a different
  lesson: the material is silent on a detail, so don't fill it in. The writer had escaped the contradiction by asking
  about something the material never mentions:
  - how to store a cleaner;
  - a tea's caffeine, on a label whose only quantity is its weight;
  - which floor a service elevator is on;
  - more than ten utensils, on a box label that lists "Utensils" with no count.
- **Planned with "judges the exact size":** 3 of the 5 were voted T10 three times out of three. They have one shape:
  the material gives a loose amount ("a few items are redundant", "several team members raised concerns"), and the
  statement claims an exact one ("exactly three"). The other 2 weren't clean. One swapped the North Wing for the South
  Wing; the other stretched a week's schedule over a month.

The fix in the planner is simple: never pair a verdict with a side it contradicts. A second fix is an option in the
writer's brief. It asks for that loose-versus-exact shape on T10's cannot_tell items, and forbids swapped names and
unmentioned topics. Both have been agreed but not built. The option will be tested against today's brief before it
becomes the default.

## Cause 3: sometimes the critic is right

Before measuring how often the critic wrongly refuses, we needed to know which items are sound. So we built a panel
of 30 items, 10 for each label, and had them graded **blind**: the grader saw the material, the statement and the
label definitions, with no stored label and no critic output.

Two graders worked separately: Antigravity, in a fresh conversation, and the R&D seat. An item counted as **sound**
only if both graders and its stored label agreed, and neither grader flagged it as unclear. Anything else counted as
**ambiguous**, with no tiebreak.

![The 30-item panel: 23 sound (10 cannot_tell, 7 supported, 6 unsupported) and 7 ambiguous. On 2 of the ambiguous items every label agreed but a grader flagged it unclear; on 5 the labels disagreed. On 3 of the 4 Track A trap items, both graders broke the stored label](/rnd/charts/issue-28-graded-panel.svg)

One ambiguous item shows the critic doing its job. Its stored label was supported, and the critic refused it. Both
graders read cannot_tell. The statement named a payroll portal that the material never mentions. That draft's flaw
was the writer's, and the critic was right to refuse it.

Another needs a judgment the definitions don't settle. The material is a complete input check with no upper limit,
and the statement says the code caps guests at 50. If that function is the whole check, the material rules the
statement out. If it might be one piece of a larger system, the material is silent. The two graders split. No prompt
change or vote can make an item like that stable, so the bench counts such items apart.

R&D had looked at three of the 30 items before grading, so its grades on those three weren't blind. Two of them are
among the 7 ambiguous ones.

**A key file corrected before any run.** Four panel items come from Track A's traps. On 3 of the 4, both graders
disagreed with the stored label. The reason was in the study's design document, written four days earlier. Those items are deliberate traps: the deciding fact
is removed, so the true label becomes cannot_tell while the stored label keeps the old answer on purpose. The panel
builder had copied the stored label. The key file now holds the true one, and keeps the stored value alongside. The
graders' disagreement is what caught it.

## A measure we tried: hesitation

The critic thinks before it answers. We counted how often its thinking switches between the three labels, and called
it **hesitation**. On the two Track A runs:

![Median label switches per call: 12 on the 14 calls whose item flipped, 6 on the 190 that stayed the same, 13.5 on the 4 intact items refused, and 3 on the 82 accepted. Ranked by switches, the top 10 items hold 1 of the 7 flips, and the top 20 hold 4](/rnd/charts/issue-28-hesitation-spread.svg)

The gap is real, but hesitation is a weak alarm. The 10 most hesitant items held only 1 of the 7 flips, and the top
20 held 4. And it can
only find doubts the critic writes down. A confident wrong refusal leaves no trace. So it's useful as a hint, not as a
gate.

## How this was found

None of this came from a checklist. It came from an open research dialogue with Antigravity, the outside model we use
for reviews. It began as follow-up questions on issue 27's results. Antigravity lined the cannot_tell drafts up
against the plan, and spotted both the contradictory pairing and the missing definitions. It also suggested the
hesitation measure, and grading a sample blind. We checked each claim against the code and the run records. One list of item names it gave was wrong, though
its count was right. The figures in this issue are ours, recounted from those records.

Antigravity also designed this issue's charts and diagrams, over three rounds with the newsletter desk, which
recounted every number in them from the same records.

## What's next

![The planned bench, drawn dashed because it hasn't run: 30 blind-graded items, 3 seeds and 2 prompts, 180 verdict calls on one A100, with the decision rule fixed before any run](/rnd/charts/issue-28-bench-ahead.svg)

- **A 30-item bench.** It runs on one rented A100, with each of the 30 items × 3 seeds × 2 prompts: today's critic
  prompt, and the same prompt plus one sentence giving the writer's definitions. The decision rule is fixed in
  advance:
  - the definitions are recommended only if they cut false refusals on sound items by at least half;
  - and they accept no more than one extra item whose sound label they contradict.

  Not yet measured.
- **The planner fix and the writer-brief option.** Agreed, not built. The option's test measures two things: how
  often the critic votes T10, and how many drafts it accepts.

The raw notes, the bench design and the graded panel are in the studio's research library, and will move into rnd
with the bench's results.
