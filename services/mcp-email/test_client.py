"""Unit test for mcp-email tools against local dummy emails."""

import unittest
from mcp_email.server import list_emails, get_email, get_latest_emails


class TestMcpEmail(unittest.TestCase):
    def test_list_emails(self):
        emails = list_emails()
        self.assertGreater(len(emails), 0)
        first = emails[0]
        self.assertIn("id", first)
        self.assertIn("subject", first)
        self.assertEqual(first["source_type"], "email")

    def test_get_email(self):
        item = get_email("TH-E-001")
        self.assertEqual(item["id"], "TH-E-001")
        self.assertEqual(item["author"], "Erkki Expert")
        self.assertIn("TRN-042", item["subject"])
        self.assertIn("traffic", item["body"])

    def test_get_latest_emails(self):
        latest = get_latest_emails(n=2)
        self.assertLessEqual(len(latest), 2)


if __name__ == "__main__":
    unittest.main()
