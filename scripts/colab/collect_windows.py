#!/usr/bin/env python3
"""Collect the Publisher's Colab receipts into a public, scrubbed data folder.

  python scripts/colab/collect_windows.py --src <receipts/colab dir> --out experiments/colab-golden-path/data

Reads the source folder only; never modifies it. Stdlib only.
Writes: windows.csv, windows/<folder>/ (small text records), MANIFEST.tsv, units-ledger.md.
Exits 1 (naming the file, never printing the match) if a token-shaped string survives scrubbing.
"""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
from datetime import datetime

MAX_COPY = 200 * 1024
NOCOPY_DIRS = {"build", "upload", "token-scope-check", "convert"}
COPY_NAME = re.compile(
    r"^(pin-result[\w.-]*\.json|gate\.jsonl|launch[\w.-]*\.sh|run[\w.-]*\.sh|smoke-report\.txt"
    r"|result[\w.-]*\.json|outcome\.json|[\w.-]+\.md)$")
# R&D's classification where the keyword rules can't see the cause (2026-10-18). A window's own outcome.json, written
# at close-out by the Publisher, wins over both.
OUTCOMES = ("results", "partial", "lost-vm", "cap-stop", "tooling-fault", "not-assigned", "test")
OUTCOME_OVERRIDES = {
    "10c": ("tooling-fault", "conversions reproduced, then the first wave failed: rnd's package lacked the proxy module"),
    "11a": ("tooling-fault", "the cap watcher counted both 11a's and 11b's sessions and stopped it early"),
    "11b": ("tooling-fault", "the cap watcher counted both 11a's and 11b's sessions and stopped it early"),
}
TOP_COPY = {"highmem-rate-probe.txt"}  # top-level files that are copied (to windows/_top/)

# ---------------------------------------------------------------- scrubbing
PATH_RES = [
    re.compile(r"/mnt/[a-z](?:/[^\s\"'`,;)\]>]*)?"),
    re.compile(r"/home/[A-Za-z0-9_.-]+(?:/[^\s\"'`,;)\]>]*)?"),
    re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/][^\s\"'`,;)\]>]*"),
]
TOKEN_RES = [re.compile(r"hf_[A-Za-z0-9]{30,}"), re.compile(r"ya29\.")]


def _path_sub(m):
    s = m.group(0)
    tail = ""
    while s and s[-1] in ":.":
        tail = s[-1] + tail
        s = s[:-1]
    norm = s.replace("\\\\", "/").replace("\\", "/")
    i = norm.find("receipts/colab/")
    return (norm[i + len("receipts/colab/"):] if i >= 0 else "<path>") + tail


# The private names to scrub (account, private repo, user name) are never written in this public file: they come from
# a JSON file outside the repo, {"<term>": "<replacement>", ...}, default ~/.config/rnd/collect-scrub.json.
PRIVATE_TERMS: list = []


def load_private_terms(path: str) -> list:
    if not os.path.exists(path):
        print(f"REFUSED: no private scrub terms at {path}; the collector won't write public data without them",
              file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        terms = json.load(f)
    return sorted(terms.items(), key=lambda kv: -len(kv[0]))  # longest first: a repo id before the account in it


def scrub(text):
    for rx in PATH_RES:
        text = rx.sub(_path_sub, text)
    for term, repl in PRIVATE_TERMS:
        text = re.sub(r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])", repl, text)
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "<email>", text)
    text = re.sub(r"m-s-[a-z0-9-]+", "<session>", text)
    return text


def token_hit(text):
    return any(rx.search(text) for rx in TOKEN_RES)


# ---------------------------------------------------------------- ledger
def expand_keys(cell):
    keys = []
    for part in re.split(r"\s*[+,]\s*", cell.strip()):
        if not part:
            continue
        if "/" in part:
            base, rest = part.split("/", 1)
            m = re.match(r"^(.*?)([a-z])$", base)
            if m:
                keys += [m.group(1) + m.group(2)] + [m.group(1) + c for c in rest.split("/")]
                continue
        keys.append(part)
    return keys


def parse_ledger(text):
    rows = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or cells[0] == "Window" or set(cells[0]) <= set("-: "):
            continue
        for k in expand_keys(cells[0]):
            rows[k] = {"keys": expand_keys(cells[0]), "what": cells[1], "start": cells[2],
                       "end": cells[3], "spent": cells[4]}
    return rows


