"""Create settings table.

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-29
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE setting_scope AS ENUM ('global', 'company', 'program')")
    op.create_table(
        "settings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "scope",
            sa.Enum("global", "company", "program", name="setting_scope", create_type=False),
            nullable=False,
        ),
        sa.Column("scope_id", UUID(as_uuid=True), nullable=True),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("value", JSONB, nullable=True),
        sa.Column("is_secret", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("scope", "scope_id", "key", name="uq_setting_scope_key"),
    )
    op.create_index("ix_settings_scope_id", "settings", ["scope_id"])


def downgrade() -> None:
    op.drop_index("ix_settings_scope_id", table_name="settings")
    op.drop_table("settings")
    op.execute("DROP TYPE IF EXISTS setting_scope")
