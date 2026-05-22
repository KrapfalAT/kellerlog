const BASE = '/api';
const ADMIN_KEY_STORAGE = 'kellerlog_admin_key';

export const getAdminKey = () => {
  if (typeof localStorage === 'undefined') return '';
  return localStorage.getItem(ADMIN_KEY_STORAGE) || '';
};
export const setAdminKey = (key) => {
  if (typeof localStorage !== 'undefined') localStorage.setItem(ADMIN_KEY_STORAGE, key);
};

function authHeaders() {
  return { 'X-Admin-Key': getAdminKey() };
}

export async function getWines() {
  const r = await fetch(`${BASE}/wines`);
  if (!r.ok) throw new Error('Fehler beim Laden');
  return r.json();
}

export async function createWine(wine) {
  const r = await fetch(`${BASE}/wines`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(wine),
  });
  if (r.status === 401) throw new Error('UNAUTHORIZED');
  if (!r.ok) throw new Error('Fehler beim Speichern');
  return r.json();
}

export async function updateWine(id, wine) {
  const r = await fetch(`${BASE}/wines/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(wine),
  });
  if (r.status === 401) throw new Error('UNAUTHORIZED');
  if (!r.ok) throw new Error('Fehler beim Aktualisieren');
  return r.json();
}

export async function deleteWine(id) {
  const r = await fetch(`${BASE}/wines/${id}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
  if (r.status === 401) throw new Error('UNAUTHORIZED');
  if (!r.ok) throw new Error('Fehler beim Löschen');
}

export async function searchWines(q) {
  const r = await fetch(`${BASE}/search?q=${encodeURIComponent(q)}`);
  if (r.status === 502 || r.status === 503) throw new Error('API_UNAVAILABLE');
  if (!r.ok) return [];
  return r.json();
}

export async function getWineDetails(wineapiId) {
  const r = await fetch(`${BASE}/wine-details/${encodeURIComponent(wineapiId)}`);
  if (!r.ok) return null;
  return r.json();
}

export async function lookupBarcode(barcode) {
  const r = await fetch(`${BASE}/lookup/${barcode}`);
  if (!r.ok) return null;
  return r.json();
}

export async function uploadImage(file) {
  const fd = new FormData();
  fd.append('file', file);
  const r = await fetch(`${BASE}/upload`, { method: 'POST', headers: authHeaders(), body: fd });
  if (r.status === 401) throw new Error('UNAUTHORIZED');
  if (!r.ok) throw new Error('Upload fehlgeschlagen');
  const data = await r.json();
  return data.url;
}

export async function getStats() {
  const r = await fetch(`${BASE}/stats`);
  if (!r.ok) return null;
  return r.json();
}

export async function searchLibrary(q) {
  const r = await fetch(`${BASE}/library/search?q=${encodeURIComponent(q)}`);
  if (!r.ok) return [];
  const results = await r.json();
  return results.map(e => ({ ...e, source: 'local' }));
}

export async function getLibrary() {
  const r = await fetch(`${BASE}/library`);
  if (!r.ok) throw new Error('Fehler beim Laden der Bibliothek');
  return r.json();
}

export async function deleteLibraryEntry(id) {
  const r = await fetch(`${BASE}/library/${id}`, { method: 'DELETE', headers: authHeaders() });
  if (r.status === 401) throw new Error('UNAUTHORIZED');
  if (!r.ok) throw new Error('Fehler beim Löschen');
}

export async function exportWines(format) {
  const r = await fetch(`${BASE}/export/${format}`);
  if (!r.ok) throw new Error('Export fehlgeschlagen');
  const blob = await r.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `kellerlog_export.${format}`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function importWines(file) {
  const fd = new FormData();
  fd.append('file', file);
  const r = await fetch(`${BASE}/import`, { method: 'POST', headers: authHeaders(), body: fd });
  if (r.status === 401) throw new Error('UNAUTHORIZED');
  if (!r.ok) throw new Error('Import fehlgeschlagen');
  return r.json();
}
