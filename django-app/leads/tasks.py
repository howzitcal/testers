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


def dummy_job() -> str:
    log.info("dummy job")
    return "dummy job"


def ensure_health_check_schedule() -> None:
    """Register repeating Django-Q schedules that fire every 1 second."""
    # django-q2 has no SECONDS type; use 6-field cron (requires croniter).
    every_second = "* * * * * *"

    # Drop legacy names from earlier broken SECONDS attempts / 30m schedules.
    Schedule.objects.filter(name__in=("health_check_30m", "dummy_job_1m")).delete()

    Schedule.objects.update_or_create(
        name="health_check_1s",
        defaults={
            "func": "leads.tasks.run_health_check",
            "schedule_type": Schedule.CRON,
            "cron": every_second,
            "minutes": None,
            "repeats": -1,
        },
    )

    Schedule.objects.update_or_create(
        name="dummy_job_1s",
        defaults={
            "func": "leads.tasks.dummy_job",
            "schedule_type": Schedule.CRON,
            "cron": every_second,
            "minutes": None,
            "repeats": -1,
        },
    )
