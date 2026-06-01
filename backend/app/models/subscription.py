"""Subscription model for user job alerts."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, ARRAY, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from ..database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )

    keywords: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    cities: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    job_types: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    frequency: Mapped[str] = mapped_column(
        Enum("daily", "weekly", name="frequency_enum"), default="daily", nullable=False
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    last_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="subscription")
