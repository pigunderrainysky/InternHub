"""Subscription CRUD service."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.subscription import Subscription
from ..models.user import User


def get_subscription(db: Session, user: User) -> Subscription | None:
    """Get the user's subscription (one-to-one)."""
    stmt = select(Subscription).where(Subscription.user_id == user.id)
    return db.execute(stmt).scalar_one_or_none()


def upsert_subscription(
    db: Session,
    user: User,
    *,
    keywords: list[str],
    cities: list[str],
    job_types: list[str],
    frequency: str,
    enabled: bool,
) -> Subscription:
    """Create or replace the user's subscription settings."""
    sub = get_subscription(db, user)

    if sub is None:
        sub = Subscription(
            user_id=user.id,
            keywords=keywords,
            cities=cities,
            job_types=job_types,
            frequency=frequency,
            enabled=enabled,
        )
        db.add(sub)
    else:
        sub.keywords = keywords
        sub.cities = cities
        sub.job_types = job_types
        sub.frequency = frequency
        sub.enabled = enabled

    db.commit()
    db.refresh(sub)
    return sub
