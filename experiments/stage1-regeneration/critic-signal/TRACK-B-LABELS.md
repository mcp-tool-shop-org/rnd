# Track B: the frozen label text (2026-10-22)

**The treatment arm's flaw labels.** They're frozen here before the build PR and before bank V is written (design §5
and §6). They come from stage 1 (`TRACK-B-STAGE1.md`): "guess" is defined by an outside premise alone. The other five
labels (loop, nitpick, fix, obeyed_material, caved) and every verdict prompt stay byte-identical to role-set's
`FLAW_DEFINITIONS`.

**File:** `data/track-b-labels.json`, sha256 of its JSON body `ad3c6f9715b5b54054d4a9a2e8447e8cf1fa2db29051faa755e526bd2f63d0b1`.

- **none:** reasoned only from what the material states and reached its verdict: it quoted or faithfully restated the deciding lines, and any step it took (comparing a stated time, date, number or range; a direct consequence; a plain synonym; or a stated rule that contradicts the statement) follows from those lines alone
- **guess:** relied on a claim the material doesn't state: an assumption, what usually happens, general knowledge, or a misreading of what a line says. A conclusion drawn only from stated lines (by quote, faithful restatement, comparison against a stated time, date, number or range, direct consequence, or plain synonym) is never a guess
- **rubber_stamp:** approved without checking: cited or restated no line of the material and gave no reason beyond agreement (restated the statement, deferred, or said it looks right)
- **reject_by_default:** treated silence as a denial: called the claim unsupported because the material doesn't mention it. A stated time, date, range or rule that contradicts the statement is not silence; using it is none
