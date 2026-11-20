"""Tests for rnd 1.3 Part A: review follow-ups on claims, check, sync, questions, bump, and collect."""

import json
import os
import shutil
import unittest
from pathlib import Path
from unittest import mock

from mcptoolshop_rnd import collect, model, release

from .test_cli import CliBase
from .test_rnd import ENTRY, write


class PartAFollowupTests(CliBase):
    def test_superseded_without_link_warns_disputed_without_link_clean_and_reverse_hint_resets_state(self):
        # 1. [superseded] without (superseded-by: ...) emits a warning with state-back hint.
        p_sup = write(
            self.root,
            "entries/2026/2026-01-10-orphan-sup.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-10-orphan-sup").replace(
                "- [unverified] It helps decode more than diffusion.",
                "- [superseded] [c-sups0001] Replaced claim without link.",
            ),
        )
        code, out, err = self.run_cli("check")
        self.assertEqual(code, 0)
        self.assertIn("0 errors, 1 warnings", out)
        self.assertIn("[superseded] claim c-sups0001 has no '(superseded-by: <id>)' link", err)
        self.assertIn("set its state back", err)
        p_sup.unlink()

        # 2. [disputed] without (contradicted-by: ...) is legitimate (source conflict) and emits 0 warnings.
        p_disp = write(
            self.root,
            "entries/2026/2026-01-11-src-conflict.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-11-src-conflict").replace(
                "- [unverified] It helps decode more than diffusion.",
                "- [disputed] Two sources disagree on latency.",
            ),
        )
        code, out, err = self.run_cli("check")
        self.assertEqual(code, 0, err)
        self.assertIn("0 errors, 0 warnings", out)
        p_disp.unlink()

        # 3. Reverse-only hints for superseded-by and contradicted-by both instruct setting state back.
        id_s0 = model.make_claim_id("2026-01-02-sample", "Graphs replay with one call.")
        id_s1 = model.make_claim_id("2026-01-02-sample", "It helps decode more than diffusion.")
        p_new = write(
            self.root,
            "entries/2026/2026-01-12-newer.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-12-newer").replace(
                "- [verified] Graphs replay with one call. (via: NVIDIA docs, 2026-01-02)",
                f"- [verified] [c-newsup01] Newer supersedes. (via: bench, 2026-01-12) (supersedes: {id_s0})",
            ).replace(
                "- [unverified] It helps decode more than diffusion.",
                f"- [verified] [c-newcon02] Newer contradicts. (via: bench, 2026-01-12) (contradicts: {id_s1})",
            ),
        )
        self.assertEqual(self.run_cli("reconcile", "2026-01-12-newer")[0], 0)
        p_new.write_text(
            p_new.read_text(encoding="utf-8")
            .replace(f" (supersedes: {id_s0})", "")
            .replace(f" (contradicts: {id_s1})", ""),
            encoding="utf-8",
        )
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn(f"remove '(superseded-by: c-newsup01)' from entries/2026/2026-01-02-sample.md and set its state back", err)
        self.assertIn(f"remove '(contradicted-by: c-newcon02)' from entries/2026/2026-01-02-sample.md and set its state back", err)

    def test_unclosed_code_fence_reported_by_name_as_error(self):
        p_backtick = write(
            self.root,
            "entries/2026/2026-01-10-open-backtick.md",
            "---\n"
            "id: 2026-01-10-open-backtick\n"
            "title: Open backtick fence\n"
            "date: 2026-01-10\n"
            "kind: finding\n"
            "relevance: reference\n"
            "fields: [gpu-computing]\n"
            "---\n\n"
            "## Summary\n\n"
            "```python\n"
            "x = 1\n\n"
            "## Claims\n\n"
            "- [unverified] Hidden claim.\n\n"
            "## Sources\n\n"
            "- [rig] bench\n",
        )
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("error: entries/2026/2026-01-10-open-backtick.md: unclosed code fence (```) opened at line 12", err)
        p_backtick.unlink()

        write(
            self.root,
            "entries/2026/2026-01-11-open-tilde.md",
            "---\n"
            "id: 2026-01-11-open-tilde\n"
            "title: Open tilde fence\n"
            "date: 2026-01-11\n"
            "kind: finding\n"
            "relevance: reference\n"
            "fields: [gpu-computing]\n"
            "---\n\n"
            "## Summary\n\n"
            "~~~~\n"
            "hidden\n",
        )
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("error: entries/2026/2026-01-11-open-tilde.md: unclosed code fence (~~~~) opened at line 12", err)

    def test_writers_refuse_multiple_claims_headings_writing_nothing(self):
        # Case A: claims assign refuses even when the last Claims heading already has ids.
        p_assigned = write(
            self.root,
            "entries/2026/2026-01-10-two-heads.md",
            "---\n"
            "id: 2026-01-10-two-heads\n"
            "title: Two heads\n"
            "date: 2026-01-10\n"
            "kind: finding\n"
            "relevance: act\n"
            "fields: [gpu-computing]\n"
            "---\n\n"
            "## Claims\n\n"
            "- [unverified] First section.\n\n"
            "## Claims\n\n"
            "- [unverified] [c-head0002] Already assigned.\n\n"
            "## Sources\n\n"
            "- [rig] bench\n",
        )
        before_assigned = p_assigned.read_bytes()
        code, _, err = self.run_cli("claims", "assign", "2026-01-10-two-heads")
        self.assertEqual(code, 1)
        self.assertIn("MULTIPLE_CLAIMS_HEADINGS", err)
        self.assertIn("entries/2026/2026-01-10-two-heads.md", err)
        self.assertEqual(p_assigned.read_bytes(), before_assigned)

        # Case B: reconcile refuses when source has two Claims headings (even with no forward links).
        code, _, err = self.run_cli("reconcile", "2026-01-10-two-heads")
        self.assertEqual(code, 1)
        self.assertIn("MULTIPLE_CLAIMS_HEADINGS", err)
        self.assertEqual(p_assigned.read_bytes(), before_assigned)

        # Case C: reconcile refuses before writing ANY file when one of two targets has duplicate Claims headings.
        p_clean_old = self.root / "entries/2026/2026-01-02-sample.md"
        clean_old_before = p_clean_old.read_bytes()
        id_s0 = model.make_claim_id("2026-01-02-sample", "Graphs replay with one call.")
        p_src = write(
            self.root,
            "entries/2026/2026-01-15-multi-target.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-15-multi-target").replace(
                "- [verified] Graphs replay with one call. (via: NVIDIA docs, 2026-01-02)",
                f"- [verified] Updates sample. (via: bench, 2026-01-15) (supersedes: {id_s0})",
            ).replace(
                "- [unverified] It helps decode more than diffusion.",
                "- [verified] Updates dup. (via: bench, 2026-01-15) (contradicts: c-head0002)",
            ),
        )
        src_before = p_src.read_bytes()
        code, _, err = self.run_cli("reconcile", "2026-01-15-multi-target")
        self.assertEqual(code, 1)
        self.assertIn("MULTIPLE_CLAIMS_HEADINGS", err)
        self.assertEqual(p_clean_old.read_bytes(), clean_old_before)
        self.assertEqual(p_assigned.read_bytes(), before_assigned)
        self.assertEqual(p_src.read_bytes(), src_before)

    def test_claim_mismatch_relative_path_missing_target_hint_and_missing_key_file(self):
        # 1. CLAIM_MISMATCH prints library-relative path, not temp/drive path.
        p_sample = self.root / "entries/2026/2026-01-02-sample.md"
        before_bytes = p_sample.read_bytes()
        with self.assertRaises(model.ReconcileError) as ctx:
            model._apply_claim_line_edits(
                p_sample,
                {0: {"assign_id": "c-00000001", "expected_id": "", "expected_text": "Changed sentence."}},
            )
        self.assertEqual(ctx.exception.code, "CLAIM_MISMATCH")
        msg = str(ctx.exception)
        self.assertTrue(msg.startswith("entries/2026/2026-01-02-sample.md: "), msg)
        self.assertNotIn(str(self.root), msg)
        self.assertEqual(p_sample.read_bytes(), before_bytes)

        # 2a. Missing-target reverse hint names older entry, parenthesized clause, and newer-entry arg when unassigned.
        id_cand = model.make_claim_id("2026-01-03-other", "Graphs replay with one call.")
        p_old = write(
            self.root,
            "entries/2026/2026-01-10-dangling-prov.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-10-dangling-prov").replace(
                "- [unverified] It helps decode more than diffusion.",
                f"- [superseded] [c-oldd1111] Stale claim. (superseded-by: {id_cand})",
            ),
        )
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("entries/2026/2026-01-03-other.md", err)
        self.assertIn("'(supersedes: c-oldd1111)'", err)
        self.assertIn("`rnd reconcile 2026-01-03-other`", err)
        self.assertIn("set its state back", err)
        p_old.unlink()

        # 2b. Missing-target reverse hint with completely unknown id names parenthesized clause and <newer-entry>.
        write(
            self.root,
            "entries/2026/2026-01-10-dangling-missing.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-10-dangling-missing").replace(
                "- [unverified] It helps decode more than diffusion.",
                "- [disputed] [c-oldd2222] Stale disputed. (contradicted-by: c-deadbeef)",
            ),
        )
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("'(contradicts: c-oldd2222)'", err)
        self.assertIn("<newer-entry>", err)
        self.assertIn("`rnd reconcile <newer-entry>`", err)
        self.assertIn("set its state back", err)

        # 3. sync MISSING_KEY error names the Markdown file holding the binding and leaves siblings untouched.
        write(self.root, "experiments/demo/results.json", json.dumps({"accuracy": 0.842}))
        p_good = write(
            self.root,
            "experiments/demo/good.md",
            "Acc 10.0%<!-- rnd:experiments/demo/results.json#accuracy:.1% -->.\n",
        )
        good_before = p_good.read_bytes()
        write(
            self.root,
            "experiments/demo/bad.md",
            "Missing 1<!-- rnd:experiments/demo/results.json#nope:d -->.\n",
        )
        code, _, err = self.run_cli("sync", "experiments/demo")
        self.assertEqual(code, 1)
        self.assertIn("MISSING_KEY", err)
        self.assertIn("experiments/demo/bad.md: ", err)
        self.assertEqual(p_good.read_bytes(), good_before)

    def test_new_question_roundtrips_four_awkward_titles_via_questions_json(self):
        awkward = [
            ("q-awk-1", 'Why #1 is "best" and \'worst\''),
            ("q-awk-2", '#2: [fast] "quoted" \'mix\' > pipe | tail:'),
            ("q-awk-3", '- leading dash: "a" and \'b\' # keep hash'),
            ("q-awk-4", '| block indicator & *star* "x" \'y\': ok'),
        ]
        for qid, title in awkward:
            code, _, err = self.run_cli(
                "new-question", title, "--id", qid, "--field", "gpu-computing", "--date", "2026-11-20"
            )
            self.assertEqual(code, 0, err)

        code, out, err = self.run_cli("questions", "--json")
        self.assertEqual(code, 0, err)
        by_id = {row["id"]: row for row in json.loads(out)}
        for qid, title in awkward:
            self.assertEqual(by_id[qid]["title"], title)
        self.assertEqual(self.run_cli("check")[0], 0)

    def test_reconcile_contradicts_leaves_wrong_claim_wrong_and_marks_verified_unverified_disputed(self):
        old_p = write(
            self.root,
            "entries/2026/2026-01-10-states.md",
            "---\n"
            "id: 2026-01-10-states\n"
            "title: Mixed states\n"
            "date: 2026-01-10\n"
            "kind: finding\n"
            "relevance: act\n"
            "fields: [gpu-computing]\n"
            "---\n\n"
            "## Summary\n\nMixed.\n\n"
            "## Claims\n\n"
            "- [wrong] [c-wrg00001] False statement. (via: audit, 2026-01-10)\n"
            "- [verified] [c-ver00002] Verified statement. (via: docs, 2026-01-10)\n"
            "- [unverified] [c-unv00003] Unverified statement.\n\n"
            "## Sources\n\n- [rig] bench\n",
        )
        write(
            self.root,
            "entries/2026/2026-01-20-rebut.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-20-rebut").replace(
                "- [verified] Graphs replay with one call. (via: NVIDIA docs, 2026-01-02)",
                "- [verified] [c-reb00001] Rebuts all three. (via: bench, 2026-01-20) "
                "(contradicts: c-wrg00001, c-ver00002, c-unv00003)",
            ),
        )
        code, _, err = self.run_cli("reconcile", "2026-01-20-rebut")
        self.assertEqual(code, 0, err)
        after = old_p.read_text(encoding="utf-8")
        self.assertIn("- [wrong] [c-wrg00001] False statement. (via: audit, 2026-01-10) (contradicted-by: c-reb00001)", after)
        self.assertIn("- [disputed] [c-ver00002] Verified statement. (via: docs, 2026-01-10) (contradicted-by: c-reb00001)", after)
        self.assertIn("- [disputed] [c-unv00003] Unverified statement. (contradicted-by: c-reb00001)", after)
        self.assertEqual(self.run_cli("check")[0], 0)

    def test_unbound_number_warnings_ignore_product_and_title_tag_numbers(self):
        write(self.root, "experiments/demo/results.json", json.dumps({"accuracy": 0.842}))
        write(self.root, "experiments/demo/README.md", "# Demo\n")
        write(self.root, "experiments/demo/experiment.json", json.dumps({
            "schema": "rnd-experiment/v1",
            "name": "demo",
            "status": "running",
            "design": "README.md",
            "template": None,
            "budgets": [],
            "licences": [],
            "runs": [],
        }))
        p = write(
            self.root,
            "entries/2026/2026-01-12-names.md",
            "---\n"
            "id: 2026-01-12-names\n"
            "title: Benchmarking llama 3.1 on RTX 5090\n"
            "date: 2026-01-12\n"
            "kind: finding\n"
            "relevance: act\n"
            "fields: [gpu-computing]\n"
            "tags: [rtx-5090, llama-3.1]\n"
            "---\n\n"
            "## Summary\n\nSummary.\n\n"
            "## Claims\n\n"
            "- [verified] On the RTX 5090, Jev 1.13 and llama 3.1 scored "
            "84.2%<!-- rnd:experiments/demo/results.json#accuracy:.1% -->. "
            "(via: experiments/demo/results.json, 2026-11-19)\n\n"
            "## Sources\n\n- [rig] bench\n",
        )
        code, out, err = self.run_cli("check")
        self.assertEqual(code, 0, err)
        self.assertIn("0 errors, 0 warnings", out)

        # Metric names, seed numbers, and numbers with measurement units still trigger warnings.
        write(
            self.root,
            "entries/2026/2026-01-12-names.md",
            p.read_text(encoding="utf-8").replace(
                "84.2%<!-- rnd:experiments/demo/results.json#accuracy:.1% -->.",
                "84.2%<!-- rnd:experiments/demo/results.json#accuracy:.1% --> on Seed 42 with AUC 0.91 and CUDA 10 ms.",
            ),
        )
        code, out, err = self.run_cli("check")
        self.assertEqual(code, 0)
        self.assertIn("0 errors, 1 warnings", out)
        self.assertIn("42, 0.91, 10", err)

    def test_bump_failure_between_version_and_changelog_never_bumps_twice(self):
        # 1. Runtime failure during insert_changelog rolls back __init__.py and keeps fragments.
        self.run_cli("change", "Fix claims check", "--level", "patch")
        with mock.patch.object(release, "insert_changelog", side_effect=OSError("disk full")):
            code, _, err = self.run_cli("bump")
        self.assertEqual(code, 3)
        self.assertIn("disk full", err)
        self.assertIn('__version__ = "1.0.0"', (self.root / "mcptoolshop_rnd/__init__.py").read_text(encoding="utf-8"))
        self.assertEqual(len(list((self.root / "changes").glob("*.md"))), 1)

        code, out, _ = self.run_cli("bump")
        self.assertEqual(code, 0)
        self.assertIn("bumped 1.0.0 -> 1.0.1.0.0", out)
        self.assertIn('__version__ = "1.0.1.0.0"', (self.root / "mcptoolshop_rnd/__init__.py").read_text(encoding="utf-8"))
        self.assertIn("## [1.0.1.0.0]", (self.root / "CHANGELOG.md").read_text(encoding="utf-8"))
        self.assertFalse((self.root / "changes").exists())

        # 2. Simulated crash state: __init__.py already holds the bumped version 1.0.2.0.0 while CHANGELOG.md
        #    still stops at 1.0.1.0.0 -> re-run finishes 1.0.2.0.0 instead of raising to 1.0.3.0.0.
        self.run_cli("change", "Recover interrupted bump", "--level", "patch")
        release.write_version(self.root, "1.0.2.0.0")
        code, out, _ = self.run_cli("bump")
        self.assertEqual(code, 0)
        self.assertIn("bumped 1.0.1.0.0 -> 1.0.2.0.0", out)
        self.assertIn('__version__ = "1.0.2.0.0"', (self.root / "mcptoolshop_rnd/__init__.py").read_text(encoding="utf-8"))
        self.assertIn("## [1.0.2.0.0]", (self.root / "CHANGELOG.md").read_text(encoding="utf-8"))
        self.assertNotIn("1.0.3.0.0", (self.root / "mcptoolshop_rnd/__init__.py").read_text(encoding="utf-8"))

        # 3. Non-fragment bump checks CHANGELOG.md before writing __init__.py.
        write(self.root, "CHANGELOG.md", "# Changelog\n")
        with mock.patch.object(release, "last_tag", return_value=None), \
                mock.patch.object(release, "changes", return_value=[]):
            code, _, err = self.run_cli("bump")
        self.assertEqual(code, 2)
        self.assertIn("BAD_CHANGELOG", err)
        self.assertIn('__version__ = "1.0.2.0.0"', (self.root / "mcptoolshop_rnd/__init__.py").read_text(encoding="utf-8"))

    def test_collect_resolve_guard_reached_via_symlink_into_instruments(self):
        # Unused regexes removed from model (fix-1 C7).
        self.assertFalse(hasattr(model, "HEADING_RE"))
        self.assertFalse(hasattr(model, "CLAIM_LINE_RE"))

        payload = b'{"ok": true}\n'
        import hashlib
        sha = hashlib.sha256(payload).hexdigest()
        write(self.root, "experiments/demo-col/README.md", "# col\n")
        write(
            self.root,
            "experiments/demo-col/extract.py",
            f"def trim(raw, ctx):\n    return {{'provenance': {{'repo': ctx.repo, 'source': ctx.source, 'sha256': {sha!r}}}}}\n",
        )
        clone = self.root.parent / "demo-src-guard"
        (clone / ".git").mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, clone, True)

        spec = {
            "repo": "x/y",
            "sibling": "demo-src-guard",
            "sources": [{"path": "out.json", "commit": "a" * 40, "sha256": sha, "out": "results/leak.json", "fn": "trim"}],
        }
        # spec_problems accepts 'results/leak.json', so only the resolve() guard can stop traversal through the link.
        self.assertEqual(collect.spec_problems(spec), [])
        write(self.root, "experiments/demo-col/collect.json", json.dumps(spec))

        inst_dir = self.root / "instruments"
        link_path = self.root / "experiments/demo-col/results"
        try:
            os.symlink(inst_dir, link_path, target_is_directory=True)
        except OSError:  # pragma: no cover
            import _winapi
            _winapi.CreateJunction(str(inst_dir), str(link_path))

        before_inst = {p.name: p.read_bytes() for p in sorted(inst_dir.iterdir()) if p.is_file()}
        with mock.patch.object(collect, "git_show", return_value=payload):
            code, _, err = self.run_cli("collect", "demo-col", "--clone", str(clone))
        self.assertEqual(code, 2)
        self.assertIn("COLLECT_BAD_SPEC", err)
        self.assertIn("escapes experiments/demo-col/", err)
        self.assertFalse((inst_dir / "leak.json").exists())
        after_inst = {p.name: p.read_bytes() for p in sorted(inst_dir.iterdir()) if p.is_file()}
        self.assertEqual(after_inst, before_inst)


if __name__ == "__main__":
    unittest.main()
