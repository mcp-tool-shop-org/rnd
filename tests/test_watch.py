"""rnd watch.

The parsers run on responses recorded from the live sources on 2026-10-13 (tests/fixtures/watch/, trimmed to the
fields read), and the page test uses the pattern from the shipped watchlist, so a change to either is caught here.
"""

import io
import json
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from mcptoolshop_rnd import cli, watch

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures" / "watch"
WATCHLIST = HERE.parent / "docs" / "watchlist.json"


def text(name):
    return (FIX / name).read_text(encoding="utf-8")


def fixture(name):
    return json.loads(text(name))


class ParserTests(unittest.TestCase):
    def test_releases_from_recorded_response(self):
        items = watch.from_releases(fixture("github-releases.json"))
        self.assertEqual(len(items), 3)
        self.assertTrue(items[0]["key"].startswith("v0.40"))
        self.assertTrue(items[0]["url"].startswith("https://github.com/ollama/ollama/releases/tag/"))

    def test_drafts_are_skipped(self):
        rows = [{"tag_name": "v2", "draft": True}, {"tag_name": "v1", "published_at": "2026-10-01T00:00:00Z"}]
        self.assertEqual([i["key"] for i in watch.from_releases(rows)], ["v1"])

    def test_commits_from_recorded_response(self):
        items = watch.from_commits(fixture("github-commits.json"))
        self.assertEqual(len(items[0]["key"]), 12)
        self.assertTrue(items[0]["title"])
        self.assertEqual(watch.from_commits([{"sha": "a" * 40, "commit": {"message": ""}}])[0]["title"], "")

    def test_hf_listing_from_recorded_response(self):
        items = watch.from_hf_list(fixture("hf-models.json"))
        self.assertTrue(all(i["key"].startswith("nvidia/") for i in items))
        self.assertEqual(items[0]["url"], f"https://huggingface.co/{items[0]['key']}")

    def test_atom_feed_takes_the_alternate_link_not_the_replies_link(self):
        items = watch.from_feed(text("feed-atom.xml"))
        self.assertEqual(len(items), 3)
        self.assertTrue(items[0]["key"].startswith("https://developer.nvidia.com/blog/?p="))
        self.assertNotIn("#comments", items[0]["url"])
        self.assertTrue(items[0]["title"].startswith("NVIDIA Run:ai"))
        self.assertEqual(items[0]["date"], "2026-10-13T14:19:40Z")

    def test_rss_feed_from_recorded_response(self):
        items = watch.from_feed(text("feed-rss.xml"))
        self.assertEqual([i["title"] for i in items], ["0.10.0", "0.10.0rc4", "0.10.0rc3"])
        self.assertEqual(items[0]["key"], "https://pypi.org/project/nemo-relay/0.10.0/")

    def test_cuda_page_with_the_shipped_pattern(self):
        src = next(s for s in watch.load_watchlist(WATCHLIST) if s["id"] == "cuda-toolkit")
        items = watch.from_page(text("cuda-page.html"), src["pattern"], src["url"])
        self.assertEqual([i["key"] for i in items], ["CUDA Toolkit 13.4 Update 2"])


class FetchTests(unittest.TestCase):
    def test_each_kind_goes_to_its_source(self):
        calls = []

        def github(path, *fields):
            calls.append(path)
            return fixture("github-commits.json")

        pages = {"https://hf.test/api": text("hf-models.json"), "https://docs.test/notes": text("cuda-page.html")}
        commits = watch.fetch_items({"kind": "github-commits", "url": "https://github.com/NVIDIA/skills"},
                                    github=github, fetch=pages.get)
        models = watch.fetch_items({"kind": "huggingface", "url": "https://hf.test/api"}, github=github, fetch=pages.get)
        page = watch.fetch_items({"kind": "page", "url": "https://docs.test/notes", "pattern": r"<title>(CUDA Toolkit [\d.]+)"},
                                 github=github, fetch=pages.get)
        self.assertEqual(calls, ["repos/NVIDIA/skills/commits"])
        self.assertEqual(len(commits[0]["key"]), 12)
        self.assertTrue(models[0]["key"].startswith("nvidia/"))
        self.assertEqual(page[0]["key"], "CUDA Toolkit 13.4")


