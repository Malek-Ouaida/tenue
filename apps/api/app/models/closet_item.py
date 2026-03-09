from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ClosetItemStatus(str, enum.Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    PROCESSED = "processed"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class ClosetFieldSource(str, enum.Enum):
    AI = "ai"
    USER = "user"
    AI_THEN_USER_EDITED = "ai_then_user_edited"


class ClosetSleeveLength(str, enum.Enum):
    SLEEVELESS = "sleeveless"
    SHORT = "short"
    THREE_QUARTER = "three_quarter"
    LONG = "long"


class ClosetFit(str, enum.Enum):
    SLIM = "slim"
    REGULAR = "regular"
    RELAXED = "relaxed"
    OVERSIZED = "oversized"
    TAILORED = "tailored"


class ClosetProcessingRunStatus(str, enum.Enum):
    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ClosetItem(Base):
    __tablename__ = "closet_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    item_status: Mapped[ClosetItemStatus] = mapped_column(
        Enum(ClosetItemStatus, name="closet_item_status"),
        nullable=False,
        server_default=ClosetItemStatus.DRAFT.value,
    )

    original_image_key: Mapped[str] = mapped_column(String(512), nullable=False)
    processed_image_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    thumbnail_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    original_image_meta_json: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    processed_image_meta_json: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    thumbnail_meta_json: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("closet_categories.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    subcategory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("closet_subcategories.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    type_label: Mapped[str | None] = mapped_column(String(60), nullable=True)
    primary_color_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("closet_colors.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    material_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("closet_materials.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    pattern_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("closet_patterns.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    brand: Mapped[str | None] = mapped_column(String(80), nullable=True)
    sleeve_length: Mapped[ClosetSleeveLength | None] = mapped_column(
        Enum(ClosetSleeveLength, name="closet_sleeve_length"),
        nullable=True,
    )
    fit: Mapped[ClosetFit | None] = mapped_column(
        Enum(ClosetFit, name="closet_fit"),
        nullable=True,
    )
    formality_level_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("closet_formality_levels.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    ai_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ai_provider_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ai_raw_response_json: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)

    processing_attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "processing_attempt_count >= 0",
            name="ck_closet_items_processing_attempt_count_nonnegative",
        ),
        Index(
            "ix_closet_items_user_status_created_id",
            "user_id",
            "item_status",
            "created_at",
            "id",
        ),
        Index("ix_closet_items_user_created_id", "user_id", "created_at", "id"),
        Index(
            "ix_closet_items_active_user_created_id",
            "user_id",
            "created_at",
            "id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )


class ClosetItemSecondaryColor(Base):
    __tablename__ = "closet_item_secondary_colors"

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("closet_items.id", ondelete="CASCADE"),
        primary_key=True,
    )
    color_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("closet_colors.id", ondelete="RESTRICT"),
        primary_key=True,
    )


class ClosetItemSeason(Base):
    __tablename__ = "closet_item_seasons"

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("closet_items.id", ondelete="CASCADE"),
        primary_key=True,
    )
    season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("closet_seasons.id", ondelete="RESTRICT"),
        primary_key=True,
    )


class ClosetItemOccasion(Base):
    __tablename__ = "closet_item_occasions"

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("closet_items.id", ondelete="CASCADE"),
        primary_key=True,
    )
    occasion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("closet_occasions.id", ondelete="RESTRICT"),
        primary_key=True,
    )


class ClosetItemStyleTag(Base):
    __tablename__ = "closet_item_style_tags"

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("closet_items.id", ondelete="CASCADE"),
        primary_key=True,
    )
    style_tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("closet_style_tags.id", ondelete="RESTRICT"),
        primary_key=True,
    )


class ClosetItemFieldState(Base):
    __tablename__ = "closet_item_field_states"

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("closet_items.id", ondelete="CASCADE"),
        primary_key=True,
    )
    field_name: Mapped[str] = mapped_column(String(64), primary_key=True)
    value_json: Mapped[object | None] = mapped_column(JSONB, nullable=True)
    source: Mapped[ClosetFieldSource] = mapped_column(
        Enum(ClosetFieldSource, name="closet_field_source"),
        nullable=False,
    )
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    is_user_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    needs_review: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    candidates_json: Mapped[object | None] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_closet_item_field_states_confidence_0_1",
        ),
        Index("ix_closet_item_field_states_item_id", "item_id"),
        Index("ix_closet_item_field_states_needs_review", "needs_review"),
    )


class ClosetProcessingRun(Base):
    __tablename__ = "closet_processing_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("closet_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[ClosetProcessingRunStatus] = mapped_column(
        Enum(ClosetProcessingRunStatus, name="closet_processing_run_status"),
        nullable=False,
        server_default=ClosetProcessingRunStatus.STARTED.value,
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_response_json: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_closet_processing_runs_item_started_at", "item_id", "started_at"),
        Index("ix_closet_processing_runs_item_stage_started_at", "item_id", "stage", "started_at"),
    )
