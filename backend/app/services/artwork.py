from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

from PIL import Image

DEFAULT_SPECS = {
    "poster": {"aspect": "2:3", "target_px": [600, 900], "max_kb": 200},
    "banner": {"aspect": "16:9", "target_px": [1280, 720], "max_kb": 200},
    "thumbnail": {"aspect": "16:9", "target_px": [640, 360], "max_kb": 200},
}

ALLOWED_KINDS = ("poster", "banner", "thumbnail")
ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}

# How far off aspect/size we tolerate. "~600×900" is not exact-pixel.
ASPECT_TOLERANCE = 0.04  # 4%
SIZE_TOLERANCE = 0.12  # 12%


class ArtworkError(Exception):
    def __init__(self, message: str, code: str = "invalid_artwork"):
        super().__init__(message)
        self.message = message
        self.code = code


def load_specs(reference_path: Path | None = None) -> dict:
    if reference_path and reference_path.exists():
        data = json.loads(reference_path.read_text())
        return data.get("artwork_specs", DEFAULT_SPECS)
    return DEFAULT_SPECS


def _parse_aspect(spec: str) -> float:
    a, b = spec.split(":")
    return float(a) / float(b)


def validate_image(data: bytes, kind: str, filename: str, specs: dict | None = None) -> dict:
    """Return {width, height, content_type} or raise ArtworkError with editor-facing copy."""
    specs = specs or DEFAULT_SPECS
    if kind not in ALLOWED_KINDS:
        raise ArtworkError(
            f"'{kind}' isn't a slot we use. Please upload a poster, banner, or thumbnail."
        )

    spec = specs[kind]
    max_bytes = spec["max_kb"] * 1024
    if len(data) > max_bytes:
        kb = round(len(data) / 1024)
        raise ArtworkError(
            f"This file is {kb} KB. {kind.capitalize()}s must be {spec['max_kb']} KB or smaller. "
            "Export a JPEG at medium quality and try again.",
            code="file_too_large",
        )
    if len(data) == 0:
        raise ArtworkError("That file looks empty. Please pick an image and try again.")

    try:
        img = Image.open(BytesIO(data))
        img.load()
    except Exception:
        raise ArtworkError(
            "We couldn't open that file as an image. Please upload a JPEG or PNG.",
            code="unreadable",
        )

    fmt = (img.format or "").upper()
    if fmt not in {"JPEG", "PNG", "WEBP"}:
        raise ArtworkError(
            f"This is a {fmt or 'unknown'} file. Please upload a JPEG or PNG.",
            code="bad_type",
        )

    width, height = img.size
    if width < 16 or height < 16:
        raise ArtworkError(
            f"This image is {width}×{height} pixels — too small to use. "
            f"A {kind} should be around {spec['target_px'][0]}×{spec['target_px'][1]}.",
            code="too_small",
        )

    target_w, target_h = spec["target_px"]
    expected_ratio = _parse_aspect(spec["aspect"])
    actual_ratio = width / height
    if abs(actual_ratio - expected_ratio) / expected_ratio > ASPECT_TOLERANCE:
        raise ArtworkError(
            f"This {kind} is {width}×{height} (about {_ratio_label(width, height)}). "
            f"Please upload a {spec['aspect']} image around {target_w}×{target_h} pixels.",
            code="wrong_ratio",
        )

    if abs(width - target_w) / target_w > SIZE_TOLERANCE or abs(height - target_h) / target_h > SIZE_TOLERANCE:
        raise ArtworkError(
            f"This {kind} is {width}×{height} pixels. Please use something close to "
            f"{target_w}×{target_h} (within about 12%).",
            code="wrong_size",
        )

    content_type = "image/jpeg" if fmt == "JPEG" else f"image/{fmt.lower()}"
    return {
        "width": width,
        "height": height,
        "content_type": content_type,
        "byte_size": len(data),
        "filename": filename,
        "kind": kind,
    }


def _ratio_label(w: int, h: int) -> str:
    # Reduce to a small integer ratio for the error message.
    a, b = w, h
    while b:
        a, b = b, a % b
    g = a or 1
    return f"{w // g}:{h // g}"
