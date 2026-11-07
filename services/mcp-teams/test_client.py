"""Unit test for mcp-teams tools against local dummy data."""

import unittest
from mcp_teams.server import list_conversations, get_conversation, get_latest_conversations


class TestMcpTeams(unittest.TestCase):
    def test_list_conversations(self):
        items = list_conversations()
        self.assertGreater(len(items), 0)
        first = items[0]
        self.assertIn("id", first)
        self.assertIn("subject", first)
        self.assertEqual(first["source_type"], "teams")

    def test_get_conversation(self):
        conv = get_conversation("TH-T-001")
        self.assertEqual(conv["id"], "TH-T-001")
        self.assertIn("TRN-042", conv["subject"])
        self.assertGreater(len(conv["messages"]), 0)

    def test_get_latest_conversations(self):
        latest = get_latest_conversations(n=2)
        self.assertLessEqual(len(latest), 2)


if __name__ == "__main__":
    unittest.main()
