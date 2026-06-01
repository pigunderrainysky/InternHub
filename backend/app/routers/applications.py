"""Applications router: Kanban CRUD."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.application import (
    CreateApplicationRequest,
    UpdateApplicationRequest,
    UpdateStatusRequest,
)
from ..services import application_service
from ..routers.dependencies import get_current_user

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.get("", response_model=dict)
def list_applications(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all applications grouped by status (Kanban columns)."""
    grouped = application_service.get_user_applications(db, current_user)
    return {"code": 0, "message": "ok", "data": {"columns": grouped}}


@router.post("", response_model=dict)
def create_application(
    body: CreateApplicationRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a job to the applied column."""
    try:
        app = application_service.create_application(db, current_user, body.job_id)
        return {
            "code": 0,
            "message": "投递成功",
            "data": {
                "id": str(app.id),
                "status": app.status,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.patch("/{application_id}/status", response_model=dict)
def update_status(
    application_id: str,
    body: UpdateStatusRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Move an application card to a different Kanban column."""
    app = application_service.update_application_status(
        db, current_user, application_id, body.status
    )
    if app is None:
        raise HTTPException(status_code=404, detail="投递记录不存在")
    return {
        "code": 0,
        "message": "状态已更新",
        "data": {"id": str(app.id), "status": app.status},
    }


@router.put("/{application_id}", response_model=dict)
def update_application(
    application_id: str,
    body: UpdateApplicationRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Edit application notes."""
    app = application_service.update_application(
        db, current_user, application_id, body.notes
    )
    if app is None:
        raise HTTPException(status_code=404, detail="投递记录不存在")
    return {
        "code": 0,
        "message": "已更新",
        "data": {"id": str(app.id), "notes": app.notes},
    }


@router.delete("/{application_id}", response_model=dict)
def delete_application(
    application_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an application record."""
    deleted = application_service.delete_application(db, current_user, application_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="投递记录不存在")
    return {"code": 0, "message": "已删除", "data": None}
