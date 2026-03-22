from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.closet.normalization.catalog import ClosetTaxonomyCatalog
from app.closet.normalization.rules import (
    AUTO_ACCEPT_CONFIDENCE,
    FIT_SYNONYMS,
    IMPLICIT_CONFIDENCE,
    REVIEW_CONFIDENCE,
    SLEEVE_LENGTH_SYNONYMS,
)
from app.closet.normalization.text import normalize_lookup_key
from app.closet.normalization.types import (
    NormalizedClosetMetadata,
    NormalizedFieldStatePayload,
    TaxonomySubcategoryValue,
    TaxonomyValue,
)
from app.closet.schemas import GarmentAnalysisCandidate, GarmentAnalysisExtraction
from app.models.closet_item import ClosetFieldSource, ClosetFit, ClosetSleeveLength

_FIELD_NAMES = (
    "category",
    "subcategory",
    "type_label",
    "primary_color",
    "secondary_colors",
    "material",
    "pattern",
    "brand",
    "sleeve_length",
    "fit",
    "formality_level",
    "seasons",
    "occasions",
    "style_tags",
    "notes",
)

@dataclass(frozen=True, slots=True)
class _Suggestion:
    raw_value: str
    confidence: float
    source: str


@dataclass(frozen=True, slots=True)
class _SingleResolution:
    value: object | None
    confidence: float | None
    candidates_json: list[dict[str, object]]

    @property
    def needs_review(self) -> bool:
        return self.value is not None and self.confidence is not None and self.confidence < AUTO_ACCEPT_CONFIDENCE


@dataclass(frozen=True, slots=True)
class _MultiResolution:
    values: tuple[object, ...]
    confidence: float | None
    candidates_json: list[dict[str, object]]

    @property
    def needs_review(self) -> bool:
        return bool(self.values) and self.confidence is not None and self.confidence < AUTO_ACCEPT_CONFIDENCE


def _round_confidence(value: float | None) -> float | None:
    if value is None:
        return None
    bounded = max(0.0, min(1.0, value))
    return round(bounded, 3)


def _coalesce_suggestions(suggestions: list[_Suggestion]) -> list[_Suggestion]:
    deduped: dict[str, _Suggestion] = {}
    for suggestion in suggestions:
        lookup_key = normalize_lookup_key(suggestion.raw_value)
        if not lookup_key:
            continue

        current = deduped.get(lookup_key)
        if current is None:
            deduped[lookup_key] = suggestion
            continue

        if suggestion.confidence > current.confidence:
            deduped[lookup_key] = suggestion
            continue

        if suggestion.confidence == current.confidence and suggestion.source == "extraction":
            deduped[lookup_key] = suggestion

    return sorted(
        deduped.values(),
        key=lambda item: (-item.confidence, 0 if item.source == "extraction" else 1, normalize_lookup_key(item.raw_value)),
    )


def _build_scalar_suggestions(
    value: str | None,
    candidates: list[GarmentAnalysisCandidate],
) -> list[_Suggestion]:
    suggestions: list[_Suggestion] = []
    if value:
        suggestions.append(
            _Suggestion(
                raw_value=value,
                confidence=IMPLICIT_CONFIDENCE,
                source="extraction",
            )
        )

    for candidate in candidates:
        suggestions.append(
            _Suggestion(
                raw_value=candidate.value,
                confidence=candidate.confidence if candidate.confidence is not None else IMPLICIT_CONFIDENCE,
                source="candidate",
            )
        )

    return _coalesce_suggestions(suggestions)


def _build_list_suggestions(
    values: list[str],
    candidates: list[GarmentAnalysisCandidate],
) -> list[_Suggestion]:
    suggestions = [
        _Suggestion(
            raw_value=value,
            confidence=IMPLICIT_CONFIDENCE,
            source="extraction",
        )
        for value in values
    ]
    suggestions.extend(
        _Suggestion(
            raw_value=candidate.value,
            confidence=candidate.confidence if candidate.confidence is not None else IMPLICIT_CONFIDENCE,
            source="candidate",
        )
        for candidate in candidates
    )
    return _coalesce_suggestions(suggestions)


