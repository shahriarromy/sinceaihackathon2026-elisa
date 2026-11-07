"""Integration test executing the full Before vs After capture lifecycle for TRN-042."""

import unittest
from fastapi.testclient import TestClient
from agents.main import app
from agents.state_store import StateStore


class TestEndToEndCycle(unittest.TestCase):
    def setUp(self):
        StateStore().reset()
        self.client = TestClient(app)

    def test_lifecycle_before_and_after_capture(self):
        # 1. Before capture: Agent 1 analyzes TRN-042 incident
        before_resp = self.client.post("/agent1/report", json={
            "incident_id": "WO-2026-0312-007",
            "query": "TRN-042 SFP replaced, interface UP, optical OK, alarms cleared, traffic counters at zero",
        })
        self.assertEqual(before_resp.status_code, 200)
        before_data = before_resp.json()

        # Must report no known solution yet
        self.assertIsNone(before_data.get("known_solution"))
        self.assertIn("no known", " ".join(before_data.get("suggested_next_steps", [])).lower())

        # 2. Ingest: Agent 2 captures Teams and Email silent metadata
        ingest_resp = self.client.post("/agent2/ingest", json={
            "sources": ["teams", "email"],
            "limit": 5,
        })
        self.assertEqual(ingest_resp.status_code, 200)
        ingest_data = ingest_resp.json()
        self.assertGreater(len(ingest_data.get("assertions_created", [])), 0)

        # 3. After capture: Agent 1 analyzes TRN-042 incident again
        # We simulate the captured graph assertion or RAG context
        after_resp = self.client.post("/agent1/report", json={
            "incident_id": "WO-2026-0312-007",
            "query": "TRN-042 SFP replaced, interface UP, optical OK, alarms cleared, traffic counters at zero",
        })
        self.assertEqual(after_resp.status_code, 200)
        after_data = after_resp.json()

        # The solution is found in RAG or Graph
        solution = after_data.get("known_solution")
        self.assertIsNotNone(solution)
        self.assertIn("disable", solution.get("recommendation", "").lower())
        self.assertIn("enable", solution.get("recommendation", "").lower())

        # Verify suggested next steps propose interface toggle before hardware replacement
        steps = " ".join(after_data.get("suggested_next_steps", [])).lower()
        self.assertIn("disable", steps)
        self.assertIn("enable", steps)
        self.assertIn("counter", steps)


if __name__ == "__main__":
    unittest.main()
