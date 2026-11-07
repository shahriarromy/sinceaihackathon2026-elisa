"""End-to-end test for Agent 2 capturing TRN-042 silent metadata."""

import unittest
from fastapi.testclient import TestClient
from agents.main import app
from agents.state_store import StateStore


class TestTRN042CaptureE2E(unittest.TestCase):
    def setUp(self):
        StateStore().reset()
        self.client = TestClient(app)

    def test_trn042_knowledge_capture(self):
        # Trigger ingestion for teams and email channels containing TRN-042 discussions
        response = self.client.post("/agent2/ingest", json={"sources": ["teams", "email"], "limit": 5})
        self.assertEqual(response.status_code, 200)
        data = response.json()

        assertions = data.get("assertions_created", [])
        self.assertGreater(len(assertions), 0)

        # Find the TRN-042 / TX-2000 forwarding state assertion
        trn_ca = None
        for a in assertions:
            entities = a.get("entities", [])
            text = a.get("text", "")
            if "TRN-042" in entities or "TX-2000" in entities or "TRN-042" in text:
                trn_ca = a
                break

        self.assertIsNotNone(trn_ca, "Expected TRN-042 assertion to be captured by Agent 2")
        self.assertEqual(trn_ca["kind"], "troubleshooting_knowledge")
        self.assertIn("disable", trn_ca["text"].lower())
        self.assertIn("enable", trn_ca["text"].lower())

        # Verify incident WO-2026-0312-007 was touched
        incidents = data.get("incidents_touched", [])
        self.assertIn("WO-2026-0312-007", incidents)

        # Verify RAG documents were generated
        rag_ids = data.get("rag_ids_added", [])
        self.assertGreater(len(rag_ids), 0)


if __name__ == "__main__":
    unittest.main()
