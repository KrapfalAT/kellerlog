WINE = {
    "name": "Library Search Wine",
    "producer": "Weingut Such",
    "vintage": 2020,
    "type": "white",
    "grape": "Grüner Veltliner",
    "region": "Wachau",
    "quantity": 3,
    "by_glass": True,
    "price_per_glass": 6.5,
    "location": "Regal B2",
}


def test_library_search_requires_auth(client):
    r = client.get("/library/search", params={"q": "test"})
    assert r.status_code == 401


def test_library_search_empty_query_returns_empty(client, admin_headers):
    r = client.get("/library/search", params={"q": "   "}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json() == []


def test_library_search_finds_by_name(client, admin_headers):
    client.post("/wines", json=WINE, headers=admin_headers)
    r = client.get("/library/search", params={"q": "Search Wine"}, headers=admin_headers)
    assert r.status_code == 200
    results = r.json()
    assert any(e["name"] == WINE["name"] for e in results)


def test_library_search_includes_all_wine_fields(client, admin_headers):
    """Regression: search results used to be hand-built dicts missing
    by_glass/price_per_glass/location, so those fields silently vanished
    when a wine was picked from search-as-you-type autocomplete."""
    client.post("/wines", json={**WINE, "name": "Search Field Coverage"}, headers=admin_headers)
    r = client.get("/library/search", params={"q": "Search Field Coverage"}, headers=admin_headers)
    entry = r.json()[0]
    assert entry["source"] == "local"
    assert entry["by_glass"] is True
    assert entry["price_per_glass"] == 6.5
    assert entry["location"] == "Regal B2"


def test_lookup_barcode_requires_auth(client):
    r = client.get("/lookup/0000000000000")
    assert r.status_code == 401


def test_lookup_barcode_not_found_returns_null(client, admin_headers):
    r = client.get("/lookup/0000000000000", headers=admin_headers)
    assert r.status_code == 200
    assert r.json() is None


def test_lookup_barcode_includes_all_wine_fields(client, admin_headers):
    barcode = "9998887776665"
    client.post("/wines", json={**WINE, "name": "Lookup Field Coverage", "barcode": barcode},
                headers=admin_headers)
    r = client.get(f"/lookup/{barcode}", headers=admin_headers)
    assert r.status_code == 200
    entry = r.json()
    assert entry["source"] == "local"
    assert entry["by_glass"] is True
    assert entry["price_per_glass"] == 6.5
    assert entry["location"] == "Regal B2"
