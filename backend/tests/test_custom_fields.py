import uuid


def _key(prefix="cf"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


BASE_FIELD = {
    "label_de": "Trinktemperatur",
    "label_en": "Serving Temperature",
    "field_type": "text",
    "sort_order": 0,
}

WINE = {
    "name": "Barolo Testino",
    "producer": "Testweingut",
    "vintage": 2018,
    "type": "red",
    "quantity": 2,
}


# ── Field CRUD ────────────────────────────────────────────────────────────────

def test_get_custom_fields_returns_list(client):
    r = client.get("/custom-fields")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_field_requires_auth(client):
    r = client.post("/custom-fields", json={**BASE_FIELD, "key": _key()})
    assert r.status_code == 401


def test_create_field(client, admin_headers):
    key = _key("create")
    r = client.post("/custom-fields", json={**BASE_FIELD, "key": key}, headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["key"] == key
    assert data["label_de"] == BASE_FIELD["label_de"]
    assert data["label_en"] == BASE_FIELD["label_en"]
    assert data["field_type"] == BASE_FIELD["field_type"]
    assert "id" in data


def test_create_field_duplicate_key_rejected(client, admin_headers):
    key = _key("dup")
    client.post("/custom-fields", json={**BASE_FIELD, "key": key}, headers=admin_headers)
    r = client.post("/custom-fields", json={**BASE_FIELD, "key": key}, headers=admin_headers)
    assert r.status_code == 400


def test_create_field_appears_in_list(client, admin_headers):
    key = _key("list")
    client.post("/custom-fields", json={**BASE_FIELD, "key": key}, headers=admin_headers)
    keys = [f["key"] for f in client.get("/custom-fields").json()]
    assert key in keys


def test_update_field(client, admin_headers):
    key = _key("upd")
    r = client.post("/custom-fields", json={**BASE_FIELD, "key": key}, headers=admin_headers)
    field_id = r.json()["id"]

    r2 = client.put(f"/custom-fields/{field_id}",
        json={"label_de": "Serviertemperatur", "field_type": "number"},
        headers=admin_headers,
    )
    assert r2.status_code == 200
    data = r2.json()
    assert data["label_de"] == "Serviertemperatur"
    assert data["field_type"] == "number"
    assert data["key"] == key  # key must not change


def test_update_field_requires_auth(client, admin_headers):
    key = _key("upd_auth")
    r = client.post("/custom-fields", json={**BASE_FIELD, "key": key}, headers=admin_headers)
    field_id = r.json()["id"]
    r2 = client.put(f"/custom-fields/{field_id}", json={"label_de": "Hacked"})
    assert r2.status_code == 401


def test_delete_field(client, admin_headers):
    key = _key("del")
    r = client.post("/custom-fields", json={**BASE_FIELD, "key": key}, headers=admin_headers)
    field_id = r.json()["id"]

    r2 = client.delete(f"/custom-fields/{field_id}", headers=admin_headers)
    assert r2.status_code == 200

    ids = [f["id"] for f in client.get("/custom-fields").json()]
    assert field_id not in ids


def test_delete_nonexistent_field(client, admin_headers):
    r = client.delete("/custom-fields/999999", headers=admin_headers)
    assert r.status_code == 404


# ── Custom values on wines ────────────────────────────────────────────────────

def test_wine_custom_values_in_response(client, admin_headers):
    key = _key("val")
    client.post("/custom-fields", json={**BASE_FIELD, "key": key}, headers=admin_headers)

    r = client.post("/wines",
        json={**WINE, "name": f"WineCV_{key}", "custom_values": {key: "16–18°C"}},
        headers=admin_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert "custom_values" in data
    assert data["custom_values"][key] == "16–18°C"


def test_wine_list_includes_custom_values(client, admin_headers):
    key = _key("list_val")
    client.post("/custom-fields", json={**BASE_FIELD, "key": key}, headers=admin_headers)
    wine_name = f"ListTestWein_{key}"
    client.post("/wines",
        json={**WINE, "name": wine_name, "custom_values": {key: "14°C"}},
        headers=admin_headers,
    )
    wines = client.get("/wines").json()
    target = next((w for w in wines if w["name"] == wine_name), None)
    assert target is not None
    assert target["custom_values"][key] == "14°C"


def test_update_wine_custom_values(client, admin_headers):
    key = _key("upd_val")
    client.post("/custom-fields", json={**BASE_FIELD, "key": key}, headers=admin_headers)
    r = client.post("/wines",
        json={**WINE, "name": f"WineUpdCV_{key}", "custom_values": {key: "15°C"}},
        headers=admin_headers,
    )
    wine_id = r.json()["id"]

    r2 = client.put(f"/wines/{wine_id}",
        json={"custom_values": {key: "17°C"}},
        headers=admin_headers,
    )
    assert r2.status_code == 200
    assert r2.json()["custom_values"][key] == "17°C"


def test_delete_field_cascades_values(client, admin_headers):
    key = _key("casc")
    r = client.post("/custom-fields", json={**BASE_FIELD, "key": key}, headers=admin_headers)
    field_id = r.json()["id"]
    wine_name = f"CascadeWein_{key}"
    client.post("/wines",
        json={**WINE, "name": wine_name, "custom_values": {key: "15°C"}},
        headers=admin_headers,
    )

    client.delete(f"/custom-fields/{field_id}", headers=admin_headers)

    wines = client.get("/wines").json()
    target = next((w for w in wines if w["name"] == wine_name), None)
    assert target is not None
    assert target["custom_values"].get(key) is None


def test_delete_wine_removes_custom_values(client, admin_headers):
    key = _key("del_wine")
    client.post("/custom-fields", json={**BASE_FIELD, "key": key}, headers=admin_headers)
    r = client.post("/wines",
        json={**WINE, "name": f"DeleteWine_{key}", "custom_values": {key: "14°C"}},
        headers=admin_headers,
    )
    wine_id = r.json()["id"]

    client.delete(f"/wines/{wine_id}", headers=admin_headers)

    ids = [w["id"] for w in client.get("/wines").json()]
    assert wine_id not in ids


def test_wine_without_custom_values_has_empty_dict(client, admin_headers):
    r = client.post("/wines", json={**WINE, "name": "NoCustomWein"}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["custom_values"] == {}
