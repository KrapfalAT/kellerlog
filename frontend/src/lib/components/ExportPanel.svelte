<script>
  import { createEventDispatcher } from 'svelte';
  import { exportWines, importWines } from '$lib/api.js';
  import { t } from '$lib/stores/i18n.js';
  import Modal from './Modal.svelte';

  const dispatch = createEventDispatcher();

  let importing = false;
  let importResult = null;
  let importError = '';
  let fileInput;

  async function handleExport(format) {
    try { await exportWines(format); }
    catch { /* download errors are silent */ }
  }

  async function handleImport(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    importing = true;
    importResult = null;
    importError = '';
    try {
      importResult = await importWines(file);
    } catch {
      importError = $t('import_error');
    } finally {
      importing = false;
      e.target.value = '';
    }
  }


</script>

<Modal variant="drawer" labelledby="export-title" on:close={() => dispatch('close')}>
  <div class="panel">
    <div class="panel-header">
      <div>
        <h2 id="export-title">{$t('export_title')}</h2>
        <p class="subtitle">{$t('export_subtitle')}</p>
      </div>
      <button class="close-btn" on:click={() => dispatch('close')} aria-label="Schließen">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <div class="body">
      <section class="section">
        <div class="section-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          {$t('export_section')}
        </div>
        <p class="section-desc">{$t('export_desc')}</p>
        <div class="btn-row">
          <button class="export-btn" on:click={() => handleExport('json')}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
            </svg>
            {$t('export_json')}
          </button>
          <button class="export-btn" on:click={() => handleExport('csv')}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/>
              <line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="9" x2="9" y2="21"/>
            </svg>
            {$t('export_csv')}
          </button>
        </div>
      </section>

      <div class="divider"></div>

      <section class="section">
        <div class="section-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          {$t('import_section')}
        </div>
        <p class="section-desc">{$t('import_desc')}</p>

        <input type="file" accept=".json,.csv" bind:this={fileInput} on:change={handleImport} style="display:none" />
        <button class="import-btn" on:click={() => fileInput.click()} disabled={importing}>
          {#if importing}
            <div class="spinner"></div>
            {$t('import_loading')}
          {:else}
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            {$t('import_btn')}
          {/if}
        </button>

        {#if importResult}
          <div class="result success">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            <span><strong>{importResult.created}</strong> {importResult.created !== 1 ? $t('count_plural') : $t('count_singular')} {$t('import_success_verb')}
            {#if importResult.skipped > 0}· {importResult.skipped} {$t('import_skipped')}{/if}</span>
          </div>
        {/if}
        {#if importError}
          <div class="result error">{importError}</div>
        {/if}
      </section>
    </div>
  </div>
</Modal>

<style>
  .panel {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .panel-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    padding: 24px 24px 16px;
    border-bottom: 1px solid var(--border);
    gap: 12px;
    background: linear-gradient(135deg, var(--header-start, #5a1328) 0%, var(--header-end, #3d0d1c) 100%);
    color: white;
    flex-shrink: 0;
  }
  .panel-header h2 { font-size: 18px; font-weight: 700; }
  .subtitle { font-size: 12px; opacity: 0.7; margin-top: 3px; line-height: 1.4; }

  .close-btn {
    flex-shrink: 0;
    width: 32px; height: 32px;
    border-radius: 50%;
    border: none;
    background: rgba(255,255,255,0.15);
    color: white;
    display: flex; align-items: center; justify-content: center;
    transition: background 0.15s;
  }
  .close-btn:hover { background: rgba(255,255,255,0.25); }

  .body {
    flex: 1;
    overflow-y: auto;
    padding: 0;
  }

  .section {
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--primary);
  }

  .section-desc {
    font-size: 13px;
    color: var(--text-muted);
    line-height: 1.5;
  }

  .btn-row {
    display: flex;
    gap: 10px;
  }

  .export-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    padding: 11px 14px;
    border: 1.5px solid var(--border);
    border-radius: 10px;
    background: var(--surface-2);
    color: var(--text);
    font-size: 13px;
    font-weight: 600;
    transition: border-color 0.15s, background 0.15s;
  }
  .export-btn:hover {
    border-color: var(--primary);
    background: rgba(123, 29, 63, 0.05);
  }

  .import-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px;
    border: 2px dashed var(--border);
    border-radius: 10px;
    background: var(--surface-2);
    color: var(--text-muted);
    font-size: 13px;
    font-weight: 600;
    width: 100%;
    transition: border-color 0.15s, color 0.15s;
  }
  .import-btn:hover:not(:disabled) {
    border-color: var(--primary);
    color: var(--primary);
  }
  .import-btn:disabled { opacity: 0.6; cursor: not-allowed; }

  .divider {
    height: 1px;
    background: var(--border);
    margin: 0 24px;
  }

  .result {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 13px;
  }
  .result.success {
    background: rgba(44, 122, 75, 0.1);
    color: #2c7a4b;
    border: 1px solid rgba(44, 122, 75, 0.25);
  }
  .result.error {
    background: rgba(192, 57, 43, 0.08);
    color: var(--danger);
    border: 1px solid rgba(192, 57, 43, 0.2);
  }

  .spinner {
    width: 14px; height: 14px;
    border: 2px solid rgba(123, 29, 63, 0.2);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
