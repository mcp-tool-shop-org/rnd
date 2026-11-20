"""Tests for rnd 1.2: changelog fragments, bound numbers, claim ids/links, questions, miss log, and guards."""

import datetime as dt
import json
import os
import shutil
import sqlite3
import subprocess
from pathlib import Path
from unittest import mock

from mcptoolshop_rnd import catalog, cli, collect, layout, model, numbers, probe, questions, release, store, watch

from .test_cli import CliBase
from .test_rnd import ENTRY, write


class FragmentTests(CliBase):
    def test_change_writes_non_colliding_fragments_and_leaves_version_and_changelog_alone(self):
        before_ver = (self.root / "mcptoolshop_rnd" / "__init__.py").read_text(encoding="utf-8")
        before_cl = (self.root / "CHANGELOG.md").read_text(encoding="utf-8")

        class FixedDate(dt.date):
            @classmethod
            def today(cls):
                return cls(2026, 11, 19)

        with mock.patch.object(release, "date", FixedDate):
            c1, o1, _ = self.run_cli("change", "First update on branch A")
            c2, o2, _ = self.run_cli("change", "Second update on branch B", "--level", "minor")
        self.assertEqual((c1, c2), (0, 0))
        p1, p2 = o1.strip(), o2.strip()
        self.assertNotEqual(p1, p2)
        self.assertTrue(p1.startswith("changes/2026-11-19-"))
        self.assertTrue(p2.startswith("changes/2026-11-19-"))
        self.assertIn("level: nano", (self.root / p1).read_text(encoding="utf-8"))
        self.assertIn("level: minor", (self.root / p2).read_text(encoding="utf-8"))
        self.assertEqual((self.root / "mcptoolshop_rnd" / "__init__.py").read_text(encoding="utf-8"), before_ver)
        self.assertEqual((self.root / "CHANGELOG.md").read_text(encoding="utf-8"), before_cl)

        code, _, err = self.run_cli("change", "   ")
        self.assertEqual(code, 2)
        self.assertIn("BAD_CHANGE", err)
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 0)

    def test_bump_with_fragments_takes_highest_level_writes_one_section_and_deletes_fragments(self):
        self.run_cli("change", "Ordinary entry note", "--level", "nano")
        self.run_cli("change", "New feature note", "--level", "minor")
        self.run_cli("change", "Structural note", "--level", "micro")

        code, out, _ = self.run_cli("bump", "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("would bump 1.0.0 -> 1.1.0.0.0 (3 fragment(s), level minor)", out)
        self.assertIn("- Ordinary entry note", out)
        self.assertIn("- New feature note", out)
        self.assertEqual(len(list((self.root / "changes").glob("*.md"))), 3)
        self.assertIn('__version__ = "1.0.0"', (self.root / "mcptoolshop_rnd" / "__init__.py").read_text(encoding="utf-8"))

        # Missing ## [Unreleased] refuses cleanly before deleting fragments or bumping version.
        saved_cl = (self.root / "CHANGELOG.md").read_text(encoding="utf-8")
        write(self.root, "CHANGELOG.md", "# Changelog\n")
        code, _, err = self.run_cli("bump")
        self.assertEqual(code, 2)
        self.assertIn("BAD_CHANGELOG", err)
        self.assertEqual(len(list((self.root / "changes").glob("*.md"))), 3)
        write(self.root, "CHANGELOG.md", saved_cl)

        code, out, _ = self.run_cli("bump", "--note", "Release summary")
        self.assertEqual(code, 0, out)
        self.assertIn("bumped 1.0.0 -> 1.1.0.0.0 (3 fragment(s), level minor)", out)
        self.assertIn("- Release summary", out)
        self.assertIn('__version__ = "1.1.0.0.0"', (self.root / "mcptoolshop_rnd" / "__init__.py").read_text(encoding="utf-8"))
        cl = (self.root / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## [1.1.0.0.0]", cl)
        self.assertIn("- Ordinary entry note", cl)
        self.assertIn("- New feature note", cl)
        self.assertFalse((self.root / "changes").exists())

        # With no fragments left, bump falls back to git-diff flow (mocking git to keep test isolated).
        with mock.patch.object(release, "last_tag", return_value="v1.1.0.0.0"), \
                mock.patch.object(release, "changes", return_value=[]):
            code, out, _ = self.run_cli("bump")
        self.assertEqual(code, 0)
        self.assertIn("bumped 1.1.0.0.0 -> 1.1.0.0.1", out)

    def test_check_and_bump_report_malformed_fragments_as_errors(self):
        cases = [
            ("changes/no-fm.md", "plain text without frontmatter\n", "missing frontmatter"),
            ("changes/bad-yaml.md", "---\n: :\n---\nhi\n", "unreadable fragment"),
            ("changes/unknown-key.md", "---\nlevel: nano\nwho: test\n---\nhi\n", "unknown fragment keys"),
            ("changes/bad-level.md", "---\nlevel: giant\n---\nhi\n", "fragment 'level'"),
            ("changes/bad-date.md", "---\nlevel: nano\ndate: 19-11-2026\n---\nhi\n", "fragment 'date'"),
            ("changes/empty-body.md", "---\nlevel: nano\n---\n   \n", "fragment body is empty"),
            ("changes/nested/sub.md", "---\nlevel: nano\n---\nhi\n", "directly under changes/"),
        ]
        for rel, content, needle in cases:
            p = write(self.root, rel, content)
            code, _, err = self.run_cli("check")
            self.assertEqual(code, 1, rel)
            self.assertIn(needle, err, rel)
            code, _, err = self.run_cli("bump")
            self.assertEqual(code, 1, rel)
            self.assertIn("BAD_FRAGMENT", err, rel)
            p.unlink()


class BoundNumberTests(CliBase):
    def _setup_demo_experiment(self, extra=None):
        data = {
            "accuracy": 0.842,
            "delta": -0.0083,
            "count": 1562,
            "range_lo": 0.956,
            "range_hi": 0.963,
            "gemma4:31b": 86016,
            "kev": {"brier": 0.24},
        }
        if extra:
            data.update(extra)
        write(self.root, "experiments/demo/README.md", "# Demo\n\nCount: 999<!-- rnd:experiments/demo/results.json#count:,d -->.\n")
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
        write(self.root, "experiments/demo/results.json", json.dumps(data))

    def test_sync_rewrites_bound_numbers_across_entries_briefs_questions_and_experiment_notes(self):
        self._setup_demo_experiment()
        write(
            self.root,
            "entries/2026/2026-01-10-bound.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-10-bound").replace(
                "CUDA graphs cut launch overhead for small kernels.",
                "Summary range 0.956-0.900<!-- rnd:experiments/demo/results.json#range_hi:.3f -->.",
            ).replace(
                "- [verified] Graphs replay with one call. (via: NVIDIA docs, 2026-01-02)",
                "- [verified] Accuracy 10.0%<!-- rnd:experiments/demo/results.json#accuracy:.1% -->, "
                "delta +0.00%<!-- rnd:experiments/demo/results.json#delta:+.2% -->, "
                "range 0.900<!-- rnd:experiments/demo/results.json#range_lo:.3f -->-"
                "0.900<!-- rnd:experiments/demo/results.json#range_hi:.3f -->, "
                "win 10<!-- rnd:experiments/demo/results.json#gemma4:31b:d -->, "
                "brier 0.100<!-- rnd:experiments/demo/results.json#kev.brier:.3f -->. "
                "`99.9%<!-- rnd:experiments/missing/results.json#x:.1% -->` "
                "(via: experiments/demo, 2026-11-19)\n\n"
                "```markdown\n"
                "0.0%<!-- rnd:experiments/missing/results.json#ignored:.1% -->\n"
                "```\n",
            ),
        )
        write(
            self.root,
            "site/src/content/docs/briefs/demo-brief.md",
            "---\ntitle: Demo\n---\n\nBrier 0.1<!-- rnd:experiments/demo/results.json#kev.brier:.3f -->.\n",
        )
        write(
            self.root,
            "questions/2026-11-19-q.md",
            "---\nid: 2026-11-19-q\ntitle: Q\ndate: 2026-11-19\nstatus: open\nfields: [gpu-computing]\n---\n\n"
            "Target 10<!-- rnd:experiments/demo/results.json#count:,d -->.\n",
        )

        # Missing or outside explicit paths exit 2.
        code, _, err = self.run_cli("sync", "entries/2026/nope.md")
        self.assertEqual(code, 2)
        self.assertIn("NOT_FOUND", err)
        outside = self.root.parent / "outside.md"
        write(self.root.parent, "outside.md", "1<!-- rnd:experiments/demo/results.json#count:d -->\n")
        self.addCleanup(lambda: outside.exists() and outside.unlink())
        code, _, err = self.run_cli("sync", str(outside))
        self.assertEqual(code, 2)
        self.assertIn("OUTSIDE_LIBRARY", err)

        code, out, _ = self.run_cli("sync")
        self.assertEqual(code, 0, out)
        self.assertIn("updated entries/2026/2026-01-10-bound.md#accuracy: 10.0% -> 84.2%", out)
        entry_text = (self.root / "entries/2026/2026-01-10-bound.md").read_text(encoding="utf-8")
        self.assertIn("84.2%<!-- rnd:experiments/demo/results.json#accuracy:.1% -->", entry_text)
        self.assertIn("-0.83%<!-- rnd:experiments/demo/results.json#delta:+.2% -->", entry_text)
        self.assertIn("Summary range 0.956-0.963<!-- rnd:experiments/demo/results.json#range_hi:.3f -->.", entry_text)
        self.assertIn("0.956<!-- rnd:experiments/demo/results.json#range_lo:.3f -->-0.963<!-- rnd:experiments/demo/results.json#range_hi:.3f -->", entry_text)
        self.assertIn("86016<!-- rnd:experiments/demo/results.json#gemma4:31b:d -->", entry_text)
        self.assertIn("0.240<!-- rnd:experiments/demo/results.json#kev.brier:.3f -->", entry_text)
        self.assertIn("`99.9%<!-- rnd:experiments/missing/results.json#x:.1% -->`", entry_text)
        self.assertIn("1,562<!-- rnd:experiments/demo/results.json#count:,d -->",
                      (self.root / "experiments/demo/README.md").read_text(encoding="utf-8"))
        self.assertIn("0.240<!--", (self.root / "site/src/content/docs/briefs/demo-brief.md").read_text(encoding="utf-8"))
        self.assertIn("1,562<!--", (self.root / "questions/2026-11-19-q.md").read_text(encoding="utf-8"))

        # Check passes with 0 errors and 0 warnings once bound!
        code, out, err = self.run_cli("check")
        self.assertEqual(code, 0, err)
        self.assertIn("0 errors, 0 warnings", out)

        # Instrument files cannot be rewritten by sync.
        inst_path = self.root / "instruments/tool-x.md"
        inst_path.write_text(
            inst_path.read_text(encoding="utf-8") + "\nVal 1<!-- rnd:experiments/demo/results.json#count:d -->.\n",
            encoding="utf-8",
        )
        code, _, err = self.run_cli("sync", "instruments/tool-x.md")
        self.assertEqual(code, 2)
        self.assertIn("INSTRUMENTS_PROTECTED", err)

    def test_sync_check_exits_1_on_drift_without_writing_and_0_when_in_sync(self):
        self._setup_demo_experiment()
        readme = self.root / "experiments/demo/README.md"
        before = readme.read_text(encoding="utf-8")
        code, out, _ = self.run_cli("sync", "experiments/demo", "--check")
        self.assertEqual(code, 1)
        self.assertIn("would update experiments/demo/README.md#count: 999 -> 1,562", out)
        self.assertEqual(readme.read_text(encoding="utf-8"), before)

        code, out, _ = self.run_cli("sync", "experiments/demo", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(len(json.loads(out)["changed"]), 1)

        # Sync also refuses malformed bindings and missing files with exit 1.
        write(self.root, "experiments/demo/README.md", "bad <!-- rnd:experiments/demo/results.json#count:d -->\n")
        self.assertEqual(self.run_cli("sync", "experiments/demo")[0], 1)
        write(self.root, "experiments/demo/README.md", "1<!-- rnd:experiments/missing/results.json#count:d -->\n")
        self.assertEqual(self.run_cli("sync", "experiments/demo")[0], 1)
        write(self.root, "experiments/demo/README.md", "1,562<!-- rnd:experiments/demo/results.json#count:,d -->.\n")

        code, out, _ = self.run_cli("sync", "--check")
        self.assertEqual(code, 0)
        self.assertIn("in sync:", out)

    def test_crlf_mixed_line_endings_and_missing_final_newline_preserved(self):
        self._setup_demo_experiment()
        crlf_old = self.root / "entries/2026/2026-01-02-sample.md"
        crlf_bytes = crlf_old.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8")
        crlf_old.write_bytes(crlf_bytes)

        # 1. `claims assign` keeps CRLF line endings on every line.
        code, _, err = self.run_cli("claims", "assign", "2026-01-02-sample")
        self.assertEqual(code, 0, err)
        assigned_bytes = crlf_old.read_bytes()
        self.assertEqual(assigned_bytes.count(b"\r\n"), assigned_bytes.count(b"\n"))

        # 2. `reconcile` keeps CRLF line endings + trailing non-ASCII without turning file to LF.
        id_s0 = model.make_claim_id("2026-01-02-sample", "Graphs replay with one call.")
        write(
            self.root,
            "entries/2026/2026-01-29-crlfnew.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-29-crlfnew").replace(
                "- [unverified] It helps decode more than diffusion.",
                f"- [verified] [c-crlf0001] Replaces éüï claim. (via: bench, 2026-01-29) (supersedes: {id_s0})",
            ),
        )
        code, _, err = self.run_cli("reconcile", "2026-01-29-crlfnew")
        self.assertEqual(code, 0, err)
        reconciled_bytes = crlf_old.read_bytes()
        self.assertEqual(reconciled_bytes.count(b"\r\n"), reconciled_bytes.count(b"\n"))
        self.assertIn(b"\r\n- [superseded] ", reconciled_bytes)

        # 3. `sync` preserves CRLF and mixed endings + missing final newline at EOF.
        crlf_sync = self.root / "entries/2026/2026-01-30-sync-crlf.md"
        crlf_sync.write_bytes((
            "---\r\nid: 2026-01-30-sync-crlf\r\ntitle: CRLF\r\ndate: 2026-01-30\r\n"
            "kind: finding\r\nrelevance: act\r\nfields: [gpu-computing]\r\ntags: [cuda]\r\n---\r\n\r\n"
            "## Summary\r\n\r\nRate 1.0%<!-- rnd:experiments/demo/results.json#accuracy:.1% -->.\r\n"
        ).encode("utf-8"))
        mixed_note = self.root / "experiments/demo/README.md"
        # Mixed line endings (line 1 CRLF, line 2 LF) and NO trailing newline at EOF.
        mixed_note.write_bytes(b"First line\r\nSecond 1<!-- rnd:experiments/demo/results.json#count:,d -->")
        code, _, err = self.run_cli("sync", "entries/2026/2026-01-30-sync-crlf.md", "experiments/demo/README.md")
        self.assertEqual(code, 0, err)
        synced_crlf = crlf_sync.read_bytes()
        self.assertEqual(synced_crlf.count(b"\r\n"), synced_crlf.count(b"\n"))
        self.assertIn(b"84.2%<!-- rnd:experiments/demo/results.json#accuracy:.1% -->", synced_crlf)
        self.assertEqual(
            mixed_note.read_bytes(),
            b"First line\r\nSecond 1,562<!-- rnd:experiments/demo/results.json#count:,d -->",
        )

        # 4. Sync MISSING_KEY error names the Markdown file and leaves sibling drifted files untouched (C11).
        crlf_sync.write_bytes(crlf_sync.read_bytes().replace(b"84.2%", b"10.0%"))
        sibling_before = crlf_sync.read_bytes()
        mixed_note.write_bytes(b"Bad 1<!-- rnd:experiments/demo/results.json#missing_key:d -->\n")
        code, _, err = self.run_cli("sync")
        self.assertEqual(code, 1)
        self.assertIn("MISSING_KEY", err)
        self.assertIn("experiments/demo/README.md: ", err)
        self.assertEqual(crlf_sync.read_bytes(), sibling_before)

    def test_check_errors_on_drifted_literal_missing_file_missing_key_and_bad_bindings(self):
        self._setup_demo_experiment()
        # 1. Drifted literal
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("differs from experiments/demo/results.json#count", err)

        self.run_cli("sync")
        # 2. Missing results file
        write(self.root, "experiments/demo/README.md", "1.0<!-- rnd:experiments/nope/results.json#a:.1f -->\n")
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("missing bound results file experiments/nope/results.json", err)

        # 3. Missing key
        write(self.root, "experiments/demo/README.md", "1.0<!-- rnd:experiments/demo/results.json#nope:.1f -->\n")
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("has no key 'nope'", err)

        # 4. Non-numeric value & bad format
        self._setup_demo_experiment({"flag": True, "label": "abc"})
        write(self.root, "experiments/demo/README.md", "1<!-- rnd:experiments/demo/results.json#flag:d -->\n")
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("must be a number", err)

        write(self.root, "experiments/demo/README.md", "1<!-- rnd:experiments/demo/results.json#accuracy:d -->\n")
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("invalid format", err)

        # 5. Malformed binding & missing preceding number
        write(self.root, "experiments/demo/README.md", "84%<!-- rnd:bad/path#x:.1f -->\n")
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("invalid binding target", err)

        write(self.root, "experiments/demo/README.md", "value <!-- rnd:experiments/demo/results.json#accuracy:.1% -->\n")
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("no numeric literal directly before it", err)

        # 6. results.json with machine path or invalid JSON
        write(self.root, "experiments/demo/README.md", "# clean\n")
        bad_home = "/" + "home" + "/acct/results.jsonl"
        write(self.root, "experiments/demo/results.json", json.dumps({"source": bad_home}))
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("machine path", err)

        write(self.root, "experiments/demo/results.json", "{broken")
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("unreadable experiments/demo/results.json", err)

    def test_verified_experiment_claim_with_unbound_number_is_warning_not_error(self):
        self._setup_demo_experiment()
        write(self.root, "experiments/demo/README.md", "# Demo\n")
        entry_path = "entries/2026/2026-01-11-unbound.md"
        write(
            self.root,
            entry_path,
            ENTRY.replace("2026-01-02-sample", "2026-01-11-unbound").replace(
                "- [verified] Graphs replay with one call. (via: NVIDIA docs, 2026-01-02)",
                "- [verified] Kev-4B v1.0 scored 84.2% on the split. (via: experiments/demo/results.json, 2026-11-19)",
            ),
        )
        code, out, err = self.run_cli("check")
        self.assertEqual(code, 0)
        self.assertIn("0 errors, 1 warnings", out)
        self.assertIn("has unbound number(s) (84.2%)", err)

        write(
            self.root,
            entry_path,
            ENTRY.replace("2026-01-02-sample", "2026-01-11-unbound").replace(
                "- [verified] Graphs replay with one call. (via: NVIDIA docs, 2026-01-02)",
                "- [verified] Kev-4B v1.0 scored 84.2%<!-- rnd:experiments/demo/results.json#accuracy:.1% --> on the split. "
                "(via: experiments/demo/results.json, 2026-11-19)",
            ),
        )
        code, out, _ = self.run_cli("check")
        self.assertEqual(code, 0)
        self.assertIn("0 errors, 0 warnings", out)


class ClaimsAndReconcileTests(CliBase):
    def test_claims_assign_is_deterministic_idempotent_and_protects_instruments(self):
        code, out, _ = self.run_cli("claims", "assign", "2026-01-02-sample", "--json")
        self.assertEqual(code, 0)
        assigned = json.loads(out)["assigned"]
        self.assertEqual(len(assigned), 2)
        self.assertTrue(all(model.CLAIM_ID_RE.match(cid) for cid in assigned))
        expected = [
            model.make_claim_id("2026-01-02-sample", "Graphs replay with one call."),
            model.make_claim_id("2026-01-02-sample", "It helps decode more than diffusion."),
        ]
        self.assertEqual(assigned, expected)

        # Running assign a second time changes nothing.
        before = (self.root / "entries/2026/2026-01-02-sample.md").read_text(encoding="utf-8")
        code, out, _ = self.run_cli("claims", "assign", "2026-01-02-sample")
        self.assertEqual(code, 0)
        self.assertIn("none needed", out)
        self.assertEqual((self.root / "entries/2026/2026-01-02-sample.md").read_text(encoding="utf-8"), before)

        # Error & protection cases.
        code, _, err = self.run_cli("claims", "assign")
        self.assertEqual(code, 2)
        self.assertIn("USAGE", err)
        code, _, err = self.run_cli("claims", "assign", "missing-entry")
        self.assertEqual(code, 2)
        self.assertIn("NOT_FOUND", err)
        code, _, err = self.run_cli("claims", "assign", "tool-x")
        self.assertEqual(code, 2)
        self.assertIn("INSTRUMENTS_PROTECTED", err)

    def test_reconcile_marks_superseded_disputed_and_supported_without_changing_sentence_or_other_lines(self):
        # Assign id on sample's first claim only, leaving sample's second claim and other's first claim unassigned.
        old_sample_path = self.root / "entries/2026/2026-01-02-sample.md"
        old_other_path = self.root / "entries/2026/2026-01-03-other.md"
        id_s0 = model.make_claim_id("2026-01-02-sample", "Graphs replay with one call.")
        id_s1 = model.make_claim_id("2026-01-02-sample", "It helps decode more than diffusion.")
        id_o0 = model.make_claim_id("2026-01-03-other", "Graphs replay with one call.")

        old_sample_before = old_sample_path.read_text(encoding="utf-8").splitlines()
        old_other_before = old_other_path.read_text(encoding="utf-8").splitlines()

        write(
            self.root,
            "entries/2026/2026-01-15-followup.md",
            "---\nid: 2026-01-15-followup\ntitle: Followup\ndate: 2026-01-15\nkind: finding\nrelevance: act\n"
            "fields: [gpu-computing]\ntags: [cuda]\n---\n\n## Summary\n\nFollowup.\n\n## Claims\n\n"
            f"- [verified] Graphs replay with batching too. (via: bench, 2026-01-15) (supersedes: {id_s0})\n"
            f"- [verified] Decode gains match diffusion gains. (via: bench, 2026-01-15) (contradicts: {id_s1})\n"
            f"- [verified] Confirmed in second study. (via: bench, 2026-01-15) (supports: {id_o0})\n\n"
            "## Sources\n\n- [rig] bench\n",
        )

        # Before reconcile: rnd check errors and suggests `rnd reconcile 2026-01-15-followup`.
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("rnd reconcile 2026-01-15-followup", err)

        code, out, _ = self.run_cli("reconcile", "2026-01-15-followup")
        self.assertEqual(code, 0, out)
        self.assertIn("reconciled 3 link(s) across 3 changed file(s)", out)

        old_sample_after = old_sample_path.read_text(encoding="utf-8").splitlines()
        old_other_after = old_other_path.read_text(encoding="utf-8").splitlines()

        # Non-claim lines are byte-for-byte identical.
        self.assertEqual(len(old_sample_before), len(old_sample_after))
        for idx, (b, a) in enumerate(zip(old_sample_before, old_sample_after)):
            if "Graphs replay with one call." in b or "It helps decode more than diffusion." in b:
                self.assertIn(b.split("]", 1)[1].strip(), a)  # exact sentence + via preserved!
            else:
                self.assertEqual(b, a, f"sample line {idx} changed unexpectedly")

        self.assertEqual(len(old_other_before), len(old_other_after))
        for idx, (b, a) in enumerate(zip(old_other_before, old_other_after)):
            if "Graphs replay with one call." in b:
                self.assertIn(b.split("]", 1)[1].strip(), a)
                self.assertTrue(a.startswith("- [verified] "))  # supports does not alter state
            else:
                self.assertEqual(b, a, f"other line {idx} changed unexpectedly")

        new_claims = model.load(self.root / "entries/2026/2026-01-15-followup.md", self.root)[0].claims
        id_f0, id_f1, id_f2 = [c["id"] for c in new_claims]
        self.assertIn(f"- [superseded] [{id_s0}] Graphs replay with one call. (via: NVIDIA docs, 2026-01-02) (superseded-by: {id_f0})", old_sample_after)
        self.assertIn(f"- [disputed] [{id_s1}] It helps decode more than diffusion. (contradicted-by: {id_f1})", old_sample_after)
        self.assertIn(f"- [verified] [{id_o0}] Graphs replay with one call. (via: NVIDIA docs, 2026-01-02) (supported-by: {id_f2})", old_other_after)

        # Running reconcile twice changes nothing!
        code, out, _ = self.run_cli("reconcile", "2026-01-15-followup", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["changed_files"], [])

        # Library check is now clean!
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 0, err)

        # Missing target claim id fails with CLAIM_NOT_FOUND.
        write(
            self.root,
            "entries/2026/2026-01-16-badlink.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-16-badlink").replace(
                "- [unverified] It helps decode more than diffusion.",
                "- [unverified] Bad link. (supersedes: c-00000000)",
            ),
        )
        code, _, err = self.run_cli("reconcile", "2026-01-16-badlink")
        self.assertEqual(code, 1)
        self.assertIn("CLAIM_NOT_FOUND", err)

        # Self-relation refuses cleanly with SELF_RELATION.
        write(
            self.root,
            "entries/2026/2026-01-16-badlink.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-16-badlink").replace(
                "- [unverified] It helps decode more than diffusion.",
                "- [unverified] [c-self0001] Self link. (supersedes: c-self0001)",
            ),
        )
        code, _, err = self.run_cli("reconcile", "2026-01-16-badlink")
        self.assertEqual(code, 1)
        self.assertIn("SELF_RELATION", err)
        (self.root / "entries/2026/2026-01-16-badlink.md").unlink()

        # Reconcile refuses to target an instrument claim.
        inst = self.root / "instruments/tool-x.md"
        inst.write_text(inst.read_text(encoding="utf-8") + "\n## Claims\n\n- [unverified] [c-inst0001] Tool fact.\n",
                        encoding="utf-8")
        write(
            self.root,
            "entries/2026/2026-01-16-badlink.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-16-badlink").replace(
                "- [unverified] It helps decode more than diffusion.",
                "- [unverified] Overrides tool. (supersedes: c-inst0001)",
            ),
        )
        code, _, err = self.run_cli("reconcile", "2026-01-16-badlink")
        self.assertEqual(code, 2)
        self.assertIn("INSTRUMENTS_PROTECTED", err)

    def test_check_errors_on_nonexistent_claim_id_one_sided_links_duplicates_and_self_links(self):
        self.run_cli("claims", "assign", "2026-01-02-sample")
        c0 = model.load(self.root / "entries/2026/2026-01-02-sample.md", self.root)[0].claims[0]["id"]

        # Nonexistent target claim id -> error with rnd reconcile hint.
        write(
            self.root,
            "entries/2026/2026-01-17-missing.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-17-missing").replace(
                "- [unverified] It helps decode more than diffusion.",
                "- [unverified] [c-1111aaaa] Claims target missing. (supersedes: c-deadbeef)",
            ),
        )
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("does not exist", err)
        self.assertIn("rnd reconcile 2026-01-17-missing", err)
        (self.root / "entries/2026/2026-01-17-missing.md").unlink()

        # One-sided link (with assigned id, and with unassigned source id) -> error with rnd reconcile hint.
        write(
            self.root,
            "entries/2026/2026-01-17-onesided.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-17-onesided").replace(
                "- [unverified] It helps decode more than diffusion.",
                f"- [unverified] [c-1111bbbb] One-sided. (supersedes: {c0})",
            ),
        )
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("link present on one side only", err)
        self.assertIn("rnd reconcile 2026-01-17-onesided", err)

        # Duplicate claim id, malformed id, and self-link.
        write(
            self.root,
            "entries/2026/2026-01-17-onesided.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-17-onesided").replace(
                "- [unverified] It helps decode more than diffusion.",
                f"- [unverified] [{c0}] Dup id.\n"
                "- [unverified] [c-bad id] Bad id.\n"
                "- [unverified] [c-3333cccc] Self rel. (contradicts: c-3333cccc)",
            ),
        )
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("duplicate claim id", err)
        self.assertIn("must match 'c-<id>'", err)
        self.assertIn("cannot state 'contradicts' on itself", err)

    def test_fenced_and_duplicate_claims_headings_and_claim_mismatch_guard(self):
        # 1. Entry with fenced `## Claims` headings before one real `## Claims` heading.
        fenced_entry = (
            "---\n"
            "id: 2026-01-20-fence\n"
            "title: Fence test\n"
            "date: 2026-01-20\n"
            "kind: finding\n"
            "relevance: act\n"
            "fields: [gpu-computing]\n"
            "tags: [cuda]\n"
            "---\n\n"
            "## Summary\n\n"
            "```markdown\n"
            "## Claims\n"
            "- [unverified] Example inside a fence.\n"
            "```\n\n"
            "~~~markdown\n"
            "## Claims\n"
            "- [unverified] Second example in tilde fence.\n"
            "~~~\n\n"
            "## Claims\n\n"
            "- [unverified] Real first claim.\n"
            "- [unverified] Real second claim.\n\n"
            "## Sources\n\n"
            "- [rig] bench\n"
        )
        p = self.root / "entries/2026/2026-01-20-fence.md"
        p.write_bytes(fenced_entry.encode("utf-8"))
        before_bytes = p.read_bytes()
        id_r0 = model.make_claim_id("2026-01-20-fence", "Real first claim.")
        id_r1 = model.make_claim_id("2026-01-20-fence", "Real second claim.")

        code, out, err = self.run_cli("claims", "assign", "2026-01-20-fence", "--json")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["assigned"], [id_r0, id_r1])
        after_assign = p.read_bytes()
        expected_assign = (
            before_bytes
            .replace(b"- [unverified] Real first claim.", f"- [unverified] [{id_r0}] Real first claim.".encode())
            .replace(b"- [unverified] Real second claim.", f"- [unverified] [{id_r1}] Real second claim.".encode())
        )
        self.assertEqual(after_assign, expected_assign)
        self.assertEqual(self.run_cli("check")[0], 0)

        # Fresh fenced copy for reconcile (unassigned real claims, fenced headings ignored).
        p.write_bytes(fenced_entry.encode("utf-8"))
        write(
            self.root,
            "entries/2026/2026-02-01-newfence.md",
            ENTRY.replace("2026-01-02-sample", "2026-02-01-newfence").replace(
                "- [unverified] It helps decode more than diffusion.",
                f"- [verified] Supersedes real first. (via: bench, 2026-02-01) (supersedes: {id_r0})",
            ),
        )
        code, out, err = self.run_cli("reconcile", "2026-02-01-newfence")
        self.assertEqual(code, 0, err or out)
        id_nf = model.make_claim_id("2026-02-01-newfence", "Supersedes real first.")
        after_rec = p.read_bytes()
        expected_rec = before_bytes.replace(
            b"- [unverified] Real first claim.",
            f"- [superseded] [{id_r0}] Real first claim. (superseded-by: {id_nf})".encode(),
        )
        self.assertEqual(after_rec, expected_rec)
        self.assertEqual(self.run_cli("check")[0], 0)
        (self.root / "entries/2026/2026-02-01-newfence.md").unlink()

        # 2. Entry with two real `## Claims` headings: `rnd check` reports an error and writers
        # refuse with MULTIPLE_CLAIMS_HEADINGS without modifying any file.
        dup_entry = (
            "---\n"
            "id: 2026-01-21-duphead\n"
            "title: Duplicate claims headings\n"
            "date: 2026-01-21\n"
            "kind: finding\n"
            "relevance: act\n"
            "fields: [gpu-computing]\n"
            "tags: [cuda]\n"
            "---\n\n"
            "## Claims\n\n"
            "- [unverified] First section claim.\n\n"
            "## Claims\n\n"
            "- [unverified] Second section claim.\n\n"
            "## Sources\n\n"
            "- [rig] bench\n"
        )
        p_dup = self.root / "entries/2026/2026-01-21-duphead.md"
        write(self.root, "entries/2026/2026-01-21-duphead.md", dup_entry)
        dup_bytes = p_dup.read_bytes()
        id_sec2 = model.make_claim_id("2026-01-21-duphead", "Second section claim.")
        code, _, err = self.run_cli("claims", "assign", "2026-01-21-duphead")
        self.assertEqual(code, 1)
        self.assertIn("MULTIPLE_CLAIMS_HEADINGS", err)
        self.assertEqual(p_dup.read_bytes(), dup_bytes)
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("multiple '## Claims' headings (2 found)", err)

        # Reconcile also refuses without writing when target has two real Claims headings.
        p_newdup = write(
            self.root,
            "entries/2026/2026-02-02-newdup.md",
            ENTRY.replace("2026-01-02-sample", "2026-02-02-newdup").replace(
                "- [unverified] It helps decode more than diffusion.",
                f"- [verified] Supersedes sec2. (via: bench, 2026-02-02) (supersedes: {id_sec2})",
            ),
        )
        newdup_bytes = p_newdup.read_bytes()
        code, _, err = self.run_cli("reconcile", "2026-02-02-newdup")
        self.assertEqual(code, 1)
        self.assertIn("MULTIPLE_CLAIMS_HEADINGS", err)
        self.assertEqual(p_dup.read_bytes(), dup_bytes)
        self.assertEqual(p_newdup.read_bytes(), newdup_bytes)
        p_dup.unlink()
        p_newdup.unlink()

        # 3. Pre-write CLAIM_MISMATCH refusal writes nothing.
        before_bytes = p.read_bytes()
        with self.assertRaises(model.ReconcileError) as ctx:
            model._apply_claim_line_edits(p, {0: {"assign_id": "c-00000001", "expected_id": "", "expected_text": "Wrong sentence."}})
        self.assertEqual(ctx.exception.code, "CLAIM_MISMATCH")
        self.assertEqual(p.read_bytes(), before_bytes)

        # 4. Duplicate claim id across files refuses in reconcile (C8).
        write(
            self.root,
            "entries/2026/2026-02-03-dupa.md",
            ENTRY.replace("2026-01-02-sample", "2026-02-03-dupa").replace(
                "- [unverified] It helps decode more than diffusion.",
                "- [unverified] [c-99998888] Claim A.",
            ),
        )
        write(
            self.root,
            "entries/2026/2026-02-04-dupb.md",
            ENTRY.replace("2026-01-02-sample", "2026-02-04-dupb").replace(
                "- [unverified] It helps decode more than diffusion.",
                "- [unverified] [c-99998888] Claim B.",
            ),
        )
        write(
            self.root,
            "entries/2026/2026-02-05-dupc.md",
            ENTRY.replace("2026-01-02-sample", "2026-02-05-dupc").replace(
                "- [unverified] It helps decode more than diffusion.",
                "- [verified] Overrides dup. (via: bench, 2026-02-05) (supersedes: c-99998888)",
            ),
        )
        code, _, err = self.run_cli("reconcile", "2026-02-05-dupc")
        self.assertEqual(code, 1)
        self.assertIn("DUPLICATE_CLAIM_ID", err)

    def test_reverse_only_link_hint_and_repairs(self):
        old_p = self.root / "entries/2026/2026-01-02-sample.md"
        id_s0 = model.make_claim_id("2026-01-02-sample", "Graphs replay with one call.")
        write(
            self.root,
            "entries/2026/2026-01-22-newer.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-22-newer").replace(
                "- [unverified] It helps decode more than diffusion.",
                f"- [verified] [c-new11111] Newer claim. (via: bench, 2026-01-22) (supersedes: {id_s0})",
            ),
        )
        self.assertEqual(self.run_cli("reconcile", "2026-01-22-newer")[0], 0)
        new_p = self.root / "entries/2026/2026-01-22-newer.md"

        # Break the forward side so only the reverse half remains.
        new_orig = new_p.read_bytes()
        new_p.write_text(
            new_p.read_text(encoding="utf-8").replace(f" (supersedes: {id_s0})", ""),
            encoding="utf-8",
        )
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("link present on one side only", err)
        self.assertNotIn(f"); run `rnd reconcile 2026-01-22-newer`", err)
        self.assertIn(f"add '(supersedes: {id_s0})' to c-new11111", err)
        self.assertIn("remove '(superseded-by: c-new11111)'", err)

        # Hinted repair 1: restore forward relation and run reconcile -> check clean.
        new_p.write_bytes(new_orig)
        self.assertEqual(self.run_cli("reconcile", "2026-01-22-newer")[0], 0)
        self.assertEqual(self.run_cli("check")[0], 0)

        # Hinted repair 2: remove forward side, then remove stale reverse clause -> check clean.
        new_p.write_text(
            new_p.read_text(encoding="utf-8").replace(f" (supersedes: {id_s0})", ""),
            encoding="utf-8",
        )
        self.assertEqual(self.run_cli("check")[0], 1)
        old_p.write_text(
            old_p.read_text(encoding="utf-8")
            .replace("[superseded]", "[verified]")
            .replace(" (superseded-by: c-new11111)", ""),
            encoding="utf-8",
        )
        self.assertEqual(self.run_cli("check")[0], 0)

    def test_relation_target_must_be_claim_id_not_prose(self):
        write(
            self.root,
            "entries/2026/2026-01-25-prose.md",
            "---\n"
            "id: 2026-01-25-prose\n"
            "title: Prose glosses\n"
            "date: 2026-01-25\n"
            "kind: finding\n"
            "relevance: act\n"
            "fields: [gpu-computing]\n"
            "tags: [cuda]\n"
            "---\n\n"
            "## Summary\n\nSummary.\n\n"
            "## Claims\n\n"
            "- [unverified] Prose ending with a gloss (supports: the earlier benchmark)\n"
            "- [verified] Gloss before via (supports: the earlier benchmark) (via: docs, 2026-01-25)\n"
            "- [unverified] Empty rel stays text (supersedes: )\n"
            "- [verified] Double via keeps first (via: X) (via: Y)\n\n"
            "## Sources\n\n"
            "- [rig] bench\n",
        )
        e, probs = model.load(self.root / "entries/2026/2026-01-25-prose.md", self.root)
        self.assertFalse(any(p.level == "error" for p in probs), probs)
        self.assertEqual(e.claims[0]["relations"], {})
        self.assertEqual(e.claims[0]["text"], "Prose ending with a gloss (supports: the earlier benchmark)")
        self.assertEqual(e.claims[1]["relations"], {})
        self.assertEqual(e.claims[1]["text"], "Gloss before via (supports: the earlier benchmark)")
        self.assertEqual(e.claims[1]["via"], "docs, 2026-01-25")
        self.assertEqual(e.claims[2]["relations"], {})
        self.assertEqual(e.claims[2]["text"], "Empty rel stays text (supersedes: )")
        self.assertEqual(e.claims[3]["text"], "Double via keeps first (via: X)")
        self.assertEqual(e.claims[3]["via"], "Y")
        self.assertEqual(self.run_cli("check")[0], 0)

    def test_wrapped_multiline_claim_reconcile_places_inverse_at_end_and_keeps_words(self):
        wrapped_entry = (
            "---\n"
            "id: 2026-01-26-wrapped\n"
            "title: Wrapped claim\n"
            "date: 2026-01-26\n"
            "kind: finding\n"
            "relevance: act\n"
            "fields: [gpu-computing]\n"
            "tags: [cuda]\n"
            "---\n\n"
            "## Summary\n\nSummary.\n\n"
            "## Claims\n\n"
            "- [unverified] Old sentence that wraps\n"
            "  onto a second line. (via: docs, 2026-01-01)\n"
            "- [verified] Unchanged claim. (via: docs, 2026-01-01)\n\n"
            "## Sources\n\n"
            "- [rig] bench\n"
        )
        p_wrap = self.root / "entries/2026/2026-01-26-wrapped.md"
        write(self.root, "entries/2026/2026-01-26-wrapped.md", wrapped_entry)
        id_w0 = model.make_claim_id("2026-01-26-wrapped", "Old sentence that wraps onto a second line.")
        write(
            self.root,
            "entries/2026/2026-02-06-contradict.md",
            ENTRY.replace("2026-01-02-sample", "2026-02-06-contradict").replace(
                "- [unverified] It helps decode more than diffusion.",
                f"- [verified] [c-cont0001] Refutes wrapped claim. (via: bench, 2026-02-06) (contradicts: {id_w0})",
            ),
        )
        code, out, err = self.run_cli("reconcile", "2026-02-06-contradict")
        self.assertEqual(code, 0, err or out)
        after = p_wrap.read_text(encoding="utf-8")
        self.assertIn(
            f"- [disputed] [{id_w0}] Old sentence that wraps\n"
            "  onto a second line. (via: docs, 2026-01-01) (contradicted-by: c-cont0001)\n",
            after,
        )
        self.assertIn("- [verified] Unchanged claim. (via: docs, 2026-01-01)\n", after)
        # Idempotent second run changes nothing, and check passes cleanly.
        code, out, _ = self.run_cli("reconcile", "2026-02-06-contradict", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["changed_files"], [])
        self.assertEqual(self.run_cli("check")[0], 0)

    def test_index_search_show_and_claims_command_surface_superseded_and_disputed_claims(self):
        id_s0 = model.make_claim_id("2026-01-02-sample", "Graphs replay with one call.")
        id_s1 = model.make_claim_id("2026-01-02-sample", "It helps decode more than diffusion.")
        write(
            self.root,
            "entries/2026/2026-01-18-update.md",
            "---\nid: 2026-01-18-update\ntitle: Update\ndate: 2026-01-18\nkind: finding\nrelevance: act\n"
            "fields: [gpu-computing]\ntags: [cuda]\n---\n\n## Summary\n\nUpdate.\n\n## Claims\n\n"
            f"- [verified] [c-newsup01] New replay fact. (via: bench, 2026-01-18) (supersedes: {id_s0})\n"
            f"- [verified] [c-newcon02] Decode contradiction. (via: bench, 2026-01-18) (contradicts: {id_s1})\n\n"
            "## Sources\n\n- [rig] bench\n",
        )
        self.assertEqual(self.run_cli("reconcile", "2026-01-18-update")[0], 0)

        code, out, _ = self.run_cli("claims", "--state", "superseded")
        self.assertEqual(code, 0)
        self.assertIn(id_s0, out)
        self.assertIn("superseded-by: c-newsup01", out)

        code, out, _ = self.run_cli("claims", "--state", "disputed", "--json")
        self.assertEqual(code, 0)
        rows = json.loads(out)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["relations"]["contradicted-by"], ["c-newcon02"])

        code, out, _ = self.run_cli("show", "2026-01-02-sample")
        self.assertEqual(code, 0)
        self.assertIn(f"! [superseded] {id_s0}: Graphs replay with one call. — replaced by c-newsup01 (2026-01-18-update)", out)
        self.assertIn(f"! [disputed] {id_s1}: It helps decode more than diffusion. — contradicted by c-newcon02 (2026-01-18-update)", out)

        code, out, _ = self.run_cli("show", "2026-01-02-sample", "--json")
        claims_json = json.loads(out)["claims"]
        self.assertEqual(claims_json[0]["replaced_by"], [{"id": "c-newsup01", "entry_id": "2026-01-18-update"}])
        self.assertEqual(claims_json[1]["contradicted_by"], [{"id": "c-newcon02", "entry_id": "2026-01-18-update"}])

        code, out, _ = self.run_cli("search", "launch", "overhead")
        self.assertEqual(code, 0)
        self.assertIn("! [superseded]", out)
        self.assertIn("replaced by c-newsup01 (2026-01-18-update)", out)
        self.assertIn("! [disputed]", out)
        self.assertIn("contradicted by c-newcon02 (2026-01-18-update)", out)


