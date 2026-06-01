"""Subscription router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.subscription import SubscriptionRequest
from ..services import subscription_service
from ..routers.dependencies import get_current_user

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


@router.get("", response_model=dict)
def get_subscription(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's subscription settings."""
    sub = subscription_service.get_subscription(db, current_user)
    if sub is None:
        return {
            "code": 0,
            "message": "ok",
            "data": None,  # No subscription yet
        }

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "id": str(sub.id),
            "keywords": sub.keywords or [],
            "cities": sub.cities or [],
            "job_types": sub.job_types or [],
            "frequency": sub.frequency,
            "enabled": sub.enabled,
            "last_sent_at": sub.last_sent_at.isoformat() if sub.last_sent_at else None,
        },
    }


@router.post("", response_model=dict)
def create_or_update_subscription(
    body: SubscriptionRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update subscription settings (upsert)."""
    sub = subscription_service.upsert_subscription(
        db,
        current_user,
        keywords=body.keywords,
        cities=body.cities,
        job_types=body.job_types,
        frequency=body.frequency,
        enabled=body.enabled,
    )

    return {
        "code": 0,
        "message": "订阅设置已保存",
        "data": {
            "id": str(sub.id),
            "keywords": sub.keywords or [],
            "cities": sub.cities or [],
            "job_types": sub.job_types or [],
            "frequency": sub.frequency,
            "enabled": sub.enabled,
            "last_sent_at": sub.last_sent_at.isoformat() if sub.last_sent_at else None,
        },
    }
