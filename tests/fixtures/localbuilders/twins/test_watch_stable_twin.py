import unittest
from mcptoolshop_rnd import watch


class StableLatestTwinTests(unittest.TestCase):
    def test_latest_prefers_stable_and_reports_prerelease(self):
        sources = [{"id": "pkg", "kind": "github-releases", "url": "https://github.com/example/pkg"}]
        releases = [
            {"tag_name": "v5.1.0-beta2", "prerelease": True, "published_at": "2026-10-10T00:00:00Z"},
            {"tag_name": "v5.0.2", "prerelease": False, "published_at": "2026-10-05T00:00:00Z"},
        ]
        rep, _ = watch.check(sources, {}, github=lambda *a: releases, now="t")
        self.assertEqual(rep["sources"][0]["latest"]["key"], "v5.0.2")
        self.assertEqual(rep["sources"][0]["latest_prerelease"]["key"], "v5.1.0-beta2")
