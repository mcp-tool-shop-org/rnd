"""Offline tests for site/scripts/hf_newsletter_sync.py: the build step only, no network and no token."""
import importlib.util
import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("hf_newsletter_sync", ROOT / "site" / "scripts" / "hf_newsletter_sync.py")
sync = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync)

ISSUE = """---
title: "A \\"quoted\\" title: with a colon"
description: Plain description.
issue: {n}
date: 2026-10-2{n}
highlights:
  - "<strong>One.</strong> First."
  - "Two."
{extra}---

Body of issue {n}. A [brief](../../briefs/math-ladder/), a chart ![c](/rnd/charts/c.svg),
an [outside link](https://example.org/x), a [same-page anchor](#below) and <a href="/rnd/newsletter/">html</a>.
"""


def write(folder: pathlib.Path, name: str, n: int, extra: str = "") -> None:
    (folder / name).write_text(ISSUE.format(n=n, extra=extra), encoding="utf-8")


class BuildTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = pathlib.Path(self._tmp.name)
        self.src = self.tmp / "newsletter"
        self.src.mkdir()
        self.out = self.tmp / "out"

    def tearDown(self):
        self._tmp.cleanup()

    def rows(self):
        return [json.loads(line) for line in (self.out / "data" / "issues.jsonl").read_text(encoding="utf-8").splitlines()]

    def test_files_and_rows(self):
        write(self.src, "issue-02.md", 2)
        write(self.src, "issue-01.md", 1)
        (self.src / "subscribe.md").write_text("---\ntitle: Subscribe\n---\n\nnot an issue\n", encoding="utf-8")
        built = sync.build(self.out, self.src)
        self.assertEqual([r["issue"] for r in built], [1, 2])
        self.assertEqual(sorted(p.name for p in (self.out / "issues").iterdir()), ["issue-01.md", "issue-02.md"])
        rows = self.rows()
        self.assertEqual([r["issue"] for r in rows], [1, 2])
        self.assertEqual(list(rows[0]), list(sync.FIELDS))
        first = rows[0]
        self.assertEqual(first["title"], 'A "quoted" title: with a colon')
        self.assertEqual(first["date"], "2026-10-21")
        self.assertEqual(first["highlights"], ["<strong>One.</strong> First.", "Two."])
        self.assertEqual(first["url"], sync.SITE + "newsletter/issue-01/")
        body = first["body_markdown"]
        self.assertIn("](https://mcp-tool-shop-org.github.io/rnd/briefs/math-ladder/)", body)
        self.assertIn("](https://mcp-tool-shop-org.github.io/rnd/charts/c.svg)", body)
        self.assertIn("](https://example.org/x)", body)
        self.assertIn("](#below)", body)
        self.assertIn('href="https://mcp-tool-shop-org.github.io/rnd/newsletter/"', body)
        card = (self.out / "README.md").read_text(encoding="utf-8")
        self.assertIn("license: mit", card)
        self.assertIn("It holds 2 issues.", card)
        self.assertIn(sync.FEED, card)
        self.assertIn('load_dataset("mcp-tool-shop/rnd-newsletter"', card)
        page = (self.out / "issues" / "issue-01.md").read_text(encoding="utf-8")
        self.assertTrue(page.startswith("---\nissue: 1\n"))
        self.assertIn("Body of issue 1.", page)

    def test_drafts_and_files_without_an_issue_number_are_left_out(self):
        write(self.src, "issue-01.md", 1)
        write(self.src, "issue-02.md", 2, extra="draft: true\n")
        (self.src / "issue-03.md").write_text("---\ntitle: Held\ndescription: x\ndate: 2026-10-25\n---\n\nheld\n",
                                              encoding="utf-8")
        sync.build(self.out, self.src)
        self.assertEqual([r["issue"] for r in self.rows()], [1])
        self.assertEqual([p.name for p in (self.out / "issues").iterdir()], ["issue-01.md"])

    def test_rebuild_is_byte_identical_and_drops_removed_issues(self):
        write(self.src, "issue-01.md", 1)
        write(self.src, "issue-02.md", 2)
        sync.build(self.out, self.src)
        before = {p.relative_to(self.out): p.read_bytes() for p in self.out.rglob("*") if p.is_file()}
        sync.build(self.out, self.src)
        after = {p.relative_to(self.out): p.read_bytes() for p in self.out.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        (self.src / "issue-02.md").write_text(ISSUE.format(n=2, extra="draft: true\n"), encoding="utf-8")
        sync.build(self.out, self.src)
        self.assertFalse((self.out / "issues" / "issue-02.md").exists())

    def test_inconsistent_issues_stop_the_build(self):
        write(self.src, "issue-07.md", 8)
        with self.assertRaises(sync.BuildError):
            sync.build(self.out, self.src)
        (self.src / "issue-07.md").unlink()
        write(self.src, "issue-01.md", 1)
        write(self.src, "issue-001.md", 1)
        with self.assertRaises(sync.BuildError):
            sync.build(self.out, self.src)

    def test_unreadable_front_matter_stops_the_build(self):
        (self.src / "issue-01.md").write_text("no front matter\n", encoding="utf-8")
        with self.assertRaises(sync.BuildError):
            sync.build(self.out, self.src)
        (self.src / "issue-01.md").write_text("---\nissue: 1\n", encoding="utf-8")
        with self.assertRaises(sync.BuildError):
            sync.build(self.out, self.src)
        (self.src / "issue-01.md").write_text('---\nissue: 1\ntitle: "broken\n---\n\nx\n', encoding="utf-8")
        with self.assertRaises(sync.BuildError):
            sync.build(self.out, self.src)
        (self.src / "issue-01.md").write_text("---\nissue: 1\ndate: 2026-10-01\ndescription: d\n---\n\nx\n",
                                              encoding="utf-8")
        with self.assertRaises(sync.BuildError):
            sync.build(self.out, self.src)

    def test_cli_build_and_missing_token(self):
        out = self.tmp / "cli-out"
        self.assertEqual(sync.main(["build", "--out", str(out)]), 0)
        self.assertTrue((out / "data" / "issues.jsonl").is_file())
        with mock.patch.dict(os.environ, {"HF_TOKEN": ""}):
            self.assertEqual(sync.main(["upload", "--out", str(out)]), 2)

    def test_every_published_issue_in_the_repository_parses(self):
        rows = sync.published_issues()
        numbers = [r["issue"] for r in rows]
        self.assertGreaterEqual(len(rows), 28)
        self.assertEqual(numbers, sorted(set(numbers)))
        for row in rows:
            self.assertTrue(row["title"] and row["description"] and row["body_markdown"])
            self.assertRegex(row["date"], r"^\d{4}-\d{2}-\d{2}$")


if __name__ == "__main__":
    unittest.main()
