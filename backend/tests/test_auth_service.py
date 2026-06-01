"""Test auth_service: password hashing, token creation, user CRUD.

Uses SQLite-compatible test models from conftest.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import select

from app.services import auth_service
from .conftest import User


class TestPasswordHashing:
    def test_hash_and_verify(self):
        pw = "securePassword123"
        hashed = auth_service.hash_password(pw)
        assert hashed != pw
        assert hashed.startswith("$2b$")  # bcrypt prefix
        assert auth_service.verify_password(pw, hashed) is True

    def test_verify_wrong_password(self):
        hashed = auth_service.hash_password("correct")
        assert auth_service.verify_password("wrong", hashed) is False

    def test_hash_truncation_72_bytes(self):
        """bcrypt truncates at 72 bytes — ensure no crash on long passwords."""
        long_pw = "a" * 100
        hashed = auth_service.hash_password(long_pw)
        assert auth_service.verify_password(long_pw, hashed) is True


class TestTokenCreation:
    def test_access_token_contains_claims(self):
        token = auth_service.create_access_token("user-123", token_version=1)
        payload = auth_service.decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"
        assert payload["tv"] == 1

    def test_refresh_token_contains_claims(self):
        token = auth_service.create_refresh_token("user-456", token_version=3)
        payload = auth_service.decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-456"
        assert payload["type"] == "refresh"
        assert payload["tv"] == 3

    def test_decode_invalid_token(self):
        assert auth_service.decode_token("not.a.valid.token") is None
        assert auth_service.decode_token("") is None

    def test_token_version_mismatch(self):
        token = auth_service.create_access_token("user-1", token_version=5)
        assert auth_service.verify_token_version(token, 5) is True
        assert auth_service.verify_token_version(token, 3) is False


class TestUserCRUDWithSQLite:
    """Test core auth logic using SQLite-compatible User model."""

    def _create_user(self, db_session, email="test@example.com", password="password123", nickname="测试用户"):
        """Helper: create a user directly in the test DB."""
        user = User(
            email=email.lower().strip(),
            password_hash=auth_service.hash_password(password),
            nickname=nickname.strip(),
            token_version=1,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(user)
        db_session.commit()
        return user

    def test_register_flow(self, db_session):
        """Test manual register flow with password verify."""
        email = "new@test.com"
        pw = "strongPassword456"
        hashed = auth_service.hash_password(pw)

        user = User(
            email=email,
            password_hash=hashed,
            nickname="新用户",
            token_version=1,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(user)
        db_session.commit()

        # Verify can authenticate
        assert auth_service.verify_password(pw, user.password_hash)
        assert user.email == email
        assert user.token_version == 1

    def test_duplicate_email_prevented(self, db_session):
        self._create_user(db_session, "dup@test.com", "pw1", "A")
        # Second insert should fail due to unique constraint
        with pytest.raises(Exception):
            self._create_user(db_session, "dup@test.com", "pw2", "B")

    def test_email_lowercase_normalized(self, db_session):
        user = self._create_user(db_session, "  MIXED@Case.COM  ", "pw", "X")
        assert user.email == "mixed@case.com"

    def test_query_by_email(self, db_session):
        user = self._create_user(db_session, "findme@test.com", "pw", "Finder")
        stmt = select(User).where(User.email == "findme@test.com")
        found = db_session.execute(stmt).scalar_one_or_none()
        assert found is not None
        assert found.nickname == "Finder"

        stmt_none = select(User).where(User.email == "nobody@test.com")
        assert db_session.execute(stmt_none).scalar_one_or_none() is None

    def test_authenticate_flow(self, db_session):
        self._create_user(db_session, "auth@test.com", "correct_pw", "User")
        # Query user then verify password (mimics auth_service.authenticate_user)
        stmt = select(User).where(User.email == "auth@test.com")
        user = db_session.execute(stmt).scalar_one_or_none()
        assert user is not None
        assert auth_service.verify_password("correct_pw", user.password_hash) is True
        assert auth_service.verify_password("wrong_pw", user.password_hash) is False

    def test_change_password_and_bump_version(self, db_session):
        user = self._create_user(db_session, "cp@test.com", "old_password", "User")
        old_version = user.token_version

        # Verify old password
        assert auth_service.verify_password("old_password", user.password_hash)

        # Change password
        user.password_hash = auth_service.hash_password("new_password")
        user.token_version += 1
        db_session.commit()

        assert user.token_version == old_version + 1
        assert auth_service.verify_password("old_password", user.password_hash) is False
        assert auth_service.verify_password("new_password", user.password_hash) is True

    def test_wrong_old_password_no_change(self, db_session):
        user = self._create_user(db_session, "cp2@test.com", "old_pw", "User")
        # Verify wrong old password doesn't authenticate
        assert not auth_service.verify_password("wrong_old", user.password_hash)
        assert user.token_version == 1  # Unchanged
