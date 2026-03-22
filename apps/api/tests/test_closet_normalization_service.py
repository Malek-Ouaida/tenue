from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.closet.repositories.item_repository import ClosetItemRepository
from app.closet.schemas import GarmentAnalysisCandidate, GarmentAnalysisExtraction
from app.closet.services.normalization_service import (
    normalize_garment_analysis,
    persist_processed_metadata,
)
from app.models.closet_item import (
    ClosetFieldSource,
    ClosetFit,
    ClosetItemFieldState,
    ClosetItemOccasion,
    ClosetItemSecondaryColor,
    ClosetItemSeason,
    ClosetItemStatus,
    ClosetItemStyleTag,
    ClosetSleeveLength,
)
from app.models.closet_taxonomy import (
    ClosetCategory,
    ClosetColor,
    ClosetFormalityLevel,
    ClosetMaterial,
    ClosetOccasion,
    ClosetPattern,
    ClosetSeason,
    ClosetStyleTag,
    ClosetSubcategory,
)


def _get_or_create_taxonomy_row(
    db: Session,
    model: type[Any],
    *,
    slug: str,
    label: str,
    **extra: object,
) -> Any:
    existing = db.execute(select(model).where(model.slug == slug)).scalar_one_or_none()
    if existing is not None:
        return existing

    row = model(id=uuid.uuid4(), slug=slug, label=label, **extra)
    db.add(row)
    db.flush()
    return row


def _get_or_create_subcategory(
    db: Session,
    *,
    category_id: uuid.UUID,
    slug: str,
    label: str,
) -> ClosetSubcategory:
    existing = db.execute(select(ClosetSubcategory).where(ClosetSubcategory.slug == slug)).scalar_one_or_none()
    if existing is not None:
        return existing

    row = ClosetSubcategory(
        id=uuid.uuid4(),
        category_id=category_id,
        slug=slug,
        label=label,
    )
    db.add(row)
    db.flush()
    return row


def _ensure_closet_taxonomy(db: Session) -> dict[str, Any]:
    tops = _get_or_create_taxonomy_row(db, ClosetCategory, slug="tops", label="Tops")
    t_shirt = _get_or_create_subcategory(db, category_id=tops.id, slug="t_shirt", label="T-Shirt")
    hoodie = _get_or_create_subcategory(db, category_id=tops.id, slug="hoodie", label="Hoodie")

    gray = _get_or_create_taxonomy_row(db, ClosetColor, slug="gray", label="Gray")
    white = _get_or_create_taxonomy_row(db, ClosetColor, slug="white", label="White")
    red = _get_or_create_taxonomy_row(db, ClosetColor, slug="red", label="Red")
    cotton = _get_or_create_taxonomy_row(db, ClosetMaterial, slug="cotton", label="Cotton")
    striped = _get_or_create_taxonomy_row(db, ClosetPattern, slug="striped", label="Striped")
    autumn = _get_or_create_taxonomy_row(db, ClosetSeason, slug="autumn", label="Autumn")
    summer = _get_or_create_taxonomy_row(db, ClosetSeason, slug="summer", label="Summer")
    work = _get_or_create_taxonomy_row(db, ClosetOccasion, slug="work", label="Work")
    smart_casual = _get_or_create_taxonomy_row(
        db,
        ClosetFormalityLevel,
        slug="smart_casual",
        label="Smart Casual",
        rank=3,
    )
    minimalist = _get_or_create_taxonomy_row(db, ClosetStyleTag, slug="minimalist", label="Minimalist")
    streetwear = _get_or_create_taxonomy_row(db, ClosetStyleTag, slug="streetwear", label="Streetwear")

    return {
        "tops": tops,
        "t_shirt": t_shirt,
        "hoodie": hoodie,
        "gray": gray,
        "white": white,
        "red": red,
        "cotton": cotton,
        "striped": striped,
        "autumn": autumn,
        "summer": summer,
        "work": work,
        "smart_casual": smart_casual,
        "minimalist": minimalist,
        "streetwear": streetwear,
    }


