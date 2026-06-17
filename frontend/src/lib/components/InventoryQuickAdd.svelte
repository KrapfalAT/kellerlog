<script>
  import { createEventDispatcher } from 'svelte';
  import { uploadImage, lookupBarcode, searchLibrary } from '$lib/api.js';
  import { t } from '$lib/stores/i18n.js';
  import BarcodeScanner from '$lib/components/BarcodeScanner.svelte';

  export let wine;
  export let isNew = false;
  export let fromLibrary = false;

  const dispatch = createEventDispatcher();

  let qty = 1;
  let localName = wine.name || '';
  let localProducer = wine.producer || '';
  let localVintage = wine.vintage || '';
  let localType = wine.type || 'red';
  let localPrice = wine.price || '';
  let localImage = wine.image_url || '';
  let localBarcode = wine.barcode || '';
  let uploading = false;
  let uploadError = false;
  let photoInput;
  let showScanner = false;

  // Library autocomplete
  let suggestions = [];
  let showSuggestions = false;
  let selectedEntry = null;   // library entry chosen from suggestions
  let searchTimer;

  function onNameInput() {
    selectedEntry = null;       // typing again clears selection
    clearTimeout(searchTimer);
    const q = localName.trim();
    if (q.length < 1) { suggestions = []; showSuggestions = false; return; }
    searchTimer = setTimeout(async () => {
      try {
        suggestions = await searchLibrary(q);
        showSuggestions = suggestions.length > 0;
      } catch { suggestions = []; showSuggestions = false; }
    }, 200);
  }

  function pickSuggestion(entry) {
    selectedEntry  = entry;
    localName      = entry.name      || '';
    localProducer  = entry.producer  || '';
    localVintage   = entry.vintage   || '';
    localType      = entry.type      || 'red';
    localImage     = entry.image_url || '';
    localPrice     = entry.price     != null ? entry.price : '';
    localBarcode   = entry.barcode   || '';
    suggestions    = [];
    showSuggestions = false;
  }

  function clearSelection() {
    selectedEntry = null;
    localName = '';
    suggestions = [];
    showSuggestions = false;
  }

  $: typeOptions = [
    { value: 'red',      label: $t('type_red') },
    { value: 'white',    label: $t('type_white') },
    { value: 'rosé',     label: $t('type_rose') },
    { value: 'sparkling',label: $t('type_sparkling') },
    { value: 'dessert',  label: $t('type_dessert') },
    { value: 'other',    label: $t('type_other') },
  ];

  function increment() { qty++; }
  function decrement() { if (qty > 1) qty--; }

  async function handlePhoto(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    uploading = true;
    uploadError = false;
    try {
      localImage = await uploadImage(file);
    } catch {
      uploadError = true;
    } finally {
      uploading = false;
      e.target.value = '';
    }
  }

  async function handleScan(e) {
    showScanner = false;
    const barcode = e.detail;
    localBarcode = barcode;
    try {
      const result = await lookupBarcode(barcode);
      if (result?.source === 'local') {
        // Barcode already in library → overwrite all fields
        localName     = result.name      || '';
        localProducer = result.producer  || '';
        localVintage  = result.vintage   || '';
        localType     = result.type      || 'red';
        localImage    = result.image_url || '';
        localPrice    = result.price     || '';
      }
      // If not in library → barcode is saved but fields stay as typed
    } catch { /* keep barcode, ignore lookup failure */ }
  }

  function confirm() {
    if (uploading) return;
    const base = selectedEntry ? { ...selectedEntry } : { ...wine };
    dispatch('confirm', {
      wine: {
        ...base,
        name: localName,
        image_url: localImage,
        producer: localProducer,
        vintage: localVintage ? parseInt(localVintage) : null,
        type: localType,
        price: localPrice ? parseFloat(localPrice) : null,
        barcode: localBarcode,
      },
      qty,
      isNew,
    });
  }

  function cancel() {
    dispatch('cancel');
  }
</script>

