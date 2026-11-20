"""Tests for rnd 1.3 Part B: `rnd similar` and `rnd digest` (read-only commands and claims_fts)."""

import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mcptoolshop_rnd import model

from .test_cli import CliBase
from .test_rnd import ENTRY, write


class SimilarCommandTests(CliBase):
    def _git(self, *args):
        return subprocess.run(
            ["git", "-c", "user.name=tester", "-c", "user.email=tester@example.com", *args],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )

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

        # Unlinked [disputed] claim so Review #324 B5 prints "! contradicted by unlinked".
        write(
            self.root,
            "entries/2026/2026-01-06-disputed-src.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-06-disputed-src")
            .replace("2026-01-02", "2026-01-06")
            .replace(
                "- [unverified] It helps decode more than diffusion.",
                "- [disputed] [c-srcdis1] Disputedsource gainz diverge across decode batch sizes.",
            ),
        )

        # Three entries on the same date whose entry ids sort REVERSE of their true BM25 rank
        # (a-low < b-mid < c-top lexicographically), proving ranking is genuinely BM25 descending (-bm25).
        rank_specs = [
            ("2026-01-04-a-low", "nvgraphlaunch lowers jitter slightly when queue depth stays short."),
            ("2026-01-04-b-mid", "nvgraphlaunch streamcapture lowers jitter across short queues."),
            ("2026-01-04-c-top", "nvgraphlaunch streamcapture warmupbatch tilekernel lowers jitter cleanly."),
        ]
        for eid, claim_text in rank_specs:
            write(
                self.root,
                f"entries/2026/{eid}.md",
                ENTRY.replace("2026-01-02-sample", eid)
                .replace("date: 2026-01-02", "date: 2026-01-04")
                .replace("- [verified] Graphs replay with one call. (via: NVIDIA docs, 2026-01-02)\n", "")
                .replace("- [unverified] It helps decode more than diffusion.", f"- [unverified] {claim_text}"),
            )
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
            "- [unverified] nvgraphlaunch streamcapture warmupbatch tilekernel replay.\n"
            "- [unverified] Replay kernel launches with CUDA graphs in one call.\n"
            "- [unverified] It helps decode more than diffusion.\n"
            "- [unverified] Disputedsource gainz diverge across decode batches.\n",
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
        self.assertIn("! contradicted by unlinked", out)
        self.assertIn("for example, for the top hit above", out)
        self.assertIn("(supersedes:", out)
        self.assertIn("(contradicts:", out)
        self.assertIn("(supports:", out)
        self.assertIn("rnd reconcile 2026-01-20-draft", out)

        code_j, out_j, err_j = self.run_cli("similar", "2026-01-20-draft", "--limit", "3", "--json")
        self.assertEqual(code_j, 0, err_j)
        rep = json.loads(out_j)
        for c in rep["claims"]:
            self.assertTrue(all(h["entry_id"] != "2026-01-20-draft" for h in c["hits"]))
            self.assertTrue(all(h["entry_id"] != "tool-x" for h in c["hits"]))

        # Item 5: explicitly assert ranked order and strictly decreasing positive scores on >= 3 hits.
        rank_hits = rep["claims"][0]["hits"]
        self.assertEqual(
            [h["entry_id"] for h in rank_hits],
            ["2026-01-04-c-top", "2026-01-04-b-mid", "2026-01-04-a-low"],
        )
        scores = [h["score"] for h in rank_hits]
        self.assertGreater(scores[0], scores[1])
        self.assertGreater(scores[1], scores[2])
        self.assertGreater(scores[2], 0.0)
        self.assertLess(out.index("2026-01-04-c-top"), out.index("2026-01-04-b-mid"))
        self.assertLess(out.index("2026-01-04-b-mid"), out.index("2026-01-04-a-low"))

        # Initialize git + build rnd.db and prove Item 11: `?mode=ro` index path is used and refs/HEAD/files stay identical.
        self._git("init", "-q")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "seed")
        self.assertEqual(self.run_cli("build")[0], 0)
        self.assertTrue(db_file.is_file())
        db_before = db_file.read_bytes()
        draft_before = draft.read_bytes()
        head_bytes_before = (self.root / ".git" / "HEAD").read_bytes()
        rev_head_before = self._git("rev-parse", "HEAD").stdout
        refs_before = self._git("for-each-ref", "--format=%(refname) %(objectname)").stdout
        index_before = (self.root / ".git" / "index").read_bytes()

        with mock.patch("mcptoolshop_rnd.similar.sqlite3.connect", wraps=sqlite3.connect) as connect_spy:
            code, json_out, err = self.run_cli("similar", str(draft), "--limit", "3", "--json")
        self.assertEqual(code, 0, err)
        self.assertEqual(connect_spy.call_count, 1)
        conn_args, conn_kwargs = connect_spy.call_args
        self.assertIn("?mode=ro", str(conn_args[0]))
        self.assertTrue(conn_kwargs.get("uri"))
        self.assertNotIn(":memory:", str(conn_args[0]))

        parsed = json.loads(json_out)
        self.assertEqual(
            [h["entry_id"] for h in parsed["claims"][0]["hits"]],
            ["2026-01-04-c-top", "2026-01-04-b-mid", "2026-01-04-a-low"],
        )
        self.assertEqual(db_file.read_bytes(), db_before)
        self.assertEqual(draft.read_bytes(), draft_before)
        self.assertEqual((self.root / ".git" / "HEAD").read_bytes(), head_bytes_before)
        self.assertEqual(self._git("rev-parse", "HEAD").stdout, rev_head_before)
        self.assertEqual(self._git("for-each-ref", "--format=%(refname) %(objectname)").stdout, refs_before)
        self.assertEqual((self.root / ".git" / "index").read_bytes(), index_before)

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

    def test_similar_includes_later_dated_entries_and_matches_unicode_words(self):
        # Item 6: no "older" in --help or output; later-dated entries are included as "claims in other entries".
        from mcptoolshop_rnd import cli as rnd_cli
        parser = rnd_cli.build_parser()
        sub_actions = [a for a in parser._actions if getattr(a, "choices", None) and "similar" in a.choices]
        sim_parser = sub_actions[0].choices["similar"]
        self.assertNotIn("older", sim_parser.format_help().lower())
        self.assertIn("claims in other entries", sim_parser.description.lower())
        similar_line = next(ln for ln in parser.format_help().splitlines() if ln.lstrip().startswith("similar "))
        self.assertNotIn("older", similar_line.lower())

        early = write(
            self.root,
            "entries/2026/2026-01-10-early.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-10-early")
            .replace("2026-01-02", "2026-01-10")
            .replace(
                "- [unverified] It helps decode more than diffusion.",
                "- [unverified] Tensorcoregraph latermatch survives batching.",
            ),
        )
        write(
            self.root,
            "entries/2026/2026-02-15-later.md",
            ENTRY.replace("2026-01-02-sample", "2026-02-15-later")
            .replace("2026-01-02", "2026-02-15")
            .replace(
                "- [unverified] It helps decode more than diffusion.",
                "- [unverified] Tensorcoregraph latermatch also holds on February hardware.",
            ),
        )
        code, out, err = self.run_cli("similar", early.stem)
        self.assertEqual(code, 0, err)
        self.assertIn("2026-02-15-later", out)
        self.assertNotIn("older", out.lower())

        # Item 8: accented Latin words (naïve résumé) and CJK tokens (音声合成) are kept whole.
        write(
            self.root,
            "entries/2026/2026-01-12-accented.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-12-accented")
            .replace("date: 2026-01-02", "date: 2026-01-12")
            .replace("- [verified] Graphs replay with one call. (via: NVIDIA docs, 2026-01-02)\n", "")
            .replace(
                "- [unverified] It helps decode more than diffusion.",
                "- [unverified] Diacritics in naïve résumé survive FTS indexing cleanly.",
            ),
        )
        write(
            self.root,
            "entries/2026/2026-01-12-cjk.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-12-cjk")
            .replace("date: 2026-01-02", "date: 2026-01-12")
            .replace("- [verified] Graphs replay with one call. (via: NVIDIA docs, 2026-01-02)\n", "")
            .replace(
                "- [unverified] It helps decode more than diffusion.",
                "- [unverified] Streaming 音声合成 lowers first-packet latency.",
            ),
        )
        probe_uni = write(
            self.root,
            "entries/2026/2026-01-25-unicode-query.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-25-unicode-query")
            .replace("date: 2026-01-02", "date: 2026-01-25")
            .replace(
                "- [verified] Graphs replay with one call. (via: NVIDIA docs, 2026-01-02)",
                "- [unverified] naïve résumé",
            )
            .replace(
                "- [unverified] It helps decode more than diffusion.",
                "- [unverified] 音声合成",
            ),
        )
        code, json_out, err = self.run_cli("similar", probe_uni.stem, "--json")
        self.assertEqual(code, 0, err)
        uni_rep = json.loads(json_out)
        self.assertEqual(uni_rep["claims"][0]["query"], '"naïve" OR "résumé"')
        self.assertEqual(uni_rep["claims"][0]["hits"][0]["entry_id"], "2026-01-12-accented")
        self.assertEqual(uni_rep["claims"][1]["query"], '"音声合成"')
        self.assertEqual(uni_rep["claims"][1]["hits"][0]["entry_id"], "2026-01-12-cjk")

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
    def _git(self, *args, commit_date=None, cwd=None):
        env = dict(os.environ)
        if commit_date:
            env["GIT_AUTHOR_DATE"] = commit_date
            env["GIT_COMMITTER_DATE"] = commit_date
        return subprocess.run(
            ["git", "-c", "user.name=tester", "-c", "user.email=tester@example.com", *args],
            cwd=cwd or self.root,
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
        # rewords unassigned claim (must NOT be state change; appears as 1 removed + 1 added),
        # rewords+changes state on c-keep0001, answers q-answer, parks q-park, opens q-new.
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
                "claims_removed": 1,
                "claims_state_changed": 3,
                "questions_opened": 1,
                "questions_answered": 1,
                "questions_parked": 1,
            })
            for k, v in rep["counts"].items():
                self.assertEqual(v, len(rep[k]))
            self.assertEqual([e["id"] for e in rep["entries_added"]], ["2026-01-15-followup"])
            added_texts = {c["text"] for c in rep["claims_added"]}
            self.assertIn("Reworded unassigned claim.", added_texts)
            self.assertIn("Graph replay needs warm cache.", added_texts)
            self.assertIn("Contradicts other entry claim.", added_texts)
            self.assertEqual([c["text"] for c in rep["claims_removed"]], ["Unassigned claim that gets reworded."])

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
        self.assertIn("1 claims removed", txt)
        self.assertIn("Claims removed (1)", txt)
        self.assertIn("Unassigned claim that gets reworded.", txt)
        self.assertIn("verified -> superseded", txt)
        self.assertIn("replaced by c-new11111 (2026-01-15-followup)", txt)
        self.assertIn("verified -> disputed", txt)
        self.assertIn("contradicted by c-new22222 (2026-01-15-followup)", txt)
        self.assertIn("2026-01-10-q-answer -> c-new11111", txt)

    def test_digest_reworded_unassigned_claim_with_state_change_is_removed_and_added_only(self):
        bad_utf8 = self.root / "entries/2026/2026-01-01-bad-utf8.md"
        bad_utf8.write_bytes(b"\xff\xfe")
        self._git("init", "-q")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "base", commit_date="2026-01-10T12:00:00+00:00")
        bad_utf8.unlink()
        other_p = self.root / "entries/2026/2026-01-03-other.md"
        other_p.write_text(
            other_p.read_text(encoding="utf-8").replace(
                "- [unverified] It helps decode more than diffusion.",
                "- [wrong] Reworded unassigned statement after recheck. (via: audit, 2026-01-15)",
            ),
            encoding="utf-8",
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "reword", commit_date="2026-01-15T12:00:00+00:00")

        code, out, err = self.run_cli("digest", "--since", "HEAD~1", "--json")
        self.assertEqual(code, 0, err)
        rep = json.loads(out)
        self.assertEqual(rep["counts"], {
            "entries_added": 0,
            "claims_added": 1,
            "claims_removed": 1,
            "claims_state_changed": 0,
            "questions_opened": 0,
            "questions_answered": 0,
            "questions_parked": 0,
        })
        for k, v in rep["counts"].items():
            self.assertEqual(v, len(rep[k]))
        self.assertEqual(rep["claims_removed"][0]["state"], "unverified")
        self.assertEqual(rep["claims_removed"][0]["text"], "It helps decode more than diffusion.")
        self.assertEqual(rep["claims_added"][0]["state"], "wrong")
        self.assertEqual(rep["claims_added"][0]["text"], "Reworded unassigned statement after recheck.")

    def test_digest_since_date_follows_first_parent_not_merged_side_branch(self):
        self._git("init", "-q")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "c0", commit_date="2026-01-10T12:00:00+00:00")
        main_branch = self._git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()

        # Side branch forked from C0 with a LATER commit timestamp on 2026-01-19.
        self._git("checkout", "-q", "-b", "side")
        write(
            self.root,
            "entries/2026/2026-01-19-side-entry.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-19-side-entry").replace("2026-01-02", "2026-01-19"),
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "side-s1", commit_date="2026-01-19T18:00:00+00:00")
        s1_sha = self._git("rev-parse", "HEAD").stdout.strip()

        # First-parent commit M1 on main with an EARLIER timestamp on 2026-01-19, then merge side later.
        self._git("checkout", "-q", main_branch)
        write(
            self.root,
            "entries/2026/2026-01-19-main-entry.md",
            ENTRY.replace("2026-01-02-sample", "2026-01-19-main-entry").replace("2026-01-02", "2026-01-19"),
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "main-m1", commit_date="2026-01-19T10:00:00+00:00")
        m1_sha = self._git("rev-parse", "HEAD").stdout.strip()

        self._git("merge", "--no-ff", "-q", "side", "-m", "merge side", commit_date="2026-01-20T12:00:00+00:00")

        code, out, err = self.run_cli("digest", "--since", "2026-01-19", "--json")
        self.assertEqual(code, 0, err)
        rep = json.loads(out)
        self.assertEqual(rep["since_commit"], m1_sha)
        self.assertNotEqual(rep["since_commit"], s1_sha)
        self.assertEqual([e["id"] for e in rep["entries_added"]], ["2026-01-19-side-entry"])

    def test_digest_outside_git_repo_and_shallow_or_tagless_clones(self):
        self._setup_git_history()

        # 1. Non-git directory: both ref and date must give GIT_FAILED (exit 3).
        non_git = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, non_git, True)
        shutil.copytree(self.root / "entries", non_git / "entries")
        shutil.copytree(self.root / "instruments", non_git / "instruments")
        with mock.patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": str(non_git.parent)}):
            for since_arg in ("v0.1.0", "2026-01-10"):
                code, _, err = self.run_cli("--library", str(non_git), "digest", "--since", since_arg)
                self.assertEqual(code, 3, (since_arg, err))
                self.assertIn("GIT_FAILED", err)
                self.assertIn("not a git repository", err)

        # 2. Shallow clone: missing tag/date both give shallow --unshallow hint.
        parent_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, parent_dir, True)
        shallow_dir = parent_dir / "shallow"
        self._git("clone", "-q", "--depth", "1", "--no-tags", self.root.as_uri(), str(shallow_dir))

        code, _, err = self.run_cli("--library", str(shallow_dir), "digest", "--since", "v0.1.0")
        self.assertEqual(code, 2, err)
        self.assertIn("UNKNOWN_REF", err)
        self.assertIn("--unshallow", err)

        code, _, err = self.run_cli("--library", str(shallow_dir), "digest", "--since", "2026-01-10")
        self.assertEqual(code, 2, err)
        self.assertIn("BAD_SINCE", err)
        self.assertIn("--unshallow", err)

        # 3. Full clone with no tags: missing ref gives git fetch --tags hint.
        notags_dir = parent_dir / "notags"
        self._git("clone", "-q", "--no-tags", self.root.as_uri(), str(notags_dir))
        code, _, err = self.run_cli("--library", str(notags_dir), "digest", "--since", "v0.1.0")
        self.assertEqual(code, 2, err)
        self.assertIn("UNKNOWN_REF", err)
        self.assertIn("git fetch --tags", err)

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
        head_path = self.root / ".git" / "HEAD"
        tracked_snapshot = {
            p.relative_to(self.root).as_posix(): p.read_bytes()
            for p in sorted(self.root.rglob("*"))
            if p.is_file() and ".git/" not in p.relative_to(self.root).as_posix()
        }
        db_bytes_before = db_path.read_bytes()
        index_bytes_before = index_path.read_bytes()
        head_bytes_before = head_path.read_bytes()
        refs_before = self._git("for-each-ref", "--format=%(refname) %(objectname)").stdout
        git_status_before = self._git("status", "--porcelain").stdout

        empty_tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, empty_tmp, True)
        with mock.patch.dict(os.environ, {"TMP": str(empty_tmp), "TEMP": str(empty_tmp), "TMPDIR": str(empty_tmp)}):
            code, out, err = self.run_cli("digest", "--since", "v0.1.0", "--json")
        self.assertEqual(code, 0, err)
        rep = json.loads(out)
        self.assertEqual(rep["counts"]["entries_added"], 2)
        self.assertEqual(list(empty_tmp.iterdir()), [], "digest must parse in memory and write no temp files")

        tracked_after = {
            p.relative_to(self.root).as_posix(): p.read_bytes()
            for p in sorted(self.root.rglob("*"))
            if p.is_file() and ".git/" not in p.relative_to(self.root).as_posix()
        }
        self.assertEqual(tracked_after, tracked_snapshot)
        self.assertEqual(db_path.read_bytes(), db_bytes_before)
        self.assertEqual(index_path.read_bytes(), index_bytes_before)
        self.assertEqual(head_path.read_bytes(), head_bytes_before)
        self.assertEqual(self._git("for-each-ref", "--format=%(refname) %(objectname)").stdout, refs_before)
        self.assertEqual(self._git("status", "--porcelain").stdout, git_status_before)


if __name__ == "__main__":
    unittest.main()
