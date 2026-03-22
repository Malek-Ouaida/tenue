from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.closet.normalization.rules import (
    CATEGORY_SYNONYMS,
    COLOR_SYNONYMS,
    FORMALITY_SYNONYMS,
    MATERIAL_SYNONYMS,
    OCCASION_SYNONYMS,
    PATTERN_SYNONYMS,
    SEASON_SYNONYMS,
    STYLE_TAG_SYNONYMS,
    SUBCATEGORY_SYNONYMS,
)
from app.closet.normalization.text import normalize_lookup_key
from app.closet.normalization.types import TaxonomySubcategoryValue, TaxonomyValue
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


@dataclass(frozen=True, slots=True)
class ClosetTaxonomyCatalogError(Exception):
    code: str


@dataclass(frozen=True, slots=True)
class ClosetTaxonomyCatalog:
    categories_by_slug: dict[str, TaxonomyValue]
    categories_by_id: dict[uuid.UUID, TaxonomyValue]
    category_lookup: dict[str, TaxonomyValue]
    subcategories_by_slug: dict[str, TaxonomySubcategoryValue]
    subcategory_lookup: dict[str, TaxonomySubcategoryValue]
    colors_by_slug: dict[str, TaxonomyValue]
    color_lookup: dict[str, TaxonomyValue]
    materials_by_slug: dict[str, TaxonomyValue]
    material_lookup: dict[str, TaxonomyValue]
    patterns_by_slug: dict[str, TaxonomyValue]
    pattern_lookup: dict[str, TaxonomyValue]
    seasons_by_slug: dict[str, TaxonomyValue]
    season_lookup: dict[str, TaxonomyValue]
    occasions_by_slug: dict[str, TaxonomyValue]
    occasion_lookup: dict[str, TaxonomyValue]
    formality_by_slug: dict[str, TaxonomyValue]
    formality_lookup: dict[str, TaxonomyValue]
    style_tags_by_slug: dict[str, TaxonomyValue]
    style_tag_lookup: dict[str, TaxonomyValue]

    def match_category(self, value: str) -> TaxonomyValue | None:
        return self.category_lookup.get(normalize_lookup_key(value))

    def match_subcategory(self, value: str) -> TaxonomySubcategoryValue | None:
        return self.subcategory_lookup.get(normalize_lookup_key(value))

    def match_color(self, value: str) -> TaxonomyValue | None:
        return self.color_lookup.get(normalize_lookup_key(value))

    def match_material(self, value: str) -> TaxonomyValue | None:
        return self.material_lookup.get(normalize_lookup_key(value))

    def match_pattern(self, value: str) -> TaxonomyValue | None:
        return self.pattern_lookup.get(normalize_lookup_key(value))

    def match_season(self, value: str) -> TaxonomyValue | None:
        return self.season_lookup.get(normalize_lookup_key(value))

    def match_occasion(self, value: str) -> TaxonomyValue | None:
        return self.occasion_lookup.get(normalize_lookup_key(value))

    def match_formality_level(self, value: str) -> TaxonomyValue | None:
        return self.formality_lookup.get(normalize_lookup_key(value))

    def match_style_tag(self, value: str) -> TaxonomyValue | None:
        return self.style_tag_lookup.get(normalize_lookup_key(value))


def _to_taxonomy_value(model: object) -> TaxonomyValue:
    return TaxonomyValue(id=model.id, slug=model.slug, label=model.label)


def _build_lookup(
    values: list[TaxonomyValue],
    *,
    synonyms: dict[str, str],
) -> tuple[dict[str, TaxonomyValue], dict[str, TaxonomyValue]]:
    by_slug = {value.slug: value for value in values}
    lookup: dict[str, TaxonomyValue] = {}

    for value in values:
        lookup[normalize_lookup_key(value.slug)] = value
        lookup[normalize_lookup_key(value.label)] = value

    for raw_value, slug in synonyms.items():
        match = by_slug.get(slug)
        if match is not None:
            lookup[normalize_lookup_key(raw_value)] = match

    return by_slug, lookup


