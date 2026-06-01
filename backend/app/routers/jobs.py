"""Jobs router: search, detail, stats."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.job import JobOut, JobListResponse, JobStatsOut
from ..services import job_service

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=dict)
def list_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    keyword: str | None = None,
    job_type: str | None = None,
    city: str | None = None,
    salary_min: int | None = None,
    sort: str = Query("latest", pattern="^(latest|salary|deadline)$"),
    db: Session = Depends(get_db),
):
    """Paginated job listing with search, filter, and sort."""
    jobs, total = job_service.search_jobs(
        db,
        keyword=keyword,
        job_type=job_type,
        city=city,
        salary_min=salary_min,
        sort=sort,
        page=page,
        size=size,
    )
    pages = max(1, -(-total // size))  # ceil division

    items = [
        {
            "id": str(j.id),
            "title": j.title,
            "company": j.company,
            "city": j.city,
            "job_type": j.job_type,
            "salary_min": j.salary_min,
            "salary_max": j.salary_max,
            "description": j.description[:500] if j.description else None,
            "skills": j.skills,
            "source": j.source,
            "source_url": j.source_url,
            "is_active": j.is_active,
            "posted_at": j.posted_at.isoformat() if j.posted_at else None,
            "deadline": j.deadline.isoformat() if j.deadline else None,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        }
        for j in jobs
    ]

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        },
    }


@router.get("/stats", response_model=dict)
def get_stats(db: Session = Depends(get_db)):
    """Get aggregate stats: counts by type/city/source."""
    stats = job_service.get_job_stats(db)
    return {"code": 0, "message": "ok", "data": stats}


@router.get("/{job_id}", response_model=dict)
def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get full job detail by ID."""
    job = job_service.get_job_by_id(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="岗位不存在或已下线")

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "id": str(job.id),
            "title": job.title,
            "company": job.company,
            "city": job.city,
            "job_type": job.job_type,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "description": job.description,
            "skills": job.skills,
            "source": job.source,
            "source_url": job.source_url,
            "is_active": job.is_active,
            "posted_at": job.posted_at.isoformat() if job.posted_at else None,
            "deadline": job.deadline.isoformat() if job.deadline else None,
            "created_at": job.created_at.isoformat() if job.created_at else None,
        },
    }
