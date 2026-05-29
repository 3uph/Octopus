"""Create assets, scan_profiles, scan_jobs, tool_runs tables.

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-29
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ASSET_TYPE = ("domain", "subdomain", "ip", "url", "cloud", "mobile")
_SCOPE_DECISION = ("in", "out", "ambiguous", "blocked")
_RECON_MODE = ("passive", "medium", "active", "dry_run")
_JOB_STATUS = ("queued", "dry_run", "running", "done", "failed", "cancelled")


def _ts():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    op.execute(f"CREATE TYPE asset_type AS ENUM ({', '.join(repr(v) for v in _ASSET_TYPE)})")
    op.execute(f"CREATE TYPE scope_decision AS ENUM ({', '.join(repr(v) for v in _SCOPE_DECISION)})")
    op.execute(f"CREATE TYPE recon_mode AS ENUM ({', '.join(repr(v) for v in _RECON_MODE)})")
    op.execute(f"CREATE TYPE job_status AS ENUM ({', '.join(repr(v) for v in _JOB_STATUS)})")

    op.create_table(
        "assets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("program_id", UUID(as_uuid=True), sa.ForeignKey("programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("value", sa.String(1024), nullable=False),
        sa.Column("asset_type", sa.Enum(*_ASSET_TYPE, name="asset_type", create_type=False), nullable=False),
        sa.Column("parent_asset_id", UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("discovered_via", sa.String(128), nullable=True),
        sa.Column("first_seen", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("scope_decision", sa.Enum(*_SCOPE_DECISION, name="scope_decision", create_type=False), nullable=False, server_default="out"),
        sa.Column("score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("score_breakdown", JSONB, nullable=True),
        sa.Column("confidence", sa.Enum("high", "medium", "low", name="confidence", create_type=False), nullable=False, server_default="medium"),
        sa.Column("review_status", sa.Enum("auto", "requires_review", "confirmed", "rejected", name="review_status", create_type=False), nullable=False, server_default="auto"),
        sa.Column("tags", JSONB, nullable=True),
        *_ts(),
        sa.UniqueConstraint("program_id", "value", name="uq_asset_program_value"),
    )
    op.create_index("ix_assets_program_id", "assets", ["program_id"])
    op.create_index("ix_assets_value", "assets", ["value"])

    op.create_table(
        "scan_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("mode", sa.Enum(*_RECON_MODE, name="recon_mode", create_type=False), nullable=False),
        sa.Column("tools_enabled", JSONB, nullable=True),
        sa.Column("default_args", JSONB, nullable=True),
        sa.Column("rate_limits", JSONB, nullable=True),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default="false"),
        *_ts(),
    )

    op.create_table(
        "scan_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("program_id", UUID(as_uuid=True), sa.ForeignKey("programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("audit_id", UUID(as_uuid=True), sa.ForeignKey("audits.id", ondelete="SET NULL"), nullable=True),
        sa.Column("profile_id", UUID(as_uuid=True), sa.ForeignKey("scan_profiles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("mode", sa.Enum(*_RECON_MODE, name="recon_mode", create_type=False), nullable=False),
        sa.Column("status", sa.Enum(*_JOB_STATUS, name="job_status", create_type=False), nullable=False, server_default="queued"),
        sa.Column("targets", JSONB, nullable=True),
        sa.Column("requested_by", UUID(as_uuid=True), nullable=True),
        sa.Column("dry_run", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary", JSONB, nullable=True),
        *_ts(),
    )
    op.create_index("ix_scan_jobs_program_id", "scan_jobs", ["program_id"])

    op.create_table(
        "tool_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scan_job_id", UUID(as_uuid=True), sa.ForeignKey("scan_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool_name", sa.String(64), nullable=False),
        sa.Column("tool_version", sa.String(64), nullable=True),
        sa.Column("args_sanitized", JSONB, nullable=True),
        sa.Column("target_scope", JSONB, nullable=True),
        sa.Column("mode", sa.Enum(*_RECON_MODE, name="recon_mode", create_type=False), nullable=False),
        sa.Column("status", sa.Enum(*_JOB_STATUS, name="job_status", create_type=False), nullable=False, server_default="queued"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exit_code", sa.Integer, nullable=True),
        sa.Column("raw_output_path", sa.String(512), nullable=True),
        sa.Column("items_produced", sa.Integer, nullable=False, server_default="0"),
        sa.Column("blocked_by_scope", sa.Boolean, nullable=False, server_default="false"),
        *_ts(),
    )
    op.create_index("ix_tool_runs_scan_job_id", "tool_runs", ["scan_job_id"])


def downgrade() -> None:
    for t in ("tool_runs", "scan_jobs", "scan_profiles", "assets"):
        op.drop_table(t)
    for e in ("job_status", "recon_mode", "scope_decision", "asset_type"):
        op.execute(f"DROP TYPE IF EXISTS {e}")