def segment_for(key, what):
    """For shared rows written '...: 8 = q6k, ...; 7b = critic-control, ...' return this key's part."""
    m = re.search(r"(?:^|[:;]\s*)" + re.escape(key) + r"\s=\s([^;]*)", what)
    if m and re.search(r"\S+\s=\s", what):
        return key + " = " + m.group(1).strip()
    return what


def fnum(s):
    m = re.search(r"\d+(?:\.\d+)?", s or "")
    return float(m.group(0)) if m else None


def spent_for(key, row):
    cell = row["spent"]
    m = re.search(r"\b" + re.escape(key) + r"\s*[≈~]\s*(\d+(?:\.\d+)?)", cell)
    if m and len(row["keys"]) > 1:
        return float(m.group(1)), "estimate"
    v = fnum(cell)
    if v is None:
        return None, ""
    if "×" in cell:
        return v, "rate_x_runtime"
    if "≈" in cell or "~" in cell:
        return v, "estimate"
    if fnum(row["start"]) is not None:
        return v, "balance"
    return v, ""


# ---------------------------------------------------------------- classes
RULES = [  # (class, keywords) applied in order to the lowercased ledger text
    ("lost-vm", ["dropped the vm", "pruned", "lost its connection", "stopped receiving", "session_terminated"]),
    ("cap-stop", ["hit the cap", "hit its cap", "cut off by"]),
    ("partial", ["accepted", "both conversions reproduced", "stopped at the fit check", "stopped after",
                 "stopped while"]),
    ("tooling-fault", ["not forwarded", "lacks the proxy", "nameerror", "my input error", "pin_window defect",
                       "same cap fault", "refused at start"]),
    ("results", ["reproduce", "fits", "pinned and fit", "both critics pass", "pass"]),
]


def classify(text, is_test):
    t = text.lower()
    if "not assigned" in t:
        return "not-assigned", "not assigned"
    if is_test:
        return "test", "stub/CPU/measure"
    for cls, kws in RULES:
        for kw in kws:
            if kw in t:
                return cls, kw
    return "", ""


# ---------------------------------------------------------------- helpers
def read_text(p):
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def load_json(p):
    try:
        return json.loads(read_text(p))
    except Exception:
        return None


def hash_file(p):
    h = hashlib.sha256()
    n = 0
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
            n += len(b)
    return h.hexdigest(), n


def copy_decision(rel, size):
    parts = rel.split("/")
    name = parts[-1]
    if len(parts) == 1:
        if name in TOP_COPY:
            return True, "top-level small record"
        return False, "top-level file, hash only"
    if any(p in NOCOPY_DIRS for p in parts[:-1]):
        d = next(p for p in parts[:-1] if p in NOCOPY_DIRS)
        return False, ("token-scope-check: hash only" if d == "token-scope-check" else "under " + d + "/")
    if len(parts) > 2:
        return False, "subdirectory"
    low = name.lower()
    if low.endswith((".tar", ".tar.gz", ".tgz", ".gguf", ".gz")) or ".gz.part" in low:
        return False, "archive/binary"
    if low == "llama-server":
        return False, "binary"
    if low.endswith(".log") or low.startswith("exec-"):
        return False, "log, hash only"
    if low.endswith(".jsonl") and low != "gate.jsonl":
        return False, "draft jsonl"
    if not COPY_NAME.match(name):
        return False, "not on copy list"
    if size > MAX_COPY:
        return False, "over 200 KB"
    return True, "small text record"


