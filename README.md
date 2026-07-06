# KellerLog

A self-hosted wine cellar management app. Track your collection, scan barcodes, manage inventory, and share a read-only kiosk view for guests.

![KellerLog Banner](frontend/static/logo/kellerlog-banner.png)

## Screenshots

| Collection | Wine Details | Kiosk |
|:---:|:---:|:---:|
| ![Collection view](docs/screenshots/collection.png) | ![Wine details](docs/screenshots/description.png) | ![Inventory mode](docs/screenshots/inventory.png) |

---

## Features

**Collection management**
- Add, edit, and delete wines with photos, tasting notes, ratings, and food pairings
- Filter by type, sort by date / rating / quantity, full-text search
- Batch edit — select multiple wines and update type, region, or location at once
- Click any wine to open a detail panel with a full-screen image lightbox
- Audit trail — each entry records who created and last edited it, shown in the detail view

**Photo search**
- Paste an image straight from the clipboard (Ctrl+V) while adding or editing a wine
- Or search by name via the Brave Image Search API, with a Google Images link as fallback

**Custom fields**
- Define your own fields to track anything the built-in schema doesn't cover
- Configurable via the hamburger menu → **Custom Fields**; appear on every wine automatically

**By-the-glass mode**
- Mark a wine as available by the glass with its own price
- Shown separately in the kiosk view for restaurant- or event-style setups

**Barcode scanner**
- Scan a bottle's EAN/UPC to auto-fill wine details from the local library
- Works on mobile via the camera; also available as a manual text input

**Wine library**
- Shared database of wine metadata, separate from inventory counts
- Add any library entry to inventory with one click; edits propagate to the live collection
- Autocomplete while typing a wine name pulls from the library

**Inventory mode**
- Dedicated mode with +/− controls for fast stock adjustment
- Wines that reach zero bottles are removed automatically when you exit

**Kiosk view** (`/kiosk`)
- Clean, public, read-only wine list for guests or a wall display
- Configurable title, subtitle, map button, footer, drink-window display, and on/off toggle
- Real-time updates — refreshes automatically when the collection changes

**Drink window**
- Define rules per wine type (e.g. "drink Riesling between 3 and 8 years after vintage")
- Each wine card shows whether it's ready to drink, too young, or past peak

**Real-time sync**
- Dashboard and kiosk update instantly across all connected devices via Server-Sent Events (SSE)
- No polling — changes appear within a second of being saved

**Wine map**
- World map showing where your wines come from
- Automatic geocoding for unknown regions via Nominatim

**Import / Export**
- Full backup and restore as JSON or CSV

**Branding**
- Customize the app title, subtitle, logo, accent color, and dark/light mode
- Settings are stored server-side and apply to all users and devices immediately

**User accounts**
- JWT-based auth with Admin and Viewer roles
- Admins have full read/write access; Viewers are read-only

**PWA**
- Installable as a home-screen app on iOS, Android, and desktop
- Service worker caches the app shell; API calls always go to the network

**i18n**
- German and English UI; switchable per user

