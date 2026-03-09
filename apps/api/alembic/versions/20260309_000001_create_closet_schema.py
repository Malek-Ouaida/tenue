"""create closet schema

Revision ID: 20260309_000001
Revises: 20260123_000001
Create Date: 2026-03-09 14:20:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260309_000001"
down_revision = "20260123_000001"
branch_labels = None
depends_on = None


closet_item_status = postgresql.ENUM(
    "draft",
    "processing",
    "processed",
    "confirmed",
    "failed",
    name="closet_item_status",
    create_type=False,
)

closet_field_source = postgresql.ENUM(
    "ai",
    "user",
    "ai_then_user_edited",
    name="closet_field_source",
    create_type=False,
)

closet_sleeve_length = postgresql.ENUM(
    "sleeveless",
    "short",
    "three_quarter",
    "long",
    name="closet_sleeve_length",
    create_type=False,
)

closet_fit = postgresql.ENUM(
    "slim",
    "regular",
    "relaxed",
    "oversized",
    "tailored",
    name="closet_fit",
    create_type=False,
)

closet_processing_run_status = postgresql.ENUM(
    "started",
    "succeeded",
    "failed",
    name="closet_processing_run_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    closet_item_status.create(bind, checkfirst=True)
    closet_field_source.create(bind, checkfirst=True)
    closet_sleeve_length.create(bind, checkfirst=True)
    closet_fit.create(bind, checkfirst=True)
    closet_processing_run_status.create(bind, checkfirst=True)

    op.create_table(
        "closet_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_closet_categories_slug", "closet_categories", ["slug"], unique=True)

    op.create_table(
        "closet_subcategories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("closet_categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_closet_subcategories_slug", "closet_subcategories", ["slug"], unique=True)
    op.create_index("ix_closet_subcategories_category_id", "closet_subcategories", ["category_id"], unique=False)

    op.create_table(
        "closet_colors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_closet_colors_slug", "closet_colors", ["slug"], unique=True)

    op.create_table(
        "closet_materials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_closet_materials_slug", "closet_materials", ["slug"], unique=True)

    op.create_table(
        "closet_patterns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_closet_patterns_slug", "closet_patterns", ["slug"], unique=True)

    op.create_table(
        "closet_seasons",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_closet_seasons_slug", "closet_seasons", ["slug"], unique=True)

    op.create_table(
        "closet_occasions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_closet_occasions_slug", "closet_occasions", ["slug"], unique=True)

    op.create_table(
        "closet_formality_levels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=80), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_closet_formality_levels_slug", "closet_formality_levels", ["slug"], unique=True)
    op.create_index("ix_closet_formality_levels_rank", "closet_formality_levels", ["rank"], unique=True)

    op.create_table(
        "closet_style_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_closet_style_tags_slug", "closet_style_tags", ["slug"], unique=True)

    op.create_table(
        "closet_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_status", closet_item_status, nullable=False, server_default=sa.text("'draft'")),
        sa.Column("original_image_key", sa.String(length=512), nullable=False),
        sa.Column("processed_image_key", sa.String(length=512), nullable=True),
        sa.Column("thumbnail_key", sa.String(length=512), nullable=True),
        sa.Column("original_image_meta_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("processed_image_meta_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("thumbnail_meta_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("closet_categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "subcategory_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("closet_subcategories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("type_label", sa.String(length=60), nullable=True),
        sa.Column(
            "primary_color_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("closet_colors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "material_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("closet_materials.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "pattern_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("closet_patterns.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("brand", sa.String(length=80), nullable=True),
        sa.Column("sleeve_length", closet_sleeve_length, nullable=True),
        sa.Column("fit", closet_fit, nullable=True),
        sa.Column(
            "formality_level_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("closet_formality_levels.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("ai_provider", sa.String(length=64), nullable=True),
        sa.Column("ai_provider_version", sa.String(length=64), nullable=True),
        sa.Column("ai_raw_response_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("processing_attempt_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.Column("last_error_message", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "processing_attempt_count >= 0",
            name="ck_closet_items_processing_attempt_count_nonnegative",
        ),
    )
    op.create_index("ix_closet_items_user_id", "closet_items", ["user_id"], unique=False)
    op.create_index("ix_closet_items_category_id", "closet_items", ["category_id"], unique=False)
    op.create_index("ix_closet_items_subcategory_id", "closet_items", ["subcategory_id"], unique=False)
    op.create_index("ix_closet_items_primary_color_id", "closet_items", ["primary_color_id"], unique=False)
    op.create_index("ix_closet_items_material_id", "closet_items", ["material_id"], unique=False)
    op.create_index("ix_closet_items_pattern_id", "closet_items", ["pattern_id"], unique=False)
    op.create_index("ix_closet_items_formality_level_id", "closet_items", ["formality_level_id"], unique=False)
    op.create_index(
        "ix_closet_items_user_status_created_id",
        "closet_items",
        ["user_id", "item_status", "created_at", "id"],
        unique=False,
    )
    op.create_index(
        "ix_closet_items_user_created_id",
        "closet_items",
        ["user_id", "created_at", "id"],
        unique=False,
    )
    op.create_index(
        "ix_closet_items_active_user_created_id",
        "closet_items",
        ["user_id", "created_at", "id"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "closet_item_secondary_colors",
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("closet_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "color_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("closet_colors.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("item_id", "color_id"),
    )
    op.create_index(
        "ix_closet_item_secondary_colors_color_id",
        "closet_item_secondary_colors",
        ["color_id"],
        unique=False,
    )

    op.create_table(
        "closet_item_seasons",
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("closet_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "season_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("closet_seasons.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("item_id", "season_id"),
    )
    op.create_index("ix_closet_item_seasons_season_id", "closet_item_seasons", ["season_id"], unique=False)

    op.create_table(
        "closet_item_occasions",
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("closet_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "occasion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("closet_occasions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("item_id", "occasion_id"),
    )
    op.create_index(
        "ix_closet_item_occasions_occasion_id",
        "closet_item_occasions",
        ["occasion_id"],
        unique=False,
    )

    op.create_table(
        "closet_item_style_tags",
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("closet_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "style_tag_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("closet_style_tags.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("item_id", "style_tag_id"),
    )
    op.create_index(
        "ix_closet_item_style_tags_style_tag_id",
        "closet_item_style_tags",
        ["style_tag_id"],
        unique=False,
    )

    op.create_table(
        "closet_item_field_states",
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("closet_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("field_name", sa.String(length=64), nullable=False),
        sa.Column("value_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source", closet_field_source, nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("is_user_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("candidates_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_closet_item_field_states_confidence_0_1",
        ),
        sa.PrimaryKeyConstraint("item_id", "field_name"),
    )
    op.create_index("ix_closet_item_field_states_item_id", "closet_item_field_states", ["item_id"], unique=False)
    op.create_index(
        "ix_closet_item_field_states_needs_review",
        "closet_item_field_states",
        ["needs_review"],
        unique=False,
    )

    op.create_table(
        "closet_processing_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("closet_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stage", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("provider_version", sa.String(length=64), nullable=True),
        sa.Column("status", closet_processing_run_status, nullable=False, server_default=sa.text("'started'")),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("raw_response_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_closet_processing_runs_item_id", "closet_processing_runs", ["item_id"], unique=False)
    op.create_index(
        "ix_closet_processing_runs_item_started_at",
        "closet_processing_runs",
        ["item_id", "started_at"],
        unique=False,
    )
    op.create_index(
        "ix_closet_processing_runs_item_stage_started_at",
        "closet_processing_runs",
        ["item_id", "stage", "started_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_closet_processing_runs_item_stage_started_at", table_name="closet_processing_runs")
    op.drop_index("ix_closet_processing_runs_item_started_at", table_name="closet_processing_runs")
    op.drop_index("ix_closet_processing_runs_item_id", table_name="closet_processing_runs")
    op.drop_table("closet_processing_runs")

    op.drop_index("ix_closet_item_field_states_needs_review", table_name="closet_item_field_states")
    op.drop_index("ix_closet_item_field_states_item_id", table_name="closet_item_field_states")
    op.drop_table("closet_item_field_states")

    op.drop_index("ix_closet_item_style_tags_style_tag_id", table_name="closet_item_style_tags")
    op.drop_table("closet_item_style_tags")

    op.drop_index("ix_closet_item_occasions_occasion_id", table_name="closet_item_occasions")
    op.drop_table("closet_item_occasions")

    op.drop_index("ix_closet_item_seasons_season_id", table_name="closet_item_seasons")
    op.drop_table("closet_item_seasons")

    op.drop_index("ix_closet_item_secondary_colors_color_id", table_name="closet_item_secondary_colors")
    op.drop_table("closet_item_secondary_colors")

    op.drop_index("ix_closet_items_active_user_created_id", table_name="closet_items")
    op.drop_index("ix_closet_items_user_created_id", table_name="closet_items")
    op.drop_index("ix_closet_items_user_status_created_id", table_name="closet_items")
    op.drop_index("ix_closet_items_formality_level_id", table_name="closet_items")
    op.drop_index("ix_closet_items_pattern_id", table_name="closet_items")
    op.drop_index("ix_closet_items_material_id", table_name="closet_items")
    op.drop_index("ix_closet_items_primary_color_id", table_name="closet_items")
    op.drop_index("ix_closet_items_subcategory_id", table_name="closet_items")
    op.drop_index("ix_closet_items_category_id", table_name="closet_items")
    op.drop_index("ix_closet_items_user_id", table_name="closet_items")
    op.drop_table("closet_items")

    op.drop_index("ix_closet_style_tags_slug", table_name="closet_style_tags")
    op.drop_table("closet_style_tags")

    op.drop_index("ix_closet_formality_levels_rank", table_name="closet_formality_levels")
    op.drop_index("ix_closet_formality_levels_slug", table_name="closet_formality_levels")
    op.drop_table("closet_formality_levels")

    op.drop_index("ix_closet_occasions_slug", table_name="closet_occasions")
    op.drop_table("closet_occasions")

    op.drop_index("ix_closet_seasons_slug", table_name="closet_seasons")
    op.drop_table("closet_seasons")

    op.drop_index("ix_closet_patterns_slug", table_name="closet_patterns")
    op.drop_table("closet_patterns")

    op.drop_index("ix_closet_materials_slug", table_name="closet_materials")
    op.drop_table("closet_materials")

    op.drop_index("ix_closet_colors_slug", table_name="closet_colors")
    op.drop_table("closet_colors")

    op.drop_index("ix_closet_subcategories_category_id", table_name="closet_subcategories")
    op.drop_index("ix_closet_subcategories_slug", table_name="closet_subcategories")
    op.drop_table("closet_subcategories")

    op.drop_index("ix_closet_categories_slug", table_name="closet_categories")
    op.drop_table("closet_categories")

    bind = op.get_bind()
    closet_processing_run_status.drop(bind, checkfirst=True)
    closet_fit.drop(bind, checkfirst=True)
    closet_sleeve_length.drop(bind, checkfirst=True)
    closet_field_source.drop(bind, checkfirst=True)
    closet_item_status.drop(bind, checkfirst=True)