class QuestionTests(CliBase):
    def test_new_question_questions_list_show_and_search(self):
        code, out, _ = self.run_cli(
            "new-question", "Why does latency spike at 8k?", "--field", "gpu-computing", "--tag", "kv-cache", "--date", "2026-11-19"
        )
        self.assertEqual(code, 0)
        qpath = out.strip()
        self.assertEqual(qpath, "questions/2026-11-19-why-does-latency-spike-at-8k.md")
        self.assertTrue((self.root / qpath).is_file())

        code, out, _ = self.run_cli("questions", "--status", "open", "--field", "gpu-computing")
        self.assertEqual(code, 0)
        self.assertIn("2026-11-19-why-does-latency-spike-at-8k", out)
        self.assertIn("[open]", out)

        code, out, _ = self.run_cli("questions", "--json")
        self.assertEqual(json.loads(out)[0]["fields"], ["gpu-computing"])

        code, out, _ = self.run_cli("search", "latency", "spike", "--field", "gpu-computing", "--exact")
        self.assertEqual(code, 0)
        self.assertIn("Questions (1)", out)
        self.assertIn("2026-11-19-why-does-latency-spike-at-8k", out)

        code, out, _ = self.run_cli("show", "2026-11-19-why-does-latency-spike-at-8k")
        self.assertEqual(code, 0)
        self.assertIn("question · status:open", out)

        # Title containing ' #' is safely quoted; bad date fails cleanly.
        self.assertEqual(self.run_cli("new-question", "Why #2?", "--id", "q-hash", "--date", "2026-11-19")[0], 0)
        self.assertEqual(self.run_cli("new-question", "Bad date", "--date", "nope")[0], 2)

        # Error cases for new-question
        self.assertEqual(self.run_cli("new-question", "   ")[0], 2)
        self.assertEqual(self.run_cli("new-question", "X", "--id", "Bad ID")[0], 2)
        self.assertEqual(self.run_cli("new-question", "Dup", "--id", "2026-11-19-why-does-latency-spike-at-8k")[0], 2)

    def test_new_question_refuses_invalid_answered_and_roundtrips_complex_title(self):
        before_q = sorted(p.name for p in (self.root / "questions").glob("*")) if (self.root / "questions").exists() else []
        code, _, err = self.run_cli("new-question", "Answered without id", "--status", "answered", "--field", "gpu-computing")
        self.assertEqual(code, 2)
        self.assertIn("BAD_ANSWERED_BY", err)

        code, _, err = self.run_cli(
            "new-question", "Answered bad id", "--status", "answered", "--answered-by", "c-deadbeef", "--field", "gpu-computing"
        )
        self.assertEqual(code, 2)
        self.assertIn("CLAIM_NOT_FOUND", err)
        after_q = sorted(p.name for p in (self.root / "questions").glob("*")) if (self.root / "questions").exists() else []
        self.assertEqual(after_q, before_q)

        # Valid --answered-by succeeds and passes check.
        self.run_cli("claims", "assign", "2026-01-02-sample")
        c0 = model.load(self.root / "entries/2026/2026-01-02-sample.md", self.root)[0].claims[0]["id"]
        code, out, err = self.run_cli(
            "new-question", "Answered ok", "--status", "answered", "--answered-by", c0, "--field", "gpu-computing"
        )
        self.assertEqual(code, 0, err)
        self.assertTrue((self.root / out.strip()).is_file())
        self.assertEqual(self.run_cli("check")[0], 0)

        # Title with '#', '"', and "'" round-trips losslessly (C4).
        tricky = 'Why #1 is "best" and \'worst\''
        code, _, err = self.run_cli("new-question", tricky, "--id", "q-tricky", "--field", "gpu-computing", "--date", "2026-11-19")
        self.assertEqual(code, 0, err)
        code, out, _ = self.run_cli("questions", "--json")
        self.assertEqual(code, 0)
        by_id = {row["id"]: row for row in json.loads(out)}
        self.assertEqual(by_id["q-tricky"]["title"], tricky)

    def test_check_validates_questions_and_errors_on_answered_without_existing_claim_id(self):
        self.run_cli("claims", "assign", "2026-01-02-sample")
        c0 = model.load(self.root / "entries/2026/2026-01-02-sample.md", self.root)[0].claims[0]["id"]

        # Valid answered question naming an existing claim id passes.
        q_ok = (
            "---\nid: q-ok\ntitle: Answered question\ndate: 2026-11-19\nstatus: answered\n"
            f"fields: [gpu-computing]\nanswered_by: [{c0}]\n---\n\n## Question\n\nAnswered.\n"
        )
        write(self.root, "questions/q-ok.md", q_ok)
        self.assertEqual(self.run_cli("check")[0], 0)
        code, out, _ = self.run_cli("show", "q-ok")
        self.assertEqual(code, 0)
        self.assertIn(f"answered_by: {c0}", out)

        bad_cases = [
            (q_ok.replace(f"answered_by: [{c0}]", "answered_by: []"), "needs 'answered_by'"),
            (q_ok.replace(c0, "c-doesnotexist"), "does not exist"),
            (q_ok.replace("status: answered", "status: maybe"), "'status' must be one of"),
            (q_ok.replace("date: 2026-11-19", "date: bad"), "'date' must be YYYY-MM-DD"),
            (q_ok.replace("fields: [gpu-computing]", "fields: []"), "'fields' needs"),
            ("---\nid: q-ok\ntitle: X\ndate: 2026-11-19\nstatus: open\nfields: [a]\nwho: bad\n---\n", "unknown question frontmatter keys"),
            ("no frontmatter here\n", "missing frontmatter"),
        ]
        for content, needle in bad_cases:
            write(self.root, "questions/q-bad.md", content)
            code, _, err = self.run_cli("check")
            self.assertEqual(code, 1, needle)
            self.assertIn(needle, err)
        (self.root / "questions/q-bad.md").unlink()

        # Duplicate question id is an error.
        write(self.root, "questions/q-dup.md", q_ok)
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("duplicate id 'q-ok'", err)


