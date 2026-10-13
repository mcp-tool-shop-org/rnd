"""rnd probe and rnd search --exact.

The probe's parsers run on responses recorded from the live APIs on 2026-10-13 (tests/fixtures/probe/, trimmed to
the fields read), so the tests see the platform's real shapes, not shapes the code assumes.
"""

import json
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mcptoolshop_rnd import probe, store

FIX = Path(__file__).resolve().parent / "fixtures" / "probe"


def fixture(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


class ParserTests(unittest.TestCase):
    def test_github_repo_release_and_telemetry_from_recorded_responses(self):
        out = probe.from_github(fixture("github-repo.json"), fixture("github-release.json"), fixture("github-code.json"))
        self.assertEqual(out["licence"], "Apache-2.0")
        self.assertEqual(out["latest"], "0.10.0")
        self.assertFalse(out["archived"])
        self.assertGreater(out["telemetry_hits"], 0)
        self.assertIn("crates/adaptive/src/acg/telemetry.rs", out["telemetry_paths"])

    def test_huggingface_other_licence_reads_the_card_name(self):
        out = probe.from_huggingface(fixture("hf-model.json"))
        self.assertEqual(out["licence"], "openmdw-1.1")
        self.assertEqual(out["licence_link"], "https://openmdw.ai/license/1-1/")
        self.assertFalse(out["gated"])

    def test_pypi_and_npm_from_recorded_responses(self):
        pypi = probe.from_pypi(fixture("pypi.json"))
        npm = probe.from_npm(fixture("npm.json"))
        self.assertEqual((pypi["licence"], pypi["latest"]), ("Apache-2.0", "0.10.0"))
        self.assertEqual((npm["licence"], npm["latest"]), ("Apache-2.0", "0.10.0"))
        self.assertTrue(pypi["released"].startswith("2026-10-08"))

    def test_noassertion_falls_back_to_the_licence_name_and_gated_strings_count(self):
        repo = {"license": {"spdx_id": "NOASSERTION", "name": "Other"}, "archived": True}
        self.assertEqual(probe.from_github(repo, None, None)["licence"], "Other")
        self.assertTrue(probe.from_huggingface({"gated": "manual", "tags": ["license:mit"]})["gated"])
        self.assertEqual(probe.from_npm({"license": {"type": "MIT"}})["licence"], "MIT")


class UrlTests(unittest.TestCase):
    def test_supported_urls(self):
        cases = {
            "https://github.com/NVIDIA/NeMo-Relay": ("github", "NVIDIA/NeMo-Relay"),
            "https://github.com/NVIDIA/NeMo-Relay.git": ("github", "NVIDIA/NeMo-Relay"),
            "https://huggingface.co/nvidia/Some-Model": ("huggingface", "nvidia/Some-Model"),
            "https://pypi.org/project/nemo-relay/": ("pypi", "nemo-relay"),
            "https://www.npmjs.com/package/@scope/pkg": ("npm", "@scope/pkg"),
        }
        for url, want in cases.items():
            self.assertEqual(probe.kind_of(url), want, url)

    def test_unsupported_url_is_refused(self):
        for url in ("https://example.com/x", "https://huggingface.co/datasets/a/b"):
            with self.assertRaises(probe.ProbeError):
                probe.kind_of(url)


class ProbeFlowTests(unittest.TestCase):
    def test_github_flow_with_recorded_responses_and_library_hits(self):
        answers = {"repos/NVIDIA/NeMo-Relay": fixture("github-repo.json"),
                   "repos/NVIDIA/NeMo-Relay/releases/latest": fixture("github-release.json"),
                   "search/code": fixture("github-code.json")}
        out = probe.probe("https://github.com/NVIDIA/NeMo-Relay", github=lambda path, *f: answers[path],
                          library=lambda name: ["nemo-relay"])
        self.assertEqual(out["licence"], "Apache-2.0")
        self.assertEqual(out["library_hits"], ["nemo-relay"])
        self.assertEqual(out["unknown"], {})

    def test_an_unreachable_source_is_unknown_never_guessed(self):
        def down(*_):
            raise probe.ProbeError("PROBE_GH_FAILED", "HTTP 404")
        out = probe.probe("https://github.com/x/y", github=down)
        self.assertNotIn("licence", out)
        self.assertIn("repository", out["unknown"])

        def no_release(path, *f):
            if path.endswith("releases/latest"):
                raise probe.ProbeError("PROBE_GH_FAILED", "Not Found")
            return fixture("github-repo.json") if path.startswith("repos/") else fixture("github-code.json")
        out = probe.probe("https://github.com/NVIDIA/NeMo-Relay", github=no_release)
        self.assertEqual(out["licence"], "Apache-2.0")
        self.assertIsNone(out["latest"])
        self.assertIn("release", out["unknown"])

    def test_http_flows(self):
        for url, name in (("https://huggingface.co/nvidia/m", "hf-model.json"), ("https://pypi.org/project/p", "pypi.json"),
                          ("https://www.npmjs.com/package/n", "npm.json")):
            out = probe.probe(url, fetch=lambda _u, n=name: fixture(n))
            self.assertIn("licence", out, url)

    def test_gh_reads_utf8_whatever_the_os_codepage(self):
        # Live 2026-10-13: without encoding="utf-8", Windows decoded gh's output as cp1252 and crashed.
        done = subprocess.CompletedProcess([], 0, stdout='{"name": "café"}', stderr="")
        with mock.patch.object(probe.subprocess, "run", return_value=done) as run:
            self.assertEqual(probe.gh_json("repos/a/b"), {"name": "café"})
        self.assertEqual(run.call_args.kwargs.get("encoding"), "utf-8")
        failed = subprocess.CompletedProcess([], 1, stdout="", stderr="gh: Not Found (HTTP 404)")
        with mock.patch.object(probe.subprocess, "run", return_value=failed):
            with self.assertRaises(probe.ProbeError):
                probe.gh_json("repos/a/b")


class CliTests(unittest.TestCase):
    def test_probe_and_exact_search_from_the_cli(self):
        import contextlib
        import io

        from mcptoolshop_rnd import cli

        answers = {"repos/NVIDIA/NeMo-Relay": fixture("github-repo.json"),
                   "repos/NVIDIA/NeMo-Relay/releases/latest": fixture("github-release.json"),
                   "search/code": fixture("github-code.json")}
        out = io.StringIO()
        with mock.patch.object(probe, "gh_json", lambda path, *f: answers[path]), \
                mock.patch.object(probe, "http_json", lambda url: fixture("pypi.json")), \
                contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["probe", "https://github.com/NVIDIA/NeMo-Relay", "https://pypi.org/project/x"]), 0)
            self.assertEqual(cli.main(["probe", "--json", "https://pypi.org/project/x"]), 0)
            self.assertEqual(cli.main(["search", "--exact", "NeMo", "Relay"]), 0)
        text = out.getvalue()
        self.assertIn("Apache-2.0", text)
        self.assertIn("a lead to read, not proof", text)
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["probe", "https://example.com/nope"]), 2)
        self.assertIn("PROBE_UNSUPPORTED_URL", err.getvalue())


