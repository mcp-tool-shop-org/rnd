"""Publish the rnd newsletter: to Hugging Face as the dataset mcp-tool-shop/rnd-newsletter, to npm as
@rnd-news/newsletter, to PyPI as mcptoolshop-rnd-newsletter, and as one GitHub release per new issue. One builder,
run by .github/workflows/newsletter-publish.yml.

  python site/scripts/newsletter_publish.py build --out nl-out                  # no secrets
  python site/scripts/newsletter_publish.py upload --out nl-out                 # HF_TOKEN + huggingface_hub
  python site/scripts/newsletter_publish.py npm-plan --out nl-out --pkg nl-pkg  # reads npm, writes the package
  python site/scripts/newsletter_publish.py pypi-plan --out nl-out --pkg nl-pypi --version 1.N.R   # reads PyPI
  python site/scripts/newsletter_publish.py releases --out nl-out               # GH_TOKEN + SOURCE_SHA; gh CLI

The build reads only published issues: site/src/content/docs/newsletter/issue-*.md on the checked-out commit, with
an integer `issue` in the front matter and no `draft: true`. Drafts and held articles live outside this repository,
so they can't reach it. It writes:

  issues/issue-NN.md    each issue's front matter and Markdown, with site links made absolute
  data/issues.jsonl     one row per issue: issue, date, title, description, highlights, url, body_markdown
  README.md             the dataset card

The output is byte-for-byte the same for the same issues. The HF upload is one upload_folder commit, and
huggingface_hub makes no commit when no file differs. The npm package (package.json, README, index.json, data/,
issues/) is versioned 1.<latest issue>.<revision>, carries the build's contentSha256, and is published only when
that exact content isn't already the newest version for the issue, so reruns publish nothing.

Standards compliance (workflow standards, scored 0-3):
- PIN_PER_STEP 2: huggingface_hub, npm and every action are pinned in .github/workflows/newsletter-publish.yml; the build is
  deterministic from the checked-out commit.
- ANDON_AUTHORITY 2: any parse error, a duplicate issue number or a file name that doesn't match its issue number
  stops the build before anything is uploaded.
- NAMED_COMPENSATORS 2: the irreversible steps are an HF dataset commit and an npm publish (see the compensators
  table in the workflow file).
- DECOMPOSE_BY_SECRETS 2: the build needs no secret; HF_TOKEN is set only for the HF upload step, and the npm publish
  authenticates by OIDC in its own job and environment.
- UNCERTAINTY_GATED_HUMANS 2: the newsletter is already public and Director-approved before it reaches main; this
  only mirrors it. The first backfill is a manual workflow_dispatch run.
- EXTERNAL_VERIFIER: n/a, no specialized claims.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import hashlib
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

REPO_ID = "mcp-tool-shop/rnd-newsletter"
SITE = "https://mcp-tool-shop-org.github.io/rnd/"
FEED = SITE + "newsletter/rss.xml"
STUDIO = "mcp-tool-shop"
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
NEWSLETTER = ROOT / "site" / "src" / "content" / "docs" / "newsletter"
FIELDS = ("issue", "date", "title", "description", "highlights", "url", "body_markdown")


class BuildError(Exception):
    """A published issue that can't be read as one; nothing is uploaded."""


def _scalar(raw: str, where: str):
    value = raw.strip()
    if value.startswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise BuildError(f"{where}: unreadable double-quoted value ({exc})") from exc
    if value.startswith("'"):
        if not value.endswith("'") or len(value) < 2:
            raise BuildError(f"{where}: unterminated single-quoted value")
        return value[1:-1].replace("''", "'")
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if value in ("true", "false"):
        return value == "true"
    return value


