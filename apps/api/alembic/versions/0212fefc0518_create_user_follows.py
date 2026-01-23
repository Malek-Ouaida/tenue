"""create user_follows

Revision ID: 0212fefc0518
Revises: 18061deb2c8a
Create Date: 2026-01-23 12:15:21.743190

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260123_000001"
down_revision = "18061deb2c8a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_follows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "follower_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "following_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "follower_user_id <> following_user_id",
            name="ck_user_follows_no_self_follow",
        ),
        sa.UniqueConstraint(
            "follower_user_id",
            "following_user_id",
            name="uq_user_follows_pair",
        ),
    )

    # For "following" lists
    op.create_index(
        "ix_user_follows_follower_created_id",
        "user_follows",
        ["follower_user_id", "created_at", "id"],
        unique=False,
    )

    # For "followers" lists
    op.create_index(
        "ix_user_follows_following_created_id",
        "user_follows",
        ["following_user_id", "created_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_follows_following_created_id", table_name="user_follows")
    op.drop_index("ix_user_follows_follower_created_id", table_name="user_follows")
    op.drop_table("user_follows")