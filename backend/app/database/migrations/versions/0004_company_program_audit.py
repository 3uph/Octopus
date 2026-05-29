"""Create companies, programs, audits tables.

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-29
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PROGRAM_TYPES = ("external_audit", "bug_bounty", "osint", "surface_review", "private_program", "other")
_PROGRAM_PLATFORMS = ("hackerone", "bugcrowd", "intigriti", "private", "client", "other")
_PROGRAM_STATUSES = ("planning", "active", "paused", "closed")
_AUDIT_STATUSES = ("draft", "active", "completed", "archived")


def upgrade() -> None:
    for name, values in [
        ("program_type", _PROGRAM_TYPES),
        ("program_platform", _PROGRAM_PLATFORMS),
        ("program_status", _PROGRAM_STATUSES),
        ("audit_status", _AUDIT_STATUSES),
    ]:
        op.execute(f"CREATE TYPE {name} AS ENUM ({', '.join(repr(v) for v in values)})")

    op.create_table(
        "companies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name_legal", sa.String(256), nullable=False),
        sa.Column("name_commercial", sa.String(256), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "programs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("program_type", sa.Enum(*_PROGRAM_TYPES, name="program_type", create_type=False), nullable=False),
        sa.Column("platform", sa.Enum(*_PROGRAM_PLATFORMS, name="program_platform", create_type=False), nullable=False, server_default="other"),
        sa.Column("program_url", sa.String(512), nullable=True),
        sa.Column("status", sa.Enum(*_PROGRAM_STATUSES, name="program_status", create_type=False), nullable=False, server_default="planning"),
        sa.Column("scope_raw", sa.Text, nullable=True),
        sa.Column("scope_last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_programs_company_id", "programs", ["company_id"])

    op.create_table(
        "audits",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("program_id", UUID(as_uuid=True), sa.ForeignKey("programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("objective", sa.Text, nullable=True),
        sa.Column("status", sa.Enum(*_AUDIT_STATUSES, name="audit_status", create_type=False), nullable=False, server_default="draft"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audits_program_id", "audits", ["program_id"])


def downgrade() -> None:
    op.drop_index("ix_audits_program_id", table_name="audits")
    op.drop_table("audits")
    op.drop_index("ix_programs_company_id", table_name="programs")
    op.drop_table("programs")
    op.drop_table("companies")
    for t in ("audit_status", "program_status", "program_platform", "program_type"):
        op.execute(f"DROP TYPE IF EXISTS {t}")
