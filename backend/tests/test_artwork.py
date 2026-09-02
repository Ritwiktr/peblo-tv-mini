from io import BytesIO

import pytest
from PIL import Image

from app.services.artwork import ArtworkError, validate_image


def _img(w, h, fmt="JPEG") -> bytes:
    buf = BytesIO()
    Image.new("RGB", (w, h), (40, 80, 120)).save(buf, format=fmt, quality=80)
    return buf.getvalue()


def test_poster_good():
    meta = validate_image(_img(600, 900), "poster", "poster.jpg")
    assert meta["width"] == 600
    assert meta["height"] == 900


def test_banner_good():
    meta = validate_image(_img(1280, 720), "banner", "banner.jpg")
    assert meta["kind"] == "banner"


def test_thumbnail_good():
    validate_image(_img(640, 360), "thumbnail", "t.jpg")


def test_wrong_ratio_is_human_readable():
    with pytest.raises(ArtworkError) as exc:
        validate_image(_img(900, 600), "poster", "poster.jpg")
    assert "2:3" in exc.value.message
    assert exc.value.code == "wrong_ratio"


def test_too_large():
    # Uncompressed-ish PNG will blow the 200 KB ceiling at 1280x720 with noise
    buf = BytesIO()
    Image.new("RGB", (1280, 720), (1, 2, 3)).save(buf, format="PNG")
    # PNG of flat color is small — force the byte check directly
    data = b"x" * (201 * 1024)
    with pytest.raises(ArtworkError) as exc:
        validate_image(data, "banner", "banner.png")
    assert exc.value.code == "file_too_large"
    assert "KB" in exc.value.message


def test_tiny_rejected():
    with pytest.raises(ArtworkError):
        validate_image(_img(64, 36), "thumbnail", "t.jpg")
