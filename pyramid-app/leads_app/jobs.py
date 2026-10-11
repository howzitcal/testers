import json
import logging
from datetime import datetime, timezone

from .models import BackgroundJob

log = logging.getLogger(__name__)

JOB_WELCOME_EMAIL = "welcome_email"


def enqueue_welcome_email(dbsession, lead_id: int, name: str, email: str) -> BackgroundJob:
    job = BackgroundJob(
        job_type=JOB_WELCOME_EMAIL,
        payload=json.dumps({"lead_id": lead_id, "name": name, "email": email}),
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    dbsession.add(job)
    dbsession.flush()
    log.info("Enqueued welcome_email job id=%s for lead id=%s", job.id, lead_id)
    return job