def _serialize_taxonomy_candidate(
    suggestion: _Suggestion,
    matched: TaxonomyValue | TaxonomySubcategoryValue | None,
    *,
    accepted: bool,
    reason: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "raw_value": suggestion.raw_value,
        "confidence": _round_confidence(suggestion.confidence),
        "source": suggestion.source,
        "accepted": accepted,
    }
    if matched is not None:
        payload["canonical_slug"] = matched.slug
        payload["canonical_label"] = matched.label
    if reason is not None:
        payload["reason"] = reason
    return payload


def _serialize_text_candidate(
    suggestion: _Suggestion,
    value: str | None,
    *,
    accepted: bool,
    reason: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "raw_value": suggestion.raw_value,
        "confidence": _round_confidence(suggestion.confidence),
        "source": suggestion.source,
        "accepted": accepted,
    }
    if value is not None:
        payload["normalized_value"] = value
    if reason is not None:
        payload["reason"] = reason
    return payload


def _resolve_single_taxonomy(
    value: str | None,
    candidates: list[GarmentAnalysisCandidate],
    matcher: Callable[[str], TaxonomyValue | TaxonomySubcategoryValue | None],
) -> _SingleResolution:
    suggestions = _build_scalar_suggestions(value, candidates)
    candidate_payloads: list[dict[str, object]] = []

    best_match: TaxonomyValue | TaxonomySubcategoryValue | None = None
    best_confidence: float | None = None
    best_any_confidence: float | None = None

    for suggestion in suggestions:
        matched = matcher(suggestion.raw_value)
        best_any_confidence = max(best_any_confidence or 0.0, suggestion.confidence)

        accepted = matched is not None and suggestion.confidence >= REVIEW_CONFIDENCE
        if accepted and best_match is None:
            best_match = matched
            best_confidence = suggestion.confidence

        reason = None
        if matched is None:
            reason = "no_taxonomy_match"
        elif not accepted:
            reason = "below_threshold"

        candidate_payloads.append(
            _serialize_taxonomy_candidate(
                suggestion,
                matched,
                accepted=accepted,
                reason=reason,
            )
        )

    return _SingleResolution(
        value=best_match,
        confidence=_round_confidence(best_confidence or best_any_confidence),
        candidates_json=candidate_payloads,
    )


def _resolve_multi_taxonomy(
    values: list[str],
    candidates: list[GarmentAnalysisCandidate],
    matcher: Callable[[str], TaxonomyValue | None],
) -> _MultiResolution:
    suggestions = _build_list_suggestions(values, candidates)
    accepted_by_slug: dict[str, tuple[TaxonomyValue, float]] = {}
    candidate_payloads: list[dict[str, object]] = []
    best_any_confidence: float | None = None

    for suggestion in suggestions:
        matched = matcher(suggestion.raw_value)
        best_any_confidence = max(best_any_confidence or 0.0, suggestion.confidence)
        accepted = matched is not None and suggestion.confidence >= REVIEW_CONFIDENCE

        if accepted and matched is not None:
            existing = accepted_by_slug.get(matched.slug)
            if existing is None or suggestion.confidence > existing[1]:
                accepted_by_slug[matched.slug] = (matched, suggestion.confidence)

        reason = None
        if matched is None:
            reason = "no_taxonomy_match"
        elif not accepted:
            reason = "below_threshold"

        candidate_payloads.append(
            _serialize_taxonomy_candidate(
                suggestion,
                matched,
                accepted=accepted,
                reason=reason,
            )
        )

    ordered_matches = sorted(
        accepted_by_slug.values(),
        key=lambda item: (-item[1], item[0].label),
    )
    confidence = _round_confidence(min((item[1] for item in ordered_matches), default=best_any_confidence))

    return _MultiResolution(
        values=tuple(item[0] for item in ordered_matches),
        confidence=confidence,
        candidates_json=candidate_payloads,
    )


