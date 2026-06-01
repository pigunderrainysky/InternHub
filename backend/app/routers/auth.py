"""Authentication router: register, login, refresh, change password."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.auth import (
    RegisterRequest,
    LoginRequest,
    ChangePasswordRequest,
    RefreshRequest,
    AuthResponse,
    UserResponse,
    TokenResponse,
)
from ..services import auth_service
from .dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=dict)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account."""
    try:
        user = auth_service.register_user(
            db, email=body.email, password=body.password, nickname=body.nickname
        )
        return {
            "code": 0,
            "message": "注册成功，请登录",
            "data": {"id": str(user.id)},
        }
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/login", response_model=dict)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Login and return JWT tokens."""
    user = auth_service.authenticate_user(db, body.email, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    access_token = auth_service.create_access_token(str(user.id), user.token_version)
    refresh_token = auth_service.create_refresh_token(str(user.id), user.token_version)

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "nickname": user.nickname,
            },
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        },
    }


@router.post("/refresh", response_model=dict)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access token pair."""
    payload = auth_service.decode_token(body.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="无效的 refresh token")

    user_id = payload.get("sub")
    user = auth_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")

    # Verify token_version — if password changed, refresh is also invalid
    if not auth_service.verify_token_version(body.refresh_token, user.token_version):
        raise HTTPException(status_code=401, detail="Token 已失效，请重新登录")

    access_token = auth_service.create_access_token(str(user.id), user.token_version)
    refresh_token = auth_service.create_refresh_token(str(user.id), user.token_version)

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        },
    }


@router.get("/me", response_model=dict)
def get_me(current_user=Depends(get_current_user)):
    """Return the currently authenticated user."""
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "id": str(current_user.id),
            "email": current_user.email,
            "nickname": current_user.nickname,
        },
    }


@router.put("/password", response_model=dict)
def update_password(
    body: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change password — invalidates all existing tokens."""
    try:
        auth_service.change_password(
            db, current_user, body.old_password, body.new_password
        )
        return {"code": 0, "message": "密码修改成功，请重新登录", "data": None}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
