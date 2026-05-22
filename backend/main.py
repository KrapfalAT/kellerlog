import csv
import io
import json
import os
import secrets
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import httpx
from fastapi import FastAPI, HTTPException, Depends, File, Header, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, text, func, or_
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DATABASE_URL = "sqlite:////app/data/wines.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

WINEAPI_KEY = os.getenv("WINEAPI_KEY", "")
WINEAPI_BASE = "https://api.wineapi.io"
WINEAPI_HEADERS = {"X-API-Key": WINEAPI_KEY}

ADMIN_KEY = os.getenv("KELLERLOG_ADMIN_KEY", "")
if not ADMIN_KEY:
    ADMIN_KEY = secrets.token_hex(32)
    print(f"⚠️  KELLERLOG_ADMIN_KEY not set — generated: {ADMIN_KEY}", flush=True)

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]

# Magic bytes for supported image formats
_IMAGE_SIGNATURES = [
    b'\xff\xd8\xff',           # JPEG
    b'\x89PNG\r\n\x1a\n',     # PNG
    b'GIF87a', b'GIF89a',     # GIF
    b'RIFF',                   # WebP (verify bytes 8-12 == WEBP)
]

def _valid_image_header(header: bytes) -> bool:
    for sig in _IMAGE_SIGNATURES:
        if header[:len(sig)] == sig:
            if sig == b'RIFF':
                return len(header) >= 12 and header[8:12] == b'WEBP'
            return True
    # HEIC/HEIF: ISO Base Media File Format — ftyp box at offset 4
    return len(header) >= 8 and header[4:8] == b'ftyp'

def require_auth(x_admin_key: str = Header(default="")):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Ungültiger Admin-Key")


class WineModel(Base):
    __tablename__ = "wines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    producer = Column(String, default="")
    vintage = Column(Integer, nullable=True)
    grape = Column(String, default="")
    region = Column(String, default="")
    country = Column(String, default="")
    type = Column(String, default="red")
    alcohol = Column(Float, nullable=True)
    rating = Column(Integer, nullable=True)
    quantity = Column(Integer, default=1)
    notes = Column(String, default="")
    price = Column(Float, nullable=True)
    barcode = Column(String, default="")
    image_url = Column(String, default="")
    body = Column(String, default="")
    acidity = Column(String, default="")
    pairings = Column(String, default="")
    description = Column(String, default="")
    wineapi_id = Column(String, default="")
    added_at = Column(DateTime, default=datetime.utcnow)


class WineLibrary(Base):
    __tablename__ = "wine_library"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    producer = Column(String, default="")
    vintage = Column(Integer, nullable=True)
    grape = Column(String, default="")
    region = Column(String, default="")
    country = Column(String, default="")
    type = Column(String, default="red")
    alcohol = Column(Float, nullable=True)
    rating = Column(Integer, nullable=True)
    notes = Column(String, default="")
    price = Column(Float, nullable=True)
    barcode = Column(String, default="")
    image_url = Column(String, default="")
    body = Column(String, default="")
    acidity = Column(String, default="")
    pairings = Column(String, default="")
    description = Column(String, default="")
    wineapi_id = Column(String, default="")
    saved_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


def _ensure_columns():
    new_cols = [
        ("body", "TEXT DEFAULT ''"),
        ("acidity", "TEXT DEFAULT ''"),
        ("pairings", "TEXT DEFAULT ''"),
        ("description", "TEXT DEFAULT ''"),
        ("wineapi_id", "TEXT DEFAULT ''"),
    ]
    with engine.connect() as conn:
        existing = {row[1] for row in conn.execute(text("PRAGMA table_info(wines)"))}
        for col_name, col_def in new_cols:
            if col_name not in existing:
                conn.execute(text(f"ALTER TABLE wines ADD COLUMN {col_name} {col_def}"))
        conn.commit()

_ensure_columns()