def _normalize_spaces(value: str) -> str:
    return " ".join(value.strip().split())


def _sanitize_type_label(value: str) -> str | None:
    collapsed = _normalize_spaces(value)
    if not collapsed:
        return None
    return collapsed.title()[:60]


def _sanitize_brand(value: str) -> str | None:
    collapsed = _normalize_spaces(value)
    return collapsed[:80] or None


def _sanitize_notes(value: str) -> str | None:
    collapsed = _normalize_spaces(value)
    return collapsed[:500] or None


def _resolve_single_text(
    value: str | None,
    candidates: list[GarmentAnalysisCandidate],
    sanitizer: Callable[[str], str | None],
) -> _SingleResolution:
    suggestions = _build_scalar_suggestions(value, candidates)
    candidate_payloads: list[dict[str, object]] = []

    best_value: str | None = None
    best_confidence: float | None = None
    best_any_confidence: float | None = None

    for suggestion in suggestions:
        normalized_value = sanitizer(suggestion.raw_value)
        best_any_confidence = max(best_any_confidence or 0.0, suggestion.confidence)

        accepted = normalized_value is not None and suggestion.confidence >= REVIEW_CONFIDENCE
        if accepted and best_value is None:
            best_value = normalized_value
            best_confidence = suggestion.confidence

        reason = None
        if normalized_value is None:
            reason = "empty_value"
        elif not accepted:
            reason = "below_threshold"

        candidate_payloads.append(
            _serialize_text_candidate(
                suggestion,
                normalized_value,
                accepted=accepted,
                reason=reason,
            )
        )

    return _SingleResolution(
        value=best_value,
        confidence=_round_confidence(best_confidence or best_any_confidence),
        candidates_json=candidate_payloads,
    )


def _resolve_single_enum(
    value: str | None,
    candidates: list[GarmentAnalysisCandidate],
    mapping: dict[str, str],
) -> _SingleResolution:
    def _sanitize(raw_value: str) -> str | None:
        lookup_key = normalize_lookup_key(raw_value)
        if not lookup_key:
            return None
        if lookup_key in mapping:
            return mapping[lookup_key]
        return lookup_key if lookup_key in mapping.values() else None

    suggestions = _build_scalar_suggestions(value, candidates)
    candidate_payloads: list[dict[str, object]] = []

    best_value: str | None = None
    best_confidence: float | None = None
    best_any_confidence: float | None = None

    for suggestion in suggestions:
        normalized_value = _sanitize(suggestion.raw_value)
        best_any_confidence = max(best_any_confidence or 0.0, suggestion.confidence)

        accepted = normalized_value is not None and suggestion.confidence >= REVIEW_CONFIDENCE
        if accepted and best_value is None:
            best_value = normalized_value
            best_confidence = suggestion.confidence

        reason = None
        if normalized_value is None:
            reason = "invalid_enum_value"
        elif not accepted:
            reason = "below_threshold"

        candidate_payloads.append(
            _serialize_text_candidate(
                suggestion,
                normalized_value,
                accepted=accepted,
                reason=reason,
            )
        )

    return _SingleResolution(
        value=best_value,
        confidence=_round_confidence(best_confidence or best_any_confidence),
        candidates_json=candidate_payloads,
    )


def _build_field_state(
    *,
    field_name: str,
    value_json: object | None,
    confidence: float | None,
    needs_review: bool,
    candidates_json: list[dict[str, object]],
) -> NormalizedFieldStatePayload:
    return NormalizedFieldStatePayload(
        field_name=field_name,
        value_json=value_json,
        source=ClosetFieldSource.AI,
        confidence=_round_confidence(confidence),
        is_user_confirmed=False,
        needs_review=needs_review,
        candidates_json=candidates_json or [],
    )


def _candidate_for_derived_value(
    *,
    raw_value: str,
    matched: TaxonomyValue,
    confidence: float | None,
    accepted: bool,
    reason: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "raw_value": raw_value,
        "confidence": _round_confidence(confidence),
        "source": "derived",
        "accepted": accepted,
        "canonical_slug": matched.slug,
        "canonical_label": matched.label,
    }
    if reason is not None:
        payload["reason"] = reason
    return payload


