<script>
  import { createEventDispatcher } from 'svelte';
  import { t } from '$lib/stores/i18n.js';
  import { branding, DEFAULTS } from '$lib/stores/branding.js';
  import { uploadImage } from '$lib/api.js';

  const dispatch = createEventDispatcher();

  let darkMode        = $branding.darkMode ?? false;
  let showDrinkWindow = $branding.showDrinkWindow ?? true;
  let color        = $branding.primaryColor;
  let title        = $branding.title;
  let subtitle     = $branding.subtitle;
  let logoUrl         = $branding.logoUrl;
  let uploadingLogo = false;
  let logoInput;

  function onDarkMode()        { branding.save({ darkMode }); }
  function onShowDrinkWindow() { branding.save({ showDrinkWindow }); }

  function onColor(e) {
    color = e.target.value;
    branding.save({ primaryColor: color });
  }

  function onHex(e) {
    const v = e.target.value.trim();
    if (/^#[0-9a-fA-F]{6}$/.test(v)) {
      color = v;
      branding.save({ primaryColor: color });
    }
  }

  function onTitle()         { branding.save({ title }); }
  function onSubtitle()      { branding.save({ subtitle }); }

  async function handleLogoUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    uploadingLogo = true;
    try {
      logoUrl = await uploadImage(file);
      branding.save({ logoUrl });
    } finally {
      uploadingLogo = false;
      e.target.value = '';
    }
  }

  function removeLogo() {
    logoUrl = '';
    branding.save({ logoUrl: '' });
  }

  function reset() {
    darkMode        = DEFAULTS.darkMode;
    showDrinkWindow = DEFAULTS.showDrinkWindow;
    color         = DEFAULTS.primaryColor;
    title         = DEFAULTS.title;
    subtitle      = DEFAULTS.subtitle;
    logoUrl         = DEFAULTS.logoUrl;
    branding.reset();
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
        <h2>{$t('branding_panel_title')}</h2>
        <p class="subtitle-hd">{$t('branding_panel_subtitle')}</p>
      </div>
      <button class="close-btn" on:click={() => dispatch('close')} aria-label="Schließen">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <div class="body">

      <!-- Dark mode + Drink window -->
      <section class="section">
        <label class="toggle-row">
          <div>
            <div class="toggle-label">{$t('branding_darkmode')}</div>
            <div class="toggle-desc">{$t('branding_darkmode_desc')}</div>
          </div>
          <input type="checkbox" bind:checked={darkMode} on:change={onDarkMode} class="toggle-input" />
          <span class="toggle-track" class:on={darkMode}><span class="toggle-thumb"></span></span>
        </label>
        <label class="toggle-row">
          <div>
            <div class="toggle-label">{$t('branding_drink_window')}</div>
            <div class="toggle-desc">{$t('branding_drink_window_desc')}</div>
          </div>
          <input type="checkbox" bind:checked={showDrinkWindow} on:change={onShowDrinkWindow} class="toggle-input" />
          <span class="toggle-track" class:on={showDrinkWindow}><span class="toggle-thumb"></span></span>
        </label>
      </section>

      <div class="divider"></div>

      <!-- Color -->
      <section class="section">
        <div class="section-title">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><circle cx="6.5" cy="6.5" r="3.5"/><circle cx="17.5" cy="6.5" r="3.5"/><circle cx="6.5" cy="17.5" r="3.5"/><circle cx="17.5" cy="17.5" r="3.5"/></svg>
          {$t('branding_color_section')}
        </div>
        <p class="desc">{$t('branding_color_desc')}</p>
        <div class="color-row">
          <div class="color-swatch" style="background:{color}">
            <input type="color" bind:value={color} on:input={onColor} class="color-input" title="Farbe wählen" />
          </div>
          <input type="text" class="hex-input" value={color} on:change={onHex} maxlength="7" placeholder="#7B1D3F" spellcheck="false" />
          <div class="color-preview">
            <span class="preview-chip" style="background:{color}">Schaltfläche</span>
            <span class="preview-chip outline" style="border-color:{color};color:{color}">Rahmen</span>
          </div>
        </div>
      </section>

      <div class="divider"></div>

      <!-- Logo -->
      <section class="section">
        <div class="section-title">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
          {$t('branding_logo_section')}
        </div>
        <p class="desc">{$t('branding_logo_desc')}</p>

        {#if logoUrl}
          <div class="logo-preview">
            <img src={logoUrl} alt="Logo" />
            <button class="remove-btn" on:click={removeLogo} title="Logo entfernen">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
        {/if}

        <input type="file" accept="image/*" bind:this={logoInput} on:change={handleLogoUpload} style="display:none" />
        <button class="upload-btn" on:click={() => logoInput.click()} disabled={uploadingLogo}>
          {#if uploadingLogo}
            <div class="spinner"></div> {$t('branding_logo_uploading')}
          {:else}
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            {$t('branding_logo_upload')}
          {/if}
        </button>
      </section>

      <div class="divider"></div>

      <!-- Texts -->
      <section class="section">
        <div class="section-title">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>
          {$t('branding_texts_main')}
        </div>
        <div class="field">
          <label>{$t('branding_label_title')}</label>
          <input type="text" bind:value={title} on:input={onTitle} placeholder="KellerLog" maxlength="40" />
        </div>
        <div class="field">
          <label>{$t('branding_label_subtitle')}</label>
          <input type="text" bind:value={subtitle} on:input={onSubtitle} placeholder="Meine Weinsammlung" maxlength="60" />
        </div>
      </section>

      <div class="divider"></div>

      <section class="section">
        <button class="reset-btn" on:click={reset}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-4"/>
          </svg>
          {$t('branding_reset')}
        </button>
      </section>

    </div>
  </div>
</div>

<style>
  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(26, 13, 17, 0.65);
    backdrop-filter: blur(5px);
    z-index: 150;
    display: flex;
    align-items: stretch;
    justify-content: flex-end;
  }

  .panel {
    background: var(--surface);
    width: 100%;
    max-width: 400px;
    display: flex;
    flex-direction: column;
    box-shadow: -8px 0 40px rgba(0,0,0,0.25);
    animation: slideIn 0.25s ease;
  }
  @keyframes slideIn {
    from { transform: translateX(40px); opacity: 0; }
    to   { transform: translateX(0);    opacity: 1; }
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
  .subtitle-hd { font-size: 12px; opacity: 0.7; margin-top: 3px; }

  .close-btn {
    flex-shrink: 0;
    width: 32px; height: 32px;
    border-radius: 50%; border: none;
    background: rgba(255,255,255,0.15); color: white;
    display: flex; align-items: center; justify-content: center;
    transition: background 0.15s;
  }
  .close-btn:hover { background: rgba(255,255,255,0.25); }

  .body { flex: 1; overflow-y: auto; }

  .section {
    padding: 20px 24px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .section-title {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: var(--primary);
  }

  .desc {
    font-size: 13px;
    color: var(--text-muted);
    line-height: 1.5;
  }
  .hint { font-style: italic; font-size: 12px; }
  code { font-family: monospace; font-size: 12px; background: var(--surface-2); padding: 1px 5px; border-radius: 4px; border: 1px solid var(--border); }

  .divider { height: 1px; background: var(--border); margin: 0 24px; }

  /* Color */
  .color-row {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }
  .color-swatch {
    width: 44px; height: 44px;
    border-radius: 10px;
    border: 2px solid var(--border);
    position: relative;
    overflow: hidden;
    flex-shrink: 0;
    cursor: pointer;
  }
  .color-input {
    position: absolute;
    inset: -8px;
    opacity: 0;
    cursor: pointer;
    width: calc(100% + 16px);
    height: calc(100% + 16px);
  }
  .hex-input {
    width: 96px;
    padding: 8px 10px;
    border: 1.5px solid var(--border);
    border-radius: 8px;
    font-size: 13px;
    font-family: monospace;
    background: var(--surface-2);
    color: var(--text);
    transition: border-color 0.15s;
  }
  .hex-input:focus { outline: none; border-color: var(--primary); }
  .color-preview {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }
  .preview-chip {
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
    color: white;
    white-space: nowrap;
  }
  .preview-chip.outline {
    background: none !important;
    border: 1.5px solid;
  }

  /* Logo */
  .logo-preview {
    position: relative;
    width: 100%;
    height: 80px;
    background: var(--surface-2);
    border: 1.5px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .logo-preview img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    padding: 8px;
  }
  .remove-btn {
    position: absolute;
    top: 6px; right: 6px;
    width: 24px; height: 24px;
    border-radius: 50%;
    background: rgba(0,0,0,0.5);
    color: white;
    border: none;
    display: flex; align-items: center; justify-content: center;
    transition: background 0.15s;
  }
  .remove-btn:hover { background: rgba(192,57,43,0.8); }

  .upload-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 10px;
    border: 1.5px dashed var(--border);
    border-radius: 10px;
    background: var(--surface-2);
    color: var(--text-muted);
    font-size: 13px;
    font-weight: 500;
    width: 100%;
    transition: border-color 0.15s, color 0.15s;
  }
  .upload-btn:hover:not(:disabled) { border-color: var(--primary); color: var(--primary); }
  .upload-btn:disabled { opacity: 0.6; cursor: not-allowed; }

  /* Fields */
  .field { display: flex; flex-direction: column; gap: 5px; }
  .field label { font-size: 12px; font-weight: 600; color: var(--text-muted); }
  .field input {
    padding: 9px 11px;
    border: 1.5px solid var(--border);
    border-radius: 8px;
    font-size: 14px;
    background: var(--surface-2);
    color: var(--text);
    transition: border-color 0.15s;
  }
  .field input:focus { outline: none; border-color: var(--primary); }

  .toggle-label { font-size: 13px; color: var(--text); }
  .toggle-desc  { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

  /* Toggle */
  .toggle-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 13px;
    color: var(--text);
    cursor: pointer;
    user-select: none;
  }
  .toggle-input { display: none; }
  .toggle-track {
    width: 40px;
    height: 22px;
    border-radius: 11px;
    background: var(--border);
    position: relative;
    flex-shrink: 0;
    transition: background 0.2s;
  }
  .toggle-track.on { background: var(--primary); }
  .toggle-thumb {
    position: absolute;
    top: 3px;
    left: 3px;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: white;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    transition: transform 0.2s;
  }
  .toggle-track.on .toggle-thumb { transform: translateX(18px); }

  /* Reset */
  .reset-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    padding: 10px;
    width: 100%;
    border: 1.5px solid var(--border);
    border-radius: 10px;
    background: none;
    color: var(--text-muted);
    font-size: 13px;
    font-weight: 600;
    transition: border-color 0.15s, color 0.15s;
  }
  .reset-btn:hover { border-color: #c0392b; color: #c0392b; }

  .spinner {
    width: 14px; height: 14px;
    border: 2px solid rgba(123, 29, 63, 0.2);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
