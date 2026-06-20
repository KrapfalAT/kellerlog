import asyncio
import csv
import io
import json
import os
import secrets
import uuid
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, File, Header, Query, Request, UploadFile
import httpx
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import bcrypt as _bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, text, func, or_
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////app/data/wines.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

GOOGLE_CSE_KEY = os.getenv("GOOGLE_CSE_KEY", "")
GOOGLE_CSE_ID  = os.getenv("GOOGLE_CSE_ID", "")

# ── SSE broadcast ────────────────────────────────────────────────────────────
_sse_subscribers: list[asyncio.Queue] = []
_main_loop: asyncio.AbstractEventLoop | None = None

async def _sse_notify(event: str = "wines"):
    dead = []
    for q in _sse_subscribers:
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        _sse_subscribers.remove(q)

def notify_clients(event: str = "wines"):
    if _main_loop is not None:
        asyncio.run_coroutine_threadsafe(_sse_notify(event), _main_loop)

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]

SECRET_KEY = os.getenv("KELLERLOG_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("KELLERLOG_SECRET_KEY is not set — set it in your .env file")
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 30


def _hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    return _bcrypt.checkpw(password.encode(), hashed.encode())


def _create_token(user_id: int, role: str) -> str:
    exp = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    return jwt.encode({"sub": str(user_id), "role": role, "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Ungültiges Token")


def require_auth(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    payload = _decode_token(authorization[7:])
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin-Rechte erforderlich")
    return payload


def require_login(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    return _decode_token(authorization[7:])


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


# ── ORM Models ────────────────────────────────────────────────────────────────

class WineLibrary(Base):
    """Unified wine table — library entries with quantity > 0 appear in dashboard."""
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
    # Stock fields (merged from former wines table)
    quantity = Column(Integer, default=0)
    by_glass = Column(Boolean, default=False)
    price_per_glass = Column(Float, nullable=True)
    location = Column(String, default="")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="viewer")  # "admin" or "viewer"
    language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow)


class AppSettings(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, default=1)
    kiosk_enabled = Column(Boolean, default=True)
    kiosk_title = Column(String, default="Weinkarte")
    kiosk_subtitle = Column(String, default="Unsere Weinauswahl")
    kiosk_show_footer = Column(Boolean, default=True)
    kiosk_show_map = Column(Boolean, default=True)
    primary_color = Column(String, default="#480f25")
    dark_mode = Column(Boolean, default=False)
    app_title = Column(String, default="KellerLog")
    app_subtitle = Column(String, default="Meine Weinsammlung")
    logo_url = Column(String, default="")
    show_drink_window = Column(Boolean, default=True)
    kiosk_show_drink_window = Column(Boolean, default=False)
    show_zero_quantity_in_dashboard = Column(Boolean, default=False)


class Grape(Base):
    __tablename__ = "grapes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)


class DrinkWindowRule(Base):
    __tablename__ = "drink_window_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    wine_type = Column(String, default="")  # empty string = any type
    grape = Column(String, nullable=True)   # null = any grape
    from_offset = Column(Integer, default=0)
    to_offset = Column(Integer, default=5)


class CustomField(Base):
    __tablename__ = "custom_fields"
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, unique=True, nullable=False)
    label_de = Column(String, nullable=False, default="")
    label_en = Column(String, nullable=False, default="")
    field_type = Column(String, default="text")  # text | number | date | textarea
    sort_order = Column(Integer, default=0)


class WineCustomValue(Base):
    __tablename__ = "wine_custom_values"
    id = Column(Integer, primary_key=True, autoincrement=True)
    wine_id = Column(Integer, nullable=False)  # references wine_library.id
    field_key = Column(String, nullable=False)
    value = Column(String, default="")


Base.metadata.create_all(bind=engine)


# ── Migrations ────────────────────────────────────────────────────────────────

def _migrate_library_columns():
    """Add stock columns to wine_library if missing (for existing installs)."""
    new_cols = [
        ("quantity",        "INTEGER DEFAULT 0"),
        ("by_glass",        "INTEGER DEFAULT 0"),
        ("price_per_glass", "REAL"),
        ("location",        "TEXT DEFAULT ''"),
    ]
    with engine.connect() as conn:
        existing = {row[1] for row in conn.execute(text("PRAGMA table_info(wine_library)"))}
        for col_name, col_def in new_cols:
            if col_name not in existing:
                conn.execute(text(f"ALTER TABLE wine_library ADD COLUMN {col_name} {col_def}"))
        conn.commit()

_migrate_library_columns()


def _migrate_settings():
    new_cols = [
        ("kiosk_show_map",                   "INTEGER DEFAULT 1"),
        ("primary_color",                    "TEXT DEFAULT '#480f25'"),
        ("dark_mode",                        "INTEGER DEFAULT 0"),
        ("app_title",                        "TEXT DEFAULT 'KellerLog'"),
        ("app_subtitle",                     "TEXT DEFAULT 'Meine Weinsammlung'"),
        ("logo_url",                         "TEXT DEFAULT ''"),
        ("show_drink_window",                "INTEGER DEFAULT 1"),
        ("kiosk_show_drink_window",          "INTEGER DEFAULT 0"),
        ("show_zero_quantity_in_dashboard",  "INTEGER DEFAULT 0"),
    ]
    with engine.connect() as conn:
        existing = {row[1] for row in conn.execute(text("PRAGMA table_info(app_settings)"))}
        for col_name, col_def in new_cols:
            if col_name not in existing:
                conn.execute(text(f"ALTER TABLE app_settings ADD COLUMN {col_name} {col_def}"))
        conn.commit()

_migrate_settings()


def _migrate_drink_rules():
    with engine.connect() as conn:
        existing = {row[1] for row in conn.execute(text("PRAGMA table_info(drink_window_rules)"))}
        if 'grape' not in existing:
            conn.execute(text("ALTER TABLE drink_window_rules ADD COLUMN grape TEXT"))
        conn.commit()

_migrate_drink_rules()


def _migrate_users():
    with engine.connect() as conn:
        existing = {row[1] for row in conn.execute(text("PRAGMA table_info(users)"))}
        if "language" not in existing:
            conn.execute(text("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'en'"))
        conn.commit()

_migrate_users()


def _migrate_to_unified():
    """One-time migration: merge wines table into wine_library, then archive it."""
    with engine.connect() as conn:
        tables = {row[0] for row in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))}
        if 'wines' not in tables:
            return  # Already migrated or fresh install

        wines_rows = conn.execute(text("SELECT * FROM wines")).mappings().all()
        lib_rows = conn.execute(text("SELECT * FROM wine_library")).mappings().all()

        # Build lookup maps for matching
        lib_by_barcode: dict = {}
        lib_by_wineapi: dict = {}
        lib_by_name_producer: dict = {}
        for lib in lib_rows:
            if lib['barcode']:
                lib_by_barcode[lib['barcode']] = lib['id']
            if lib['wineapi_id']:
                lib_by_wineapi[lib['wineapi_id']] = lib['id']
            key = (lib['name'].lower(), (lib['producer'] or '').lower())
            lib_by_name_producer[key] = lib['id']

        id_map: dict = {}  # old wines.id → wine_library.id

        for wine in wines_rows:
            lib_id = None
            if wine['barcode'] and wine['barcode'] in lib_by_barcode:
                lib_id = lib_by_barcode[wine['barcode']]
            elif wine.get('wineapi_id') and wine['wineapi_id'] in lib_by_wineapi:
                lib_id = lib_by_wineapi[wine['wineapi_id']]
            else:
                key = (wine['name'].lower(), (wine.get('producer') or '').lower())
                lib_id = lib_by_name_producer.get(key)

            if lib_id:
                conn.execute(text("""
                    UPDATE wine_library SET
                        quantity        = :qty,
                        by_glass        = :bg,
                        price_per_glass = :ppg,
                        location        = :loc
                    WHERE id = :id
                """), {
                    'qty': wine['quantity'], 'bg': wine.get('by_glass', 0),
                    'ppg': wine.get('price_per_glass'), 'loc': wine.get('location', ''),
                    'id': lib_id,
                })
            else:
                conn.execute(text("""
                    INSERT INTO wine_library
                        (name, producer, vintage, grape, region, country, type, alcohol, rating,
                         notes, price, barcode, image_url, body, acidity, pairings, description,
                         wineapi_id, saved_at, updated_at, quantity, by_glass, price_per_glass, location)
                    VALUES
                        (:name, :producer, :vintage, :grape, :region, :country, :type, :alcohol, :rating,
                         :notes, :price, :barcode, :image_url, :body, :acidity, :pairings, :description,
                         :wineapi_id, :saved_at, :updated_at, :qty, :bg, :ppg, :loc)
                """), {
                    'name': wine['name'], 'producer': wine.get('producer', ''),
                    'vintage': wine.get('vintage'), 'grape': wine.get('grape', ''),
                    'region': wine.get('region', ''), 'country': wine.get('country', ''),
                    'type': wine.get('type', 'red'), 'alcohol': wine.get('alcohol'),
                    'rating': wine.get('rating'), 'notes': wine.get('notes', ''),
                    'price': wine.get('price'), 'barcode': wine.get('barcode', ''),
                    'image_url': wine.get('image_url', ''), 'body': wine.get('body', ''),
                    'acidity': wine.get('acidity', ''), 'pairings': wine.get('pairings', ''),
                    'description': wine.get('description', ''), 'wineapi_id': wine.get('wineapi_id', ''),
                    'saved_at': wine.get('added_at', datetime.utcnow()),
                    'updated_at': datetime.utcnow(),
                    'qty': wine['quantity'], 'bg': wine.get('by_glass', 0),
                    'ppg': wine.get('price_per_glass'), 'loc': wine.get('location', ''),
                })
                lib_id = conn.execute(text("SELECT last_insert_rowid()")).scalar()

            id_map[wine['id']] = lib_id

        conn.commit()

        # Re-map custom values from old wines.id → wine_library.id
        for old_id, new_id in id_map.items():
            conn.execute(text(
                "UPDATE wine_custom_values SET wine_id = :new WHERE wine_id = :old"
            ), {'new': new_id, 'old': old_id})
        conn.commit()

        # Archive old wines table
        conn.execute(text("ALTER TABLE wines RENAME TO wines_archived"))
        conn.commit()

        print(f"✓ Unified library migration complete — {len(id_map)} wines merged", flush=True)

