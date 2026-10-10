"""Charts for the bench, built only from committed receipts in this repo, so a chart can't drift from its data.

  python experiments/charts/make_charts.py

Writes SVG files and manifest.json (each input's path, git commit and sha256) into experiments/charts/, and a
copy of each SVG into site/public/charts/ for the site's briefs and newsletter.
Standard library only. CPU for a few seconds; render outside any quiet-CPU device window.

Conventions (agreed with the Publisher and ASPIRE, 2026-10-09):
- Every rate carries its n and a Wilson 95% interval, exact at the edges. Cells with n < 30 are hollow and
  marked tentative.
- Each calibration is its own series, labelled with contract, quote rule, num_predict and offrig build.
  Different calibrations are never joined by a line.
- INCOMPLETE runs show as INCOMPLETE, not as a score. No line crosses a missing cell.
- Pre-registered vs post hoc is stated on every chart.
- No home, drive or run-directory paths. Sources are repo-relative.
"""

import hashlib
import html
import json
import math
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CAL = REPO / "experiments" / "verifier-gold" / "calibration" / "results"
LADDER = REPO / "experiments" / "verifier-gold" / "math-ladder"
NPU = REPO / "experiments" / "npu-probe" / "results"
SITE_CHARTS = REPO / "site" / "public" / "charts"
CU134 = REPO / "experiments" / "cloud-cu134" / "results"
KEV = REPO / "experiments" / "kev-judge-finetune" / "env" / "README.md"
GRAPHS = REPO / "experiments" / "cuda-graphs" / "results" / "2026-10-08-llama.json"
# Receipts from other studio repos, read at a pinned commit from a sibling clone with `git show`.
JAM = {"repo": "mcp-tool-shop-org/ai-jam-sessions", "clone": REPO.parent / "ai-jam-sessions",
       "sha": "5aa092c4fe2a680968f171d78696d58e285c9982"}
EXTERNAL: dict[str, dict] = {}
Z = 1.959963984540054

INPUTS: dict[str, Path] = {}

FAMILY = {"llama3.1": "Meta Llama", "qwen3": "Qwen", "mistral-small": "Mistral", "granite4.1": "IBM Granite",
          "gemma4": "Google Gemma"}
THINK = {"llama3.1:8b": "off", "qwen3:8b": "on", "qwen3:14b": "on", "mistral-small:24b": "off",
         "granite4.1:30b": "off", "gemma4:31b": "on"}
ORDER = ["llama3.1:8b", "qwen3:8b", "qwen3:14b", "mistral-small:24b", "granite4.1:30b", "gemma4:31b"]
COLORS = {"llama3.1:8b": "#c2410c", "qwen3:8b": "#2563eb", "qwen3:14b": "#1e3a8a", "mistral-small:24b": "#b45309",
          "granite4.1:30b": "#4d7c0f", "gemma4:31b": "#7c3aed"}

CHAIN = ("chain: contract v2 · quote rule 1 · num_predict 4096 · num_ctx 16384 · "
         "offrig pre-#47 (sha256 not recorded) · tune · pre-registered")
RERUN = ("rerun: contract v2 · quote rule 2 · num_predict 12288 · num_ctx 16384 · "
         "offrig 751fb1d (sha256 6A1622C5…) · post hoc (pre-registered before its run)")

INK, MUTED, GRID, BG, RULE, BAND = "#1f2430", "#5b6272", "#e3e6ec", "#ffffff", "#b91c1c", "#f1f3f7"


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p, z2 = k / n, Z * Z
    c = (p + z2 / (2 * n)) / (1 + z2 / n)
    m = Z * ((p * (1 - p) / n + z2 / (4 * n * n)) ** 0.5) / (1 + z2 / n)
    return (0.0 if k == 0 else max(0.0, c - m), 1.0 if k == n else min(1.0, c + m))


def load(path: Path):
    INPUTS[path.relative_to(REPO).as_posix()] = path
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        return [json.loads(x) for x in text.splitlines() if x.strip()]
    if path.suffix == ".json":
        return json.loads(text)
    return text


def family(model: str) -> str:
    return FAMILY.get(model.split(":")[0], "?")


def esc(s) -> str:
    return html.escape(str(s), quote=True)


class Svg:
    def __init__(self, w: int, h: int, title: str):
        self.w, self.h, self.parts = w, h, []
        self.parts.append(f'<rect width="{w}" height="{h}" fill="{BG}"/>')
        self.text(24, 34, title, size=17, weight=600)

    def text(self, x, y, s, size=12, color=INK, anchor="start", weight=400, italic=False):
        style = ' font-style="italic"' if italic else ""
        self.parts.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}" text-anchor="{anchor}" '
                          f'font-weight="{weight}"{style}>{esc(s)}</text>')

    def line(self, x1, y1, x2, y2, color=INK, width=1.0, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" '
                          f'stroke-width="{width}"{d}/>')

    def rect(self, x, y, w, h, fill, stroke="none"):
        self.parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" '
                          f'stroke="{stroke}"/>')

    def dot(self, x, y, color, hollow=False, r=4.5, shape="circle"):
        fill = BG if hollow else color
        if shape == "diamond":
            pts = f"{x},{y - r - 1} {x + r + 1},{y} {x},{y + r + 1} {x - r - 1},{y}"
            self.parts.append(f'<polygon points="{pts}" fill="{fill}" stroke="{color}" stroke-width="1.6"/>')
        else:
            self.parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{color}" '
                              f'stroke-width="1.6"/>')

    def path(self, pts, color, width=1.8):
        d = " ".join(("M" if i == 0 else "L") + f"{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
        self.parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"/>')

    def footer(self, lines):
        y = self.h - 14 - 15 * (len(lines) - 1)
        for ln in lines:
            self.text(24, y, ln, size=10.5, color=MUTED)
            y += 15

    def save(self, name: str):
        body = "\n".join(self.parts)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
               f'height="{self.h}" font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif">\n{body}\n</svg>\n')
        (HERE / name).write_text(svg, encoding="utf-8")
        SITE_CHARTS.mkdir(parents=True, exist_ok=True)
        (SITE_CHARTS / name).write_text(svg, encoding="utf-8")  # the site serves its copy at /rnd/charts/