IMAGES_DIR = Path("/app/data/images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="KellerLog API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class WineCreate(BaseModel):
    name: str
    producer: str = ""
    vintage: Optional[int] = None
    grape: str = ""
    region: str = ""
    country: str = ""
    type: str = "red"
    alcohol: Optional[float] = None
    rating: Optional[int] = None
    quantity: int = 1
    notes: str = ""
    price: Optional[float] = None
    barcode: str = ""
    image_url: str = ""
    body: str = ""
    acidity: str = ""
    pairings: str = ""
    description: str = ""
    wineapi_id: str = ""


class WineUpdate(BaseModel):
    name: Optional[str] = None
    producer: Optional[str] = None
    vintage: Optional[int] = None
    grape: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    type: Optional[str] = None
    alcohol: Optional[float] = None
    rating: Optional[int] = None
    quantity: Optional[int] = None
    notes: Optional[str] = None
    price: Optional[float] = None
    barcode: Optional[str] = None
    image_url: Optional[str] = None
    body: Optional[str] = None
    acidity: Optional[str] = None
    pairings: Optional[str] = None
    description: Optional[str] = None
    wineapi_id: Optional[str] = None


class WineResponse(BaseModel):
    id: int
    name: str
    producer: str
    vintage: Optional[int]
    grape: str
    region: str
    country: str
    type: str
    alcohol: Optional[float]
    rating: Optional[int]
    quantity: int
    notes: str
    price: Optional[float]
    barcode: str
    image_url: str
    body: str
    acidity: str
    pairings: str
    description: str
    wineapi_id: str
    added_at: datetime

    model_config = {"from_attributes": True}


class WineLibraryResponse(BaseModel):
    id: int
    name: str
    producer: str
    vintage: Optional[int]
    grape: str
    region: str
    country: str
    type: str
    alcohol: Optional[float]
    rating: Optional[int]
    notes: str
    price: Optional[float]
    barcode: str
    image_url: str
    body: str
    acidity: str
    pairings: str
    description: str
    wineapi_id: str
    saved_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _wineapi_type(raw: str | None) -> str:
    mapping = {"red": "red", "white": "white", "rosé": "rosé", "rose": "rosé",
               "sparkling": "sparkling", "dessert": "dessert", "fortified": "dessert"}
    return mapping.get((raw or "").lower(), "other")


def _rating_from_avg(avg: float | None) -> Optional[int]:
    if avg is None:
        return None
    return max(1, min(5, round(avg)))


def _parse_wineapi(data: dict) -> dict:
    winery = data.get("winery") or {}
    region = data.get("region") or {}
    grapes = data.get("grapes") or []
    pairings = data.get("pairings") or []

    producer = winery.get("name", "") if isinstance(winery, dict) else str(winery)
    region_name = region.get("name", "") if isinstance(region, dict) else str(region)
    country = region.get("country", "") if isinstance(region, dict) else ""
    grape_str = ", ".join(g["name"] for g in grapes if g.get("name"))
    pairings_str = ", ".join(p["food"] for p in pairings if p.get("food"))

    return {
        "wineapi_id": data.get("id", ""),
        "name": data.get("name", ""),
        "producer": producer,
        "type": _wineapi_type(data.get("type")),
        "region": region_name,
        "country": country,
        "grape": grape_str,
        "alcohol": data.get("alcoholContent"),
        "rating": _rating_from_avg(data.get("averageRating")),
        "image_url": data.get("imageUrl") or "",
        "vintage": data.get("vintage"),
        "body": data.get("body") or "",
        "acidity": data.get("acidity") or "",
        "description": data.get("description") or "",
        "pairings": pairings_str,
    }


_LIB_STR = ["name", "producer", "grape", "region", "country", "type", "notes",
            "barcode", "image_url", "body", "acidity", "pairings", "description", "wineapi_id"]
_LIB_OPT = ["vintage", "rating", "alcohol", "price"]


def _upsert_library(db: Session, data: dict) -> None:
    entry = None
    if data.get("barcode"):
        entry = db.query(WineLibrary).filter(WineLibrary.barcode == data["barcode"]).first()
    if not entry and data.get("wineapi_id"):
        entry = db.query(WineLibrary).filter(WineLibrary.wineapi_id == data["wineapi_id"]).first()
    if not entry:
        name_q = (data.get("name") or "").lower()
        producer_q = (data.get("producer") or "").lower()
        for c in db.query(WineLibrary).filter(func.lower(WineLibrary.name) == name_q).all():
            if (c.producer or "").lower() == producer_q:
                entry = c
                break

    if entry:
        for f in _LIB_STR:
            setattr(entry, f, data.get(f) or "")
        for f in _LIB_OPT:
            setattr(entry, f, data.get(f))
        entry.updated_at = datetime.utcnow()
    else:
        kwargs = {f: data.get(f) or "" for f in _LIB_STR}
        kwargs.update({f: data.get(f) for f in _LIB_OPT})
        entry = WineLibrary(**kwargs)
        db.add(entry)
    db.commit()


# ── Wine CRUD ─────────────────────────────────────────────────────────────────

@app.get("/wines", response_model=List[WineResponse])
def get_wines(db: Session = Depends(get_db)):
    return db.query(WineModel).order_by(WineModel.added_at.desc()).all()


@app.post("/wines", response_model=WineResponse)
def create_wine(wine: WineCreate, db: Session = Depends(get_db), _=Depends(require_auth)):
    db_wine = WineModel(**wine.model_dump())
    db.add(db_wine)
    db.commit()
    db.refresh(db_wine)
    _upsert_library(db, wine.model_dump())
    return db_wine


@app.get("/wines/{wine_id}", response_model=WineResponse)
def get_wine(wine_id: int, db: Session = Depends(get_db)):
    wine = db.query(WineModel).filter(WineModel.id == wine_id).first()
    if not wine:
        raise HTTPException(status_code=404, detail="Wein nicht gefunden")
    return wine


@app.put("/wines/{wine_id}", response_model=WineResponse)
def update_wine(wine_id: int, wine_update: WineUpdate, db: Session = Depends(get_db), _=Depends(require_auth)):
    wine = db.query(WineModel).filter(WineModel.id == wine_id).first()
    if not wine:
        raise HTTPException(status_code=404, detail="Wein nicht gefunden")
    for field, value in wine_update.model_dump(exclude_unset=True).items():
        setattr(wine, field, value)
    db.commit()
    db.refresh(wine)
    skip = {"id", "quantity", "added_at"}
    _upsert_library(db, {c.name: getattr(wine, c.name) for c in WineModel.__table__.columns if c.name not in skip})
    return wine


@app.delete("/wines/{wine_id}")
def delete_wine(wine_id: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    wine = db.query(WineModel).filter(WineModel.id == wine_id).first()
    if not wine:
        raise HTTPException(status_code=404, detail="Wein nicht gefunden")
    db.delete(wine)
    db.commit()
    return {"message": "Wein gelöscht"}


# ── Library endpoints ─────────────────────────────────────────────────────────

@app.get("/library", response_model=List[WineLibraryResponse])
def get_library(db: Session = Depends(get_db)):
    return db.query(WineLibrary).order_by(WineLibrary.saved_at.desc()).all()


@app.get("/library/search")
def search_library(q: str, db: Session = Depends(get_db)):
    if not q.strip():
        return []
    pat = f"%{q.lower()}%"
    rows = db.query(WineLibrary).filter(
        or_(
            func.lower(WineLibrary.name).like(pat),
            func.lower(WineLibrary.producer).like(pat),
            func.lower(WineLibrary.region).like(pat),
            func.lower(WineLibrary.grape).like(pat),
            WineLibrary.barcode == q,
        )
    ).order_by(WineLibrary.saved_at.desc()).limit(10).all()
    return [
        {
            "source": "local", "id": e.id,
            "name": e.name, "producer": e.producer, "vintage": e.vintage,
            "grape": e.grape, "region": e.region, "country": e.country,
            "type": e.type, "alcohol": e.alcohol, "rating": e.rating,
            "notes": e.notes, "price": e.price, "barcode": e.barcode,
            "image_url": e.image_url, "body": e.body, "acidity": e.acidity,
            "pairings": e.pairings, "description": e.description,
            "wineapi_id": e.wineapi_id,
        }
        for e in rows
    ]


@app.delete("/library/{entry_id}")
def delete_library_entry(entry_id: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    entry = db.query(WineLibrary).filter(WineLibrary.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Eintrag nicht gefunden")
    db.delete(entry)
    db.commit()
    return {"ok": True}


# ── Search & lookup ───────────────────────────────────────────────────────────

@app.get("/search")
async def search_wines(q: str):
    if not q.strip():
        return []
    if not WINEAPI_KEY:
        raise HTTPException(status_code=503, detail="WINEAPI_KEY nicht konfiguriert")
    try:
        async with httpx.AsyncClient(timeout=15.0, headers=WINEAPI_HEADERS) as client:
            resp = await client.get(f"{WINEAPI_BASE}/wines/search", params={"q": q, "limit": 10})
        if resp.status_code == 401:
            raise HTTPException(status_code=503, detail="WineAPI-Schlüssel ungültig")
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="WineAPI nicht erreichbar")
        results = []
        for item in resp.json().get("results", []):
            winery = item.get("winery") or {}
            region = item.get("region") or {}
            results.append({
                "wineapi_id": item.get("id", ""),
                "name": item.get("name", ""),
                "producer": winery.get("name", "") if isinstance(winery, dict) else str(winery),
                "type": _wineapi_type(item.get("type")),
                "region": region.get("name", "") if isinstance(region, dict) else str(region),
                "country": region.get("country", "") if isinstance(region, dict) else "",
                "rating": _rating_from_avg(item.get("averageRating")),
                "image_url": item.get("imageUrl") or "",
                "vintage": item.get("vintage"),
            })
        return results
    except HTTPException:
        raise
    except Exception as e:
        print(f"Search error: {e}")
        raise HTTPException(status_code=502, detail="WineAPI nicht erreichbar")


@app.get("/wine-details/{wineapi_id}")
async def get_wine_details(wineapi_id: str):
    if not WINEAPI_KEY:
        raise HTTPException(status_code=503, detail="WINEAPI_KEY nicht konfiguriert")
    async with httpx.AsyncClient(timeout=15.0, headers=WINEAPI_HEADERS) as client:
        resp = await client.get(f"{WINEAPI_BASE}/wines/{wineapi_id}")
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Wein nicht gefunden")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="WineAPI nicht erreichbar")
    return _parse_wineapi(resp.json())


@app.post("/upload")
async def upload_image(file: UploadFile = File(...), _=Depends(require_auth)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Nur Bilddateien erlaubt")
    header = await file.read(12)
    file.file.seek(0)
    if not _valid_image_header(header):
        raise HTTPException(status_code=400, detail="Ungültiges Bildformat")
    ext_map = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
               "image/gif": ".gif", "image/heic": ".jpg"}
    ext = ext_map.get(file.content_type, ".jpg")
    filename = f"{uuid.uuid4()}{ext}"
    dest = IMAGES_DIR / filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"url": f"/api/images/{filename}"}


@app.get("/lookup/{barcode}")
async def lookup_barcode(barcode: str, db: Session = Depends(get_db)):
    # Check local library first
    lib = db.query(WineLibrary).filter(WineLibrary.barcode == barcode).first()
    if lib:
        return {
            "source": "local", "id": lib.id,
            "name": lib.name, "producer": lib.producer, "vintage": lib.vintage,
            "grape": lib.grape, "region": lib.region, "country": lib.country,
            "type": lib.type, "alcohol": lib.alcohol, "rating": lib.rating,
            "notes": lib.notes, "price": lib.price, "barcode": lib.barcode,
            "image_url": lib.image_url, "body": lib.body, "acidity": lib.acidity,
            "pairings": lib.pairings, "description": lib.description,
            "wineapi_id": lib.wineapi_id,
        }

    # Open Food Facts lookup
    try:
        async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "KellerLog/1.0"}) as client:
            resp = await client.get(f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json")
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("status") != 1:
            return None
        product = data.get("product", {})
        name = product.get("product_name") or product.get("product_name_de") or ""
        if not name:
            return None
    except Exception:
        return None

    off_image = product.get("image_front_url") or product.get("image_url") or ""
    off_brands = product.get("brands") or ""

    if WINEAPI_KEY:
        try:
            async with httpx.AsyncClient(timeout=10.0, headers=WINEAPI_HEADERS) as client:
                resp = await client.get(f"{WINEAPI_BASE}/wines/search", params={"q": name, "limit": 1})
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results:
                    item = results[0]
                    winery = item.get("winery") or {}
                    region = item.get("region") or {}
                    return {
                        "wineapi_id": item.get("id", ""),
                        "name": item.get("name", name),
                        "producer": winery.get("name", "") if isinstance(winery, dict) else str(winery),
                        "type": _wineapi_type(item.get("type")),
                        "region": region.get("name", "") if isinstance(region, dict) else str(region),
                        "country": region.get("country", "") if isinstance(region, dict) else "",
                        "rating": _rating_from_avg(item.get("averageRating")),
                        "image_url": item.get("imageUrl") or off_image,
                        "vintage": item.get("vintage"),
                        "barcode": barcode,
                    }
        except Exception:
            pass

    countries = product.get("countries_tags") or []
    country = countries[0].replace("en:", "").title() if countries else ""
    return {
        "wineapi_id": "", "name": name, "producer": off_brands,
        "type": "red", "region": "", "country": country,
        "rating": None, "image_url": off_image, "vintage": None, "barcode": barcode,
    }


_EXPORT_FIELDS = [
    'name', 'producer', 'vintage', 'type', 'grape', 'region', 'country',
    'quantity', 'price', 'alcohol', 'rating', 'body', 'acidity',
    'pairings', 'description', 'notes', 'barcode', 'image_url', 'wineapi_id',
]


@app.get("/export/json")
def export_json(db: Session = Depends(get_db)):
    wines = db.query(WineModel).order_by(WineModel.added_at.desc()).all()
    data = [{f: getattr(w, f, None) for f in _EXPORT_FIELDS} for w in wines]
    return Response(
        content=json.dumps(data, indent=2, ensure_ascii=False),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=kellerlog_export.json"},
    )


@app.get("/export/csv")
def export_csv(db: Session = Depends(get_db)):
    wines = db.query(WineModel).order_by(WineModel.added_at.desc()).all()
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_EXPORT_FIELDS)
    writer.writeheader()
    for w in wines:
        writer.writerow({f: (getattr(w, f, '') or '') for f in _EXPORT_FIELDS})
    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=kellerlog_export.csv"},
    )