_migrate_to_unified()


def _init_users():
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            username = os.getenv("KELLERLOG_ADMIN_USER", "admin")
            password = os.getenv("KELLERLOG_ADMIN_PASSWORD", "")
            if not password:
                password = secrets.token_urlsafe(12)
                print(f"⚠️  KELLERLOG_ADMIN_PASSWORD not set — generated password for '{username}': {password}", flush=True)
            db.add(User(username=username, password_hash=_hash_password(password), role="admin"))
            db.commit()
            print(f"✓ Admin user '{username}' created", flush=True)
    finally:
        db.close()

_init_users()


def _init_settings():
    db = SessionLocal()
    try:
        if not db.get(AppSettings, 1):
            db.add(AppSettings(id=1))
            db.commit()
    finally:
        db.close()

_init_settings()


def _init_drink_rules():
    db = SessionLocal()
    try:
        if db.query(DrinkWindowRule).count() == 0:
            defaults = [
                DrinkWindowRule(name="Weißwein",         wine_type="white",    from_offset=0, to_offset=4),
                DrinkWindowRule(name="Rotwein",          wine_type="red",      from_offset=3, to_offset=12),
                DrinkWindowRule(name="Rosé",             wine_type="rosé",     from_offset=0, to_offset=3),
                DrinkWindowRule(name="Sekt / Schaumwein",wine_type="sparkling",from_offset=0, to_offset=5),
                DrinkWindowRule(name="Dessertwein",      wine_type="dessert",  from_offset=3, to_offset=20),
                DrinkWindowRule(name="Sonstige",         wine_type="other",    from_offset=1, to_offset=6),
            ]
            db.add_all(defaults)
            db.commit()
    finally:
        db.close()

