import logging
from datetime import datetime, timezone

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import sessionmaker

from .models import AuditLog, Lead

log = logging.getLogger(__name__)

_engine = None


def run_health_check():
    """Mirrors Django leads.tasks.run_health_check."""
    global _engine
    if _engine is None:
        return
    Session = sessionmaker(bind=_engine)
    session = Session()
    try:
        lead_count = session.query(Lead).count()
        message = f"System health check OK — lead count={lead_count}"
        session.add(AuditLog(created_at=datetime.now(timezone.utc), message=message))
        session.commit()
        log.info(message)
        return message
    except Exception:
        session.rollback()
        log.exception("Health check job failed")
    finally:
        session.close()


def dummy_job():
    """Mirrors Django leads.tasks.dummy_job."""
    log.info("dummy job")
    return "dummy job"


def start_scheduler(settings, engine):
    global _engine
    _engine = engine

    jobstore_url = settings.get("scheduler.jobstore.url") or settings.get("sqlalchemy.url")
    jobstores = {"default": SQLAlchemyJobStore(url=jobstore_url)}
    scheduler = BackgroundScheduler(jobstores=jobstores)

    # Match Django-Q schedules in leads.tasks.ensure_health_check_schedule
    # (currently every 1 second for load comparison).
    scheduler.add_job(
        run_health_check,
        trigger="interval",
        seconds=1,
        id="health_check_30m",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        dummy_job,
        trigger="interval",
        seconds=1,
        id="dummy_job_1m",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    log.info("APScheduler started (health_check + dummy_job every 1s)")
    return scheduler
