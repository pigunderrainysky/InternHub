"""Authentication business logic."""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..config import settings
from ..models.user import User


# ── Password helpers ──────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password using bcrypt (auto-salted)."""
    # truncate to 72 bytes (bcrypt limit)
    password_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    plain_bytes = plain.encode("utf-8")[:72]
    return bcrypt.checkpw(plain_bytes, hashed.encode("utf-8"))


# ── Token helpers ─────────────────────────────────────────────

def create_access_token(user_id: str, token_version: int) -> str:
    """Create a short-lived access token (15 min)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "access",
        "tv": token_version,          # token_version for forced revocation
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str, token_version: int) -> str:
    """Create a long-lived refresh token (7 days)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "tv": token_version,
        "iat": now,
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT. Returns payload or None."""
    try:
        return jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        return None


def verify_token_version(token: str, current_version: int) -> bool:
    """Check that token's token_version matches user's current one."""
    payload = decode_token(token)
    if payload is None:
        return False
    return payload.get("tv") == current_version


# ── User CRUD ─────────────────────────────────────────────────

def get_user_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email.lower().strip())
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    stmt = select(User).where(User.id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def register_user(db: Session, email: str, password: str, nickname: str) -> User:
    """Create a new user. Raises ValueError if email already taken."""
    email = email.lower().strip()
    if get_user_by_email(db, email):
        raise ValueError("该邮箱已被注册")

    user = User(
        email=email,
        password_hash=hash_password(password),
        nickname=nickname.strip(),
        token_version=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return user if credentials valid, else None."""
    user = get_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def change_password(db: Session, user: User, old_password: str, new_password: str) -> None:
    """Change password and increment token_version to revoke all existing tokens."""
    if not verify_password(old_password, user.password_hash):
        raise ValueError("原密码错误")

    user.password_hash = hash_password(new_password)
    user.token_version += 1  # Invalidate all existing JWTs
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
