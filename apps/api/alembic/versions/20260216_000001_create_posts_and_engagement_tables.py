"""create posts and engagement tables

Revision ID: 20260216_000001
Revises: 20260123_000001
Create Date: 2026-02-16 22:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260216_000001"
down_revision = "20260123_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("caption", sa.String(length=2000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.execute("CREATE INDEX ix_posts_author_created_id ON posts (author_id, created_at DESC, id DESC)")
    op.execute("CREATE INDEX ix_posts_created_id ON posts (created_at DESC, id DESC)")

    op.create_table(
        "post_media",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "post_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("key", sa.String(length=512), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.CheckConstraint('"order" >= 0', name="ck_post_media_order_nonnegative"),
        sa.CheckConstraint("width IS NULL OR width > 0", name="ck_post_media_width_positive"),
        sa.CheckConstraint("height IS NULL OR height > 0", name="ck_post_media_height_positive"),
        sa.UniqueConstraint("post_id", "order", name="uq_post_media_post_order"),
    )
    op.create_index("ix_post_media_post_order", "post_media", ["post_id", "order", "id"], unique=False)

    op.create_table(
        "post_likes",
        sa.Column(
            "post_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("post_id", "user_id", name="pk_post_likes"),
        sa.UniqueConstraint("post_id", "user_id", name="uq_post_likes_post_user"),
    )
    op.create_index("ix_post_likes_post_id", "post_likes", ["post_id"], unique=False)
    op.create_index("ix_post_likes_user_id", "post_likes", ["user_id"], unique=False)

    op.create_table(
        "post_saves",
        sa.Column(
            "post_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("post_id", "user_id", name="pk_post_saves"),
        sa.UniqueConstraint("post_id", "user_id", name="uq_post_saves_post_user"),
    )
    op.create_index("ix_post_saves_post_id", "post_saves", ["post_id"], unique=False)
    op.create_index("ix_post_saves_user_id", "post_saves", ["user_id"], unique=False)

    op.create_table(
        "post_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "post_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("body", sa.String(length=1000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.execute("CREATE INDEX ix_post_comments_post_created_id ON post_comments (post_id, created_at DESC, id DESC)")
    op.create_index("ix_post_comments_user_id", "post_comments", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_post_comments_user_id", table_name="post_comments")
    op.drop_index("ix_post_comments_post_created_id", table_name="post_comments")
    op.drop_table("post_comments")

    op.drop_index("ix_post_saves_user_id", table_name="post_saves")
    op.drop_index("ix_post_saves_post_id", table_name="post_saves")
    op.drop_table("post_saves")

    op.drop_index("ix_post_likes_user_id", table_name="post_likes")
    op.drop_index("ix_post_likes_post_id", table_name="post_likes")
    op.drop_table("post_likes")

    op.drop_index("ix_post_media_post_order", table_name="post_media")
    op.drop_table("post_media")

    op.drop_index("ix_posts_created_id", table_name="posts")
    op.drop_index("ix_posts_author_created_id", table_name="posts")
    op.drop_table("posts")