def panel_axis(svg, x0, x1, y0, y1, lo, hi, ticks, label, rule=None, rule_label=None, rule_side="lt"):
    """A horizontal value axis from lo..hi across x0..x1, gridlines from y0 to y1, optional rule line."""
    sx = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    if rule is not None:
        if rule_side == "lt":
            svg.rect(sx(rule), y0, x1 - sx(rule), y1 - y0, "#fdf0f0")
        else:
            svg.rect(x0, y0, sx(rule) - x0, y1 - y0, "#fdf0f0")
    for t in ticks:
        svg.line(sx(t), y0, sx(t), y1, GRID)
        svg.text(sx(t), y1 + 15, f"{t:g}", size=10, color=MUTED, anchor="middle")
    svg.text((x0 + x1) / 2, y0 - 10, label, size=11.5, weight=600, anchor="middle")
    if rule is not None:
        svg.line(sx(rule), y0, sx(rule), y1, RULE, 1.4, "5,3")
        svg.text(sx(rule), y1 + 28, rule_label, size=10, color=RULE, anchor="middle")
    return sx


# --- calibration -----------------------------------------------------------------------------------------------

def cal_row(run_dir: Path) -> dict:
    m = load(run_dir / "metrics.json")
    r = m["rows"][0]
    return {"model": m["model"], "digest": m.get("model_digest", "")[:12], "type": r["check_type"],
            "split": m["settings"]["split"], "fa": r["false_accept"], "ab": r["abstain"],
            "ba": r["decided_balanced_accuracy"], "missing": r["missing"], "passes": r["passes_default_rule"],
            "ct": r.get("cannot_tell_gold", {}).get("false_accept"), "n": r["n"]}


def cal_rows_chart(svg, top, rows, left=330):
    """Three panels (FA upper, abstain, decided BA) for a list of (label, sub, row, color, hollow) rows."""
    x = [left, left + 190, left + 230, left + 420, left + 460, left + 640]
    y0, step = top, 30
    y1 = y0 + step * len(rows)
    fa_x = panel_axis(svg, x[0], x[1], y0, y1, 0, 0.6, [0, 0.1, 0.2, 0.4, 0.6], "false accepts (Wilson 95%)",
                      0.10, "rule: upper < 0.10")
    ab_x = panel_axis(svg, x[2], x[3], y0, y1, 0, 0.5, [0, 0.1, 0.2, 0.3, 0.4, 0.5], "abstain (Wilson 95%)",
                      0.20, "rule: ≤ 0.20")
    ba_x = panel_axis(svg, x[4], x[5], y0, y1, 0.5, 1.0, [0.5, 0.6, 0.7, 0.8, 0.9, 1.0], "decided balanced accuracy",
                      0.80, "rule: ≥ 0.80", rule_side="gt")
    svg.text(x[5] + 16, y0 - 10, "missing", size=11.5, weight=600)
    svg.text(x[5] + 82, y0 - 10, "rule", size=11.5, weight=600)
    for i, (label, sub, r, color, hollow) in enumerate(rows):
        y = y0 + step * i + step / 2
        if i % 2 == 0:
            svg.rect(24, y - step / 2, x[5] + 150 - 24, step, BAND)
        svg.text(28, y - 1, label, size=12, weight=600)
        svg.text(28, y + 11, sub, size=9.5, color=MUTED)
        for sx, v in ((fa_x, r["fa"]), (ab_x, r["ab"])):
            lo, hi = min(v["low"], 0.6 if sx is fa_x else 0.5), min(v["high"], 0.6 if sx is fa_x else 0.5)
            svg.line(sx(lo), y, sx(hi), y, color, 2.2)
            svg.dot(sx(min(v["rate"], 0.6)), y, color, hollow)
        svg.text(fa_x(min(r["fa"]["high"], 0.6)) + 6, y + 4, f'{r["fa"]["high"]:.3f}', size=9.5, color=MUTED)
        svg.dot(ba_x(max(0.5, r["ba"])), y, color, hollow, shape="diamond")
        svg.text(x[5] + 30, y + 4, str(r["missing"]), size=12, anchor="middle",
                 color=RULE if r["missing"] else INK, weight=600 if r["missing"] else 400)
        svg.text(x[5] + 82, y + 4, "PASS" if r["passes"] else "fail", size=11.5,
                 color="#15803d" if r["passes"] else RULE, weight=600)
    return y1


def chart_calibration():
    chain = {}
    for d in sorted((CAL / "2026-10-09-chain").glob("cal-*-tune")):
        r = cal_row(d)
        chain[(r["model"], r["type"])] = r
    r2 = {t: cal_row(CAL / "2026-10-09-gemma-r2" / f"cal-gemma4_31b-{t}-tune") for t in ("grounded", "reasoning")}
    for ct in ("grounded", "reasoning"):
        rows = []
        for m in ORDER:
            r = chain[(m, ct)]
            rows.append((f"{m} (think {THINK[m]})", f"{family(m)} · digest {r['digest']} · chain", r, COLORS[m], False))
        rows.append(("gemma4:31b (think on)", f"Google Gemma · digest {r2[ct]['digest']} · rerun", r2[ct],
                     COLORS["gemma4:31b"], True))
        svg = Svg(1140, 92 + 30 * len(rows) + 140, f"Verifier calibration, verify:{ct}, tune split (2026-10-09)")
        svg.text(24, 54, "offrig's default rule, per model. Two calibrations, drawn as separate series: filled = the "
                 "six-model chain, hollow = the gemma rerun. They are never joined.", size=11.5, color=MUTED)
        y1 = cal_rows_chart(svg, 92, rows)
        note = {"grounded": "No model passes grounded. The rerun misses on 1 missing claim: a deterministic thinking "
                            "loop under the one-quote contract (contract v3 planned).",
                "reasoning": "The rerun passes on tune; its held-out confirmation is in reasoning-default.svg."}[ct]
        svg.text(24, y1 + 50, note, size=11.5)
        svg.footer([CHAIN, RERUN,
                    "Missing = truncated or unusable replies; the rule needs 0. Dot = observed rate, bar = Wilson 95% "
                    "interval; the rule reads the interval's upper end for false accepts.",
                    "Source: mcp-tool-shop-org/rnd experiments/verifier-gold/calibration/results/ (metrics.json per "
                    "run). Inputs pinned in experiments/charts/manifest.json."])
        svg.save(f"calibration-{ct}.svg")


