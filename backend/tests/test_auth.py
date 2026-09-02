def _login(client, email, password):
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_login_ok(client):
    r = client.post("/auth/login", json={"email": "admin@peblo.local", "password": "peblo-admin"})
    assert r.status_code == 200
    assert r.json()["role"] == "admin"


def test_login_bad_password(client):
    r = client.post("/auth/login", json={"email": "admin@peblo.local", "password": "nope"})
    assert r.status_code == 401


def test_editor_cannot_publish(client):
    token = _login(client, "editor@peblo.local", "peblo-editor")
    r = client.post("/admin/catalog/publish", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert "admin" in r.json()["detail"].lower()


def test_editor_can_create_show(client):
    token = _login(client, "editor@peblo.local", "peblo-editor")
    r = client.post(
        "/admin/shows",
        json={"title": "Test Show", "section": "series", "status": "draft"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    assert r.json()["slug"] == "test-show"


def test_cannot_publish_show_without_section(client):
    token = _login(client, "editor@peblo.local", "peblo-editor")
    r = client.post(
        "/admin/shows",
        json={"title": "No Section", "status": "published"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400


def test_unauthenticated_cms_blocked(client):
    r = client.get("/admin/shows")
    assert r.status_code == 401


def test_duplicate_content_group_language_rejected(client):
    token = _login(client, "editor@peblo.local", "peblo-editor")
    headers = {"Authorization": f"Bearer {token}"}
    show = client.post(
        "/admin/shows",
        json={"title": "Dup Show", "section": "series", "status": "draft"},
        headers=headers,
    ).json()
    a = client.post(
        f"/admin/shows/{show['id']}/episodes",
        json={
            "title": "Ep 1",
            "season_number": 1,
            "episode_number": 1,
            "language": "en",
            "content_group": "dup-g",
            "duration_seconds": 120,
            "status": "draft",
        },
        headers=headers,
    )
    assert a.status_code == 201
    b = client.post(
        f"/admin/shows/{show['id']}/episodes",
        json={
            "title": "Ep 1 hi",
            "season_number": 1,
            "episode_number": 1,
            "language": "en",
            "content_group": "dup-g",
            "duration_seconds": 120,
            "status": "draft",
        },
        headers=headers,
    )
    assert b.status_code == 409


def test_admin_can_publish(client):
    token = _login(client, "admin@peblo.local", "peblo-admin")
    r = client.post("/admin/catalog/publish", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["status"] == "success"
    cat = client.get("/catalog")
    assert cat.status_code == 200
    assert "sections" in cat.json()
