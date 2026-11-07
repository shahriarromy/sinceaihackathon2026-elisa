"""Unit tests for agents FastAPI service endpoints."""

import unittest
from fastapi.testclient import TestClient
from agents.main import app


class TestAgentsApp(unittest.TestCase):
    def setUp(self):
        import agents.agent2.graph as a2g
        self._orig_key = a2g.LLM_API_KEY
        a2g.LLM_API_KEY = "your_llm_api_key_here"
        self.client = TestClient(app)

    def tearDown(self):
        import agents.agent2.graph as a2g
        a2g.LLM_API_KEY = self._orig_key

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("mcp_endpoints", data)
        self.assertIn("rag", data["mcp_endpoints"])
        self.assertIn("neo4j_ro", data["mcp_endpoints"])

    def test_agent1_report_endpoint(self):
        response = self.client.post("/agent1/report", json={"incident_id": "WO-2026-0312-007", "query": "TRN-042"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("summary", data)
        self.assertIn("suggested_next_steps", data)
        self.assertIn("timeline", data)

    def test_agent1_report_stream_endpoint(self):
        response = self.client.post("/agent1/report/stream", json={"incident_id": "WO-2026-0312-007"})
        self.assertEqual(response.status_code, 200)
        content = response.text
        self.assertIn("event: step", content)
        self.assertIn("event: report", content)
        self.assertIn("compose_report", content)

    def test_agent2_ingest_scaffold(self):
        from agents.state_store import StateStore
        StateStore().reset()

        # First call ingests items
        response = self.client.post("/agent2/ingest", json={"sources": ["teams", "email"], "limit": 2})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("assertions_created", data)
        self.assertGreater(len(data["assertions_created"]), 0)
        first_count = len(data["assertions_created"])

        # Second call is idempotent (items already processed)
        second_resp = self.client.post("/agent2/ingest", json={"sources": ["teams", "email"], "limit": 2})
        self.assertEqual(second_resp.status_code, 200)
        second_data = second_resp.json()
        self.assertEqual(len(second_data["assertions_created"]), 0)

    def test_agent2_targeted_incident_capture(self):
        # Target WO-2026-1107-003 with specific channel
        response = self.client.post(
            "/agent2/ingest",
            json={"sources": ["teams"], "incident_id": "WO-2026-1107-003"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("assertions_created", data)
        self.assertIn("incidents_touched", data)
        self.assertIn("WO-2026-1107-003", data["incidents_touched"])

    def test_list_and_get_incidents(self):
        # Verify listing 5 work orders from reference diagram
        res = self.client.get("/incidents")
        self.assertEqual(res.status_code, 200)
        items = res.json()
        self.assertEqual(len(items), 5)
        ids = [item["id"] for item in items]
        self.assertIn("WO-2026-1107-003", ids)
        self.assertIn("WO-2026-0312-007", ids)

        # Verify incident detail
        detail_res = self.client.get("/incidents/WO-2026-0312-007")
        self.assertEqual(detail_res.status_code, 200)
        detail = detail_res.json()
        self.assertEqual(detail["element_id"], "TRN-042")
        self.assertEqual(detail["model"], "TX-2000")
        self.assertTrue(len(detail["sequence"]) > 0)


if __name__ == "__main__":
    unittest.main()
