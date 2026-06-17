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
    grapes = client.get("/grapes").json()
    assert grape in grapes


def test_stats(client, admin_headers):
    client.post("/wines", json={**WINE, "name": "StatTestWein"}, headers=admin_headers)
    r = client.get("/stats")
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
    # 1. Wein per Barcode hinzufügen
    r = client.post("/wines", json=WINE_BARCODE, headers=admin_headers)
    assert r.status_code == 200
    wine_id = r.json()["id"]
    assert r.json()["barcode"] == BARCODE

    # 2. Description ändern → wird auch in WineLibrary geschrieben
    description = "Eleganter Bordeaux mit Noten von Cassis, Zedernholz und einem langen Abgang."
    r = client.put(f"/wines/{wine_id}", json={"description": description}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["description"] == description

    # 3. Wein aus dem Dashboard entfernen (wines-Tabelle), WineLibrary bleibt erhalten
    r = client.delete(f"/wines/{wine_id}", headers=admin_headers)
    assert r.status_code == 200
    ids = [w["id"] for w in client.get("/wines").json()]
    assert wine_id not in ids

    # 4. Barcode nochmal scannen → trifft lokale Library, description muss noch da sein
    r = client.get(f"/lookup/{BARCODE}", headers=admin_headers)
    assert r.status_code == 200
    lookup = r.json()
    assert lookup is not None
    assert lookup["source"] == "local"
    assert lookup["description"] == description
    assert lookup["name"] == WINE_BARCODE["name"]

    # 5. Wein mit den Lookup-Daten erneut anlegen
    r = client.post("/wines", json={
        "name": lookup["name"],
        "producer": lookup["producer"],
        "vintage": lookup["vintage"],
        "type": lookup["type"],
        "grape": lookup.get("grape", ""),
        "region": lookup.get("region", ""),
        "country": lookup.get("country", ""),
        "quantity": 1,
        "barcode": BARCODE,
        "description": lookup["description"],
    }, headers=admin_headers)
    assert r.status_code == 200
    new_wine = r.json()

    # 6. Description ist im neu angelegten Wein vorhanden
    assert new_wine["description"] == description
    assert new_wine["barcode"] == BARCODE
