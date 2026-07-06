<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import { getSettings, updateSettings } from '$lib/api.js';
  import { t } from '$lib/stores/i18n.js';
  import Modal from './Modal.svelte';

  const dispatch = createEventDispatcher();

  let loading = true;
  let saving = false;
  let error = '';
  let success = false;

  let kioskEnabled = true;
  let kioskTitle = 'Weinkarte';
  let kioskSubtitle = 'Unsere Weinauswahl';
  let kioskShowFooter = true;
  let kioskShowMap = true;
  let kioskShowDrinkWindow = false;

  onMount(async () => {
    try {
      const s = await getSettings();
      if (s) {
        kioskEnabled = s.kiosk_enabled;
        kioskTitle = s.kiosk_title;
        kioskSubtitle = s.kiosk_subtitle;
        kioskShowFooter = s.kiosk_show_footer;
        kioskShowMap = s.kiosk_show_map;
        kioskShowDrinkWindow = s.kiosk_show_drink_window ?? false;
      }
    } catch {
      error = $t('kiosk_panel_error');
    } finally {
      loading = false;
    }
  });

  async function save() {
    saving = true;
    error = '';
    success = false;
    try {
      await updateSettings({
        kiosk_enabled: kioskEnabled,
        kiosk_title: kioskTitle,
        kiosk_subtitle: kioskSubtitle,
        kiosk_show_footer: kioskShowFooter,
        kiosk_show_map: kioskShowMap,
        kiosk_show_drink_window: kioskShowDrinkWindow,
      });
      success = true;
      setTimeout(() => { success = false; }, 2500);
    } catch (err) {
      error = err.message;
    } finally {
      saving = false;
    }
  }


</script>