def chart_reasoning_default():
    rows = []
    for split, name in (("tune", "cal-gemma4_31b-reasoning-tune"), ("held-out (spent)", "cal-gemma4_31b-reasoning-heldout")):
        r = cal_row(CAL / "2026-10-09-gemma-r2" / name)
        rows.append((f"reasoning · {split}", f"n = {r['n']} · FA {r['fa']['hits']}/{r['fa']['of']} · "
                     f"abstain {r['ab']['hits']}/{r['ab']['of']}", r, COLORS["gemma4:31b"], False))
    g = cal_row(CAL / "2026-10-09-gemma-r2" / "cal-gemma4_31b-grounded-tune")
    rows.append(("grounded · tune", f"n = {g['n']} · no default: fails on 1 missing claim", g, "#9ca3af", True))
    svg = Svg(1140, 92 + 30 * len(rows) + 150, "offrig verify default for reasoning (contract v2, think on, quote rule 2, "
              "num_ctx 16384, num_predict 12288)")
    svg.text(24, 54, "gemma4:31b (Google Gemma, digest 6316f0629137) · offrig 751fb1d · temperature 0, seed 0 · "
             "the rerun calibration, pre-registered before its run", size=11.5, color=MUTED)
    y1 = cal_rows_chart(svg, 92, rows)
    # The teacher bar is a different decision. Drawn apart, labelled as not met, so nothing reads as a teacher choice.
    x0, x1 = 330, 520
    sx = lambda v: x0 + v / 0.6 * (x1 - x0)
    svg.line(sx(0.07), 92, sx(0.07), y1, "#6b7280", 1.2, "2,3")
    svg.text(sx(0.07) - 4, y1 + 42, "distillation teacher bar (not met)", size=10, color="#6b7280", anchor="end")
    svg.text(24, y1 + 72, "Named default for reasoning only, served at exactly these settings. The held-out split was "
             "used once and is spent: a contract v3 default needs a fresh sealed split.", size=11.5)
    svg.text(24, y1 + 90, "All 4 held-out false accepts are on gold cannot_tell claims (4/21); 0/108 on gold unsupported. "
             "Grounded has no default.", size=11.5)
    svg.footer(["The teacher bar belongs to the distillation plan, a separate decision; gemma misses it "
                "(tune FA upper 0.0704 vs 0.07; held-out cannot_tell FA 19% vs 10%).",
                "Source: mcp-tool-shop-org/rnd experiments/verifier-gold/calibration/results/2026-10-09-gemma-r2/. "
                "Inputs pinned in experiments/charts/manifest.json."])
    svg.save("reasoning-default.svg")


# --- error lean (ASPIRE's view) -------------------------------------------------------------------------------

def chart_error_lean():
    rows = []
    for m in ORDER:
        tag = m.replace(":", "_")
        for ct in ("grounded", "reasoning"):
            d = CAL / "2026-10-09-chain" / f"cal-{tag}-{ct}-tune"
            sup, uns, ab = [0, 0], [0, 0], [0, 0]
            for x in load(d / "verdicts.jsonl"):
                if x["status"] != "ok":
                    continue
                g, v = x.get("gold_label"), x.get("final_verdict")
                if g == "supported":
                    sup[0] += 1; sup[1] += v == "unsupported"
                if g == "unsupported":
                    uns[0] += 1; uns[1] += v == "supported"
                if g in ("supported", "unsupported"):
                    ab[0] += 1; ab[1] += v == "cannot_tell"
            rows.append((m, ct, sup, uns, ab))
    svg = Svg(1140, 120 + 26 * len(rows) + 120, "Error lean per model: false rejects, false accepts, abstain "
              "(chain, tune, final verdict)")
    svg.text(24, 54, "POST HOC, DESCRIPTIVE: built after the results were seen, for ASPIRE's judge choice. "
             "proxy: a different task (verify:grounded / verify:reasoning, not judge:*).", size=11.5, color=RULE)
    left, top, step = 330, 100, 26
    y1 = top + step * len(rows)
    axes = [("false reject: gold supported → unsupported", left, left + 220),
            ("false accept: gold unsupported → supported", left + 260, left + 480),
            ("abstain on supported + unsupported", left + 520, left + 740)]
    sxs = [panel_axis(svg, a, b, top, y1, 0, 0.8, [0, 0.2, 0.4, 0.6, 0.8], t) for t, a, b in axes]
    for i, (m, ct, sup, uns, ab) in enumerate(rows):
        y = top + step * i + step / 2
        if i % 2 == 0:
            svg.rect(24, y - step / 2, left + 780 - 24, step, BAND)
        if ct == "grounded":
            svg.text(28, y + 4, f"{m} (think {THINK[m]})", size=12, weight=600)
        svg.text(200, y + 4, f"{family(m)} · {ct}", size=10.5, color=MUTED)
        for sx, (k, n) in zip(sxs, ((sup[1], sup[0]), (uns[1], uns[0]), (ab[1], ab[0]))):
            lo, hi = wilson(k, n)
            svg.line(sx(lo), y, sx(min(hi, 0.8)), y, COLORS[m], 2.0)
            svg.dot(sx(min(k / n, 0.8)), y, COLORS[m], hollow=n < 30)
            svg.text(sx(min(hi, 0.8)) + 5, y + 4, f"{k}/{n}", size=9, color=MUTED)
    svg.footer([CHAIN,
                "For a pair judge under AND, a false reject and an abstain both cost a matched pair (ASPIRE). "
                "The Qwen family planted the errors in some gold sets: read qwen rows with the self-preference caveat.",
                "Source: mcp-tool-shop-org/rnd experiments/verifier-gold/calibration/results/2026-10-09-chain/ "
                "(verdicts.jsonl per run). Inputs pinned in experiments/charts/manifest.json."])
    svg.save("error-lean.svg")


