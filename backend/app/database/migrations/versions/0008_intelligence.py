"""Create corporate intelligence tables.

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-29
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ACTIONABILITY = (
    "technical_actionable", "contextual", "low_confidence",
    "requires_review", "possibly_out_of_scope", "sensitive",
)
_PROVIDER_KIND = ("cloud", "saas", "identity", "other")


def _ts():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def _conf_review():
    return [
        sa.Column("confidence", sa.Enum("high", "medium", "low", name="confidence", create_type=False), nullable=False, server_default="medium"),
        sa.Column("review_status", sa.Enum("auto", "requires_review", "confirmed", "rejected", name="review_status", create_type=False), nullable=False, server_default="requires_review"),
    ]


def _company_fk():
    return sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)


def upgrade() -> None:
    op.execute(f"CREATE TYPE actionability AS ENUM ({', '.join(repr(v) for v in _ACTIONABILITY)})")
    op.execute(f"CREATE TYPE provider_kind AS ENUM ({', '.join(repr(v) for v in _PROVIDER_KIND)})")

    op.create_table(
        "company_intelligence_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        _company_fk(),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("regions", JSONB, nullable=True),
        sa.Column("operating_countries", JSONB, nullable=True),
        sa.Column("last_refreshed_at", sa.DateTime(timezone=True), nullable=True),
        *_ts(),
        sa.UniqueConstraint("company_id", name="uq_intel_profile_company"),
    )

    op.create_table(
        "brands",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        _company_fk(),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        *_conf_review(), *_ts(),
    )

    op.create_table(
        "products",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        _company_fk(),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("public_url", sa.String(512), nullable=True),
        *_conf_review(), *_ts(),
    )

    op.create_table(
        "public_portals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        _company_fk(),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("portal_type", sa.String(64), nullable=True),
        *_conf_review(), *_ts(),
    )

    op.create_table(
        "technology_signals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        _company_fk(),
        sa.Column("technology", sa.String(128), nullable=False),
        sa.Column("evidence_type", sa.String(64), nullable=True),
        *_conf_review(), *_ts(),
    )

    op.create_table(
        "third_party_providers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        _company_fk(),
        sa.Column("provider_name", sa.String(256), nullable=False),
        sa.Column("kind", sa.Enum(*_PROVIDER_KIND, name="provider_kind", create_type=False), nullable=False, server_default="other"),
        sa.Column("exposes_surface", sa.Boolean, nullable=False, server_default="false"),
        *_conf_review(), *_ts(),
    )

    op.create_table(
        "intelligence_sources",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        _company_fk(),
        sa.Column("url", sa.String(1024), nullable=True),
        sa.Column("source_type", sa.String(64), nullable=True),
        sa.Column("reliability", sa.Enum("high", "medium", "low", name="confidence", create_type=False), nullable=False, server_default="medium"),
        *_ts(),
    )

    op.create_table(
        "intelligence_findings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        _company_fk(),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("actionability", sa.Enum(*_ACTIONABILITY, name="actionability", create_type=False), nullable=False, server_default="contextual"),
        sa.Column("source_id", UUID(as_uuid=True), sa.ForeignKey("intelligence_sources.id", ondelete="SET NULL"), nullable=True),
        *_conf_review(), *_ts(),
    )

    op.create_table(
        "intelligence_review_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        _company_fk(),
        sa.Column("finding_id", UUID(as_uuid=True), sa.ForeignKey("intelligence_findings.id", ondelete="CASCADE"), nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("status", sa.Enum("auto", "requires_review", "confirmed", "rejected", name="review_status", create_type=False), nullable=False, server_default="requires_review"),
        *_ts(),
    )

    for t in ("brands", "products", "public_portals", "technology_signals",
              "third_party_providers", "intelligence_sources",
              "intelligence_findings", "intelligence_review_items"):
        op.create_index(f"ix_{t}_company_id", t, ["company_id"])


def downgrade() -> None:
    for t in ("intelligence_review_items", "intelligence_findings", "intelligence_sources",
              "third_party_providers", "technology_signals", "public_portals",
              "products", "brands", "company_intelligence_profiles"):
        op.drop_table(t)
    for e in ("provider_kind", "actionability"):
        op.execute(f"DROP TYPE IF EXISTS {e}")
