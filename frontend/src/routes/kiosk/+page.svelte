<script>
  import { onMount } from 'svelte';
  import { getWines } from '$lib/api.js';
  import { branding } from '$lib/stores/branding.js';
  import { t } from '$lib/stores/i18n.js';
  import WineCard from '$lib/components/WineCard.svelte';
  import WineMap from '$lib/components/WineMap.svelte';
  import WineDetail from '$lib/components/WineDetail.svelte';

  let wines = [];
  let loading = true;
  let filterType = 'all';
  let searchQuery = '';
  let showMap = false;
  let selectedWine = null;

  $: typeFilters = [
    { value: 'all',      label: $t('filter_all') },
    { value: 'by_glass', label: $t('filter_by_glass') },
    { value: 'red',      label: $t('filter_red') },
    { value: 'white',    label: $t('filter_white') },
    { value: 'rosé',     label: $t('filter_rose') },
    { value: 'sparkling',label: $t('filter_sparkling') },
    { value: 'dessert',  label: $t('filter_dessert') },
    { value: 'other',    label: $t('filter_other') },
  ];

  $: filteredWines = wines
    .filter(w => {
      if (filterType === 'all') return true;
      if (filterType === 'by_glass') return !!w.by_glass;
      return w.type === filterType;
    })
    .filter(w => {
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      return (
        w.name?.toLowerCase().includes(q) ||
        w.producer?.toLowerCase().includes(q) ||
        w.region?.toLowerCase().includes(q) ||
        w.country?.toLowerCase().includes(q) ||
        w.grape?.toLowerCase().includes(q)
      );
    });

  onMount(async () => {
    branding.init();
    try {
      wines = await getWines();
    } finally {
      loading = false;
    }
  });
</script>

<svelte:head>
  <title>{$branding.kioskTitle}</title>
</svelte:head>

