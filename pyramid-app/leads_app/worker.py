"""Standalone worker process: drains MySQL job queue + runs APScheduler.

Mirrors Django's qcluster role so resource use can be compared fairly.
"""

import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone

from .jobs import JOB_WELCOME_EMAIL
from .mail import MockMailClient
from .models import BackgroundJob, Base, get_engine, get_session_factory, resolve_db_url
from .scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s",
)
log = logging.getLogger("leads_app.worker")

POLL_INTERVAL_SEC = 1.0


def _claim_next_job(session):
    job = (
        session.query(BackgroundJob)
        .filter(BackgroundJob.status == "pending")
        .order_by(BackgroundJob.id)
        .first()
    )
    if job is None:
        return None
    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    session.commit()
    return job


def _process_job(session, job, mail: MockMailClient):
    payload = json.loads(job.payload or "{}")
    if job.job_type == JOB_WELCOME_EMAIL:
        log.info("Processing welcome_email job id=%s lead_id=%s", job.id, payload.get("lead_id"))
        time.sleep(0.5)
        mail.send(
            payload.get("name", ""),
            payload.get("email", ""),
            "Welcome!",
            f"Thanks for signing up, {payload.get('name', '')}.",
        )
    else:
        raise ValueError(f"Unknown job_type: {job.job_type}")

    job.status = "done"
    job.finished_at = datetime.now(timezone.utc)
    session.commit()


def run_worker():
    db_url = resolve_db_url()
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)
    session_factory = get_session_factory(engine)

    jobstore_url = os.environ.get("SCHEDULER_JOBSTORE_URL") or db_url
    settings = {
        "sqlalchemy.url": db_url,
        "scheduler.jobstore.url": jobstore_url,
    }
    scheduler = start_scheduler(settings, engine)

    mail = MockMailClient()
    stop = False

    def _handle_signal(signum, frame):
        nonlocal stop
        log.info("Received signal %s, shutting down worker", signum)
        stop = True

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    log.info("Pyramid worker started (MySQL queue + APScheduler)")

    try:
        while not stop:
            session = session_factory()
            try:
                job = _claim_next_job(session)
                if job is None:
                    session.close()
                    time.sleep(POLL_INTERVAL_SEC)
                    continue
                try:
                    _process_job(session, job, mail)
                except Exception as exc:
                    log.exception("Job id=%s failed", job.id)
                    job.status = "failed"
                    job.error = str(exc)
                    job.finished_at = datetime.now(timezone.utc)
                    session.commit()
            finally:
                session.close()
    finally:
        try:
            scheduler.shutdown(wait=False)
        except Exception:
            pass
        log.info("Pyramid worker stopped")


def main(argv=None):
    run_worker()
    return 0


if __name__ == "__main__":
    sys.exit(main())
