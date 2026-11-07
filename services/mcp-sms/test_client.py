"""Unit test for mcp-sms tools against local dummy SMS files."""

import unittest
from mcp_sms.server import list_messages, get_message, get_latest_messages


class TestMcpSms(unittest.TestCase):
    def test_list_messages(self):
        items = list_messages()
        self.assertGreater(len(items), 0)
        first = items[0]
        self.assertEqual(first["id"], "TH-S-001")
        self.assertEqual(first["source_type"], "sms")
        self.assertIn("Pekka Pohjola", first["participants"])

    def test_get_message(self):
        item = get_message("TH-S-001")
        self.assertEqual(item["id"], "TH-S-001")
        self.assertIn("SAL-03", item["body"])
        self.assertGreater(len(item["messages"]), 0)

    def test_get_latest_messages(self):
        latest = get_latest_messages(n=1)
        self.assertEqual(len(latest), 1)


if __name__ == "__main__":
    unittest.main()
