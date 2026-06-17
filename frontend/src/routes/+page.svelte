<script>
  import { onMount } from 'svelte';
  import { version } from '../../package.json';
  import { getWines, createWine, updateWine, deleteWine, getStats, lookupBarcode, getDrinkRules, batchUpdateWines, getCustomFields, getMe, setMyLanguage } from '$lib/api.js';
  import WineCard from '$lib/components/WineCard.svelte';
  import AddWineModal from '$lib/components/AddWineModal.svelte';
  import WineMap from '$lib/components/WineMap.svelte';
  import LibraryManager from '$lib/components/LibraryManager.svelte';
  import ExportPanel from '$lib/components/ExportPanel.svelte';
  import BrandingPanel from '$lib/components/BrandingPanel.svelte';
  import UserManagementPanel from '$lib/components/UserManagementPanel.svelte';
  import KioskPanel from '$lib/components/KioskPanel.svelte';
  import DrinkRulesPanel from '$lib/components/DrinkRulesPanel.svelte';
  import BatchEditPanel from '$lib/components/BatchEditPanel.svelte';
  import CustomFieldsPanel from '$lib/components/CustomFieldsPanel.svelte';
  import WineDetail from '$lib/components/WineDetail.svelte';
  import BarcodeScanner from '$lib/components/BarcodeScanner.svelte';
  import InventoryQuickAdd from '$lib/components/InventoryQuickAdd.svelte';
  import { branding } from '$lib/stores/branding.js';
  import { lang, t } from '$lib/stores/i18n.js';
  import { auth, isAdmin } from '$lib/stores/auth.js';
  import { goto } from '$app/navigation';

  let wines = [];
  let stats = null;
  let loading = true;
  let error = '';
  let toast = '';
  let toastTimeout;

  let showModal = false;
  let editingWine = null;
  let libraryPrefill = null;
  let modalHideStock = false;
  let showMap = false;
  let showLibrary = false;
  let showExport = false;
  let showBranding = false;
  let showUsers = false;
  let showKiosk = false;
  let showDrinkRules = false;
  let showBatchEdit = false;
  let showCustomFields = false;
  let showMenu = false;
  let drinkRules = [];
  let customFields = [];
  let selectionMode = false;
  let selectedIds = new Set();

  function toggleSelection(id) {
    selectedIds = selectedIds.has(id)
      ? (selectedIds.delete(id), new Set(selectedIds))
      : new Set(selectedIds).add(id);
  }
  function selectAll() {
    selectedIds = new Set(filteredWines.map(w => w.id));
  }
  function exitSelectionMode() {
    selectionMode = false;
    selectedIds = new Set();
  }
  async function handleBatchSave(e) {
    try {
      const result = await batchUpdateWines([...selectedIds], e.detail);
      wines = await getWines();
      stats = await getStats();
      showToast(`${result.updated} ${$t('batch_success')}`);
      showBatchEdit = false;
      exitSelectionMode();
    } catch (err) {
      handleApiError(err);
    }
  }
  let selectedWine = null;
  let libraryAddWine = null;
  let libraryAddIsNew = false;
  let libraryAddFromLibrary = false;
  let inventoryMode = false;
  let showInventoryScanner = false;
  let inventoryScanWine = null;
  let inventoryScanIsNew = false;
  const qtyTimers = {};

  let filterType = 'all';
  let searchQuery = '';
  let sortBy = 'date';

  $: typeFilters = [
    { value: 'all',      label: $t('filter_all') },
    { value: 'red',      label: $t('filter_red') },
    { value: 'white',    label: $t('filter_white') },
    { value: 'rosé',     label: $t('filter_rose') },
    { value: 'sparkling',label: $t('filter_sparkling') },
    { value: 'dessert',  label: $t('filter_dessert') },
    { value: 'other',    label: $t('filter_other') },
  ];

  $: filteredWines = wines
    .filter(w => filterType === 'all' || w.type === filterType)
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
    })
    .sort((a, b) => {
      if (sortBy === 'name') return a.name.localeCompare(b.name);
      if (sortBy === 'vintage') return (b.vintage || 0) - (a.vintage || 0);
      if (sortBy === 'rating') return (b.rating || 0) - (a.rating || 0);
      if (sortBy === 'quantity') return b.quantity - a.quantity;
      return new Date(b.added_at) - new Date(a.added_at);
    });

  async function load() {
    try {
      [wines, stats, drinkRules, customFields] = await Promise.all([getWines(), getStats(), getDrinkRules(), getCustomFields()]);
    } catch (e) {
      error = $t('error_connection');
    } finally {
      loading = false;
    }
  }

  function showToast(msg) {
    toast = msg;
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => (toast = ''), 3000);
  }

  function handleApiError(e) {
    if (e.message === 'UNAUTHORIZED') {
      auth.logout();
      goto('/login');
    } else {
      showToast(e.message);
    }
  }

  function handleLogout() {
    auth.logout();
    goto('/login');
  }

  async function handleSave(e) {
    const data = e.detail;
    try {
      if (editingWine) {
        await updateWine(editingWine.id, data);
        showToast($t('toast_updated'));
      } else {
        const created = await createWine(data);
        wines = [created, ...wines];
        showToast($t('toast_added'));
      }
      // Always reload: edited wine might change qty and appear/disappear from dashboard
      wines = await getWines();
      stats = await getStats();
      closeModal();
    } catch (e) {
      handleApiError(e);
    }
  }

  async function handleDelete(e) {
    const id = e.detail;
    if (!confirm($t('confirm_delete'))) return;
    try {
      await deleteWine(id);
      wines = wines.filter(w => w.id !== id);
      stats = await getStats();
      showToast($t('toast_deleted'));
    } catch (e) {
      handleApiError(e);
    }
  }

  function handleEdit(e) {
    editingWine = e.detail;
    showModal = true;
  }

  function openAdd() {
    editingWine = null;
    showModal = true;
  }

  function closeModal() {
    showModal = false;
    editingWine = null;
    libraryPrefill = null;
    modalHideStock = false;
  }

  function handleLibrarySelect(e) {
    libraryPrefill = e.detail;
    showLibrary = false;
    showModal = true;
  }

  function handleLibraryAddToInventory(e) {
    // Library entries are already unified — just increment quantity
    libraryAddWine = e.detail;
    libraryAddIsNew = false;
    libraryAddFromLibrary = true;
  }

  function handleLibraryEdit(e) {
    // Library entries and wine entries are the same — use regular edit flow
    editingWine = e.detail;
    showLibrary = false;
    showModal = true;
  }

  function handleLibraryDuplicate(e) {
    const { id: _id, ...copy } = e.detail;
    libraryPrefill = copy;
    editingWine = null;
    editingLibraryId = null;
    showLibrary = false;
    showModal = true;
  }

  async function handleLibraryQuickAdd(e) {
    const { wine, qty } = e.detail;
    libraryAddWine = null;
    try {
      await updateWine(wine.id, { quantity: (wine.quantity || 0) + qty });
      // Reload in case wine moved from 0→visible or changed position
      wines = await getWines();
      stats = await getStats();
      showToast(`${wine.name} hinzugefügt`);
    } catch {
      showToast($t('toast_error_save'));
    }
  }

  function handleQuantityChange(e) {
    const { id, quantity } = e.detail;
    wines = wines.map(w => w.id === id ? { ...w, quantity } : w);
    clearTimeout(qtyTimers[id]);
    qtyTimers[id] = setTimeout(async () => {
      try {
        await updateWine(id, { quantity });
        stats = await getStats();
      } catch {
        showToast($t('toast_error_save'));
      }
    }, 700);
  }

  async function handleInventoryScan(e) {
    showInventoryScanner = false;
    const barcode = e.detail;
    const existing = wines.find(w => w.barcode === barcode);
    if (existing) {
      inventoryScanWine = existing;
      inventoryScanIsNew = false;
      return;
    }
    try {
      const result = await lookupBarcode(barcode);
      if (result) {
        if (!result.barcode) result.barcode = barcode;
        inventoryScanWine = result;
      } else {
        inventoryScanWine = { name: '', barcode, type: 'red', quantity: 0 };
      }
      inventoryScanIsNew = true;
    } catch {
      inventoryScanWine = { name: '', barcode, type: 'red', quantity: 0 };
      inventoryScanIsNew = true;
    }
  }

  async function handleInventoryQuickAdd(e) {
    const { wine, qty, isNew } = e.detail;
    inventoryScanWine = null;
    try {
      if (isNew) {
        const created = await createWine({ ...wine, quantity: qty });
        wines = [created, ...wines];
        showToast(`${wine.name} ${$t('toast_added')}`);
      } else {
        const newQty = wine.quantity + qty;
        const updated = await updateWine(wine.id, {
          quantity: newQty,
          name: wine.name,
          image_url: wine.image_url,
          producer: wine.producer,
          vintage: wine.vintage,
          type: wine.type,
          price: wine.price,
        });
        wines = wines.map(w => w.id === updated.id ? updated : w);
        showToast(`${wine.name}: jetzt ${newQty}×`);
      }
      stats = await getStats();
    } catch (err) {
      handleApiError(err);
    }
    showInventoryScanner = true;
  }

  async function exitInventoryMode() {
    inventoryMode = false;
    showInventoryScanner = false;
    // Wines with qty=0 now stay in library — reload to refresh dashboard
    wines = await getWines();
    stats = await getStats();
  }

  onMount(async () => {
    branding.init();
    load();
    const me = await getMe();
    if (me?.language) lang.set(me.language);
  });

  function saveAdminKey() {
    setAdminKey(adminKey.trim());
  }
