"""Job query service: search, filter, paginate."""

import math
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from ..models.job import Job


def search_jobs(
    db: Session,
    *,
    keyword: str | None = None,
    job_type: str | None = None,
    city: str | None = None,
    salary_min: int | None = None,
    sort: str = "latest",
    page: int = 1,
    size: int = 20,
) -> tuple[list[Job], int]:
    """Paginated job search with filters.

    - keyword: pg_trgm fuzzy match on title, company, description (ILIKE)
    - job_type: exact match
    - city: exact match
    - salary_min: minimum salary filter
    - sort: "latest" (posted_at DESC), "salary" (salary_max DESC), "deadline" (deadline ASC)
    """
    size = min(size, 50)  # Cap page size
    page = max(page, 1)

    # ── Base query ──
    base = select(Job).where(Job.is_active == True)

    # ── Keyword search (pg_trgm-powered ILIKE) ──
    if keyword:
        pattern = f"%{keyword}%"
        base = base.where(
            or_(
                Job.title.ilike(pattern),
                Job.company.ilike(pattern),
                Job.description.ilike(pattern),
            )
        )

    # ── Filters ──
    if job_type:
        base = base.where(Job.job_type == job_type)
    if city:
        # Support partial match like "北京" matching "北京市朝阳区"
        base = base.where(Job.city.ilike(f"%{city}%"))
    if salary_min is not None:
        base = base.where(
            or_(
                Job.salary_max >= salary_min,
                Job.salary_min >= salary_min,
            )
        )

    # ── Count ──
    count_stmt = select(func.count()).select_from(base.subquery())
    total = db.execute(count_stmt).scalar() or 0

    # ── Sort ──
    sort_map = {
        "latest": Job.posted_at.desc().nullslast(),
        "salary": Job.salary_max.desc().nullslast(),
        "deadline": Job.deadline.asc().nullslast(),
    }
    order = sort_map.get(sort, sort_map["latest"])
    base = base.order_by(order)

    # ── Paginate ──
    offset = (page - 1) * size
    base = base.offset(offset).limit(size)

    jobs = db.execute(base).scalars().all()

    return list(jobs), total


def get_job_by_id(db: Session, job_id: str) -> Job | None:
    """Get a single job by ID (only if active)."""
    stmt = select(Job).where(Job.id == job_id, Job.is_active == True)
    return db.execute(stmt).scalar_one_or_none()


def get_job_stats(db: Session) -> dict:
    """Aggregate stats: total active jobs, counts by type/city/source."""
    # Total
    total = db.execute(
        select(func.count(Job.id)).where(Job.is_active == True)
    ).scalar() or 0

    # By type
    type_rows = db.execute(
        select(Job.job_type, func.count(Job.id))
        .where(Job.is_active == True, Job.job_type != None)
        .group_by(Job.job_type)
    ).all()
    type_counts = {row[0]: row[1] for row in type_rows if row[0]}

    # By city (top 20)
    city_rows = db.execute(
        select(Job.city, func.count(Job.id))
        .where(Job.is_active == True, Job.city != None)
        .group_by(Job.city)
        .order_by(func.count(Job.id).desc())
        .limit(20)
    ).all()
    city_counts = {row[0]: row[1] for row in city_rows if row[0]}

    # By source
    source_rows = db.execute(
        select(Job.source, func.count(Job.id))
        .where(Job.is_active == True)
        .group_by(Job.source)
    ).all()
    source_counts = {row[0]: row[1] for row in source_rows if row[0]}

    return {
        "total_jobs": total,
        "type_counts": type_counts,
        "city_counts": city_counts,
        "source_counts": source_counts,
    }
