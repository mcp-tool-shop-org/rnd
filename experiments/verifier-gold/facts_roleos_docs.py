"""Docs vs code: role-os 2.12.0 README sentences checked against the code they describe (ce91be8).

The true claim is the README sentence (verbatim where it stands alone). The false claim is a near-miss of it,
except `docs-nine` whose false form is a real historical error: the CHANGELOG said "Eight standard controls"
until the 2.12 release pass. Natural doc errors that need several files to refute belong in the end-to-end
(retrieval) calibration, not here, because one snippet can't decide them.
"""

NAME = "role-os"

CAL = "src/calibration.mjs"
PACKS = "src/packs.mjs"
JURY = "src/specialist/jury.mjs"
CARD = "src/specialist/recipe-card.mjs"
JCMD = "src/jury-cmd.mjs"

FACTS = [
    {"id": "docs-same-runid", "file": CAL, "anchor": "if (prior[i].runId === outcome.runId) return false;",
     "before": 6, "after": 4,
     "true": "The same run id does not write a second line.",
     "false": "The same run id writes a second line, and the newest line wins.",
     "kind": "different behaviour"},
    {"id": "docs-boost", "spans": [
        {"file": CAL, "anchor": "export const MIN_CALIBRATION_RUNS = 5;", "before": 2, "after": 0},
        {"file": CAL, "anchor": "if (!(minRuns >= 0) || runs < minRuns) {", "before": 11, "after": 20},
        {"file": CAL, "anchor": "boosts[pack] = Math.min((boosts[pack] || 0) + 0.5, 2.0);", "before": 10, "after": 3},
        {"file": PACKS, "anchor": 'const boost = row && row.status === "measured" ? row.boost : 0;', "before": 3, "after": 1}],
     "true": "After a pack has at least 5 recorded outcomes, each completed run with corrections 0 adds +0.5 to that pack, capped at +2.",
     "false": "After a pack has at least 5 recorded outcomes, each completed run with corrections 0 adds +0.5 to that pack, capped at +5.",
     "kind": "changed number"},
    {"id": "docs-killswitch", "file": CAL, "anchor": 'return env.ROLEOS_NO_CALIBRATION === "1";', "before": 5, "after": 1,
     "true": "`ROLEOS_NO_CALIBRATION=1` turns the boost off.",
     "false": "`ROLEOS_NO_CALIBRATION=true` turns the boost off.",
     "kind": "changed value (the code compares to the string \"1\")"},
    {"id": "docs-panel", "file": JURY, "anchor": "const clears = nested.differenceCi !== null && nested.differenceCi.low > 0;",
     "before": 3, "after": 14,
     "true": "Keeps a panel only when the nested interval of panel minus best single lies entirely above 0.",
     "false": "Keeps a panel when the nested interval of panel minus best single includes values above 0.",
     "kind": "weakened condition"},
    {"id": "docs-nine", "file": CARD, "anchor": "export const STANDARD_CONTROLS = Object.freeze([", "before": 0, "after": 10,
     "true": "Nine standard controls, from a positive marker through reversed-correction to a natural-error check.",
     "false": "Eight standard controls, from a positive marker to a natural-error check.",
     "kind": "natural error (the pre-2.12 CHANGELOG wording)"},
    {"id": "docs-gap", "spans": [
        {"file": CARD, "anchor": "warnings mark gaps in the recipe's evidence", "before": 0, "after": 2},
        {"file": CARD, "anchor": "warnings.push(why ? `${tag}: passed without a measure — ${why}` : `${tag}: passed without a measure`);", "before": 5, "after": 1}],
     "true": "A passed control with no measure is a gap.",
     "false": "A passed control with no measure is an error.",
     "kind": "changed severity"},
    {"id": "docs-reversed", "file": CARD, "anchor": "if (!measure.ci || !(measure.ci[0] > 0.5)) {", "before": 2, "after": 4,
     "true": "`reversed-correction` passes only when its accuracy interval lies entirely above 0.5.",
     "false": "`reversed-correction` passes when its accuracy interval reaches 0.5 or more.",
     "kind": "strict vs non-strict bound"},
    {"id": "docs-out", "file": JCMD, "anchor": "body.panel_not_written", "before": 3, "after": 2,
     "true": "`--out` writes a panel file only when the verdict is `panel`.",
     "false": "`--out` writes a panel file whenever the verdict is not `insufficient-data`.",
     "kind": "broadened condition"},
]
