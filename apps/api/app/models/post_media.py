from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class PostMedia(Base):
    __tablename__ = "post_media"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    key: Mapped[str] = mapped_column(String(512), nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    order: Mapped[int] = mapped_column("order", Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("\"order\" >= 0", name="ck_post_media_order_nonnegative"),
        CheckConstraint("width IS NULL OR width > 0", name="ck_post_media_width_positive"),
        CheckConstraint("height IS NULL OR height > 0", name="ck_post_media_height_positive"),
        UniqueConstraint("post_id", "order", name="uq_post_media_post_order"),
        Index("ix_post_media_post_order", "post_id", "order", "id"),
    )
