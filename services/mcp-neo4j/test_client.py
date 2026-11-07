"""Verification script for mcp-neo4j module logic."""

import unittest
from mcp_neo4j.server import CypherQueryResult, SchemaResult


class TestNeo4jMCPModels(unittest.TestCase):
    def test_schema_model(self):
        s = SchemaResult(labels=["NetworkElement", "Site"], relationship_types=["LOCATED_AT"], property_keys=["id", "name"])
        data = s.model_dump()
        self.assertEqual(data["labels"], ["NetworkElement", "Site"])
        self.assertEqual(data["relationship_types"], ["LOCATED_AT"])

    def test_cypher_result_model(self):
        r = CypherQueryResult(records=[{"id": "TRN-042"}], summary={"nodes_created": 0})
        data = r.model_dump()
        self.assertEqual(len(data["records"]), 1)
        self.assertEqual(data["records"][0]["id"], "TRN-042")


if __name__ == "__main__":
    unittest.main()
