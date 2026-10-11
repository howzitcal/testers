import logging

log = logging.getLogger(__name__)


class MockMailClient:
    """Mock mail client — no SMTP, no network. Logs only."""

    def send(self, to_name: str, to_email: str, subject: str, body: str) -> None:
        log.info(
            "[MOCK MAIL] to=%s <%s> subject=%r body=%r",
            to_name,
            to_email,
            subject,
            body,
        )
