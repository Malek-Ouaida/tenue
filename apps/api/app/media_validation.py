from __future__ import annotations

from dataclasses import dataclass


class MediaValidationError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class ImageMetadata:
    content_type: str
    extension: str
    width: int
    height: int


_JPEG_SOF_MARKERS = {
    0xC0,
    0xC1,
    0xC2,
    0xC3,
    0xC5,
    0xC6,
    0xC7,
    0xC9,
    0xCA,
    0xCB,
    0xCD,
    0xCE,
    0xCF,
}


def _parse_png_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 24:
        raise MediaValidationError("invalid_image")
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    if width < 1 or height < 1:
        raise MediaValidationError("invalid_image")
    return width, height


def _parse_jpeg_dimensions(data: bytes) -> tuple[int, int]:
    index = 2
    data_len = len(data)

    while index < data_len:
        while index < data_len and data[index] == 0xFF:
            index += 1
        if index >= data_len:
            break

        marker = data[index]
        index += 1

        if marker in {0x01, 0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9}:
            continue

        if index + 2 > data_len:
            break

        segment_len = int.from_bytes(data[index : index + 2], "big")
        index += 2
        if segment_len < 2 or index + segment_len - 2 > data_len:
            break

        if marker in _JPEG_SOF_MARKERS:
            if segment_len < 7:
                break
            height = int.from_bytes(data[index + 1 : index + 3], "big")
            width = int.from_bytes(data[index + 3 : index + 5], "big")
            if width < 1 or height < 1:
                break
            return width, height

        index += segment_len - 2

    raise MediaValidationError("invalid_image")


def _parse_webp_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 30:
        raise MediaValidationError("invalid_image")

    chunk = data[12:16]
    if chunk == b"VP8X":
        width = 1 + int.from_bytes(data[24:27], "little")
        height = 1 + int.from_bytes(data[27:30], "little")
        if width < 1 or height < 1:
            raise MediaValidationError("invalid_image")
        return width, height

    if chunk == b"VP8L":
        if len(data) < 25 or data[20] != 0x2F:
            raise MediaValidationError("invalid_image")
        b0, b1, b2, b3 = data[21:25]
        width = 1 + (((b1 & 0x3F) << 8) | b0)
        height = 1 + (((b3 & 0x0F) << 10) | (b2 << 2) | ((b1 & 0xC0) >> 6))
        if width < 1 or height < 1:
            raise MediaValidationError("invalid_image")
        return width, height

    if chunk == b"VP8 ":
        if len(data) < 30:
            raise MediaValidationError("invalid_image")
        width = int.from_bytes(data[26:28], "little") & 0x3FFF
        height = int.from_bytes(data[28:30], "little") & 0x3FFF
        if width < 1 or height < 1:
            raise MediaValidationError("invalid_image")
        return width, height

    raise MediaValidationError("invalid_image")


def detect_image_metadata(data: bytes) -> ImageMetadata:
    if not data:
        raise MediaValidationError("empty_file")

    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        width, height = _parse_png_dimensions(data)
        return ImageMetadata(content_type="image/png", extension="png", width=width, height=height)

    if data.startswith(b"\xFF\xD8"):
        width, height = _parse_jpeg_dimensions(data)
        return ImageMetadata(content_type="image/jpeg", extension="jpg", width=width, height=height)

    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        width, height = _parse_webp_dimensions(data)
        return ImageMetadata(content_type="image/webp", extension="webp", width=width, height=height)

    raise MediaValidationError("unsupported_image_type")
