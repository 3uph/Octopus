"""Create scope entity tables: scope_items, out_of_scope_items, scope_rules, rate_limit_rules.

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-29
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SCOPE_KIND = ("domain", "wildcard", "url", "ip", "cidr", "asn", "mobile_app", "other")
_CONFIDENCE = ("high", "medium", "low")
_REVIEW_STATUS = ("auto", "requires_review", "confirmed", "rejected")


def upgrade() -> None:
    op.execute(f"CREATE TYPE scope_kind AS ENUM ({', '.join(repr(v) for v in _SCOPE_KIND)})")
    op.execute(f"CREATE TYPE confidence AS ENUM ({', '.join(repr(v) for v in _CONFIDENCE)})")
    op.execute(f"CREATE TYPE review_status AS ENUM ({', '.join(repr(v) for v in _REVIEW_STATUS)})")

    ts = lambda: [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]
    fk = lambda: sa.Column(
        "program_id", UUID(as_uuid=True),
        sa.ForeignKey("programs.id", ondelete="CASCADE"), nullable=False,
    )

    op.create_table(
        "scope_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        fk(),
        sa.Column("raw_value", sa.String(1024), nullable=False),
        sa.Column("normalized_value", sa.String(1024), nullable=False),
        sa.Column("kind", sa.Enum(*_SCOPE_KIND, name="scope_kind", create_type=False), nullable=False, server_default="other"),
        sa.Column("is_wildcard", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("confidence", sa.Enum(*_CONFIDENCE, name="confidence", create_type=False), nullable=False, server_default="medium"),
        sa.Column("review_status", sa.Enum(*_REVIEW_STATUS, name="review_status", create_type=False), nullable=False, server_default="auto"),
        sa.Column("source", sa.String(128), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        *ts(),
    )
    op.create_index("ix_scope_items_program_id", "scope_items", ["program_id"])
    op.create_index("ix_scope_items_normalized_value", "scope_items", ["normalized_value"])

    op.create_table(
        "out_of_scope_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        fk(),
        sa.Column("raw_value", sa.String(1024), nullable=False),
        sa.Column("normalized_value", sa.String(1024), nullable=False),
        sa.Column("kind", sa.Enum(*_SCOPE_KIND, name="scope_kind", create_type=False), nullable=False, server_default="other"),
        sa.Column("is_wildcard", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("source", sa.String(128), nullable=True),
        *ts(),
    )
    op.create_index("ix_out_of_scope_items_program_id", "out_of_scope_items", ["program_id"])
    op.create_index("ix_out_of_scope_items_normalized_value", "out_of_scope_items", ["normalized_value"])

    op.create_table(
        "scope_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        fk(),
        sa.Column("rule_type", sa.String(64), nullable=False),
        sa.Column("description_raw", sa.Text, nullable=True),
        sa.Column("parsed_summary", sa.Text, nullable=True),
        sa.Column("severity", sa.String(32), nullable=True),
        sa.Column("review_status", sa.Enum(*_REVIEW_STATUS, name="review_status", create_type=False), nullable=False, server_default="auto"),
        *ts(),
    )
    op.create_index("ix_scope_rules_program_id", "scope_rules", ["program_id"])

    op.create_table(
        "rate_limit_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        fk(),
        sa.Column("scope_pattern", sa.String(256), nullable=True),
        sa.Column("max_rps", sa.Float, nullable=True),
        sa.Column("max_concurrency", sa.Integer, nullable=True),
        sa.Column("window", sa.String(32), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("source", sa.String(128), nullable=True),
        *ts(),
    )
    op.create_index("ix_rate_limit_rules_program_id", "rate_limit_rules", ["program_id"])


def downgrade() -> None:
    for t in ("rate_limit_rules", "scope_rules", "out_of_scope_items", "scope_items"):
        op.drop_table(t)
    for e in ("review_status", "confidence", "scope_kind"):
        op.execute(f"DROP TYPE IF EXISTS {e}")
