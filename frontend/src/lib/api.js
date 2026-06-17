const BASE = '/api';
const AUTH_STORAGE = 'kellerlog_auth';

function getToken() {
  if (typeof localStorage === 'undefined') return '';
  try {
    const raw = localStorage.getItem(AUTH_STORAGE);
    return raw ? JSON.parse(raw).token || '' : '';
  } catch {
    return '';
  }
}

function authHeaders() {
  const token = getToken();
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

export async function login(username, password) {
  const r = await fetch(`${BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (r.status === 401) throw new Error('INVALID_CREDENTIALS');
  if (!r.ok) throw new Error('Login fehlgeschlagen');
  return r.json();
}

export async function getMe() {
  const r = await fetch(`${BASE}/auth/me`, { headers: authHeaders() });
  if (r.status === 401) throw new Error('UNAUTHORIZED');
  if (!r.ok) throw new Error('Fehler');
  return r.json();
}

export async function getUsers() {
  const r = await fetch(`${BASE}/auth/users`, { headers: authHeaders() });
  if (r.status === 401) throw new Error('UNAUTHORIZED');
  if (!r.ok) throw new Error('Fehler beim Laden');
  return r.json();
}

export async function createUser(data) {
  const r = await fetch(`${BASE}/auth/users`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(data),
  });
  if (r.status === 401) throw new Error('UNAUTHORIZED');
  if (!r.ok) throw new Error((await r.json()).detail || 'Fehler');
  return r.json();
}

export async function updateUser(id, data) {
  const r = await fetch(`${BASE}/auth/users/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(data),
  });
  if (r.status === 401) throw new Error('UNAUTHORIZED');
  if (!r.ok) throw new Error((await r.json()).detail || 'Fehler');
  return r.json();
}

export async function deleteUser(id) {
  const r = await fetch(`${BASE}/auth/users/${id}`, { method: 'DELETE', headers: authHeaders() });
  if (r.status === 401) throw new Error('UNAUTHORIZED');
  if (!r.ok) throw new Error((await r.json()).detail || 'Fehler');
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

export async function batchUpdateWines(ids, updates) {
  const r = await fetch(`${BASE}/wines/batch`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ ids, updates }),
  });
  if (r.status === 401) throw new Error('UNAUTHORIZED');
  if (!r.ok) throw new Error((await r.json()).detail || 'Fehler');
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

export async function updateLibraryEntry(id, data) {
  const r = await fetch(`${BASE}/library/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(data),
  });
  if (r.status === 401) throw new Error('UNAUTHORIZED');
  if (!r.ok) throw new Error('Fehler beim Aktualisieren');
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

export async function getGrapes() {
  const r = await fetch(`${BASE}/grapes`);
  if (!r.ok) return [];
  return r.json();
}

export async function getDrinkRules() {
  const r = await fetch(`${BASE}/drink-rules`);
  if (!r.ok) return [];
  return r.json();
}

export async function createDrinkRule(data) {
  const r = await fetch(`${BASE}/drink-rules`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(data),
  });
  if (r.status === 401) throw new Error('UNAUTHORIZED');
  if (!r.ok) throw new Error((await r.json()).detail || 'Fehler');
  return r.json();
}

export async function updateDrinkRule(id, data) {
  const r = await fetch(`${BASE}/drink-rules/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(data),
  });
  if (r.status === 401) throw new Error('UNAUTHORIZED');
  if (!r.ok) throw new Error('Fehler beim Speichern');
  return r.json();
}

export async function deleteDrinkRule(id) {
  const r = await fetch(`${BASE}/drink-rules/${id}`, { method: 'DELETE', headers: authHeaders() });
  if (r.status === 401) throw new Error('UNAUTHORIZED');
  if (!r.ok) throw new Error('Fehler beim Löschen');
}

export async function getSettings() {
  const r = await fetch(`${BASE}/settings`);
  if (!r.ok) return null;
  return r.json();
}

export async function updateSettings(data) {
  const r = await fetch(`${BASE}/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(data),
  });
  if (r.status === 401) throw new Error('UNAUTHORIZED');
  if (!r.ok) throw new Error('Fehler beim Speichern');
  return r.json();
}

export async function getCustomFields() {
  const r = await fetch(`${BASE}/custom-fields`);
  if (!r.ok) return [];
  return r.json();
}

export async function createCustomField(data) {
  const r = await fetch(`${BASE}/custom-fields`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(data),
  });
  if (r.status === 401) throw new Error('UNAUTHORIZED');
  if (!r.ok) throw new Error((await r.json()).detail || 'Fehler');
  return r.json();
}

export async function updateCustomField(id, data) {
  const r = await fetch(`${BASE}/custom-fields/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(data),
  });
  if (r.status === 401) throw new Error('UNAUTHORIZED');
  if (!r.ok) throw new Error('Fehler');
  return r.json();
}

export async function deleteCustomField(id) {
  const r = await fetch(`${BASE}/custom-fields/${id}`, { method: 'DELETE', headers: authHeaders() });
  if (r.status === 401) throw new Error('UNAUTHORIZED');
  if (!r.ok) throw new Error('Fehler');
}
