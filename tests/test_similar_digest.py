"""Tests for rnd 1.3 Part B: `rnd similar` and `rnd digest` (read-only commands and claims_fts)."""

import json
import os
import sqlite3
import subprocess
from pathlib import Path
from unittest import mock

from mcptoolshop_rnd import model

from .test_cli import CliBase
from .test_rnd import ENTRY, write


class SimilarCommandTests(CliBase):
    def _seed_claims_library(self):
        id_s0 = model.make_claim_id("2026-01-02-sample", "Graphs replay with one call.")
        id_s1 = model.make_claim_id("2026-01-02-sample", "It helps decode more than diffusion.")
        write(
            self.root,
            "entries/2026/2026-01-05-newer-link.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-05-newer-link")
            .replace(
                "- [verified] Graphs replay with one call. (via: NVIDIA docs, 2026-01-02)",
                f"- [verified] [c-rep00001] CUDA graphs replay kernel launches in one call. "
                f"(via: bench, 2026-01-05) (supersedes: {id_s0})",
            )
            .replace(
                "- [unverified] It helps decode more than diffusion.",
                f"- [verified] [c-con00002] Diffusion and decode benefit equally from graphs. "
                f"(via: bench, 2026-01-05) (contradicts: {id_s1})",
            )
            .replace("date: 2026-01-02", "date: 2026-01-05"),
        )
        self.assertEqual(self.run_cli("reconcile", "2026-01-05-newer-link")[0], 0)
        return id_s0, id_s1

    def test_similar_ranks_other_entries_shows_superseded_disputed_clauses_and_never_writes(self):
        id_s0, id_s1 = self._seed_claims_library()
        draft = write(
            self.root,
            "entries/2026/2026-01-20-draft.md",
            "---\n"
            "id: 2026-01-20-draft\n"
            "title: Draft CUDA graph notes\n"
            "date: 2026-01-20\n"
            "kind: finding\n"
            "relevance: reference\n"
            "fields: [gpu-computing]\n"
            "---\n\n"
            "## Claims\n\n"
            "- [unverified] Replay kernel launches with CUDA graphs in one call.\n"
            "- [unverified] Diffusion and decode gains match.\n",
        )
        # Note: draft intentionally has no `## Sources` (check warning), and no `rnd.db` exists yet.
        db_file = self.root / "rnd.db"
        self.assertFalse(db_file.exists())

        code, out, err = self.run_cli("similar", "2026-01-20-draft", "--limit", "3")
        self.assertEqual(code, 0, err)
        self.assertFalse(db_file.exists(), "similar must never write rnd.db")
        self.assertIn(id_s0, out)
        self.assertIn("! replaced by c-rep00001 (2026-01-05-newer-link)", out)
        self.assertIn(id_s1, out)
        self.assertIn("! contradicted by c-con00002 (2026-01-05-newer-link)", out)
        self.assertIn("(supersedes:", out)
        self.assertIn("(contradicts:", out)
        self.assertIn("(supports:", out)
        self.assertIn("rnd reconcile 2026-01-20-draft", out)
        for c in json.loads(self.run_cli("similar", "2026-01-20-draft", "--json")[1])["claims"]:
            self.assertTrue(all(h["entry_id"] != "2026-01-20-draft" for h in c["hits"]))
            self.assertTrue(all(h["entry_id"] != "tool-x" for h in c["hits"]))

        # Build rnd.db and verify `claims_fts` is populated and used read-only without changing bytes.
        self.assertEqual(self.run_cli("build")[0], 0)
        self.assertTrue(db_file.is_file())
        db_before = db_file.read_bytes()
        draft_before = draft.read_bytes()

        code, json_out, err = self.run_cli("similar", str(draft), "--limit", "2", "--json")
        self.assertEqual(code, 0, err)
        parsed = json.loads(json_out)
        self.assertEqual(len(parsed["claims"][0]["hits"]), 2)
        self.assertIn("score", parsed["claims"][0]["hits"][0])
        self.assertEqual(db_file.read_bytes(), db_before)
        self.assertEqual(draft.read_bytes(), draft_before)

        # Unassigned claim hit reports `entry#ord`, and stale/corrupt rnd.db falls back to memory without writing.
        other_p = self.root / "entries/2026/2026-01-03-other.md"
        other_p.write_text(
            other_p.read_text(encoding="utf-8").replace(
                "## Sources",
                "- [unverified] Unique unassigned token xylophonebench.\n\n## Sources",
            ),
            encoding="utf-8",
        )
        db_file.write_bytes(b"corrupt")
        corrupt_before = db_file.read_bytes()
        q_unassigned = write(
            self.root,
            "entries/2026/2026-01-21-xylo.md",
            "---\nid: 2026-01-21-xylo\ntitle: X\ndate: 2026-01-21\nkind: finding\nrelevance: reference\n"
            "fields: [gpu-computing]\n---\n\n## Claims\n\n- [unverified] xylophonebench.\n",
        )
        code, out, err = self.run_cli("similar", "2026-01-21-xylo")
        self.assertEqual(code, 0, err)
        self.assertIn("2026-01-03-other#2", out)
        self.assertEqual(db_file.read_bytes(), corrupt_before)
        q_unassigned.unlink()

    def test_similar_handles_external_draft_empty_claims_and_errors(self):
        # Empty claims, stopword-only fallback query, and standalone file outside entries/.
        ext = self.root / "draft-outside.md"
        ext.write_text(
            "---\nid: draft-outside\ntitle: External\ndate: 2026-01-22\nkind: finding\nrelevance: reference\n"
            "fields: [gpu-computing]\n---\n\n## Claims\n\n"
            "- [unverified] is it on?\n"
            "- [unverified] ?\n",
            encoding="utf-8",
        )
        code, out, err = self.run_cli("similar", str(ext))
        self.assertEqual(code, 0, err)
        self.assertIn("draft-outside", out)

        empty_entry = write(
            self.root,
            "entries/2026/2026-01-22-empty.md",
            "---\nid: 2026-01-22-empty\ntitle: Empty\ndate: 2026-01-22\nkind: finding\nrelevance: reference\n"
            "fields: [gpu-computing]\n---\n\n## Summary\n\nNothing.\n",
        )
        code, out, err = self.run_cli("similar", "2026-01-22-empty")
        self.assertEqual(code, 0, err)
        self.assertIn("no claims in this entry", out)
        empty_entry.unlink()

        # Error cases: NOT_FOUND (exit 2), --limit 0 (USAGE, exit 2), UNREADABLE (exit 1).
        code, _, err = self.run_cli("similar", "missing-entry")
        self.assertEqual(code, 2)
        self.assertIn("NOT_FOUND", err)

        code, _, err = self.run_cli("similar", "2026-01-02-sample", "--limit", "0")
        self.assertEqual(code, 2)
        self.assertIn("USAGE", err)

        bad_in_entries = write(self.root, "entries/2026/2026-01-23-broken.md", "---\nunclosed: frontmatter\n")
        code, _, err = self.run_cli("similar", str(bad_in_entries))
        self.assertEqual(code, 1)
        self.assertIn("UNREADABLE", err)
        bad_in_entries.unlink()

        ext.write_text("---\nbroken\n", encoding="utf-8")
        code, _, err = self.run_cli("similar", str(ext))
        self.assertEqual(code, 1)
        self.assertIn("UNREADABLE", err)