@app.post("/import")
async def import_wines(file: UploadFile = File(...), db: Session = Depends(get_db), _=Depends(require_auth)):
    content = await file.read()
    created = skipped = 0

    def _make_wine(row: dict) -> WineModel:
        def _int(v): return int(v) if str(v).strip() not in ('', 'None', 'null') else None
        def _float(v): return float(v) if str(v).strip() not in ('', 'None', 'null') else None
        return WineModel(
            name=row.get('name', '').strip(),
            producer=row.get('producer', '') or '',
            vintage=_int(row.get('vintage')),
            type=row.get('type', 'red') or 'red',
            grape=row.get('grape', '') or '',
            region=row.get('region', '') or '',
            country=row.get('country', '') or '',
            quantity=int(row.get('quantity') or 1),
            price=_float(row.get('price')),
            alcohol=_float(row.get('alcohol')),
            rating=_int(row.get('rating')),
            body=row.get('body', '') or '',
            acidity=row.get('acidity', '') or '',
            pairings=row.get('pairings', '') or '',
            description=row.get('description', '') or '',
            notes=row.get('notes', '') or '',
            barcode=row.get('barcode', '') or '',
            image_url=row.get('image_url', '') or '',
            wineapi_id=row.get('wineapi_id', '') or '',
        )

    fname = (file.filename or '').lower()
    if fname.endswith('.json'):
        rows = json.loads(content.decode('utf-8'))
    elif fname.endswith('.csv'):
        rows = list(csv.DictReader(io.StringIO(content.decode('utf-8'))))
    else:
        raise HTTPException(status_code=400, detail="Nur .json oder .csv Dateien erlaubt")

    for row in rows:
        name = (row.get('name') or '').strip()
        if not name:
            continue
        producer = (row.get('producer') or '').strip()
        exists = db.query(WineModel).filter(
            func.lower(WineModel.name) == name.lower(),
            func.lower(WineModel.producer) == producer.lower(),
        ).first()
        if exists:
            skipped += 1
            continue
        db.add(_make_wine(row))
        created += 1

    db.commit()
    return {"created": created, "skipped": skipped}


@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    wines = db.query(WineModel).all()
    total_bottles = sum(w.quantity for w in wines)
    type_counts: dict = {}
    for w in wines:
        type_counts[w.type] = type_counts.get(w.type, 0) + w.quantity
    rated = [w.rating for w in wines if w.rating]
    avg_rating = round(sum(rated) / len(rated), 1) if rated else None
    countries: dict = {}
    for w in wines:
        if w.country:
            countries[w.country] = countries.get(w.country, 0) + 1
    return {
        "total_wines": len(wines),
        "total_bottles": total_bottles,
        "type_counts": type_counts,
        "avg_rating": avg_rating,
        "top_countries": sorted(countries.items(), key=lambda x: x[1], reverse=True)[:5],
    }
