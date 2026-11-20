"""Numbers bound to experiments/<id>/results.json, sync/check, and unbound-number warnings.

Binding syntax (HTML comment immediately after the literal number):
    84.2%<!-- rnd:experiments/e4b/results.json#accuracy:.1% -->

The literal stays directly in raw Markdown (grep, FTS5 and raw readers see `84.2%`),
GitHub strips the HTML comment, Starlight preserves it invisibly without a broken link,
and `rnd sync` / `rnd check` format the value from `results.json` using the Python format spec.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import layout, model, questions

COMMENT_RE = re.compile(r"<!--\s*rnd:([\s\S]*?)-->")
RESULTS_FILE_RE = re.compile(r"^experiments/([a-z0-9][a-z0-9._-]*)/results\.json$")
LITERAL_BEFORE_RE = re.compile(
    r"((?:(?:(?<=^)|(?<=[\s(\[{:;,=*~|\"']))[+\-\u2212])?(?<![0-9A-Za-z._])"
    r"\d(?:[\d,_]*\d)?(?:\.\d(?:[\d_]*\d)?)?(?:[eE][+\-]?\d+)?%?)$"
)
BOUND_PAIR_RE = re.compile(
    r"(?:(?:(?<=^)|(?<=[\s(\[{:;,=*~|\"']))[+\-\u2212])?(?<![0-9A-Za-z._])"
    r"\d(?:[\d,_]*\d)?(?:\.\d(?:[\d_]*\d)?)?(?:[eE][+\-]?\d+)?%?\s*<!--\s*rnd:[\s\S]*?-->"
)
UNBOUND_NUM_RE = re.compile(
    r"(?<![A-Za-z0-9_.:/\-])(?:[+\-\u2212])?\d[\d,]*(?:\.\d+)?%?(?!\.[0-9]|,\d|[A-Za-z0-9_:])"
)
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


class NumbersError(Exception):
    def __init__(self, code: str, message: str, hint: str = "", exit_code: int = 1):
        super().__init__(message)
        self.code, self.hint, self.exit_code = code, hint, exit_code


def _non_code_ranges(text: str) -> list[tuple[int, int]]:
    """Return [start, end) character ranges outside frontmatter, fenced blocks, and inline code spans."""
    lines = text.splitlines(keepends=True)
    n_lines = len(lines)
    offsets = []
    pos = 0
    for line in lines:
        offsets.append(pos)
        pos += len(line)

    i = 0
    if lines and lines[0].strip() == "---":
        for j in range(1, n_lines):
            if lines[j].strip() == "---":
                i = j + 1
                break

    plain_spans: list[tuple[int, int]] = []
    cur_start: int | None = None
    fence_char = ""
    fence_len = 0
    while i < n_lines:
        line = lines[i]
        stripped = line.lstrip()
        if fence_char:
            if stripped.startswith(fence_char * fence_len) and stripped[fence_len:].strip() == "":
                fence_char = ""
                fence_len = 0
            i += 1
            continue
        fm = FENCE_RE.match(line)
        if fm:
            if cur_start is not None:
                plain_spans.append((cur_start, offsets[i]))
                cur_start = None
            fence_char = fm.group(1)[0]
            fence_len = len(fm.group(1))
            i += 1
            continue
        if cur_start is None:
            cur_start = offsets[i]
        i += 1
    if cur_start is not None:
        plain_spans.append((cur_start, len(text)))

    out: list[tuple[int, int]] = []
    for span_start, span_end in plain_spans:
        seg = text[span_start:span_end]
        idx = 0
        chunk_start = 0
        while idx < len(seg):
            if seg[idx] != "`":
                idx += 1
                continue
            ticks = 1
            while idx + ticks < len(seg) and seg[idx + ticks] == "`":
                ticks += 1
            close = seg.find("`" * ticks, idx + ticks)
            while close != -1 and close + ticks < len(seg) and seg[close + ticks] == "`":
                # Skip longer backtick runs that do not close this inline code span.
                run_end = close + ticks
                while run_end < len(seg) and seg[run_end] == "`":
                    run_end += 1
                close = seg.find("`" * ticks, run_end)
            if close == -1:
                idx += ticks
                continue
            if idx > chunk_start:
                out.append((span_start + chunk_start, span_start + idx))
            idx = close + ticks
            chunk_start = idx
        if chunk_start < len(seg):
            out.append((span_start + chunk_start, span_end))
    return out


def parse_spec(raw_spec: str) -> tuple[str, str, str]:
    """Parse 'experiments/<id>/results.json#<key>:<format>' -> (rel_file, key, fmt)."""
    spec = raw_spec.strip()
    rel_file, sep, rest = spec.partition("#")
    if not sep or not RESULTS_FILE_RE.match(rel_file):
        raise NumbersError(
            "BAD_BINDING",
            f"invalid binding target {spec!r}",
            "use 'experiments/<id>/results.json#<key>:<format>'",
        )
    key, sep2, fmt = rest.rpartition(":")
    if not sep2 or not key.strip() or not fmt or any(ch.isspace() for ch in fmt):
        raise NumbersError(
            "BAD_BINDING",
            f"invalid key/format in binding {spec!r}",
            "end the binding with '#<key>:<format>', e.g. '#accuracy:.1%'",
        )
    return rel_file, key.strip(), fmt


def _resolve_key(data: dict, key: str):
    if key in data:
        return data[key]
    if "." in key:
        cur = data
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                raise KeyError(key)
        return cur
    raise KeyError(key)


def load_results_file(root: Path, rel_file: str, cache: dict | None = None) -> tuple[dict | None, str | None]:
    """Load and public-guard validate one experiments/<id>/results.json file."""
    if cache is not None and rel_file in cache:
        return cache[rel_file]
    path = Path(root) / rel_file
    if not path.is_file():
        res = (None, f"missing bound results file {rel_file}")
        if cache is not None:
            cache[rel_file] = res
        return res
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        res = (None, f"unreadable {rel_file}: {exc}")
        if cache is not None:
            cache[rel_file] = res
        return res
    if not isinstance(data, dict):
        res = (None, f"{rel_file} must be a JSON object")
    elif layout._machine_paths(data):
        res = (None, f"{rel_file} holds a machine path; results.json must be public-safe")
    else:
        res = (data, None)
    if cache is not None:
        cache[rel_file] = res
    return res


def format_bound_value(data: dict, rel_file: str, key: str, fmt: str) -> str:
    """Resolve `key` inside `data` and format it with `fmt`."""
    try:
        val = _resolve_key(data, key)
    except KeyError:
        raise NumbersError("MISSING_KEY", f"{rel_file} has no key {key!r}") from None
    if not isinstance(val, (int, float)) or isinstance(val, bool):
        raise NumbersError("BAD_VALUE", f"{rel_file}#{key} must be a number, got {type(val).__name__}")
    try:
        expected = format(val, fmt)
    except (ValueError, TypeError) as exc:
        raise NumbersError("BAD_FORMAT", f"invalid format {fmt!r} for {rel_file}#{key}: {exc}") from None
    m = LITERAL_BEFORE_RE.search(expected)
    if not m or m.group(1) != expected:
        raise NumbersError("BAD_FORMAT", f"formatted value {expected!r} from {fmt!r} is not a plain numeric literal")
    return expected


def find_bindings(text: str) -> list[dict]:
    """Find every `<!-- rnd:... -->` binding outside code spans, with offsets for its literal."""
    items = []
    for seg_start, seg_end in _non_code_ranges(text):
        seg = text[seg_start:seg_end]
        for cm in COMMENT_RE.finditer(seg):
            raw_spec = cm.group(1)
            prefix = seg[:cm.start()]
            lm = LITERAL_BEFORE_RE.search(prefix)
            items.append({
                "raw_spec": raw_spec.strip(),
                "literal": lm.group(1) if lm else None,
                "lit_start": seg_start + lm.start(1) if lm else None,
                "lit_end": seg_start + lm.end(1) if lm else None,
                "comment_start": seg_start + cm.start(),
            })
    return items


def default_bindable_paths(root: Path) -> list[Path]:
    """Entries, instruments, questions, site briefs, and experiment Markdown notes."""
    root = Path(root)
    paths: list[Path] = []
    paths.extend(model.entry_paths(root))
    paths.extend(questions.question_paths(root))
    briefs_dir = root / "site" / "src" / "content" / "docs" / "briefs"
    if briefs_dir.is_dir():
        paths.extend(sorted(briefs_dir.rglob("*.md")))
    exp_dir = root / "experiments"
    if exp_dir.is_dir():
        for p in sorted(exp_dir.rglob("*.md")):
            rel = p.relative_to(exp_dir)
            if "staging" not in rel.parts:
                paths.append(p)
    seen = set()
    unique = []
    for p in paths:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(p)
    return unique


def _resolve_sync_paths(root: Path, raw_paths: list[str] | None) -> list[Path]:
    root_res = Path(root).resolve()
    if not raw_paths:
        return default_bindable_paths(root_res)
    out: list[Path] = []
    seen = set()
    for raw in raw_paths:
        cand = Path(raw)
        if not cand.is_absolute():
            cwd_cand = (Path.cwd() / cand).resolve()
            cand = cwd_cand if cwd_cand.exists() else (root_res / cand).resolve()
        else:
            cand = cand.resolve()
        if not cand.exists():
            raise NumbersError("NOT_FOUND", f"no file or folder {raw!r}", "pass paths inside the library", exit_code=2)
        if not cand.is_relative_to(root_res):
            raise NumbersError("OUTSIDE_LIBRARY", f"{raw!r} is outside the library", exit_code=2)
        if cand.is_dir():
            for p in sorted(cand.rglob("*.md")):
                if p.resolve() not in seen:
                    seen.add(p.resolve())
                    out.append(p)
        else:
            if cand not in seen:
                seen.add(cand)
                out.append(cand)
    return out


def sync_files(root: Path, paths: list[str] | None = None, check: bool = False) -> dict:
    """Recompute bound literals from experiments/<id>/results.json. If check=True, change nothing."""
    root = Path(root)
    targets = _resolve_sync_paths(root, paths)
    cache: dict = {}
    inst_dir = (root / "instruments").resolve()
    pending_writes: list[tuple[Path, str, str]] = []
    changed: list[dict] = []
    total_bindings = 0

    for path in targets:
        rel = path.relative_to(root.resolve()).as_posix() if path.is_absolute() else path.as_posix()
        text = path.read_text(encoding="utf-8")
        bindings = find_bindings(text)
        if not bindings:
            continue
        replacements: list[tuple[int, int, str]] = []
        for b in bindings:
            total_bindings += 1
            if b["literal"] is None:
                raise NumbersError("BAD_BINDING", f"{rel}: bound comment has no number directly before it",
                                   "place the literal right before <!-- rnd:... -->, e.g. 84.2%<!-- rnd:... -->")
            rel_file, key, fmt = parse_spec(b["raw_spec"])
            data, err = load_results_file(root, rel_file, cache)
            if err:
                raise NumbersError("BAD_RESULTS", f"{rel}: {err}")
            expected = format_bound_value(data, rel_file, key, fmt)
            if b["literal"] != expected:
                changed.append({
                    "path": rel,
                    "results_file": rel_file,
                    "key": key,
                    "was": b["literal"],
                    "now": expected,
                })
                replacements.append((b["lit_start"], b["lit_end"], expected))
        if replacements and not check:
            if path.resolve().is_relative_to(inst_dir):
                raise NumbersError(
                    "INSTRUMENTS_PROTECTED",
                    f"refusing to modify instrument file {rel}",
                    "instrument files are edited only by the R&D seat in a reviewed diff",
                    exit_code=2,
                )
            new_text = text
            for start, end, expected in sorted(replacements, reverse=True):
                new_text = new_text[:start] + expected + new_text[end:]
            eol = "\r\n" if "\r\n" in text else "\n"
            pending_writes.append((path, new_text.replace("\r\n", "\n"), eol))

    if not check:
        for path, body, eol in pending_writes:
            with open(path, "w", encoding="utf-8", newline=eol) as fh:
                fh.write(body)

    return {
        "checked_files": len(targets),
        "bindings": total_bindings,
        "changed": changed,
        "ok": not changed if check else True,
    }


def _experiment_patterns(root: Path) -> list[tuple[str, re.Pattern]]:
    exp_base = Path(root) / "experiments"
    if not exp_base.is_dir():
        return []
    out = []
    for d in sorted(exp_base.iterdir()):
        if not d.is_dir():
            continue
        name = d.name
        if name == "charts":
            pat = re.compile(r"(?<![A-Za-z0-9._-])experiments/charts(?![A-Za-z0-9._-])")
        else:
            pat = re.compile(r"(?:experiments/)?(?<![A-Za-z0-9._-])" + re.escape(name) + r"(?![A-Za-z0-9._-])")
        out.append((name, pat))
    return out


def _unbound_numbers(text: str) -> list[str]:
    cleaned = BOUND_PAIR_RE.sub(" ", text)
    cleaned = re.sub(r"<!--[\s\S]*?-->", " ", cleaned)
    cleaned = re.sub(r"`[^`]+`", " ", cleaned)
    cleaned = re.sub(r"\]\([^)]+\)", "]()", cleaned)
    cleaned = re.sub(r"\[\[[^\]]+\]\]", " ", cleaned)
    cleaned = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", cleaned)
    cleaned = re.sub(r"\bv\d+(?:\.\d+)+\b", " ", cleaned)
    return UNBOUND_NUM_RE.findall(cleaned)


def check_all(root: Path, entries: list[model.Entry] | None = None) -> list[model.Problem]:
    """Validate experiments/*/results.json, bound numbers, and unbound numbers in experiment-backed claims."""
    root = Path(root)
    problems: list[model.Problem] = []
    cache: dict = {}

    exp_base = root / "experiments"
    if exp_base.is_dir():
        for res_path in sorted(exp_base.glob("*/results.json")):
            rel_file = res_path.relative_to(root).as_posix()
            _, err = load_results_file(root, rel_file, cache)
            if err:
                problems.append(model.Problem("error", rel_file, err))

    for path in default_bindable_paths(root):
        rel = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for b in find_bindings(text):
            if b["literal"] is None:
                problems.append(model.Problem("error", rel, "bound comment has no numeric literal directly before it"))
                continue
            try:
                rel_file, key, fmt = parse_spec(b["raw_spec"])
            except NumbersError as exc:
                problems.append(model.Problem("error", rel, str(exc)))
                continue
            data, err = load_results_file(root, rel_file, cache)
            if err:
                problems.append(model.Problem("error", rel, err))
                continue
            try:
                expected = format_bound_value(data, rel_file, key, fmt)
            except NumbersError as exc:
                problems.append(model.Problem("error", rel, str(exc)))
                continue
            if b["literal"] != expected:
                problems.append(model.Problem(
                    "error", rel,
                    f"bound number {b['literal']} differs from {rel_file}#{key} ({expected}); run `rnd sync`"))

    if entries is None:
        entries, _ = model.load_all(root)
    exp_patterns = _experiment_patterns(root)
    if exp_patterns:
        for e in entries:
            for c in e.claims:
                if c["confidence"] != "verified" or not c["via"]:
                    continue
                matched = [name for name, pat in exp_patterns if pat.search(c["via"])]
                if not matched:
                    continue
                nums = _unbound_numbers(c["text"])
                if nums:
                    preview = re.sub(r"<!--[\s\S]*?-->", "", c["text"]).strip()[:60]
                    problems.append(model.Problem(
                        "warning", e.path,
                        f"[verified] claim via experiment {matched[0]!r} has unbound number(s) "
                        f"({', '.join(nums[:3])}): {preview!r}"))
    return problems
