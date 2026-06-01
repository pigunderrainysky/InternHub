"""Test fixtures — SQLite in-memory database for local testing.

PostgreSQL-specific types (UUID, ARRAY, ENUM, GIN, pg_trgm, ON CONFLICT)
are adapted for SQLite compatibility.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import uuid
from sqlalchemy import (
    create_engine, event, Column, String, Integer, Text, Boolean,
    DateTime, ForeignKey, JSON, UniqueConstraint
)
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# ══ SQLite-compatible base (no PG-specific types) ══

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(100), nullable=True)
    token_version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime, nullable=True)


class Job(Base):
    __tablename__ = "jobs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    company = Column(String(255), nullable=False)
    city = Column(String(100), nullable=True)
    job_type = Column(String(50), nullable=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    skills = Column(JSON, nullable=True)  # SQLite: JSON instead of ARRAY
    source = Column(String(50), nullable=False)
    source_url = Column(Text, nullable=False)
    source_hash = Column(String(64), unique=True, nullable=False)
    dedup_key = Column(String(64), unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    posted_at = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime, nullable=True)


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    keywords = Column(JSON, nullable=True)
    cities = Column(JSON, nullable=True)
    job_types = Column(JSON, nullable=True)
    frequency = Column(String(10), nullable=False, default="daily")
    enabled = Column(Boolean, default=True, nullable=False)
    last_sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime)


class Application(Base):
    __tablename__ = "applications"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    status = Column(String(20), nullable=False, default="applied")
    notes = Column(Text, nullable=True)
    applied_at = Column(DateTime)
    updated_at = Column(DateTime, nullable=True)


class DigestQueue(Base):
    __tablename__ = "digest_queue"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    is_sent = Column(Boolean, default=False, nullable=False)
    matched_at = Column(DateTime)
    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="idx_digest_queue_unique"),
    )


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh SQLite in-memory database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
