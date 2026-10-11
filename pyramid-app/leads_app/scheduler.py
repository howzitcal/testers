import logging
from datetime import datetime, timezone

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import sessionmaker

from .models import AuditLog, Lead

log = logging.getLogger(__name__)

_engine = None


def _maintenance_job():
    """Runs every 30 minutes: write a maintenance/health row to audit_log."""
    global _engine
    if _engine is None:
        return
    Session = sessionmaker(bind=_engine)
    session = Session()
    try:
        lead_count = session.query(Lead).count()
        message = f"Maintenance routine OK — lead count={lead_count}"
        session.add(AuditLog(created_at=datetime.now(timezone.utc), message=message))
        session.commit()
        log.info(message)
    except Exception:
        session.rollback()
        log.exception("Maintenance job failed")
    finally:
        session.close()


def start_scheduler(settings, engine):
    global _engine
    _engine = engine

    jobstore_url = settings.get("scheduler.jobstore.url", "sqlite:///./data/apscheduler.db")
    jobstores = {"default": SQLAlchemyJobStore(url=jobstore_url)}
    scheduler = BackgroundScheduler(jobstores=jobstores)
    scheduler.add_job(
        _maintenance_job,
        trigger="interval",
        minutes=30,
        id="maintenance_job",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    log.info("APScheduler started (maintenance every 30 minutes)")
    return scheduler
