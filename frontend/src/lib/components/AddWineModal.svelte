<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import { lookupBarcode, uploadImage } from '$lib/api.js';
  import { t, lang } from '$lib/stores/i18n.js';
  import BarcodeScanner from './BarcodeScanner.svelte';

  function autoResize(node) {
    function resize() {
      node.style.height = 'auto';
      node.style.height = node.scrollHeight + 'px';
    }
    node.addEventListener('input', resize);
    resize();
    return { destroy() { node.removeEventListener('input', resize); } };
  }

  export let wine = null;
  export let prefill = null;
  export let hideStock = false;
  export let customFields = [];

  const dispatch = createEventDispatcher();

  const emptyForm = {
    name: '', producer: '', vintage: null, grape: '',
    region: '', country: '', type: 'red', alcohol: null,
    rating: null, quantity: 1, notes: '', price: null,
    barcode: '', image_url: '', body: '', acidity: '',
    pairings: '', description: '', by_glass: false, price_per_glass: null,
    location: ''
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
  let customValues = wine?.custom_values ? { ...wine.custom_values } : {};
  let error = '';
  let saving = false;
  let showScanner = false;
  let uploading = false;
  let fileInput;

  $: googleImagesUrl = (() => {
    const parts = [form.name, form.producer, form.vintage].filter(Boolean);
    if (!parts.length) return null;
    return `https://www.google.com/search?tbm=isch&q=${encodeURIComponent(parts.join(' ') + ' wine bottle')}`;
  })();

  $: typePills = [
    { value: 'red',       emoji: '🍷', label: $t('type_red') },
    { value: 'white',     emoji: '🥂', label: $t('type_white') },
    { value: 'rosé',      emoji: '🌹', label: $t('type_rose') },
    { value: 'sparkling', emoji: '✨', label: $t('type_sparkling_long') },
    { value: 'dessert',   emoji: '🍯', label: $t('type_dessert') },
    { value: 'other',     emoji: '⚪', label: $t('type_other') },
  ];

  async function handleScan(event) {
    showScanner = false;
    const barcode = event.detail;
    form = { ...form, barcode };
    try {
      const result = await lookupBarcode(barcode);
      if (result?.source === 'local') {
        const { id, source, saved_at, updated_at, ...data } = result;
        form = { ...form, ...data };
      }
    } catch { /* barcode is set; ignore lookup failure */ }
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
        custom_values: customValues,
      });
    } finally {
      saving = false;
    }
  }

  async function uploadFile(file) {
    uploading = true;
    error = '';
    try {
      form.image_url = await uploadImage(file);
    } catch {
      error = 'modal_error_upload';
    } finally {
      uploading = false;
    }
  }

  async function handleFileUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    event.target.value = '';
    await uploadFile(file);
  }

  async function handlePaste(event) {
    const items = event.clipboardData?.items;
    if (!items) return;
    for (const item of items) {
      if (item.type.startsWith('image/')) {
        event.preventDefault();
        const file = item.getAsFile();
        if (file) await uploadFile(file);
        break;
      }
    }
  }

  async function handlePasteClick() {
    try {
      const items = await navigator.clipboard.read();
      for (const item of items) {
        const imageType = item.types.find(t => t.startsWith('image/'));
        if (imageType) {
          const blob = await item.getType(imageType);
          await uploadFile(new File([blob], 'paste', { type: imageType }));
          break;
        }
      }
    } catch { /* no image in clipboard or permission denied */ }
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
  <div class="modal" role="dialog" aria-modal="true" on:paste={handlePaste}>

    <header class="modal-header">
      <h2>{wine ? $t('modal_edit_title') : $t('modal_add_title')}</h2>
      <button class="close-btn" on:click={() => dispatch('close')} aria-label={$t('modal_cancel')}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </header>

    <div class="modal-body">
      <div class="modal-layout">

        <!-- ─── Left: Image Panel ─────────────────────────────── -->
        <aside class="image-panel">
          <div class="img-container">
            {#if form.image_url}
              <img src={form.image_url} alt={form.name} class="wine-img" />
              <button type="button" class="img-remove" on:click={() => form.image_url = ''} title={$t('modal_remove_image')}>×</button>
            {:else if uploading}
              <div class="img-placeholder">
                <span class="spinner-lg"></span>
              </div>
            {:else}
              <div class="img-placeholder">
                <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" opacity="0.25">
                  <path d="M8 2h8v2a4 4 0 014 4v10a4 4 0 01-4 4H8a4 4 0 01-4-4V8a4 4 0 014-4V2z"/>
                  <path d="M12 10v6m-3-3h6"/>
                </svg>
                <span>Kein Foto</span>
              </div>
            {/if}
          </div>

          <input type="file" accept="image/*" capture="environment" bind:this={fileInput} on:change={handleFileUpload} style="display:none" />

          <div class="img-actions">
            <button type="button" class="btn-img-action" on:click={() => fileInput.click()} disabled={uploading}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/>
                <circle cx="12" cy="13" r="4"/>
              </svg>
              {$t('modal_photo_upload')}
            </button>

            {#if googleImagesUrl}
              <a href={googleImagesUrl} target="_blank" rel="noopener noreferrer" class="btn-img-action">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/>
                  <polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
                </svg>
                Google Bilder
              </a>
            {/if}

            <button type="button" class="btn-img-action" on:click={handlePasteClick} disabled={uploading}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2"/>
                <rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>
              </svg>
              Einfügen
            </button>
          </div>

          {#if uploading}
            <span class="img-uploading"><span class="spinner-sm"></span> Wird hochgeladen…</span>
          {/if}

          <input type="text" bind:value={form.image_url} placeholder={$t('modal_image_url_placeholder')} class="url-input" />
        </aside>

        <!-- ─── Right: Content ────────────────────────────────── -->
        <div class="modal-content">
          <form on:submit|preventDefault={handleSubmit} id="wine-form">
            {#if error}
              <p class="error">{$t(error)}</p>
            {/if}

            <div class="form-grid">

              <!-- Name + barcode badge -->
              <div class="field span-2">
                <div class="label-row">
                  <label for="name">{$t('modal_field_name')}</label>
                  {#if form.barcode}
                    <span class="barcode-badge">
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor">
                        <rect x="1"  y="4" width="2" height="16"/>
                        <rect x="5"  y="4" width="1" height="16"/>
                        <rect x="8"  y="4" width="2" height="16"/>
                        <rect x="12" y="4" width="1" height="16"/>
                        <rect x="15" y="4" width="2" height="16"/>
                        <rect x="19" y="4" width="1" height="16"/>
                        <rect x="22" y="4" width="1" height="16"/>
                      </svg>
                      {form.barcode}
                    </span>
                  {/if}
                </div>
                <input id="name" type="text" bind:value={form.name} placeholder={$t('modal_field_name')} required />
              </div>

              <!-- Type pills -->
              <div class="field span-2">
                <label>{$t('modal_field_type')}</label>
                <div class="type-pills">
                  {#each typePills as pill}
                    <button type="button" class="type-pill" class:active={form.type === pill.value} on:click={() => form.type = pill.value}>
                      <span class="pill-emoji">{pill.emoji}</span>
                      <span class="pill-label">{pill.label}</span>
                    </button>
                  {/each}
                </div>
              </div>

              <div class="field">
                <label for="vintage">{$t('modal_field_vintage')}</label>
                <input id="vintage" type="number" bind:value={form.vintage} placeholder="2019" min="1900" max="2100" />
              </div>

              <div class="field">
                <label for="producer">{$t('modal_field_producer')}</label>
                <input id="producer" type="text" bind:value={form.producer} placeholder={$t('modal_field_producer')} />
              </div>

              <!-- Rating -->
              <div class="field span-2">
                <label id="rating-label">{$t('modal_field_rating')}</label>
                <div class="star-rating" role="group" aria-labelledby="rating-label">
                  {#each [1,2,3,4,5] as n}
                    <button type="button" class="star" class:filled={form.rating >= n} on:click={() => setRating(n)}>★</button>
                  {/each}
                  {#if form.rating}
                    <span class="rating-label">{form.rating}/5</span>
                  {/if}
                </div>
              </div>

              <div class="field-divider span-2"></div>

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

              <div class="field span-2">
                <label>{$t('modal_field_body')}</label>
                <div class="segment-ctrl">
                  <button type="button" class:seg-active={form.body === 'Light-bodied'}  on:click={() => form.body = form.body === 'Light-bodied'  ? '' : 'Light-bodied'}>{$t('body_light')}</button>
                  <button type="button" class:seg-active={form.body === 'Medium-bodied'} on:click={() => form.body = form.body === 'Medium-bodied' ? '' : 'Medium-bodied'}>{$t('body_medium')}</button>
                  <button type="button" class:seg-active={form.body === 'Full-bodied'}   on:click={() => form.body = form.body === 'Full-bodied'   ? '' : 'Full-bodied'}>{$t('body_full')}</button>
                </div>
              </div>

              <div class="field span-2">
                <label>{$t('modal_field_acidity')}</label>
                <div class="segment-ctrl">
                  <button type="button" class:seg-active={form.acidity === 'Low'}    on:click={() => form.acidity = form.acidity === 'Low'    ? '' : 'Low'}>{$t('acidity_low')}</button>
                  <button type="button" class:seg-active={form.acidity === 'Medium'} on:click={() => form.acidity = form.acidity === 'Medium' ? '' : 'Medium'}>{$t('acidity_medium')}</button>
                  <button type="button" class:seg-active={form.acidity === 'High'}   on:click={() => form.acidity = form.acidity === 'High'   ? '' : 'High'}>{$t('acidity_high')}</button>
                </div>
              </div>

              <div class="field-divider span-2"></div>

              <div class="field span-2">
                <label for="description">{$t('modal_field_description')}</label>
                <textarea id="description" bind:value={form.description} placeholder={$t('modal_field_description')} rows="2" use:autoResize></textarea>
              </div>

              <div class="field span-2">
                <label for="notes">{$t('modal_field_notes')}</label>
                <textarea id="notes" bind:value={form.notes} placeholder={$t('modal_field_notes')} rows="2" use:autoResize></textarea>
              </div>

              <div class="field span-2">
                <label for="pairings">{$t('modal_field_pairings')}</label>
                <input id="pairings" type="text" bind:value={form.pairings} placeholder={$t('modal_field_pairings')} />
              </div>

              <div class="field-divider span-2"></div>

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
                <label for="location">{$t('modal_field_location')}</label>
                <input id="location" type="text" bind:value={form.location} placeholder="z.B. Regal A3, Kühlschrank" />
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

              {#if customFields.length > 0}
                <div class="field span-2 custom-section">
                  <div class="custom-section-label">{$t('custom_fields_in_modal')}</div>
                  {#each customFields as cf (cf.key)}
                    <div class="field">
                      <label for="cf-{cf.key}">{$lang === 'de' ? cf.label_de : (cf.label_en || cf.label_de)}</label>
                      {#if cf.field_type === 'textarea'}
                        <textarea id="cf-{cf.key}" bind:value={customValues[cf.key]} rows="1" use:autoResize></textarea>
                      {:else}
                        <input id="cf-{cf.key}" type={cf.field_type === 'number' ? 'number' : cf.field_type === 'date' ? 'date' : 'text'} bind:value={customValues[cf.key]} />
                      {/if}
                    </div>
                  {/each}
                </div>
              {/if}

              <!-- Barcode at the bottom -->
              <div class="field-divider span-2"></div>

              <div class="field span-2">
                <label class="field-label" for="barcode-input">{$t('modal_auto_search')}</label>
                <div class="search-row">
                  <input
                    type="text"
                    id="barcode-input"
                    class="search-input"
                    placeholder={$t('modal_search_placeholder')}
                    bind:value={form.barcode}
                  />
                  <button class="btn-scan" type="button" title="Barcode scannen" on:click={() => showScanner = true}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/>
                      <circle cx="12" cy="13" r="4"/>
                    </svg>
                  </button>
                </div>
              </div>

            </div>
          </form>
        </div>
      </div>
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
    max-width: 860px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: var(--shadow-lg);
    animation: slideIn 0.2s ease;
  }

  @keyframes slideIn {
    from { transform: translateY(20px); opacity: 0; }
    to   { transform: translateY(0);    opacity: 1; }
  }

  /* ── Header ────────────────────────────────────────────── */
  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 24px;
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
  }
  .modal-header h2 { font-size: 18px; color: var(--primary); }
  .close-btn {
    background: none; border: none;
    color: var(--text-muted); padding: 4px;
    border-radius: 6px; display: flex;
    transition: color 0.15s;
  }
  .close-btn:hover { color: var(--text); }

  /* ── Body & layout ─────────────────────────────────────── */
  .modal-body {
    flex: 1;
    min-height: 0;
    overflow: hidden;
    display: flex;
  }

  .modal-layout {
    display: flex;
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }

  /* ── Image Panel (left column) ─────────────────────────── */
  .image-panel {
    width: 192px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 18px 16px;
    border-right: 1px solid var(--border);
    overflow-y: auto;
  }

  .img-container {
    width: 100%;
    aspect-ratio: 2 / 3;
    border-radius: 10px;
    overflow: hidden;
    background: var(--surface-2);
    border: 1.5px solid var(--border);
    position: relative;
    flex-shrink: 0;
  }
  .wine-img {
    width: 100%; height: 100%;
    object-fit: contain;
  }
  .img-placeholder {
    width: 100%; height: 100%;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    gap: 8px;
    color: var(--text-muted);
    font-size: 11px;
  }
  .img-remove {
    position: absolute; top: 6px; right: 6px;
    width: 22px; height: 22px;
    border-radius: 50%;
    background: rgba(0,0,0,0.6);
    color: white; border: none;
    font-size: 15px; line-height: 1;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer;
  }

  .img-actions {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }
  .btn-img-action {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 7px 10px;
    border: 1.5px solid var(--border);
    border-radius: 7px;
    background: var(--bg);
    color: var(--text-muted);
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: border-color 0.15s, color 0.15s;
    text-decoration: none;
    width: 100%;
  }
  .btn-img-action:hover:not(:disabled) {
    border-color: var(--primary);
    color: var(--primary);
  }
  .btn-img-action:disabled { opacity: 0.5; cursor: not-allowed; }

  .img-uploading {
    display: flex; align-items: center; gap: 6px;
    font-size: 11px; color: var(--primary);
  }

  .url-input {
    padding: 7px 9px;
    border: 1.5px solid var(--border);
    border-radius: 7px;
    font-size: 11px;
    background: var(--bg);
    color: var(--text-muted);
    transition: border-color 0.15s;
    width: 100%;
    box-sizing: border-box;
  }
  .url-input:focus { outline: none; border-color: var(--primary); }

  /* ── Right content column ───────────────────────────────── */
  .modal-content {
    flex: 1;
    min-height: 0;
    min-width: 0;
    overflow-y: auto;
    padding: 18px 22px;
  }

  /* ── Barcode search ─────────────────────────────────────── */
  .search-row { display: flex; gap: 8px; align-items: stretch; }
  .field-label {
    display: block;
    font-size: 11px; font-weight: 700;
    color: var(--text-muted);
    margin-bottom: 5px;
    text-transform: uppercase; letter-spacing: 0.5px;
  }
  .search-input {
    flex: 1;
    padding: 9px 12px;
    border: 1.5px solid var(--border);
    border-radius: 8px;
    font-size: 14px;
    background: var(--bg);
    transition: border-color 0.15s;
  }
  .search-input:focus { outline: none; border-color: var(--primary); }
  .btn-scan {
    flex-shrink: 0; width: 40px;
    border: 1.5px solid var(--border);
    border-radius: 8px; background: var(--bg);
    color: var(--text-muted);
    display: flex; align-items: center; justify-content: center;
    transition: border-color 0.15s, color 0.15s, background 0.15s;
  }
  .btn-scan:hover {
    border-color: var(--primary); color: var(--primary);
    background: rgba(123, 29, 63, 0.05);
  }

  /* ── Field divider ─────────────────────────────────────── */
  .field-divider {
    height: 1px;
    background: var(--border);
    margin: 2px 0;
  }

  /* ── Form grid ──────────────────────────────────────────── */
  .form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 13px;
  }
  .field {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }
  .field.span-2 { grid-column: 1 / -1; }
  .field label {
    font-size: 12px; font-weight: 600;
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
    outline: none; border-color: var(--primary);
  }
  .field textarea { resize: none; overflow: hidden; }

  /* ── Name + barcode badge row ───────────────────────────── */
  .label-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .barcode-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    background: rgba(123, 29, 63, 0.08);
    color: var(--primary);
    border: 1px solid rgba(123, 29, 63, 0.2);
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
    font-family: monospace;
  }

  /* ── Type pills ─────────────────────────────────────────── */
  .type-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }
  .type-pill {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 6px 13px;
    border: 1.5px solid var(--border);
    border-radius: 20px;
    background: var(--bg);
    color: var(--text-muted);
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: border-color 0.15s, background 0.15s, color 0.15s;
  }
  .type-pill.active {
    border-color: var(--primary);
    background: rgba(123, 29, 63, 0.08);
    color: var(--primary);
    font-weight: 600;
  }
  .type-pill:hover:not(.active) {
    border-color: var(--text-muted);
    color: var(--text);
  }
  .pill-emoji { font-size: 15px; line-height: 1; }
  .pill-label { font-size: 12px; }

  /* ── Stars ──────────────────────────────────────────────── */
  .star-rating {
    display: flex;
    align-items: center;
    gap: 2px;
  }
  .star {
    background: none; border: none;
    font-size: 30px;
    color: var(--border);
    padding: 0 3px;
    transition: color 0.1s, transform 0.12s, filter 0.12s;
    line-height: 1;
    cursor: pointer;
  }
  .star.filled { color: var(--accent); }
  .star:hover {
    transform: scale(1.2);
    filter: drop-shadow(0 0 4px rgba(200, 140, 40, 0.5));
  }
  .rating-label {
    font-size: 13px; color: var(--text-muted);
    margin-left: 8px;
  }

  /* ── Segmented control (body / acidity) ─────────────────── */
  .segment-ctrl {
    display: flex;
    border: 1.5px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
  }
  .segment-ctrl button {
    flex: 1;
    padding: 9px 4px;
    background: var(--bg);
    border: none;
    border-right: 1px solid var(--border);
    color: var(--text-muted);
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
  }
  .segment-ctrl button:last-child { border-right: none; }
  .segment-ctrl button.seg-active {
    background: var(--primary);
    color: white;
    font-weight: 600;
  }
  .segment-ctrl button:hover:not(.seg-active) {
    background: var(--surface-2);
    color: var(--text);
  }

  /* ── Toggle row ─────────────────────────────────────────── */
  .toggle-row {
    display: flex; align-items: center;
    justify-content: space-between; gap: 12px;
    padding: 10px 12px;
    background: var(--surface-2);
    border: 1.5px solid var(--border);
    border-radius: 8px;
    cursor: pointer; user-select: none;
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

  /* ── Custom fields ──────────────────────────────────────── */
  .custom-section { display: flex; flex-direction: column; gap: 10px; }
  .custom-section-label {
    font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
    color: var(--text-muted); padding-bottom: 4px; border-bottom: 1px solid var(--border);
  }

  /* ── Error ──────────────────────────────────────────────── */
  .error {
    background: #fde8e8; color: #c0392b;
    padding: 8px 12px; border-radius: 6px;
    font-size: 13px; margin-bottom: 12px;
  }

  /* ── Spinners ───────────────────────────────────────────── */
  .spinner-sm {
    width: 14px; height: 14px;
    border: 2px solid var(--border);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
    flex-shrink: 0;
    display: inline-block;
  }
  .spinner-lg {
    width: 32px; height: 32px;
    border: 3px solid var(--border);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
    display: inline-block;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Footer ─────────────────────────────────────────────── */
  .modal-footer {
    padding: 14px 22px;
    border-top: 1px solid var(--border);
    display: flex; justify-content: flex-end; gap: 10px;
    flex-shrink: 0;
  }
  .btn-primary {
    background: var(--primary); color: white;
    border: none; padding: 10px 22px;
    border-radius: 8px; font-size: 14px; font-weight: 600;
    transition: background 0.15s;
  }
  .btn-primary:hover:not(:disabled) { background: var(--primary-dark); }
  .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
  .btn-secondary {
    background: none; color: var(--text-muted);
    border: 1.5px solid var(--border);
    padding: 10px 20px; border-radius: 8px;
    font-size: 14px; font-weight: 600;
    transition: border-color 0.15s, color 0.15s;
  }
  .btn-secondary:hover { border-color: var(--primary); color: var(--primary); }

  /* ── Mobile: compact image panel on top ─────────────────── */
  @media (max-width: 639px) {
    .modal-layout { flex-direction: column; }

    .image-panel {
      width: 100%;
      flex-direction: row;
      flex-wrap: wrap;
      align-items: flex-start;
      border-right: none;
      border-bottom: 1px solid var(--border);
      padding: 12px 16px;
      gap: 10px;
      overflow-y: visible;
    }
    .img-container {
      width: 72px;
      aspect-ratio: 2 / 3;
      flex-shrink: 0;
    }
    .img-actions {
      flex-direction: column;
      flex: 1;
    }
    .url-input { display: none; }
    .img-uploading { width: 100%; }

    .modal-content { padding: 14px 16px; }
    .form-grid { grid-template-columns: 1fr; }
    .field.span-2 { grid-column: 1; }
  }

  /* ── Bottom-sheet on very small screens ─────────────────── */
  @media (max-width: 480px) {
    .backdrop { padding: 0; align-items: flex-end; }
    .modal {
      max-width: 100%;
      border-radius: 20px 20px 0 0;
      max-height: 95vh;
    }
  }
</style>
