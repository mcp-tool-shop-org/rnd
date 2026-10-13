"""Watch the sources in watchlist.json and report what is new since the last check.

`rnd watch` is the deterministic half of the weekly watch ritual: it fetches each source, compares what it
finds with the items seen before, and reports only the new ones. Reading and ranking them is the scout's job.

Source kinds:

- github-releases: the repository's latest releases (drafts skipped), through `gh api`.
- github-commits: the default branch's latest commits, through `gh api`.
- huggingface: a Hugging Face model listing URL (the API's JSON); a model is new the first time it is listed.
- feed: an Atom or RSS feed.
- page: a web page and a `pattern` regex with one group; each distinct match is an item, so a new version
  string on a release-notes page is a new item.

The state file maps each source id to the item keys already seen. A source with no state yet is a baseline:
its items are recorded and none is reported as new. A source that can't be reached is reported as unknown
with the reason, and its state is left as it was, so nothing is skipped silently.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import urllib.error
import urllib.request
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from .probe import TIMEOUT, UA, ProbeError, gh_json

KINDS = ("github-releases", "github-commits", "huggingface", "feed", "page")
KEEP = 300  # keys remembered per source; enough to outlast any one source's listing
GITHUB_RE = re.compile(r"^https?://github\.com/([\w.-]+/[\w.-]+?)/?$")
ATOM = "{http://www.w3.org/2005/Atom}"


class WatchError(Exception):
    def __init__(self, code, message, hint=""):
        super().__init__(message)
        self.code, self.hint = code, hint


def http_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def load_watchlist(path: Path) -> list[dict]:
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WatchError("WATCHLIST_UNREADABLE", f"{path}: {exc}", "the watchlist is docs/watchlist.json in the library")
    sources, seen = doc.get("sources") or [], set()
    for s in sources:
        sid = s.get("id")
        if not sid or sid in seen:
            raise WatchError("WATCHLIST_INVALID", f"source id missing or repeated: {sid!r}")
        seen.add(sid)
        if s.get("kind") not in KINDS:
            raise WatchError("WATCHLIST_INVALID", f"{sid}: kind {s.get('kind')!r} is not one of {', '.join(KINDS)}")
        if s["kind"].startswith("github-") and not GITHUB_RE.match(s.get("url", "")):
            raise WatchError("WATCHLIST_INVALID", f"{sid}: {s.get('url')!r} is not a github.com/<owner>/<repo> URL")
        if s["kind"] == "page":
            try:
                if re.compile(s.get("pattern") or "").groups != 1:
                    raise WatchError("WATCHLIST_INVALID", f"{sid}: a page source needs a pattern with one group")
            except re.error as exc:
                raise WatchError("WATCHLIST_INVALID", f"{sid}: pattern does not compile: {exc}")
    return sources


def load_state(path: Path) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError) as exc:
        raise WatchError("WATCH_STATE_UNREADABLE", f"{path}: {exc}",
                         "fix or move the state file; a missing file starts every source as a baseline")


def save_state(path: Path, state: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


# ------------------------------------------------------------------ parsers (newest first, as each source lists)

def from_releases(rows: list) -> list[dict]:
    return [{"key": r.get("tag_name"), "title": r.get("name") or r.get("tag_name"), "date": r.get("published_at"),
             "url": r.get("html_url"), "prerelease": bool(r.get("prerelease"))}
            for r in rows or [] if not r.get("draft") and r.get("tag_name")]


def from_commits(rows: list) -> list[dict]:
    return [{"key": r["sha"][:12], "title": (((r.get("commit") or {}).get("message") or "").splitlines() or [""])[0][:200],
             "date": ((r.get("commit") or {}).get("committer") or {}).get("date"), "url": r.get("html_url")}
            for r in rows or [] if r.get("sha")]


def from_hf_list(rows: list) -> list[dict]:
    return [{"key": r["id"], "title": r["id"], "date": r.get("lastModified") or r.get("createdAt"),
             "url": f"https://huggingface.co/{r['id']}"} for r in rows or [] if r.get("id")]


def from_feed(text: str) -> list[dict]:
    root = ET.fromstring(text)
    items = []
    if root.tag == f"{ATOM}feed":
        for e in root.findall(f"{ATOM}entry"):
            link = next((l.get("href") for l in e.findall(f"{ATOM}link") if l.get("rel", "alternate") == "alternate"), None)
            items.append({"key": (e.findtext(f"{ATOM}id") or link or "").strip(),
                          "title": (e.findtext(f"{ATOM}title") or "").strip(),
                          "date": e.findtext(f"{ATOM}published") or e.findtext(f"{ATOM}updated"), "url": link})
    else:
        for e in root.iter("item"):
            link = (e.findtext("link") or "").strip() or None
            items.append({"key": (e.findtext("guid") or link or e.findtext("title") or "").strip(),
                          "title": (e.findtext("title") or "").strip(), "date": e.findtext("pubDate"), "url": link})
    return [i for i in items if i["key"]]


def from_page(text: str, pattern: str, url: str) -> list[dict]:
    out, seen = [], set()
    for m in re.finditer(pattern, text):
        found = " ".join(m.group(1).split())
        if found and found not in seen:
            seen.add(found)
            out.append({"key": found, "title": found, "date": None, "url": url})
    return out


def fetch_items(source: dict, *, github=None, fetch=None) -> list[dict]:
    github = github or gh_json
    fetch = fetch or http_text
    kind, url = source["kind"], source["url"]
    if kind == "github-releases":
        return from_releases(github(f"repos/{GITHUB_RE.match(url).group(1)}/releases", "per_page=15"))
    if kind == "github-commits":
        return from_commits(github(f"repos/{GITHUB_RE.match(url).group(1)}/commits", "per_page=30"))
    if kind == "huggingface":
        return from_hf_list(json.loads(fetch(url)))
    if kind == "feed":
        return from_feed(fetch(url))
    return from_page(fetch(url), source["pattern"], url)


def check(sources: list[dict], state: dict, *, github=None, fetch=None, only=None, now=None) -> tuple[dict, dict]:
    """(report, new_state). The state passed in is not changed."""
    now = now or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    new_state, rows = dict(state), []
    for s in sources:
        if only and s["id"] not in only:
            continue
        row = {"id": s["id"], "kind": s["kind"], "url": s["url"], "why": s.get("why", ""),
               "latest": None, "new": [], "baseline": False, "unknown": None}
        try:
            items = fetch_items(s, github=github, fetch=fetch)
        except (ProbeError, urllib.error.URLError, TimeoutError, OSError, subprocess.TimeoutExpired,
                json.JSONDecodeError, ET.ParseError) as exc:
            row["unknown"] = f"{type(exc).__name__}: {exc}"
            rows.append(row)
            continue
        if items:
            row["latest"] = {k: items[0][k] for k in ("key", "title", "date", "url")}
        prior = state.get(s["id"])
        if prior is None:
            row["baseline"] = True
            seen_keys: list = []
        else:
            seen_keys = list(prior.get("seen") or [])
            known = set(seen_keys)
            row["new"] = [i for i in items if i["key"] not in known]
        fresh = [i["key"] for i in items if i["key"] not in set(seen_keys)]
        new_state[s["id"]] = {"seen": (fresh + seen_keys)[:KEEP], "checked": now}
        rows.append(row)
    report = {"checked": now, "sources": rows,
              "new_total": sum(len(r["new"]) for r in rows),
              "unknown": [r["id"] for r in rows if r["unknown"]]}
    return report, new_state