def short_purpose(body):
    for mm in re.finditer(r":\s", body):
        if mm.start() >= 12:
            return body[:mm.start()]
    return body


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--terms", default=os.path.join(os.path.expanduser("~"), ".config", "rnd", "collect-scrub.json"))
    a = ap.parse_args()
    src, out = a.src, a.out
    PRIVATE_TERMS[:] = load_private_terms(a.terms)

    files = []
    for root, dirs, fs in os.walk(src):
        dirs.sort()
        for f in sorted(fs):
            files.append(os.path.relpath(os.path.join(root, f), src).replace(os.sep, "/"))
    sizes = {r: os.path.getsize(os.path.join(src, r)) for r in files}

    outputs = {}
    copied = {}
    for r in files:
        ok, why = copy_decision(r, sizes[r])
        copied[r] = (ok, why)
        if ok:
            dest = ("windows/_top/" + r) if "/" not in r else ("windows/" + r)
            outputs[dest] = scrub(read_text(os.path.join(src, r)))
    ledger_raw = read_text(os.path.join(src, "units-ledger.md"))
    outputs["units-ledger.md"] = scrub(ledger_raw)
    copied["units-ledger.md"] = (True, "scrubbed copy at units-ledger.md")

    ledger = parse_ledger(ledger_raw)
    earlier = dict((k, float(v)) for k, v in re.findall(r"window (\w+) spent (\d+(?:\.\d+)?)", ledger_raw))
    probe = ""
    pp = os.path.join(src, "highmem-rate-probe.txt")
    if os.path.exists(pp):
        probe = read_text(pp)
    m_open = re.search(r"open:.*?rate:\s*([\d.]+)/hr", probe)
    m_after = re.search(r"after:.*?rate:\s*([\d.]+)/hr", probe)
    highmem_rate = round(float(m_open.group(1)) - float(m_after.group(1)), 2) if m_open and m_after else None

    folders = sorted(d for d in os.listdir(src) if os.path.isdir(os.path.join(src, d))
                     and (re.match(r"^window\w*-(?:[a-z0-9.-]+-)?\d{8}$", d) or d == "token-scope-check"
                          or d.startswith("cpu-measure")))
    cols = ["window", "date", "card", "role", "purpose", "cap_units", "spent_units", "spent_basis", "exec_wall_s",
            "ok", "outcome_class", "outcome_source", "outcome_why", "rate_units_per_hr", "ledger_text"]
    rows = []
    bad_outcomes = []
    reasons = []
    for d in folders:
        dp = os.path.join(src, d)
        m = re.match(r"^window(\w+?)(?:-[a-z0-9.-]+?)?-(\d{8})$", d)
        if m:
            key, date8 = m.group(1), m.group(2)
        elif d.startswith("cpu-measure"):
            key, date8 = "cpu-measure", re.search(r"(\d{8})", d).group(1)
        else:
            key, date8 = "", ""
        date = (date8[:4] + "-" + date8[4:6] + "-" + date8[6:]) if date8 else ""
        pr = load_json(os.path.join(dp, "pin-result.json")) or {}
        row = ledger.get(key)
        what = segment_for(key, row["what"]) if row else ""
        launch = ""
        for lf in ("launch.sh", "run.sh"):
            if os.path.exists(os.path.join(dp, lf)):
                launch += read_text(os.path.join(dp, lf)) + "\n"
        is_stub = bool(pr.get("stub") or pr.get("mock"))
        mc = re.search(r"\((A100|H100|CPU|T4|L4)\b", what)
        mg = re.search(r"PIN_GPU=(\w+)", launch)
        mach = pr["machine"].get("card", "") if isinstance(pr.get("machine"), dict) else ""
        if "not assigned" in what.lower():
            card = "none"
        elif mc:
            card = mc.group(1)
        elif mg:
            card = mg.group(1)
        elif "A100" in mach:
            card = "A100"
        elif "H100" in mach:
            card = "H100"
        elif is_stub or key == "cpu-measure":
            card = "CPU"
        else:
            card = ""
        role = pr.get("role", "") if isinstance(pr.get("role"), str) else ""
        tl = what.lower()
        if key == "cpu-measure":
            role = "cpu-measure"
        elif "survival" in d:
            role = "survival"
        elif "cpusmoke" in d:
            role = "smoke"
        elif "prebuild" in d:
            role = "prebuild"
        elif "preflight" in tl:
            role = "preflight"
        elif is_stub or "stub" in tl:
            role = "stub"
        elif "q6k" in tl:
            role = "q6k"
        elif "conversion" in tl and role in ("", "smoke"):
            role = "convert"
        elif d.startswith("window1-"):
            role = "build"
        elif d == "token-scope-check":
            role = "scope-check"
        spent, basis = (None, "")
        if row:
            spent, basis = spent_for(key, row)
        elif key in earlier:
            spent = earlier[key]
            what = "ledger note: window %s spent %g, outside the budget" % (key, earlier[key])
        cap = ""
        mcap = re.search(r"\bcap (\d+(?:\.\d+)?)", what)
        if mcap:
            cap = mcap.group(1)
        wall = ""
        rl = os.path.join(dp, "rig.log")
        if os.path.exists(rl):
            w = re.findall(r"wall=(\d+)s", read_text(rl))
            if w:
                wall = w[-1]
        if not wall and pr.get("started") and pr.get("ended"):
            f = "%Y-%m-%dT%H:%M:%SZ"
            try:
                wall = str(int((datetime.strptime(pr["ended"], f) - datetime.strptime(pr["started"], f)).total_seconds()))
            except Exception:
                pass
        if not wall and isinstance(pr.get("seconds"), (int, float)):
            wall = str(pr["seconds"])
        ok = "" if "ok" not in pr else str(bool(pr["ok"])).lower()
        rate = ""
        mr = (re.search(r"(?:min|h)\s*×\s*(\d+(?:\.\d+)?)", what) or re.search(r"[,(]\s*(\d+(?:\.\d+)?)/hr", what)
              or re.search(r"(\d+(?:\.\d+)?)/hr measured", launch))
        if mr:
            rate = mr.group(1)
        elif key == "cpu-measure" and highmem_rate is not None:
            rate = str(highmem_rate)
        purpose = ""
        if d == "token-scope-check":
            purpose = "token scope check"
        elif key in earlier and not row:
            purpose = "smoke (earlier window, outside the budget)"
        elif what:
            purpose = short_purpose(re.sub(r"^\S+\s=\s", "", what))
        else:
            fl = [l for l in launch.splitlines()[1:] if l.startswith("#")]
            if fl:
                purpose = scrub(fl[0].lstrip("# ").strip())[:160]
            elif role:
                purpose = role + " (from pin-result)"
        is_test = ((card == "CPU" and role not in ("prebuild", "survival")) or is_stub
                   or role in ("stub", "preflight", "cpu-measure"))
        cls, why = classify(what, is_test) if (what or is_test) else ("", "")
        source, owhy = ("keyword" if cls else ""), why
        if key in OUTCOME_OVERRIDES:
            cls, owhy = OUTCOME_OVERRIDES[key]
            source = "r&d"
        oc = load_json(os.path.join(dp, "outcome.json")) or {}
        if oc.get("outcome"):
            cls, owhy, source = oc["outcome"], oc.get("why", ""), "outcome.json"
            if cls not in OUTCOMES:  # a label outside the vocabulary is kept, flagged, and fails the run at the end
                print(f"OFF-VOCABULARY outcome {cls!r} in {d}/outcome.json", file=sys.stderr)
                bad_outcomes.append(d)
            if spent is None and isinstance(oc.get("spent"), (int, float)):
                spent, basis = oc["spent"], oc.get("basis", "")
            if not cap and oc.get("cap") is not None:
                cap = str(oc["cap"])
        why = owhy
        rows.append({"window": d, "date": date, "card": card, "role": role, "purpose": scrub(purpose),
                     "cap_units": cap, "spent_units": "" if spent is None else "%g" % spent,
                     "spent_basis": basis, "exec_wall_s": wall, "ok": ok, "outcome_class": cls,
                     "outcome_source": source, "outcome_why": scrub(owhy or ""),
                     "rate_units_per_hr": rate, "ledger_text": scrub(what)})
        reasons.append((d, cls, why))

    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    outputs["windows.csv"] = buf.getvalue()

    for rel, txt in sorted(outputs.items()):
        if token_hit(txt):
            print("REFUSED: token-shaped string in output file " + rel + " (match not shown)", file=sys.stderr)
            sys.exit(1)

    for rel, txt in outputs.items():
        dest = os.path.join(out, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8", newline="\n") as f:
            f.write(txt)

    total = 0
    lines = ["relative_path\tbytes\tsha256\tcopied\treason"]
    ncopied = nhash = 0
    for r in files:
        digest, n = hash_file(os.path.join(src, r))
        total += n
        ok, why = copied[r]
        if ok:
            ncopied += 1
        else:
            nhash += 1
        lines.append("\t".join([scrub(r), str(n), digest, "yes" if ok else "no", why]))
    with open(os.path.join(out, "MANIFEST.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    print("window\tclass\treason")
    for d, c, why in reasons:
        print("%s\t%s\t%s" % (d, c or "(blank)", why or "-"))
    tot = {}
    blanks = []
    for r in rows:
        c = r["outcome_class"] or "(blank)"
        if r["spent_units"] == "":
            blanks.append(r["window"])
        else:
            tot[c] = tot.get(c, 0) + float(r["spent_units"])
    print("\nSPENT BY CLASS:", {k: round(v, 2) for k, v in sorted(tot.items())})
    print("BLANK SPENT:", ", ".join(blanks))
    print("\nwindows rows=%d copied=%d hashed_only=%d (files=%d) bytes_hashed=%d"
          % (len(rows), ncopied, nhash, len(files), total))
    if bad_outcomes:
        print("REFUSED: outcome.json labels outside the vocabulary in " + ", ".join(bad_outcomes), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
