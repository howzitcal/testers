from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, create_engine, text
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


def get_engine(db_url):
    return create_engine(db_url)


def get_session_factory(engine):
    factory = sessionmaker(bind=engine)
    return factory


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
