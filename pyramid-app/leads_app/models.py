import os
from datetime import datetime, timezone
from urllib.parse import quote_plus

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from zope.sqlalchemy import register

Base = declarative_base()


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    status = Column(String(50), nullable=False, default="new")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    message = Column(String(1000), nullable=False)


class BackgroundJob(Base):
    """MySQL-backed job queue shared by web and worker containers."""

    __tablename__ = "background_jobs"

    id = Column(Integer, primary_key=True)
    job_type = Column(String(100), nullable=False)
    payload = Column(Text, nullable=False, default="{}")
    status = Column(String(20), nullable=False, default="pending")  # pending|running|done|failed
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)


def build_db_url(
    name: str | None = None,
    user: str | None = None,
    password: str | None = None,
    host: str | None = None,
    port: str | None = None,
) -> str:
    """Build a MySQL SQLAlchemy URL from the same env vars Django uses."""
    db_name = name or os.environ.get("DB_NAME", "pyramid_leads")
    db_user = user or os.environ.get("DB_USERNAME", "root")
    db_password = password or os.environ.get("DB_PASSWORD", "password")
    db_host = host or os.environ.get("DB_HOST", "host.docker.internal")
    db_port = port or os.environ.get("DB_PORT", "3306")
    return (
        f"mysql+pymysql://{quote_plus(db_user)}:{quote_plus(db_password)}"
        f"@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    )


def resolve_db_url(settings: dict | None = None) -> str:
    """Prefer SQLALCHEMY_URL, else Django-style DB_* env, else ini setting."""
    if os.environ.get("SQLALCHEMY_URL"):
        return os.environ["SQLALCHEMY_URL"]
    if any(os.environ.get(k) for k in ("DB_NAME", "DB_HOST", "DB_USERNAME", "DB_PASSWORD")):
        return build_db_url()
    if settings and settings.get("sqlalchemy.url"):
        return settings["sqlalchemy.url"]
    return build_db_url()


def get_engine(db_url: str):
    kwargs = {}
    if db_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}
    else:
        kwargs["pool_pre_ping"] = True
        kwargs["pool_recycle"] = 3600
    return create_engine(db_url, **kwargs)


def get_session_factory(engine):
    return sessionmaker(bind=engine)


def get_tm_session(session_factory, transaction_manager):
    dbsession = session_factory()
    register(dbsession, transaction_manager=transaction_manager)
    return dbsession


def init_db(db_url: str | None = None):
    engine = get_engine(db_url or build_db_url())
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return engine
