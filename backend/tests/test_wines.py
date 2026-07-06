import pytest

WINE = {
    "name": "Blaufränkisch Reserve",
    "producer": "Weingut Muster",
    "vintage": 2019,
    "type": "red",
    "grape": "Blaufränkisch",
    "region": "Mittelburgenland",
    "country": "Österreich",
    "quantity": 6,
    "price": 24.90,
    "rating": 4,
}


def test_get_wines_empty_or_list(client):
    r = client.get("/wines")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_wine_requires_auth(client):
    r = client.post("/wines", json=WINE)
    assert r.status_code == 401


def test_create_wine(client, admin_headers):
    r = client.post("/wines", json=WINE, headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == WINE["name"]
    assert data["vintage"] == 2019
    assert data["quantity"] == 6
    assert "id" in data


def test_get_wines_includes_created(client, admin_headers):
    client.post("/wines", json={**WINE, "name": "Testrotwein"}, headers=admin_headers)
    r = client.get("/wines")
    names = [w["name"] for w in r.json()]
    assert "Testrotwein" in names


def test_update_wine(client, admin_headers):
    r = client.post("/wines", json=WINE, headers=admin_headers)
    wine_id = r.json()["id"]

    r2 = client.put(f"/wines/{wine_id}", json={"quantity": 3}, headers=admin_headers)
    assert r2.status_code == 200
    assert r2.json()["quantity"] == 3


def test_update_wine_requires_auth(client, admin_headers):
    r = client.post("/wines", json=WINE, headers=admin_headers)
    wine_id = r.json()["id"]

    r2 = client.put(f"/wines/{wine_id}", json={"quantity": 99})
    assert r2.status_code == 401


def test_delete_wine(client, admin_headers):
    r = client.post("/wines", json=WINE, headers=admin_headers)
    wine_id = r.json()["id"]

    r2 = client.delete(f"/wines/{wine_id}", headers=admin_headers)
    assert r2.status_code == 200

    ids = [w["id"] for w in client.get("/wines").json()]
    assert wine_id not in ids


def test_delete_wine_requires_auth(client, admin_headers):
    r = client.post("/wines", json=WINE, headers=admin_headers)
    wine_id = r.json()["id"]

    r2 = client.delete(f"/wines/{wine_id}")
    assert r2.status_code == 401


def test_delete_nonexistent_wine(client, admin_headers):
    r = client.delete("/wines/999999", headers=admin_headers)
    assert r.status_code == 404


def test_wine_name_required(client, admin_headers):
    r = client.post("/wines", json={"type": "red", "quantity": 1}, headers=admin_headers)
    assert r.status_code == 422


def test_grape_saved_to_grapes_table(client, admin_headers):
    grape = "Zweigelt"
    client.post("/wines", json={**WINE, "name": "ZweigelterTest", "grape": grape}, headers=admin_headers)
    grapes = client.get("/grapes", headers=admin_headers).json()
    assert grape in grapes


def test_stats(client, admin_headers):
    client.post("/wines", json={**WINE, "name": "StatTestWein"}, headers=admin_headers)
    r = client.get("/stats", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "total_wines" in data
    assert "total_bottles" in data
    assert data["total_wines"] >= 1


BARCODE = "4012345678901"
WINE_BARCODE = {
    "name": "Clos du Marquis",
    "producer": "Château Léoville Las Cases",
    "vintage": 2015,
    "type": "red",
    "grape": "Cabernet Sauvignon",
    "region": "Saint-Julien",
    "country": "Frankreich",
    "quantity": 2,
    "barcode": BARCODE,
    "description": "",
}


def test_barcode_description_persists_after_delete(client, admin_headers):
    # Unified model: qty=0 keeps entry in library; DELETE removes it entirely.
    # This test verifies that setting qty=0 hides from dashboard but keeps in library.

    # 1. Wein per Barcode hinzufügen
    r = client.post("/wines", json=WINE_BARCODE, headers=admin_headers)
    assert r.status_code == 200
    wine_id = r.json()["id"]
    assert r.json()["barcode"] == BARCODE

    # 2. Description ändern
    description = "Eleganter Bordeaux mit Noten von Cassis, Zedernholz und einem langen Abgang."
    r = client.put(f"/wines/{wine_id}", json={"description": description}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["description"] == description

    # 3. Menge auf 0 setzen → verschwindet aus Dashboard, bleibt in Library
    r = client.put(f"/wines/{wine_id}", json={"quantity": 0}, headers=admin_headers)
    assert r.status_code == 200
    ids = [w["id"] for w in client.get("/wines").json()]
    assert wine_id not in ids  # Default-Setting: qty=0 nicht im Dashboard

    # 4. In der Library ist er noch vorhanden, Description erhalten
    lib = client.get("/library", headers=admin_headers).json()
    entry = next((e for e in lib if e["id"] == wine_id), None)
    assert entry is not None
    assert entry["description"] == description
    assert entry["quantity"] == 0

    # 5. Barcode-Lookup trifft lokalen Eintrag
    r = client.get(f"/lookup/{BARCODE}", headers=admin_headers)
    assert r.status_code == 200
    lookup = r.json()
    assert lookup is not None
    assert lookup["source"] == "local"
    assert lookup["name"] == WINE_BARCODE["name"]

    # 6. Menge erhöhen → wieder im Dashboard sichtbar
    r = client.put(f"/wines/{wine_id}", json={"quantity": 2}, headers=admin_headers)
    assert r.status_code == 200
    ids = [w["id"] for w in client.get("/wines").json()]
    assert wine_id in ids


def test_create_wine_rejects_invalid_type(client, admin_headers):
    r = client.post("/wines", json={"name": "BadType", "type": "banana", "quantity": 1},
                     headers=admin_headers)
    assert r.status_code == 422


def test_create_wine_rejects_invalid_body(client, admin_headers):
    r = client.post("/wines", json={"name": "BadBody", "type": "red", "body": "Chunky", "quantity": 1},
                     headers=admin_headers)
    assert r.status_code == 422


def test_get_wine_returns_visible_wine(client, admin_headers):
    wine_id = client.post("/wines", json={"name": "DetailVisible", "type": "red", "quantity": 1},
                           headers=admin_headers).json()["id"]
    r = client.get(f"/wines/{wine_id}")
    assert r.status_code == 200
    assert r.json()["name"] == "DetailVisible"


def test_get_wine_hides_zero_quantity_by_default(client, admin_headers):
    """Regression: GET /wines/{id} used to ignore show_zero_quantity_in_dashboard,
    so a hidden (out-of-stock) library entry could be read by ID even though
    it's deliberately excluded from the /wines list."""
    wine_id = client.post("/wines", json={"name": "DetailHidden", "type": "red", "quantity": 0},
                           headers=admin_headers).json()["id"]
    r = client.get(f"/wines/{wine_id}")
    assert r.status_code == 404

    # Still reachable through the library (admin browse-all view).
    r = client.get(f"/wines/{wine_id}", headers=admin_headers)
    assert r.status_code == 404  # get_wine applies the same rule regardless of auth
    lib_names = [w["name"] for w in client.get("/library", headers=admin_headers).json()]
    assert "DetailHidden" in lib_names


def test_get_nonexistent_wine_404(client):
    r = client.get("/wines/999999")
    assert r.status_code == 404
