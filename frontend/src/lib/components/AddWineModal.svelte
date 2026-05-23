<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import { searchWines, lookupBarcode, getWineDetails, uploadImage, searchLibrary } from '$lib/api.js';
  import { t } from '$lib/stores/i18n.js';
  import BarcodeScanner from './BarcodeScanner.svelte';

  export let wine = null;       // null = new, object = edit existing
  export let prefill = null;    // pre-fill from library without triggering edit mode
  export let hideStock = false; // hide inventory quantity field (e.g. when opened from map)

  const dispatch = createEventDispatcher();

  const emptyForm = {
    name: '', producer: '', vintage: null, grape: '',
    region: '', country: '', type: 'red', alcohol: null,
    rating: null, quantity: 1, notes: '', price: null,
    barcode: '', image_url: '', body: '', acidity: '',
    pairings: '', description: '', wineapi_id: '', by_glass: false, price_per_glass: null
  };

  function initForm() {
    if (wine) return { ...wine };
    if (prefill) {
      const { id, saved_at, updated_at, source, ...rest } = prefill;
      return { ...emptyForm, ...rest, quantity: 1 };
    }
    return { ...emptyForm };
  }

  let form = initForm();
  let searchInput = '';
  let searchResults = [];
  let isSearching = false;
  let isLoadingDetails = false;
  let hasSearched = false;
  let apiUnavailable = false;
  let searchTimeout;
  let error = '';
  let saving = false;
  let showScanner = false;
  let uploading = false;
  let fileInput;

  $: typeOptions = [
    { value: 'red',      label: $t('type_red') },
    { value: 'white',    label: $t('type_white') },
    { value: 'rosé',     label: $t('type_rose') },
    { value: 'sparkling',label: $t('type_sparkling_long') },
    { value: 'dessert',  label: $t('type_dessert') },
    { value: 'other',    label: $t('type_other') },
  ];

  function handleSearchInput(event) {
    clearTimeout(searchTimeout);
    const q = (event?.target?.value ?? searchInput).trim();
    if (!q) { searchResults = []; hasSearched = false; apiUnavailable = false; return; }

    // Barcode lookup: 8–13 Ziffern
    if (/^\d{8,13}$/.test(q)) {
      searchTimeout = setTimeout(() => doBarcodeLookup(q), 400);
    } else if (q.length >= 2) {
      searchTimeout = setTimeout(() => doSearch(q), 600);
    }
  }

  async function doSearch(q) {
    isSearching = true;
    hasSearched = false;
    apiUnavailable = false;

    const [libraryResult, apiResult] = await Promise.allSettled([
      searchLibrary(q),
      searchWines(q),
    ]);

    const local = libraryResult.status === 'fulfilled' ? libraryResult.value : [];
    let api = [];
    if (apiResult.status === 'fulfilled') {
      api = apiResult.value;
    } else if (apiResult.reason?.message === 'API_UNAVAILABLE') {
      apiUnavailable = true;
    }

    const localKeys = new Set(local.map(r => (r.name + '|' + (r.producer || '')).toLowerCase()));
    searchResults = [...local, ...api.filter(r => !localKeys.has((r.name + '|' + (r.producer || '')).toLowerCase()))];
    isSearching = false;
    hasSearched = true;
  }

  async function doBarcodeLookup(barcode) {
    isSearching = true;
    hasSearched = false;
    apiUnavailable = false;
    try {
      const result = await lookupBarcode(barcode);
      if (result) {
        if (!result.barcode) result.barcode = barcode;
        searchResults = [result];
      } else {
        searchResults = [];
        form = { ...form, barcode };
      }
    } catch {
      searchResults = [];
      form = { ...form, barcode };
    } finally {
      isSearching = false;
      hasSearched = true;
    }
  }

  async function selectResult(result) {
    if (result.source === 'local') {
      const { id, source, saved_at, updated_at, ...wineData } = result;
      form = { ...emptyForm, ...wineData, quantity: form.quantity || 1 };
      searchResults = [];
      searchInput = '';
      return;
    }

    form = {
      ...form,
      name: result.name || form.name,
      producer: result.producer || form.producer,
      type: result.type || form.type,
      region: result.region || form.region,
      country: result.country || form.country,
      rating: result.rating ?? form.rating,
      image_url: result.image_url || form.image_url,
      vintage: result.vintage ?? form.vintage,
      wineapi_id: result.wineapi_id || form.wineapi_id,
    };
    if (result.barcode) form.barcode = result.barcode;
    searchResults = [];
    searchInput = '';

    if (result.wineapi_id) {
      isLoadingDetails = true;
      try {
        const details = await getWineDetails(result.wineapi_id);
        if (details) {
          form = {
            ...form,
            grape: details.grape || form.grape,
            alcohol: details.alcohol ?? form.alcohol,
            body: details.body || form.body,
            acidity: details.acidity || form.acidity,
            pairings: details.pairings || form.pairings,
            description: details.description || form.description,
            image_url: details.image_url || form.image_url,
            rating: details.rating ?? form.rating,
            wineapi_id: details.wineapi_id || form.wineapi_id,
          };
        }
      } catch {
        // Details not critical — basic data is already set
      } finally {
        isLoadingDetails = false;
      }
    }
  }

  function handleScan(event) {
    showScanner = false;
    const barcode = event.detail;
    searchInput = barcode;
    doBarcodeLookup(barcode);
  }

  function setRating(n) {
    form.rating = form.rating === n ? null : n;
  }

  async function handleSubmit() {
    if (!form.name.trim()) { error = 'modal_error_required'; return; }
    error = '';
    saving = true;
    try {
      dispatch('save', {
        ...form,
        vintage: form.vintage ? parseInt(form.vintage) : null,
        alcohol: form.alcohol ? parseFloat(form.alcohol) : null,
        quantity: parseInt(form.quantity) || 1,
        price: form.price ? parseFloat(form.price) : null,
      });
    } finally {
      saving = false;
    }
  }

  async function handleFileUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    uploading = true;
    error = '';
    try {
      form.image_url = await uploadImage(file);
    } catch {
      error = 'modal_error_upload';
    } finally {
      uploading = false;
      event.target.value = '';
    }
  }

  function handleBackdrop(e) {
    if (e.target === e.currentTarget) dispatch('close');
  }

  onMount(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  });
