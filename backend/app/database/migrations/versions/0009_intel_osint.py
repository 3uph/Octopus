"""Create intel_osint run-based tables.

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-29
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def _afk():
    return sa.Column("analysis_id", UUID(as_uuid=True),
                     sa.ForeignKey("intel_analyses.id", ondelete="CASCADE"), nullable=False)


def upgrade() -> None:
    op.create_table(
        "intel_analyses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("target_company_name", sa.String(512), nullable=False),
        sa.Column("target_root_domain", sa.String(512), nullable=True),
        sa.Column("country", sa.String(8), nullable=False, server_default="ES"),
        sa.Column("nif", sa.String(32), nullable=True),
        sa.Column("aliases", JSONB, nullable=True),
        sa.Column("depth", sa.String(16), nullable=False, server_default="standard"),
        sa.Column("flags", JSONB, nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float, nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("summary_json", JSONB, nullable=True),
        sa.Column("exposure_score_json", JSONB, nullable=True),
        sa.Column("metadata_json", JSONB, nullable=True),
        *_ts(),
    )

    op.create_table(
        "intel_findings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        _afk(),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("value", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("source", sa.String(64), nullable=True),
        sa.Column("evidence_url", sa.String(1024), nullable=True),
        sa.Column("confidence", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("risk_level", sa.String(16), nullable=False, server_default="info"),
        sa.Column("tags", JSONB, nullable=True),
        sa.Column("raw_context_json", JSONB, nullable=True),
        *_ts(),
    )

    op.create_table(
        "intel_entities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        _afk(),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("value", sa.String(1024), nullable=False),
        sa.Column("normalized_value", sa.String(1024), nullable=False),
        sa.Column("confidence", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("source", sa.String(64), nullable=True),
        sa.Column("tags", JSONB, nullable=True),
        sa.Column("metadata_json", JSONB, nullable=True),
        *_ts(),
    )

    op.create_table(
        "intel_relationships",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        _afk(),
        sa.Column("source_entity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("target_entity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("source_value", sa.String(1024), nullable=True),
        sa.Column("target_value", sa.String(1024), nullable=True),
        sa.Column("relationship_type", sa.String(48), nullable=False),
        sa.Column("confidence", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("evidence", sa.Text, nullable=True),
        sa.Column("metadata_json", JSONB, nullable=True),
        *_ts(),
    )

    op.create_table(
        "intel_risk_hypotheses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        _afk(),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("risk_level", sa.String(16), nullable=False, server_default="info"),
        sa.Column("confidence", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("evidence_summary", sa.Text, nullable=True),
        sa.Column("why_it_matters", sa.Text, nullable=True),
        sa.Column("recommended_validation", sa.Text, nullable=True),
        sa.Column("recommended_remediation", sa.Text, nullable=True),
        sa.Column("related_findings_json", JSONB, nullable=True),
        sa.Column("related_entities_json", JSONB, nullable=True),
        sa.Column("tags", JSONB, nullable=True),
        *_ts(),
    )

    op.create_table(
        "intel_evidence",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        _afk(),
        sa.Column("finding_id", UUID(as_uuid=True), nullable=True),
        sa.Column("source", sa.String(64), nullable=True),
        sa.Column("url", sa.String(1024), nullable=True),
        sa.Column("content_excerpt", sa.Text, nullable=True),
        sa.Column("metadata_json", JSONB, nullable=True),
        *_ts(),
    )

    op.create_table(
        "intel_collector_status",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        _afk(),
        sa.Column("collector", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("items_produced", sa.Integer, nullable=False, server_default="0"),
        sa.Column("duration_seconds", sa.Float, nullable=True),
        sa.Column("message", sa.Text, nullable=True),
        *_ts(),
    )

    op.create_table(
        "intel_warnings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        _afk(),
        sa.Column("collector", sa.String(64), nullable=True),
        sa.Column("level", sa.String(16), nullable=False, server_default="warning"),
        sa.Column("message", sa.Text, nullable=False),
        *_ts(),
    )

    for t in ("intel_findings", "intel_entities", "intel_relationships",
              "intel_risk_hypotheses", "intel_evidence", "intel_collector_status",
              "intel_warnings"):
        op.create_index(f"ix_{t}_analysis_id", t, ["analysis_id"])


def downgrade() -> None:
    for t in ("intel_warnings", "intel_collector_status", "intel_evidence",
              "intel_risk_hypotheses", "intel_relationships", "intel_entities",
              "intel_findings", "intel_analyses"):
        op.drop_table(t)