class UsageMissTests(CliBase):
    def test_search_miss_log_no_usage_env_and_stats_usage(self):
        miss_file = store.misses_path(self.root, self.root / "rnd.db")
        code, out, _ = self.run_cli("stats", "--usage", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["usage"]["misses"], 0)
        self.assertEqual(self.run_cli("search", "cuda")[0], 0)
        self.assertFalse(miss_file.exists())

        with mock.patch.object(layout.subprocess, "run", side_effect=OSError("no git")):
            write(self.root, "rnd.misses.jsonl", "")
            self.assertNotIn("rnd.misses.jsonl", layout.library_files(self.root))
            self.assertNotIn("rnd.db", layout.library_files(self.root))
            (self.root / "rnd.misses.jsonl").unlink()

        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("RND_NO_USAGE", None)
            self.assertEqual(self.run_cli("search", "missingtermone")[0], 0)
            self.assertEqual(self.run_cli("search", "missingtermone")[0], 0)
            self.assertEqual(self.run_cli("search", "missingtermtwo")[0], 0)
            os.environ["RND_NO_USAGE"] = "1"
            self.assertEqual(self.run_cli("search", "ignoredwhenoff")[0], 0)

        lines = miss_file.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 3)
        parsed = [json.loads(line) for line in lines]
        self.assertEqual([set(row.keys()) for row in parsed], [{"time", "query"}] * 3)
        self.assertEqual([row["query"] for row in parsed], ["missingtermone", "missingtermone", "missingtermtwo"])

        code, out, _ = self.run_cli("stats", "--usage")
        self.assertEqual(code, 0)
        self.assertIn("search misses (rnd.misses.jsonl): 3", out)
        self.assertIn("2  missingtermone", out)
        self.assertIn("1  missingtermtwo", out)

        code, out, _ = self.run_cli("stats", "--usage", "--json")
        data = json.loads(out)
        self.assertEqual(data["usage"]["misses"], 3)
        self.assertEqual(data["usage"]["top_misses"], [
            {"query": "missingtermone", "count": 2},
            {"query": "missingtermtwo", "count": 1},
        ])


