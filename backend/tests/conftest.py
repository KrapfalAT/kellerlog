import os
import tempfile
from pathlib import Path

# Must be set before importing main so the engine + init functions use the test DB
_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_db_file.close()
_img_dir = tempfile.mkdtemp()

os.environ["DATABASE_URL"] = f"sqlite:///{_db_file.name}"
os.environ["IMAGES_DIR"] = _img_dir
os.environ["KELLERLOG_SECRET_KEY"] = "test-secret-key-at-least-32-bytes-x"
os.environ["KELLERLOG_ADMIN_USER"] = "admin"
os.environ["KELLERLOG_ADMIN_PASSWORD"] = "adminpass"

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture(scope="session")
def admin_headers(client):
    r = client.post("/auth/login", json={"username": "admin", "password": "adminpass"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['token']}"}
