"""Unit tests for Agent 1 (Incident Analyst) LangGraph execution."""

import unittest
from agents.agent1.graph import build_agent1_graph


class TestAgent1Graph(unittest.TestCase):
    def setUp(self):
        from agents.state_store import StateStore
        StateStore().reset()

    def test_agent1_graph_structure(self):
        graph = build_agent1_graph()
        initial_state = {
            "incident_id": "INC-TEST-001",
            "query": "Generic unknown fiber cut",
            "incident_data": {},
            "rag_results": [],
            "graph_assertions": [],
            "final_report": {},
            "step_events": [],
        }

        result = graph.invoke(initial_state)

        events = result.get("step_events", [])
        self.assertTrue(any("fetch_incident_context" in e for e in events))
        self.assertTrue(any("search_rag" in e for e in events))
        self.assertTrue(any("find_related_assertions" in e for e in events))
        self.assertTrue(any("compose_report" in e for e in events))

        report = result.get("final_report", {})
        self.assertIn("summary", report)
        self.assertIn("suggested_next_steps", report)

    def test_agent1_no_known_solution_initially(self):
        graph = build_agent1_graph()
        # Query with TRN-042 before any silent metadata is captured
        state = {
            "incident_id": "WO-2026-0312-007",
            "query": "TRN-042 1/1/2 interface UP alarms cleared traffic counters zero",
            "incident_data": {},
            "rag_results": [],
            "graph_assertions": [],
            "final_report": {},
            "step_events": [],
        }

        result = graph.invoke(state)
        report = result.get("final_report", {})
        # Must report no known solution without fabricating
        self.assertIsNone(report.get("known_solution"))
        self.assertIn("no known", " ".join(report.get("suggested_next_steps", [])).lower())

    def test_agent1_proposes_workaround_when_assertion_present(self):
        graph = build_agent1_graph()
        # Query when the captured ContextAssertion exists in graph
        state = {
            "incident_id": "WO-2026-0312-007",
            "query": "TRN-042 1/1/2 interface UP alarms cleared traffic counters zero",
            "incident_data": {},
            "rag_results": [],
            "graph_assertions": [{
                "id": "CA-0001",
                "title": "TX-2000: forwarding state stuck after SFP replacement",
                "text": "Disable the interface, wait ~30 s, enable it again.",
                "recommendation": "Check that traffic counters increase; if at zero, disable the interface, wait ~30 s, enable it again.",
                "confidence": 0.9,
                "source_ref": "teams/TH-T-001.json",
            }],
            "final_report": {},
            "step_events": [],
        }

        result = graph.invoke(state)
        report = result.get("final_report", {})
        self.assertIsNotNone(report.get("known_solution"))
        steps = " ".join(report.get("suggested_next_steps", []))
        self.assertIn("disable", steps.lower())
        self.assertIn("enable", steps.lower())


if __name__ == "__main__":
    unittest.main()
