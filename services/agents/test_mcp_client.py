"""Unit tests for MultiServerMCPClient connection configurations and tool partition."""

import unittest
from agents.mcp_client import create_mcp_connections, get_mcp_client


class TestMCPClientConfig(unittest.TestCase):
    def test_create_mcp_connections(self):
        conns = create_mcp_connections()
        expected = ["rag", "teams", "email", "sms", "neo4j_ro", "neo4j_rw"]
        for exp in expected:
            self.assertIn(exp, conns)
            self.assertEqual(conns[exp]["transport"], "sse")
            self.assertTrue(conns[exp]["url"].startswith("http"))

    def test_get_mcp_client(self):
        client = get_mcp_client()
        self.assertIsNotNone(client)
        self.assertIn("rag", client.connections)
        self.assertIn("neo4j_ro", client.connections)


if __name__ == "__main__":
    unittest.main()
