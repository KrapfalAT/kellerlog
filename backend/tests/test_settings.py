def test_get_settings(client):
    r = client.get("/settings")
    assert r.status_code == 200
    data = r.json()
    assert "kiosk_enabled" in data
    assert "primary_color" in data
    assert "show_drink_window" in data
    assert "kiosk_show_drink_window" in data
    assert "dark_mode" in data


def test_update_settings_requires_auth(client):
    r = client.put("/settings", json={"kiosk_enabled": False})
    assert r.status_code == 401


def test_update_settings(client, admin_headers):
    r = client.put("/settings",
        json={"kiosk_title": "Meine Bar", "primary_color": "#123456"},
        headers=admin_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["kiosk_title"] == "Meine Bar"
    assert data["primary_color"] == "#123456"


def test_update_kiosk_enabled(client, admin_headers):
    r = client.put("/settings", json={"kiosk_enabled": False}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["kiosk_enabled"] is False

    r2 = client.put("/settings", json={"kiosk_enabled": True}, headers=admin_headers)
    assert r2.json()["kiosk_enabled"] is True


def test_update_drink_window_flags(client, admin_headers):
    r = client.put("/settings",
        json={"show_drink_window": False, "kiosk_show_drink_window": True},
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert r.json()["show_drink_window"] is False
    assert r.json()["kiosk_show_drink_window"] is True


def test_partial_update_preserves_other_fields(client, admin_headers):
    client.put("/settings", json={"app_title": "KellerTest"}, headers=admin_headers)
    r = client.put("/settings", json={"dark_mode": True}, headers=admin_headers)
    assert r.json()["app_title"] == "KellerTest"
    assert r.json()["dark_mode"] is True