# --- math ladder ----------------------------------------------------------------------------------------------

def chart_ladder():
    gold = {r["id"]: r for r in load(LADDER / "ladder.jsonl")}
    levels = [f"L{i}" for i in range(1, 9)]
    W, H = 1140, 560
    svg = Svg(W, H, "Math ladder: accuracy by level, model's own verdict (2026-10-09)")
    svg.text(24, 54, "POST HOC VIEW: the pre-registered table scores offrig's final verdict, which here mostly "
             "measures the quote check. This scores the model's verdict before it.", size=11.5, color=RULE)
    x0, x1, y0, y1 = 90, 760, 90, 430
    sx = lambda i: x0 + i / 7 * (x1 - x0)
    sy = lambda v: y1 - v * (y1 - y0)
    for t in (0, 0.2, 0.4, 0.6, 0.8, 1.0):
        svg.line(x0, sy(t), x1, sy(t), GRID)
        svg.text(x0 - 10, sy(t) + 4, f"{t:.1f}", size=10, color=MUTED, anchor="end")
    svg.line(x0, sy(0.8), x1, sy(0.8), RULE, 1.2, "5,3")
    svg.text(x1, sy(0.8) - 6, "falloff line: accuracy 0.80", size=10, color=RULE, anchor="end")
    for i, lv in enumerate(levels):
        svg.text(sx(i), y1 + 18, lv, size=11, anchor="middle")
    svg.text((x0 + x1) / 2, y1 + 40, "ladder level (L1–L2, L3–L4 and L7–L8 share knob settings; L5→L6 raises units 1→2)",
             size=10.5, color=MUTED, anchor="middle")
    legend_y = 96
    for m in ORDER:
        tag = m.replace(":", "_")
        run = LADDER / "results" / "2026-10-09-ladder" / f"ladder-{tag}"
        manifest = load(run / "manifest.json")
        verdicts = load(run / "verdicts.jsonl")
        label = f"{m} (think {THINK[m]}) · {family(m)}"
        if m == "mistral-small:24b":
            # The Publisher's ruling: INCOMPLETE (1 claim stuck on an Ollama 500). Shown as INCOMPLETE, not a score.
            svg.text(790, legend_y + 4, f"{m} (think off): INCOMPLETE — 1 claim stuck, not scored", size=11,
                     color=COLORS[m], weight=600)
            legend_y += 22
            continue
        cells = {}
        for ln in verdicts:
            g = gold.get(ln["claim_id"])
            if not g or not g["ladder"]["cell"].startswith("L"):
                continue
            c = cells.setdefault(g["ladder"]["cell"], [0, 0, 0])
            if ln.get("status") == "unusable":
                c[2] += 1
                continue
            c[0] += 1
            c[1] += ln.get("model_verdict") == g["label"]
        pts, seg = [], []
        for i, lv in enumerate(levels):
            n, right, bad = cells.get(lv, [0, 0, 0])
            if not n:
                if len(seg) > 1:
                    svg.path(seg, COLORS[m])
                seg = []
                continue
            seg.append((sx(i), sy(right / n)))
            pts.append((sx(i), sy(right / n), n < 30))
        if len(seg) > 1:
            svg.path(seg, COLORS[m])
        for x, y, tent in pts:
            svg.dot(x, y, COLORS[m], hollow=tent, r=4)
        np_ = manifest["settings"].get("num_predict")
        svg.line(790, legend_y, 812, legend_y, COLORS[m], 2.5)
        svg.text(820, legend_y + 4, f"{label} · num_predict {np_}", size=11)
        legend_y += 22
    svg.text(790, legend_y + 14, "Hollow = n < 30 (tentative): gemma's L7–L8 lost", size=10.5, color=MUTED)
    svg.text(790, legend_y + 29, "5 and 10 claims to the 4096 reply cap (budget,", size=10.5, color=MUTED)
    svg.text(790, legend_y + 44, "not ability). 30 claims per level otherwise.", size=10.5, color=MUTED)
    svg.text(790, legend_y + 70, "L6 is a precision cliff: bytes→MiB answers of", size=10.5)
    svg.text(790, legend_y + 85, "7–10 digits, false claims off by exactly one.", size=10.5)
    svg.footer(["offrig calibrate, quote rule 1, num_ctx 16384, temperature 0, seed 0 · gold verified by executing "
                "the generated code where a cell looked odd (all L6 answers correct).",
                "Source: mcp-tool-shop-org/rnd experiments/verifier-gold/math-ladder/ (ladder.jsonl, "
                "results/2026-10-09-ladder/). Inputs pinned in experiments/charts/manifest.json."])
    svg.save("math-ladder.svg")


# --- loop repeats ---------------------------------------------------------------------------------------------

def chart_loops():
    text = load(CAL / "2026-10-09-gemma-r2" / "loop-repeats.txt")
    series = {}
    for line in text.splitlines():
        if line.startswith("  per-reply maxima"):
            series[current] = [v for _, v in json.loads(line.split(":", 1)[1])]
        elif line and not line.startswith(" "):
            current = line.split(":")[0]
    svg = Svg(1140, 330, "gemma4:31b thinking: the longest repeated 8-word run per reply (rerun, tune)")
    svg.text(24, 54, "POST HOC: the evidence behind offrig contract v3's loop detector (n = 8 words, k = 40). "
             "The threshold is gemma-derived; it is enabled only for models with a false-hit check.", size=11.5,
             color=RULE)
    x0, x1 = 170, 1100
    sx = lambda v: x0 + math.log10(v) / math.log10(400) * (x1 - x0)
    y_rows = {"grounded": 120, "reasoning": 190}
    for t in (1, 2, 5, 10, 20, 40, 100, 200, 400):
        svg.line(sx(t), 90, sx(t), 225, GRID)
        svg.text(sx(t), 242, str(t), size=10, color=MUTED, anchor="middle")
    svg.line(sx(40), 90, sx(40), 225, RULE, 1.4, "5,3")
    svg.text(sx(40) + 5, 100, "k = 40", size=10.5, color=RULE)
    for ct, y in y_rows.items():
        vals = series.get(ct, [])
        svg.text(28, y + 4, f"{ct} ({len(vals)} replies)", size=12, weight=600)
        counts = {}
        for v in vals:
            counts[v] = counts.get(v, 0) + 1
        for v, c in sorted(counts.items()):
            color = RULE if v >= 40 else COLORS["gemma4:31b"]
            r = 3 + 2.2 * math.sqrt(c)
            svg.dot(sx(v), y, color, r=round(r, 1))
            svg.text(sx(v), y - r - 4, str(c), size=9, color=MUTED, anchor="middle")
    svg.text(sx(307), 150, "the loop: 307", size=10.5, color=RULE, anchor="middle")
    svg.footer(["x = the highest repeat count of any 8-word sequence in one reply (log scale). Dot area ~ number of "
                "replies; the number above each dot is that count. Clean maxima: 12 (grounded), 13 (reasoning).",
                "Source: mcp-tool-shop-org/rnd experiments/verifier-gold/calibration/results/2026-10-09-gemma-r2/"
                "loop-repeats.txt (loop_repeats_posthoc.py). Inputs pinned in experiments/charts/manifest.json."])
    svg.save("loop-repeats.svg")


