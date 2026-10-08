"""End-to-end tests of the rnd command line against a throwaway library."""

import base64
import contextlib
import io
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mcptoolshop_rnd import catalog, cli, release

from .test_rnd import ENTRY, write

REPO = Path(__file__).resolve().parent.parent

OTHER = (ENTRY.replace("2026-01-02-sample", "2026-01-03-other").replace("Sample entry", "Other entry")
         .replace("relevance: watch", "relevance: act").replace("[[2026-01-03-other]]", "[[2026-01-02-sample]]"))

INSTRUMENT = """---
id: tool-x
title: Tool X
date: 2026-01-02
kind: instrument
relevance: reference
fields: [studio-tooling]
instrument_status: shipped
invoke: "python -m toolx"
when: "When x is needed."
---

## Summary

A tool.
"""


def make_library(root):
    write(root, "entries/2026/2026-01-02-sample.md", ENTRY)
    write(root, "entries/2026/2026-01-03-other.md", OTHER)
    write(root, "instruments/tool-x.md", INSTRUMENT)
    write(root, "instruments/tool-y.md", INSTRUMENT.replace("tool-x", "tool-y").replace("Tool X", "Tool Y")
          .replace("instrument_status: shipped", "instrument_status: planned").replace('when: "When x is needed."\n', ""))
    shutil.copy(REPO / "entries" / "_template.md", write(root, "entries/_template.md", ""))
    write(root, "catalogs/demo/source.json", json.dumps({"repo": "x/y", "families": ["nemo-rl"]}))
    write(root, "catalogs/demo/catalog.json", json.dumps({
        "upstream": "https://github.com/x/y", "ref": "abc123", "synced_at": "2026-01-02", "license": "MIT",
        "lanes": [{"title": "GPU Development", "description": "", "count": 1}],
        "items": [{"name": "tilegym-cutile-python", "family": "tilegym", "lanes": ["GPU Development"],
                   "description": "Write cuTile kernels", "license": "", "path": "p", "url": "u"},
                  {"name": "nemo-rl-docs", "family": "nemo-rl", "lanes": [],
                   "description": "NeMo RL docs", "license": "", "path": "p2", "url": "u2"}]}))
    write(root, "catalogs/demo/review.json", json.dumps({
        "families": {"tilegym": {"fit": "adjacent", "note": "kernel kit"}},
        "items": {"nemo-rl-docs": {"fit": "general", "note": "docs only"}}}))
    write(root, "mcptoolshop_rnd/__init__.py", '"""stub"""\n\n__version__ = "1.0.0"\n')
    write(root, "CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n\n## [1.0.0] - 2026-01-01\n")


def make_readouts(root):
    kb = root / "vocology-knowledge"
    kb.mkdir(parents=True)
    con = sqlite3.connect(kb / "findings.db")
    con.execute("CREATE VIRTUAL TABLE findings_fts USING fts5(slug, name, claim)")
    con.execute("INSERT INTO findings_fts VALUES ('mushra', 'MUSHRA', 'Post-screen listeners.')")
    con.commit()
    con.close()
    (root / "index.json").write_text(json.dumps({"knowledge_bases": [
        {"name": "vocology-knowledge", "noun": "findings", "entries": 1, "what": "singing",
         "db": "vocology-knowledge/findings.db", "fts": "findings_fts"},
        {"name": "broken-knowledge", "db": "x.db", "fts": "bad name"},
    ]}), encoding="utf-8")