**Security**
- Login is rate-limited (5/minute, 20/hour per IP) to slow down brute-force attempts
- Strict CSP and security headers (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`) on every response
- Interactive API docs (Swagger/ReDoc) are disabled; the OpenAPI schema is not exposed
- Cross-origin access is opt-in via `ALLOWED_ORIGINS` — closed by default

---

## Docker Images

Pre-built images are published to GitHub Container Registry on every release:

| Image | Tags |
|-------|------|
| `ghcr.io/krapfalat/kellerlog-frontend` | `latest` (stable release), `edge` (main branch) |
| `ghcr.io/krapfalat/kellerlog-backend` | `latest` (stable release), `edge` (main branch) |

Both images are built for `linux/amd64` and `linux/arm64`.

---

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Installation

**1. Create `docker-compose.yml`**

```yaml
services:
  backend:
    image: ghcr.io/krapfalat/kellerlog-backend:latest
    volumes:
      - ./kellerlog:/app/data
    environment:
      - KELLERLOG_SECRET_KEY=${KELLERLOG_SECRET_KEY}
      - KELLERLOG_ADMIN_USER=${KELLERLOG_ADMIN_USER:-admin}
      - KELLERLOG_ADMIN_PASSWORD=${KELLERLOG_ADMIN_PASSWORD}
    restart: unless-stopped

  frontend:
    image: ghcr.io/krapfalat/kellerlog-frontend:latest
    ports:
      - "8080:80"
    depends_on:
      - backend
    environment:
      - BACKEND_HOST=backend
    restart: unless-stopped
```

**2. Create `.env`**

```env
# Required — generate with: python3 -c "import secrets; print(secrets.token_hex(32))"
# Must remain stable across restarts; changing it invalidates all sessions.
KELLERLOG_SECRET_KEY=your_secret_key_here

# Admin account (created on first run if no users exist)
KELLERLOG_ADMIN_USER=admin
KELLERLOG_ADMIN_PASSWORD=your_admin_password_here

# Optional — enables photo search when adding/editing a wine
BRAVE_SEARCH_KEY=

# Optional — comma-separated CORS allow-list, only needed for cross-origin setups
ALLOWED_ORIGINS=
```

> If `KELLERLOG_ADMIN_PASSWORD` is not set, a random password is generated at startup and printed once to the container logs.

**3. Start**

```bash
docker compose up -d
```

Open [http://localhost:8080](http://localhost:8080) and log in.

### Updating

```bash
docker compose pull && docker compose up -d
```

---

## Configuration

### Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `KELLERLOG_SECRET_KEY` | **Yes** | — | JWT signing secret. Must persist across restarts. |
| `KELLERLOG_ADMIN_USER` | No | `admin` | Username for the initial admin account (first run only). |
| `KELLERLOG_ADMIN_PASSWORD` | Recommended | *(auto-generated)* | Password for the initial admin account. |
| `BACKEND_HOST` | No | `backend` | Hostname of the backend service as seen by nginx. |
| `BRAVE_SEARCH_KEY` | No | — | Brave Search API key. Enables photo search when adding/editing a wine; omit to disable. |
| `ALLOWED_ORIGINS` | No | *(none)* | Comma-separated list of allowed CORS origins, e.g. for accessing the API from a different domain. |

### User management

Admins can create, edit, and delete user accounts via the hamburger menu → **User Management**. Two roles:

- **Admin** — full read/write access
- **Viewer** — read-only; cannot add, edit, or delete wines

### Kiosk

The kiosk view at `/kiosk` is publicly accessible without login. Configure it via the hamburger menu → **Kiosk Settings**:

- Enable or disable the kiosk entirely
- Set the title and subtitle shown in the kiosk header
- Toggle the map button, footer, and drink-window indicator

### Branding

App name, logo, accent color, and dark mode are configurable through the hamburger menu → **Branding**. Settings are stored server-side and apply immediately to all devices.

### Data

All wine data and uploaded images are stored in the `kellerlog/` directory (created automatically). Back it up regularly.

---

## Routes

| Path | Auth | Description |
|------|------|-------------|
| `/` | Required | Main collection view |
| `/login` | — | Login page |
| `/kiosk` | — | Read-only guest view |

---

## API

The backend exposes a REST API at `/api/`. Write endpoints require a `Bearer` token obtained via `POST /api/auth/login`.

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/auth/login` | — | Login; returns JWT |
| `GET` | `/api/auth/me` | Any | Current user info |
| `GET` | `/api/auth/users` | Admin | List all users |
| `POST` | `/api/auth/users` | Admin | Create user |
| `PUT` | `/api/auth/users/{id}` | Admin | Update user |
| `DELETE` | `/api/auth/users/{id}` | Admin | Delete user |

### Wines

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/wines` | Login or Kiosk | List wines |
| `POST` | `/api/wines` | Admin | Add wine |
| `PUT` | `/api/wines/{id}` | Admin | Update wine |
| `PUT` | `/api/wines/batch` | Admin | Batch update |
| `DELETE` | `/api/wines/{id}` | Admin | Delete wine |
| `GET` | `/api/stats` | Login | Collection statistics |
| `GET` | `/api/lookup/{barcode}` | Login | Local library barcode lookup |
| `GET` | `/api/export/json` | Login | Export as JSON |
| `GET` | `/api/export/csv` | Login | Export as CSV |
| `POST` | `/api/import` | Admin | Import JSON or CSV |
| `GET` | `/api/image-search` | Login | Photo search via Brave Image Search API |

### Library

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/library` | Login | List library entries |
| `GET` | `/api/library/search?q=` | Login | Search library |
| `PUT` | `/api/library/{id}` | Admin | Update library entry |
| `DELETE` | `/api/library/{id}` | Admin | Delete library entry |

### Settings & configuration

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/settings` | Login or Kiosk | App and kiosk settings |
| `PUT` | `/api/settings` | Admin | Update settings |
| `GET` | `/api/drink-rules` | Login or Kiosk | List drink-window rules |
| `POST` | `/api/drink-rules` | Admin | Create rule |
| `PUT` | `/api/drink-rules/{id}` | Admin | Update rule |
| `DELETE` | `/api/drink-rules/{id}` | Admin | Delete rule |
| `GET` | `/api/custom-fields` | Login or Kiosk | List custom fields |
| `POST` | `/api/custom-fields` | Admin | Create custom field |
| `PUT` | `/api/custom-fields/{id}` | Admin | Update custom field |
| `DELETE` | `/api/custom-fields/{id}` | Admin | Delete custom field |

### Real-time

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/events` | Login or Kiosk | SSE stream; emits `wines` event on any collection change |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | SvelteKit (SPA, static adapter) + Svelte 5 |
| Backend | FastAPI + SQLAlchemy |
| Database | SQLite |
| Proxy | nginx |
| Deployment | Docker Compose |
| Real-time | Server-Sent Events (SSE) |

---

## AI Disclaimer

This project was built with the assistance of [Claude Code](https://claude.ai/code) by Anthropic. AI-generated code has been reviewed and tested, but may contain imperfections. Use at your own risk.

## License

MIT
