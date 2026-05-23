# KellerLog

A self-hosted wine cellar management app. Track your collection, scan barcodes, manage inventory, and share a read-only kiosk view for guests.

![KellerLog Banner](frontend/static/logo/kellerlog-banner.png)

## Screenshots

| Collection | Inventory Mode | Wine Details |
|:---:|:---:|:---:|
| ![Collection view](docs/screenshots/collection.png) | ![Inventory mode](docs/screenshots/inventory.png) | ![Wine details](docs/screenshots/description.png) |

## Features

- **Wine collection** — add, edit, and delete wines with photos, tasting notes, ratings, and food pairings
- **Barcode scanner** — scan a wine bottle to auto-fill details via the WineAPI
- **Inventory mode** — quickly adjust bottle counts with +/− controls; wines with zero bottles are removed when you exit
- **Kiosk view** — a clean, read-only wine list at `/kiosk` for guests or a wall display
- **Glass wine mode** — mark wines as available by the glass, with optional per-glass price; filterable in kiosk view
- **Wine map** — world map showing where your wines come from, with automatic geocoding for unknown regions via Nominatim
- **Import / Export** — backup and restore your collection as JSON or CSV
- **Branding** — customize the title, logo, accent color, and dark mode
- **PWA / installable** — install as a home screen app on mobile and desktop
- **i18n** — German and English UI

## Docker Images

Pre-built images are published to GitHub Container Registry on every release:

| Image | Tags |
|-------|------|
| `ghcr.io/krapfalat/kellerlog-frontend` | `latest` (release), `edge` (main) |
| `ghcr.io/krapfalat/kellerlog-backend` | `latest` (release), `edge` (main) |

Both images are built for `linux/amd64` and `linux/arm64`.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | SvelteKit (SPA, static adapter) |
| Backend | FastAPI + SQLAlchemy |
| Database | SQLite |
| Proxy | nginx |
| Deployment | Docker Compose |

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Installation

```bash
git clone https://github.com/KrapfalAT/kellerlog.git
cd kellerlog
cp .env.example .env
```

Edit `.env` before the first start:

```env
# Required: protects all write operations (add/edit/delete wines, upload, import)
# Generate with: python3 -c "import secrets; print(secrets.token_hex(32))"
KELLERLOG_ADMIN_KEY=your_admin_key_here

# Optional: enables barcode lookup — get a key at https://wineapi.io
WINEAPI_KEY=your_wineapi_key_here
```

> If `KELLERLOG_ADMIN_KEY` is not set, a random key is generated at startup and printed to the container logs. Set it explicitly so the key survives container restarts.

Pull the pre-built images and start:

```bash
docker compose pull
docker compose up -d
```

Open [http://localhost:8080](http://localhost:8080).

> **Build locally instead:** comment out the `image:` lines and uncomment the `build:` lines in `docker-compose.yml`, then run `docker compose up -d --build`.

### Updating

```bash
docker compose pull
docker compose up -d
```

## Configuration

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `KELLERLOG_ADMIN_KEY` | Recommended | Protects all write operations. Auto-generated at startup if not set (printed to logs). |
| `WINEAPI_KEY` | No | API key for barcode lookup ([wineapi.io](https://wineapi.io)) |

### Branding

All branding settings (app name, subtitle, accent color, logo, dark mode) are configurable through the UI — click the palette icon in the top-right menu. Settings are stored per-browser in localStorage.

### Data

Wine data and uploaded images are stored in the `kellerlog/` directory (created automatically on first run). Back it up to keep your collection safe.

## Routes

| Path | Description |
|------|-------------|
| `/` | Main collection view (private) |
| `/kiosk` | Read-only guest view |

## API

The backend exposes a REST API at `/api/`:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/wines` | List all wines |
| `POST` | `/api/wines` | Add a wine |
| `PUT` | `/api/wines/{id}` | Update a wine |
| `DELETE` | `/api/wines/{id}` | Delete a wine |
| `GET` | `/api/lookup/{barcode}` | Barcode lookup |
| `GET` | `/api/stats` | Collection statistics |
| `GET` | `/api/export/json` | Export as JSON |
| `GET` | `/api/export/csv` | Export as CSV |
| `POST` | `/api/import` | Import JSON or CSV |

## AI Disclaimer

This project was built with the assistance of [Claude Code](https://claude.ai/code) by Anthropic. AI-generated code has been reviewed and tested, but may contain imperfections. Use at your own risk.

## License

MIT
