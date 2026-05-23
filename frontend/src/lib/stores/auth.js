import { writable, derived } from 'svelte/store';

const STORAGE_KEY = 'kellerlog_auth';

function isExpired(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return Date.now() >= payload.exp * 1000;
  } catch {
    return true;
  }
}

function loadStored() {
  if (typeof localStorage === 'undefined') return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (isExpired(data.token)) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return data;
  } catch {
    return null;
  }
}

function createAuth() {
  const { subscribe, set } = writable(loadStored());

  return {
    subscribe,
    login(data) {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
      }
      set(data);
    },
    logout() {
      if (typeof localStorage !== 'undefined') {
        localStorage.removeItem(STORAGE_KEY);
      }
      set(null);
    },
  };
}

export const auth = createAuth();
export const isLoggedIn = derived(auth, $a => !!$a?.token);
export const isAdmin = derived(auth, $a => $a?.role === 'admin');