def _filter_secondary_color_candidates(
    candidates: list[dict[str, object]],
    *,
    primary_color_slug: str | None,
) -> list[dict[str, object]]:
    if primary_color_slug is None:
        return candidates

    filtered: list[dict[str, object]] = []
    for candidate in candidates:
        canonical_slug = candidate.get("canonical_slug")
        if canonical_slug == primary_color_slug:
            updated = dict(candidate)
            updated["accepted"] = False
            updated["reason"] = "same_as_primary_color"
            filtered.append(updated)
            continue
        filtered.append(candidate)
    return filtered


def normalize_garment_metadata(
    *,
    extraction: GarmentAnalysisExtraction,
    catalog: ClosetTaxonomyCatalog,
) -> NormalizedClosetMetadata:
    field_candidates = extraction.candidates

    subcategory_result = _resolve_single_taxonomy(
        extraction.subcategory,
        field_candidates.get("subcategory", []),
        catalog.match_subcategory,
    )
    category_result = _resolve_single_taxonomy(
        extraction.category,
        field_candidates.get("category", []),
        catalog.match_category,
    )
    type_label_result = _resolve_single_text(
        extraction.type_label,
        field_candidates.get("type_label", []),
        _sanitize_type_label,
    )
    primary_color_result = _resolve_single_taxonomy(
        extraction.primary_color,
        field_candidates.get("primary_color", []),
        catalog.match_color,
    )
    secondary_colors_result = _resolve_multi_taxonomy(
        extraction.secondary_colors,
        field_candidates.get("secondary_colors", []),
        catalog.match_color,
    )
    material_result = _resolve_single_taxonomy(
        extraction.material,
        field_candidates.get("material", []),
        catalog.match_material,
    )
    pattern_result = _resolve_single_taxonomy(
        extraction.pattern,
        field_candidates.get("pattern", []),
        catalog.match_pattern,
    )
    brand_result = _resolve_single_text(
        extraction.brand,
        field_candidates.get("brand", []),
        _sanitize_brand,
    )
    sleeve_length_result = _resolve_single_enum(
        extraction.sleeve_length,
        field_candidates.get("sleeve_length", []),
        SLEEVE_LENGTH_SYNONYMS,
    )
    fit_result = _resolve_single_enum(
        extraction.fit,
        field_candidates.get("fit", []),
        FIT_SYNONYMS,
    )
    formality_result = _resolve_single_taxonomy(
        extraction.formality_level,
        field_candidates.get("formality_level", []),
        catalog.match_formality_level,
    )
    seasons_result = _resolve_multi_taxonomy(
        extraction.seasons,
        field_candidates.get("seasons", []),
        catalog.match_season,
    )
    occasions_result = _resolve_multi_taxonomy(
        extraction.occasions,
        field_candidates.get("occasions", []),
        catalog.match_occasion,
    )
    style_tags_result = _resolve_multi_taxonomy(
        extraction.style_tags,
        field_candidates.get("style_tags", []),
        catalog.match_style_tag,
    )
    notes_result = _resolve_single_text(
        extraction.notes,
        field_candidates.get("notes", []),
        _sanitize_notes,
    )

    accepted_subcategory = subcategory_result.value if isinstance(subcategory_result.value, TaxonomySubcategoryValue) else None
    accepted_category = category_result.value if isinstance(category_result.value, TaxonomyValue) else None

    category_value = accepted_category
    category_confidence = category_result.confidence
    category_needs_review = category_result.needs_review
    category_candidates_json = list(category_result.candidates_json)

    if accepted_subcategory is not None:
        derived_category = catalog.categories_by_id[accepted_subcategory.category_id]
        conflicting_explicit_category = (
            accepted_category is not None and accepted_category.slug != derived_category.slug and category_result.confidence is not None
        )
        category_value = derived_category
        category_confidence = _round_confidence(
            max(
                subcategory_result.confidence or 0.0,
                category_result.confidence or 0.0,
            )
        )
        category_needs_review = (
            conflicting_explicit_category
            or (category_value is not None and category_confidence is not None and category_confidence < AUTO_ACCEPT_CONFIDENCE)
        )
        category_candidates_json.insert(
            0,
            _candidate_for_derived_value(
                raw_value=accepted_subcategory.label,
                matched=derived_category,
                confidence=subcategory_result.confidence,
                accepted=True,
                reason="derived_from_subcategory",
            ),
        )

    derived_type_label = accepted_subcategory.label if accepted_subcategory is not None else None
    type_label_value = type_label_result.value if isinstance(type_label_result.value, str) else None
    type_label_confidence = type_label_result.confidence
    type_label_needs_review = type_label_result.needs_review
    type_label_candidates_json = list(type_label_result.candidates_json)

    if type_label_value is None and derived_type_label is not None:
        type_label_value = derived_type_label
        type_label_confidence = subcategory_result.confidence
        type_label_needs_review = type_label_confidence is not None and type_label_confidence < AUTO_ACCEPT_CONFIDENCE
        type_label_candidates_json.insert(
            0,
            {
                "raw_value": derived_type_label,
                "normalized_value": derived_type_label,
                "confidence": _round_confidence(type_label_confidence),
                "source": "derived",
                "accepted": True,
                "reason": "derived_from_subcategory",
            }
        )

    accepted_primary_color = primary_color_result.value if isinstance(primary_color_result.value, TaxonomyValue) else None
    filtered_secondary_values = tuple(
        value
        for value in secondary_colors_result.values
        if isinstance(value, TaxonomyValue) and value.slug != (accepted_primary_color.slug if accepted_primary_color else None)
    )
    secondary_color_candidates_json = _filter_secondary_color_candidates(
        list(secondary_colors_result.candidates_json),
        primary_color_slug=accepted_primary_color.slug if accepted_primary_color is not None else None,
    )

    secondary_color_confidence = secondary_colors_result.confidence
    secondary_color_needs_review = bool(filtered_secondary_values) and (
        secondary_color_confidence is not None and secondary_color_confidence < AUTO_ACCEPT_CONFIDENCE
    )

    sleeve_length_value = (
        ClosetSleeveLength(sleeve_length_result.value)
        if isinstance(sleeve_length_result.value, str)
        else None
    )
    fit_value = ClosetFit(fit_result.value) if isinstance(fit_result.value, str) else None

    field_states = (
        _build_field_state(
            field_name="category",
            value_json=category_value.slug if category_value is not None else None,
            confidence=category_confidence,
            needs_review=category_needs_review,
            candidates_json=category_candidates_json,
        ),
        _build_field_state(
            field_name="subcategory",
            value_json=accepted_subcategory.slug if accepted_subcategory is not None else None,
            confidence=subcategory_result.confidence,
            needs_review=subcategory_result.needs_review,
            candidates_json=subcategory_result.candidates_json,
        ),
        _build_field_state(
            field_name="type_label",
            value_json=type_label_value,
            confidence=type_label_confidence,
            needs_review=type_label_needs_review,
            candidates_json=type_label_candidates_json,
        ),
        _build_field_state(
            field_name="primary_color",
            value_json=accepted_primary_color.slug if accepted_primary_color is not None else None,
            confidence=primary_color_result.confidence,
            needs_review=primary_color_result.needs_review,
            candidates_json=primary_color_result.candidates_json,
        ),
        _build_field_state(
            field_name="secondary_colors",
            value_json=[value.slug for value in filtered_secondary_values] or None,
            confidence=secondary_color_confidence,
            needs_review=secondary_color_needs_review,
            candidates_json=secondary_color_candidates_json,
        ),
        _build_field_state(
            field_name="material",
            value_json=material_result.value.slug if isinstance(material_result.value, TaxonomyValue) else None,
            confidence=material_result.confidence,
            needs_review=material_result.needs_review,
            candidates_json=material_result.candidates_json,
        ),
        _build_field_state(
            field_name="pattern",
            value_json=pattern_result.value.slug if isinstance(pattern_result.value, TaxonomyValue) else None,
            confidence=pattern_result.confidence,
            needs_review=pattern_result.needs_review,
            candidates_json=pattern_result.candidates_json,
        ),
        _build_field_state(
            field_name="brand",
            value_json=brand_result.value if isinstance(brand_result.value, str) else None,
            confidence=brand_result.confidence,
            needs_review=brand_result.needs_review,
            candidates_json=brand_result.candidates_json,
        ),
        _build_field_state(
            field_name="sleeve_length",
            value_json=sleeve_length_value.value if sleeve_length_value is not None else None,
            confidence=sleeve_length_result.confidence,
            needs_review=sleeve_length_result.needs_review,
            candidates_json=sleeve_length_result.candidates_json,
        ),
        _build_field_state(
            field_name="fit",
            value_json=fit_value.value if fit_value is not None else None,
            confidence=fit_result.confidence,
            needs_review=fit_result.needs_review,
            candidates_json=fit_result.candidates_json,
        ),
        _build_field_state(
            field_name="formality_level",
            value_json=formality_result.value.slug if isinstance(formality_result.value, TaxonomyValue) else None,
            confidence=formality_result.confidence,
            needs_review=formality_result.needs_review,
            candidates_json=formality_result.candidates_json,
        ),
        _build_field_state(
            field_name="seasons",
            value_json=[value.slug for value in seasons_result.values] or None,
            confidence=seasons_result.confidence,
            needs_review=seasons_result.needs_review,
            candidates_json=seasons_result.candidates_json,
        ),
        _build_field_state(
            field_name="occasions",
            value_json=[value.slug for value in occasions_result.values] or None,
            confidence=occasions_result.confidence,
            needs_review=occasions_result.needs_review,
            candidates_json=occasions_result.candidates_json,
        ),
        _build_field_state(
            field_name="style_tags",
            value_json=[value.slug for value in style_tags_result.values] or None,
            confidence=style_tags_result.confidence,
            needs_review=style_tags_result.needs_review,
            candidates_json=style_tags_result.candidates_json,
        ),
        _build_field_state(
            field_name="notes",
            value_json=notes_result.value if isinstance(notes_result.value, str) else None,
            confidence=notes_result.confidence,
            needs_review=notes_result.needs_review,
            candidates_json=notes_result.candidates_json,
        ),
    )

    by_name = {state.field_name for state in field_states}
    missing_fields = set(_FIELD_NAMES) - by_name
    if missing_fields:
        raise ValueError(f"Missing normalized field states for: {sorted(missing_fields)}")

    return NormalizedClosetMetadata(
        category_id=category_value.id if category_value is not None else None,
        subcategory_id=accepted_subcategory.id if accepted_subcategory is not None else None,
        type_label=type_label_value,
        primary_color_id=accepted_primary_color.id if accepted_primary_color is not None else None,
        secondary_color_ids=tuple(value.id for value in filtered_secondary_values),
        material_id=material_result.value.id if isinstance(material_result.value, TaxonomyValue) else None,
        pattern_id=pattern_result.value.id if isinstance(pattern_result.value, TaxonomyValue) else None,
        brand=brand_result.value if isinstance(brand_result.value, str) else None,
        sleeve_length=sleeve_length_value,
        fit=fit_value,
        formality_level_id=formality_result.value.id if isinstance(formality_result.value, TaxonomyValue) else None,
        season_ids=tuple(value.id for value in seasons_result.values if isinstance(value, TaxonomyValue)),
        occasion_ids=tuple(value.id for value in occasions_result.values if isinstance(value, TaxonomyValue)),
        style_tag_ids=tuple(value.id for value in style_tags_result.values if isinstance(value, TaxonomyValue)),
        notes=notes_result.value if isinstance(notes_result.value, str) else None,
        field_states=field_states,
    )
