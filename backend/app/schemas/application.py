"""Pydantic schemas for Application API."""

from datetime import datetime
from pydantic import BaseModel, field_validator


VALID_STATUSES = {"applied", "screening", "interview", "offer", "rejected", "closed"}


class CreateApplicationRequest(BaseModel):
    job_id: str


class UpdateApplicationRequest(BaseModel):
    notes: str | None = None


class UpdateStatusRequest(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status: {v}. Must be one of {sorted(VALID_STATUSES)}"
            )
        return v


class ApplicationOut(BaseModel):
    id: str
    user_id: str
    job_id: str
    status: str
    notes: str | None
    applied_at: datetime | None
    updated_at: datetime | None
    # Nested job info for display
    job: dict | None = None

    model_config = {"from_attributes": True}


class ApplicationGroupedResponse(BaseModel):
    """Applications grouped by status for Kanban display."""
    columns: dict[str, list[ApplicationOut]]