def load_taxonomy_catalog(db: Session) -> ClosetTaxonomyCatalog:
    try:
        categories = [
            _to_taxonomy_value(row)
            for row in db.execute(select(ClosetCategory).order_by(ClosetCategory.slug)).scalars().all()
        ]
        colors = [
            _to_taxonomy_value(row)
            for row in db.execute(select(ClosetColor).order_by(ClosetColor.slug)).scalars().all()
        ]
        materials = [
            _to_taxonomy_value(row)
            for row in db.execute(select(ClosetMaterial).order_by(ClosetMaterial.slug)).scalars().all()
        ]
        patterns = [
            _to_taxonomy_value(row)
            for row in db.execute(select(ClosetPattern).order_by(ClosetPattern.slug)).scalars().all()
        ]
        seasons = [
            _to_taxonomy_value(row)
            for row in db.execute(select(ClosetSeason).order_by(ClosetSeason.slug)).scalars().all()
        ]
        occasions = [
            _to_taxonomy_value(row)
            for row in db.execute(select(ClosetOccasion).order_by(ClosetOccasion.slug)).scalars().all()
        ]
        formality_levels = [
            _to_taxonomy_value(row)
            for row in db.execute(select(ClosetFormalityLevel).order_by(ClosetFormalityLevel.rank)).scalars().all()
        ]
        style_tags = [
            _to_taxonomy_value(row)
            for row in db.execute(select(ClosetStyleTag).order_by(ClosetStyleTag.slug)).scalars().all()
        ]
        subcategory_rows = db.execute(
            select(ClosetSubcategory, ClosetCategory.slug)
            .join(ClosetCategory, ClosetCategory.id == ClosetSubcategory.category_id)
            .order_by(ClosetSubcategory.slug)
        ).all()
    except SQLAlchemyError as e:
        raise ClosetTaxonomyCatalogError(code="taxonomy_load_failed") from e

    subcategories = [
        TaxonomySubcategoryValue(
            id=subcategory.id,
            slug=subcategory.slug,
            label=subcategory.label,
            category_id=subcategory.category_id,
            category_slug=category_slug,
        )
        for subcategory, category_slug in subcategory_rows
    ]

    categories_by_slug, category_lookup = _build_lookup(categories, synonyms=CATEGORY_SYNONYMS)
    colors_by_slug, color_lookup = _build_lookup(colors, synonyms=COLOR_SYNONYMS)
    materials_by_slug, material_lookup = _build_lookup(materials, synonyms=MATERIAL_SYNONYMS)
    patterns_by_slug, pattern_lookup = _build_lookup(patterns, synonyms=PATTERN_SYNONYMS)
    seasons_by_slug, season_lookup = _build_lookup(seasons, synonyms=SEASON_SYNONYMS)
    occasions_by_slug, occasion_lookup = _build_lookup(occasions, synonyms=OCCASION_SYNONYMS)
    formality_by_slug, formality_lookup = _build_lookup(formality_levels, synonyms=FORMALITY_SYNONYMS)
    style_tags_by_slug, style_tag_lookup = _build_lookup(style_tags, synonyms=STYLE_TAG_SYNONYMS)

    subcategories_by_slug = {value.slug: value for value in subcategories}
    subcategory_lookup: dict[str, TaxonomySubcategoryValue] = {}
    for value in subcategories:
        subcategory_lookup[normalize_lookup_key(value.slug)] = value
        subcategory_lookup[normalize_lookup_key(value.label)] = value
    for raw_value, slug in SUBCATEGORY_SYNONYMS.items():
        match = subcategories_by_slug.get(slug)
        if match is not None:
            subcategory_lookup[normalize_lookup_key(raw_value)] = match

    return ClosetTaxonomyCatalog(
        categories_by_slug=categories_by_slug,
        categories_by_id={value.id: value for value in categories},
        category_lookup=category_lookup,
        subcategories_by_slug=subcategories_by_slug,
        subcategory_lookup=subcategory_lookup,
        colors_by_slug=colors_by_slug,
        color_lookup=color_lookup,
        materials_by_slug=materials_by_slug,
        material_lookup=material_lookup,
        patterns_by_slug=patterns_by_slug,
        pattern_lookup=pattern_lookup,
        seasons_by_slug=seasons_by_slug,
        season_lookup=season_lookup,
        occasions_by_slug=occasions_by_slug,
        occasion_lookup=occasion_lookup,
        formality_by_slug=formality_by_slug,
        formality_lookup=formality_lookup,
        style_tags_by_slug=style_tags_by_slug,
        style_tag_lookup=style_tag_lookup,
    )