def parse_issue(text: str, name: str) -> tuple[dict, str]:
    """Split an issue file into its front matter (the subset the newsletter uses) and its Markdown body."""
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise BuildError(f"{name}: no front matter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise BuildError(f"{name}: front matter is not closed")
    meta: dict = {}
    current_list: list | None = None
    for number, line in enumerate(text[4:end].split("\n"), start=2):
        where = f"{name}:{number}"
        if not line.strip():
            continue
        item = re.match(r"^\s+-\s+(.*)$", line)
        if item:
            if current_list is None:
                raise BuildError(f"{where}: list item outside a list")
            current_list.append(_scalar(item.group(1), where))
            continue
        pair = re.match(r"^([A-Za-z_][\w-]*):(.*)$", line)
        if not pair:
            raise BuildError(f"{where}: unreadable front matter line")
        key, value = pair.group(1), pair.group(2)
        if value.strip():
            meta[key] = _scalar(value, where)
            current_list = None
        else:
            current_list = meta[key] = []
    return meta, text[end + 5:].lstrip("\n")


def absolutise(markdown: str, page_url: str) -> str:
    """Make the site's relative links absolute against the issue's page, so they work on Hugging Face.

    Covers Markdown links and images and HTML href/src. Absolute URLs, mailto: and same-page #anchors are kept.
    """
    host = urllib.parse.urlsplit(SITE)
    origin = f"{host.scheme}://{host.netloc}"

    def fix(target: str) -> str:
        if not target or target.startswith("#") or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I):
            return target
        return urllib.parse.urljoin(origin + "/" if target.startswith("/") else page_url, target)

    markdown = re.sub(r"(\]\()([^)\s]+)", lambda m: m.group(1) + fix(m.group(2)), markdown)
    return re.sub(r'((?:href|src)=")([^"]*)', lambda m: m.group(1) + fix(m.group(2)), markdown)


def published_issues(newsletter: pathlib.Path = NEWSLETTER) -> list[dict]:
    rows, seen = [], {}
    for path in sorted(newsletter.glob("issue-*.md")):
        meta, body = parse_issue(path.read_text(encoding="utf-8"), path.name)
        if meta.get("draft") is True:
            continue
        number = meta.get("issue")
        if not isinstance(number, int):
            continue
        if not re.fullmatch(rf"issue-0*{number}", path.stem):
            raise BuildError(f"{path.name}: front matter says issue {number}")
        if number in seen:
            raise BuildError(f"{path.name}: issue {number} is also {seen[number]}")
        seen[number] = path.name
        for key in ("title", "date", "description"):
            if not isinstance(meta.get(key), str) or not meta[key].strip():
                raise BuildError(f"{path.name}: front matter has no {key}")
        highlights = meta.get("highlights") or []
        if not all(isinstance(h, str) for h in highlights):
            raise BuildError(f"{path.name}: highlights must be strings")
        rows.append({
            "issue": number,
            "date": meta["date"],
            "title": meta["title"],
            "description": meta["description"],
            "highlights": highlights,
            "url": f"{SITE}newsletter/{path.stem}/",
            "body_markdown": absolutise(body, f"{SITE}newsletter/{path.stem}/"),
            "_stem": path.stem,
        })
    return sorted(rows, key=lambda r: r["issue"])


