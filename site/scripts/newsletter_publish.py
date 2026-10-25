"""Publish the rnd newsletter: to Hugging Face as the dataset mcp-tool-shop/rnd-newsletter, and to npm as
@rnd-news/newsletter. One builder, two uploads, run by .github/workflows/newsletter-publish.yml.

  python site/scripts/newsletter_publish.py build --out nl-out                  # no secrets
  python site/scripts/newsletter_publish.py upload --out nl-out                 # HF_TOKEN + huggingface_hub
  python site/scripts/newsletter_publish.py npm-plan --out nl-out --pkg nl-pkg  # reads npm, writes the package

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
import urllib.parse

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
    parser.add_argument("step", choices=("build", "upload", "npm-plan"))
    parser.add_argument("--out", type=pathlib.Path, default=pathlib.Path("nl-out"))
    parser.add_argument("--pkg", type=pathlib.Path, default=pathlib.Path("nl-pkg"))
    args = parser.parse_args(argv)
    try:
        if args.step == "build":
            rows = build(args.out)
            print(f"built {len(rows)} issues into {args.out}")
            return 0
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