class ExactSearchTests(unittest.TestCase):
    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        self.con.row_factory = sqlite3.Row
        self.con.executescript(store.SCHEMA)
        rows = [("a", "NVIDIA PAIR routes LAN requests", "router", "PAIR is a router for a LAN."),
                ("b", "Paired triplets", "e4b", "Each pair of devices ran in pairs; the pair was paired.")]
        for id_, title, tags, body in rows:
            self.con.execute("INSERT INTO entries (id, title, kind, relevance, date, path) VALUES (?,?,?,?,?,?)",
                             (id_, title, "finding", "act", "2026-10-13", f"{id_}.md"))
            self.con.execute("INSERT INTO entries_fts (id, title, tags, body) VALUES (?,?,?,?)", (id_, title, tags, body))

    def ids(self, text, exact):
        ents, _ = store.search(self.con, text, exact=exact, catalogs=False)
        return sorted(r["id"] for r in ents)

    def test_stemmed_search_mixes_the_product_and_the_word(self):
        self.assertEqual(self.ids("PAIR", False), ["a", "b"])

    def test_exact_keeps_case_and_whole_words(self):
        self.assertEqual(self.ids("PAIR", True), ["a"])
        self.assertEqual(self.ids("pair", True), ["b"])
        self.assertEqual(self.ids("PAIR router", True), ["a"])
        self.assertEqual(self.ids("pairs", True), ["b"])
        self.assertEqual(self.ids("PAI", True), [])

    def test_exact_snippet_brackets_the_hit_and_hides_full_text(self):
        ents, _ = store.search(self.con, "PAIR", exact=True, catalogs=False)
        self.assertIn("[PAIR]", ents[0]["snip"])
        self.assertNotIn("fb", ents[0])


if __name__ == "__main__":
    unittest.main()
