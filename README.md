# KellerLog

A self-hosted wine cellar management app. Track your collection, scan barcodes, manage inventory, and share a read-only kiosk view for guests.

![KellerLog Banner](frontend/static/logo/kellerlog-banner.png)

## Features

- **Wine collection** — add, edit, and delete wines with photos, tasting notes, ratings, and food pairings
- **Barcode scanner** — scan a wine bottle to auto-fill details via the WineAPI
- **Inventory mode** — quickly adjust bottle counts with +/− controls
- **Kiosk view** — a clean, read-only wine list at `/kiosk` for guests or a wall display
- **Wine map** — world map showing where your wines come from
- **Import / Export** — backup and restore your collection as JSON or CSV
- **Branding** — customize the title, logo, and accent color
- **i18n** — German and English UI

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

Edit `.env` and add your WineAPI key if you want barcode lookup (optional):

```env
WINEAPI_KEY=your_wineapi_key_here
```

Start the app:

```bash
docker compose up -d
```

Open [http://localhost:8080](http://localhost:8080).

### Updating

```bash
docker compose pull
docker compose up -d --build
```

## Configuration

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `WINEAPI_KEY` | No | API key for barcode lookup ([wineapi.io](https://wineapi.io)) |

### Branding

All branding settings (app name, subtitle, accent color, logo) are configurable through the UI — click the palette icon in the top-right menu. Settings are stored per-browser in localStorage.

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

## License

MIT