class WatchlistTests(unittest.TestCase):
    def test_unreadable_watchlist(self):
        with self.assertRaises(watch.WatchError) as ctx:
            watch.load_watchlist(FIX / "missing.json")
        self.assertEqual(ctx.exception.code, "WATCHLIST_UNREADABLE")

    def test_shipped_watchlist_loads(self):
        sources = watch.load_watchlist(WATCHLIST)
        self.assertGreaterEqual(len(sources), 10)
        self.assertTrue(all(s.get("why") for s in sources))

    def test_invalid_watchlists_are_refused(self):
        bad = [
            [{"id": "a", "kind": "rss-ish", "url": "x"}],
            [{"id": "a", "kind": "feed", "url": "x"}, {"id": "a", "kind": "feed", "url": "y"}],
            [{"id": "a", "kind": "github-releases", "url": "https://gitlab.com/a/b"}],
            [{"id": "a", "kind": "page", "url": "x", "pattern": "no group"}],
            [{"id": "a", "kind": "page", "url": "x", "pattern": "(unclosed"}],
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "w.json"
            for sources in bad:
                path.write_text(json.dumps({"sources": sources}), encoding="utf-8")
                with self.assertRaises(watch.WatchError) as ctx:
                    watch.load_watchlist(path)
                self.assertEqual(ctx.exception.code, "WATCHLIST_INVALID")


SOURCES = [
    {"id": "rel", "kind": "github-releases", "url": "https://github.com/o/r", "why": "w"},
    {"id": "blog", "kind": "feed", "url": "https://example.test/feed", "why": "w"},
]


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.releases = [{"tag_name": "v2", "published_at": "2026-10-02T00:00:00Z"},
                         {"tag_name": "v1", "published_at": "2026-10-01T00:00:00Z"}]
        self.feed = text("feed-atom.xml")

    def github(self, path, *fields):
        self.assertEqual(path, "repos/o/r/releases")
        return self.releases

    def fetch(self, url):
        if isinstance(self.feed, Exception):
            raise self.feed
        return self.feed

    def test_first_run_is_a_baseline_and_reports_nothing_new(self):
        rep, state = watch.check(SOURCES, {}, github=self.github, fetch=self.fetch, now="t1")
        self.assertEqual(rep["new_total"], 0)
        self.assertTrue(all(r["baseline"] for r in rep["sources"]))
        self.assertEqual(state["rel"]["seen"], ["v2", "v1"])
        self.assertEqual(rep["sources"][0]["latest"]["key"], "v2")

    def test_second_run_reports_only_the_new_items_newest_first(self):
        _, state = watch.check(SOURCES, {}, github=self.github, fetch=self.fetch, now="t1")
        self.releases.insert(0, {"tag_name": "v3", "published_at": "2026-10-03T00:00:00Z"})
        rep, state2 = watch.check(SOURCES, state, github=self.github, fetch=self.fetch, now="t2")
        rel = rep["sources"][0]
        self.assertEqual([i["key"] for i in rel["new"]], ["v3"])
        self.assertFalse(rel["baseline"])
        self.assertEqual(state2["rel"]["seen"][:3], ["v3", "v2", "v1"])
        self.assertEqual(rep["new_total"], 1)
        self.assertEqual(state["rel"]["seen"], ["v2", "v1"], "the state passed in is not changed")

    def test_unreachable_source_is_unknown_and_its_state_is_kept(self):
        _, state = watch.check(SOURCES, {}, github=self.github, fetch=self.fetch, now="t1")
        self.feed = urllib.error.URLError("down")
        rep, state2 = watch.check(SOURCES, state, github=self.github, fetch=self.fetch, now="t2")
        blog = rep["sources"][1]
        self.assertIn("URLError", blog["unknown"])
        self.assertEqual(rep["unknown"], ["blog"])
        self.assertEqual(state2["blog"], state["blog"])

    def test_malformed_feed_is_unknown_not_a_crash(self):
        self.feed = "<feed><entry>"
        rep, state = watch.check(SOURCES, {}, github=self.github, fetch=self.fetch, now="t1")
        self.assertIn("ParseError", rep["sources"][1]["unknown"])
        self.assertNotIn("blog", state)

    def test_only_limits_the_check_and_leaves_other_state_alone(self):
        prior = {"blog": {"seen": ["x"], "checked": "t0"}}
        rep, state = watch.check(SOURCES, prior, github=self.github, fetch=self.fetch, only={"rel"}, now="t1")
        self.assertEqual([r["id"] for r in rep["sources"]], ["rel"])
        self.assertEqual(state["blog"], prior["blog"])

    def test_seen_keys_are_capped(self):
        prior = {"rel": {"seen": [f"old{i}" for i in range(watch.KEEP)], "checked": "t0"}}
        _, state = watch.check(SOURCES[:1], prior, github=self.github, fetch=self.fetch, now="t1")
        self.assertEqual(len(state["rel"]["seen"]), watch.KEEP)
        self.assertEqual(state["rel"]["seen"][:2], ["v2", "v1"])


class StateTests(unittest.TestCase):
    def test_missing_state_is_empty_and_save_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sub" / "state.json"
            self.assertEqual(watch.load_state(path), {})
            watch.save_state(path, {"a": {"seen": ["é"], "checked": "t"}})
            self.assertEqual(watch.load_state(path)["a"]["seen"], ["é"])

    def test_corrupt_state_is_refused_not_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text("{not json", encoding="utf-8")
            with self.assertRaises(watch.WatchError) as ctx:
                watch.load_state(path)
            self.assertEqual(ctx.exception.code, "WATCH_STATE_UNREADABLE")


class CliTests(unittest.TestCase):
    def setUp(self):
        # --library sets the module's ROOT; put it back so later tests see the real library.
        self.addCleanup(setattr, cli, "ROOT", cli.ROOT)

    def run_cli(self, *argv):
        out = io.StringIO()
        with redirect_stdout(out):
            code = cli.main(["--library", str(HERE.parent), *argv])
        return code, out.getvalue()

    def test_watch_saves_state_and_no_save_does_not(self):
        canned = {"rel": [{"key": "v1", "title": "v1", "date": None, "url": None}]}
        listing = [{"id": "rel", "kind": "github-releases", "url": "https://github.com/o/r", "why": "w"}]
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(watch, "fetch_items", side_effect=lambda s, **kw: canned[s["id"]]):
            wl, state = Path(tmp) / "w.json", Path(tmp) / "state.json"
            wl.write_text(json.dumps({"sources": listing}), encoding="utf-8")
            code, out = self.run_cli("watch", "--list", str(wl), "--state", str(state), "--no-save")
            self.assertEqual(code, 0)
            self.assertIn("baseline recorded", out)
            self.assertFalse(state.exists())
            code, out = self.run_cli("watch", "--list", str(wl), "--state", str(state), "--json")
            self.assertEqual(json.loads(out)["state"], "saved")
            self.assertEqual(watch.load_state(state)["rel"]["seen"], ["v1"])
            canned["rel"].insert(0, {"key": "v2", "title": "v2", "date": "2026-10-13T00:00:00Z", "url": "u"})
            code, out = self.run_cli("watch", "--list", str(wl), "--state", str(state))
            self.assertIn("1 new", out)
            self.assertIn("v2  2026-10-13  u", out)

    def test_unknown_source_and_quiet_source_text(self):
        listing = [{"id": "down", "kind": "feed", "url": "https://example.test/feed", "why": "w"},
                   {"id": "quiet", "kind": "feed", "url": "https://example.test/feed2", "why": "w"}]
        rows = {"down": OSError("refused"), "quiet": [{"key": "a", "title": "A", "date": None, "url": None}]}

        def fake(s, **kw):
            got = rows[s["id"]]
            if isinstance(got, Exception):
                raise got
            return got

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(watch, "fetch_items", side_effect=fake):
            wl, state = Path(tmp) / "w.json", Path(tmp) / "state.json"
            wl.write_text(json.dumps({"sources": listing}), encoding="utf-8")
            state.write_text(json.dumps({"quiet": {"seen": ["a"], "checked": "t0"}}), encoding="utf-8")
            code, out = self.run_cli("watch", "--list", str(wl), "--state", str(state))
        self.assertEqual(code, 0)
        self.assertIn("unknown: OSError: refused", out)
        self.assertIn("nothing new; latest A", out)

    def test_unreadable_state_is_a_structured_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "s.json"
            state.write_text("{", encoding="utf-8")
            code, _ = self.run_cli("watch", "--state", str(state))
        self.assertEqual(code, 2)

    def test_unknown_only_id_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _ = self.run_cli("watch", "--state", str(Path(tmp) / "s.json"), "--only", "nope")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