<Modal variant="drawer" labelledby="kiosk-panel-title" on:close={() => dispatch('close')}>
  <div class="panel">
    <div class="panel-header">
      <div>
        <h2 id="kiosk-panel-title">{$t('kiosk_panel_title')}</h2>
        <p class="subtitle">{$t('kiosk_panel_subtitle')}</p>
      </div>
      <button class="close-btn" on:click={() => dispatch('close')} aria-label={$t('modal_cancel')}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <div class="body">
      {#if error}
        <div class="err-banner">{error}</div>
      {/if}
      {#if success}
        <div class="ok-banner">{$t('kiosk_panel_saved')}</div>
      {/if}

      {#if loading}
        <div class="center"><div class="loader"></div></div>
      {:else}
        <div class="section">
          <div class="section-title">{$t('kiosk_panel_section_mode')}</div>
          <label class="toggle-row">
            <div class="toggle-info">
              <span class="toggle-label">{$t('kiosk_panel_enable')}</span>
              <span class="toggle-desc">{$t('kiosk_panel_enable_desc')}</span>
            </div>
            <button
              class="toggle"
              class:on={kioskEnabled}
              on:click={() => kioskEnabled = !kioskEnabled}
              role="switch"
              aria-checked={kioskEnabled}
              aria-label={$t('kiosk_panel_enable')}
            >
              <span class="thumb"></span>
            </button>
          </label>
        </div>

        <div class="section" class:dimmed={!kioskEnabled}>
          <div class="section-title">{$t('kiosk_panel_section_branding')}</div>
          <div class="field">
            <label for="kiosk-title">{$t('kiosk_panel_field_title')}</label>
            <input id="kiosk-title" type="text" bind:value={kioskTitle} disabled={!kioskEnabled} placeholder="Weinkarte" />
          </div>
          <div class="field">
            <label for="kiosk-subtitle">{$t('kiosk_panel_field_subtitle')}</label>
            <input id="kiosk-subtitle" type="text" bind:value={kioskSubtitle} disabled={!kioskEnabled} placeholder="Unsere Weinauswahl" />
          </div>
          <label class="toggle-row slim">
            <div class="toggle-info">
              <span class="toggle-label">{$t('kiosk_panel_show_map')}</span>
            </div>
            <button
              class="toggle small"
              class:on={kioskShowMap}
              on:click={() => { if (kioskEnabled) kioskShowMap = !kioskShowMap; }}
              role="switch"
              aria-checked={kioskShowMap}
              aria-label={$t('kiosk_panel_show_map')}
              disabled={!kioskEnabled}
            >
              <span class="thumb"></span>
            </button>
          </label>
          <label class="toggle-row slim">
            <div class="toggle-info">
              <span class="toggle-label">{$t('kiosk_panel_show_drink_window')}</span>
            </div>
            <button
              class="toggle small"
              class:on={kioskShowDrinkWindow}
              on:click={() => { if (kioskEnabled) kioskShowDrinkWindow = !kioskShowDrinkWindow; }}
              role="switch"
              aria-checked={kioskShowDrinkWindow}
              aria-label={$t('kiosk_panel_show_drink_window')}
              disabled={!kioskEnabled}
            >
              <span class="thumb"></span>
            </button>
          </label>
          <label class="toggle-row slim">
            <div class="toggle-info">
              <span class="toggle-label">{$t('kiosk_panel_show_footer')}</span>
            </div>
            <button
              class="toggle small"
              class:on={kioskShowFooter}
              on:click={() => { if (kioskEnabled) kioskShowFooter = !kioskShowFooter; }}
              role="switch"
              aria-checked={kioskShowFooter}
              aria-label={$t('kiosk_panel_show_footer')}
              disabled={!kioskEnabled}
            >
              <span class="thumb"></span>
            </button>
          </label>
        </div>

        <div class="footer-actions">
          <button class="btn-primary btn-full" on:click={save} disabled={saving}>
            {saving ? $t('kiosk_panel_saving') : $t('kiosk_panel_save')}
          </button>
        </div>
      {/if}
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
    background: linear-gradient(135deg, var(--header-start, #5a1328) 0%, var(--header-end, #3d0d1c) 100%);
    color: white;
    gap: 12px;
  }

  .panel-header h2 { font-size: 18px; font-weight: 700; }
  .subtitle { font-size: 12px; opacity: 0.7; margin-top: 3px; }

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
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .err-banner {
    padding: 10px 14px;
    background: rgba(192,57,43,0.1);
    border: 1px solid rgba(192,57,43,0.3);
    border-radius: 10px;
    font-size: 13px;
    color: var(--danger);
  }

  .ok-banner {
    padding: 10px 14px;
    background: rgba(39,174,96,0.1);
    border: 1px solid rgba(39,174,96,0.3);
    border-radius: 10px;
    font-size: 13px;
    color: #27ae60;
    font-weight: 600;
  }

  .center { display: flex; justify-content: center; padding: 60px; }
  .loader {
    width: 36px; height: 36px;
    border: 3px solid var(--border);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .section {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    transition: opacity 0.2s;
  }
  .section.dimmed { opacity: 0.45; pointer-events: none; }

  .section-title {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-muted);
  }

  .toggle-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    cursor: pointer;
  }
  .toggle-row.slim { padding-top: 4px; border-top: 1px solid var(--border); }

  .toggle-info { display: flex; flex-direction: column; gap: 2px; }
  .toggle-label { font-size: 14px; font-weight: 600; color: var(--text); }
  .toggle-desc { font-size: 12px; color: var(--text-muted); }

  .toggle {
    flex-shrink: 0;
    width: 44px; height: 24px;
    border-radius: 12px;
    border: none;
    background: var(--border);
    position: relative;
    cursor: pointer;
    transition: background 0.2s;
    padding: 0;
  }
  .toggle.on { background: var(--primary); }
  .toggle.small { width: 36px; height: 20px; border-radius: 10px; }

  .thumb {
    position: absolute;
    top: 2px; left: 2px;
    width: 20px; height: 20px;
    border-radius: 50%;
    background: white;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    transition: transform 0.2s;
  }
  .toggle.on .thumb { transform: translateX(20px); }
  .toggle.small .thumb { width: 16px; height: 16px; }
  .toggle.small.on .thumb { transform: translateX(16px); }

  .field {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .field label {
    font-size: 10px; font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.4px;
  }
  .field input {
    padding: 8px 10px;
    border: 1.5px solid var(--border);
    border-radius: 8px;
    background: var(--surface);
    color: var(--text);
    font-size: 14px;
  }
  .field input:focus { outline: none; border-color: var(--primary); }
  .field input:disabled { opacity: 0.5; }

  .footer-actions {
    margin-top: auto;
    padding-top: 8px;
  }

  .btn-full { width: 100%; }
</style>
