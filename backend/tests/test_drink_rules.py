def test_get_drink_rules_returns_defaults(client):
    r = client.get("/drink-rules")
    assert r.status_code == 200
    rules = r.json()
    assert len(rules) == 6
    types = {r["wine_type"] for r in rules}
    assert types == {"red", "white", "rosé", "sparkling", "dessert", "other"}


def test_drink_rule_has_grape_field(client):
    rules = client.get("/drink-rules").json()
    for rule in rules:
        assert "grape" in rule


def test_create_rule_requires_auth(client):
    r = client.post("/drink-rules", json={"name": "Test", "wine_type": "red", "from_offset": 2, "to_offset": 8})
    assert r.status_code == 401


def test_create_rule(client, admin_headers):
    r = client.post("/drink-rules",
        json={"name": "Barolo", "wine_type": "red", "grape": "Nebbiolo", "from_offset": 5, "to_offset": 20},
        headers=admin_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Barolo"
    assert data["grape"] == "Nebbiolo"
    assert data["from_offset"] == 5
    assert data["to_offset"] == 20


def test_create_rule_any_type(client, admin_headers):
    r = client.post("/drink-rules",
        json={"name": "Generell", "wine_type": "", "from_offset": 1, "to_offset": 5},
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert r.json()["wine_type"] == ""


def test_update_rule(client, admin_headers):
    r = client.post("/drink-rules",
        json={"name": "ToUpdate", "wine_type": "white", "from_offset": 0, "to_offset": 3},
        headers=admin_headers,
    )
    rule_id = r.json()["id"]

    r2 = client.put(f"/drink-rules/{rule_id}",
        json={"name": "Updated", "to_offset": 7},
        headers=admin_headers,
    )
    assert r2.status_code == 200
    assert r2.json()["name"] == "Updated"
    assert r2.json()["to_offset"] == 7


def test_update_rule_requires_auth(client, admin_headers):
    r = client.post("/drink-rules",
        json={"name": "NeedsAuth", "wine_type": "red", "from_offset": 0, "to_offset": 5},
        headers=admin_headers,
    )
    rule_id = r.json()["id"]
    r2 = client.put(f"/drink-rules/{rule_id}", json={"name": "Hacked"})
    assert r2.status_code == 401


def test_delete_rule(client, admin_headers):
    r = client.post("/drink-rules",
        json={"name": "ToDelete", "wine_type": "other", "from_offset": 0, "to_offset": 4},
        headers=admin_headers,
    )
    rule_id = r.json()["id"]

    r2 = client.delete(f"/drink-rules/{rule_id}", headers=admin_headers)
    assert r2.status_code == 200

    ids = [r["id"] for r in client.get("/drink-rules").json()]
    assert rule_id not in ids


def test_delete_nonexistent_rule(client, admin_headers):
    r = client.delete("/drink-rules/999999", headers=admin_headers)
    assert r.status_code == 404
