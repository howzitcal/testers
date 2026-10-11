from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine, event, text
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
    """SQLite-backed job queue shared by web and worker containers."""

    __tablename__ = "background_jobs"

    id = Column(Integer, primary_key=True)
    job_type = Column(String(100), nullable=False)
    payload = Column(Text, nullable=False, default="{}")
    status = Column(String(20), nullable=False, default="pending")  # pending|running|done|failed
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)


def get_engine(db_url):
    engine = create_engine(db_url, connect_args={"check_same_thread": False, "timeout": 30})

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

    return engine


def get_session_factory(engine):
    return sessionmaker(bind=engine)


def get_tm_session(session_factory, transaction_manager):
    dbsession = session_factory()
    register(dbsession, transaction_manager=transaction_manager)
    return dbsession


def init_db(db_url="sqlite:///./data/leads.db"):
    import os

    os.makedirs("data", exist_ok=True)
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return engine
