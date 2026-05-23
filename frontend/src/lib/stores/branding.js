import { writable } from 'svelte/store';
import { getSettings, updateSettings } from '$lib/api.js';

const CACHE_KEY = 'kellerlog_branding_cache';

export const DEFAULTS = {
  primaryColor: '#480f25',
  darkMode: false,
  title: 'KellerLog',
  subtitle: 'Meine Weinsammlung',
  logoUrl: '',
};

function hexToHsl(hex) {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  const l = (max + min) / 2;
  if (max === min) return [0, 0, l * 100];
  const d = max - min;
  const s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
  let h;
  switch (max) {
    case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
    case g: h = ((b - r) / d + 2) / 6; break;
    case b: h = ((r - g) / d + 4) / 6; break;
  }
  return [h * 360, s * 100, l * 100];
}

function hslToHex(h, s, l) {
  s = Math.max(0, Math.min(100, s)) / 100;
  l = Math.max(0, Math.min(100, l)) / 100;
  const a = s * Math.min(l, 1 - l);
  const f = n => {
    const k = (n + h / 30) % 12;
    return Math.round(255 * (l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1))))
      .toString(16).padStart(2, '0');
  };
  return `#${f(0)}${f(8)}${f(4)}`;
}

export function applyBranding(b) {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  const [h, s, l] = hexToHsl(b.primaryColor);
  root.style.setProperty('--primary',       b.primaryColor);
  root.style.setProperty('--primary-dark',  hslToHex(h, s,              Math.max(5,  l - 15)));
  root.style.setProperty('--primary-light', hslToHex(h, Math.min(100, s + 10), Math.min(90, l + 15)));
  root.style.setProperty('--header-start',  hslToHex(h, Math.min(100, s + 5),  Math.min(70, l + 8)));
  root.style.setProperty('--header-end',    hslToHex(h, s,              Math.max(5,  l - 12)));
  root.classList.toggle('dark', !!b.darkMode);
}

function fromSettings(s) {
  return {
    primaryColor: s.primary_color ?? DEFAULTS.primaryColor,
    darkMode:     s.dark_mode     ?? DEFAULTS.darkMode,
    title:        s.app_title     ?? DEFAULTS.title,
    subtitle:     s.app_subtitle  ?? DEFAULTS.subtitle,
    logoUrl:      s.logo_url      ?? DEFAULTS.logoUrl,
  };
}

function toSettings(b) {
  return {
    primary_color: b.primaryColor,
    dark_mode:     b.darkMode,
    app_title:     b.title,
    app_subtitle:  b.subtitle,
    logo_url:      b.logoUrl,
  };
}

function loadCache() {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    return raw ? { ...DEFAULTS, ...JSON.parse(raw) } : { ...DEFAULTS };
  } catch {
    return { ...DEFAULTS };
  }
}

function saveCache(b) {
  try { localStorage.setItem(CACHE_KEY, JSON.stringify(b)); } catch { }
}

let _debounceTimer;

function createBrandingStore() {
  const { subscribe, set, update } = writable({ ...DEFAULTS });

  return {
    subscribe,

    async init() {
      // Fast paint from cache
      const cached = loadCache();
      set(cached);
      applyBranding(cached);

      // Authoritative values from server
      try {
        const s = await getSettings();
        if (s) {
          const fromServer = fromSettings(s);
          saveCache(fromServer);
          set(fromServer);
          applyBranding(fromServer);
        }
      } catch {
        // keep cache if offline
      }
    },

    save(values) {
      update(current => {
        const next = { ...current, ...values };
        saveCache(next);
        applyBranding(next);

        // Debounce API writes — avoid hammering on every keypress
        clearTimeout(_debounceTimer);
        _debounceTimer = setTimeout(() => {
          updateSettings(toSettings(next)).catch(() => {});
        }, 500);

        return next;
      });
    },

    async reset() {
      try { localStorage.removeItem(CACHE_KEY); } catch { }
      set({ ...DEFAULTS });
      applyBranding(DEFAULTS);
      try {
        await updateSettings(toSettings(DEFAULTS));
      } catch { }
    },
  };
}

export const branding = createBrandingStore();
