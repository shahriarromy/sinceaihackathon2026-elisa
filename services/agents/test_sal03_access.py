"""Test scenario for SAL-03 locked barrier and NOC keybox code (Step 7.1)."""

import unittest
from fastapi.testclient import TestClient
from agents.main import app
from agents.state_store import StateStore


class TestSAL03AccessScenario(unittest.TestCase):
    def setUp(self):
        StateStore().reset()
        self.client = TestClient(app)

    def test_sal03_access_knowledge_capture_and_reporting(self):
        # 1. Ingest email and SMS metadata
        ingest_res = self.client.post("/agent2/ingest", json={"sources": ["email", "sms"]})
        self.assertEqual(ingest_res.status_code, 200)
        data = ingest_res.json()
        self.assertTrue(len(data["assertions_created"]) > 0)

        # 2. Query Agent 1 for SAL-03 incident (WO-2026-0114-002: locked barrier on private road)
        report_res = self.client.post("/agent1/report", json={"incident_id": "WO-2026-0114-002"})
        self.assertEqual(report_res.status_code, 200)
        report = report_res.json()

        # 3. Verify access knowledge is reported with NOC keybox guidance (superseding shop key)
        self.assertIn("WO-2026-0114-002", report["summary"])
        self.assertIsNotNone(report["known_solution"])

        solution = report["known_solution"]
        # Verify the recommendation points to NOC keybox
        self.assertIn("keybox", solution["title"].lower())
        self.assertTrue(
            "noc" in solution["recommendation"].lower() or "keybox" in solution["recommendation"].lower()
        )
        self.assertIn("email/TH-E-003.txt", solution["source_ref"])

        # 4. Verify suggested next steps instruct calling NOC for keybox code before departure
        steps_str = " ".join(report["suggested_next_steps"]).lower()
        self.assertIn("keybox", steps_str)
        self.assertIn("noc", steps_str)


if __name__ == "__main__":
    unittest.main()
