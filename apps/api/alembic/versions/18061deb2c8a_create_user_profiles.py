"""create_user_profiles

Revision ID: 18061deb2c8a
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "18061deb2c8a"
down_revision = "5c87f7479010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("username", sa.String(length=20), nullable=False),
        sa.Column("display_name", sa.String(length=50), nullable=True),
        sa.Column("bio", sa.String(length=160), nullable=True),
        sa.Column("avatar_key", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_user_profiles_username", "user_profiles", ["username"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_user_profiles_username", table_name="user_profiles")
    op.drop_table("user_profiles")