_init_drink_rules()


def _init_grapes():
    db = SessionLocal()
    try:
        if db.query(Grape).count() == 0:
            for (grape_str,) in db.query(WineLibrary.grape).filter(WineLibrary.grape != "").distinct().all():
                for part in grape_str.split(','):
                    name = part.strip()
                    if name and not db.query(Grape).filter(func.lower(Grape.name) == name.lower()).first():
                        db.add(Grape(name=name))
            db.commit()
    finally:
        db.close()

_init_grapes()


def _save_grape(db: Session, grape_str: str) -> None:
    if not grape_str or not grape_str.strip():
        return
    for part in grape_str.split(','):
        name = part.strip()
        if name and not db.query(Grape).filter(func.lower(Grape.name) == name.lower()).first():
            db.add(Grape(name=name))
    db.commit()


IMAGES_DIR = Path(os.getenv("IMAGES_DIR", "/app/data/images"))
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="KellerLog API", docs_url=None, redoc_url=None, openapi_url=None)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
async def _capture_loop():
    global _main_loop
    _main_loop = asyncio.get_running_loop()

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


def require_login_or_kiosk(authorization: str = Header(default=""), db: Session = Depends(get_db)):
    """Allow unauthenticated access only when kiosk is enabled (public kiosk endpoints)."""
    if authorization.startswith("Bearer "):
        return _decode_token(authorization[7:])
    settings = db.get(AppSettings, 1)
    if settings and settings.kiosk_enabled:
        return None
    raise HTTPException(status_code=401, detail="Nicht angemeldet")


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
    by_glass: bool = False
    price_per_glass: Optional[float] = None
    location: str = ""
    custom_values: Optional[dict] = None


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
    by_glass: Optional[bool] = None
    price_per_glass: Optional[float] = None
    location: Optional[str] = None
    custom_values: Optional[dict] = None


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
    by_glass: bool
    price_per_glass: Optional[float]
    location: str
    saved_at: datetime
    updated_at: datetime
    added_at: datetime  # alias for saved_at — kept for frontend compatibility
    custom_values: dict = {}

    model_config = {"from_attributes": True}


