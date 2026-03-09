from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx

from app.config import Settings, get_settings
from app.media_validation import MediaValidationError, detect_image_metadata


@dataclass(frozen=True, slots=True)
class BackgroundRemovalError(Exception):
    code: str
    raw_response: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class BackgroundRemovalResult:
    image_bytes: bytes
    content_type: str
    extension: str
    provider_name: str
    provider_version: str
    raw_response: dict[str, object] | None = None


class BackgroundRemovalProvider(Protocol):
    name: str
    version: str

    async def remove_background(self, *, image_bytes: bytes, content_type: str) -> BackgroundRemovalResult:
        raise NotImplementedError


class MockBackgroundRemovalProvider:
    name = "mock_background_removal"
    version = "v1"

    async def remove_background(self, *, image_bytes: bytes, content_type: str) -> BackgroundRemovalResult:
        try:
            metadata = detect_image_metadata(image_bytes)
        except MediaValidationError as e:
            raise BackgroundRemovalError(code=e.code) from e

        return BackgroundRemovalResult(
            image_bytes=image_bytes,
            content_type=metadata.content_type,
            extension=metadata.extension,
            provider_name=self.name,
            provider_version=self.version,
            raw_response={"mode": "mock", "passthrough": True},
        )


class HttpBackgroundRemovalProvider:
    name = "http_background_removal"
    version = "v1"

    def __init__(self, *, endpoint_url: str, api_key: str | None, timeout_seconds: int) -> None:
        self._endpoint_url = endpoint_url
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    async def remove_background(self, *, image_bytes: bytes, content_type: str) -> BackgroundRemovalResult:
        headers: dict[str, str] = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.post(
                    self._endpoint_url,
                    files={"file": ("closet_item", image_bytes, content_type)},
                    headers=headers,
                )
        except httpx.TimeoutException as e:
            raise BackgroundRemovalError(code="background_provider_timeout") from e
        except httpx.HTTPError as e:
            raise BackgroundRemovalError(code="background_provider_unreachable") from e

        if response.status_code >= 400:
            raise BackgroundRemovalError(
                code="background_provider_failed",
                raw_response={"status_code": response.status_code, "body": response.text[:500]},
            )

        result_bytes = response.content
        if not result_bytes:
            raise BackgroundRemovalError(code="background_provider_empty_response")

        try:
            metadata = detect_image_metadata(result_bytes)
        except MediaValidationError as e:
            raise BackgroundRemovalError(code="background_provider_invalid_image") from e

        return BackgroundRemovalResult(
            image_bytes=result_bytes,
            content_type=metadata.content_type,
            extension=metadata.extension,
            provider_name=self.name,
            provider_version=self.version,
            raw_response={"status_code": response.status_code},
        )


def build_background_removal_provider(settings: Settings | None = None) -> BackgroundRemovalProvider:
    current = settings or get_settings()
    mode = current.closet_background_provider.strip().lower()

    if mode == "mock":
        return MockBackgroundRemovalProvider()

    if mode == "http":
        if not current.closet_background_remove_endpoint_url:
            raise BackgroundRemovalError(code="background_provider_not_configured")
        return HttpBackgroundRemovalProvider(
            endpoint_url=current.closet_background_remove_endpoint_url,
            api_key=current.closet_background_remove_api_key,
            timeout_seconds=current.closet_background_timeout_seconds,
        )

    raise BackgroundRemovalError(code="background_provider_not_supported", raw_response={"mode": mode})
