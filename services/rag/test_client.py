"""Unit test for rag-mcp tools and seed ingestion."""

import os
import unittest
from rag.server import rag_add, rag_search, rag_list_sources, ingest_seed_data, get_collection


class TestRAGMCP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ingest local seed data
        ingest_seed_data()

    def test_rag_list_sources(self):
        sources = rag_list_sources()
        self.assertGreater(sources["total_documents"], 0)
        self.assertGreater(len(sources["sources"]), 0)

    def test_rag_search_trn042(self):
        results = rag_search(query="TRN-042 traffic counters zero interface disable enable", entity_id="TRN-042", k=3)
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertIn("TRN-042", top["text"])
        self.assertIn("metadata", top)
        self.assertIn(top["metadata"]["source_type"], ["teams", "email"])

    def test_rag_search_access(self):
        results = rag_search(query="Hirvasvaara SAL-03 locked barrier key", entity_id="SAL-03", k=3)
        self.assertGreater(len(results), 0)
        found_barrier = any("barrier" in r["text"].lower() for r in results)
        self.assertTrue(found_barrier)

    def test_rag_add_idempotency(self):
        meta = {
            "source_type": "teams",
            "source_ref": "teams/test_custom.json",
            "author": "Tester",
            "timestamp": "2026-11-07T12:00:00+02:00",
            "entity_ids": "TEST-01",
            "incident_id": "INC-01",
            "kind": "troubleshooting_knowledge",
        }
        res1 = rag_add("Test knowledge text", meta)
        res2 = rag_add("Test knowledge text", meta)
        self.assertEqual(res1["id"], res2["id"])


if __name__ == "__main__":
    unittest.main()
