from io import BytesIO

from PIL import Image


def _img(w, h) -> bytes:
    buf = BytesIO()
    Image.new("RGB", (w, h), (40, 80, 120)).save(buf, format="JPEG", quality=80)
    return buf.getvalue()


def _upload(client, headers, path, kind, w, h):
    r = client.post(
        path,
        data={"kind": kind},
        files={"file": (f"{kind}.jpg", _img(w, h), "image/jpeg")},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_content_group_collapses_languages(client, admin_headers):
    show = client.post(
        "/admin/shows",
        json={
            "title": "Group Show",
            "section": "series",
            "status": "published",
            "categories": ["stories"],
        },
        headers=admin_headers,
    ).json()
    _upload(client, admin_headers, f"/admin/shows/{show['id']}/artwork", "poster", 600, 900)
    _upload(client, admin_headers, f"/admin/shows/{show['id']}/artwork", "banner", 1280, 720)
    _upload(client, admin_headers, f"/admin/shows/{show['id']}/artwork", "thumbnail", 640, 360)

    en = client.post(
        f"/admin/shows/{show['id']}/episodes",
        json={
            "title": "The Lost Kite",
            "season_number": 1,
            "episode_number": 1,
            "language": "en",
            "content_group": "group-show-s01e01",
            "duration_seconds": 420,
            "status": "published",
        },
        headers=admin_headers,
    ).json()
    hi = client.post(
        f"/admin/shows/{show['id']}/episodes",
        json={
            "title": "गुम पतंग",
            "season_number": 1,
            "episode_number": 1,
            "language": "hi",
            "content_group": "group-show-s01e01",
            "duration_seconds": 420,
            "status": "published",
        },
        headers=admin_headers,
    ).json()
    _upload(client, admin_headers, f"/admin/episodes/{en['id']}/artwork", "thumbnail", 640, 360)
    _upload(client, admin_headers, f"/admin/episodes/{hi['id']}/artwork", "thumbnail", 640, 360)

    pub = client.post("/admin/catalog/publish", headers=admin_headers)
    assert pub.status_code == 200, pub.text

    cat = client.get("/catalog").json()
    found = None
    for section in cat["sections"]:
        for s in section["shows"]:
            if s["slug"] == show["slug"]:
                found = s
    assert found is not None
    episodes = found["seasons"][0]["episodes"]
    assert len(episodes) == 1
    assert episodes[0]["content_group"] == "group-show-s01e01"
    assert episodes[0]["languages"] == ["en", "hi"]
    assert {v["language"] for v in episodes[0]["variants"]} == {"en", "hi"}
    by_slug = client.get(f"/catalog/shows/{show['slug']}")
    assert by_slug.status_code == 200
    assert by_slug.json()["id"] == found["id"]


def test_second_publish_is_idempotent(client, admin_headers):
    first = client.post("/admin/catalog/publish", headers=admin_headers)
    assert first.status_code == 200
    live = client.get("/catalog").json()
    published_at = live["published_at"]

    second = client.post("/admin/catalog/publish", headers=admin_headers)
    assert second.status_code == 200
    assert any("Idempotent" in w for w in second.json()["warnings"])

    again = client.get("/catalog").json()
    assert again["published_at"] == published_at
    assert again["show_count"] == live["show_count"]


def test_catalog_meta_is_public(client):
    r = client.get("/catalog/meta")
    assert r.status_code == 200
    body = r.json()
    assert "adventure" in body["categories"]
    assert "en" in body["languages"]


def test_missing_slug_is_404(client):
    missing = client.get("/catalog/shows/does-not-exist")
    assert missing.status_code == 404


def test_validation_report_includes_preview(client, admin_headers):
    r = client.get("/admin/validation-report", headers=admin_headers)
    assert r.status_code == 200
    body = r.json()
    assert "preview" in body
    assert "show_count" in body["preview"]
    assert "can_publish" in body
    assert "clean" in body