<div class="kiosk">
  <header class="kiosk-header">
    <div class="header-inner">
      <div class="brand">
        {#if $branding.logoUrl}
          <img src={$branding.logoUrl} alt="Logo" class="logo-img" />
        {:else}
          <img src="/logo/kellerlog-icon.svg" alt="KellerLog" class="app-icon" />
        {/if}
        <div>
          <h1>{$branding.kioskTitle}</h1>
          <p class="subtitle">{$branding.kioskSubtitle}</p>
        </div>
      </div>

      <div class="header-right">
        <button class="map-btn" on:click={() => showMap = true} title={$t('nav_map')}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/>
            <line x1="8" y1="2" x2="8" y2="18"/>
            <line x1="16" y1="6" x2="16" y2="22"/>
          </svg>
          {$t('kiosk_map')}
        </button>

        <div class="header-search">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            type="search"
            placeholder={$t('kiosk_search')}
            bind:value={searchQuery}
            class="search-input"
          />
        </div>
      </div>
    </div>
  </header>

  <main class="kiosk-main">
    <div class="controls">
      <div class="type-tabs">
        {#each typeFilters as f}
          <button
            class="tab"
            class:active={filterType === f.value}
            on:click={() => filterType = f.value}
          >{f.label}</button>
        {/each}
      </div>
    </div>

    {#if loading}
      <div class="center">
        <div class="loader"></div>
        <p>{$t('kiosk_loading')}</p>
      </div>
    {:else if filteredWines.length === 0}
      <div class="empty">
        <div class="empty-icon">🍷</div>
        <p>{searchQuery ? $t('kiosk_no_results') : $t('kiosk_no_wines')}</p>
      </div>
    {:else}
      <p class="count">{filteredWines.length} {filteredWines.length !== 1 ? $t('count_plural') : $t('count_singular')}</p>
      <div class="wine-grid">
        {#each filteredWines as wine (wine.id)}
          <WineCard {wine} readonly={true} on:select={(e) => selectedWine = e.detail} />
        {/each}
      </div>
    {/if}
  </main>

  {#if $branding.kioskShowFooter}
    <footer class="kiosk-footer">
      <a href="https://github.com/KrapfalAT/kellerlog" target="_blank" rel="noopener" class="footer-link">{$branding.title}</a>
    </footer>
  {/if}

  {#if showMap}
    <WineMap {wines} on:close={() => showMap = false} />
  {/if}

  {#if selectedWine}
    <WineDetail wine={selectedWine} on:close={() => selectedWine = null} />
  {/if}
</div>

<style>
  .kiosk {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: var(--bg);
  }

  /* ── Header (identical style to main page) ── */
  .kiosk-header {
    background: linear-gradient(135deg, var(--header-start, #5a1328) 0%, var(--header-end, #3d0d1c) 100%);
    color: white;
    padding: 0 24px;
    box-shadow: 0 4px 20px rgba(61, 13, 28, 0.4);
  }
  .header-inner {
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    padding: 16px 0;
    flex-wrap: wrap;
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .logo-img {
    height: 44px;
    width: auto;
    max-width: 80px;
    object-fit: contain;
    filter: brightness(0) invert(1);
  }
  .app-icon {
    height: 44px;
    width: 44px;
    border-radius: 10px;
    object-fit: contain;
  }
  h1 {
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.3px;
  }
  .subtitle {
    font-size: 11px;
    opacity: 0.65;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-top: 1px;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .map-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 7px 14px;
    background: rgba(255,255,255,0.15);
    color: white;
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    transition: background 0.15s, border-color 0.15s;
    white-space: nowrap;
  }
  .map-btn:hover {
    background: rgba(255,255,255,0.25);
    border-color: rgba(255,255,255,0.5);
  }

  .header-search {
    position: relative;
    display: flex;
    align-items: center;
  }
  .header-search svg {
    position: absolute;
    left: 12px;
    color: rgba(255,255,255,0.6);
    pointer-events: none;
  }
  .search-input {
    padding: 8px 16px 8px 36px;
    border-radius: 20px;
    border: 1.5px solid rgba(255,255,255,0.25);
    background: rgba(255,255,255,0.12);
    color: white;
    font-size: 13px;
    width: 210px;
    transition: background 0.15s, border-color 0.15s;
  }
  .search-input::placeholder { color: rgba(255,255,255,0.5); }
  .search-input:focus {
    outline: none;
    background: rgba(255,255,255,0.18);
    border-color: rgba(255,255,255,0.5);
  }

  /* ── Tabs (identical style to main page) ── */
  .controls {
    margin-bottom: 24px;
  }
  .type-tabs {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }
  .tab {
    padding: 7px 14px;
    border-radius: 20px;
    border: 1.5px solid var(--border);
    background: var(--surface);
    font-size: 13px;
    font-weight: 500;
    color: var(--text-muted);
    transition: all 0.15s;
  }
  .tab:hover { border-color: var(--primary); color: var(--primary); }
  .tab.active {
    background: var(--primary);
    border-color: var(--primary);
    color: white;
  }

  /* ── Main content ── */
  .kiosk-main {
    max-width: 1400px;
    margin: 0 auto;
    width: 100%;
    padding: 28px 24px 80px;
    flex: 1;
  }

  .count {
    font-size: 13px;
    color: var(--text-muted);
    margin-bottom: 16px;
  }

  .wine-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 22px;
  }

  .center {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16px;
    padding: 100px 20px;
    color: var(--text-muted);
  }
  .loader {
    width: 44px;
    height: 44px;
    border: 3px solid var(--border);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    padding: 100px 20px;
    color: var(--text-muted);
    text-align: center;
  }
  .empty-icon { font-size: 60px; }

  .kiosk-footer {
    text-align: center;
    padding: 16px;
    font-size: 12px;
    color: var(--text-muted);
    letter-spacing: 1px;
    text-transform: uppercase;
    border-top: 1px solid var(--border);
    background: var(--surface);
  }
  .footer-link {
    color: inherit;
    text-decoration: none;
    transition: color 0.15s;
  }
  .footer-link:hover { color: var(--primary); }

  @media (max-width: 600px) {
    h1 { font-size: 18px; }
    .header-inner { padding: 12px 0; }
    .search-input { width: 150px; }
    .kiosk-main { padding: 20px 16px 60px; }
  }
</style>
