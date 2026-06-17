def test_get_grapes_returns_list(client):
    r = client.get("/grapes")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_grape_added_on_wine_create(client, admin_headers):
    r = client.post("/wines",
        json={"name": "GrapeTest", "type": "red", "grape": "Sangiovese", "quantity": 1},
        headers=admin_headers,
    )
    assert r.status_code == 200
    grapes = client.get("/grapes").json()
    assert "Sangiovese" in grapes


def test_multiple_grapes_split_by_comma(client, admin_headers):
    client.post("/wines",
        json={"name": "BlendTest", "type": "red", "grape": "Merlot, Cabernet Sauvignon", "quantity": 1},
        headers=admin_headers,
    )
    grapes = client.get("/grapes").json()
    assert "Merlot" in grapes
    assert "Cabernet Sauvignon" in grapes


def test_grape_added_on_wine_update(client, admin_headers):
    r = client.post("/wines",
        json={"name": "UpdateGrapeTest", "type": "white", "grape": "", "quantity": 1},
        headers=admin_headers,
    )
    wine_id = r.json()["id"]

    client.put(f"/wines/{wine_id}", json={"grape": "Riesling"}, headers=admin_headers)
    grapes = client.get("/grapes").json()
    assert "Riesling" in grapes


def test_duplicate_grape_not_duplicated(client, admin_headers):
    # Add same grape twice via two wines
    client.post("/wines",
        json={"name": "DupGrape1", "type": "red", "grape": "Tempranillo", "quantity": 1},
        headers=admin_headers,
    )
    client.post("/wines",
        json={"name": "DupGrape2", "type": "red", "grape": "Tempranillo", "quantity": 1},
        headers=admin_headers,
    )
    grapes = client.get("/grapes").json()
    assert grapes.count("Tempranillo") == 1