# ── Auth schemas ─────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "viewer"

class UserUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[str] = None
    language: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    language: str = "en"
    created_at: datetime
    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    kiosk_enabled: Optional[bool] = None
    kiosk_title: Optional[str] = None
    kiosk_subtitle: Optional[str] = None
    kiosk_show_footer: Optional[bool] = None
    kiosk_show_map: Optional[bool] = None
    primary_color: Optional[str] = None
    dark_mode: Optional[bool] = None
    app_title: Optional[str] = None
    app_subtitle: Optional[str] = None
    logo_url: Optional[str] = None
    show_drink_window: Optional[bool] = None
    kiosk_show_drink_window: Optional[bool] = None
    show_zero_quantity_in_dashboard: Optional[bool] = None


class SettingsResponse(BaseModel):
    kiosk_enabled: bool
    kiosk_title: str
    kiosk_subtitle: str
    kiosk_show_footer: bool
    kiosk_show_map: bool
    primary_color: str
    dark_mode: bool
    app_title: str
    app_subtitle: str
    logo_url: str
    show_drink_window: bool
    kiosk_show_drink_window: bool
    show_zero_quantity_in_dashboard: bool
    model_config = {"from_attributes": True}


class BatchUpdateData(BaseModel):
    type: Optional[str] = None
    location: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    producer: Optional[str] = None
    rating: Optional[int] = None
    body: Optional[str] = None
    acidity: Optional[str] = None


class WineBatchUpdate(BaseModel):
    ids: List[int]
    updates: BatchUpdateData


class DrinkRuleCreate(BaseModel):
    name: str
    wine_type: str = ""     # empty = any type
    grape: Optional[str] = None
    from_offset: int = 0
    to_offset: int = 5


class DrinkRuleUpdate(BaseModel):
    name: Optional[str] = None
    wine_type: Optional[str] = None
    grape: Optional[str] = None
    from_offset: Optional[int] = None
    to_offset: Optional[int] = None


class DrinkRuleResponse(BaseModel):
    id: int
    name: str
    wine_type: str
    grape: Optional[str]
    from_offset: int
    to_offset: int
    model_config = {"from_attributes": True}


class CustomFieldCreate(BaseModel):
    key: str
    label_de: str
    label_en: str = ""
    field_type: str = "text"
    sort_order: int = 0


class CustomFieldUpdate(BaseModel):
    label_de: Optional[str] = None
    label_en: Optional[str] = None
    field_type: Optional[str] = None
    sort_order: Optional[int] = None


class CustomFieldResponse(BaseModel):
    id: int
    key: str
    label_de: str
    label_en: str
    field_type: str
    sort_order: int
    model_config = {"from_attributes": True}


