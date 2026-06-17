<script>
  import { createEventDispatcher } from 'svelte';
  import { t } from '$lib/stores/i18n.js';

  export let count = 0;

  const dispatch = createEventDispatcher();

  const WINE_TYPES = ['red', 'white', 'rosé', 'sparkling', 'dessert', 'other'];
  const BODIES     = ['Light-bodied', 'Medium-bodied', 'Full-bodied'];
  const ACIDITIES  = ['Low', 'Medium', 'High'];

  let enable = { type: false, location: false, region: false, country: false, producer: false, rating: false, body: false, acidity: false };
  let values = { type: 'red', location: '', region: '', country: '', producer: '', rating: null, body: '', acidity: '' };
  let saving = false;

  $: anyEnabled = Object.values(enable).some(Boolean);

  async function handleSave() {
    if (!anyEnabled) return;
    const updates = {};
    for (const [field, on] of Object.entries(enable)) {
      if (on) updates[field] = values[field];
    }
    saving = true;
    dispatch('save', updates);
  }

  function handleBackdrop(e) {
    if (e.target === e.currentTarget) dispatch('close');
  }
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
<div class="overlay" on:click={handleBackdrop}>
  <div class="panel">
    <div class="panel-header">
      <div>
        <h2>{$t('batch_panel_title')}</h2>
        <p class="subtitle">{count} {count === 1 ? $t('count_singular') : $t('count_plural')} · {$t('batch_panel_subtitle')}</p>
      </div>
      <button class="close-btn" on:click={() => dispatch('close')}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <div class="body">
      <div class="field-list">

        <div class="field-row" class:active={enable.type}>
          <label class="enable-toggle">
            <input type="checkbox" bind:checked={enable.type} />
            <span class="enable-label">{$t('modal_field_type')}</span>
          </label>
          <select bind:value={values.type} disabled={!enable.type}>
            {#each WINE_TYPES as t}
              <option value={t}>{t}</option>
            {/each}
          </select>
        </div>

        <div class="field-row" class:active={enable.location}>
          <label class="enable-toggle">
            <input type="checkbox" bind:checked={enable.location} />
            <span class="enable-label">{$t('modal_field_location')}</span>
          </label>
          <input type="text" bind:value={values.location} disabled={!enable.location} placeholder="z.B. Regal A3" />
        </div>

        <div class="field-row" class:active={enable.producer}>
          <label class="enable-toggle">
            <input type="checkbox" bind:checked={enable.producer} />
            <span class="enable-label">{$t('modal_field_producer')}</span>
          </label>
          <input type="text" bind:value={values.producer} disabled={!enable.producer} />
        </div>

        <div class="field-row" class:active={enable.region}>
          <label class="enable-toggle">
            <input type="checkbox" bind:checked={enable.region} />
            <span class="enable-label">{$t('modal_field_region')}</span>
          </label>
          <input type="text" bind:value={values.region} disabled={!enable.region} />
        </div>

        <div class="field-row" class:active={enable.country}>
          <label class="enable-toggle">
            <input type="checkbox" bind:checked={enable.country} />
            <span class="enable-label">{$t('modal_field_country')}</span>
          </label>
          <input type="text" bind:value={values.country} disabled={!enable.country} />
        </div>

        <div class="field-row" class:active={enable.rating}>
          <label class="enable-toggle">
            <input type="checkbox" bind:checked={enable.rating} />
            <span class="enable-label">{$t('modal_field_rating')}</span>
          </label>
          <select bind:value={values.rating} disabled={!enable.rating}>
            <option value={1}>★☆☆☆☆</option>
            <option value={2}>★★☆☆☆</option>
            <option value={3}>★★★☆☆</option>
            <option value={4}>★★★★☆</option>
            <option value={5}>★★★★★</option>
          </select>
        </div>

        <div class="field-row" class:active={enable.body}>
          <label class="enable-toggle">
            <input type="checkbox" bind:checked={enable.body} />
            <span class="enable-label">{$t('modal_field_body')}</span>
          </label>
          <select bind:value={values.body} disabled={!enable.body}>
            {#each BODIES as b}
              <option value={b}>{$t(`body_${b === 'Light-bodied' ? 'light' : b === 'Medium-bodied' ? 'medium' : 'full'}`)}</option>
            {/each}
          </select>
        </div>

        <div class="field-row" class:active={enable.acidity}>
          <label class="enable-toggle">
            <input type="checkbox" bind:checked={enable.acidity} />
            <span class="enable-label">{$t('modal_field_acidity')}</span>
          </label>
          <select bind:value={values.acidity} disabled={!enable.acidity}>
            {#each ACIDITIES as a}
              <option value={a}>{$t(`acidity_${a === 'Low' ? 'low' : a === 'Medium' ? 'medium' : 'high'}`)}</option>
            {/each}
          </select>
        </div>

      </div>
    </div>

    <div class="panel-footer">
      <button class="btn-cancel" on:click={() => dispatch('close')}>{$t('modal_cancel')}</button>
      <button class="btn-save" on:click={handleSave} disabled={!anyEnabled || saving}>
        {saving ? $t('batch_saving') : $t('batch_save')}
      </button>
    </div>
  </div>
</div>

<style>
  .overlay {
    position: fixed; inset: 0;
    background: rgba(26,13,17,0.65);
    backdrop-filter: blur(5px);
    z-index: 150;
    display: flex; align-items: stretch; justify-content: flex-end;
  }
  .panel {
    background: var(--surface);
    width: 100%; max-width: 400px;
    display: flex; flex-direction: column;
    box-shadow: -8px 0 40px rgba(0,0,0,0.25);
    animation: slideIn 0.25s ease;
  }
  @keyframes slideIn {
    from { transform: translateX(40px); opacity: 0; }
    to   { transform: translateX(0); opacity: 1; }
  }
  .panel-header {
    display: flex; align-items: flex-start; justify-content: space-between;
    padding: 24px 24px 16px;
    border-bottom: 1px solid var(--border);
    background: linear-gradient(135deg, var(--header-start, #5a1328) 0%, var(--header-end, #3d0d1c) 100%);
    color: white; gap: 12px;
  }
  .panel-header h2 { font-size: 18px; font-weight: 700; }
  .subtitle { font-size: 12px; opacity: 0.7; margin-top: 3px; }
  .close-btn {
    flex-shrink: 0; width: 32px; height: 32px; border-radius: 50%;
    border: none; background: rgba(255,255,255,0.15); color: white;
    display: flex; align-items: center; justify-content: center; transition: background 0.15s;
  }
  .close-btn:hover { background: rgba(255,255,255,0.25); }

  .body { flex: 1; overflow-y: auto; padding: 8px 0; }

  .field-list { display: flex; flex-direction: column; }

  .field-row {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 20px;
    border-bottom: 1px solid var(--border);
    transition: background 0.12s;
  }
  .field-row.active { background: rgba(72,15,37,0.04); }

  .enable-toggle {
    display: flex; align-items: center; gap: 8px;
    cursor: pointer; flex-shrink: 0; width: 130px;
  }
  .enable-toggle input[type="checkbox"] {
    width: 15px; height: 15px; accent-color: var(--primary); cursor: pointer;
  }
  .enable-label {
    font-size: 13px; font-weight: 600; color: var(--text-muted);
    transition: color 0.15s;
  }
  .field-row.active .enable-label { color: var(--text); }

  .field-row input[type="text"],
  .field-row select {
    flex: 1;
    padding: 7px 9px;
    border: 1.5px solid var(--border);
    border-radius: 8px;
    background: var(--surface);
    color: var(--text);
    font-size: 13px;
    transition: border-color 0.15s, opacity 0.15s;
  }
  .field-row.active input[type="text"],
  .field-row.active select { border-color: var(--primary); }
  .field-row input:disabled,
  .field-row select:disabled { opacity: 0.4; }
  .field-row input:focus,
  .field-row select:focus { outline: none; border-color: var(--primary); }

  .panel-footer {
    display: flex; gap: 10px;
    padding: 16px 20px;
    border-top: 1px solid var(--border);
    background: var(--surface-2);
  }
  .btn-cancel {
    flex: 1; padding: 10px; border: 1.5px solid var(--border);
    border-radius: 10px; background: none; font-size: 14px; font-weight: 600;
    color: var(--text-muted); transition: border-color 0.15s, color 0.15s;
  }
  .btn-cancel:hover { border-color: var(--primary); color: var(--primary); }
  .btn-save {
    flex: 2; padding: 10px; border: none; border-radius: 10px;
    background: var(--primary); color: white; font-size: 14px; font-weight: 600;
    transition: background 0.15s;
  }
  .btn-save:hover:not(:disabled) { background: var(--primary-dark); }
  .btn-save:disabled { opacity: 0.45; cursor: default; }
</style>