# --- NPU probe ------------------------------------------------------------------------------------------------

def chart_npu():
    probe = load(NPU / "2026-10-09-probe.json")
    health = load(NPU / "2026-10-09-health-after-e1-loss.json")
    hmed = {c["model"]: c["median_s"] for c in health["cases"] if c["device"] == "NPU" and c.get("median_s")}
    rows = []
    for model in ("BAAI/bge-small-en-v1.5", "BAAI/bge-base-en-v1.5", "cross-encoder/nli-deberta-v3-base"):
        for batch in (1, 8):
            cpu = next((c for c in probe["cases"] if c["model"] == model and c["device"] == "CPU" and c.get("batch") == batch), None)
            npu = [c for c in probe["cases"] if c["model"] == model and c["device"] == "NPU"]
            npu = next((c for c in npu if c.get("batch") == batch), None) or (
                next((c for c in npu if c.get("error")), None) if batch == 8 else None)
            rows.append((model, batch, cpu, npu))
    svg = Svg(1140, 120 + 34 * len(rows) + 110, "Intel NPU vs CPU: median seconds per call, static shape 512 tokens "
              "(OpenVINO 2026.4.1)")
    svg.text(24, 54, "PRE-REGISTERED PROBE (2026-10-09) plus the health check run after switchyard E1's device loss. "
             "Lower is faster. Parity is the NPU output against the CPU's.", size=11.5, color=MUTED)
    x0, x1, top, step = 400, 1000, 96, 34
    sx = lambda v: x0 + (math.log10(v) + 2) / 2.5 * (x1 - x0)
    y1 = top + step * len(rows)
    for t in (0.01, 0.03, 0.1, 0.3, 1, 3):
        svg.line(sx(t), top, sx(t), y1, GRID)
        svg.text(sx(t), y1 + 15, f"{t:g} s", size=10, color=MUTED, anchor="middle")
    for i, (model, batch, cpu, npu) in enumerate(rows):
        y = top + step * i + step / 2
        if i % 2 == 0:
            svg.rect(24, y - step / 2, x1 + 120 - 24, step, BAND)
        if batch == 1:
            svg.text(28, y + 4, model.split("/")[1], size=12, weight=600)
        svg.text(260, y + 4, f"batch {batch}", size=11, color=MUTED)
        if cpu:
            svg.dot(sx(cpu["median_s"]), y, "#6b7280")
        if npu and npu.get("median_s"):
            svg.dot(sx(npu["median_s"]), y, "#0f766e")
            par = npu.get("min_cosine_vs_cpu")
            par = f"cos ≥ {par}" if par is not None else ("argmax agrees" if npu.get("argmax_agrees_with_cpu") else "")
            svg.text(x1 + 10, y + 4, par, size=10, color=MUTED)
        elif npu and npu.get("error"):
            svg.text(sx(0.3), y + 4, "NPU: hang/error at batch 8 (recovered); no time", size=10.5, color=RULE)
        if batch == 1 and model in hmed:
            svg.dot(sx(hmed[model]), y, "#0f766e", hollow=True, shape="diamond", r=4)
    ly = y1 + 40
    svg.dot(40, ly, "#6b7280"); svg.text(52, ly + 4, "CPU (Core Ultra 9 285K)", size=11)
    svg.dot(230, ly, "#0f766e"); svg.text(242, ly + 4, "NPU (Intel AI Boost), probe", size=11)
    svg.dot(440, ly, "#0f766e", hollow=True, shape="diamond", r=4); svg.text(452, ly + 4, "NPU, health check after the E1 loss (passed)", size=11)
    svg.footer(["One run per cell; median of the timed calls. The CPU batch-8 medians are noisy (bge-small best 0.42 s "
                "vs median 1.64 s). The NPU does not use the RTX 5090; OpenVINO's GPU devices are excluded.",
                "Source: mcp-tool-shop-org/rnd experiments/npu-probe/results/ (2026-10-09-probe.json, "
                "2026-10-09-health-after-e1-loss.json). Inputs pinned in experiments/charts/manifest.json."])
    svg.save("npu-vs-cpu.svg")


# --- CUDA 13.4 ------------------------------------------------------------------------------------------------

