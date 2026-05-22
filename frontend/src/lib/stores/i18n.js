import { writable, derived } from 'svelte/store';
import de from '$lib/i18n/de.json';
import en from '$lib/i18n/en.json';

const KEY = 'kellerlog_lang';
const translations = { de, en };

const initialLang = (() => {
  if (typeof localStorage === 'undefined') return 'de';
  const s = localStorage.getItem(KEY);
  return s === 'en' ? 'en' : 'de';
})();

export const lang = writable(initialLang);

lang.subscribe(v => {
  if (typeof localStorage !== 'undefined') localStorage.setItem(KEY, v);
});

export const t = derived(lang, $l => key => translations[$l]?.[key] ?? translations.de[key] ?? key);
