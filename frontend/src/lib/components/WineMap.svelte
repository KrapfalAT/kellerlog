<script>
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';
  import 'leaflet/dist/leaflet.css';
  import { t } from '$lib/stores/i18n.js';

  export let wines = [];

  const dispatch = createEventDispatcher();

  let mapEl;
  let map = null;

  const esc = s => String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');

  // Canonical country centre-points
  const COUNTRY_COORDS = {
    'Austria': [47.5, 14.5], 'France': [46.2, 2.2], 'Italy': [42.8, 12.6],
    'Spain': [40.4, -3.7], 'Germany': [51.2, 10.4], 'Portugal': [39.6, -8.0],
    'Switzerland': [47.0, 8.3], 'Greece': [39.1, 21.8], 'Hungary': [47.2, 19.5],
    'Romania': [45.9, 24.9], 'Bulgaria': [42.7, 25.5], 'Croatia': [45.1, 16.4],
    'Slovenia': [46.1, 14.8], 'Serbia': [44.0, 21.0], 'Georgia': [42.3, 43.4],
    'Moldova': [47.4, 28.4], 'Czech Republic': [49.8, 15.5], 'Slovakia': [48.7, 19.7],
    'Luxembourg': [49.8, 6.1], 'Turkey': [38.9, 35.2], 'Lebanon': [33.9, 35.5],
    'Israel': [31.5, 34.8], 'Cyprus': [35.1, 33.4],
    'Argentina': [-34.0, -64.0], 'Chile': [-33.5, -70.6], 'Uruguay': [-32.5, -55.8],
    'Brazil': [-15.8, -47.9], 'USA': [37.1, -95.7], 'United States': [37.1, -95.7],
    'Canada': [56.1, -106.3], 'Mexico': [23.6, -102.6],
    'Australia': [-25.3, 133.8], 'New Zealand': [-40.9, 174.9],
    'South Africa': [-29.0, 25.1], 'China': [35.9, 104.2], 'Japan': [36.2, 138.3],
    'India': [20.6, 78.9], 'Morocco': [31.8, -7.1],
    'United Kingdom': [54.0, -2.5], 'England': [52.5, -1.5],
  };

  // Precise coordinates for named wine regions / cities
  const REGION_COORDS = {
    // Austria
    'Salzburg': [47.80, 13.04], 'Wien': [48.21, 16.37], 'Vienna': [48.21, 16.37],
    'Tirol': [47.27, 11.39], 'Burgenland': [47.51, 16.53], 'Steiermark': [47.07, 15.44],
    'Niederösterreich': [48.40, 15.60], 'Oberösterreich': [48.06, 13.99],
    'Vorarlberg': [47.25, 9.92], 'Kärnten': [46.72, 14.30],
    'Wachau': [48.37, 15.44], 'Kamptal': [48.56, 15.68], 'Kremstal': [48.41, 15.61],
    // Italy
    'Piemonte': [44.84, 7.97], 'Piedmont': [44.84, 7.97],
    'Toskana': [43.77, 11.25], 'Tuscany': [43.77, 11.25],
    'Veneto': [45.44, 12.33], 'Lombardei': [45.47, 9.19], 'Lombardy': [45.47, 9.19],
    'Sizilien': [37.60, 14.00], 'Sicily': [37.60, 14.00],
    'Lazio': [41.90, 12.48], 'Apulien': [41.12, 16.87], 'Puglia': [41.12, 16.87],
    'Emilia-Romagna': [44.50, 11.34], 'Abruzzo': [42.35, 13.39],
    'Friuli': [46.06, 13.24], 'Umbria': [43.11, 12.39], 'Campania': [40.84, 14.25],
    // France
    'Bordeaux': [44.84, -0.58], 'Burgund': [47.05, 4.84], 'Burgundy': [47.05, 4.84],
    'Champagne': [49.05, 4.35], 'Provence': [43.53, 5.45], 'Loire': [47.39, 0.69],
    'Rhône': [45.74, 4.84], 'Alsace': [48.32, 7.44], 'Elsass': [48.32, 7.44],
    'Languedoc': [43.61, 3.88], 'Roussillon': [42.69, 2.89], 'Beaujolais': [46.05, 4.65],
    // Germany
    'Mosel': [50.00, 7.08], 'Rheingau': [50.00, 8.00], 'Baden': [48.30, 7.90],
    'Franken': [49.80, 10.20], 'Pfalz': [49.40, 8.10], 'Württemberg': [48.78, 9.18],
    'Rheinhessen': [49.80, 8.30], 'Nahe': [49.78, 7.85], 'Ahr': [50.53, 6.98],
    // Spain
    'Rioja': [42.46, -2.45], 'Katalonien': [41.58, 1.52], 'Catalonia': [41.58, 1.52],
    'Ribera del Duero': [41.60, -3.70], 'Galicia': [42.60, -7.86],
    // Portugal
    'Douro': [41.16, -7.80], 'Alentejo': [38.50, -7.90], 'Vinho Verde': [41.55, -8.43],
  };

  // Map any name (German country names, region names) → canonical English country name
  const TO_COUNTRY = {
    'Frankreich': 'France', 'Italien': 'Italy', 'Spanien': 'Spain',
    'Deutschland': 'Germany', 'Österreich': 'Austria', 'Schweiz': 'Switzerland',
    'Ungarn': 'Hungary', 'Rumänien': 'Romania', 'Bulgarien': 'Bulgaria',
    'Griechenland': 'Greece', 'Tschechien': 'Czech Republic', 'Slowakei': 'Slovakia',
    'Türkei': 'Turkey', 'Marokko': 'Morocco', 'Südafrika': 'South Africa',
    'Australien': 'Australia', 'Neuseeland': 'New Zealand', 'Kanada': 'Canada',
    'Argentinien': 'Argentina', 'Brasilien': 'Brazil',
    // Austrian regions
    'Salzburg': 'Austria', 'Wien': 'Austria', 'Vienna': 'Austria',
    'Tirol': 'Austria', 'Burgenland': 'Austria', 'Steiermark': 'Austria',
    'Niederösterreich': 'Austria', 'Oberösterreich': 'Austria',
    'Vorarlberg': 'Austria', 'Kärnten': 'Austria',
    'Wachau': 'Austria', 'Kamptal': 'Austria', 'Kremstal': 'Austria',
    // Italian regions
    'Piemonte': 'Italy', 'Piedmont': 'Italy', 'Toskana': 'Italy', 'Tuscany': 'Italy',
    'Veneto': 'Italy', 'Lombardei': 'Italy', 'Lombardy': 'Italy',
    'Sizilien': 'Italy', 'Sicily': 'Italy', 'Lazio': 'Italy',
    'Apulien': 'Italy', 'Puglia': 'Italy', 'Emilia-Romagna': 'Italy',
    'Abruzzo': 'Italy', 'Friuli': 'Italy', 'Umbria': 'Italy', 'Campania': 'Italy',
    'Calabria': 'Italy', 'Basilicata': 'Italy', 'Molise': 'Italy',
    'Sardinia': 'Italy', 'Sardinien': 'Italy', 'Marche': 'Italy',
    'Trentino': 'Italy', 'Alto Adige': 'Italy', 'Südtirol': 'Italy', 'Valle d\'Aosta': 'Italy',
    // French regions
    'Bordeaux': 'France', 'Burgund': 'France', 'Burgundy': 'France',
    'Champagne': 'France', 'Alsace': 'France', 'Elsass': 'France',
    'Rhône': 'France', 'Loire': 'France', 'Provence': 'France',
    'Languedoc': 'France', 'Roussillon': 'France', 'Beaujolais': 'France',
    // German regions
    'Mosel': 'Germany', 'Rheingau': 'Germany', 'Baden': 'Germany',
    'Franken': 'Germany', 'Pfalz': 'Germany', 'Württemberg': 'Germany',
    'Rheinhessen': 'Germany', 'Nahe': 'Germany', 'Ahr': 'Germany',
    // Spanish regions
    'Rioja': 'Spain', 'Katalonien': 'Spain', 'Catalonia': 'Spain',
    'Ribera del Duero': 'Spain', 'Galicia': 'Spain',
    // Portuguese regions
    'Douro': 'Portugal', 'Alentejo': 'Portugal', 'Vinho Verde': 'Portugal',
  };

  const GEOCACHE_KEY = 'kellerlog_geocache';
  function loadGeoCache() {
    try { return JSON.parse(localStorage.getItem(GEOCACHE_KEY) || '{}'); } catch { return {}; }
  }
  function saveGeoCache(c) {
    try { localStorage.setItem(GEOCACHE_KEY, JSON.stringify(c)); } catch {}
  }

  function resolveCountry(name) {
    if (!name) return null;
    const n = name.trim();
    if (COUNTRY_COORDS[n]) return n;
    if (TO_COUNTRY[n]) return TO_COUNTRY[n];
    const lower = n.toLowerCase();
    for (const k of Object.keys(COUNTRY_COORDS)) {
      if (k.toLowerCase() === lower) return k;
    }
    for (const [alias, country] of Object.entries(TO_COUNTRY)) {
      if (alias.toLowerCase() === lower) return country;
    }
    return null;
  }

  function getRegionCoords(name) {
    if (!name) return null;
    const n = name.trim();
    if (REGION_COORDS[n]) return REGION_COORDS[n];
    const lower = n.toLowerCase();
    for (const [k, v] of Object.entries(REGION_COORDS)) {
      if (k.toLowerCase() === lower) return v;
    }
    const country = resolveCountry(name);
    return country ? (COUNTRY_COORDS[country] || null) : null;
  }

  const ZOOM_THRESHOLD = 5;

  function makeIcon(L, count, size = 34) {
    return L.divIcon({
      className: '',
      html: `<div style="
        width:${size}px;height:${size}px;
        background:#7B1D3F;color:white;
        border-radius:50%;border:3px solid white;
        box-shadow:0 2px 8px rgba(0,0,0,0.35);
        display:flex;align-items:center;justify-content:center;
        font-weight:700;font-size:${size > 38 ? 15 : 13}px;
        cursor:pointer;font-family:inherit;
      ">${count}</div>`,
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
      popupAnchor: [0, -(size / 2 + 4)],
    });
  }

  function buildPopup(label, list) {
    const rows = list.map(w =>
      `<li data-wine-id="${esc(w.id)}" style="padding:6px 0;border-top:1px solid #f0e8ed;display:flex;justify-content:space-between;align-items:center;gap:10px;font-size:13px;cursor:pointer;border-radius:4px" onmouseover="this.style.background='#fdf5f8'" onmouseout="this.style.background=''">
        <span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#3d0d1c;font-weight:600">
          ${esc(w.name)}${w.vintage ? ` <span style="color:#aaa;font-weight:400">${esc(w.vintage)}</span>` : ''}
        </span>
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#7B1D3F" stroke-width="2.5" style="flex-shrink:0"><polyline points="9 18 15 12 9 6"/></svg>
      </li>`
    ).join('');
    return `<div style="min-width:200px;max-width:280px">
      <div style="font-size:15px;font-weight:700;color:#7B1D3F;margin-bottom:8px">${esc(label)}</div>
      <ul style="margin:0;padding:0;list-style:none">${rows}</ul>
    </div>`;
  }

  onMount(async () => {
    const L = await import('leaflet');

    map = L.map(mapEl, { zoomControl: true }).setView([30, 15], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© <a href="https://openstreetmap.org">OpenStreetMap</a>',
      maxZoom: 13,
    }).addTo(map);

    // Group wines by their location key (region preferred over country)
    const byLocation = {};
    for (const wine of wines) {
      const key = (wine.region || wine.country || '').trim() || '__unknown__';
      if (!byLocation[key]) byLocation[key] = [];
      byLocation[key].push(wine);
    }

    // Build country-level groups (merge all locations in same country)
    const byCountry = {};
    for (const [loc, list] of Object.entries(byLocation)) {
      if (loc === '__unknown__') continue;
      const country = resolveCountry(loc);
      if (!country || !COUNTRY_COORDS[country]) continue;
      if (!byCountry[country]) byCountry[country] = [];
      byCountry[country].push(...list);
    }

    const countryLayer = L.layerGroup();
    const regionLayer  = L.layerGroup();
    const countryBounds = [];

    // Country markers
    for (const [country, list] of Object.entries(byCountry)) {
      const coords = COUNTRY_COORDS[country];
      countryBounds.push(coords);
      const icon = makeIcon(L, list.length, list.length >= 10 ? 44 : list.length >= 5 ? 40 : 34);
      L.marker(coords, { icon })
        .bindPopup(buildPopup(country, list), { maxWidth: 300 })
        .addTo(countryLayer);
    }

    // Region markers (one per location key)
    for (const [loc, list] of Object.entries(byLocation)) {
      if (loc === '__unknown__') continue;
      const coords = getRegionCoords(loc);
      if (!coords) continue;
      const icon = makeIcon(L, list.length, 34);
      L.marker(coords, { icon })
        .bindPopup(buildPopup(loc, list), { maxWidth: 300 })
        .addTo(regionLayer);
    }

    // Popup click → open detail
    map.on('popupopen', (e) => {
      const container = e.popup.getElement();
      container.querySelectorAll('[data-wine-id]').forEach(el => {
        L.DomEvent.on(el, 'click', () => {
          const id = parseInt(el.dataset.wineId);
          const wine = wines.find(w => w.id === id);
          if (wine) { map.closePopup(); dispatch('selectWine', wine); }
        });
      });
    });

    function updateLayers() {
      const zoom = map.getZoom();
      if (zoom >= ZOOM_THRESHOLD) {
        countryLayer.removeFrom(map);
        regionLayer.addTo(map);
      } else {
        regionLayer.removeFrom(map);
        countryLayer.addTo(map);
      }
    }

    map.on('zoomend', updateLayers);
    countryLayer.addTo(map);

    // Fit to markers
    if (countryBounds.length > 0) {
      setTimeout(() => {
        if (countryBounds.length === 1) {
          map.setView(countryBounds[0], 5);
        } else {
          map.fitBounds(countryBounds, { padding: [40, 40], maxZoom: 6 });
        }
        map.invalidateSize();
      }, 100);
    } else {
      setTimeout(() => map.invalidateSize(), 100);
    }

    // Geocode unknown locations via Nominatim (results cached in localStorage)
    const geoCache = loadGeoCache();
    const unknowns = Object.keys(byLocation).filter(
      loc => loc !== '__unknown__' && !getRegionCoords(loc)
    );

    let needsDelay = false;
    for (const loc of unknowns) {
      let coords;
      if (loc in geoCache) {
        coords = geoCache[loc];
      } else {
        if (needsDelay) await new Promise(r => setTimeout(r, 1100));
        needsDelay = true;
        try {
          const res = await fetch(
            `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(loc)}&format=json&limit=1`,
            { headers: { 'Accept-Language': 'en' } }
          );
          const data = await res.json();
          coords = data[0] ? [parseFloat(data[0].lat), parseFloat(data[0].lon)] : null;
        } catch {
          coords = null;
        }
        geoCache[loc] = coords;
        saveGeoCache(geoCache);
      }
      if (!coords) continue;
      const list = byLocation[loc];
      const icon = makeIcon(L, list.length, 34);
      L.marker(coords, { icon })
        .bindPopup(buildPopup(loc, list), { maxWidth: 300 })
        .addTo(regionLayer);
    }
  });

  onDestroy(() => { if (map) map.remove(); });

  $: byCountry = (() => {
    const groups = {};
    for (const w of wines) {
      const key = (w.region || w.country || '').trim();
      if (!key) continue;
      const country = resolveCountry(key) || key;
      groups[country] = (groups[country] || 0) + 1;
    }
    return Object.entries(groups).sort((a, b) => b[1] - a[1]);
  })();

  $: unknownCount = wines.filter(w => {
    const key = (w.region || w.country || '').trim();
    return !key || !resolveCountry(key);
  }).length;
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
<div class="overlay" on:click|self={() => dispatch('close')}>
  <div class="panel">
    <header class="panel-header">
      <div class="panel-title">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/>
          <line x1="8" y1="2" x2="8" y2="18"/>
          <line x1="16" y1="6" x2="16" y2="22"/>
        </svg>
        {$t('nav_map')}
      </div>
      <button class="close-btn" on:click={() => dispatch('close')} aria-label={$t('modal_cancel')}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </header>

    <div class="map-container" bind:this={mapEl}></div>

    {#if byCountry.length > 0}
      <div class="legend">
        {#each byCountry as [country, count]}
          <span class="legend-item" class:unknown={!resolveCountry(country) && !COUNTRY_COORDS[country]}>
            {country}
            <span class="legend-count">{count}</span>
          </span>
        {/each}
        {#if unknownCount > 0}
          <span class="legend-item unknown">{$t('map_unknown')} <span class="legend-count">{unknownCount}</span></span>
        {/if}
      </div>
    {:else}
      <p class="empty-map">{$t('map_empty')}</p>
    {/if}
  </div>
</div>

<style>
  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(26, 13, 17, 0.65);
    backdrop-filter: blur(4px);
    z-index: 200;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
  }

  .panel {
    background: var(--surface);
    border-radius: 16px;
    width: 100%;
    max-width: 900px;
    max-height: 92vh;
    display: flex;
    flex-direction: column;
    box-shadow: var(--shadow-lg);
    overflow: hidden;
    animation: slideIn 0.2s ease;
  }

  @keyframes slideIn {
    from { transform: translateY(16px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
  }

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
  }

  .panel-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 700;
    color: var(--primary);
  }

  .close-btn {
    background: none;
    border: none;
    color: var(--text-muted);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4px;
    border-radius: 6px;
    transition: color 0.15s;
  }
  .close-btn:hover { color: var(--text); }

  .map-container {
    flex: 1;
    min-height: 380px;
  }

  .legend {
    padding: 12px 16px;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    border-top: 1px solid var(--border);
    max-height: 110px;
    overflow-y: auto;
    flex-shrink: 0;
  }

  .legend-item {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px;
    background: rgba(123, 29, 63, 0.08);
    color: var(--primary);
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
  }
  .legend-item.unknown {
    background: var(--surface-2);
    color: var(--text-muted);
  }
  .legend-count {
    background: var(--primary);
    color: white;
    border-radius: 20px;
    padding: 1px 6px;
    font-size: 11px;
    font-weight: 700;
  }
  .legend-item.unknown .legend-count { background: var(--text-muted); }

  .empty-map {
    padding: 20px;
    text-align: center;
    color: var(--text-muted);
    font-size: 14px;
    border-top: 1px solid var(--border);
  }
</style>