def _front_matter(row: dict) -> str:
    lines = ["---"]
    for key in ("issue", "date", "title", "description"):
        value = row[key]
        lines.append(f"{key}: {value}" if isinstance(value, int) else f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.append(f"url: {json.dumps(row['url'])}")
    lines.append("highlights:")
    lines += [f"  - {json.dumps(h, ensure_ascii=False)}" for h in row["highlights"]]
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def dataset_card(rows: list[dict]) -> str:
    latest = rows[-1] if rows else None
    newest = f"The newest is issue {latest['issue']}, {latest['date']}: [{latest['title']}]({latest['url']})." if latest else ""
    return f"""---
license: mit
language:
  - en
pretty_name: "Research and Development: the newsletter"
tags:
  - newsletter
  - research
  - machine-learning
size_categories:
  - n<1K
configs:
  - config_name: default
    data_files:
      - split: train
        path: data/issues.jsonl
---

# Research and Development: the newsletter

The research newsletter of {STUDIO}: what we measured, and what it means. Each issue reports the studio's experiments
in plain language, with the numbers, the charts, what held up and what didn't.

This dataset mirrors the published issues and is updated automatically after each issue goes live on the site.
It holds {len(rows)} issues. {newest}

- **Read it on the web:** {SITE}
- **RSS:** {FEED}
- **Source:** [mcp-tool-shop-org/rnd](https://github.com/mcp-tool-shop-org/rnd), where each issue is
  `site/src/content/docs/newsletter/issue-NN.md`.

## Files

- `data/issues.jsonl`: one row per issue, with `issue`, `date`, `title`, `description`, `highlights` (HTML
  strings), `url` and `body_markdown` (the issue's Markdown, with site links made absolute).
- `issues/issue-NN.md`: each issue as a Markdown file with its front matter.

Charts are linked from the site, not copied here.

## Load it

```python
from datasets import load_dataset
issues = load_dataset("{REPO_ID}", split="train")
```

## Licence and author

MIT, the licence of the rnd repository the issues are published from. Author: {STUDIO}.
"""


def build(out: pathlib.Path, newsletter: pathlib.Path = NEWSLETTER) -> list[dict]:
    """Write the dataset folder for the published issues. Deterministic: same issues, same bytes."""
    rows = published_issues(newsletter)
    (out / "issues").mkdir(parents=True, exist_ok=True)
    (out / "data").mkdir(parents=True, exist_ok=True)
    keep = {f"{r['_stem']}.md" for r in rows}
    for stale in (out / "issues").glob("*.md"):
        if stale.name not in keep:
            stale.unlink()
    for row in rows:
        (out / "issues" / f"{row['_stem']}.md").write_bytes((_front_matter(row) + row["body_markdown"]).encode("utf-8"))
    jsonl = "".join(json.dumps({k: r[k] for k in FIELDS}, ensure_ascii=False) + "\n" for r in rows)
    (out / "data" / "issues.jsonl").write_bytes(jsonl.encode("utf-8"))
    (out / "README.md").write_bytes(dataset_card(rows).encode("utf-8"))
    return rows


NPM_NAME = "@rnd-news/newsletter"
NPM_FILES = ("README.md", "index.json", "data/issues.jsonl", "issues/")


def content_digest(out: pathlib.Path) -> str:
    """sha256 over the built issues and data, in a fixed order, so a correction to any issue changes it."""
    digest = hashlib.sha256()
    for path in sorted([out / "data" / "issues.jsonl", *(out / "issues").glob("*.md")]):
        digest.update(path.relative_to(out).as_posix().encode("utf-8") + b"\0")
        digest.update(path.read_bytes() + b"\0")
    return digest.hexdigest()


def plan_version(latest_issue: int, published: dict[str, str | None], digest: str) -> tuple[str, bool]:
    """The npm version for this build, and whether to publish it.

    Versions are 1.<latest issue>.<revision>. With nothing published for this issue, publish 1.N.0. If the newest
    1.N.R carries this build's content digest, skip (a rerun). Otherwise publish 1.N.(R+1): a correction to issues
    already published. `published` maps each published version to its contentSha256 (None if unknown).

    An unknown digest on the newest 1.N.R refuses the plan rather than publishing 1.N.(R+1): a version can't be taken
    back after 72 hours, so a failed lookup must never turn into a needless release.
    """
    revisions = []
    for version, seen in published.items():
        match = re.fullmatch(rf"1\.{latest_issue}\.(\d+)", version)
        if match:
            revisions.append((int(match.group(1)), seen))
    if not revisions:
        return f"1.{latest_issue}.0", True
    revision, seen = max(revisions)
    if seen is None:
        raise BuildError(f"can't read the contentSha256 of 1.{latest_issue}.{revision}; refusing to publish")
    if seen == digest:
        return f"1.{latest_issue}.{revision}", False
    return f"1.{latest_issue}.{revision + 1}", True


def npm_readme(rows: list[dict]) -> str:
    card = dataset_card(rows)
    body = card.split("\n---\n", 1)[1].lstrip("\n")
    load_python = body[body.index("## Load it"):body.index("## Licence and author")]
    load_js = (
        "## Load it\n\n"
        "```js\n"
        f'const index = require("{NPM_NAME}");          // one entry per issue, newest last\n'
        "```\n\n"
        "```js\n"
        f'import index from "{NPM_NAME}" with {{ type: "json" }};\n'
        "```\n\n"
        "Each entry gives the issue's number, date, title, description, highlights, url and `file`, the path of its\n"
        f"Markdown inside the package (`{NPM_NAME}/issues/issue-NN.md`). `data/issues.jsonl` holds the full rows,\n"
        f"bodies included. The same data is on Hugging Face as [{REPO_ID}](https://huggingface.co/datasets/{REPO_ID}).\n\n"
    )
    body = body.replace(load_python, load_js).replace("This dataset mirrors", "This package mirrors")
    body = body.replace(
        "- `issues/issue-NN.md`:",
        "- `index.json`: the package's main export, one entry per issue without its body.\n- `issues/issue-NN.md`:",
    )
    return body


def build_npm(out: pathlib.Path, pkg: pathlib.Path, version: str) -> None:
    """Assemble the npm package from a built folder: package.json, README, index.json, data/ and issues/."""
    rows = [json.loads(line) for line in (out / "data" / "issues.jsonl").read_text(encoding="utf-8").splitlines()]
    (pkg / "issues").mkdir(parents=True, exist_ok=True)
    (pkg / "data").mkdir(parents=True, exist_ok=True)
    for page in sorted((out / "issues").glob("*.md")):
        (pkg / "issues" / page.name).write_bytes(page.read_bytes())
    (pkg / "data" / "issues.jsonl").write_bytes((out / "data" / "issues.jsonl").read_bytes())
    index = [
        {**{k: r[k] for k in FIELDS if k != "body_markdown"}, "file": f"issues/{r['url'].rstrip('/').rsplit('/', 1)[1]}.md"}
        for r in rows
    ]
    (pkg / "index.json").write_bytes((json.dumps(index, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    (pkg / "README.md").write_bytes(npm_readme(rows).encode("utf-8"))
    manifest = {
        "name": NPM_NAME,
        "version": version,
        "description": "The research newsletter of mcp-tool-shop: every published issue as Markdown and JSON.",
        "author": STUDIO,
        "license": "MIT",
        "homepage": SITE + "newsletter/",
        "repository": {"type": "git", "url": "git+https://github.com/mcp-tool-shop-org/rnd.git"},
        "keywords": ["newsletter", "research", "machine-learning", "dataset"],
        "main": "index.json",
        "exports": {
            ".": "./index.json",
            "./index.json": "./index.json",
            "./data/issues.jsonl": "./data/issues.jsonl",
            "./issues/*": "./issues/*",
            "./package.json": "./package.json",
        },
        "files": list(NPM_FILES),
        "contentSha256": content_digest(out),
    }
    (pkg / "package.json").write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))


def npm_published(name: str = NPM_NAME) -> dict[str, str | None]:  # pragma: no cover - network
    """Published versions and their contentSha256, read with `npm view`. An unpublished name gives {}."""
    run = subprocess.run(["npm", "view", name, "versions", "--json"], capture_output=True, text=True)
    if run.returncode != 0:
        if "E404" in run.stderr or "404" in run.stderr:
            return {}
        raise BuildError(f"npm view failed: {run.stderr.strip()[:300]}")
    versions = json.loads(run.stdout or "[]")
    versions = [versions] if isinstance(versions, str) else versions
    found: dict[str, str | None] = {}
    for version in versions:
        field = subprocess.run(["npm", "view", f"{name}@{version}", "contentSha256"], capture_output=True, text=True)
        if field.returncode != 0:
            raise BuildError(f"npm view {name}@{version} failed: {field.stderr.strip()[:300]}")
        found[version] = field.stdout.strip() or None
    return found


PYPI_NAME = "mcptoolshop-rnd-newsletter"
PYPI_IMPORT = "rnd_newsletter"
SETUPTOOLS_PIN = "setuptools==80.9.0"

PYPI_INIT = '''"""The rnd newsletter of mcp-tool-shop: every published issue, as data.

    import rnd_newsletter
    rnd_newsletter.latest()["title"]
    rnd_newsletter.issue(30)["url"]
    [i["issue"] for i in rnd_newsletter.issues()]

Each issue is a dict with issue, date, title, description, highlights, url and body_markdown. The Markdown pages are
also in the package, under rnd_newsletter/data/issues/.
"""
from __future__ import annotations

import json
from importlib.resources import files

__version__ = "{version}"
__all__ = ["issues", "issue", "latest", "__version__"]


def issues() -> list[dict]:
    """Every published issue, oldest first."""
    text = files(__name__).joinpath("data", "issues.jsonl").read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def issue(number: int) -> dict:
    """One issue by its number; KeyError if there is no published issue with that number."""
    for entry in issues():
        if entry["issue"] == number:
            return entry
    raise KeyError(f"no published issue {{number}}")


def latest() -> dict:
    """The newest published issue."""
    return issues()[-1]
'''


def build_pypi(out: pathlib.Path, pkg: pathlib.Path, version: str, license_text: str) -> None:
    """Assemble the pure-data Python package from a built folder: pyproject.toml, README, LICENSE and the data."""
    rows = [json.loads(line) for line in (out / "data" / "issues.jsonl").read_text(encoding="utf-8").splitlines()]
    src = pkg / "src" / PYPI_IMPORT
    (src / "data" / "issues").mkdir(parents=True, exist_ok=True)
    for page in sorted((out / "issues").glob("*.md")):
        (src / "data" / "issues" / page.name).write_bytes(page.read_bytes())
    (src / "data" / "issues.jsonl").write_bytes((out / "data" / "issues.jsonl").read_bytes())
    (src / "__init__.py").write_bytes(PYPI_INIT.format(version=version).encode("utf-8"))
    (pkg / "LICENSE").write_bytes(license_text.encode("utf-8"))
    readme = npm_readme(rows)
    readme = readme[:readme.index("## Load it")] + (
        "## Load it\n\n"
        "```python\n"
        "import rnd_newsletter\n\n"
        "rnd_newsletter.latest()        # the newest issue, a dict\n"
        "rnd_newsletter.issue(30)       # one issue by number\n"
        "rnd_newsletter.issues()        # every issue, oldest first\n"
        "```\n\n"
        "No dependencies; Python 3.10 or newer. The same data is on Hugging Face as "
        f"[{REPO_ID}](https://huggingface.co/datasets/{REPO_ID}) and on npm as `{NPM_NAME}`.\n\n"
    ) + readme[readme.index("## Licence and author"):]
    readme = readme.replace("This package mirrors", "This package mirrors").replace(
        "- `index.json`: the package's main export, one entry per issue without its body.\n", "")
    (pkg / "README.md").write_bytes(readme.encode("utf-8"))
    pyproject = f'''[build-system]
requires = ["{SETUPTOOLS_PIN}"]
build-backend = "setuptools.build_meta"

[project]
name = "{PYPI_NAME}"
version = "{version}"
description = "The research newsletter of mcp-tool-shop: every published issue as data."
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
license-files = ["LICENSE"]
authors = [{{ name = "{STUDIO}" }}]
keywords = ["newsletter", "research", "machine-learning", "dataset"]
classifiers = [
  "Programming Language :: Python :: 3",
  "Topic :: Scientific/Engineering :: Artificial Intelligence",
]
dependencies = []

[project.urls]
Homepage = "{SITE}newsletter/"
Source = "https://github.com/mcp-tool-shop-org/rnd"
"Hugging Face" = "https://huggingface.co/datasets/{REPO_ID}"
npm = "https://www.npmjs.com/package/{NPM_NAME}"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
{PYPI_IMPORT} = ["data/issues.jsonl", "data/issues/*.md"]
'''
    (pkg / "pyproject.toml").write_bytes(pyproject.encode("utf-8"))


def pypi_has(version: str, name: str = PYPI_NAME) -> bool:  # pragma: no cover - network
    """Whether PyPI already has this version (its JSON API; a 404 means not published)."""
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310 - fixed https URL
            return response.status == 200
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False
        raise BuildError(f"PyPI lookup for {version} failed: HTTP {exc.code}") from exc
    except OSError as exc:
        raise BuildError(f"PyPI lookup for {version} failed: {exc}") from exc


FIRST_RELEASED_ISSUE = 30  # issues 1-29 get no GitHub release unless that is decided separately


def release_tag(stem: str) -> str:
    """The GitHub release tag for an issue page stem: issue-30 -> newsletter-issue-30. Never a tool version tag."""
    return f"newsletter-{stem}"


def release_notes(row: dict) -> str:
    """The release body: the description, the highlights as plain-text bullets, and where to read it."""
    stem = row["url"].rstrip("/").rsplit("/", 1)[1]
    plain = [re.sub(r"<[^>]+>", "", h).strip() for h in row["highlights"]]
    lines = [row["description"], ""]
    lines += [f"- {h}" for h in plain]
    lines += [
        "",
        f"- **Read it:** {row['url']}",
        f"- **Hugging Face:** https://huggingface.co/datasets/{REPO_ID}",
        f"- **npm:** https://www.npmjs.com/package/{NPM_NAME}",
        f"- **PyPI:** https://pypi.org/project/{PYPI_NAME}/",
        "",
        f"The issue's Markdown is attached as `{stem}.md`. Issue {row['issue']}, {row['date']}, by {STUDIO}.",
    ]
    return "\n".join(lines) + "\n"


def releases_due(rows: list[dict], existing: set[str], first: int = FIRST_RELEASED_ISSUE) -> list[dict]:
    """Issues from `first` on that have no release yet, oldest first. Each entry: tag, title, notes, stem."""
    due = []
    for row in rows:
        stem = row["url"].rstrip("/").rsplit("/", 1)[1]
        tag = release_tag(stem)
        if row["issue"] >= first and tag not in existing:
            due.append({"tag": tag, "title": row["title"], "notes": release_notes(row), "stem": stem})
    return due


def github_releases(out: pathlib.Path, target: str) -> list[str]:  # pragma: no cover - network
    """Create the GitHub release for each issue that is due. Returns the tags created."""
    rows = [json.loads(line) for line in (out / "data" / "issues.jsonl").read_text(encoding="utf-8").splitlines()]
    listed = subprocess.run(["gh", "release", "list", "--limit", "1000", "--json", "tagName"],
                            capture_output=True, text=True)
    if listed.returncode != 0:
        raise BuildError(f"gh release list failed: {listed.stderr.strip()[:300]}")
    existing = {r["tagName"] for r in json.loads(listed.stdout or "[]")}
    created = []
    for item in releases_due(rows, existing):
        notes = out / f"{item['stem']}.release-notes.md"
        notes.write_text(item["notes"], encoding="utf-8")
        made = subprocess.run(
            ["gh", "release", "create", item["tag"], str(out / "issues" / f"{item['stem']}.md"),
             "--target", target, "--title", item["title"], "--notes-file", str(notes), "--latest=false"],
            capture_output=True, text=True)
        if made.returncode != 0:
            raise BuildError(f"gh release create {item['tag']} failed: {made.stderr.strip()[:300]}")
        created.append(item["tag"])
    return created


def upload(out: pathlib.Path, token: str) -> str | None:  # pragma: no cover - network
    """One commit with every file in out; files no longer built are deleted from the repo. Returns the commit url."""
    from huggingface_hub import HfApi

    api = HfApi(token=token)
    api.create_repo(REPO_ID, repo_type="dataset", exist_ok=True)
    count = sum(1 for _ in (out / "issues").glob("*.md"))
    info = api.upload_folder(
        repo_id=REPO_ID,
        repo_type="dataset",
        folder_path=str(out),
        commit_message=f"Sync the newsletter from rnd {os.environ.get('SOURCE_SHA') or 'unknown'} ({count} issues)",
        delete_patterns=["issues/*.md"],
    )
    return getattr(info, "commit_url", None) or str(info)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("step", choices=("build", "upload", "npm-plan", "pypi-package", "pypi-plan", "releases"))
    parser.add_argument("--out", type=pathlib.Path, default=pathlib.Path("nl-out"))
    parser.add_argument("--pkg", type=pathlib.Path, default=pathlib.Path("nl-pkg"))
    parser.add_argument("--version", help="pypi steps: the version npm planned, 1.<issue>.<revision>")
    args = parser.parse_args(argv)
    try:
        if args.step == "build":
            rows = build(args.out)
            print(f"built {len(rows)} issues into {args.out}")
            return 0
        if args.step == "releases":  # pragma: no cover - network
            target = os.environ.get("SOURCE_SHA", "")
            if not re.fullmatch(r"[0-9a-f]{40}", target):
                raise BuildError("SOURCE_SHA must be the 40-hex commit the issues were built from")
            created = github_releases(args.out, target)
            print(f"GitHub releases created at rnd {target}: {', '.join(created) or 'none due'}")
            return 0
        if args.step in ("pypi-package", "pypi-plan"):
            if not args.version or not re.fullmatch(r"1\.\d+\.\d+", args.version):
                raise BuildError(f"--version must be 1.<issue>.<revision>, got {args.version!r}")
            build_pypi(args.out, args.pkg, args.version, (ROOT / "LICENSE").read_text(encoding="utf-8"))
            if args.step == "pypi-package":
                print(f"{PYPI_NAME} {args.version} assembled in {args.pkg}")
                return 0
            publish = not pypi_has(args.version)  # pragma: no cover - network
            source = os.environ.get("SOURCE_SHA", "unknown")  # pragma: no cover - network
            print(f"{PYPI_NAME} {args.version} from rnd {source}: "  # pragma: no cover - network
                  f"{'publish' if publish else 'already on PyPI, skip'}")
            if os.environ.get("GITHUB_OUTPUT"):  # pragma: no cover - network
                with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
                    fh.write(f"publish={'true' if publish else 'false'}\n")
            return 0  # pragma: no cover - network
        if args.step == "npm-plan":  # pragma: no cover - network
            rows = [json.loads(x) for x in (args.out / "data" / "issues.jsonl").read_text(encoding="utf-8").splitlines()]
            version, publish = plan_version(rows[-1]["issue"], npm_published(), content_digest(args.out))
            build_npm(args.out, args.pkg, version)
            source = os.environ.get("SOURCE_SHA", "unknown")
            print(f"{NPM_NAME}@{version} from rnd {source}: {'publish' if publish else 'already published, skip'}")
            if os.environ.get("GITHUB_OUTPUT"):
                with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
                    fh.write(f"version={version}\npublish={'true' if publish else 'false'}\n")
            return 0
    except BuildError as exc:
        print(json.dumps({"code": "build", "message": str(exc), "hint": "fix the issue file or the npm state"}),
              file=sys.stderr)
        return 1
    token = os.environ.get("HF_TOKEN", "")
    if not token:
        print(json.dumps({"code": "no-token", "message": "HF_TOKEN is not set", "hint": "run in the workflow"}),
              file=sys.stderr)
        return 2
    print(f"uploaded: {upload(args.out, token)}")  # pragma: no cover - network
    return 0  # pragma: no cover - network


if __name__ == "__main__":
    sys.exit(main())
