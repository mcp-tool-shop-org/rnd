import json
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from rnd import catalog, frontmatter, model, readouts, store

ENTRY = """---
id: 2026-01-02-sample
title: Sample entry
date: 2026-01-02
kind: finding
relevance: watch
fields: [gpu-computing, systems-performance]
tags:
  - cuda
  - graphs
---

## Summary

CUDA graphs cut launch overhead for small kernels.

## Studio relevance

Mostly already in our engines. See [[2026-01-03-other]].

## Claims

- [verified] Graphs replay with one call. (via: NVIDIA docs, 2026-01-02)
- [unverified] It helps decode more than diffusion.

## Sources

- [primary] https://developer.nvidia.com/blog/cuda-graphs/ — NVIDIA blog
- [primary] [Guide](https://docs.nvidia.com/cuda/) — programming guide
- [rig] nvidia-smi on the rig
"""


def write(root, rel, text):
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class FrontmatterTests(unittest.TestCase):
    def test_scalars_lists_and_nesting(self):
        meta, body = frontmatter.read(
            "---\nname: x\ntags: [a, 'b, c', d]\nitems:\n  - one\n  - two\n"
            "metadata:\n  author: NVIDIA\n  domain: skills\n---\nbody\n")
        self.assertEqual(meta["name"], "x")
        self.assertEqual(meta["tags"], ["a", "b, c", "d"])
        self.assertEqual(meta["items"], ["one", "two"])
        self.assertEqual(meta["metadata"], {"author": "NVIDIA", "domain": "skills"})
        self.assertEqual(body, "body\n")

    def test_block_scalars(self):
        meta, _ = frontmatter.read("---\nd: >-\n  folded\n  text\nl: |\n  line1\n  line2\n---\n")
        self.assertEqual(meta["d"], "folded text")
        self.assertEqual(meta["l"], "line1\nline2")

    def test_wrapped_plain_and_quoted_scalars(self):
        meta, _ = frontmatter.read(
            '---\na: first part\n  second part\nb: "quoted and\n  continued"\nc: next\n---\n')
        self.assertEqual(meta["a"], "first part second part")
        self.assertEqual(meta["b"], "quoted and continued")
        self.assertEqual(meta["c"], "next")

    def test_list_of_maps(self):
        meta, _ = frontmatter.read("---\nsib:\n  - name: a\n    folder: a/\n  - name: b\n---\n")
        self.assertEqual(meta["sib"], [{"name": "a", "folder": "a/"}, {"name": "b"}])

    def test_url_with_hash_survives(self):
        meta, _ = frontmatter.read("---\nu: https://x.org/a#frag\n---\n")
        self.assertEqual(meta["u"], "https://x.org/a#frag")

    def test_unclosed_frontmatter_raises(self):
        with self.assertRaises(frontmatter.FrontmatterError):
            frontmatter.read("---\na: b\n")


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_parses_sources_claims_links(self):
        path = write(self.root, "entries/2026/2026-01-02-sample.md", ENTRY)
        entry, problems = model.load(path, self.root)
        self.assertEqual([p for p in problems if p.level == "error"], [])
        self.assertEqual(entry.tags, ["cuda", "graphs"])
        self.assertEqual([s["tier"] for s in entry.sources], ["primary", "primary", "rig"])
        self.assertEqual(entry.sources[1]["url"], "https://docs.nvidia.com/cuda/")
        self.assertEqual(entry.sources[1]["label"], "Guide — programming guide")
        self.assertEqual(entry.claims[0]["via"], "NVIDIA docs, 2026-01-02")
        self.assertEqual(entry.links, ["2026-01-03-other"])
        self.assertIn("Mostly already", entry.relevance_note)

    def test_rejects_bad_enums_and_unsourced_verdicts(self):
        bad = (ENTRY.replace("kind: finding", "kind: rumour")
               .replace("(via: NVIDIA docs, 2026-01-02)", "")
               .replace("[primary] https://developer", "[blog] https://developer"))
        path = write(self.root, "entries/x.md", bad)
        _, problems = model.load(path, self.root)
        messages = " | ".join(p.message for p in problems if p.level == "error")
        self.assertIn("'kind'", messages)
        self.assertIn("needs '(via:", messages)
        self.assertIn("source tier [blog]", messages)

    def test_duplicate_ids_and_dangling_links(self):
        write(self.root, "entries/a.md", ENTRY)
        write(self.root, "entries/b.md", ENTRY)
        _, problems = model.load_all(self.root)
        self.assertTrue(any("duplicate id" in p.message for p in problems))
        self.assertTrue(any(p.level == "warning" and "points at no entry" in p.message for p in problems))

    def test_instrument_requires_invoke_and_status(self):
        text = ("---\nid: tool-x\ntitle: X\ndate: 2026-01-02\nkind: instrument\nrelevance: reference\n"
                "fields: [studio-tooling]\n---\n## Summary\nx\n")
        path = write(self.root, "instruments/tool-x.md", text)
        _, problems = model.load(path, self.root)
        messages = " | ".join(p.message for p in problems)
        self.assertIn("instrument_status", messages)
        self.assertIn("'invoke'", messages)

    def test_template_files_are_skipped(self):
        write(self.root, "entries/_template.md", "---\ntitle: {{title}}\n---\n")
        self.assertEqual(list(model.entry_paths(self.root)), [])


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        write(self.root, "entries/2026/2026-01-02-sample.md", ENTRY)
        cat = self.root / "catalogs" / "demo"
        write(self.root, "catalogs/demo/source.json", json.dumps({"repo": "x/y", "families": ["nemo-rl"]}))
        write(self.root, "catalogs/demo/catalog.json", json.dumps({
            "upstream": "https://github.com/x/y", "ref": "abc", "synced_at": "2026-01-02", "license": "MIT",
            "lanes": [{"title": "GPU Development", "description": "", "count": 1}],
            "items": [{"name": "tilegym-cutile-python", "family": "tilegym", "lanes": ["GPU Development"],
                       "description": "Write cuTile kernels", "license": "", "path": "p", "url": "u"},
                      {"name": "nemo-rl-docs", "family": "nemo-rl", "lanes": [],
                       "description": "NeMo RL docs", "license": "", "path": "p2", "url": "u2"}]}))
        write(self.root, "catalogs/demo/review.json", json.dumps({
            "families": {"tilegym": {"fit": "adjacent", "note": "kernel kit"}},
            "items": {"nemo-rl-docs": {"fit": "general", "note": "docs only"}}}))
        self.cat = cat
        self.db = self.root / "rnd.db"

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_build_and_search(self):
        counts, problems = store.build(self.root, self.db)
        self.assertEqual(counts, {"entries": 1, "catalogs": 1, "catalog_items": 2})
        con, _ = store.connect(self.root, self.db)
        ents, items = store.search(con, "cuda-graphs launch")  # the hyphen must not break FTS5
        self.assertEqual([e["id"] for e in ents], ["2026-01-02-sample"])
        _, items = store.search(con, "cuTile kernels")
        self.assertEqual(items[0]["name"], "tilegym-cutile-python")
        self.assertEqual(items[0]["fit"], "adjacent")
        fits = dict(con.execute("SELECT name, fit FROM catalog_items").fetchall())
        self.assertEqual(fits["nemo-rl-docs"], "general")

    def test_index_is_read_only(self):
        store.build(self.root, self.db)
        con, _ = store.connect(self.root, self.db)
        with self.assertRaises(sqlite3.OperationalError):
            con.execute("DELETE FROM entries")

    def test_errors_keep_previous_index(self):
        store.build(self.root, self.db)
        write(self.root, "entries/2026/broken.md", "---\ntitle: no date\n---\n")
        counts, problems = store.build(self.root, self.db)
        self.assertIsNone(counts)
        self.assertTrue(self.db.exists())
        con = sqlite3.connect(self.db)
        self.assertEqual(con.execute("SELECT count(*) FROM entries").fetchone()[0], 1)

    def test_auto_rebuild_on_change(self):
        store.build(self.root, self.db)
        write(self.root, "entries/2026/2026-01-05-new.md",
              ENTRY.replace("2026-01-02-sample", "2026-01-05-new").replace("Sample entry", "Newer entry"))
        con, _ = store.connect(self.root, self.db)
        self.assertEqual(con.execute("SELECT count(*) FROM entries").fetchone()[0], 2)

    def test_review_rejects_unknown_fit_and_item(self):
        (self.cat / "review.json").write_text(json.dumps({
            "families": {"tilegym": {"fit": "maybe"}}, "items": {"ghost": {"fit": "direct"}}}), encoding="utf-8")
        _, _, problems = catalog.load(self.cat)
        self.assertTrue(any("fit must be one of" in p for p in problems))
        self.assertTrue(any("'ghost' is not in the snapshot" in p for p in problems))


class ReadoutsTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        kb = self.root / "vocology-knowledge"
        kb.mkdir()
        con = sqlite3.connect(kb / "findings.db")
        con.execute("CREATE VIRTUAL TABLE findings_fts USING fts5(slug, name, claim)")
        con.executemany("INSERT INTO findings_fts VALUES (?,?,?)", [
            ("mushra", "ITU-R BS.1534 MUSHRA", "Post-screen listeners with a hidden reference."),
            ("singmos", "SingMOS", "Singing MOS dataset for quality prediction."),
        ])
        con.commit()
        con.close()
        (self.root / "index.json").write_text(json.dumps({"knowledge_bases": [
            {"name": "vocology-knowledge", "noun": "findings", "entries": 2,
             "db": "vocology-knowledge/findings.db", "fts": "findings_fts"},
            {"name": "ghost-knowledge", "db": "ghost/ghost.db", "fts": "x_fts"},
        ]}), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_prefix_search_and_missing_kb(self):
        rows, problems = readouts.search(self.root, "listener")  # prefix: matches "listeners"
        self.assertEqual([r["slug"] for r in rows], ["mushra"])
        self.assertIn("[listeners]", rows[0]["snip"])
        self.assertTrue(any("ghost-knowledge" in p for p in problems))

    def test_kb_filter_and_hostile_query(self):
        rows, _ = readouts.search(self.root, 'MOS "quality" -( *', kb="vocology-knowledge")
        self.assertEqual([r["slug"] for r in rows], ["singmos"])

    def test_any_word_ors_the_terms(self):
        self.assertEqual(readouts.search(self.root, "listener singing")[0], [])
        rows, _ = readouts.search(self.root, "listener singing", any_word=True)
        self.assertEqual(sorted(r["slug"] for r in rows), ["mushra", "singmos"])

    def test_missing_root_is_a_structured_error(self):
        with self.assertRaises(readouts.ReadoutsError) as ctx:
            readouts.knowledge_bases(self.root / "nowhere")
        self.assertEqual(ctx.exception.code, "READOUTS_MISSING")


class CatalogTests(unittest.TestCase):
    def test_family_prefers_longest_prefix(self):
        prefixes = ["nemo", "nemo-rl", "tao"]
        self.assertEqual(catalog.family_of("nemo-rl-docs", prefixes), "nemo-rl")
        self.assertEqual(catalog.family_of("nemo-x", prefixes), "nemo")
        self.assertEqual(catalog.family_of("warp-eval", prefixes), "warp")


if __name__ == "__main__":
    unittest.main()


class CliTests(unittest.TestCase):
    def test_version_flag(self):
        import contextlib
        import io

        from rnd import __version__, cli
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as ctx:
            cli.main(["--version"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn(__version__, out.getvalue())

    def test_unexpected_error_is_structured_without_debug(self):
        import contextlib
        import io
        from unittest import mock

        from rnd import cli
        err = io.StringIO()
        with mock.patch.object(cli, "cmd_stats", side_effect=RuntimeError("boom")):
            with contextlib.redirect_stderr(err):
                code = cli.main(["stats"])
        self.assertEqual(code, 3)
        self.assertIn("error: INTERNAL: RuntimeError: boom", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())


class ReleaseTests(unittest.TestCase):
    def test_bump_levels_reset_lower_segments(self):
        from rnd import release
        self.assertEqual(release.bump("1.0.0"), "1.0.0.0.1")
        self.assertEqual(release.bump("1.0.0.0.9", "micro"), "1.0.0.1.0")
        self.assertEqual(release.bump("1.2.3.4.5", "minor"), "1.3.0.0.0")
        with self.assertRaises(release.ReleaseError):
            release.bump("1.0.x")
        with self.assertRaises(release.ReleaseError):
            release.bump("1.0.0", "pico")

    def test_changelog_section_and_insert(self):
        from rnd import release
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        (root / "entries" / "2026").mkdir(parents=True)
        (root / "entries" / "2026" / "2026-01-02-sample.md").write_text(ENTRY, encoding="utf-8")
        (root / "CHANGELOG.md").write_text("# Changelog\n\n## [Unreleased]\n\n## [1.0.0] - 2026-01-01\n", encoding="utf-8")
        changed = [("A", "entries/2026/2026-01-02-sample.md"), ("M", "experiments/demo/README.md")]
        section = release.changelog_section(root, "1.0.0.0.1", changed, ["a note"], today="2026-01-02")
        self.assertIn("## [1.0.0.0.1] - 2026-01-02", section)
        self.assertIn("- Added `2026-01-02-sample`: Sample entry", section)
        self.assertIn("- Updated experiment `demo`", section)
        release.insert_changelog(root, section)
        text = (root / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertLess(text.index("[Unreleased]"), text.index("[1.0.0.0.1]"))
        self.assertLess(text.index("[1.0.0.0.1]"), text.index("[1.0.0]"))
