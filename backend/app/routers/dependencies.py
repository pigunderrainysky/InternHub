"""Shared FastAPI dependencies (JWT auth guard)."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import auth_service

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """Dependency: extract and validate the current user from JWT Bearer token."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="请先登录")

    token = credentials.credentials
    payload = auth_service.decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="无效的 access token")

    user_id = payload.get("sub")
    user = auth_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")

    # Token version check — if user changed password, this token is invalid
    if not auth_service.verify_token_version(token, user.token_version):
        raise HTTPException(status_code=401, detail="Token 已失效，请重新登录")

    return user
