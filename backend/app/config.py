"""Application settings loaded from environment variables."""

import re
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:54322/internhub"

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def check_database_url(cls, v: str) -> str:
        """Validate and log DATABASE_URL (password masked)."""
        if not v.startswith("postgresql://") and not v.startswith("postgres://"):
            raise ValueError(
                f"DATABASE_URL must start with postgresql:// or postgres://, got: {v[:50]}..."
            )
        # Print masked URL for debugging
        masked = re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", v)
        print(f"[Config] DATABASE_URL = {masked}")
        return v

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production-use-a-random-64-char-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # Resend (email)
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "InternHub <noreply@internhub.app>"

    # Scraper
    SCRAPER_USER_AGENT: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )


settings = Settings()
