import logging
import time

from django_q.models import Schedule

from .mail import mail_client
from .models import AuditLog, Lead

log = logging.getLogger(__name__)


def send_welcome_email(lead_id: int) -> str:
    lead = Lead.objects.get(pk=lead_id)
    log.info("Queueing mocked welcome email for lead id=%s", lead.id)
    time.sleep(0.5)
    mail_client.send(
        lead.name,
        lead.email,
        "Welcome!",
        f"Thanks for signing up, {lead.name}.",
    )
    return f"mock welcome emailed to {lead.email}"


def run_health_check() -> str:
    lead_count = Lead.objects.count()
    message = f"System health check OK — lead count={lead_count}"
    AuditLog.objects.create(message=message)
    log.info(message)
    return message


def ensure_health_check_schedule() -> None:
    """Register a repeating Django-Q schedule (every 30 minutes) if missing."""
    Schedule.objects.update_or_create(
        name="health_check_30m",
        defaults={
            "func": "leads.tasks.run_health_check",
            "schedule_type": Schedule.MINUTES,
            # "minutes": 30,
            "seconds": 1,
            "repeats": -1,
        },
    )
