import io

from PIL import Image
import pillow_heif

import main

pillow_heif.register_heif_opener()


def _jpeg_bytes(color=(255, 0, 0)):
    buf = io.BytesIO()
    Image.new("RGB", (16, 16), color=color).save(buf, format="JPEG")
    return buf.getvalue()


def _heic_bytes(color=(0, 200, 50)):
    buf = io.BytesIO()
    Image.new("RGB", (16, 16), color=color).save(buf, format="HEIF", quality=80)
    return buf.getvalue()


def _saved_path(url: str):
    filename = url.rsplit("/", 1)[-1]
    return main.IMAGES_DIR / filename


def test_upload_requires_auth(client):
    r = client.post("/upload", files={"file": ("x.jpg", _jpeg_bytes(), "image/jpeg")})
    assert r.status_code == 401


def test_upload_rejects_non_image_content_type(client, admin_headers):
    r = client.post("/upload", files={"file": ("x.txt", b"hello", "text/plain")},
                     headers=admin_headers)
    assert r.status_code == 400


def test_upload_rejects_mismatched_magic_bytes(client, admin_headers):
    """Declares image/jpeg but the bytes aren't a JPEG at all."""
    r = client.post("/upload", files={"file": ("x.jpg", b"not-an-image-" * 4, "image/jpeg")},
                     headers=admin_headers)
    assert r.status_code == 400


def test_upload_jpeg_success(client, admin_headers):
    r = client.post("/upload", files={"file": ("photo.jpg", _jpeg_bytes(), "image/jpeg")},
                     headers=admin_headers)
    assert r.status_code == 200
    url = r.json()["url"]
    assert url.endswith(".jpg")
    assert _saved_path(url).exists()


def test_upload_heic_is_converted_to_real_jpeg(client, admin_headers):
    """Regression: HEIC uploads used to be saved verbatim under a .jpg
    extension, so browsers received HEIC bytes labeled as image/jpeg and
    failed to render them. Now they must be decoded and re-encoded."""
    r = client.post("/upload", files={"file": ("photo.heic", _heic_bytes(), "image/heic")},
                     headers=admin_headers)
    assert r.status_code == 200
    url = r.json()["url"]
    assert url.endswith(".jpg")
    saved = _saved_path(url)
    assert saved.exists()
    # A real JPEG starts with the JPEG magic bytes, not the HEIC ftyp box.
    header = saved.read_bytes()[:12]
    assert header[:3] == b"\xff\xd8\xff"
    # And it must actually decode as a JPEG.
    img = Image.open(saved)
    img.load()
    assert img.format == "JPEG"


def test_upload_from_url_rejects_non_https(client, admin_headers):
    r = client.post("/upload-from-url", json={"url": "http://example.com/a.jpg"},
                     headers=admin_headers)
    assert r.status_code == 400


def test_upload_from_url_rejects_private_host(client, admin_headers):
    r = client.post("/upload-from-url", json={"url": "https://127.0.0.1/a.jpg"},
                     headers=admin_headers)
    assert r.status_code == 400


def test_upload_from_url_rejects_localhost_hostname(client, admin_headers):
    r = client.post("/upload-from-url", json={"url": "https://localhost/a.jpg"},
                     headers=admin_headers)
    assert r.status_code == 400


def test_upload_from_url_requires_auth(client):
    r = client.post("/upload-from-url", json={"url": "https://example.com/a.jpg"})
    assert r.status_code == 401
