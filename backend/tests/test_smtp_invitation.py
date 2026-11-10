"""SMTP adapter tests never send real email."""
import os
import unittest
from unittest.mock import patch, MagicMock

from app.services.smtp_mail import generate_invitation, send_smtp_message, smtp_configured


class SmtpInvitationTests(unittest.TestCase):
    def test_draft_contains_generated_form_link(self):
        draft = generate_invitation("Test Researcher", "test@example.edu", "https://docs.google.com/forms/d/e/test/viewform")
        self.assertEqual(draft["to"], "test@example.edu")
        self.assertIn("https://docs.google.com/forms/d/e/test/viewform", draft["body"])

    @patch.dict(os.environ, {}, clear=True)
    def test_delivery_is_off_by_default(self):
        self.assertFalse(smtp_configured())
        with self.assertRaises(RuntimeError):
            send_smtp_message(to="test@example.edu", subject="Hi", body="Test")

    @patch.dict(os.environ, {
        "SMTP_ENABLE_SEND": "true", "SMTP_ALLOWED_RECIPIENTS": "test@example.edu",
        "SMTP_FROM": "approved@uci.edu", "SMTP_HOST": "smtp.test.invalid", "SMTP_PORT": "587",
    }, clear=True)
    @patch("app.services.smtp_mail.smtplib.SMTP")
    def test_starttls_and_recipient_allowlist(self, smtp):
        client = MagicMock()
        smtp.return_value.__enter__.return_value = client
        send_smtp_message(to="test@example.edu", subject="SCRC", body="Hello")
        client.starttls.assert_called_once()
        client.send_message.assert_called_once()
        with self.assertRaises(ValueError):
            send_smtp_message(to="unauthorized@example.edu", subject="SCRC", body="Hello")
        self.assertEqual(client.send_message.call_count, 1)


if __name__ == "__main__":
    unittest.main()
