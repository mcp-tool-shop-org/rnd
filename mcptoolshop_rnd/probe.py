"""Probe a tool or model before trialling it: licence, latest release, gating, telemetry hits, library hits.

`rnd probe <url> [...]` takes GitHub repositories, Hugging Face models, PyPI projects and npm packages.
Every fact comes from the source's own API, not from a summary of a web page:

- GitHub (through `gh api`, so it uses the caller's login): the licence's SPDX id, whether the repository is
  archived, the last push, the latest release and its date, and a code search for "telemetry" (a count and
  the first paths). A hit is a lead to read, never proof; zero hits is not proof of no telemetry either.
- Hugging Face: the licence tag and the card's licence name and link, whether the model is gated, the last
  change.
- PyPI and npm: the licence (expression, field or classifier), the latest version and when it was published.
- The library: an exact-word search for the name, so the probe says when rnd already holds it.

A source that can't be reached is reported as unknown with the reason, never guessed.
"""
from __future__ import annotations

import json
import re
import subprocess
import urllib.error
import urllib.request

UA = "mcptoolshop-rnd-probe"
TIMEOUT = 20
GITHUB_RE = re.compile(r"^https?://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?/?(?:[#?].*)?$")
HF_RE = re.compile(r"^https?://huggingface\.co/((?!datasets/|spaces/)[\w.-]+/[\w.-]+)/?(?:[#?].*)?$")
PYPI_RE = re.compile(r"^https?://pypi\.org/project/([\w.-]+)/?(?:[#?].*)?$")
NPM_RE = re.compile(r"^https?://(?:www\.)?npmjs\.com/package/((?:@[\w.-]+/)?[\w.-]+)/?(?:[#?].*)?$")


class ProbeError(Exception):
    def __init__(self, code, message, hint=""):
        super().__init__(message)
        self.code, self.hint = code, hint


def kind_of(url: str) -> tuple[str, str]:
    """(kind, name) for a supported URL."""
    for kind, pattern in (("github", GITHUB_RE), ("huggingface", HF_RE), ("pypi", PYPI_RE), ("npm", NPM_RE)):
        m = pattern.match(url.strip())
        if m:
            name = "/".join(m.groups()) if kind == "github" else m.group(1)
            return kind, name
    raise ProbeError("PROBE_UNSUPPORTED_URL", f"{url} is not a GitHub repository, Hugging Face model, PyPI project "
                     "or npm package URL", "e.g. https://github.com/NVIDIA/NeMo-Relay or https://pypi.org/project/x")


def http_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def gh_json(path: str, *fields: str) -> dict:
    """`gh api` GET. Fields become `-f k=v` query parameters."""
    args = ["gh", "api", "-X", "GET", path]
    for f in fields:
        args += ["-f", f]
    # gh writes UTF-8; without an explicit encoding Windows decodes it as cp1252 and fails on real payloads.
    got = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT)
    if got.returncode != 0:
        said = (got.stderr or got.stdout or "").strip()
        raise ProbeError("PROBE_GH_FAILED", said.splitlines()[-1] if said else f"gh api {path} failed",
                         "install and log in to the GitHub CLI (gh auth login)")
    return json.loads(got.stdout or "null") or {}


def _safe(fn, *args):
    """(value, None) or (None, reason); a missing source is unknown, never guessed."""
    try:
        return fn(*args), None
    except ProbeError as exc:
        return None, str(exc)
    except (urllib.error.URLError, TimeoutError, OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


def from_github(repo: dict, release: dict | None, code: dict | None) -> dict:
    lic = repo.get("license") or {}
    out = {
        "licence": lic.get("spdx_id") if lic.get("spdx_id") not in (None, "NOASSERTION") else (lic.get("name") or None),
        "archived": bool(repo.get("archived")),
        "updated": repo.get("pushed_at"),
        "latest": None,
        "released": None,
    }
    if release:
        out["latest"], out["released"] = release.get("tag_name"), release.get("published_at")
    if code is not None:
        out["telemetry_hits"] = code.get("total_count")
        out["telemetry_paths"] = [i.get("path") for i in (code.get("items") or [])][:5]
    return out


def from_huggingface(model: dict) -> dict:
    card = model.get("cardData") or {}
    tag = next((t.split(":", 1)[1] for t in model.get("tags") or [] if t.startswith("license:")), None)
    name = card.get("license_name") if (card.get("license") or tag) == "other" else None
    return {
        "licence": name or card.get("license") or tag,
        "licence_link": card.get("license_link"),
        "gated": model.get("gated") not in (False, None),
        "updated": model.get("lastModified"),
    }


def from_pypi(doc: dict) -> dict:
    info = doc.get("info") or {}
    version = info.get("version")
    classifier = next((c.split("::")[-1].strip() for c in info.get("classifiers") or [] if c.startswith("License ::")), None)
    files = (doc.get("releases") or {}).get(version) or []
    return {
        "licence": info.get("license_expression") or (info.get("license") or None) or classifier,
        "latest": version,
        "released": files[0].get("upload_time_iso_8601") if files else None,
    }


def from_npm(doc: dict) -> dict:
    latest = (doc.get("dist-tags") or {}).get("latest")
    lic = doc.get("license")
    return {
        "licence": lic.get("type") if isinstance(lic, dict) else lic,
        "latest": latest,
        "released": (doc.get("time") or {}).get(latest),
    }


def probe(url: str, *, github=None, fetch=None, library=None) -> dict:
    """One URL's facts. `github`, `fetch` and `library` are seams; left out, the live ones are used."""
    github = github or gh_json
    fetch = fetch or http_json
    kind, name = kind_of(url)
    report = {"url": url, "kind": kind, "name": name, "unknown": {}}
    if kind == "github":
        repo, why = _safe(github, f"repos/{name}")
        if repo is None:
            report["unknown"]["repository"] = why
        else:
            release, why_r = _safe(github, f"repos/{name}/releases/latest")
            if release is None:
                report["unknown"]["release"] = why_r
            code, why_c = _safe(github, "search/code", f"q=telemetry repo:{name}", "per_page=5")
            if code is None:
                report["unknown"]["telemetry"] = why_c
            report.update(from_github(repo, release, code))
    elif kind == "huggingface":
        model, why = _safe(fetch, f"https://huggingface.co/api/models/{name}")
        if model is None:
            report["unknown"]["model"] = why
        else:
            report.update(from_huggingface(model))
    elif kind == "pypi":
        doc, why = _safe(fetch, f"https://pypi.org/pypi/{name}/json")
        if doc is None:
            report["unknown"]["project"] = why
        else:
            report.update(from_pypi(doc))
    else:
        doc, why = _safe(fetch, f"https://registry.npmjs.org/{name.replace('/', '%2F')}")
        if doc is None:
            report["unknown"]["package"] = why
        else:
            report.update(from_npm(doc))
    if library is not None:
        short = name.split("/")[-1]
        report["library_hits"] = library(short)
    return report