class CliBase(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        make_library(self.root)
        patcher = mock.patch.object(cli, "ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        env = mock.patch.dict("os.environ", {"RND_DB": str(self.root / "rnd.db")})
        env.start()
        self.addCleanup(env.stop)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = cli.main(list(argv))
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue()


class ReadCommandTests(CliBase):
    def test_build_check_and_stats(self):
        code, out, _ = self.run_cli("build")
        self.assertEqual(code, 0)
        self.assertIn("4 entries", out)  # 2 entries + 2 instruments
        code, out, _ = self.run_cli("check")
        self.assertEqual((code, "0 errors" in out), (0, True))
        code, out, _ = self.run_cli("stats")
        self.assertIn("by_kind:", out)
        self.assertIn("catalogue demo: 2 items @ abc123", out)
        code, out, _ = self.run_cli("stats", "--json")
        self.assertEqual(json.loads(out)["entries"], 4)

    def test_check_and_build_report_errors(self):
        write(self.root, "entries/2026/broken.md", "---\ntitle: no date\n---\n")
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("'date' must be", err)
        code, _, err = self.run_cli("build")
        self.assertEqual(code, 1)
        self.assertIn("INDEX_INVALID", err)

    def test_search_text_json_filters_and_raw_errors(self):
        code, out, _ = self.run_cli("search", "cuda", "graphs")
        self.assertEqual(code, 0)
        self.assertIn("2026-01-02-sample", out)
        code, out, _ = self.run_cli("search", "cuTile")
        self.assertIn("Catalogue items (1)", out)
        self.assertIn("fit:adjacent", out)
        code, out, _ = self.run_cli("search", "nothingmatchesthis")
        self.assertIn("no matches", out)
        code, out, _ = self.run_cli("search", "graphs", "--kind", "finding", "--field", "gpu-computing", "--json")
        self.assertEqual(len(json.loads(out)["entries"]), 2)
        code, out, _ = self.run_cli("search", "graphs", "--entries-only", "--limit", "1")
        self.assertNotIn("Catalogue", out)
        code, _, err = self.run_cli("search", "AND", "OR", "--raw")
        self.assertEqual(code, 2)
        self.assertIn("QUERY_INVALID", err)

    def test_show_entry_item_and_missing(self):
        code, out, _ = self.run_cli("show", "2026-01-02-sample")
        self.assertEqual(code, 0)
        self.assertIn("linked from: 2026-01-03-other", out)
        self.assertIn("CUDA graphs cut launch overhead", out)
        code, out, _ = self.run_cli("show", "2026-01-02-sample", "--json")
        data = json.loads(out)
        self.assertEqual(data["claims"][0]["confidence"], "verified")
        self.assertEqual(data["sources"][2]["tier"], "rig")
        code, out, _ = self.run_cli("show", "demo:nemo-rl-docs")
        self.assertIn("note: docs only", out)
        code, _, err = self.run_cli("show", "sample")
        self.assertEqual(code, 2)
        self.assertIn("did you mean: 2026-01-02-sample", err)
        code, _, err = self.run_cli("show", "zzz")
        self.assertIn("try `rnd search", err)

    def test_list_filters(self):
        code, out, _ = self.run_cli("list")
        self.assertIn("4 entries", out)
        code, out, _ = self.run_cli("list", "--relevance", "act", "--kind", "finding", "--status", "active")
        self.assertIn("2026-01-03-other", out)
        self.assertNotIn("2026-01-02-sample", out)
        code, out, _ = self.run_cli("list", "--field", "gpu-computing", "--tag", "cuda", "--json")
        self.assertEqual(sorted(r["id"] for r in json.loads(out)), ["2026-01-02-sample", "2026-01-03-other"])

    def test_tools(self):
        code, out, _ = self.run_cli("tools")
        self.assertIn("tool-x", out)
        self.assertIn("invoke: python -m toolx", out)
        self.assertIn("when:   When x is needed.", out)
        code, out, _ = self.run_cli("tools", "--status", "planned", "--json")
        self.assertEqual([r["id"] for r in json.loads(out)], ["tool-y"])

    def test_catalog_views(self):
        code, out, _ = self.run_cli("catalog", "lanes", "demo")
        self.assertIn("GPU Development", out)
        code, out, _ = self.run_cli("catalog", "families", "demo")
        self.assertIn("tilegym", out)
        code, out, _ = self.run_cli("catalog", "list", "demo")
        self.assertIn("2 items", out)
        code, out, _ = self.run_cli("catalog", "list", "demo", "--fit", "adjacent", "--family", "tilegym",
                                    "--lane", "GPU Development", "--json")
        self.assertEqual([r["name"] for r in json.loads(out)], ["tilegym-cutile-python"])

    def test_sql(self):
        code, out, _ = self.run_cli("sql", "SELECT count(*) AS n FROM entries")
        self.assertEqual(out.strip(), "4")
        code, out, _ = self.run_cli("sql", "SELECT 1 AS one", "--json")
        self.assertEqual(json.loads(out), [{"one": 1}])
        code, _, err = self.run_cli("sql", "DELETE FROM entries")
        self.assertEqual(code, 2)
        self.assertIn("SQL_ERROR", err)

    def test_invalid_index_without_previous_build(self):
        write(self.root, "entries/2026/broken.md", "---\ntitle: no date\n---\n")
        code, _, err = self.run_cli("list")
        self.assertEqual(code, 1)
        self.assertIn("INDEX_INVALID", err)

    def test_stale_index_warning_keeps_last_good(self):
        self.run_cli("build")
        write(self.root, "entries/2026/broken.md", "---\ntitle: no date\n---\n")
        code, out, err = self.run_cli("list")
        self.assertEqual(code, 0)
        self.assertIn("showing the last good index", err)

    def test_readouts(self):
        ro = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, ro, True)
        make_readouts(ro)
        code, out, _ = self.run_cli("readouts", "--root", str(ro))
        self.assertIn("2 knowledge bases", out)
        code, out, err = self.run_cli("readouts", "listener", "--root", str(ro))
        self.assertIn("vocology-knowledge (findings)", out)
        self.assertIn("mushra", out)
        self.assertIn("broken-knowledge", err)
        code, out, _ = self.run_cli("readouts", "zzz", "--root", str(ro), "--json")
        self.assertEqual(json.loads(out), [])
        code, out, _ = self.run_cli("readouts", "zzz", "--root", str(ro))
        self.assertIn("no matches", out)
        code, _, err = self.run_cli("readouts", "x", "--root", str(ro / "nowhere"))
        self.assertEqual(code, 2)
        self.assertIn("READOUTS_MISSING", err)
        (ro / "index.json").write_text("{}", encoding="utf-8")
        code, _, err = self.run_cli("readouts", "--list", "--root", str(ro))
        self.assertIn("READOUTS_INDEX_INVALID", err)


class NewCommandTests(CliBase):
    def test_new_entry_instrument_and_errors(self):
        code, out, _ = self.run_cli("new", "A Test: Title!", "--date", "2026-02-03", "--field", "audio", "--tag", "x")
        self.assertEqual(out.strip(), "entries/2026/2026-02-03-a-test-title.md")
        text = (self.root / out.strip()).read_text(encoding="utf-8")
        self.assertIn("title: A Test: Title!", text)
        self.assertIn("fields: [audio]", text)
        code, out, _ = self.run_cli("new", "Kit", "--kind", "instrument", "--id", "kit")
        self.assertEqual(out.strip(), "instruments/kit.md")
        code, _, err = self.run_cli("new", "Kit", "--kind", "instrument", "--id", "kit")
        self.assertEqual(code, 2)
        self.assertIn("EXISTS", err)
        code, _, err = self.run_cli("new", "x", "--id", "Bad ID")
        self.assertIn("BAD_ID", err)


class CatalogSyncTests(CliBase):
    def fake_gh(self, args):
        if args[:2] == ["api", "repos/x/y"]:
            return json.dumps({"license": {"spdx_id": "Apache-2.0"}})
        if args[1].startswith("repos/x/y/git/trees"):
            return json.dumps({"sha": "f" * 40, "tree": [
                {"path": "skills/nemo-rl-docs/SKILL.md"}, {"path": "skills/tilegym-cutile-python/SKILL.md"},
                {"path": "alt/tilegym-cutile-python/SKILL.md"}, {"path": "skills/broken/SKILL.md"},
                {"path": "README.md"}]})
        if args[1] == "graphql":
            texts = {
                "skills/nemo-rl-docs/SKILL.md": "---\nname: nemo-rl-docs\ndescription: NeMo RL\n  docs\nlicense: MIT\n---\n",
                "skills/tilegym-cutile-python/SKILL.md": "---\nname: tilegym-cutile-python\ndescription: cuTile\n---\n",
                "alt/tilegym-cutile-python/SKILL.md": "---\nname: tilegym-cutile-python\ndescription: alt copy\n---\n",
                "skills/broken/SKILL.md": "---\nname: broken\n",
            }
            query = args[3]
            data = {}
            for n, (path, text) in enumerate(t for t in texts.items() if f':{t[0]}"' in query):
                data[f"f{n}"] = {"text": text, "byteSize": len(text)}
            return json.dumps({"data": {"repository": data}})
        if "contents/lanes.json" in args[1]:
            groupings = {"groupings": [{"title": "Docs", "skills": ["nemo-rl-docs"]}]}
            return json.dumps({"content": base64.b64encode(json.dumps(groupings).encode()).decode()})
        raise AssertionError(args)

    def test_sync_writes_snapshot_and_rebuilds(self):
        write(self.root, "catalogs/demo/source.json", json.dumps({
            "repo": "x/y", "families": ["nemo-rl"], "groupings_file": "lanes.json", "prefer_prefix": "skills/"}))
        with mock.patch.object(catalog, "_gh", side_effect=self.fake_gh):
            code, out, _ = self.run_cli("catalog", "sync", "demo")
        self.assertEqual(code, 0)
        snap = json.loads((self.root / "catalogs/demo/catalog.json").read_text(encoding="utf-8"))
        self.assertEqual(snap["license"], "Apache-2.0")
        self.assertEqual(snap["ref"], "f" * 40)
        by_name = {it["name"]: it for it in snap["items"]}
        self.assertEqual(by_name["nemo-rl-docs"]["description"], "NeMo RL docs")
        self.assertEqual(by_name["nemo-rl-docs"]["lanes"], ["Docs"])
        self.assertEqual(by_name["tilegym-cutile-python"]["path"], "skills/tilegym-cutile-python/SKILL.md")
        self.assertEqual(len(snap["unparsed"]), 1)
        self.assertIn("built rnd.db", out)

    def test_sync_errors(self):
        code, _, err = self.run_cli("catalog", "sync", "nope")
        self.assertEqual(code, 3)
        self.assertIn("CATALOG_UNKNOWN", err)
        with mock.patch.object(catalog.subprocess, "run", side_effect=FileNotFoundError):
            code, _, err = self.run_cli("catalog", "sync", "demo")
        self.assertIn("GH_MISSING", err)
        failed = subprocess.CompletedProcess([], 1, "", "boom")
        with mock.patch.object(catalog.subprocess, "run", return_value=failed):
            code, _, err = self.run_cli("catalog", "sync", "demo")
        self.assertIn("GH_FAILED", err)

    def test_missing_snapshot_is_a_warning(self):
        (self.root / "catalogs/demo/catalog.json").unlink()
        code, out, err = self.run_cli("check")
        self.assertEqual(code, 0)
        self.assertIn("no catalog.json yet", err)


class BumpCommandTests(CliBase):
    def git(self, *args):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                       cwd=self.root, check=True, capture_output=True)

    def test_bump_in_a_git_repo(self):
        self.git("init", "-q")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "init")
        self.git("tag", "-a", "v1.0.0", "-m", "v1.0.0")
        write(self.root, "entries/2026/2026-01-09-new.md", OTHER.replace("2026-01-03-other", "2026-01-09-new"))
        (self.root / "entries/2026/2026-01-02-sample.md").write_text(ENTRY + "\nmore\n", encoding="utf-8")
        write(self.root, "experiments/demo/README.md", "# demo\n")
        code, out, _ = self.run_cli("bump", "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("would bump 1.0.0 -> 1.0.0.0.1 (changes since v1.0.0)", out)
        self.assertIn("1.0.0", (self.root / "mcptoolshop_rnd/__init__.py").read_text(encoding="utf-8"))
        code, out, _ = self.run_cli("bump", "micro", "--note", "a note")
        self.assertIn("bumped 1.0.0 -> 1.0.0.1.0", out)
        self.assertIn("- Added `2026-01-09-new`: Other entry", out)
        self.assertIn("- Updated `2026-01-02-sample`: Sample entry", out)
        self.assertIn("- Added experiment `demo`", out)
        self.assertIn("next: git add", out)
        self.assertIn('__version__ = "1.0.0.1.0"', (self.root / "mcptoolshop_rnd/__init__.py").read_text(encoding="utf-8"))
        self.assertIn("## [1.0.0.1.0]", (self.root / "CHANGELOG.md").read_text(encoding="utf-8"))

    def test_bump_without_git_history(self):
        with mock.patch.object(release, "_git", side_effect=release.ReleaseError("GIT_FAILED", "no git")):
            code, _, err = self.run_cli("bump")
        self.assertEqual(code, 3)
        self.assertIn("GIT_FAILED", err)

    def test_bump_bad_version_and_changelog(self):
        write(self.root, "mcptoolshop_rnd/__init__.py", "nothing here\n")
        code, _, err = self.run_cli("bump", "--dry-run")
        self.assertEqual(code, 2)
        self.assertIn("BAD_VERSION", err)
        write(self.root, "mcptoolshop_rnd/__init__.py", '__version__ = "1.0.0"\n')
        write(self.root, "CHANGELOG.md", "# Changelog\n")
        with mock.patch.object(release, "last_tag", return_value=None), \
                mock.patch.object(release, "changes", return_value=[]):
            code, _, err = self.run_cli("bump")
        self.assertIn("BAD_CHANGELOG", err)


class LibraryDiscoveryTests(CliBase):
    def test_find_root_order(self):
        nested = self.root / "entries" / "2026"
        with mock.patch.dict("os.environ", {}, clear=False):
            os.environ.pop("RND_ROOT", None)
            self.assertEqual(cli.find_root(cwd=nested), self.root.resolve())
            self.assertEqual(cli.find_root(override=str(self.root)), self.root.resolve())
            os.environ["RND_ROOT"] = str(nested)
            self.assertEqual(cli.find_root(cwd=self.root), nested.resolve())
        elsewhere = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, elsewhere, True)
        with mock.patch.dict("os.environ", {}, clear=False), mock.patch.object(cli, "SOURCE_ROOT", elsewhere):
            os.environ.pop("RND_ROOT", None)
            self.assertIsNone(cli.find_root(cwd=elsewhere))
            with mock.patch.object(cli, "SOURCE_ROOT", self.root):
                self.assertEqual(cli.find_root(cwd=elsewhere), self.root)

    def test_library_flag_and_no_library(self):
        code, out, _ = self.run_cli("--library", str(self.root), "list", "--json")
        self.assertEqual(code, 0)
        self.assertIn("2026-01-02-sample", out)
        empty = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, empty, True)
        code, _, err = self.run_cli("--library", str(empty), "list")
        self.assertEqual(code, 2)
        self.assertIn("NO_LIBRARY", err)
        with mock.patch.object(cli, "ROOT", None):
            code, _, err = self.run_cli("stats")
        self.assertIn("NO_LIBRARY", err)


class ReleaseUnitTests(unittest.TestCase):
    def test_git_errors_are_structured(self):
        with mock.patch.object(release.subprocess, "run", side_effect=OSError("no git")):
            with self.assertRaises(release.ReleaseError) as ctx:
                release._git(".", "status")
        self.assertEqual(ctx.exception.code, "GIT_FAILED")
        with mock.patch.object(release.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "", "")):
            with self.assertRaises(release.ReleaseError):
                release._git(".", "status")
            self.assertIsNone(release.last_tag("."))

    def test_section_without_changes_and_with_removals(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        self.assertIn("version bump only", release.changelog_section(root, "1.0.0.0.1", [], today="2026-01-01"))
        section = release.changelog_section(root, "1.0.0.0.2", [("D", "entries/2026/gone.md")], today="2026-01-01")
        self.assertIn("- Removed `gone`", section)
        write(root, "entries/bad.md", "---\nno close\n")
        self.assertEqual(release._title(root, "entries/bad.md"), "")


if __name__ == "__main__":
    unittest.main()
