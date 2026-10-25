"""Publish the rnd newsletter to Hugging Face as the dataset repo mcp-tool-shop/rnd-newsletter.

Two steps, so the build can be tested offline and the token is only present for the upload:

  python site/scripts/hf_newsletter_sync.py build --out hf-out
  python site/scripts/hf_newsletter_sync.py upload --out hf-out      # needs HF_TOKEN and huggingface_hub

The build reads only published issues: site/src/content/docs/newsletter/issue-*.md on the checked-out branch, with
an integer `issue` in the front matter and no `draft: true`. Drafts and held articles live outside this repository,
so they can't reach it. It writes:

  issues/issue-NN.md    each issue's front matter and Markdown, with site links made absolute
  data/issues.jsonl     one row per issue: issue, date, title, description, highlights, url, body_markdown
  README.md             the dataset card

The output is byte-for-byte the same for the same issues, so a rerun changes nothing. The upload is one
upload_folder commit; huggingface_hub skips the commit when no file differs from the repo, so a run with no new
issue makes no commit.

Standards compliance (workflow standards, scored 0-3):
- PIN_PER_STEP 2: huggingface_hub and every action are pinned in .github/workflows/hf-newsletter.yml; the build is
  deterministic from the checked-out commit.
- ANDON_AUTHORITY 2: any parse error, a duplicate issue number or a file name that doesn't match its issue number
  stops the build before anything is uploaded.
- NAMED_COMPENSATORS 2: the one irreversible step is an HF dataset commit (see the compensators table in the
  workflow file).
- DECOMPOSE_BY_SECRETS 2: build (no secret) and upload (HF_TOKEN only) are separate steps.
- UNCERTAINTY_GATED_HUMANS 2: the newsletter is already public and Director-approved before it reaches main; this
  only mirrors it. The first backfill is a manual workflow_dispatch run.
- EXTERNAL_VERIFIER: n/a, no specialized claims.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
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
        commit_message=f"Sync the newsletter from rnd ({count} issues)",
        delete_patterns=["issues/*.md"],
    )
    return getattr(info, "commit_url", None) or str(info)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("step", choices=("build", "upload"))
    parser.add_argument("--out", type=pathlib.Path, default=pathlib.Path("hf-out"))
    args = parser.parse_args(argv)
    if args.step == "build":
        try:
            rows = build(args.out)
        except BuildError as exc:
            print(json.dumps({"code": "build", "message": str(exc), "hint": "fix the issue file"}), file=sys.stderr)
            return 1
        print(f"built {len(rows)} issues into {args.out}")
        return 0
    token = os.environ.get("HF_TOKEN", "")
    if not token:
        print(json.dumps({"code": "no-token", "message": "HF_TOKEN is not set", "hint": "run in the workflow"}),
              file=sys.stderr)
        return 2
    print(f"uploaded: {upload(args.out, token)}")  # pragma: no cover - network
    return 0  # pragma: no cover - network


if __name__ == "__main__":
    sys.exit(main())
