"""Tests for rnd 1.3 Part A: review follow-ups on claims, check, sync, questions, bump, and collect."""

import json
import os
import shutil
import unittest
from pathlib import Path
from unittest import mock

from mcptoolshop_rnd import collect, model, questions, release

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

        # 3. Reverse-only hints: [superseded] and [disputed] instruct setting state back, while [wrong] must NOT.
        id_s0 = model.make_claim_id("2026-01-02-sample", "Graphs replay with one call.")
        id_s1 = model.make_claim_id("2026-01-02-sample", "It helps decode more than diffusion.")
        other_p = self.root / "entries/2026/2026-01-03-other.md"
        other_p.write_text(
            other_p.read_text(encoding="utf-8").replace(
                "- [unverified] It helps decode more than diffusion.",
                "- [wrong] [c-oldwrg1] Known false claim. (via: audit, 2026-01-03)",
            ),
            encoding="utf-8",
        )
        p_new = write(
            self.root,
            "entries/2026/2026-01-12-newer.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-12-newer").replace(
                "- [verified] Graphs replay with one call. (via: NVIDIA docs, 2026-01-02)",
                f"- [verified] [c-newsup01] Newer supersedes. (via: bench, 2026-01-12) (supersedes: {id_s0})",
            ).replace(
                "- [unverified] It helps decode more than diffusion.",
                f"- [verified] [c-newcon02] Newer contradicts. (via: bench, 2026-01-12) "
                f"(contradicts: {id_s1}, c-oldwrg1)",
            ),
        )
        self.assertEqual(self.run_cli("reconcile", "2026-01-12-newer")[0], 0)
        p_new.write_text(
            p_new.read_text(encoding="utf-8")
            .replace(f" (supersedes: {id_s0})", "")
            .replace(f" (contradicts: {id_s1}, c-oldwrg1)", ""),
            encoding="utf-8",
        )
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("remove '(superseded-by: c-newsup01)' from entries/2026/2026-01-02-sample.md and set its state back", err)
        self.assertIn("remove '(contradicted-by: c-newcon02)' from entries/2026/2026-01-02-sample.md and set its state back", err)
        wrong_lines = [ln for ln in err.splitlines() if "c-oldwrg1" in ln]
        self.assertEqual(len(wrong_lines), 1, err)
        self.assertIn("remove '(contradicted-by: c-newcon02)' from entries/2026/2026-01-03-other.md", wrong_lines[0])
        self.assertNotIn("set its state back", wrong_lines[0])

        # Also cover missing-target case on a [wrong] claim (must not suggest setting state back).
        other_p.write_text(
            other_p.read_text(encoding="utf-8").replace("c-newcon02", "c-deadbeef"),
            encoding="utf-8",
        )
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        wrong_missing = [ln for ln in err.splitlines() if "c-oldwrg1" in ln]
        self.assertEqual(len(wrong_missing), 1, err)
        self.assertIn("remove stale '(contradicted-by: c-deadbeef)' from entries/2026/2026-01-03-other.md,", wrong_missing[0])
        self.assertNotIn("set its state back", wrong_missing[0])

        # Cover in-memory load_text error paths cleanly.
        ent_none, probs_none = model.load_text("---\nbad\n", "entries/2026/bad.md")
        self.assertIsNone(ent_none)
        self.assertEqual(probs_none[0].level, "error")
        q_none, q_probs = questions.load_text("no frontmatter\n", "questions/bad.md")
        self.assertIsNone(q_none)
        self.assertEqual(q_probs[0].level, "error")
        q_bad_yaml, q_bad_probs = questions.load_text("---\n[broken\n---\n", "questions/bad2.md")
        self.assertIsNone(q_bad_yaml)
        self.assertEqual(q_bad_probs[0].level, "error")

        # Cover unreadable-file decode errors in model.load and questions.load.
        bad_entry_p = self.root / "entries/2026/bad-bytes.md"
        bad_entry_p.write_bytes(b"\xff\xfe")
        bad_q_p = self.root / "questions/bad-bytes.md"
        bad_q_p.parent.mkdir(parents=True, exist_ok=True)
        bad_q_p.write_bytes(b"\xff\xfe")
        ent_bytes, probs_bytes = model.load(bad_entry_p, self.root)
        self.assertIsNone(ent_bytes)
        self.assertIn("unreadable:", probs_bytes[0].message)
        q_bytes, q_probs_bytes = questions.load(bad_q_p, self.root)
        self.assertIsNone(q_bytes)
        self.assertIn("unreadable:", q_probs_bytes[0].message)
        bad_entry_p.unlink()
        bad_q_p.unlink()

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

        def make_entry(eid, title, tags, claims_lines):
            claims_block = "\n".join(claims_lines)
            return write(
                self.root,
                f"entries/2026/{eid}.md",
                "---\n"
                f"id: {eid}\n"
                f"title: {title}\n"
                "date: 2026-01-12\n"
                "kind: finding\n"
                "relevance: act\n"
                "fields: [gpu-computing]\n"
                f"tags: [{', '.join(tags)}]\n"
                "---\n\n"
                "## Summary\n\nSummary.\n\n"
                "## Claims\n\n"
                f"{claims_block}\n\n"
                "## Sources\n\n- [rig] bench\n",
            )

        # 1. Explicit patterns (RTX 5090) and title/tag pairs (Switchyard 2, RTX 5090) do NOT warn.
        p = make_entry(
            "2026-01-12-names",
            "Benchmarking Switchyard 2 on RTX 5090",
            ["rtx-5090", "switchyard-2"],
            [
                "- [verified] On the RTX 5090, Switchyard 2, CUDA 13, and Llama 3 scored "
                "84.2%<!-- rnd:experiments/demo/results.json#accuracy:.1% -->. "
                "(via: experiments/demo/results.json, 2026-11-19)",
            ],
        )
        code, out, err = self.run_cli("check")
        self.assertEqual(code, 0, err)
        self.assertIn("0 errors, 0 warnings", out)
        p.unlink()

        # 2. Without Switchyard 2 in title/tags, non-pattern Switchyard 2 STILL warns (whereas RTX 5090 stays ignored).
        p2 = make_entry(
            "2026-01-12-generic",
            "Benchmarking results",
            ["bench"],
            [
                "- [verified] Switchyard 2 ran on RTX 5090. (via: experiments/demo/results.json, 2026-11-19)",
            ],
        )
        code, out, err = self.run_cli("check")
        self.assertEqual(code, 0)
        self.assertIn("0 errors, 1 warnings", out)
        self.assertIn("unbound number(s) (2):", err)
        p2.unlink()

        # 3. Reviewer's three measured sentences + measured figure after RTX 5090 + decimals/percents/units ALL warn.
        p3 = make_entry(
            "2026-01-12-rev",
            "Jev 1.13 and RTX 5090 measurements",
            ["rtx-5090", "jev-1.13"],
            [
                "- [verified] Kev-4B 87.5 on the hard set, against Jev 81.2. (via: experiments/demo/results.json, 2026-11-19)",
                "- [verified] Across 350 hard pairs the judge never flipped. (via: experiments/demo/results.json, 2026-11-19)",
                "- [verified] Lifetime completion on Death Road to Canada 20.3 and Spire 12.3. (via: experiments/demo/results.json, 2026-11-19)",
                "- [verified] RTX 5090 reached 87.5%. (via: experiments/demo/results.json, 2026-11-19)",
                "- [verified] Jev 1.13 and CUDA 10 ms at Batch 1,562. (via: experiments/demo/results.json, 2026-11-19)",
            ],
        )
        code, out, err = self.run_cli("check")
        self.assertEqual(code, 0)
        self.assertIn("0 errors, 5 warnings", out)
        self.assertIn("(87.5, 81.2)", err)
        self.assertIn("(350)", err)
        self.assertIn("(20.3, 12.3)", err)
        self.assertIn("(87.5%)", err)
        self.assertIn("(1.13, 10, 1,562)", err)
        p3.unlink()

    def test_bump_failure_between_version_and_changelog_never_bumps_twice(self):
        cl_path = self.root / "CHANGELOG.md"
        init_path = self.root / "mcptoolshop_rnd/__init__.py"
        orig_cl_bytes = cl_path.read_bytes()
        orig_init_bytes = init_path.read_bytes()

        # 1. Partial write failure INSIDE staging CHANGELOG.md temp file (simulates mid-write ENOSPC).
        #    Both CHANGELOG.md and __init__.py remain completely intact, and no .tmp files linger.
        p_frag = Path(write(self.root, "changes/2026-11-20-aaaaaaaa-fix-claims-check.md",
                            "---\nlevel: patch\ndate: 2026-11-20\n---\n\nFix claims check\n"))
        orig_fdopen = release.os.fdopen

        def failing_cl_fdopen(fd, mode, *args, **kwargs):
            real_fh = orig_fdopen(fd, mode, *args, **kwargs)
            failing_cl_fdopen.calls += 1
            if failing_cl_fdopen.calls == 2:
                class HalfWriter:
                    def write(self, data):
                        real_fh.write(data[:47])
                        real_fh.flush()
                        raise OSError(28, "No space left on device")
                    def flush(self):
                        real_fh.flush()
                    def fileno(self):
                        return real_fh.fileno()
                    def close(self):
                        real_fh.close()
                return HalfWriter()
            return real_fh

        failing_cl_fdopen.calls = 0
        with mock.patch.object(release.os, "fdopen", side_effect=failing_cl_fdopen):
            code, _, err = self.run_cli("bump")
        self.assertEqual(code, 3)
        self.assertIn("No space left on device", err)
        self.assertEqual(cl_path.read_bytes(), orig_cl_bytes)
        self.assertEqual(init_path.read_bytes(), orig_init_bytes)
        self.assertFalse(list(self.root.glob(".*tmp*")))
        self.assertFalse(list((self.root / "mcptoolshop_rnd").glob(".*tmp*")))
        self.assertTrue(p_frag.exists())

        # 1b. Failure on the FIRST os.replace inside apply_bump cleans up both temp files and leaves targets untouched.
        with mock.patch.object(release.os, "replace", side_effect=OSError(13, "First replace denied")):
            code, _, err = self.run_cli("bump")
        self.assertEqual(code, 3)
        self.assertIn("First replace denied", err)
        self.assertEqual(init_path.read_bytes(), orig_init_bytes)
        self.assertEqual(cl_path.read_bytes(), orig_cl_bytes)
        self.assertFalse(list(self.root.glob(".*tmp*")))
        self.assertFalse(list((self.root / "mcptoolshop_rnd").glob(".*tmp*")))

        # 1c. Direct _atomic_write_bytes os.replace failure cleans up temp file and leaves __init__.py untouched.
        with mock.patch.object(release.os, "replace", side_effect=OSError(13, "Atomic replace denied")), \
                self.assertRaises(OSError):
            release.write_version(self.root, "9.9.9")
        self.assertEqual(init_path.read_bytes(), orig_init_bytes)
        self.assertFalse(list((self.root / "mcptoolshop_rnd").glob(".*tmp*")))

        # 2. Failure BETWEEN replacing __init__.py and replacing CHANGELOG.md rolls back __init__.py atomically.
        orig_replace = release.os.replace

        def fail_second_replace(src, dst):
            fail_second_replace.calls += 1
            if fail_second_replace.calls == 2:
                raise OSError(13, "Permission denied")
            return orig_replace(src, dst)

        fail_second_replace.calls = 0
        with mock.patch.object(release.os, "replace", side_effect=fail_second_replace):
            code, _, err = self.run_cli("bump")
        self.assertEqual(code, 3)
        self.assertIn("Permission denied", err)
        self.assertEqual(init_path.read_bytes(), orig_init_bytes)
        self.assertEqual(cl_path.read_bytes(), orig_cl_bytes)
        self.assertFalse(list(self.root.glob(".*tmp*")))
        self.assertTrue(p_frag.exists())

        # 3. Simulated crash BETWEEN the two os.replace calls: __init__.py is at 1.0.1.0.0, CHANGELOG.md still at 1.0.0.
        release.write_version(self.root, "1.0.1.0.0")
        crashed_init_bytes = init_path.read_bytes()
        patch_frag_bytes = p_frag.read_bytes()

        # 3a. Re-run at a LOWER level (nano) must refuse with BAD_CHANGELOG naming both versions, never bump or clobber.
        p_frag.write_text("---\nlevel: nano\ndate: 2026-11-20\n---\n\nLower nano note\n", encoding="utf-8")
        code, _, err = self.run_cli("bump")
        self.assertEqual(code, 2)
        self.assertIn("BAD_CHANGELOG", err)
        self.assertIn("1.0.1.0.0", err)
        self.assertIn("1.0.0", err)
        self.assertEqual(init_path.read_bytes(), crashed_init_bytes)
        self.assertEqual(cl_path.read_bytes(), orig_cl_bytes)

        # 3b. Re-run at the MATCHING level (patch) completes 1.0.1.0.0 cleanly and writes exact expected CHANGELOG bytes.
        p_frag.write_bytes(patch_frag_bytes)
        today_iso = __import__("datetime").date.today().isoformat()
        eol = "\r\n" if b"\r\n" in orig_cl_bytes else "\n"
        expected_cl = (
            f"# Changelog\n\n## [Unreleased]\n\n"
            f"## [1.0.1.0.0] - {today_iso}\n\n"
            f"- Fix claims check\n\n"
            f"## [1.0.0] - 2026-01-01\n"
        ).replace("\n", eol).encode("utf-8")
        code, out, err = self.run_cli("bump")
        self.assertEqual(code, 0, err)
        self.assertIn("bumped 1.0.0 -> 1.0.1.0.0", out)
        self.assertIn('__version__ = "1.0.1.0.0"', init_path.read_text(encoding="utf-8"))
        self.assertEqual(cl_path.read_bytes(), expected_cl)
        self.assertFalse((self.root / "changes").exists())

        # 4. Subsequent crash recovery at higher version 1.0.2.0.0 + lower level without fragments also refuses cleanly.
        release.write_version(self.root, "1.0.2.0.0")
        with mock.patch.object(release, "last_tag", return_value=None), \
                mock.patch.object(release, "changes", return_value=[]):
            code, _, err = self.run_cli("bump", "nano")
            self.assertEqual(code, 2)
            self.assertIn("BAD_CHANGELOG", err)
            self.assertEqual(cl_path.read_bytes(), expected_cl)

            # Matching level finishes 1.0.2.0.0
            code, out, err = self.run_cli("bump", "patch")
            self.assertEqual(code, 0, err)
            self.assertIn("bumped 1.0.1.0.0 -> 1.0.2.0.0", out)
            self.assertIn("## [1.0.2.0.0]", cl_path.read_text(encoding="utf-8"))
            self.assertIn("## [1.0.1.0.0]", cl_path.read_text(encoding="utf-8"))
            self.assertIn("## [1.0.0] - 2026-01-01", cl_path.read_text(encoding="utf-8"))

        # 5. Missing ## [Unreleased] refuses before touching __init__.py or writing temp files.
        write(self.root, "CHANGELOG.md", "# Changelog\n")
        init_before_bad = init_path.read_bytes()
        with mock.patch.object(release, "last_tag", return_value=None), \
                mock.patch.object(release, "changes", return_value=[]):
            code, _, err = self.run_cli("bump")
        self.assertEqual(code, 2)
        self.assertIn("BAD_CHANGELOG", err)
        self.assertEqual(init_path.read_bytes(), init_before_bad)

        # 6. Non-version CHANGELOG heading falls back cleanly in resolve_bump_versions without crashing.
        write(self.root, "CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n\n## [unparsed-tag] - 2026-01-01\n")
        current_ver = release.read_version(self.root)
        self.assertEqual(
            release.resolve_bump_versions(self.root, "nano"),
            (current_ver, release.bump(current_ver, "nano")),
        )

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
