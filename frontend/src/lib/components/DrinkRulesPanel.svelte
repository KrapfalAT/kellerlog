<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import { getDrinkRules, createDrinkRule, updateDrinkRule, deleteDrinkRule, getGrapes } from '$lib/api.js';
  import { t } from '$lib/stores/i18n.js';

  const dispatch = createEventDispatcher();

  const WINE_TYPES = ['red', 'white', 'rosé', 'sparkling', 'dessert', 'other'];
  const TYPE_COLORS = { red: '#8b2035', white: '#c8a94a', rosé: '#d4607a', sparkling: '#6aabcc', dessert: '#a07040', other: '#7a7a7a' };

  let rules = [];
  let grapes = [];
  let loading = true;
  let error = '';

  let editingId = null;
  let editName = '';
  let editType = '';
  let editGrape = '';
  let editFrom = 0;
  let editTo = 5;
  let saving = false;

  let showCreate = false;
  let newName = '';
  let newType = '';
  let newGrape = '';
  let newFrom = 0;
  let newTo = 5;
  let creating = false;
  let createError = '';

  onMount(async () => {
    document.body.style.overflow = 'hidden';
    await Promise.all([load(), loadGrapes()]);
    return () => { document.body.style.overflow = ''; };
  });

  async function load() {
    loading = true;
    try {
      rules = await getDrinkRules();
    } catch {
      error = $t('drink_rules_error_load');
    } finally {
      loading = false;
    }
  }

  async function loadGrapes() {
    grapes = await getGrapes();
  }

  function startEdit(rule) {
    editingId = rule.id;
    editName  = rule.name;
    editType  = rule.wine_type ?? '';
    editGrape = rule.grape ?? '';
    editFrom  = rule.from_offset;
    editTo    = rule.to_offset;
  }

  async function saveEdit() {
    saving = true;
    try {
      await updateDrinkRule(editingId, {
        name: editName,
        wine_type: editType,
        grape: editGrape.trim() || null,
        from_offset: editFrom,
        to_offset: editTo,
      });
      editingId = null;
      await load();
      dispatch('rulesChanged');
    } catch (err) {
      error = err.message;
    } finally {
      saving = false;
    }
  }

  async function handleDelete(rule) {
    if (!confirm($t('drink_rules_confirm_delete'))) return;
    try {
      await deleteDrinkRule(rule.id);
      await load();
      dispatch('rulesChanged');
    } catch (err) {
      error = err.message;
    }
  }

  async function handleCreate() {
    if (!newName.trim()) return;
    creating = true;
    createError = '';
    try {
      await createDrinkRule({
        name: newName.trim(),
        wine_type: newType,
        grape: newGrape.trim() || null,
        from_offset: newFrom,
        to_offset: newTo,
      });
      newName = ''; newType = ''; newGrape = ''; newFrom = 0; newTo = 5;
      showCreate = false;
      await load();
      dispatch('rulesChanged');
    } catch (err) {
      createError = err.message;
    } finally {
      creating = false;
    }
  }

  function handleBackdrop(e) {
    if (e.target === e.currentTarget) dispatch('close');
  }

  function windowLabel(from, to) {
    const yr = new Date().getFullYear() - 3;
    return `${yr + from} – ${yr + to}`;
  }

  function ruleMatchLabel(rule) {
    const parts = [];
    if (rule.wine_type) parts.push(rule.wine_type);
    if (rule.grape) parts.push(rule.grape);
    return parts.length ? parts.join(' · ') : $t('drink_rules_any_type');
  }

  const STATUS_DOTS = [
    { key: 'young', color: '#5b9bd5' },
    { key: 'ready', color: '#27ae60' },
    { key: 'late',  color: '#e67e22' },
    { key: 'past',  color: '#c0392b' },
  ];
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
<div class="overlay" on:click={handleBackdrop}>
  <div class="panel">
    <div class="panel-header">
      <div>
        <h2>{$t('drink_rules_title')}</h2>
        <p class="subtitle">{$t('drink_rules_subtitle')}</p>
      </div>
      <button class="close-btn" on:click={() => dispatch('close')}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <div class="body">
      {#if error}
        <div class="err-banner">{error}</div>
      {/if}

      <div class="info-box">
        <div class="info-title">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          {$t('drink_rules_how_title')}
        </div>
        <p class="info-text">{$t('drink_rules_how_text')}</p>
        <div class="status-row">
          {#each STATUS_DOTS as s}
            <span class="status-item">
              <span class="dot" style="background:{s.color}"></span>
              {$t(`drink_${s.key}`)}
            </span>
          {/each}
        </div>
        <p class="info-note">{$t('drink_rules_no_match')}</p>
      </div>

      {#if loading}
        <div class="center"><div class="loader"></div></div>
      {:else}
        <ul class="rule-list">
          {#each rules as rule (rule.id)}
            <li class="rule-row">
              {#if editingId === rule.id}
                <div class="edit-form">
                  <div class="field">
                    <label>{$t('drink_rules_name')}</label>
                    <input type="text" bind:value={editName} />
                  </div>
                  <div class="two-col">
                    <div class="field">
                      <label>{$t('drink_rules_type')}</label>
                      <select bind:value={editType}>
                        <option value="">{$t('drink_rules_any_type')}</option>
                        {#each WINE_TYPES as wt}
                          <option value={wt}>{wt}</option>
                        {/each}
                      </select>
                    </div>
                    <div class="field">
                      <label>{$t('drink_rules_grape')}</label>
                      <input type="text" list="grape-list" bind:value={editGrape} placeholder={$t('drink_rules_any_grape')} />
                    </div>
                  </div>
                  <div class="offset-row">
                    <div class="field">
                      <label>{$t('drink_rules_from')} <span class="example">+{editFrom}J.</span></label>
                      <input type="number" min="0" max="50" bind:value={editFrom} />
                    </div>
                    <div class="arrow">→</div>
                    <div class="field">
                      <label>{$t('drink_rules_to')} <span class="example">+{editTo}J.</span></label>
                      <input type="number" min="1" max="100" bind:value={editTo} />
                    </div>
                  </div>
                  <div class="edit-actions">
                    <button class="btn-cancel" on:click={() => editingId = null}>{$t('drink_rules_cancel')}</button>
                    <button class="btn-save" on:click={saveEdit} disabled={saving}>
                      {saving ? $t('drink_rules_saving') : $t('drink_rules_save')}
                    </button>
                  </div>
                </div>
              {:else}
                <div class="rule-info">
                  <span class="type-dot" style="background:{rule.wine_type ? (TYPE_COLORS[rule.wine_type] ?? '#888') : '#aaa'}"></span>
                  <div class="rule-text">
                    <span class="rule-name">{rule.name}</span>
                    <span class="rule-meta">{ruleMatchLabel(rule)} · +{rule.from_offset} bis +{rule.to_offset} Jahre</span>
                  </div>
                  <div class="window-preview">{windowLabel(rule.from_offset, rule.to_offset)}</div>
                </div>
                <div class="row-actions">
                  <button class="icon-btn" title="Bearbeiten" on:click={() => startEdit(rule)}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>
                  <button class="icon-btn danger" title="Löschen" on:click={() => handleDelete(rule)}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="3 6 5 6 21 6"/>
                      <path d="M19 6l-1 14H6L5 6"/>
                      <path d="M10 11v6M14 11v6M9 6V4h6v2"/>
                    </svg>
                  </button>
                </div>
              {/if}
            </li>
          {/each}
        </ul>

        {#if showCreate}
          <div class="create-form">
            {#if createError}<div class="err-inline">{createError}</div>{/if}
            <div class="field">
              <label for="new-name">{$t('drink_rules_name')}</label>
              <input id="new-name" type="text" bind:value={newName} placeholder="z.B. Barolo / Gran Reserva" />
            </div>
            <div class="two-col">
              <div class="field">
                <label for="new-type">{$t('drink_rules_type')}</label>
                <select id="new-type" bind:value={newType}>
                  <option value="">{$t('drink_rules_any_type')}</option>
                  {#each WINE_TYPES as wt}
                    <option value={wt}>{wt}</option>
                  {/each}
                </select>
              </div>
              <div class="field">
                <label for="new-grape">{$t('drink_rules_grape')}</label>
                <input id="new-grape" type="text" list="grape-list" bind:value={newGrape} placeholder={$t('drink_rules_any_grape')} />
              </div>
            </div>
            <div class="offset-row">
              <div class="field">
                <label>{$t('drink_rules_from')} <span class="example">+{newFrom}J.</span></label>
                <input type="number" min="0" max="50" bind:value={newFrom} />
              </div>
              <div class="arrow">→</div>
              <div class="field">
                <label>{$t('drink_rules_to')} <span class="example">+{newTo}J.</span></label>
                <input type="number" min="1" max="100" bind:value={newTo} />
              </div>
            </div>
            <div class="edit-actions">
              <button class="btn-cancel" on:click={() => { showCreate = false; createError = ''; }}>{$t('drink_rules_cancel')}</button>
              <button class="btn-save" on:click={handleCreate} disabled={creating || !newName.trim()}>
                {creating ? $t('drink_rules_creating') : $t('drink_rules_create')}
              </button>
            </div>
          </div>
        {:else}
          <button class="btn-add" on:click={() => showCreate = true}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            {$t('drink_rules_add')}
          </button>
        {/if}
      {/if}
    </div>
  </div>
</div>

<datalist id="grape-list">
  {#each grapes as g}
    <option value={g}></option>
  {/each}
</datalist>

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
    width: 100%; max-width: 460px;
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

  .body { flex: 1; overflow-y: auto; padding: 12px 0 16px; }

  .err-banner {
    margin: 0 16px 8px;
    padding: 10px 14px;
    background: rgba(192,57,43,0.1); border: 1px solid rgba(192,57,43,0.3);
    border-radius: 10px; font-size: 13px; color: #c0392b;
  }

  .info-box {
    margin: 0 16px 12px;
    padding: 12px 14px;
    background: var(--surface-2); border: 1px solid var(--border);
    border-radius: 10px; display: flex; flex-direction: column; gap: 6px;
  }
  .info-title {
    display: flex; align-items: center; gap: 6px;
    font-size: 11px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.4px; color: var(--text-muted);
  }
  .info-text { font-size: 12px; color: var(--text-muted); line-height: 1.5; }
  .info-note { font-size: 11px; color: var(--text-muted); font-style: italic; }

  .status-row { display: flex; flex-wrap: wrap; gap: 8px; }
  .status-item {
    display: flex; align-items: center; gap: 5px;
    font-size: 11px; font-weight: 600; color: var(--text);
  }
  .dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

  .center { display: flex; justify-content: center; padding: 40px; }
  .loader {
    width: 32px; height: 32px;
    border: 3px solid var(--border); border-top-color: var(--primary);
    border-radius: 50%; animation: spin 0.7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .rule-list { list-style: none; }
  .rule-row { padding: 10px 16px; border-bottom: 1px solid var(--border); }
  .rule-info { display: flex; align-items: center; gap: 10px; }
  .type-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  .rule-text { flex: 1; display: flex; flex-direction: column; gap: 2px; }
  .rule-name { font-size: 13px; font-weight: 600; color: var(--text); }
  .rule-meta { font-size: 11px; color: var(--text-muted); }
  .window-preview {
    font-size: 11px; font-weight: 600;
    color: var(--primary); font-variant-numeric: tabular-nums; white-space: nowrap;
  }

  .row-actions { display: flex; gap: 4px; margin-top: 6px; justify-content: flex-end; }
  .icon-btn {
    width: 28px; height: 28px; border-radius: 50%; border: none;
    background: none; color: var(--text-muted);
    display: flex; align-items: center; justify-content: center;
    transition: color 0.15s, background 0.15s;
  }
  .icon-btn:hover { color: var(--primary); background: rgba(123,29,63,0.08); }
  .icon-btn.danger:hover { color: #c0392b; background: rgba(192,57,43,0.08); }

  .edit-form, .create-form {
    display: flex; flex-direction: column; gap: 8px;
  }
  .create-form {
    margin: 8px 16px 0;
    padding: 14px;
    background: var(--surface-2); border: 1px solid var(--border);
    border-radius: 12px;
  }
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .field { display: flex; flex-direction: column; gap: 4px; }
  .field label {
    font-size: 10px; font-weight: 600; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.4px;
    display: flex; align-items: center; gap: 4px;
  }
  .example { font-size: 10px; color: var(--primary); font-weight: 700; text-transform: none; }
  .field input, .field select {
    padding: 7px 9px; border: 1.5px solid var(--border);
    border-radius: 8px; background: var(--surface); color: var(--text); font-size: 13px;
  }
  .field input:focus, .field select:focus { outline: none; border-color: var(--primary); }

  .offset-row { display: grid; grid-template-columns: 1fr auto 1fr; align-items: end; gap: 6px; }
  .arrow { font-size: 16px; color: var(--text-muted); padding-bottom: 7px; text-align: center; }

  .edit-actions { display: flex; gap: 8px; margin-top: 2px; }
  .btn-cancel {
    flex: 1; padding: 7px 10px; border: 1.5px solid var(--border);
    border-radius: 8px; background: none; font-size: 13px; font-weight: 600;
    color: var(--text-muted); transition: border-color 0.15s, color 0.15s;
  }
  .btn-cancel:hover { border-color: var(--primary); color: var(--primary); }
  .btn-save {
    flex: 2; padding: 7px 10px; border: none; border-radius: 8px;
    background: var(--primary); color: white; font-size: 13px; font-weight: 600;
    transition: background 0.15s;
  }
  .btn-save:hover:not(:disabled) { background: var(--primary-dark); }
  .btn-save:disabled { opacity: 0.55; cursor: default; }

  .err-inline {
    font-size: 12px; color: #c0392b;
    background: rgba(192,57,43,0.08); border-radius: 6px; padding: 6px 10px;
  }

  .btn-add {
    margin: 10px 16px 0;
    padding: 9px 14px;
    border: 1.5px dashed var(--border); border-radius: 10px;
    background: none; color: var(--text-muted); font-size: 13px; font-weight: 600;
    display: flex; align-items: center; gap: 7px;
    width: calc(100% - 32px); transition: border-color 0.15s, color 0.15s;
  }
  .btn-add:hover { border-color: var(--primary); color: var(--primary); }
</style>
