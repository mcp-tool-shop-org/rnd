"""Offline tests for site/scripts/newsletter_publish.py: the build, the npm package and the version plan. No network."""
import importlib.util
import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("newsletter_publish", ROOT / "site" / "scripts" / "newsletter_publish.py")
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


class NpmTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = pathlib.Path(self._tmp.name)
        self.src = self.tmp / "newsletter"
        self.src.mkdir()
        write(self.src, "issue-01.md", 1)
        write(self.src, "issue-02.md", 2)
        self.out = self.tmp / "out"
        sync.build(self.out, self.src)
        self.digest = sync.content_digest(self.out)

    def tearDown(self):
        self._tmp.cleanup()

    def test_version_derivation(self):
        self.assertEqual(sync.plan_version(2, {}, self.digest), ("1.2.0", True))
        self.assertEqual(sync.plan_version(2, {"0.0.0": None, "1.1.0": "a", "1.1.3": "b"}, self.digest), ("1.2.0", True))
        self.assertEqual(sync.plan_version(2, {"1.2.0": "older", "1.2.1": "old"}, self.digest), ("1.2.2", True))
        # an older revision without a readable digest doesn't matter; only the newest is compared
        self.assertEqual(sync.plan_version(2, {"1.2.0": None, "1.2.1": "old"}, self.digest), ("1.2.2", True))
        self.assertEqual(sync.plan_version(12, {"1.1.0": self.digest}, self.digest), ("1.12.0", True))

    def test_an_unreadable_digest_on_the_newest_version_refuses_instead_of_republishing(self):
        with self.assertRaises(sync.BuildError):
            sync.plan_version(2, {"1.2.0": "older", "1.2.1": None}, self.digest)
        with self.assertRaises(sync.BuildError):
            sync.plan_version(2, {"1.2.0": None}, self.digest)

    def test_rerun_with_the_same_content_skips(self):
        self.assertEqual(sync.plan_version(2, {"1.2.0": "older", "1.2.1": self.digest}, self.digest), ("1.2.1", False))
        sync.build(self.out, self.src)
        self.assertEqual(sync.content_digest(self.out), self.digest)

    def test_a_correction_changes_the_digest(self):
        (self.src / "issue-01.md").write_text(ISSUE.format(n=1, extra="").replace("First.", "First, corrected."),
                                              encoding="utf-8")
        sync.build(self.out, self.src)
        self.assertNotEqual(sync.content_digest(self.out), self.digest)

    def test_package_contents(self):
        pkg = self.tmp / "pkg"
        sync.build_npm(self.out, pkg, "1.2.0")
        files = sorted(p.relative_to(pkg).as_posix() for p in pkg.rglob("*") if p.is_file())
        self.assertEqual(files, ["README.md", "data/issues.jsonl", "index.json", "issues/issue-01.md",
                                 "issues/issue-02.md", "package.json"])
        manifest = json.loads((pkg / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "@rnd-news/newsletter")
        self.assertEqual(manifest["version"], "1.2.0")
        self.assertEqual(manifest["author"], "mcp-tool-shop")
        self.assertEqual(manifest["license"], "MIT")
        self.assertEqual(manifest["repository"]["url"], "git+https://github.com/mcp-tool-shop-org/rnd.git")
        self.assertEqual(manifest["homepage"], sync.SITE + "newsletter/")
        self.assertEqual(manifest["main"], "index.json")
        self.assertEqual(manifest["contentSha256"], self.digest)
        self.assertEqual(set(manifest["files"]), {"README.md", "index.json", "data/issues.jsonl", "issues/"})
        index = json.loads((pkg / "index.json").read_text(encoding="utf-8"))
        self.assertEqual([e["issue"] for e in index], [1, 2])
        self.assertEqual(index[0]["file"], "issues/issue-01.md")
        self.assertNotIn("body_markdown", index[0])
        self.assertEqual((pkg / "data" / "issues.jsonl").read_bytes(), (self.out / "data" / "issues.jsonl").read_bytes())
        readme = (pkg / "README.md").read_text(encoding="utf-8")
        self.assertFalse(readme.startswith("---"))
        self.assertIn('require("@rnd-news/newsletter")', readme)
        self.assertIn("`index.json`", readme)
        self.assertNotIn("load_dataset", readme)


class PypiTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = pathlib.Path(self._tmp.name)
        self.src = self.tmp / "newsletter"
        self.src.mkdir()
        write(self.src, "issue-01.md", 1)
        write(self.src, "issue-03.md", 3)
        self.out = self.tmp / "out"
        sync.build(self.out, self.src)
        self.pkg = self.tmp / "pypi"

    def tearDown(self):
        self._tmp.cleanup()

    def test_package_contents(self):
        sync.build_pypi(self.out, self.pkg, "1.3.0", "MIT License\n")
        files = sorted(p.relative_to(self.pkg).as_posix() for p in self.pkg.rglob("*") if p.is_file())
        self.assertEqual(files, ["LICENSE", "README.md", "pyproject.toml", "src/rnd_newsletter/__init__.py",
                                 "src/rnd_newsletter/data/issues.jsonl", "src/rnd_newsletter/data/issues/issue-01.md",
                                 "src/rnd_newsletter/data/issues/issue-03.md"])
        pyproject = (self.pkg / "pyproject.toml").read_text(encoding="utf-8")
        for line in ('name = "mcptoolshop-rnd-newsletter"', 'version = "1.3.0"', 'requires-python = ">=3.10"',
                     'license = "MIT"', 'dependencies = []', '{ name = "mcp-tool-shop" }',
                     'rnd_newsletter = ["data/issues.jsonl", "data/issues/*.md"]',
                     '"Hugging Face" = "https://huggingface.co/datasets/mcp-tool-shop/rnd-newsletter"',
                     'npm = "https://www.npmjs.com/package/@rnd-news/newsletter"'):
            self.assertIn(line, pyproject)
        readme = (self.pkg / "README.md").read_text(encoding="utf-8")
        self.assertIn("import rnd_newsletter", readme)
        self.assertNotIn("require(", readme)
        self.assertNotIn("index.json", readme)

    def test_the_api_on_a_fixture(self):
        sync.build_pypi(self.out, self.pkg, "1.3.0", "MIT License\n")
        spec = importlib.util.spec_from_file_location(
            "rnd_newsletter", self.pkg / "src" / "rnd_newsletter" / "__init__.py",
            submodule_search_locations=[str(self.pkg / "src" / "rnd_newsletter")])
        module = importlib.util.module_from_spec(spec)
        with mock.patch.dict("sys.modules", {"rnd_newsletter": module}):
            spec.loader.exec_module(module)
            self.assertEqual(module.__version__, "1.3.0")
            self.assertEqual([i["issue"] for i in module.issues()], [1, 3])
            self.assertEqual(module.latest()["issue"], 3)
            self.assertEqual(module.issue(1)["title"], 'A "quoted" title: with a colon')
            with self.assertRaises(KeyError):
                module.issue(2)

    def test_cli_needs_a_version_in_npm_form(self):
        self.assertEqual(sync.main(["pypi-package", "--out", str(self.out), "--pkg", str(self.pkg)]), 1)
        self.assertEqual(sync.main(["pypi-package", "--out", str(self.out), "--pkg", str(self.pkg), "--version", "2.0"]), 1)
        self.assertEqual(sync.main(["pypi-package", "--out", str(self.out), "--pkg", str(self.pkg), "--version", "1.3.0"]), 0)
        self.assertTrue((self.pkg / "pyproject.toml").is_file())


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = pathlib.Path(self._tmp.name)
        self.src = self.tmp / "newsletter"
        self.src.mkdir()
        for n in (29, 30, 31):
            write(self.src, f"issue-{n}.md", n)
        self.rows = sync.build(self.tmp / "out", self.src)

    def tearDown(self):
        self._tmp.cleanup()

    def test_tags_never_look_like_tool_versions(self):
        self.assertEqual(sync.release_tag("issue-30"), "newsletter-issue-30")
        self.assertNotRegex(sync.release_tag("issue-30"), r"^v\d+(\.\d+){4}$")

    def test_only_new_issues_from_30_are_due(self):
        due = sync.releases_due(self.rows, existing=set())
        self.assertEqual([d["tag"] for d in due], ["newsletter-issue-30", "newsletter-issue-31"])
        due = sync.releases_due(self.rows, existing={"newsletter-issue-30", "v1.1.23.1.35"})
        self.assertEqual([d["tag"] for d in due], ["newsletter-issue-31"])
        self.assertEqual(sync.releases_due(self.rows, existing={"newsletter-issue-30", "newsletter-issue-31"}), [])

    def test_release_title_and_notes(self):
        item = sync.releases_due(self.rows, existing=set())[0]
        self.assertEqual(item["title"], 'A "quoted" title: with a colon')
        self.assertEqual(item["stem"], "issue-30")
        notes = item["notes"]
        self.assertTrue(notes.startswith("Plain description.\n"))
        self.assertIn("- One. First.", notes)
        self.assertNotIn("<strong>", notes)
        for link in (sync.SITE + "newsletter/issue-30/", "https://huggingface.co/datasets/mcp-tool-shop/rnd-newsletter",
                     "https://www.npmjs.com/package/@rnd-news/newsletter",
                     "https://pypi.org/project/mcptoolshop-rnd-newsletter/"):
            self.assertIn(link, notes)
        self.assertIn("`issue-30.md`", notes)


if __name__ == "__main__":
    unittest.main()
