"""Unit tests for Agent 2 (Knowledge Capturer) graph execution."""

import unittest
from agents.agent2.graph import build_agent2_graph
from agents.state_store import StateStore


class TestAgent2Graph(unittest.TestCase):
    def setUp(self):
        # Reset state store for clean test
        self.store = StateStore()
        self.store.reset()

    def test_agent2_graph_flow(self):
        graph = build_agent2_graph()
        initial_state = {
            "sources": ["teams", "email"],
            "limit": 2,
            "unprocessed_items": [],
            "extracted_assertions": [],
            "created_assertions": [],
            "incidents_touched": [],
            "rag_ids_added": [],
            "step_events": [],
        }

        result = graph.invoke(initial_state)

        # Check step events flowed through all 5 nodes
        events = result.get("step_events", [])
        self.assertTrue(any("fetch_latest_messages" in e for e in events))
        self.assertTrue(any("extract_context" in e for e in events))
        self.assertTrue(any("link_entities" in e for e in events))
        self.assertTrue(any("write_graph" in e for e in events))
        self.assertTrue(any("add_to_rag" in e for e in events))

        # Check extracted assertions
        extracted = result.get("extracted_assertions", [])
        self.assertGreater(len(extracted), 0)
        trn_assertion = next((a for a in extracted if "TX-2000" in a["title"] or "TRN-042" in str(a.get("entity_mentions", []))), None)
        self.assertIsNotNone(trn_assertion)
        self.assertIn("disable", trn_assertion["recommended_action"].lower())


if __name__ == "__main__":
    unittest.main()