class DigestCommandTests(CliBase):
    def _git(self, *args, commit_date=None):
        env = dict(os.environ)
        if commit_date:
            env["GIT_AUTHOR_DATE"] = commit_date
            env["GIT_COMMITTER_DATE"] = commit_date
        return subprocess.run(
            ["git", "-c", "user.name=tester", "-c", "user.email=tester@example.com", *args],
            cwd=self.root,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    def _setup_git_history(self):
        # Set up an initial commit at 2026-01-10 tagged v0.1.0 with assigned/unassigned claims & questions.
        write(
            self.root,
            "entries/2026/2026-01-02-sample.md",
            "---\n"
            "id: 2026-01-02-sample\n"
            "title: Sample entry\n"
            "date: 2026-01-02\n"
            "kind: finding\n"
            "relevance: watch\n"
            "fields: [gpu-computing]\n"
            "tags: [cuda]\n"
            "---\n\n"
            "## Summary\n\nInitial.\n\n"
            "## Claims\n\n"
            "- [verified] Graphs replay with one call. (via: NVIDIA docs, 2026-01-02)\n"
            "- [unverified] Unassigned claim that gets reworded.\n"
            "- [unverified] [c-keep0001] Claim with id before reword.\n\n"
            "## Sources\n\n- [primary] https://example.com — docs\n",
        )
        write(
            self.root,
            "questions/2026-01-10-q-answer.md",
            "---\nid: 2026-01-10-q-answer\ntitle: Question to answer?\ndate: 2026-01-10\nstatus: open\n"
            "fields: [gpu-computing]\ntags: []\nanswered_by: []\n---\n\n## Question\n\nQ1\n",
        )
        write(
            self.root,
            "questions/2026-01-10-q-park.md",
            "---\nid: 2026-01-10-q-park\ntitle: Question to park?\ndate: 2026-01-10\nstatus: open\n"
            "fields: [gpu-computing]\ntags: []\nanswered_by: []\n---\n\n## Question\n\nQ2\n",
        )
        self._git("init", "-q")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "initial", commit_date="2026-01-10T12:00:00+00:00")
        self._git("tag", "-a", "v0.1.0", "-m", "v0.1.0", commit_date="2026-01-10T12:00:00+00:00")

        # Second commit at 2026-01-15: new entry supersedes sample#0 & contradicts other#0,
        # rewords unassigned claim (must NOT be state change), rewords+changes state on c-keep0001,
        # answers q-answer, parks q-park, opens q-new.
        id_s0 = model.make_claim_id("2026-01-02-sample", "Graphs replay with one call.")
        id_o0 = model.make_claim_id("2026-01-03-other", "Graphs replay with one call.")
        write(
            self.root,
            "entries/2026/2026-01-15-followup.md",
            "---\nid: 2026-01-15-followup\ntitle: Followup findings\ndate: 2026-01-15\nkind: finding\n"
            "relevance: act\nfields: [gpu-computing]\ntags: [cuda]\n---\n\n"
            "## Summary\n\nFollowup.\n\n## Claims\n\n"
            f"- [verified] [c-new11111] Graph replay needs warm cache. (via: bench, 2026-01-15) (supersedes: {id_s0})\n"
            f"- [verified] [c-new22222] Contradicts other entry claim. (via: bench, 2026-01-15) (contradicts: {id_o0})\n\n"
            "## Sources\n\n- [rig] bench\n",
        )
        self.assertEqual(self.run_cli("reconcile", "2026-01-15-followup")[0], 0)
        sample_p = self.root / "entries/2026/2026-01-02-sample.md"
        sample_p.write_text(
            sample_p.read_text(encoding="utf-8")
            .replace(
                "- [unverified] Unassigned claim that gets reworded.",
                "- [verified] Reworded unassigned claim. (via: audit, 2026-01-15)",
            )
            .replace(
                "- [unverified] [c-keep0001] Claim with id before reword.",
                "- [verified] [c-keep0001] Claim with id after reword. (via: audit, 2026-01-15)",
            ),
            encoding="utf-8",
        )
        write(
            self.root,
            "questions/2026-01-10-q-answer.md",
            "---\nid: 2026-01-10-q-answer\ntitle: Question to answer?\ndate: 2026-01-10\nstatus: answered\n"
            "fields: [gpu-computing]\ntags: []\nanswered_by: [c-new11111]\n---\n\n## Question\n\nQ1\n",
        )
        write(
            self.root,
            "questions/2026-01-10-q-park.md",
            "---\nid: 2026-01-10-q-park\ntitle: Question to park?\ndate: 2026-01-10\nstatus: parked\n"
            "fields: [gpu-computing]\ntags: []\nanswered_by: []\n---\n\n## Question\n\nQ2\n",
        )
        write(
            self.root,
            "questions/2026-01-15-q-new.md",
            "---\nid: 2026-01-15-q-new\ntitle: Brand new question?\ndate: 2026-01-15\nstatus: open\n"
            "fields: [gpu-computing]\ntags: []\nanswered_by: []\n---\n\n## Question\n\nQ3\n",
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "second", commit_date="2026-01-15T14:00:00+00:00")
        return id_s0, id_o0

    def test_digest_since_git_ref_and_date_tracks_entries_claims_states_and_questions(self):
        id_s0, id_o0 = self._setup_git_history()

        for since_arg in ("v0.1.0", "2026-01-10"):
            code, out, err = self.run_cli("digest", "--since", since_arg, "--json")
            self.assertEqual(code, 0, err)
            rep = json.loads(out)
            self.assertEqual(rep["counts"], {
                "entries_added": 1,
                "claims_added": 3,
                "claims_state_changed": 3,
                "questions_opened": 1,
                "questions_answered": 1,
                "questions_parked": 1,
            })
            self.assertEqual([e["id"] for e in rep["entries_added"]], ["2026-01-15-followup"])
            added_texts = {c["text"] for c in rep["claims_added"]}
            self.assertIn("Reworded unassigned claim.", added_texts)
            self.assertIn("Graph replay needs warm cache.", added_texts)
            self.assertIn("Contradicts other entry claim.", added_texts)

            changes = {c["id"]: c for c in rep["claims_state_changed"]}
            self.assertEqual(set(changes), {id_s0, id_o0, "c-keep0001"})
            self.assertEqual((changes[id_s0]["old_state"], changes[id_s0]["new_state"]), ("verified", "superseded"))
            self.assertEqual(changes[id_s0]["replaced_by"], [{"id": "c-new11111", "entry_id": "2026-01-15-followup"}])
            self.assertEqual((changes[id_o0]["old_state"], changes[id_o0]["new_state"]), ("verified", "disputed"))
            self.assertEqual(changes[id_o0]["contradicted_by"], [{"id": "c-new22222", "entry_id": "2026-01-15-followup"}])
            self.assertEqual((changes["c-keep0001"]["old_state"], changes["c-keep0001"]["new_state"]), ("unverified", "verified"))

            self.assertEqual([q["id"] for q in rep["questions_opened"]], ["2026-01-15-q-new"])
            self.assertEqual(rep["questions_answered"][0]["id"], "2026-01-10-q-answer")
            self.assertEqual(rep["questions_answered"][0]["answered_by"], ["c-new11111"])
            self.assertEqual([q["id"] for q in rep["questions_parked"]], ["2026-01-10-q-park"])

        code, txt, err = self.run_cli("digest", "--since", "v0.1.0")
        self.assertEqual(code, 0, err)
        self.assertIn("verified -> superseded", txt)
        self.assertIn("replaced by c-new11111 (2026-01-15-followup)", txt)
        self.assertIn("verified -> disputed", txt)
        self.assertIn("contradicted by c-new22222 (2026-01-15-followup)", txt)
        self.assertIn("2026-01-10-q-answer -> c-new11111", txt)

    def test_digest_errors_on_unknown_ref_and_date_before_history_exit_2(self):
        self._setup_git_history()

        for since_arg in ("--since=no-such-ref", "--since=-bad", "--since="):
            code, _, err = self.run_cli("digest", since_arg)
            self.assertEqual(code, 2)
            self.assertIn("UNKNOWN_REF", err)

        code, _, err = self.run_cli("digest", "--since", "2020-01-01")
        self.assertEqual(code, 2)
        self.assertIn("BAD_SINCE", err)
        self.assertIn("2026-01-10", err)

        code, _, err = self.run_cli("digest", "--since", "2026-02-30")
        self.assertEqual(code, 2)
        self.assertIn("BAD_SINCE", err)

        with mock.patch("mcptoolshop_rnd.digest.subprocess.run", side_effect=OSError("missing git")):
            code, _, err = self.run_cli("digest", "--since", "v0.1.0")
        self.assertEqual(code, 3)
        self.assertIn("GIT_FAILED", err)

    def test_digest_leaves_working_tree_and_rnd_db_byte_identical(self):
        self._setup_git_history()
        self.assertEqual(self.run_cli("build")[0], 0)
        # Add an uncommitted edit AND an untracked note so we prove digest reads them without touching disk.
        write(
            self.root,
            "entries/2026/2026-01-16-uncommitted.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-16-uncommitted").replace("2026-01-02", "2026-01-16"),
        )
        db_path = self.root / "rnd.db"
        index_path = self.root / ".git" / "index"
        tracked_snapshot = {
            p.relative_to(self.root).as_posix(): p.read_bytes()
            for p in sorted(self.root.rglob("*"))
            if p.is_file() and ".git/" not in p.relative_to(self.root).as_posix()
        }
        db_bytes_before = db_path.read_bytes()
        index_bytes_before = index_path.read_bytes()
        git_status_before = self._git("status", "--porcelain").stdout

        code, out, err = self.run_cli("digest", "--since", "v0.1.0", "--json")
        self.assertEqual(code, 0, err)
        rep = json.loads(out)
        self.assertEqual(rep["counts"]["entries_added"], 2)

        tracked_after = {
            p.relative_to(self.root).as_posix(): p.read_bytes()
            for p in sorted(self.root.rglob("*"))
            if p.is_file() and ".git/" not in p.relative_to(self.root).as_posix()
        }
        self.assertEqual(tracked_after, tracked_snapshot)
        self.assertEqual(db_path.read_bytes(), db_bytes_before)
        self.assertEqual(index_path.read_bytes(), index_bytes_before)
        self.assertEqual(self._git("status", "--porcelain").stdout, git_status_before)


if __name__ == "__main__":
    import unittest
    unittest.main()
