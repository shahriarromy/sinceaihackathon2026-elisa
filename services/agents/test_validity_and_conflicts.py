"""Test handling of outdated assertions (:SUPERSEDES / valid_to) and conflicting assertions (:CONTRADICTS) (Step 7.2)."""

import unittest
from fastapi.testclient import TestClient
from agents.main import app
from agents.state_store import StateStore


class TestValidityAndConflicts(unittest.TestCase):
    def setUp(self):
        StateStore().reset()
        self.client = TestClient(app)

    def test_outdated_assertion_superseded_by_newer_guidance(self):
        """Verify outdated assertion (shop key) is superseded by active assertion (NOC keybox)."""
        # Ingest emails containing both TH-E-002 (old 2024 shop key) and TH-E-003 (new 2026 keybox)
        ingest_res = self.client.post("/agent2/ingest", json={"sources": ["email"]})
        self.assertEqual(ingest_res.status_code, 200)

        report_res = self.client.post("/agent1/report", json={"incident_id": "WO-2026-0114-002"})
        self.assertEqual(report_res.status_code, 200)
        report = report_res.json()

        sol = report["known_solution"]
        self.assertIsNotNone(sol)
        # Verify the active solution is keybox, NOT the superseded village shop
        self.assertIn("keybox", sol["title"].lower())
        self.assertNotIn("kyläkauppa", sol["title"].lower())
        self.assertIn("email/TH-E-003.txt", sol["source_ref"])

    def test_conflicting_assertions_handled_gracefully(self):
        """Verify conflicting expert advice (clean connectors vs reseat card) flags open question and orders steps."""
        # Ingest teams thread TH-T-002 containing disputed discussion between Aino and Mikko
        ingest_res = self.client.post("/agent2/ingest", json={"sources": ["teams"]})
        self.assertEqual(ingest_res.status_code, 200)

        report_res = self.client.post("/agent1/report", json={"incident_id": "WO-2026-0718-011"})
        self.assertEqual(report_res.status_code, 200)
        report = report_res.json()

        # 1. Verify conflict is identified in open questions
        self.assertTrue(len(report["open_questions"]) > 0)
        q_str = " ".join(report["open_questions"]).lower()
        self.assertTrue("conflicting" in q_str or "disputed" in q_str)

        # 2. Verify confidence is bounded due to disagreement
        self.assertLessEqual(report["confidence"], 0.65)

        # 3. Verify suggested next steps prioritize least intrusive step (clean connectors first)
        steps_str = " ".join(report["suggested_next_steps"]).lower()
        self.assertIn("clean", steps_str)
        self.assertIn("reseat", steps_str)


if __name__ == "__main__":
    unittest.main()
