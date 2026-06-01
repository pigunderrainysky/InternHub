"""Application CRUD service."""

from datetime import datetime, timezone
from collections import defaultdict

from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from ..models.application import Application
from ..models.job import Job
from ..models.user import User


def get_user_applications(db: Session, user: User) -> dict[str, list[dict]]:
    """Get all applications for a user, grouped by status.

    Returns:
        dict like {"applied": [...], "screening": [...], ...}
    """
    stmt = (
        select(Application)
        .where(Application.user_id == user.id)
        .options(joinedload(Application.job))
        .order_by(Application.applied_at.desc())
    )
    apps = db.execute(stmt).scalars().all()

    grouped: dict[str, list[dict]] = defaultdict(list)
    for app in apps:
        item = _serialize_app(app)
        grouped[app.status].append(item)

    # Ensure all 6 columns exist
    for status in ["applied", "screening", "interview", "offer", "rejected", "closed"]:
        if status not in grouped:
            grouped[status] = []

    return dict(grouped)


def create_application(db: Session, user: User, job_id: str) -> Application:
    """Create a new application record.

    Raises ValueError if job not found or already applied.
    """
    # Validate job exists
    job = db.execute(select(Job).where(Job.id == job_id)).scalar_one_or_none()
    if job is None:
        raise ValueError("岗位不存在")

    # Check for duplicate
    existing = db.execute(
        select(Application).where(
            Application.user_id == user.id, Application.job_id == job_id
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ValueError("你已经投递过这个岗位了")

    app = Application(
        user_id=user.id,
        job_id=job_id,
        status="applied",
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def update_application_status(
    db: Session, user: User, application_id: str, new_status: str
) -> Application | None:
    """Update the status of an application. Returns None if not found."""
    stmt = select(Application).where(
        Application.id == application_id, Application.user_id == user.id
    )
    app = db.execute(stmt).scalar_one_or_none()
    if app is None:
        return None

    app.status = new_status
    app.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(app)
    return app


def update_application(
    db: Session, user: User, application_id: str, notes: str | None
) -> Application | None:
    """Update application notes. Returns None if not found."""
    stmt = select(Application).where(
        Application.id == application_id, Application.user_id == user.id
    )
    app = db.execute(stmt).scalar_one_or_none()
    if app is None:
        return None

    app.notes = notes
    app.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(app)
    return app


def delete_application(db: Session, user: User, application_id: str) -> bool:
    """Delete an application. Returns True if deleted, False if not found."""
    stmt = select(Application).where(
        Application.id == application_id, Application.user_id == user.id
    )
    app = db.execute(stmt).scalar_one_or_none()
    if app is None:
        return False

    db.delete(app)
    db.commit()
    return True


def _serialize_app(app: Application) -> dict:
    """Serialize an Application to a dict with nested job info."""
    job = app.job
    return {
        "id": str(app.id),
        "user_id": str(app.user_id),
        "job_id": str(app.job_id),
        "status": app.status,
        "notes": app.notes,
        "applied_at": app.applied_at.isoformat() if app.applied_at else None,
        "updated_at": app.updated_at.isoformat() if app.updated_at else None,
        "job": {
            "id": str(job.id),
            "title": job.title,
            "company": job.company,
            "city": job.city,
            "job_type": job.job_type,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "source": job.source,
            "source_url": job.source_url,
        } if job else None,
    }