</script>

{#if showScanner}
  <BarcodeScanner on:scan={handleScan} on:close={() => showScanner = false} />
{/if}

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
<div class="backdrop" on:click={handleBackdrop}>
  <div class="modal" role="dialog" aria-modal="true">
    <header class="modal-header">
      <h2>{wine ? $t('modal_edit_title') : $t('modal_add_title')}</h2>
      <button class="close-btn" on:click={() => dispatch('close')} aria-label={$t('modal_cancel')}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </header>

    <div class="modal-body">
      <!-- API Search -->
      <div class="search-section">
        <label class="field-label" for="api-search">{$t('modal_auto_search')}</label>
        <div class="search-row">
          <div class="search-input-wrap">
            <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input
              type="text"
              id="api-search"
              class="search-input"
              placeholder={$t('modal_search_placeholder')}
              bind:value={searchInput}
              on:input={handleSearchInput}
            />
            {#if isSearching}
              <div class="spinner"></div>
            {/if}
          </div>
          <button class="btn-scan" type="button" title="Barcode scannen" on:click={() => showScanner = true}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/>
              <circle cx="12" cy="13" r="4"/>
            </svg>
          </button>
        </div>

        {#if searchResults.length > 0}
          <ul class="results">
            {#each searchResults as result}
              <li>
                <!-- svelte-ignore a11y-click-events-have-key-events -->
                <button class="result-item" class:local={result.source === 'local'} on:click={() => selectResult(result)}>
                  {#if result.image_url}
                    <img src={result.image_url} alt="" class="result-img" />
                  {:else}
                    <div class="result-img-placeholder">🍷</div>
                  {/if}
                  <div class="result-info">
                    <div class="result-title">
                      <strong>{result.name}</strong>
                      {#if result.source === 'local'}
                        <span class="local-badge">{$t('modal_local_saved')}</span>
                      {/if}
                    </div>
                    {#if result.producer}<span>{result.producer}</span>{/if}
                    <span class="result-meta">{result.type}{result.country ? ' · ' + result.country : ''}</span>
                  </div>
                </button>
              </li>
            {/each}
          </ul>
        {:else if hasSearched && !isSearching && searchInput.trim().length >= 2}
          {#if apiUnavailable}
            <p class="no-results api-warn">⚠ {$t('modal_api_warn')}</p>
          {:else}
            <p class="no-results">{$t('modal_not_found')}</p>
          {/if}
        {/if}
      </div>

      {#if isLoadingDetails}
        <div class="loading-details">
          <div class="spinner-sm"></div>
          <span>{$t('modal_loading_details')}</span>
        </div>
      {/if}

      <div class="divider">
        <span>{$t('modal_wine_details')}</span>
      </div>

      <!-- Form -->
      <form on:submit|preventDefault={handleSubmit} id="wine-form">
        {#if error}
          <p class="error">{$t(error)}</p>
        {/if}

        <div class="form-grid">
          <div class="field span-2">
            <label for="name">{$t('modal_field_name')}</label>
            <input id="name" type="text" bind:value={form.name} placeholder={$t('modal_field_name')} required />
          </div>

          <div class="field">
            <label for="producer">{$t('modal_field_producer')}</label>
            <input id="producer" type="text" bind:value={form.producer} placeholder={$t('modal_field_producer')} />
          </div>

          <div class="field">
            <label for="type">{$t('modal_field_type')}</label>
            <select id="type" bind:value={form.type}>
              {#each typeOptions as opt}
                <option value={opt.value}>{opt.label}</option>
              {/each}
            </select>
          </div>

          <div class="field">
            <label for="vintage">{$t('modal_field_vintage')}</label>
            <input id="vintage" type="number" bind:value={form.vintage} placeholder="2019" min="1900" max="2100" />
          </div>

          <div class="field">
            <label for="grape">{$t('modal_field_grape')}</label>
            <input id="grape" type="text" bind:value={form.grape} placeholder={$t('modal_field_grape')} />
          </div>

          <div class="field">
            <label for="region">{$t('modal_field_region')}</label>
            <input id="region" type="text" bind:value={form.region} placeholder={$t('modal_field_region')} />
          </div>

          <div class="field">
            <label for="country">{$t('modal_field_country')}</label>
            <input id="country" type="text" bind:value={form.country} placeholder={$t('modal_field_country')} />
          </div>

          <div class="field">
            <label for="alcohol">{$t('modal_field_alcohol')}</label>
            <input id="alcohol" type="number" bind:value={form.alcohol} placeholder="13.5" step="0.1" min="0" max="25" />
          </div>

          {#if !hideStock}
          <div class="field">
            <label for="quantity">{$t('modal_field_quantity')}</label>
            <input id="quantity" type="number" bind:value={form.quantity} min="0" />
          </div>
          {/if}

          <div class="field">
            <label for="price">{$t('modal_field_price')}</label>
            <input id="price" type="number" bind:value={form.price} placeholder="0.00" step="0.01" min="0" />
          </div>

          <div class="field span-2">
            <label id="rating-label">{$t('modal_field_rating')}</label>
            <div class="star-rating" role="group" aria-labelledby="rating-label">
              {#each [1,2,3,4,5] as n}
                <button type="button" class="star" class:filled={form.rating >= n} on:click={() => setRating(n)}>
                  ★
                </button>
              {/each}
              {#if form.rating}
                <span class="rating-label">{form.rating}/5</span>
              {/if}
            </div>
          </div>

          <div class="field">
            <label for="body">{$t('modal_field_body')}</label>
            <select id="body" bind:value={form.body}>
              <option value="">—</option>
              <option value="Light-bodied">{$t('body_light')}</option>
              <option value="Medium-bodied">{$t('body_medium')}</option>
              <option value="Full-bodied">{$t('body_full')}</option>
            </select>
          </div>

          <div class="field">
            <label for="acidity">{$t('modal_field_acidity')}</label>
            <select id="acidity" bind:value={form.acidity}>
              <option value="">—</option>
              <option value="Low">{$t('acidity_low')}</option>
              <option value="Medium">{$t('acidity_medium')}</option>
              <option value="High">{$t('acidity_high')}</option>
            </select>
          </div>

          <div class="field span-2">
            <label for="pairings">{$t('modal_field_pairings')}</label>
            <input id="pairings" type="text" bind:value={form.pairings} placeholder={$t('modal_field_pairings')} />
          </div>

          <div class="field span-2">
            <label for="description">{$t('modal_field_description')}</label>
            <textarea id="description" bind:value={form.description} placeholder={$t('modal_field_description')} rows="2"></textarea>
          </div>

          <div class="field span-2">
            <label for="notes">{$t('modal_field_notes')}</label>
            <textarea id="notes" bind:value={form.notes} placeholder={$t('modal_field_notes')} rows="2"></textarea>
          </div>

          <div class="field span-2">
            <label class="toggle-row">
              <div>
                <div class="toggle-label">{$t('modal_field_by_glass')}</div>
                <div class="toggle-desc">{$t('modal_field_by_glass_desc')}</div>
              </div>
              <input type="checkbox" bind:checked={form.by_glass} class="toggle-input" />
              <span class="toggle-track" class:on={form.by_glass}><span class="toggle-thumb"></span></span>
            </label>
          </div>

          {#if form.by_glass}
          <div class="field span-2">
            <label for="price_per_glass">{$t('modal_field_price_per_glass')}</label>
            <input id="price_per_glass" type="number" bind:value={form.price_per_glass} placeholder="0.00" step="0.01" min="0" />
          </div>
          {/if}

          <div class="field span-2">
            <label>{$t('modal_field_photo')}</label>
            <div class="image-field">
              {#if form.image_url}
                <div class="img-preview">
                  <img src={form.image_url} alt={form.name} />
                  <button type="button" class="img-remove" on:click={() => form.image_url = ''} title={$t('modal_remove_image')}>×</button>
                </div>
              {/if}
              <input type="file" accept="image/*" capture="environment" bind:this={fileInput} on:change={handleFileUpload} style="display:none" />
              <button type="button" class="btn-upload" on:click={() => fileInput.click()} disabled={uploading}>
                {#if uploading}
                  <div class="spinner-sm"></div>
                  {$t('modal_photo_uploading')}
                {:else}
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/>
                    <circle cx="12" cy="13" r="4"/>
                  </svg>
                  {$t('modal_photo_upload')}
                {/if}
              </button>
              <input type="text" id="image_url" bind:value={form.image_url} placeholder={$t('modal_image_url_placeholder')} class="url-input" />
            </div>
          </div>
        </div>
      </form>
    </div>

    <footer class="modal-footer">
      <button type="button" class="btn-secondary" on:click={() => dispatch('close')}>{$t('modal_cancel')}</button>
      <button type="submit" form="wine-form" class="btn-primary" disabled={saving}>
        {saving ? $t('modal_updating') : wine ? $t('modal_update') : $t('nav_add')}
      </button>
    </footer>
  </div>
</div>

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    background: rgba(26, 13, 17, 0.6);
    backdrop-filter: blur(4px);
    z-index: 100;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
  }

  .modal {
    background: var(--surface);
    border-radius: 16px;
    width: 100%;
    max-width: 640px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: var(--shadow-lg);
    animation: slideIn 0.2s ease;
  }

  @keyframes slideIn {
    from { transform: translateY(20px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 24px;
    border-bottom: 1px solid var(--border);
  }
  .modal-header h2 {
    font-size: 18px;
    color: var(--primary);
  }
  .close-btn {
    background: none;
    border: none;
    color: var(--text-muted);
    padding: 4px;
    border-radius: 6px;
    display: flex;
    transition: color 0.15s;
  }
  .close-btn:hover { color: var(--text); }

  .modal-body {
    padding: 20px 24px;
    overflow-y: auto;
    flex: 1;
  }

  .search-section { margin-bottom: 4px; }
  .search-row {
    display: flex;
    gap: 8px;
    align-items: stretch;
  }
  .search-row .search-input-wrap { flex: 1; }
  .btn-scan {
    flex-shrink: 0;
    width: 42px;
    border: 2px solid var(--border);
    border-radius: 8px;
    background: var(--bg);
    color: var(--text-muted);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: border-color 0.15s, color 0.15s, background 0.15s;
  }
  .btn-scan:hover {
    border-color: var(--primary);
    color: var(--primary);
    background: rgba(123, 29, 63, 0.05);
  }
  .field-label {
    display: block;
    font-size: 13px;
    font-weight: 600;
    color: var(--text-muted);
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .search-input-wrap {
    position: relative;
    display: flex;
    align-items: center;
  }
  .search-icon {
    position: absolute;
    left: 12px;
    color: var(--text-muted);
    pointer-events: none;
  }
  .search-input {
    width: 100%;
    padding: 10px 12px 10px 38px;
    border: 2px solid var(--border);
    border-radius: 8px;
    font-size: 14px;
    transition: border-color 0.15s;
    background: var(--bg);
  }
  .search-input:focus {
    outline: none;
    border-color: var(--primary);
  }
  .spinner {
    position: absolute;
    right: 12px;
    width: 16px;
    height: 16px;
    border: 2px solid var(--border);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .loading-details {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 0;
    font-size: 13px;
    color: var(--primary);
  }
  .spinner-sm {
    width: 14px;
    height: 14px;
    border: 2px solid var(--border);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
    flex-shrink: 0;
  }

  .no-results {
    margin-top: 8px;
    padding: 10px 12px;
    background: var(--surface-2);
    border: 1px dashed var(--border);
    border-radius: 8px;
    font-size: 13px;
    color: var(--text-muted);
  }
  .api-warn {
    background: #fff8e6;
    border-color: #e6a817;
    color: #7a5800;
  }

  .results {
    list-style: none;
    border: 1px solid var(--border);
    border-radius: 8px;
    margin-top: 6px;
    overflow: hidden;
    max-height: 280px;
    overflow-y: auto;
  }
  .result-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    width: 100%;
    background: none;
    border: none;
    text-align: left;
    cursor: pointer;
    transition: background 0.15s;
    border-bottom: 1px solid var(--border);
  }
  .result-item:last-child { border-bottom: none; }
  .result-item:hover { background: var(--surface-2); }
  .result-img {
    width: 40px;
    height: 48px;
    object-fit: contain;
    border-radius: 4px;
    flex-shrink: 0;
  }
  .result-img-placeholder {
    width: 40px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    background: var(--surface-2);
    border-radius: 4px;
    flex-shrink: 0;
  }
  .result-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
    font-size: 13px;
  }
  .result-info strong { font-weight: 600; color: var(--text); }
  .result-info span { color: var(--text-muted); }
  .result-meta { font-size: 12px; }

  .divider {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 20px 0;
    color: var(--text-muted);
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .divider::before, .divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }

  .error {
    background: #fde8e8;
    color: #c0392b;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 13px;
    margin-bottom: 12px;
  }

  .form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
  }
  .field {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }
  .field.span-2 { grid-column: 1 / -1; }
  .field label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-muted);
  }
  .field input, .field select, .field textarea {
    padding: 8px 10px;
    border: 1.5px solid var(--border);
    border-radius: 7px;
    font-size: 14px;
    background: var(--bg);
    transition: border-color 0.15s;
  }
  .field input:focus, .field select:focus, .field textarea:focus {
    outline: none;
    border-color: var(--primary);
  }
  .field textarea { resize: vertical; }

  .star-rating {
    display: flex;
    align-items: center;
    gap: 4px;
  }
  .star {
    background: none;
    border: none;
    font-size: 24px;
    color: var(--border);
    padding: 0 2px;
    transition: color 0.1s, transform 0.1s;
    line-height: 1;
  }
  .star.filled { color: var(--accent); }
  .star:hover { transform: scale(1.15); }
  .rating-label {
    font-size: 13px;
    color: var(--text-muted);
    margin-left: 6px;
  }

  .modal-footer {
    padding: 16px 24px;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }
  .btn-primary {
    background: var(--primary);
    color: white;
    border: none;
    padding: 10px 22px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    transition: background 0.15s;
  }
  .btn-primary:hover:not(:disabled) { background: var(--primary-dark); }
  .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
  .btn-secondary {
    background: none;
    color: var(--text-muted);
    border: 1.5px solid var(--border);
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    transition: border-color 0.15s, color 0.15s;
  }
  .btn-secondary:hover { border-color: var(--primary); color: var(--primary); }

  .image-field {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .img-preview {
    position: relative;
    width: 100%;
    height: 120px;
    border-radius: 8px;
    overflow: hidden;
    background: var(--surface-2);
    border: 1.5px solid var(--border);
  }
  .img-preview img {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }
  .img-remove {
    position: absolute;
    top: 6px;
    right: 6px;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: rgba(0,0,0,0.6);
    color: white;
    border: none;
    font-size: 16px;
    line-height: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }
  .btn-upload {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    padding: 9px 14px;
    border: 1.5px dashed var(--border);
    border-radius: 8px;
    background: var(--bg);
    color: var(--text-muted);
    font-size: 13px;
    font-weight: 500;
    transition: border-color 0.15s, color 0.15s, background 0.15s;
    width: 100%;
  }
  .btn-upload:hover:not(:disabled) {
    border-color: var(--primary);
    color: var(--primary);
    background: rgba(123, 29, 63, 0.04);
  }
  .btn-upload:disabled { opacity: 0.6; cursor: not-allowed; }
  .url-input {
    padding: 8px 10px;
    border: 1.5px solid var(--border);
    border-radius: 7px;
    font-size: 13px;
    background: var(--bg);
    transition: border-color 0.15s;
    color: var(--text-muted);
  }
  .url-input:focus { outline: none; border-color: var(--primary); }

  .toggle-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 12px;
    background: var(--surface-2);
    border: 1.5px solid var(--border);
    border-radius: 8px;
    cursor: pointer;
    user-select: none;
  }
  .toggle-label { font-size: 13px; font-weight: 600; color: var(--text); }
  .toggle-desc  { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
  .toggle-input { display: none; }
  .toggle-track {
    width: 40px; height: 22px; flex-shrink: 0;
    border-radius: 11px; background: var(--border);
    position: relative; transition: background 0.2s;
  }
  .toggle-track.on { background: var(--primary); }
  .toggle-thumb {
    position: absolute; top: 3px; left: 3px;
    width: 16px; height: 16px; border-radius: 50%;
    background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    transition: transform 0.2s;
  }
  .toggle-track.on .toggle-thumb { transform: translateX(18px); }

  .result-item.local { background: rgba(123, 29, 63, 0.03); }
  .result-title {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
  }
  .local-badge {
    font-size: 10px;
    background: rgba(123, 29, 63, 0.1);
    color: var(--primary);
    border: 1px solid rgba(123, 29, 63, 0.2);
    padding: 1px 6px;
    border-radius: 8px;
    font-weight: 600;
    white-space: nowrap;
  }
</style>