def _field_states_by_name(db: Session, *, item_id: uuid.UUID) -> dict[str, ClosetItemFieldState]:
    rows = db.execute(
        select(ClosetItemFieldState).where(ClosetItemFieldState.item_id == item_id)
    ).scalars().all()
    return {row.field_name: row for row in rows}


def test_normalize_garment_analysis_maps_synonyms_and_derives_category(db: Session) -> None:
    taxonomy = _ensure_closet_taxonomy(db)

    normalized = normalize_garment_analysis(
        db,
        extraction=GarmentAnalysisExtraction(
            category="top",
            subcategory="tee",
            primary_color="grey",
            material="cotton",
            pattern="striped",
            brand="Acme",
            sleeve_length="short sleeve",
            fit="regular",
            formality_level="smart casual",
            candidates={
                "subcategory": [GarmentAnalysisCandidate(value="t-shirt", confidence=0.91)],
                "primary_color": [GarmentAnalysisCandidate(value="gray", confidence=0.86)],
                "secondary_colors": [
                    GarmentAnalysisCandidate(value="white", confidence=0.88),
                    GarmentAnalysisCandidate(value="black", confidence=0.53),
                ],
                "seasons": [
                    GarmentAnalysisCandidate(value="fall", confidence=0.81),
                    GarmentAnalysisCandidate(value="summer", confidence=0.62),
                ],
                "style_tags": [
                    GarmentAnalysisCandidate(value="streetwear", confidence=0.84),
                    GarmentAnalysisCandidate(value="minimal", confidence=0.78),
                ],
            },
        ),
    )

    assert normalized.category_id == taxonomy["tops"].id
    assert normalized.subcategory_id == taxonomy["t_shirt"].id
    assert normalized.type_label == "T-Shirt"
    assert normalized.primary_color_id == taxonomy["gray"].id
    assert normalized.secondary_color_ids == (taxonomy["white"].id,)
    assert normalized.material_id == taxonomy["cotton"].id
    assert normalized.pattern_id == taxonomy["striped"].id
    assert normalized.formality_level_id == taxonomy["smart_casual"].id
    assert normalized.sleeve_length == ClosetSleeveLength.SHORT
    assert normalized.fit == ClosetFit.REGULAR
    assert normalized.season_ids == (taxonomy["autumn"].id, taxonomy["summer"].id)
    assert normalized.style_tag_ids == (taxonomy["streetwear"].id, taxonomy["minimalist"].id)

    state_by_name = {state.field_name: state for state in normalized.field_states}
    assert state_by_name["category"].value_json == "tops"
    assert state_by_name["category"].needs_review is False
    assert state_by_name["type_label"].value_json == "T-Shirt"
    assert state_by_name["secondary_colors"].value_json == ["white"]
    assert state_by_name["secondary_colors"].needs_review is False
    assert state_by_name["seasons"].value_json == ["autumn", "summer"]
    assert state_by_name["seasons"].needs_review is True


def test_normalize_garment_analysis_nulls_low_confidence_values_but_keeps_candidates(db: Session) -> None:
    _ensure_closet_taxonomy(db)

    normalized = normalize_garment_analysis(
        db,
        extraction=GarmentAnalysisExtraction(
            candidates={
                "subcategory": [GarmentAnalysisCandidate(value="sweatshirt", confidence=0.49)],
                "primary_color": [GarmentAnalysisCandidate(value="burgundy", confidence=0.42)],
                "pattern": [GarmentAnalysisCandidate(value="chevron", confidence=0.48)],
            },
        ),
    )

    assert normalized.subcategory_id is None
    assert normalized.primary_color_id is None
    assert normalized.pattern_id is None

    state_by_name = {state.field_name: state for state in normalized.field_states}

    assert state_by_name["subcategory"].value_json is None
    assert state_by_name["subcategory"].confidence == 0.49
    assert state_by_name["subcategory"].needs_review is False
    assert state_by_name["subcategory"].candidates_json[0]["canonical_slug"] == "hoodie"
    assert state_by_name["subcategory"].candidates_json[0]["reason"] == "below_threshold"

    assert state_by_name["primary_color"].value_json is None
    assert state_by_name["primary_color"].confidence == 0.42
    assert state_by_name["primary_color"].candidates_json[0]["canonical_slug"] == "red"
    assert state_by_name["primary_color"].candidates_json[0]["reason"] == "below_threshold"

    assert state_by_name["pattern"].value_json is None
    assert state_by_name["pattern"].confidence == 0.48
    assert state_by_name["pattern"].candidates_json[0]["reason"] == "no_taxonomy_match"