</script>

<div class="app">
  <!-- Header -->
  <header class="header">
    <div class="header-inner">
      <div class="logo">
        {#if $branding.logoUrl}
          <img src={$branding.logoUrl} alt="Logo" class="logo-img" />
        {:else}
          <img src="/logo/kellerlog-icon.svg" alt="KellerLog" class="app-icon" />
        {/if}
        <div>
          <h1>{$branding.title}</h1>
          <p class="subtitle">{$branding.subtitle}</p>
        </div>
      </div>

      <div class="icon-group">
        <button class="icon-btn" on:click={() => showLibrary = true} title={$t('nav_library')}>
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/>
          </svg>
        </button>
        <div class="icon-sep"></div>
        <a class="icon-btn kiosk-btn" href="/kiosk" target="_blank" rel="noopener" title={$t('nav_kiosk')}>
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2"/>
            <line x1="8" y1="21" x2="16" y2="21"/>
            <line x1="12" y1="17" x2="12" y2="21"/>
          </svg>
        </a>
        <div class="icon-sep"></div>
        <button class="icon-btn" on:click={() => showMap = true} title={$t('nav_map')}>
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/>
            <line x1="8" y1="2" x2="8" y2="18"/>
            <line x1="16" y1="6" x2="16" y2="22"/>
          </svg>
        </button>
        {#if $isAdmin}
        <div class="icon-sep"></div>
        <button class="icon-btn" class:active={inventoryMode} on:click={() => { if (inventoryMode) { exitInventoryMode(); } else { inventoryMode = true; } }} title={$t('nav_inventory')}>
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
          </svg>
        </button>
        {/if}
      </div>

      <div class="header-right">
        {#if stats}
          <div class="stats-bar">
            <div class="stat">
              <span class="stat-value">{stats.total_wines}</span>
              <span class="stat-label">{$t('stat_wines')}</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat">
              <span class="stat-value">{stats.total_bottles}</span>
              <span class="stat-label">{$t('stat_bottles')}</span>
            </div>
            {#if stats.avg_rating}
              <div class="stat-divider"></div>
              <div class="stat">
                <span class="stat-value">⭐ {stats.avg_rating}</span>
                <span class="stat-label">{$t('stat_avg_rating')}</span>
              </div>
            {/if}
          </div>
        {/if}

        <div class="burger-wrap">
          <button class="burger-btn" on:click={() => showMenu = !showMenu} aria-label="Menü" title="Einstellungen">
            <span class="bar" class:open={showMenu}></span>
            <span class="bar" class:open={showMenu}></span>
            <span class="bar" class:open={showMenu}></span>
          </button>
          {#if showMenu}
            <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
            <div class="menu-backdrop" on:click={() => showMenu = false}></div>
            <div class="menu-dropdown">
              <div class="menu-section-label">{$t('menu_settings')}</div>
              <button class="menu-item" on:click={() => { showExport = true; showMenu = false; }}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                {$t('menu_backup')}
              </button>
              <button class="menu-item" on:click={() => { showBranding = true; showMenu = false; }}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="3"/>
                  <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>
                </svg>
                {$t('menu_branding')}
              </button>
              {#if $isAdmin}
              <button class="menu-item" on:click={() => { showKiosk = true; showMenu = false; }}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="2" y="3" width="20" height="14" rx="2"/>
                  <path d="M8 21h8M12 17v4"/>
                </svg>
                {$t('menu_kiosk_settings')}
              </button>
              <button class="menu-item" on:click={() => { showDrinkRules = true; showMenu = false; }}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="2"/><circle cx="12" cy="4" r="2"/><circle cx="12" cy="20" r="2"/>
                  <line x1="14" y1="4" x2="20" y2="4"/><line x1="14" y1="12" x2="20" y2="12"/><line x1="14" y1="20" x2="20" y2="20"/>
                  <line x1="4" y1="4" x2="10" y2="4"/><line x1="4" y1="12" x2="10" y2="12"/><line x1="4" y1="20" x2="10" y2="20"/>
                </svg>
                {$t('drink_rules_menu')}
              </button>
              <button class="menu-item" on:click={() => { showCustomFields = true; showMenu = false; }}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/>
                  <line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
                </svg>
                {$t('custom_fields_menu')}
              </button>
              {/if}
              <div class="menu-divider"></div>
              <div class="menu-section-label">{$t('menu_language')}</div>
              <div class="lang-row">
                <button class="lang-btn" class:lang-active={$lang === 'de'} on:click={() => { lang.set('de'); setMyLanguage('de').catch(() => {}); }}>🇩🇪 Deutsch</button>
                <button class="lang-btn" class:lang-active={$lang === 'en'} on:click={() => { lang.set('en'); setMyLanguage('en').catch(() => {}); }}>🇬🇧 English</button>
              </div>
              {#if $isAdmin}
              <div class="menu-divider"></div>
              <button class="menu-item" on:click={() => { showUsers = true; showMenu = false; }}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>
                </svg>
                {$t('menu_users')}
              </button>
              {/if}
              <div class="menu-divider"></div>
              <div class="menu-user-row">
                <span class="menu-username">{$auth?.username}</span>
                <button class="menu-logout" on:click={handleLogout}>{$t('menu_logout')}</button>
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>
  </header>

  <main class="main">
    <!-- Filter Bar -->
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

      <div class="control-right">
        <div class="search-wrap">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            type="search"
            class="control-search"
            placeholder={$t('search_placeholder')}
            bind:value={searchQuery}
          />
        </div>

        {#if $isAdmin && !inventoryMode}
          <button class="btn-select-mode" class:active={selectionMode} on:click={() => { if (selectionMode) { exitSelectionMode(); } else { selectionMode = true; } }} title={$t('batch_mode')}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
              <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
            </svg>
            {$t('batch_mode')}
          </button>
        {/if}
        <select class="control-sort" bind:value={sortBy}>
          <option value="date">{$t('sort_date')}</option>
          <option value="name">{$t('sort_name')}</option>
          <option value="vintage">{$t('sort_vintage')}</option>
          <option value="rating">{$t('sort_rating')}</option>
          <option value="quantity">{$t('sort_quantity')}</option>
        </select>
      </div>
    </div>

    <!-- Content -->
    {#if loading}
      <div class="center">
        <div class="loader"></div>
        <p>{$t('loading')}</p>
      </div>
    {:else if error}
      <div class="center error-box">
        <p>{error}</p>
        <button class="btn-retry" on:click={load}>{$t('retry')}</button>
      </div>
    {:else if filteredWines.length === 0}
      <div class="empty">
        <div class="empty-icon">🍷</div>
        {#if wines.length === 0}
          <h2>{$t('empty_no_wines_title')}</h2>
          <p>{$t('empty_no_wines_sub')}</p>
        {:else}
          <h2>{$t('empty_no_results_title')}</h2>
          <p>{$t('empty_no_results_sub')}</p>
        {/if}
      </div>
    {:else}
      <p class="result-count">{filteredWines.length} {filteredWines.length !== 1 ? $t('count_plural') : $t('count_singular')}</p>
      <div class="wine-grid">
        {#each filteredWines as wine (wine.id)}
          <WineCard {wine} {inventoryMode} readonly={!$isAdmin || inventoryMode} showDrinkWindow={$branding.showDrinkWindow} {drinkRules} selectable={selectionMode} selected={selectedIds.has(wine.id)} on:toggle={(e) => toggleSelection(e.detail)} on:select={(e) => selectedWine = e.detail} on:edit={handleEdit} on:delete={handleDelete} on:quantityChange={handleQuantityChange} />
        {/each}
      </div>
    {/if}
  </main>

  <footer class="footer">
    <a href="https://github.com/KrapfalAT/kellerlog" target="_blank" rel="noopener" class="footer-link">KellerLog</a>
    <a class="footer-version" href="https://github.com/KrapfalAT/kellerlog/releases" target="_blank" rel="noopener">v{version}</a>
  </footer>

  <!-- Selection Bar -->
  {#if selectionMode}
    <div class="selection-bar">
      <span class="sel-count">{selectedIds.size} {selectedIds.size === 1 ? $t('count_singular') : $t('count_plural')} {$t('batch_selected')}</span>
      <div class="sel-actions">
        <button class="sel-btn" on:click={selectedIds.size === filteredWines.length ? () => selectedIds = new Set() : selectAll}>
          {selectedIds.size === filteredWines.length ? $t('batch_deselect_all') : $t('batch_select_all')}
        </button>
        <button class="sel-btn primary" disabled={selectedIds.size === 0} on:click={() => showBatchEdit = true}>
          {$t('batch_edit_btn')}
        </button>
        <button class="sel-btn close" on:click={exitSelectionMode}>✕</button>
      </div>
    </div>
  {/if}

  <!-- FAB -->
  {#if inventoryMode}
    <div class="inv-bar">
      <span class="inv-label">{$t('inventory_mode_label')}</span>
      <button class="inv-exit" on:click={exitInventoryMode}>{$t('inventory_exit')}</button>
    </div>
    <button class="fab fab-scan" on:click={() => showInventoryScanner = true} title="Barcode scannen" aria-label="Barcode scannen">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="2" y="2" width="6" height="6" rx="1"/><rect x="16" y="2" width="6" height="6" rx="1"/>
        <rect x="2" y="16" width="6" height="6" rx="1"/>
        <path d="M22 16h-6v2M16 22h2M22 22v-2"/>
        <path d="M2 12h8M12 2v8M12 12h2v2M14 18h2v2M12 20v2M20 12h2"/>
      </svg>
    </button>
  {/if}
  {#if $isAdmin && !selectionMode}
  <button class="fab" on:click={openAdd} title={$t('nav_add')} aria-label={$t('nav_add')}>
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
      <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
    </svg>
  </button>
  {/if}

  <!-- Modal -->
  {#if showModal}
    <AddWineModal wine={editingWine} prefill={libraryPrefill} hideStock={modalHideStock || inventoryMode} {customFields} on:save={handleSave} on:close={closeModal} />
  {/if}

  <!-- Map -->
  {#if showMap}
    <WineMap {wines} on:close={() => showMap = false} on:selectWine={(e) => { showMap = false; editingWine = e.detail; modalHideStock = true; showModal = true; }} />
  {/if}

  <!-- Export/Import -->
  {#if showExport}
    <ExportPanel on:close={() => showExport = false} />
  {/if}

  <!-- Branding -->
  {#if showBranding}
    <BrandingPanel on:close={() => showBranding = false} />
  {/if}

  <!-- User Management -->
  {#if showUsers}
    <UserManagementPanel on:close={() => showUsers = false} />
  {/if}

  <!-- Kiosk Settings -->
  {#if showKiosk}
    <KioskPanel on:close={() => showKiosk = false} />
  {/if}

  <!-- Batch Edit -->
  {#if showBatchEdit}
    <BatchEditPanel count={selectedIds.size} on:save={handleBatchSave} on:close={() => showBatchEdit = false} />
  {/if}

  <!-- Drink Rules -->
  {#if showDrinkRules}
    <DrinkRulesPanel on:close={() => showDrinkRules = false} on:rulesChanged={async () => drinkRules = await getDrinkRules()} />
  {/if}

  <!-- Custom Fields -->
  {#if showCustomFields}
    <CustomFieldsPanel on:close={() => showCustomFields = false} on:changed={async () => customFields = await getCustomFields()} />
  {/if}

  <!-- Wine detail (image click) -->
  {#if selectedWine}
    <WineDetail wine={selectedWine} editable={true} {customFields}
      on:close={() => selectedWine = null}
      on:edit={(e) => { selectedWine = null; editingWine = e.detail; showModal = true; }}
    />
  {/if}

  <!-- Library -->
  {#if showLibrary}
    <LibraryManager
      on:close={() => showLibrary = false}
      on:selectEntry={handleLibrarySelect}
      on:addToInventory={handleLibraryAddToInventory}
      on:editEntry={handleLibraryEdit}
      on:duplicateEntry={handleLibraryDuplicate}
    />
  {/if}

  <!-- Library quick-add -->
  {#if libraryAddWine}
    <InventoryQuickAdd wine={libraryAddWine} isNew={libraryAddIsNew} fromLibrary={libraryAddFromLibrary}
      on:confirm={handleLibraryQuickAdd}
      on:cancel={() => { libraryAddWine = null; libraryAddFromLibrary = false; }}
    />
  {/if}

  <!-- Inventory scanner + quick-add -->
  {#if showInventoryScanner}
    <BarcodeScanner on:scan={handleInventoryScan} on:close={() => showInventoryScanner = false} />
  {/if}
  {#if inventoryScanWine}
    <InventoryQuickAdd wine={inventoryScanWine} isNew={inventoryScanIsNew}
      on:confirm={handleInventoryQuickAdd}
      on:cancel={() => { inventoryScanWine = null; showInventoryScanner = true; }}
    />
  {/if}

  <!-- Toast -->
  {#if toast}
    <div class="toast">{toast}</div>
  {/if}
</div>

<style>
  .app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* Header */
  .header {
    background: linear-gradient(135deg, var(--header-start, #5a1328) 0%, var(--header-end, #3d0d1c) 100%);
    color: white;
    padding: 0 24px;
    box-shadow: 0 4px 20px rgba(61, 13, 28, 0.4);
  }
  .header-inner {
    max-width: 1400px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    padding: 16px 0;
    gap: 20px;
  }
  .logo {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .logo-img {
    height: 44px;
    width: auto;
    max-width: 80px;
    object-fit: contain;
  }
  .app-icon {
    height: 44px;
    width: 44px;
    border-radius: 10px;
    object-fit: contain;
  }
  .logo h1 {
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
  .icon-btn.active {
    background: rgba(255,255,255,0.28);
    color: white;
  }

  .btn-select-mode {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 7px 12px;
    border: 1.5px solid var(--border);
    border-radius: 8px;
    background: var(--surface);
    font-size: 13px;
    font-weight: 500;
    color: var(--text-muted);
    transition: all 0.15s;
  }
  .btn-select-mode:hover { border-color: var(--primary); color: var(--primary); }
  .btn-select-mode.active {
    background: var(--primary);
    border-color: var(--primary);
    color: white;
  }

  .selection-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: var(--surface);
    border-top: 1.5px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 24px;
    gap: 12px;
    z-index: 45;
    box-shadow: 0 -4px 20px rgba(0,0,0,0.1);
  }
  .sel-count {
    font-size: 14px;
    font-weight: 600;
    color: var(--text);
  }
  .sel-actions {
    display: flex;
    gap: 8px;
    align-items: center;
  }
  .sel-btn {
    padding: 8px 16px;
    border-radius: 8px;
    border: 1.5px solid var(--border);
    background: var(--surface-2);
    font-size: 13px;
    font-weight: 600;
    color: var(--text-muted);
    transition: all 0.15s;
  }
  .sel-btn:hover:not(:disabled) { border-color: var(--primary); color: var(--primary); }
  .sel-btn.primary {
    background: var(--primary);
    border-color: var(--primary);
    color: white;
  }
  .sel-btn.primary:hover:not(:disabled) { background: var(--primary-dark); }
  .sel-btn.primary:disabled { opacity: 0.45; cursor: default; }
  .sel-btn.close { padding: 8px 12px; }

  .inv-bar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background: var(--primary);
    color: white;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 600;
    z-index: 40;
    box-shadow: 0 2px 12px rgba(0,0,0,0.2);
  }
  .inv-label { letter-spacing: 0.3px; }
  .inv-exit {
    border: 1.5px solid rgba(255,255,255,0.5);
    background: none;
    color: white;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    transition: background 0.15s;
  }
  .inv-exit:hover { background: rgba(255,255,255,0.15); }

  .fab.fab-scan {
    right: 100px;
    background: #2c7a4b;
    box-shadow: 0 4px 16px rgba(44, 122, 75, 0.4);
  }
  .fab.fab-scan:hover {
    background: #245f3b;
    box-shadow: 0 6px 24px rgba(44, 122, 75, 0.5);
  }

  .icon-group {
    display: flex;
    align-items: stretch;
    border: 1px solid rgba(255,255,255,0.28);
    border-radius: 20px;
    background: rgba(255,255,255,0.1);
    overflow: hidden;
  }
  .icon-btn {
    width: 40px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: none;
    border: none;
    color: rgba(255,255,255,0.85);
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
  }
  .icon-btn:hover {
    background: rgba(255,255,255,0.18);
    color: white;
  }
  .kiosk-btn { text-decoration: none; border-radius: 6px; }

  .icon-sep {
    width: 1px;
    background: rgba(255,255,255,0.25);
    margin: 7px 0;
  }
  .stats-bar {
    display: flex;
    align-items: center;
    gap: 16px;
    background: rgba(255,255,255,0.12);
    padding: 8px 18px;
    border-radius: 50px;
  }
  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1px;
  }
  .stat-value {
    font-size: 18px;
    font-weight: 700;
    line-height: 1;
  }
  .stat-label {
    font-size: 11px;
    opacity: 0.75;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .stat-divider {
    width: 1px;
    height: 28px;
    background: rgba(255,255,255,0.25);
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;
    justify-content: flex-end;
  }

  .burger-wrap {
    position: relative;
  }

  .burger-btn {
    width: 36px;
    height: 36px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 5px;
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 8px;
    cursor: pointer;
    padding: 0;
    transition: background 0.15s;
  }
  .burger-btn:hover { background: rgba(255,255,255,0.22); }

  .bar {
    display: block;
    width: 16px;
    height: 2px;
    background: white;
    border-radius: 2px;
    transition: transform 0.2s, opacity 0.2s;
  }
  .bar.open:nth-child(1) { transform: translateY(7px) rotate(45deg); }
  .bar.open:nth-child(2) { opacity: 0; }
  .bar.open:nth-child(3) { transform: translateY(-7px) rotate(-45deg); }

  .menu-backdrop {
    position: fixed;
    inset: 0;
    z-index: 98;
  }

  .menu-dropdown {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.18);
    min-width: 220px;
    z-index: 99;
    overflow: hidden;
    animation: menuIn 0.15s ease;
  }
  @keyframes menuIn {
    from { opacity: 0; transform: translateY(-6px) scale(0.97); }
    to   { opacity: 1; transform: translateY(0)    scale(1); }
  }

  .menu-section-label {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: var(--text-muted);
    padding: 10px 14px 4px;
  }

  .menu-item {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 10px 14px;
    background: none;
    border: none;
    text-align: left;
    font-size: 14px;
    font-weight: 500;
    color: var(--text);
    cursor: pointer;
    transition: background 0.12s;
  }
  .menu-item:hover { background: var(--surface-2); }
  .menu-item svg { color: var(--primary); flex-shrink: 0; }

  .menu-divider { height: 1px; background: var(--border); margin: 4px 0; }

  .lang-row {
    display: flex;
    gap: 6px;
    padding: 6px 14px 12px;
  }
  .lang-btn {
    flex: 1;
    padding: 7px 6px;
    border-radius: 8px;
    border: 1.5px solid var(--border);
    background: var(--surface-2);
    font-size: 13px;
    font-weight: 500;
    color: var(--text-muted);
    cursor: pointer;
    transition: all 0.15s;
  }
  .lang-btn:hover:not(.lang-active) { background: var(--surface); }
  .lang-btn.lang-active {
    border-color: var(--primary);
    color: var(--primary);
    font-weight: 700;
    background: rgba(72, 15, 37, 0.06);
  }

  .menu-user-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 12px 8px;
    gap: 8px;
  }
  .menu-username {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-muted);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .menu-logout {
    flex-shrink: 0;
    font-size: 12px;
    font-weight: 600;
    color: #c0392b;
    background: none;
    border: 1px solid rgba(192,57,43,0.3);
    border-radius: 6px;
    padding: 3px 10px;
    cursor: pointer;
    transition: background 0.15s;
  }
  .menu-logout:hover { background: rgba(192,57,43,0.08); }

  /* Main */
  .main {
    max-width: 1400px;
    margin: 0 auto;
    width: 100%;
    padding: 24px 24px 100px;
    flex: 1;
  }

  .footer {
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
  .footer-version {
    margin-left: 8px;
    opacity: 0.5;
    color: inherit;
    text-decoration: none;
    transition: opacity 0.15s;
  }
  .footer-version:hover { opacity: 1; }
  .footer-link:hover { color: var(--primary); }

  /* Controls */
  .controls {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
    flex-wrap: wrap;
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
  .control-right {
    display: flex;
    gap: 10px;
    margin-left: auto;
    align-items: center;
  }
  .search-wrap {
    position: relative;
    display: flex;
    align-items: center;
  }
  .search-wrap svg {
    position: absolute;
    left: 10px;
    color: var(--text-muted);
    pointer-events: none;
  }
  .control-search {
    padding: 8px 12px 8px 32px;
    border: 1.5px solid var(--border);
    border-radius: 8px;
    font-size: 13px;
    background: var(--surface);
    width: 200px;
    transition: border-color 0.15s;
  }
  .control-search:focus { outline: none; border-color: var(--primary); }
  .control-sort {
    padding: 8px 10px;
    border: 1.5px solid var(--border);
    border-radius: 8px;
    font-size: 13px;
    background: var(--surface);
    cursor: pointer;
  }

  /* Grid */
  .result-count {
    font-size: 13px;
    color: var(--text-muted);
    margin-bottom: 16px;
  }
  .wine-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 20px;
  }

  /* States */
  .center {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16px;
    padding: 80px 20px;
    color: var(--text-muted);
  }
  .loader {
    width: 40px;
    height: 40px;
    border: 3px solid var(--border);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .error-box { color: #c0392b; }
  .btn-retry {
    padding: 8px 18px;
    background: var(--primary);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 14px;
  }

  .empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    padding: 80px 20px;
    color: var(--text-muted);
    text-align: center;
  }
  .empty-icon { font-size: 64px; }
  .empty h2 { font-size: 20px; color: var(--text); }
  .empty p { font-size: 14px; }

  /* FAB */
  .fab {
    position: fixed;
    bottom: 32px;
    right: 32px;
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: var(--primary);
    color: white;
    border: none;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 16px rgba(123, 29, 63, 0.4);
    transition: transform 0.2s, box-shadow 0.2s, background 0.15s;
    z-index: 50;
  }
  .fab:hover {
    background: var(--primary-light);
    transform: scale(1.08);
    box-shadow: 0 6px 24px rgba(123, 29, 63, 0.5);
  }
  .fab:active { transform: scale(0.97); }

  /* Toast */
  .toast {
    position: fixed;
    bottom: 32px;
    left: 50%;
    transform: translateX(-50%);
    background: var(--text);
    color: white;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 14px;
    z-index: 200;
    box-shadow: 0 4px 16px rgba(0,0,0,0.25);
    animation: fadeUp 0.2s ease;
  }
  @keyframes fadeUp {
    from { opacity: 0; transform: translateX(-50%) translateY(10px); }
    to { opacity: 1; transform: translateX(-50%) translateY(0); }
  }

  @media (max-width: 600px) {
    .header-inner { grid-template-columns: 1fr auto; }
    .header-right { display: none; }
    .control-right { width: 100%; }
    .control-search { flex: 1; width: auto; }
  }
</style>
