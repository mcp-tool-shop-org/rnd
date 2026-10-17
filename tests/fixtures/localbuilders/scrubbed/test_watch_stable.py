import unittest
from mcptoolshop_rnd import watch


class StableLatestTests(unittest.TestCase):
    def test_latest_skips_prerelease(self):
        sources = [{"id": "s", "kind": "github-releases", "url": "https://github.com/org/repo"}]
        releases = [
            {"tag_name": "v2.0.0-rc1", "prerelease": True, "published_at": "2026-10-02T00:00:00Z"},
            {"tag_name": "v1.9.0", "prerelease": False, "published_at": "2026-10-01T00:00:00Z"},
        ]
        rep, _ = watch.check(sources, {}, github=lambda *a: releases, now="t")
        self.assertEqual(rep["sources"][0]["latest"]["key"], "v1.9.0")
        self.assertEqual(rep["sources"][0]["latest_prerelease"]["key"], "v2.0.0-rc1")
