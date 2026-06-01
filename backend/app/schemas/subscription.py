"""Pydantic schemas for Subscription API."""

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class SubscriptionRequest(BaseModel):
    """Create or update a subscription (upsert)."""
    keywords: list[str] = []
    cities: list[str] = []
    job_types: list[str] = []
    frequency: str = "daily"
    enabled: bool = True

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        if v not in ("daily", "weekly"):
            raise ValueError("frequency must be 'daily' or 'weekly'")
        return v

    @model_validator(mode="after")
    def at_least_one_criterion(self):
        """Require at least one non-empty filter to avoid matching ALL jobs."""
        if not self.keywords and not self.cities and not self.job_types:
            raise ValueError("请至少设置一个筛选条件：关键词、城市或岗位类型")
        return self


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    keywords: list[str] | None
    cities: list[str] | None
    job_types: list[str] | None
    frequency: str
    enabled: bool
    last_sent_at: str | None
