"""The licence registry stays well formed: every entry can be followed back to its proof."""

import json
import re
import unittest
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[1] / "licences" / "registry.json"
USES = {"assets", "training", "evaluation", "code"}
VERDICTS = {"proven", "conditions", "barred", "not_proven", "n/a"}
REQUIRED = ("id", "owner", "kind", "covers", "url", "page_date", "read_date", "clauses", "uses")


class LicenceRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.entries = cls.reg["entries"]

    def test_ids_unique(self):
        ids = [e["id"] for e in self.entries]
        self.assertEqual(len(ids), len(set(ids)))

    def test_required_fields(self):
        for e in self.entries:
            for k in REQUIRED:
                self.assertIn(k, e, f"{e.get('id')}: missing {k}")
            self.assertTrue(e["url"].startswith("https://"), e["id"])
            self.assertRegex(e["read_date"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertTrue(e["covers"], e["id"])

    def test_uses_and_verdicts(self):
        for e in self.entries:
            self.assertEqual(set(e["uses"]), USES, e["id"])
            for use, v in e["uses"].items():
                self.assertIn(v, VERDICTS, f"{e['id']}.{use}")

    def test_a_grant_rests_on_a_clause(self):
        # proven or conditions needs quoted text to rest on; only an entry that grants nothing may have none
        for e in self.entries:
            grants = [u for u, v in e["uses"].items() if v in ("proven", "conditions")]
            if grants:
                # a grant rests on a quoted clause, or on a documented search that found no restriction (the rule as
                # reworded on 2026-10-16)
                self.assertTrue(e["clauses"] or e.get("restriction_search"), f"{e['id']}: {grants} with no clause or search")

    def test_conditions_are_listed(self):
        for e in self.entries:
            if "conditions" in e["uses"].values():
                self.assertTrue(e.get("conditions"), f"{e['id']}: a 'conditions' verdict lists none")

    def test_snapshots_hashed(self):
        for e in self.entries:
            if "snapshot_sha256" in e:
                self.assertRegex(e["snapshot_sha256"], r"^[0-9a-f]{64}$", e["id"])

    def test_clauses_are_short_quotes(self):
        for e in self.entries:
            for c in e["clauses"]:
                self.assertLessEqual(len(re.findall(r"\S+", c)), 45, f"{e['id']}: quote longer than 45 words")


if __name__ == "__main__":
    unittest.main()