# ── Helpers ───────────────────────────────────────────────────────────────────



def _wine_to_dict(wine: WineLibrary, custom_values: Optional[dict] = None) -> dict:
    d = {c.name: getattr(wine, c.name) for c in WineLibrary.__table__.columns}
    d['custom_values'] = custom_values or {}
    d['added_at'] = wine.saved_at  # alias for frontend compatibility
    return d


def _load_cvs(db: Session, wine_ids: list) -> dict:
    if not wine_ids:
        return {}
    rows = db.query(WineCustomValue).filter(WineCustomValue.wine_id.in_(wine_ids)).all()
    result: dict = {}
    for r in rows:
        result.setdefault(r.wine_id, {})[r.field_key] = r.value
    return result


def _save_custom_values(db: Session, wine_id: int, values: dict):
    db.query(WineCustomValue).filter(WineCustomValue.wine_id == wine_id).delete()
    for key, val in values.items():
        if val is not None and str(val).strip():
            db.add(WineCustomValue(wine_id=wine_id, field_key=key, value=str(val).strip()))
    db.commit()


# ── Auth endpoints ───────────────────────────────────────────────────────────

@app.post("/auth/login")
@limiter.limit("5/minute;20/hour")
def login(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not _verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Ungültige Anmeldedaten")
    token = _create_token(user.id, user.role)
    return {"token": token, "role": user.role, "username": user.username, "id": user.id}


@app.get("/auth/me")
def get_me(payload=Depends(require_login), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=404)
    return {"id": user.id, "username": user.username, "role": user.role, "language": user.language or "en"}


@app.put("/auth/me/language")
def set_my_language(data: dict, payload=Depends(require_login), db: Session = Depends(get_db)):
    lang = data.get("language", "en")
    if lang not in ("de", "en"):
        raise HTTPException(status_code=400, detail="Ungültige Sprache")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=404)
    user.language = lang
    db.commit()
    return {"ok": True}


