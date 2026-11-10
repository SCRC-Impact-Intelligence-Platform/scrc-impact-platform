"""SMTP STARTTLS adapter. Sending is disabled by default and test-recipient gated.

This module does not confer authorization to use UCI's relay or sender address.
"""
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import parseaddr


def generate_invitation(name: str, email: str, form_url: str) -> dict:
    return {
        "to": email,
        "subject": "SCRC Research Publication Resource Verification",
        "body": (
            f"Dear {name},\n\n"
            "We are reviewing publications associated with the UCI Stem Cell Research Center. "
            "Could you please confirm whether SCRC resources contributed to the research?\n\n"
            f"Please use the following verification form:\n{form_url}\n\n"
            "Thank you for your time.\n\n"
            "SCRC Impact Intelligence Team"
        ),
    }


def smtp_configured() -> bool:
    return os.getenv("SMTP_ENABLE_SEND") == "true" and bool(os.getenv("SMTP_ALLOWED_RECIPIENTS"))


def send_smtp_message(*, to: str, subject: str, body: str) -> None:
    if not smtp_configured():
        raise RuntimeError("SMTP not enabled")
    allowed = {item.strip().lower() for item in os.environ["SMTP_ALLOWED_RECIPIENTS"].split(",") if item.strip()}
    if to.lower() not in allowed:
        raise ValueError("Recipient not in SMTP_ALLOWED_RECIPIENTS")
    sender = os.getenv("SMTP_FROM", "")
    if not sender or parseaddr(sender)[1] != sender:
        raise ValueError("SMTP_FROM must be a valid authorized address")
    if "\n" in subject or "\r" in subject:
        raise ValueError("Invalid email subject")
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    reply_to = os.getenv("SMTP_REPLY_TO", "")
    if reply_to:
        msg["Reply-To"] = reply_to
    msg["Subject"] = subject
    msg.set_content(body)
    # Port 587 conventionally uses STARTTLS, not SMTP_SSL implicit TLS.
    with smtplib.SMTP(os.getenv("SMTP_HOST", "mta.service.uci.edu"), int(os.getenv("SMTP_PORT", "587")), timeout=15) as client:
        client.ehlo()
        client.starttls(context=ssl.create_default_context())
        client.ehlo()
        username = os.getenv("SMTP_USERNAME")
        password = os.getenv("SMTP_PASSWORD")
        if username and password:
            client.login(username, password)
        client.send_message(msg)
