"""Service layer for persisting scraped jobs into the database."""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from ..models.job import Job
from ..models.application import Application
from ..models.digest_queue import DigestQueue
from ..scraper.base import BaseScraper

logger = logging.getLogger(__name__)


def upsert_job(db: Session, job_data: dict) -> Job | None:
    """Insert or update a job by dedup_key.

    - If dedup_key doesn't exist → INSERT new row.
    - If dedup_key exists → UPDATE changed fields (keep source info merged).

    Returns the Job (new or existing) or None on error.
    """
    try:
        stmt = (
            insert(Job)
            .values(**job_data)
            .on_conflict_do_update(
                index_elements=["dedup_key"],
                set_={
                    "source": Job.source,
                    "source_url": Job.source_url,
                    "source_hash": Job.source_hash,
                    "salary_min": Job.salary_min,
                    "salary_max": Job.salary_max,
                    "description": Job.description,
                    "skills": Job.skills,
                    "is_active": True,
                    "posted_at": Job.posted_at,
                    "deadline": Job.deadline,
                    "updated_at": datetime.now(timezone.utc),
                },
            )
        )
        db.execute(stmt)
        db.commit()

        # Fetch the persisted row
        result = db.execute(
            select(Job).where(Job.dedup_key == job_data["dedup_key"])
        )
        return result.scalar_one_or_none()
    except Exception:
        db.rollback()
        logger.exception("Failed to upsert job: %s", job_data.get("title"))
        return None


def validate_and_deactivate(db: Session) -> int:
    """Validate active jobs and deactivate unavailable ones.

    1. Select active jobs posted within last 30 days.
    2. For each, send an async HEAD request to source_url.
    3. If 404/connection error → mark is_active=False + cascade close applications.

    Returns: number of jobs deactivated.
    """
    threshold = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    # 30-day window
    from datetime import timedelta

    cutoff = threshold - timedelta(days=30)

    stmt = select(Job).where(Job.is_active == True, Job.posted_at >= cutoff)  # noqa: E712
    active_jobs = db.execute(stmt).scalars().all()

    deactivated = 0
    for job in active_jobs:
        # We'll run async HEAD inside a sync loop via asyncio
        # (the worker script runs standalone, not inside FastAPI)
        try:
            # Synchronous fallback — use a simple HEAD check
            import httpx

            with httpx.Client(timeout=10.0) as client:
                resp = client.head(job.source_url, follow_redirects=True)
                if resp.status_code >= 400:
                    _deactivate_job(db, job)
                    deactivated += 1
        except Exception:
            # Connection error → probably dead
            _deactivate_job(db, job)
            deactivated += 1

    db.commit()
    return deactivated


def _deactivate_job(db: Session, job: Job) -> None:
    """Mark a job as inactive and close related applications."""
    job.is_active = False
    job.updated_at = datetime.now(timezone.utc)

    # Cascade close: mark all non-terminated applications as 'closed'
    close_stmt = (
        update(Application)
        .where(
            Application.job_id == job.id,
            Application.status.in_(["applied", "screening"]),
        )
        .values(status="closed", updated_at=datetime.now(timezone.utc))
    )
    db.execute(close_stmt)
    logger.info("Deactivated job %s: %s@%s", job.id, job.title, job.company)


def cleanup_digest_queue(db: Session) -> int:
    """Clean up old digest queue entries (only runs on 1st day of month).

    Deletes entries that are sent AND older than 30 days.

    Returns: number of rows deleted.
    """
    today = datetime.now(timezone.utc)
    if today.day != 1:
        return 0  # Time-gated: only run on the 1st

    from datetime import timedelta

    cutoff = today - timedelta(days=30)
    stmt = (
        DigestQueue.__table__.delete()
        .where(DigestQueue.is_sent == True)  # noqa: E712
        .where(DigestQueue.matched_at < cutoff)
    )
    result = db.execute(stmt)
    db.commit()
    deleted = result.rowcount
    if deleted:
        logger.info("Cleaned up %d old digest_queue entries", deleted)
    return deleted