def _hbar_chart(name, title, subtitle, rows, lo, hi, ticks, unit, gate=None, gate_label="", log=False, footer=()):
    """Horizontal dots on a shared axis. rows: (label, sublabel, value or None, color, note)."""
    step, top = 30, 96
    svg = Svg(1140, top + step * len(rows) + 90 + 15 * len(footer), title)
    svg.text(24, 54, subtitle, size=11.5, color=MUTED)
    x0, x1 = 380, 1000
    f = (lambda v: math.log10(v)) if log else (lambda v: v)
    sx = lambda v: x0 + (f(v) - f(lo)) / (f(hi) - f(lo)) * (x1 - x0)
    y1 = top + step * len(rows)
    for t in ticks:
        svg.line(sx(t), top, sx(t), y1, GRID)
        svg.text(sx(t), y1 + 15, f"{t:g}{unit}", size=10, color=MUTED, anchor="middle")
    if gate is not None:
        svg.line(sx(gate), top, sx(gate), y1, RULE, 1.4, "5,3")
        svg.text(sx(gate), y1 + 30, gate_label, size=10, color=RULE, anchor="middle")
    for i, (label, sub, v, color, note) in enumerate(rows):
        y = top + step * i + step / 2
        if i % 2 == 0:
            svg.rect(24, y - step / 2, x1 + 110 - 24, step, BAND)
        svg.text(28, y - 1, label, size=12, weight=600)
        svg.text(28, y + 11, sub, size=9.5, color=MUTED)
        if v is not None:
            svg.line(sx(lo), y, sx(v), y, color, 2.0)
            svg.dot(sx(v), y, color)
        svg.text((sx(v) if v is not None else x0) + 10, y + 4, note, size=10.5, color=MUTED)
    svg.footer(list(footer))
    svg.save(name)


def chart_cuda():
    text = load(KEV)
    first = re.search(r"\| median step \| ≤ 6\.55 s \| ([\d.]+) \| ([\d.]+) ✗ \| \*\*([\d.]+)\*\* \|", text)
    final = re.search(r"\| median step \| ≤ 6\.55 s \| ([\d.]+) \| ([\d.]+) \| \*\*([\d.]+)\*\* \|", text)
    assert first and final, "Kev README's median-step tables changed; update the parser"
    ref, nofla, cu134 = (float(x) for x in first.groups())
    assert float(final.group(1)) == ref and float(final.group(2)) == cu134
    cc1d = float(final.group(3))
    _hbar_chart("cuda-kev-band.svg", "Kev judge fine-tune: median step time by environment (RTX 5090, WSL)",
                "Measured against a band fixed before the run (≤ 1.25× the CUDA 12.8 reference). Lower is faster.",
                [("CUDA 12.8 reference", "torch cu128", ref, "#6b7280", f"{ref:.2f} s"),
                 ("CUDA 13.4, first try", "missing flash-linear-attention", nofla, RULE, f"{nofla:.2f} s · FAILED the speed gate"),
                 ("CUDA 13.4", "torch 2.16.0.dev20261008+cu134", cu134, "#2563eb", f"{cu134:.2f} s · 149/149 agree with 12.8"),
                 ("CUDA 13.4 + causal-conv1d", "kernel built for sm_120", cc1d, "#15803d", f"{cc1d:.2f} s · 149/149 agree with 12.8")],
                0, 20, [0, 5, 10, 15, 20], " s", gate=6.55, gate_label="speed gate ≤ 6.55 s",
                footer=["The gain to 4.80 s comes from the causal-conv1d kernel, not from CUDA 13.4: plain 13.4 is a little slower than 12.8.",
                        "Single 30-step smokes per environment. Source: mcp-tool-shop-org/rnd experiments/kev-judge-finetune/env/README.md (its median-step tables).",
                        "Inputs pinned in experiments/charts/manifest.json."])
    g = load(GRAPHS)
    rows = []
    for form, d in g["forms"].items():
        ok = d["exact"]["pass"]
        rows.append((form, "train, graphed vs original", d["speedup_train"]["graphed"], "#7c3aed",
                     f'{d["speedup_train"]["graphed"]:.1f}×' + ("" if ok else " · exact check failed (optimizer, see caveat)")))
    _hbar_chart("cuda-graphs.svg", "CUDA graphs on aspire-si critic heads: training speed-up (RTX 5090)",
                f'Median of seeds 42–44; {g["torch"]}. Speed-up = original time / graphed time. All five keep their outcome.',
                rows, 1, 40, [1, 2, 5, 10, 20, 40], "×", log=True,
                footer=["advocate:mean's exact-match failure comes from the optimizer the graph needs (capturable AdamW); eager with the same optimizer matches exactly (diagnostic not yet committed).",
                        "Source: mcp-tool-shop-org/rnd experiments/cuda-graphs/results/2026-10-08-llama.json. Inputs pinned in experiments/charts/manifest.json."])
    pods = []
    for fname, label in (("2026-10-08-a100-probe.log", "A100, host driver only"), ("2026-10-08-a100-compat.log", "A100 + cuda-compat-13-4"),
                         ("2026-10-08-b200-compat.log", "B200 + cuda-compat-13-4")):
        line = next(x for x in load(CU134 / fname).splitlines() if x.startswith("PROBE-JSON "))
        pods.append((label, json.loads(line[len("PROBE-JSON "):])))
    rows = []
    for check, key, name in (("cudnn_conv", "max_abs_err", "cuDNN convolution"), ("sdpa_flash", "max_abs_err", "flash attention (SDPA)")):
        for label, d in pods:
            rows.append((name, label, d[check][key], "#0f766e", f'{d[check][key]:.2e}'))
    for label, d in pods:
        lt = d["lora_train"]
        first_last = (lt.get("loss_first"), lt.get("loss_last"))
        if first_last[0] is None:
            m = re.search(r"([\d.]+) -> ([\d.]+)", lt.get("error", ""))
            first_last = (float(m.group(1)), float(m.group(2))) if m else (None, None)
        rows.append(("30-step LoRA loss", label, None, "#0f766e",
                     f"{first_last[0]:.4f} → {first_last[1]:.4f}" + ("" if lt["ok"] else " (probe's 20% bound was a guess; loss fell)")))
    _hbar_chart("cuda-probe.svg", "CUDA 13.4 nightly on RunPod CUDA 13.0 hosts: numerical checks (one run per pod)",
                "Max absolute error against reference. Every check ran; the only 'fail' was the A100 LoRA bound, a probe artefact.",
                rows, 1e-7, 1e-1, [1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1], "", log=True,
                footer=["Wall times are not charted: first runs, cold caches, network filesystem. The B200 reported 2 × 70 SMs against 148: unexplained.",
                        "Source: mcp-tool-shop-org/rnd experiments/cloud-cu134/results/ (PROBE-JSON lines). Inputs pinned in experiments/charts/manifest.json."])


# --- vocal timing and pitch (ai-jam-sessions) -----------------------------------------------------------------

