import csv
import io
import json


def test_export_json_requires_auth(client):
    r = client.get("/export/json")
    assert r.status_code == 401


def test_export_json(client, admin_headers):
    client.post("/wines", json={"name": "ExportJsonWine", "type": "red", "quantity": 1},
                headers=admin_headers)
    r = client.get("/export/json", headers=admin_headers)
    assert r.status_code == 200
    data = json.loads(r.content)
    assert any(w["name"] == "ExportJsonWine" for w in data)


def test_export_csv(client, admin_headers):
    client.post("/wines", json={"name": "ExportCsvWine", "type": "white", "quantity": 2},
                headers=admin_headers)
    r = client.get("/export/csv", headers=admin_headers)
    assert r.status_code == 200
    rows = list(csv.DictReader(io.StringIO(r.text)))
    assert any(row["name"] == "ExportCsvWine" for row in rows)


def test_import_requires_auth(client):
    payload = json.dumps([{"name": "NoAuthImport"}]).encode()
    r = client.post("/import", files={"file": ("wines.json", payload, "application/json")})
    assert r.status_code == 401


def test_import_json_creates_wines(client, admin_headers):
    payload = json.dumps([
        {"name": "ImportedWineA", "type": "red", "quantity": 1},
        {"name": "ImportedWineB", "type": "white", "quantity": 2},
    ]).encode()
    r = client.post("/import", files={"file": ("wines.json", payload, "application/json")},
                     headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["created"] == 2

    names = [w["name"] for w in client.get("/library", headers=admin_headers).json()]
    assert "ImportedWineA" in names
    assert "ImportedWineB" in names


def test_import_skips_existing_name_producer_pair(client, admin_headers):
    payload = json.dumps([{"name": "DupImportWine", "producer": "Same Producer", "type": "red"}]).encode()
    r1 = client.post("/import", files={"file": ("a.json", payload, "application/json")},
                      headers=admin_headers)
    r2 = client.post("/import", files={"file": ("b.json", payload, "application/json")},
                      headers=admin_headers)
    assert r1.json()["created"] == 1
    assert r2.json()["skipped"] == 1
    assert r2.json()["created"] == 0


def test_import_rejects_non_list_json(client, admin_headers):
    payload = json.dumps({"name": "NotAList"}).encode()
    r = client.post("/import", files={"file": ("wines.json", payload, "application/json")},
                     headers=admin_headers)
    assert r.status_code == 400


def test_import_rejects_malformed_json(client, admin_headers):
    r = client.post("/import", files={"file": ("wines.json", b"{not valid json", "application/json")},
                     headers=admin_headers)
    assert r.status_code == 400


def test_import_rejects_unsupported_extension(client, admin_headers):
    r = client.post("/import", files={"file": ("wines.txt", b"name,type\nFoo,red", "text/plain")},
                     headers=admin_headers)
    assert r.status_code == 400


def test_import_csv_creates_wine(client, admin_headers):
    csv_content = "name,type,quantity\nCsvImportWine,red,3\n"
    r = client.post("/import", files={"file": ("wines.csv", csv_content.encode(), "text/csv")},
                     headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["created"] == 1
    names = [w["name"] for w in client.get("/library", headers=admin_headers).json()]
    assert "CsvImportWine" in names
