from __future__ import annotations

from dataclasses import dataclass

from app.closet.providers.background_removal import (
    BackgroundRemovalError,
    BackgroundRemovalProvider,
    BackgroundRemovalResult,
)
from app.media_validation import MediaValidationError, detect_image_metadata


@dataclass(frozen=True, slots=True)
class ImageProcessingError(Exception):
    code: str
    raw_response: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ImageAsset:
    content_type: str
    extension: str
    width: int
    height: int
    size_bytes: int
    image_bytes: bytes
    meta_json: dict[str, object]


@dataclass(frozen=True, slots=True)
class ImageProcessingResult:
    processed_image: ImageAsset
    thumbnail_image: ImageAsset
    provider_name: str
    provider_version: str
    provider_raw_response: dict[str, object] | None


def _build_asset(*, image_bytes: bytes, source: str) -> ImageAsset:
    try:
        metadata = detect_image_metadata(image_bytes)
    except MediaValidationError as e:
        raise ImageProcessingError(code=e.code) from e

    return ImageAsset(
        content_type=metadata.content_type,
        extension=metadata.extension,
        width=metadata.width,
        height=metadata.height,
        size_bytes=len(image_bytes),
        image_bytes=image_bytes,
        meta_json={
            "content_type": metadata.content_type,
            "extension": metadata.extension,
            "width": metadata.width,
            "height": metadata.height,
            "size_bytes": len(image_bytes),
            "source": source,
        },
    )


def _build_thumbnail_bytes(*, processed: BackgroundRemovalResult) -> bytes:
    # MVP fallback: produce a dedicated thumbnail artifact from processed bytes.
    # Real resizing can be swapped in without changing service contracts.
    return processed.image_bytes


async def process_image(
    *,
    image_bytes: bytes,
    content_type: str,
    provider: BackgroundRemovalProvider,
) -> ImageProcessingResult:
    try:
        processed = await provider.remove_background(
            image_bytes=image_bytes,
            content_type=content_type,
        )
    except BackgroundRemovalError as e:
        raise ImageProcessingError(code=e.code, raw_response=e.raw_response) from e

    processed_asset = _build_asset(image_bytes=processed.image_bytes, source="background_removal")
    thumbnail_bytes = _build_thumbnail_bytes(processed=processed)
    thumbnail_asset = _build_asset(image_bytes=thumbnail_bytes, source="thumbnail_generation")

    return ImageProcessingResult(
        processed_image=processed_asset,
        thumbnail_image=thumbnail_asset,
        provider_name=processed.provider_name,
        provider_version=processed.provider_version,
        provider_raw_response=processed.raw_response,
    )
