"""initial: users, jobs, subscriptions, applications, digest_queue

Revision ID: b29073199dae
Revises:
Create Date: 2026-06-01 15:57:44.257101
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b29073199dae'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extensions ──
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ── users ──
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("nickname", sa.String(100), nullable=True),
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ── jobs ──
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("company", sa.String(255), nullable=False),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("job_type", sa.String(50), nullable=True),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("skills", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("dedup_key", sa.String(64), unique=True, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True),
    )
    op.create_index("idx_jobs_posted_at", "jobs", ["posted_at"], postgresql_using=None)
    op.create_index("idx_jobs_job_type", "jobs", ["job_type"])
    op.create_index("idx_jobs_city", "jobs", ["city"])
    op.create_index("idx_jobs_skills", "jobs", ["skills"], postgresql_using="gin")
    op.create_index(
        "idx_jobs_is_active_posted",
        "jobs",
        ["is_active", "posted_at"],
        postgresql_where=sa.text("is_active = true"),
    )
    # pg_trgm indexes for Chinese fuzzy search
    op.create_index("idx_jobs_title_trgm", "jobs", ["title"], postgresql_using="gin", postgresql_ops={"title": "gin_trgm_ops"})
    op.create_index("idx_jobs_company_trgm", "jobs", ["company"], postgresql_using="gin", postgresql_ops={"company": "gin_trgm_ops"})

    # ── subscriptions ──
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("keywords", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("cities", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("job_types", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column(
            "frequency",
            sa.Enum("daily", "weekly", name="frequency_enum"),
            nullable=False,
            server_default="daily",
        ),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── applications ──
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("applied", "screening", "interview", "offer", "rejected", "closed", name="application_status_enum"),
            nullable=False,
            server_default="applied",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True),
    )
    op.create_index("idx_applications_user_status", "applications", ["user_id", "status"])

    # ── digest_queue ──
    op.create_table(
        "digest_queue",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("is_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("matched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_digest_queue_unique", "digest_queue", ["user_id", "job_id"], unique=True)


def downgrade() -> None:
    op.drop_table("digest_queue")
    op.execute("DROP TYPE IF EXISTS application_status_enum")
    op.drop_table("applications")
    op.drop_table("subscriptions")
    op.execute("DROP TYPE IF EXISTS frequency_enum")
    op.drop_table("jobs")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