def load_external(src: dict, path: str):
    """A committed file from another studio repo, at a pinned commit. None if the clone isn't on this machine."""
    if not (src["clone"] / ".git").exists():
        return None
    out = subprocess.run(["git", "show", f'{src["sha"]}:{path}'], cwd=src["clone"], capture_output=True, check=True)
    EXTERNAL[f'{src["repo"]}@{src["sha"][:10]}:{path}'] = {"sha256": hashlib.sha256(out.stdout).hexdigest()}
    return json.loads(out.stdout.decode("utf-8"))


SONGS = [("amazing-grace-new-britain", "Amazing Grace"), ("america-the-beautiful-materna", "America the Beautiful"),
         ("battle-hymn-of-the-republic", "Battle Hymn of the Republic")]


def chart_vocal():
    data = []
    for slug, name in SONGS:
        base = f"scores/receipts/{slug}/sung-2026-10-08/"
        r, p = load_external(JAM, base + "receipt.json"), load_external(JAM, base + "pitch.json")
        if r is None or p is None:
            print("skip vocal charts: ai-jam-sessions clone not found")
            return
        data.append((name, r, p))
    # Timing: |onset error| histogram per song, against the 40 ms gate.
    bins = [0, 10, 20, 30, 40, 60, 80, 120, 200]
    svg = Svg(1140, 120 + 150 * len(data) + 70, "Sung hymns: vowel-onset timing error per syllable (published renders, 2026-10-08)")
    svg.text(24, 54, "MEASURED. |onset error| = distance from the score's beat to the detected vowel onset. Gate: 40 ms. "
             "Syllables with no dated onset are counted by reason, not drawn.", size=11.5, color=MUTED)
    for k, (name, r, _) in enumerate(data):
        top = 90 + 150 * k
        errs = [abs(t["err_ms"]) for t in r["table"] if t.get("err_ms") is not None]
        passed = sum(1 for t in r["table"] if t.get("pass"))
        counts = [0] * len(bins)
        for e in errs:
            i = next((j for j in range(len(bins) - 1) if bins[j] <= e < bins[j + 1]), len(bins) - 1)
            counts[i] += 1
        med = sorted(errs)[len(errs) // 2] if errs else 0
        svg.text(28, top + 16, name, size=13, weight=600)
        svg.text(28, top + 34, f"{passed}/{len(r['table'])} syllables pass · median {med:.1f} ms", size=10.5, color=MUTED)
        reasons = {}
        for t in r["table"]:
            if t.get("reason") != "ok":
                key = t["reason"].split(":")[0]
                reasons[key] = reasons.get(key, 0) + 1
        for j, (key, c) in enumerate(sorted(reasons.items(), key=lambda x: -x[1])):
            svg.text(28, top + 52 + 14 * j, f"{key}: {c}", size=10, color=MUTED)
        x0, w, hmax = 330, 70, 110
        cmax = max(counts) or 1
        for j, c in enumerate(counts):
            hgt = c / cmax * hmax
            x = x0 + j * (w + 6)
            svg.rect(x, top + hmax + 10 - hgt, w, hgt, "#2563eb" if (j < len(bins) - 1 and bins[j + 1] <= 40) else "#9ca3af")
            svg.text(x + w / 2, top + hmax + 4 - hgt, str(c), size=10, color=MUTED, anchor="middle")
            lab = f"{bins[j]}–{bins[j + 1]}" if j < len(bins) - 1 else f"≥{bins[-1]}"
            svg.text(x + w / 2, top + hmax + 24, lab + " ms", size=9.5, color=MUTED, anchor="middle")
        gx = x0 + 4 * (w + 6) - 3
        svg.line(gx, top + 4, gx, top + hmax + 12, RULE, 1.4, "5,3")
        svg.text(gx + 4, top + 12, "40 ms gate", size=10, color=RULE)
    svg.footer(["Blue = within the 40 ms gate. 'no-rise-in-window' syllables are short notes that ride the time warp by design; "
                "the vowel-onset aligner is a second instrument that can rescue a syllable but never fails one alone (its own validation is interim).",
                f"Source: {JAM['repo']} @ {JAM['sha'][:10]}, scores/receipts/<song>/sung-2026-10-08/receipt.json (field guide: scores/receipts/README-sung-2026-10-08.md)."])
    svg.save("vocal-timing.svg")
    # Pitch: each note's median cents off, against the 25 / 50 cent lines.
    svg = Svg(1140, 120 + 170 * len(data) + 70, "Sung hymns: pitch per note, median cents from the score (published renders, 2026-10-08)")
    svg.text(24, 54, "MEASURED. FCPE tracker with a pYIN recheck. Each dot is one sung note, judged on its steady middle; "
             "warn at ±25 cents, fail at ±50.", size=11.5, color=MUTED)
    col = {"PASS": "#15803d", "WARN": "#b45309", "FAIL": RULE}
    for k, (name, _, p) in enumerate(data):
        top = 90 + 170 * k
        rows = [x for x in p["rows"] if x.get("cents_median") is not None and x["status"] in col]
        n_ok = sum(1 for x in p["rows"] if x["status"] in ("PASS", "WARN"))
        svg.text(28, top + 16, name, size=13, weight=600)
        svg.text(28, top + 34, f"{n_ok}/{len(p['rows'])} notes pass or warn", size=10.5, color=MUTED)
        svg.text(28, top + 50, f"global offset {p['global_offset_cents']} c · scatter SD {p['scatter_sd_cents']} c", size=10.5, color=MUTED)
        midis = [x["midi"] for x in rows]
        lo, hi = min(midis) - 1, max(midis) + 1
        x0, x1, ymid, scale = 330, 1100, top + 75, 1.0
        sx = lambda m: x0 + (m - lo) / (hi - lo) * (x1 - x0)
        sy = lambda c: ymid - max(-120, min(120, c)) * 0.55
        for c, color in ((0, GRID), (25, "#f2d4a5"), (-25, "#f2d4a5"), (50, "#f3b4b4"), (-50, "#f3b4b4")):
            svg.line(x0, sy(c), x1, sy(c), color, 1)
            svg.text(x0 - 6, sy(c) + 3, f"{c:+d}" if c else "0", size=9, color=MUTED, anchor="end")
        for m in range(lo + 1, hi):
            if m % 2 == 0:
                svg.text(sx(m), ymid + 82, f"midi {m}", size=8.5, color=MUTED, anchor="middle")
        for x in rows:
            svg.dot(sx(x["midi"]), sy(x["cents_median"]), col[x["status"]], r=2.6)
    svg.footer(["Unvoiced and untrackable notes are counted in the denominator but not drawn. Values beyond ±120 cents are pinned to the edge.",
                f"Source: {JAM['repo']} @ {JAM['sha'][:10]}, scores/receipts/<song>/sung-2026-10-08/pitch.json."])
    svg.save("vocal-pitch.svg")


# --- thinking off vs on (pre-registered rnd acb333d; primary view: the model's own verdict) ----------------------

def verdict_stats(path: Path) -> dict:
    """Model-verdict scoring on one run: FA on gold unsupported, FR on gold supported, cannot_tell rate, seconds."""
    sup = uns = fa = fr = ct = n = bad = 0
    secs = []
    for x in load(path):
        if x["status"] != "ok":
            bad += 1
            continue
        n += 1
        g, v = x.get("gold_label"), x.get("model_verdict")
        secs.append(x.get("wall_seconds") or 0)
        ct += v == "cannot_tell"
        if g == "unsupported":
            uns += 1; fa += v == "supported"
        if g == "supported":
            sup += 1; fr += v == "unsupported"
    secs.sort()
    return {"fa": (fa, uns), "fr": (fr, sup), "ct": (ct, n), "sec": secs[len(secs) // 2] if secs else 0, "bad": bad}


def chart_thinking():
    off_dir = CAL / "2026-10-09-thinking-off"
    if not off_dir.is_dir():
        print("skip thinking chart: results/2026-10-09-thinking-off not committed yet")
        return
    on_dirs = {"qwen3:8b": CAL / "2026-10-09-chain", "qwen3:14b": CAL / "2026-10-09-chain",
               "gemma4:31b": CAL / "2026-10-09-gemma-r2"}
    rows = []
    for m in ("qwen3:8b", "qwen3:14b", "gemma4:31b"):
        tag = m.replace(":", "_")
        for ct in ("grounded", "reasoning"):
            off = off_dir / f"cal-{tag}-{ct}-tune" / "verdicts.jsonl"
            on = on_dirs[m] / f"cal-{tag}-{ct}-tune" / "verdicts.jsonl"
            if not off.is_file():
                continue
            rows.append((m, ct, verdict_stats(on), verdict_stats(off)))
    if not rows:
        return
    svg = Svg(1140, 130 + 52 * len(rows) + 100, "Thinking on vs off, same model, same tune claims (model's own verdict)")
    svg.text(24, 54, "POST HOC (pre-registered before its runs, rnd acb333d). Filled = think on, hollow = think off. "
             "Model verdict before offrig's quote check, because the on-runs used older quote rules and builds.",
             size=11.5, color=RULE)
    left, top, step = 300, 104, 52
    y1 = top + step * len(rows)
    axes = [("false accept on gold unsupported", left, left + 200, 0, 0.6),
            ("false reject on gold supported", left + 240, left + 440, 0, 0.6),
            ("cannot_tell rate", left + 480, left + 680, 0, 0.6)]
    sxs = [panel_axis(svg, a, b, top, y1, lo, hi, [0, 0.2, 0.4, 0.6], t) for t, a, b, lo, hi in axes]
    svg.text(left + 730, top - 10, "median s / claim", size=11.5, weight=600)
    for i, (m, ct, on, off) in enumerate(rows):
        y = top + step * i + step / 2
        if i % 2 == 0:
            svg.rect(24, y - step / 2, left + 840 - 24, step, BAND)
        svg.text(28, y - 2, f"{m} · {ct}", size=12, weight=600)
        svg.text(28, y + 12, f"{family(m)} · unusable on {on['bad']} / off {off['bad']}", size=9.5, color=MUTED)
        for sx, key in zip(sxs, ("fa", "fr", "ct")):
            for st, dy, hollow in ((on, -7, False), (off, 7, True)):
                k, n = st[key]
                lo, hi = wilson(k, n)
                svg.line(sx(min(lo, 0.6)), y + dy, sx(min(hi, 0.6)), y + dy, COLORS[m], 1.8)
                svg.dot(sx(min(k / n if n else 0, 0.6)), y + dy, COLORS[m], hollow=hollow, r=3.8)
        svg.text(left + 740, y - 3, f"on  {on['sec']:.1f} s", size=10.5)
        svg.text(left + 740, y + 11, f"off {off['sec']:.1f} s", size=10.5, color=MUTED)
    svg.footer(["On-runs: qwen3 from the chain (quote rule 1, num_predict 4096, older offrig); gemma4:31b from the rerun "
                "(quote rule 2, num_predict 12288, 751fb1d). Off-runs: offrig 9b6527f, same num_predict per model, num_ctx 16384.",
                "Seconds per claim are wall time on the RTX 5090, one run each. Wilson 95% intervals. "
                "Source: mcp-tool-shop-org/rnd experiments/verifier-gold/calibration/results/. Inputs pinned in experiments/charts/manifest.json."])
    svg.save("thinking-off-vs-on.svg")


def manifest():
    out = {}
    for rel, p in sorted(INPUTS.items()):
        try:
            commit = subprocess.run(["git", "log", "-1", "--format=%h", "--", rel], cwd=REPO, capture_output=True,
                                    text=True, check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            commit = ""
        out[rel] = {"commit": commit or "uncommitted", "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    (HERE / "manifest.json").write_text(json.dumps({"repo": "mcp-tool-shop-org/rnd", "inputs": out,
                                                    "external": EXTERNAL}, indent=1) + "\n", encoding="utf-8")


def main():
    chart_calibration()
    chart_reasoning_default()
    chart_error_lean()
    chart_ladder()
    chart_loops()
    chart_npu()
    chart_cuda()
    chart_vocal()
    chart_thinking()
    manifest()


if __name__ == "__main__":
    main()
