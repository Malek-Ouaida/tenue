from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError

from app.closet.providers.garment_analysis import (
    GarmentAnalysisError,
    GarmentAnalysisProvider,
)
from app.closet.schemas import GarmentAnalysisExtraction


@dataclass(frozen=True, slots=True)
class GarmentAnalysisServiceError(Exception):
    code: str
    raw_response: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class GarmentAnalysisServiceResult:
    extraction: GarmentAnalysisExtraction
    provider_name: str
    provider_version: str
    raw_response: dict[str, object] | None


async def analyze_garment(
    *,
    image_url: str,
    provider: GarmentAnalysisProvider,
) -> GarmentAnalysisServiceResult:
    try:
        result = await provider.analyze(image_url=image_url)
    except GarmentAnalysisError as e:
        raise GarmentAnalysisServiceError(code=e.code, raw_response=e.raw_response) from e

    try:
        extraction = GarmentAnalysisExtraction.model_validate(result.extraction)
    except ValidationError as e:
        raise GarmentAnalysisServiceError(
            code="garment_analysis_invalid_response",
            raw_response={
                "validation_errors": e.errors(include_url=False),
                "provider_raw_response": result.raw_response,
            },
        ) from e

    return GarmentAnalysisServiceResult(
        extraction=extraction,
        provider_name=result.provider_name,
        provider_version=result.provider_version,
        raw_response=result.raw_response,
    )
