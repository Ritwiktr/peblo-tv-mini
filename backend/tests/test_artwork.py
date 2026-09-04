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
    data = b"x" * (201 * 1024)
    with pytest.raises(ArtworkError) as exc:
        validate_image(data, "banner", "banner.png")
    assert exc.value.code == "file_too_large"
    assert "KB" in exc.value.message


def test_tiny_rejected():
    with pytest.raises(ArtworkError):
        validate_image(_img(64, 36), "thumbnail", "t.jpg")


def test_upload_wrong_ratio_returns_422(client, admin_headers):
    show = client.post(
        "/admin/shows",
        json={"title": "Art Check", "section": "series", "status": "draft"},
        headers=admin_headers,
    ).json()
    r = client.post(
        f"/admin/shows/{show['id']}/artwork",
        data={"kind": "poster"},
        files={"file": ("poster.jpg", _img(900, 600), "image/jpeg")},
        headers=admin_headers,
    )
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert detail["code"] == "wrong_ratio"
    assert "2:3" in detail["message"]


def test_upload_good_poster_accepted(client, admin_headers):
    show = client.post(
        "/admin/shows",
        json={"title": "Art Ok", "section": "series", "status": "draft"},
        headers=admin_headers,
    ).json()
    r = client.post(
        f"/admin/shows/{show['id']}/artwork",
        data={"kind": "poster"},
        files={"file": ("poster.jpg", _img(600, 900), "image/jpeg")},
        headers=admin_headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["width"] == 600
    assert r.json()["height"] == 900


def test_upload_banner_wrong_ratio_returns_422(client, admin_headers):
    show = client.post(
        "/admin/shows",
        json={"title": "Banner Check", "section": "series", "status": "draft"},
        headers=admin_headers,
    ).json()
    r = client.post(
        f"/admin/shows/{show['id']}/artwork",
        data={"kind": "banner"},
        files={"file": ("banner.jpg", _img(600, 900), "image/jpeg")},
        headers=admin_headers,
    )
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "wrong_ratio"


def test_upload_tiny_thumbnail_returns_422(client, admin_headers):
    show = client.post(
        "/admin/shows",
        json={"title": "Thumb Check", "section": "series", "status": "draft"},
        headers=admin_headers,
    ).json()
    r = client.post(
        f"/admin/shows/{show['id']}/artwork",
        data={"kind": "thumbnail"},
        files={"file": ("t.jpg", _img(64, 36), "image/jpeg")},
        headers=admin_headers,
    )
    assert r.status_code == 422
