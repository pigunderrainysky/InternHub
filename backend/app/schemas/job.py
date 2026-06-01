"""Pydantic schemas for Job responses and query parameters."""

from datetime import datetime
from pydantic import BaseModel


class JobOut(BaseModel):
    """Public job listing item."""
    id: str
    title: str
    company: str
    city: str | None
    job_type: str | None
    salary_min: int | None
    salary_max: int | None
    description: str | None
    skills: list[str] | None
    source: str
    source_url: str
    is_active: bool
    posted_at: datetime | None
    deadline: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class JobDetailOut(JobOut):
    """Full job detail including full description text."""
    pass


class JobListResponse(BaseModel):
    """Paginated job list."""
    items: list[JobOut]
    total: int
    page: int
    size: int
    pages: int


class JobStatsOut(BaseModel):
    """Aggregate stats for filter options."""
    total_jobs: int
    type_counts: dict[str, int]
    city_counts: dict[str, int]
    source_counts: dict[str, int]
