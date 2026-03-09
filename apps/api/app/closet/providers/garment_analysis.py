from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.config import Settings, get_settings


@dataclass(frozen=True, slots=True)
class GarmentAnalysisError(Exception):
    code: str
    raw_response: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class GarmentAnalysisProviderResult:
    extraction: dict[str, Any]
    provider_name: str
    provider_version: str
    raw_response: dict[str, object] | None = None


class GarmentAnalysisProvider(Protocol):
    name: str
    version: str

    async def analyze(self, *, image_url: str) -> GarmentAnalysisProviderResult:
        raise NotImplementedError


class MockGarmentAnalysisProvider:
    name = "mock_garment_analysis"
    version = "v1"

    async def analyze(self, *, image_url: str) -> GarmentAnalysisProviderResult:
        extraction: dict[str, Any] = {
            "category": None,
            "subcategory": None,
            "type_label": None,
            "primary_color": None,
            "secondary_colors": [],
            "material": None,
            "pattern": None,
            "brand": None,
            "sleeve_length": None,
            "fit": None,
            "formality_level": None,
            "seasons": [],
            "occasions": [],
            "style_tags": [],
            "notes": None,
            "candidates": {},
        }
        return GarmentAnalysisProviderResult(
            extraction=extraction,
            provider_name=self.name,
            provider_version=self.version,
            raw_response={"mode": "mock", "image_url": image_url},
        )


class HttpGarmentAnalysisProvider:
    name = "http_garment_analysis"
    version = "v1"

    def __init__(
        self,
        *,
        endpoint_url: str,
        api_key: str | None,
        timeout_seconds: int,
        model: str | None,
    ) -> None:
        self._endpoint_url = endpoint_url
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._model = model

    async def analyze(self, *, image_url: str) -> GarmentAnalysisProviderResult:
        headers: dict[str, str] = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload: dict[str, Any] = {"image_url": image_url}
        if self._model:
            payload["model"] = self._model

        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.post(
                    self._endpoint_url,
                    json=payload,
                    headers=headers,
                )
        except httpx.TimeoutException as e:
            raise GarmentAnalysisError(code="garment_provider_timeout") from e
        except httpx.HTTPError as e:
            raise GarmentAnalysisError(code="garment_provider_unreachable") from e

        if response.status_code >= 400:
            raise GarmentAnalysisError(
                code="garment_provider_failed",
                raw_response={"status_code": response.status_code, "body": response.text[:1000]},
            )

        try:
            response_json = response.json()
        except ValueError as e:
            raise GarmentAnalysisError(code="garment_provider_invalid_response") from e

        if not isinstance(response_json, dict):
            raise GarmentAnalysisError(
                code="garment_provider_invalid_response",
                raw_response={"response_type": type(response_json).__name__},
            )

        extraction = response_json.get("extraction", response_json)
        if not isinstance(extraction, dict):
            raise GarmentAnalysisError(
                code="garment_provider_invalid_response",
                raw_response={"status_code": response.status_code, "body": response.text[:1000]},
            )

        return GarmentAnalysisProviderResult(
            extraction=extraction,
            provider_name=self.name,
            provider_version=self.version,
            raw_response=response_json,
        )


def build_garment_analysis_provider(settings: Settings | None = None) -> GarmentAnalysisProvider:
    current = settings or get_settings()
    mode = current.closet_garment_analysis_provider.strip().lower()

    if mode == "mock":
        return MockGarmentAnalysisProvider()

    if mode == "http":
        if not current.closet_garment_analysis_endpoint_url:
            raise GarmentAnalysisError(code="garment_provider_not_configured")
        return HttpGarmentAnalysisProvider(
            endpoint_url=current.closet_garment_analysis_endpoint_url,
            api_key=current.closet_garment_analysis_api_key,
            timeout_seconds=current.closet_garment_analysis_timeout_seconds,
            model=current.closet_garment_analysis_model,
        )

    raise GarmentAnalysisError(code="garment_provider_not_supported", raw_response={"mode": mode})