@app.get("/auth/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db), _=Depends(require_auth)):
    return db.query(User).order_by(User.created_at).all()


@app.post("/auth/users", response_model=UserResponse)
def create_user(data: UserCreate, db: Session = Depends(get_db), _=Depends(require_auth)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Benutzername bereits vergeben")
    if data.role not in ("admin", "viewer"):
        raise HTTPException(status_code=400, detail="Ungültige Rolle")
    user = User(username=data.username, password_hash=_hash_password(data.password), role=data.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.put("/auth/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), payload=Depends(require_auth)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    if data.role is not None:
        if data.role not in ("admin", "viewer"):
            raise HTTPException(status_code=400, detail="Ungültige Rolle")
        if user.role == "admin" and data.role != "admin":
            admin_count = db.query(User).filter(User.role == "admin").count()
            if admin_count <= 1:
                raise HTTPException(status_code=400, detail="Letzter Admin kann nicht degradiert werden")
        user.role = data.role
    if data.password:
        user.password_hash = _hash_password(data.password)
    db.commit()
    db.refresh(user)
    return user


@app.delete("/auth/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), payload=Depends(require_auth)):
    if int(payload["sub"]) == user_id:
        raise HTTPException(status_code=400, detail="Eigenen Account nicht löschbar")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    if user.role == "admin":
        admin_count = db.query(User).filter(User.role == "admin").count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Letzter Admin kann nicht gelöscht werden")
    db.delete(user)
    db.commit()
    return {"ok": True}


# ── App Settings ──────────────────────────────────────────────────────────────

@app.get("/settings", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db), _=Depends(require_login_or_kiosk)):
    return db.get(AppSettings, 1)


@app.put("/settings", response_model=SettingsResponse)
def update_settings(data: SettingsUpdate, db: Session = Depends(get_db), _=Depends(require_auth)):
    row = db.get(AppSettings, 1)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return row


# ── Grapes ───────────────────────────────────────────────────────────────────

@app.get("/grapes")
def get_grapes(db: Session = Depends(get_db), _=Depends(require_login)):
    return [g.name for g in db.query(Grape).order_by(Grape.name).all()]


# ── Drink Window Rules ────────────────────────────────────────────────────────

@app.get("/drink-rules", response_model=List[DrinkRuleResponse])
def get_drink_rules(db: Session = Depends(get_db), _=Depends(require_login_or_kiosk)):
    return db.query(DrinkWindowRule).order_by(DrinkWindowRule.id).all()


@app.post("/drink-rules", response_model=DrinkRuleResponse)
def create_drink_rule(data: DrinkRuleCreate, db: Session = Depends(get_db), _=Depends(require_auth)):
    rule = DrinkWindowRule(**data.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@app.put("/drink-rules/{rule_id}", response_model=DrinkRuleResponse)
def update_drink_rule(rule_id: int, data: DrinkRuleUpdate, db: Session = Depends(get_db), _=Depends(require_auth)):
    rule = db.get(DrinkWindowRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return rule


@app.delete("/drink-rules/{rule_id}")
def delete_drink_rule(rule_id: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    rule = db.get(DrinkWindowRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404)
    db.delete(rule)
    db.commit()
    return {"ok": True}


# ── Custom Fields ─────────────────────────────────────────────────────────────

@app.get("/custom-fields", response_model=List[CustomFieldResponse])
def get_custom_fields(db: Session = Depends(get_db), _=Depends(require_login_or_kiosk)):
    return db.query(CustomField).order_by(CustomField.sort_order, CustomField.id).all()


@app.post("/custom-fields", response_model=CustomFieldResponse)
def create_custom_field(data: CustomFieldCreate, db: Session = Depends(get_db), _=Depends(require_auth)):
    if db.query(CustomField).filter(CustomField.key == data.key).first():
        raise HTTPException(status_code=400, detail="Key bereits vergeben")
    field = CustomField(**data.model_dump())
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


@app.put("/custom-fields/{field_id}", response_model=CustomFieldResponse)
def update_custom_field(field_id: int, data: CustomFieldUpdate, db: Session = Depends(get_db), _=Depends(require_auth)):
    field = db.get(CustomField, field_id)
    if not field:
        raise HTTPException(status_code=404)
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(field, k, v)
    db.commit()
    db.refresh(field)
    return field


@app.delete("/custom-fields/{field_id}")
def delete_custom_field(field_id: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    field = db.get(CustomField, field_id)
    if not field:
        raise HTTPException(status_code=404)
    db.query(WineCustomValue).filter(WineCustomValue.field_key == field.key).delete()
    db.delete(field)
    db.commit()
    return {"ok": True}


# ── Wine CRUD (unified library) ───────────────────────────────────────────────

@app.get("/wines", response_model=List[WineResponse])
def get_wines(db: Session = Depends(get_db), _=Depends(require_login_or_kiosk)):
    settings = db.get(AppSettings, 1)
    show_zero = settings and settings.show_zero_quantity_in_dashboard
    query = db.query(WineLibrary)
    if not show_zero:
        query = query.filter(WineLibrary.quantity > 0)
    wines = query.order_by(WineLibrary.saved_at.desc()).all()
    cv_map = _load_cvs(db, [w.id for w in wines])
    return [_wine_to_dict(w, cv_map.get(w.id)) for w in wines]


_SSE_MAX_CONNECTIONS = 50

@app.get("/events")
async def sse_events(request: Request, token: str = "", db: Session = Depends(get_db)):
    # EventSource API cannot set headers — accept token via query param
    auth = request.headers.get("authorization", "")
    if not auth and token:
        auth = f"Bearer {token}"
    settings = db.get(AppSettings, 1)
    kiosk_open = settings and settings.kiosk_enabled
    if auth.startswith("Bearer "):
        _decode_token(auth[7:])  # raises 401 if invalid
    elif not kiosk_open:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    if len(_sse_subscribers) >= _SSE_MAX_CONNECTIONS:
        raise HTTPException(status_code=429, detail="Zu viele SSE-Verbindungen")
    q: asyncio.Queue = asyncio.Queue(maxsize=20)
    _sse_subscribers.append(q)

    async def stream():
        try:
            yield "retry: 3000\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(q.get(), timeout=25)
                    yield f"event: {event}\ndata: 1\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            if q in _sse_subscribers:
                _sse_subscribers.remove(q)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/wines", response_model=WineResponse)
def create_wine(wine: WineCreate, db: Session = Depends(get_db), _=Depends(require_auth)):
    wine_data = wine.model_dump(exclude={'custom_values'})
    db_wine = WineLibrary(**wine_data)
    db.add(db_wine)
    db.commit()
    db.refresh(db_wine)
    _save_grape(db, wine.grape)
    if wine.custom_values:
        _save_custom_values(db, db_wine.id, wine.custom_values)
    cvs = {r.field_key: r.value for r in db.query(WineCustomValue).filter(WineCustomValue.wine_id == db_wine.id).all()}
    notify_clients()
    return _wine_to_dict(db_wine, cvs)


@app.get("/wines/{wine_id}", response_model=WineResponse)
def get_wine(wine_id: int, db: Session = Depends(get_db), _=Depends(require_login_or_kiosk)):
    wine = db.get(WineLibrary, wine_id)
    if not wine:
        raise HTTPException(status_code=404, detail="Wein nicht gefunden")
    cvs = {r.field_key: r.value for r in db.query(WineCustomValue).filter(WineCustomValue.wine_id == wine_id).all()}
    return _wine_to_dict(wine, cvs)


@app.put("/wines/{wine_id}", response_model=WineResponse)
def update_wine(wine_id: int, wine_update: WineUpdate, db: Session = Depends(get_db), _=Depends(require_auth)):
    wine = db.get(WineLibrary, wine_id)
    if not wine:
        raise HTTPException(status_code=404, detail="Wein nicht gefunden")
    for field, value in wine_update.model_dump(exclude_unset=True, exclude={'custom_values'}).items():
        setattr(wine, field, value)
    wine.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(wine)
    _save_grape(db, wine.grape)
    if wine_update.custom_values is not None:
        _save_custom_values(db, wine_id, wine_update.custom_values)
    cvs = {r.field_key: r.value for r in db.query(WineCustomValue).filter(WineCustomValue.wine_id == wine_id).all()}
    notify_clients()
    return _wine_to_dict(wine, cvs)


@app.put("/wines/batch")
def batch_update_wines(data: WineBatchUpdate, db: Session = Depends(get_db), _=Depends(require_auth)):
    if not data.ids:
        raise HTTPException(status_code=400, detail="Keine IDs angegeben")
    updates = data.updates.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Keine Felder zum Aktualisieren")
    wines = db.query(WineLibrary).filter(WineLibrary.id.in_(data.ids)).all()
    for wine in wines:
        for field, value in updates.items():
            setattr(wine, field, value)
        wine.updated_at = datetime.utcnow()
    db.commit()
    notify_clients()
    return {"updated": len(wines)}


@app.delete("/wines/{wine_id}")
def delete_wine(wine_id: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    wine = db.get(WineLibrary, wine_id)
    if not wine:
        raise HTTPException(status_code=404, detail="Wein nicht gefunden")
    db.query(WineCustomValue).filter(WineCustomValue.wine_id == wine_id).delete()
    db.delete(wine)
    db.commit()
    notify_clients()
    return {"message": "Wein gelöscht"}


# ── Library endpoints ─────────────────────────────────────────────────────────

@app.get("/library", response_model=List[WineResponse])
def get_library(db: Session = Depends(get_db), _=Depends(require_login)):
    wines = db.query(WineLibrary).order_by(WineLibrary.saved_at.desc()).all()
    cv_map = _load_cvs(db, [w.id for w in wines])
    return [_wine_to_dict(w, cv_map.get(w.id)) for w in wines]


@app.get("/library/search")
def search_library(q: str, db: Session = Depends(get_db), _=Depends(require_login)):
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
            "wineapi_id": e.wineapi_id, "quantity": e.quantity,
        }
        for e in rows
    ]


@app.put("/library/{entry_id}", response_model=WineResponse)
def update_library_entry(entry_id: int, data: WineUpdate, db: Session = Depends(get_db), _=Depends(require_auth)):
    entry = db.get(WineLibrary, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Eintrag nicht gefunden")
    for field, value in data.model_dump(exclude_unset=True, exclude={'custom_values'}).items():
        setattr(entry, field, value)
    entry.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(entry)
    if data.custom_values is not None:
        _save_custom_values(db, entry_id, data.custom_values)
    cvs = {r.field_key: r.value for r in db.query(WineCustomValue).filter(WineCustomValue.wine_id == entry_id).all()}
    notify_clients()
    return _wine_to_dict(entry, cvs)


@app.delete("/library/{entry_id}")
def delete_library_entry(entry_id: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    entry = db.get(WineLibrary, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Eintrag nicht gefunden")
    db.query(WineCustomValue).filter(WineCustomValue.wine_id == entry_id).delete()
    db.delete(entry)
    db.commit()
    notify_clients()
    return {"ok": True}


# ── Lookup ───────────────────────────────────────────────────────────────────

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


@app.get("/image-search")
async def image_search(q: str = Query(..., min_length=1), _=Depends(require_login)):
    if not GOOGLE_CSE_KEY or not GOOGLE_CSE_ID:
        raise HTTPException(status_code=503, detail="Google Image Search nicht konfiguriert")
    params = {
        "key": GOOGLE_CSE_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": q,
        "searchType": "image",
        "num": 10,
        "safe": "active",
        "imgType": "photo",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://www.googleapis.com/customsearch/v1", params=params)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Google API Fehler")
        items = resp.json().get("items") or []
        return [
            {
                "url": item.get("link", ""),
                "thumbnail": item.get("image", {}).get("thumbnailLink", item.get("link", "")),
                "title": item.get("title", ""),
            }
            for item in items
            if item.get("link")
        ]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="Google API nicht erreichbar")


@app.post("/upload-from-url")
async def upload_from_url(body: dict, _=Depends(require_auth)):
    url = (body.get("url") or "").strip()
    if not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Nur HTTPS-URLs erlaubt")
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True,
                                     headers={"User-Agent": "KellerLog/1.5"}) as client:
            resp = await client.get(url)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Bild konnte nicht geladen werden")
        content_type = resp.headers.get("content-type", "").split(";")[0].strip()
        if not content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="URL ist kein Bild")
        data = resp.content
        if not _valid_image_header(data[:12]):
            raise HTTPException(status_code=400, detail="Ungültiges Bildformat")
        ext_map = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}
        ext = ext_map.get(content_type, ".jpg")
        filename = f"{uuid.uuid4()}{ext}"
        dest = IMAGES_DIR / filename
        dest.write_bytes(data)
        return {"url": f"/api/images/{filename}"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="Bild konnte nicht geladen werden")


@app.get("/lookup/{barcode}")
def lookup_barcode(barcode: str, db: Session = Depends(get_db), _=Depends(require_login)):
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
            "quantity": lib.quantity,
        }
    return None


_EXPORT_FIELDS = [
    'name', 'producer', 'vintage', 'type', 'grape', 'region', 'country',
    'location', 'quantity', 'price', 'alcohol', 'rating', 'body', 'acidity',
    'pairings', 'description', 'notes', 'barcode', 'image_url', 'wineapi_id',
]


@app.get("/export/json")
def export_json(db: Session = Depends(get_db), _=Depends(require_login)):
    wines = db.query(WineLibrary).order_by(WineLibrary.saved_at.desc()).all()
    data = [{f: getattr(w, f, None) for f in _EXPORT_FIELDS} for w in wines]
    return Response(
        content=json.dumps(data, indent=2, ensure_ascii=False),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=kellerlog_export.json"},
    )


@app.get("/export/csv")
def export_csv(db: Session = Depends(get_db), _=Depends(require_login)):
    wines = db.query(WineLibrary).order_by(WineLibrary.saved_at.desc()).all()
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

    def _make_entry(row: dict) -> WineLibrary:
        def _int(v): return int(v) if str(v).strip() not in ('', 'None', 'null') else None
        def _float(v): return float(v) if str(v).strip() not in ('', 'None', 'null') else None
        return WineLibrary(
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
        exists = db.query(WineLibrary).filter(
            func.lower(WineLibrary.name) == name.lower(),
            func.lower(WineLibrary.producer) == producer.lower(),
        ).first()
        if exists:
            skipped += 1
            continue
        db.add(_make_entry(row))
        created += 1

    db.commit()
    return {"created": created, "skipped": skipped}


@app.get("/stats")
def get_stats(db: Session = Depends(get_db), _=Depends(require_login)):
    wines = db.query(WineLibrary).filter(WineLibrary.quantity > 0).all()
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