class InstrumentsAndExtrasTests(CliBase):
    def _instruments_snapshot(self):
        base = self.root / "instruments"
        return {
            p.relative_to(base).as_posix(): p.read_bytes()
            for p in sorted(base.rglob("*"))
            if p.is_file()
        }

    def test_watch_probe_collect_and_catalog_sync_cannot_write_under_instruments(self):
        before = self._instruments_snapshot()

        # 1. rnd watch (valid run + hostile --state inside instruments/)
        write(self.root, "docs/watchlist.json", json.dumps({
            "schema": "rnd-watchlist/v1",
            "sources": [{"id": "ollama", "kind": "github-releases", "url": "https://github.com/ollama/ollama"}],
        }))
        state_tmp = self.root / "watch-state.json"
        with mock.patch.object(watch, "gh_json", return_value=[{"tag_name": "v0.1.0", "html_url": "https://x", "draft": False}]):
            code, _, _ = self.run_cli("watch", "--state", str(state_tmp))
            self.assertEqual(code, 0)
            code, _, err = self.run_cli("watch", "--state", str(self.root / "instruments" / "leak.json"))
            self.assertEqual(code, 2)
            self.assertIn("INSTRUMENTS_PROTECTED", err)

        # 2. rnd probe (valid run + hostile --db inside instruments/)
        with mock.patch.object(probe, "http_json", return_value={"info": {"version": "1.0", "license": "MIT"}, "releases": {}}):
            code, _, _ = self.run_cli("probe", "https://pypi.org/project/demo")
            self.assertEqual(code, 0)
            code, _, err = self.run_cli("--db", str(self.root / "instruments" / "leak.db"), "probe", "https://pypi.org/project/demo")
            self.assertEqual(code, 2)
            self.assertIn("INSTRUMENTS_PROTECTED", err)

        # 3. rnd collect (valid run + hostile traversal out path toward instruments/)
        write(self.root, "experiments/demo-col/README.md", "# col\n")
        write(self.root, "experiments/demo-col/extract.py",
              "def trim(raw, ctx):\n    return {'provenance': {'repo': ctx.repo, 'source': ctx.source, 'sha256': ''}}\n")
        payload = b'{"ok": true}\n'
        import hashlib
        sha = hashlib.sha256(payload).hexdigest()
        write(self.root, "experiments/demo-col/extract.py",
              f"def trim(raw, ctx):\n    return {{'provenance': {{'repo': ctx.repo, 'source': ctx.source, 'sha256': {sha!r}}}}}\n")
        clone = self.root.parent / "demo-src"
        (clone / ".git").mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, clone, True)
        write(self.root, "experiments/demo-col/collect.json", json.dumps({
            "repo": "x/y",
            "sibling": "demo-src",
            "sources": [{"path": "out.json", "commit": "a" * 40, "sha256": sha, "out": "results/out.json", "fn": "trim"}],
        }))
        with mock.patch.object(collect, "git_show", return_value=payload):
            code, _, _ = self.run_cli("collect", "demo-col", "--clone", str(clone))
            self.assertEqual(code, 0)
            write(self.root, "experiments/demo-col/collect.json", json.dumps({
                "repo": "x/y",
                "sibling": "demo-src",
                "sources": [{"path": "out.json", "commit": "a" * 40, "sha256": sha, "out": "../../instruments/x.json", "fn": "trim"}],
            }))
            code, _, err = self.run_cli("collect", "demo-col", "--clone", str(clone))
            self.assertEqual(code, 2)
            self.assertIn("COLLECT_BAD_SPEC", err)

        # 4. rnd catalog sync (valid run + hostile traversal name toward instruments/)
        def fake_gh(args):
            if args[:2] == ["api", "repos/x/y"]:
                return json.dumps({"license": {"spdx_id": "MIT"}})
            if args[1].startswith("repos/x/y/git/trees"):
                return json.dumps({"sha": "a" * 40, "tree": []})
            raise AssertionError(args)

        write(self.root, "catalogs/plain/source.json", json.dumps({"repo": "x/y", "match": "SKILL.md"}))
        with mock.patch.object(catalog, "_gh", side_effect=fake_gh):
            code, _, err = self.run_cli("catalog", "sync", "plain")
            self.assertEqual(code, 0, err)
            code, _, err = self.run_cli("catalog", "sync", "../instruments")
            self.assertEqual(code, 3)
            self.assertIn("CATALOG_UNKNOWN", err)

        # 5. rnd build with --db inside instruments/ is also refused.
        code, _, err = self.run_cli("--db", str(self.root / "instruments" / "bad.db"), "build")
        self.assertEqual(code, 2)
        self.assertIn("INSTRUMENTS_PROTECTED", err)

        self.assertEqual(self._instruments_snapshot(), before)

    def test_require_extra_succeeds_for_installed_module_and_fails_with_code_and_hint_when_missing(self):
        mod = cli.require_extra("json", "demo")
        self.assertIs(mod, json)

        def fake_cmd(_args):
            cli.require_extra("nonexistent_optional_pkg_xyz", "demo")
            return 0  # pragma: no cover

        with mock.patch.object(cli, "cmd_stats", side_effect=fake_cmd):
            code, _, err = self.run_cli("stats")
        self.assertEqual(code, 2)
        self.assertIn("MISSING_EXTRA", err)
        self.assertIn('pip install "mcptoolshop-rnd[demo]"', err)


if __name__ == "__main__":
    import unittest
    unittest.main()