def test_persist_processed_metadata_updates_canonical_fields_and_field_states(
    db: Session,
    make_user,
) -> None:
    taxonomy = _ensure_closet_taxonomy(db)
    user = make_user("closet_norm")

    item = ClosetItemRepository.create_draft(
        db,
        item_id=uuid.uuid4(),
        user_id=user.id,
        original_image_key="closet/original.jpg",
        original_image_meta={"content_type": "image/jpeg"},
    )

    normalized = normalize_garment_analysis(
        db,
        extraction=GarmentAnalysisExtraction(
            subcategory="tee",
            primary_color="gray",
            material="cotton",
            formality_level="smart casual",
            candidates={
                "secondary_colors": [GarmentAnalysisCandidate(value="white", confidence=0.88)],
                "seasons": [GarmentAnalysisCandidate(value="fall", confidence=0.81)],
                "occasions": [GarmentAnalysisCandidate(value="work", confidence=0.77)],
                "style_tags": [GarmentAnalysisCandidate(value="streetwear", confidence=0.84)],
            },
        ),
    )

    updated = persist_processed_metadata(
        db,
        item=item,
        processed_image_key="closet/processed.png",
        processed_image_meta={"content_type": "image/png"},
        thumbnail_key="closet/thumbnail.png",
        thumbnail_meta={"content_type": "image/png"},
        ai_provider="mock_garment_analysis",
        ai_provider_version="v1",
        ai_raw_response={"normalized": normalized.to_debug_payload()},
        normalized_metadata=normalized,
    )

    assert updated.item_status == ClosetItemStatus.PROCESSED
    assert updated.category_id == taxonomy["tops"].id
    assert updated.subcategory_id == taxonomy["t_shirt"].id
    assert updated.type_label == "T-Shirt"
    assert updated.primary_color_id == taxonomy["gray"].id
    assert updated.material_id == taxonomy["cotton"].id
    assert updated.formality_level_id == taxonomy["smart_casual"].id
    assert updated.ai_raw_response_json["normalized"]["subcategory"]["value"] == "t_shirt"

    secondary_rows = db.execute(
        select(ClosetItemSecondaryColor).where(ClosetItemSecondaryColor.item_id == item.id)
    ).scalars().all()
    season_rows = db.execute(
        select(ClosetItemSeason).where(ClosetItemSeason.item_id == item.id)
    ).scalars().all()
    occasion_rows = db.execute(
        select(ClosetItemOccasion).where(ClosetItemOccasion.item_id == item.id)
    ).scalars().all()
    style_tag_rows = db.execute(
        select(ClosetItemStyleTag).where(ClosetItemStyleTag.item_id == item.id)
    ).scalars().all()

    assert [row.color_id for row in secondary_rows] == [taxonomy["white"].id]
    assert [row.season_id for row in season_rows] == [taxonomy["autumn"].id]
    assert [row.occasion_id for row in occasion_rows] == [taxonomy["work"].id]
    assert [row.style_tag_id for row in style_tag_rows] == [taxonomy["streetwear"].id]

    state_by_name = _field_states_by_name(db, item_id=item.id)
    assert len(state_by_name) == 15
    assert state_by_name["category"].value_json == "tops"
    assert state_by_name["category"].source == ClosetFieldSource.AI
    assert state_by_name["type_label"].value_json == "T-Shirt"
    assert state_by_name["type_label"].needs_review is False
