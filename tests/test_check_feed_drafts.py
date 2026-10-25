"""A newsletter page marked draft: true must never reach the feed, which Buttondown emails to subscribers."""
import importlib.util
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("check_feed", ROOT / "site" / "scripts" / "check_feed.py")
check_feed = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_feed)

PAGE = "---\ntitle: T\ndescription: D\nissue: {n}\ndate: 2026-10-25\n{extra}---\n\nBody. draft: true in the body doesn't count.\n"


class DraftTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self._tmp.name)
        (self.dir / "issue-30.md").write_text(PAGE.format(n=30, extra=""), encoding="utf-8")
        (self.dir / "issue-31.md").write_text(PAGE.format(n=31, extra="draft: true\n"), encoding="utf-8")
        (self.dir / "issue-32.md").write_text(PAGE.format(n=32, extra="draft: false\n").replace("\n", "\r\n"),
                                              encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_is_draft_reads_only_the_front_matter(self):
        self.assertFalse(check_feed.is_draft(self.dir / "issue-30.md"))
        self.assertTrue(check_feed.is_draft(self.dir / "issue-31.md"))
        self.assertFalse(check_feed.is_draft(self.dir / "issue-32.md"))

    def test_published_pages_leave_drafts_out(self):
        published, drafts = check_feed.published_pages(self.dir)
        self.assertEqual([p.name for p in published], ["issue-30.md", "issue-32.md"])
        self.assertEqual([p.name for p in drafts], ["issue-31.md"])

    def test_a_draft_in_the_feed_is_an_error(self):
        _, drafts = check_feed.published_pages(self.dir)
        site = check_feed.SITE + "newsletter/"
        self.assertEqual(check_feed.draft_errors([site + "issue-30/", site + "issue-32/"], drafts), [])
        errors = check_feed.draft_errors([site + "issue-30/", site + "issue-31/"], drafts)
        self.assertEqual(len(errors), 1)
        self.assertIn("issue-31.md is a draft", errors[0])

    def test_the_repository_has_no_draft_issue_in_its_published_set(self):
        published, drafts = check_feed.published_pages()
        self.assertTrue(published)
        self.assertFalse(set(published) & set(drafts))


if __name__ == "__main__":
    unittest.main()