{#if showScanner}
  <BarcodeScanner on:scan={handleScan} on:close={() => showScanner = false} />
{/if}

<div class="overlay">
  <div class="sheet">
    <div class="handle"></div>

    <!-- Wine header row -->
    <div class="wine-header">
      {#if !fromLibrary}
        <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
        <div class="wine-thumb" on:click={() => photoInput.click()} title="Foto aufnehmen">
          {#if uploading}
            <div class="thumb-loading"><div class="spinner-sm"></div></div>
          {:else if localImage}
            <img src={localImage} alt={localName} />
          {:else}
            <div class="thumb-placeholder">🍷</div>
          {/if}
          {#if !uploading}
            <div class="thumb-cam">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/>
                <circle cx="12" cy="13" r="4"/>
              </svg>
            </div>
          {/if}
        </div>
        <input type="file" accept="image/*" capture="environment" bind:this={photoInput} on:change={handlePhoto} style="display:none" />
      {:else if localImage}
        <div class="wine-thumb">
          <img src={localImage} alt={localName} />
        </div>
      {:else}
        <div class="wine-thumb"><div class="thumb-placeholder">🍷</div></div>
      {/if}

      <div class="wine-meta">
        {#if fromLibrary}
          <span class="lib-name">{localName}</span>
          {#if localProducer}<span class="lib-sub">{localProducer}{localVintage ? ` · ${localVintage}` : ''}</span>{/if}
        {:else}
          <div class="name-row">
            <div class="name-autocomplete">
              <input class="name-input" bind:value={localName} placeholder={$t('inv_wine_name')} on:input={onNameInput} autocomplete="off" />
              {#if showSuggestions}
                <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
                <ul class="suggestions">
                  {#each suggestions as s (s.id)}
                    <!-- svelte-ignore a11y-click-events-have-key-events -->
                    <li class="suggestion-item" on:click={() => pickSuggestion(s)}>
                      <span class="sug-name">{s.name}</span>
                      {#if s.producer || s.vintage}
                        <span class="sug-sub">{s.producer || ''}{s.vintage ? (s.producer ? ` · ${s.vintage}` : s.vintage) : ''}</span>
                      {/if}
                    </li>
                  {/each}
                </ul>
              {/if}
            </div>
            <button class="scan-btn" on:click={() => showScanner = true} title="Barcode scannen" type="button">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 9V5a2 2 0 012-2h4M3 15v4a2 2 0 002 2h4M21 9V5a2 2 0 00-2-2h-4M21 15v4a2 2 0 01-2 2h-4"/>
                <line x1="7" y1="12" x2="7" y2="12.01"/>
                <line x1="12" y1="8" x2="12" y2="16"/>
                <line x1="17" y1="12" x2="17" y2="12.01"/>
              </svg>
            </button>
          </div>
        {/if}
        {#if uploadError}
          <span class="upload-err">{$t('inv_upload_error')}</span>
        {:else if localBarcode && isNew}
          <span class="barcode-hint">Barcode: {localBarcode}</span>
        {:else if !isNew}
          <span class="stock-info">{$t('inv_stock_info')}: {wine.quantity} {$t('inv_bottles')}</span>
        {:else}
          <span class="new-badge">{$t('inv_new_wine')}</span>
        {/if}
      </div>
    </div>

    <!-- Editable fields (hidden in library mode) -->
    {#if !fromLibrary}
    <div class="fields">
      <div class="field-row">
        <div class="field">
          <label>{$t('modal_field_producer')}</label>
          <input type="text" bind:value={localProducer} placeholder={$t('modal_field_producer')} />
        </div>
        <div class="field">
          <label>{$t('modal_field_vintage')}</label>
          <input type="number" bind:value={localVintage} placeholder="2020" min="1900" max="2100" />
        </div>
      </div>
      <div class="field-row">
        <div class="field">
          <label>{$t('modal_field_type')}</label>
          <select bind:value={localType}>
            {#each typeOptions as opt}
              <option value={opt.value}>{opt.label}</option>
            {/each}
          </select>
        </div>
        <div class="field">
          <label>{$t('modal_field_price')}</label>
          <input type="number" bind:value={localPrice} placeholder="0.00" step="0.01" min="0" />
        </div>
      </div>
    </div>
    {/if}

    <!-- Qty strip -->
    <div class="qty-strip">
      <button class="qty-btn minus" on:click={decrement}>−</button>
      <div class="qty-center">
        <span class="qty-num">{qty}</span>
        <span class="qty-label">{$t('inv_qty_add')}</span>
      </div>
      <button class="qty-btn plus" on:click={increment}>+</button>
    </div>

    <!-- Actions -->
    <div class="actions">
      <button class="btn-cancel" on:click={cancel}>{$t('modal_cancel')}</button>
      <button class="btn-confirm" on:click={confirm} disabled={uploading}>
        {#if uploading}
          <div class="spinner-sm"></div>
          {$t('modal_photo_uploading')}
        {:else}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          {$t('inv_add_btn')}
        {/if}
      </button>
    </div>
  </div>
</div>

<style>
  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(26, 13, 17, 0.6);
    backdrop-filter: blur(4px);
    z-index: 300;
    display: flex;
    align-items: flex-end;
    justify-content: center;
  }

  .sheet {
    background: var(--surface);
    border-radius: 20px 20px 0 0;
    width: 100%;
    max-width: 480px;
    box-shadow: 0 -8px 40px rgba(0,0,0,0.3);
    animation: slideUp 0.22s cubic-bezier(0.34, 1.4, 0.64, 1);
    padding-bottom: env(safe-area-inset-bottom, 0px);
  }

  @keyframes slideUp {
    from { transform: translateY(40px); opacity: 0; }
    to   { transform: translateY(0);    opacity: 1; }
  }

  .handle {
    width: 36px;
    height: 4px;
    background: var(--border);
    border-radius: 2px;
    margin: 10px auto 0;
  }

  /* Wine header */
  .wine-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border);
  }

  .wine-thumb {
    width: 50px;
    height: 60px;
    border-radius: 8px;
    overflow: hidden;
    background: var(--surface-2);
    border: 1px solid var(--border);
    flex-shrink: 0;
    cursor: pointer;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .wine-thumb img { width: 100%; height: 100%; object-fit: contain; }
  .thumb-placeholder { font-size: 22px; }

  .thumb-loading {
    position: absolute;
    inset: 0;
    background: rgba(0,0,0,0.5);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .thumb-cam {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(0,0,0,0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4px 0;
    opacity: 0;
    transition: opacity 0.15s;
  }
  .wine-thumb:hover .thumb-cam { opacity: 1; }

  .wine-meta {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .name-row {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .name-autocomplete {
    flex: 1;
    min-width: 0;
    position: relative;
  }

  .suggestions {
    position: absolute;
    top: calc(100% + 4px);
    left: -8px;
    right: -8px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.18);
    list-style: none;
    z-index: 50;
    overflow: hidden;
    max-height: 200px;
    overflow-y: auto;
  }

  .suggestion-item {
    display: flex;
    flex-direction: column;
    gap: 1px;
    padding: 9px 12px;
    cursor: pointer;
    border-bottom: 1px solid var(--border);
    transition: background 0.1s;
  }
  .suggestion-item:last-child { border-bottom: none; }
  .suggestion-item:hover { background: var(--surface-2); }

  .sug-name {
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
  }
  .sug-sub {
    font-size: 11px;
    color: var(--text-muted);
  }

  .name-input {
    flex: 1;
    font-size: 15px;
    font-weight: 700;
    color: var(--text);
    border: none;
    border-bottom: 1.5px solid transparent;
    background: transparent;
    padding: 0 0 2px;
    transition: border-color 0.15s;
    min-width: 0;
  }
  .name-input:focus {
    outline: none;
    border-bottom-color: var(--primary);
  }

  .scan-btn {
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    border-radius: 8px;
    border: 1.5px solid var(--border);
    background: var(--surface-2);
    color: var(--primary);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
  }
  .scan-btn:hover {
    background: rgba(123, 29, 63, 0.08);
    border-color: var(--primary);
  }

  .lib-name {
    font-size: 15px;
    font-weight: 700;
    color: var(--text);
  }
  .lib-sub {
    font-size: 12px;
    color: var(--text-muted);
  }

  .stock-info {
    font-size: 12px;
    color: var(--primary);
    font-weight: 600;
  }
  .new-badge {
    font-size: 11px;
    color: #2c7a4b;
    font-weight: 600;
  }
  .upload-err {
    font-size: 11px;
    color: #c0392b;
    font-weight: 600;
  }
  .barcode-hint {
    font-size: 11px;
    color: var(--text-muted);
    font-family: monospace;
  }

  /* Fields */
  .fields {
    padding: 10px 16px;
    border-bottom: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    gap: 8px;
    background: var(--surface-2);
  }

  .field-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .field label {
    font-size: 10px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.4px;
  }

  .field input, .field select {
    padding: 6px 8px;
    border: 1.5px solid var(--border);
    border-radius: 6px;
    font-size: 13px;
    background: var(--surface);
    color: var(--text);
    width: 100%;
    box-sizing: border-box;
  }
  .field input:focus, .field select:focus {
    outline: none;
    border-color: var(--primary);
  }

  /* Qty strip */
  .qty-strip {
    display: flex;
    align-items: stretch;
    height: 72px;
    border-bottom: 1px solid var(--border);
  }

  .qty-btn {
    flex: 1;
    font-size: 32px;
    font-weight: 300;
    line-height: 1;
    border: none;
    background: none;
    cursor: pointer;
    transition: background 0.12s;
  }
  .qty-btn.minus { color: #c0392b; }
  .qty-btn.minus:hover { background: rgba(192, 57, 43, 0.07); }
  .qty-btn.plus  { color: var(--primary); }
  .qty-btn.plus:hover  { background: rgba(123, 29, 63, 0.07); }

  .qty-center {
    flex: 1.2;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border-left: 1px solid var(--border);
    border-right: 1px solid var(--border);
    gap: 1px;
  }
  .qty-num {
    font-size: 36px;
    font-weight: 800;
    color: var(--text);
    line-height: 1;
  }
  .qty-label {
    font-size: 10px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  /* Actions */
  .actions {
    display: flex;
    gap: 10px;
    padding: 12px 16px;
  }

  .btn-cancel {
    flex: 1;
    padding: 11px;
    border: 1.5px solid var(--border);
    border-radius: 10px;
    background: none;
    font-size: 14px;
    font-weight: 600;
    color: var(--text-muted);
    cursor: pointer;
    transition: border-color 0.15s, color 0.15s;
  }
  .btn-cancel:hover { border-color: var(--primary); color: var(--primary); }

  .btn-confirm {
    flex: 2;
    padding: 11px;
    border: none;
    border-radius: 10px;
    background: var(--primary);
    color: white;
    font-size: 14px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    cursor: pointer;
    transition: background 0.15s;
  }
  .btn-confirm:not(:disabled):hover { background: var(--primary-dark); }
  .btn-confirm:disabled { opacity: 0.6; cursor: default; }

  .spinner-sm {
    width: 14px;
    height: 14px;
    border: 2px solid rgba(255,255,255,0.4);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
    flex-shrink: 0;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
