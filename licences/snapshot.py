"""Fetch every page in registry.json, hash its text, and keep a full-text copy off the repo.

Usage: python licences/snapshot.py <snapshot-dir> [--write]

For each entry, the page is fetched, its visible text extracted, and the sha256 of that text recorded with the
snapshot's relative path. Each quoted clause is checked against the text (whitespace and quote marks normalised),
so a clause that no longer appears on the live page shows up as MISSING. The Wayback Machine's availability API is
asked for its closest snapshot (a read; nothing is submitted to the archive). Without --write it only reports.
"""

from __future__ import annotations

import gzip
import hashlib
import http.cookiejar
import json
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

REGISTRY = Path(__file__).with_name("registry.json")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, identity"})
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    with opener.open(req, timeout=60) as resp:  # noqa: S310 - fixed https URLs from the registry; cookies for consent redirects
        body = resp.read()
    if body[:2] == bytes((0x1F, 0x8B)):  # gzip magic: some servers compress regardless of the request
        body = gzip.decompress(body)
    if body[:5] == b"%PDF-":
        return pdf_text(body)
    return body.decode("utf-8", errors="replace")


def pdf_text(body: bytes) -> str:
    """A policy published as a PDF. pypdf is optional (the rnd package itself stays standard-library only)."""

    try:
        import io

        import pypdf
    except ImportError as e:
        raise RuntimeError("this entry is a PDF; install pypdf to read it") from e
    reader = pypdf.PdfReader(io.BytesIO(body))
    return " ".join(p.extract_text() or "" for p in reader.pages)


class _Text(HTMLParser):
    """The page's visible text: every text node outside script, style and noscript, entities decoded."""

    SKIP = {"script", "style", "noscript", "template"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.depth += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if not self.depth:
            self.parts.append(data)


def page_text(raw: str) -> str:
    if "<" not in raw:  # a plain-text licence file
        return re.sub(r"\s+", " ", raw).strip()
    p = _Text()
    p.feed(raw)
    p.close()
    return re.sub(r"\s+", " ", " ".join(p.parts)).strip()


def norm(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("—", "-").replace("–", "-")
    s = re.sub(r"\(\s+", "(", re.sub(r"\s+\)", ")", s))
    return re.sub(r"\s+", " ", s).strip().lower()


def wayback(url: str) -> str | None:
    q = "https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe="")
    try:
        data = json.loads(fetch(q))
    except Exception:  # noqa: BLE001 - the archive is optional
        return None
    snap = (data.get("archived_snapshots") or {}).get("closest") or {}
    return snap.get("url") if snap.get("available") else None


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    out_dir = Path(argv[0])
    write = "--write" in argv
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    bad = 0
    for e in reg["entries"]:
        try:
            text = page_text(fetch(e["url"]))
        except Exception as ex:  # noqa: BLE001 - reported per entry
            print(f"{e['id']}: FETCH FAILED {ex.__class__.__name__}: {ex}")
            bad += 1
            continue
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        name = f"{e['id']}.txt"
        (out_dir / name).write_text(e["url"] + "\n\n" + text, encoding="utf-8")
        body = norm(text)
        missing = [c for c in e.get("clauses", []) if norm(c) not in body]
        arch = wayback(e["url"])
        print(f"{e['id']}: {len(text)} chars sha256 {digest[:12]} clauses {len(e.get('clauses', [])) - len(missing)}/{len(e.get('clauses', []))}"
              f"{' MISSING: ' + '; '.join(m[:60] for m in missing) if missing else ''} archive {'yes' if arch else 'none'}")
        if missing:
            bad += 1
        if write:
            e["snapshot_sha256"] = digest
            e["snapshot_file"] = f"{out_dir.name}/{name}"
            e["archive_url"] = arch or e.get("archive_url")  # the archive API is flaky: never drop a copy already found
    if write:
        REGISTRY.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
