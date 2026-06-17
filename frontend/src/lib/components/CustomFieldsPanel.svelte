<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import { getCustomFields, createCustomField, updateCustomField, deleteCustomField } from '$lib/api.js';
  import { t } from '$lib/stores/i18n.js';

  const dispatch = createEventDispatcher();

  let fields = [];
  let loading = true;
  let showCreate = false;
  let saving = false;
  let createError = '';
  let editingId = null;

  const FIELD_TYPES = ['text', 'textarea', 'number', 'date'];

  let newKey = '';
  let newLabelDe = '';
  let newLabelEn = '';
  let newType = 'text';
  let newOrder = 0;

  let editLabelDe = '';
  let editLabelEn = '';
  let editType = 'text';
  let editOrder = 0;

  onMount(async () => {
    await reload();
  });

  async function reload() {
    loading = true;
    try { fields = await getCustomFields(); } finally { loading = false; }
  }

  function slugify(s) {
    return s.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '').slice(0, 40);
  }

  $: if (newLabelDe && !editingId) {
    newKey = slugify(newLabelDe);
  }

  async function handleCreate() {
    if (!newKey.trim() || !newLabelDe.trim()) {
      createError = 'Schlüssel und Deutsche Bezeichnung sind erforderlich.';
      return;
    }
    saving = true;
    createError = '';
    try {
      await createCustomField({ key: newKey.trim(), label_de: newLabelDe.trim(), label_en: newLabelEn.trim(), field_type: newType, sort_order: newOrder });
      newKey = ''; newLabelDe = ''; newLabelEn = ''; newType = 'text'; newOrder = 0;
      showCreate = false;
      await reload();
      dispatch('changed');
    } catch (e) {
      createError = e.message;
    } finally {
      saving = false;
    }
  }

  function startEdit(field) {
    editingId = field.id;
    editLabelDe = field.label_de;
    editLabelEn = field.label_en;
    editType = field.field_type;
    editOrder = field.sort_order;
  }

  async function handleSaveEdit(field) {
    saving = true;
    try {
      await updateCustomField(field.id, { label_de: editLabelDe, label_en: editLabelEn, field_type: editType, sort_order: editOrder });
      editingId = null;
      await reload();
      dispatch('changed');
    } finally {
      saving = false;
    }
  }

  async function handleDelete(field) {
    if (!confirm($t('custom_fields_confirm_delete'))) return;
    try {
      await deleteCustomField(field.id);
      await reload();
      dispatch('changed');
    } catch {}
  }
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
<div class="overlay" on:click={(e) => e.target === e.currentTarget && dispatch('close')}>
  <div class="panel">
    <div class="panel-header">
      <div>
        <h2>{$t('custom_fields_title')}</h2>
        <p class="subtitle">{$t('custom_fields_subtitle')}</p>
      </div>
      <button class="close-btn" on:click={() => dispatch('close')}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <div class="body">
      {#if loading}
        <div class="center"><div class="spinner"></div></div>
      {:else}
        <ul class="field-list">
          {#each fields as field (field.id)}
            <li class="field-item">
              {#if editingId === field.id}
                <div class="edit-form">
                  <div class="edit-key">🔑 <code>{field.key}</code></div>
                  <div class="two-col">
                    <div class="form-field">
                      <label for="edit-de-{field.id}">{$t('custom_fields_label_de')}</label>
                      <input id="edit-de-{field.id}" type="text" bind:value={editLabelDe} />
                    </div>
                    <div class="form-field">
                      <label for="edit-en-{field.id}">{$t('custom_fields_label_en')}</label>
                      <input id="edit-en-{field.id}" type="text" bind:value={editLabelEn} />
                    </div>
                  </div>
                  <div class="two-col">
                    <div class="form-field">
                      <label for="edit-type-{field.id}">{$t('custom_fields_type')}</label>
                      <select id="edit-type-{field.id}" bind:value={editType}>
                        {#each FIELD_TYPES as ft}
                          <option value={ft}>{$t(`custom_fields_type_${ft}`)}</option>
                        {/each}
                      </select>
                    </div>
                    <div class="form-field">
                      <label for="edit-order-{field.id}">{$t('custom_fields_sort_order')}</label>
                      <input id="edit-order-{field.id}" type="number" bind:value={editOrder} min="0" />
                    </div>
                  </div>
                  <div class="edit-actions">
                    <button class="btn-cancel" on:click={() => editingId = null}>{$t('custom_fields_cancel')}</button>
                    <button class="btn-save" on:click={() => handleSaveEdit(field)} disabled={saving}>
                      {saving ? $t('custom_fields_saving') : $t('custom_fields_save')}
                    </button>
                  </div>
                </div>
              {:else}
                <div class="field-info">
                  <div class="field-labels">
                    <span class="label-de">{field.label_de}</span>
                    {#if field.label_en}
                      <span class="label-en">/ {field.label_en}</span>
                    {/if}
                    <span class="type-tag">{$t(`custom_fields_type_${field.field_type}`)}</span>
                  </div>
                  <code class="field-key">{field.key}</code>
                </div>
                <div class="row-actions">
                  <button class="icon-btn" on:click={() => startEdit(field)} title="Bearbeiten">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>
                  <button class="icon-btn danger" on:click={() => handleDelete(field)} title="Löschen">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="3 6 5 6 21 6"/>
                      <path d="M19 6l-1 14H6L5 6"/>
                      <path d="M10 11v6M14 11v6M9 6V4h6v2"/>
                    </svg>
                  </button>
                </div>
              {/if}
            </li>
          {:else}
            <li class="empty-hint">{$t('custom_fields_empty')}</li>
          {/each}
        </ul>

        {#if showCreate}
          <div class="create-form">
            {#if createError}<div class="err-msg">{createError}</div>{/if}
            <div class="two-col">
              <div class="form-field">
                <label for="new-label-de">{$t('custom_fields_label_de')} *</label>
                <input id="new-label-de" type="text" bind:value={newLabelDe} placeholder="z.B. Trinktemperatur" />
              </div>
              <div class="form-field">
                <label for="new-label-en">{$t('custom_fields_label_en')}</label>
                <input id="new-label-en" type="text" bind:value={newLabelEn} placeholder="e.g. Serving Temperature" />
              </div>
            </div>
            <div class="form-field">
              <label for="new-key">{$t('custom_fields_key_label')} *</label>
              <input id="new-key" type="text" bind:value={newKey} placeholder={$t('custom_fields_key_placeholder')} />
            </div>
            <div class="two-col">
              <div class="form-field">
                <label for="new-type">{$t('custom_fields_type')}</label>
                <select id="new-type" bind:value={newType}>
                  {#each FIELD_TYPES as ft}
                    <option value={ft}>{$t(`custom_fields_type_${ft}`)}</option>
                  {/each}
                </select>
              </div>
              <div class="form-field">
                <label for="new-order">{$t('custom_fields_sort_order')}</label>
                <input id="new-order" type="number" bind:value={newOrder} min="0" />
              </div>
            </div>
            <div class="create-actions">
              <button class="btn-cancel" on:click={() => { showCreate = false; createError = ''; }}>{$t('custom_fields_cancel')}</button>
              <button class="btn-save" on:click={handleCreate} disabled={saving}>
                {saving ? $t('custom_fields_creating') : $t('custom_fields_create')}
              </button>
            </div>
          </div>
        {:else}
          <button class="btn-add" on:click={() => showCreate = true}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            {$t('custom_fields_add')}
          </button>
        {/if}
      {/if}
    </div>
  </div>
</div>

<style>
  .overlay {
    position: fixed; inset: 0;
    background: rgba(26,13,17,0.6);
    backdrop-filter: blur(5px);
    z-index: 150;
    display: flex; align-items: stretch; justify-content: flex-end;
  }
  .panel {
    background: var(--surface);
    width: 100%; max-width: 480px;
    display: flex; flex-direction: column;
    box-shadow: -8px 0 40px rgba(0,0,0,0.2);
    animation: slideIn 0.22s ease;
  }
  @keyframes slideIn {
    from { transform: translateX(40px); opacity: 0; }
    to   { transform: translateX(0);    opacity: 1; }
  }
  .panel-header {
    display: flex; align-items: flex-start; justify-content: space-between;
    padding: 22px 22px 16px;
    border-bottom: 1px solid var(--border);
    background: linear-gradient(135deg, var(--header-start, #5a1328) 0%, var(--header-end, #3d0d1c) 100%);
    color: white; gap: 12px;
  }
  .panel-header h2 { font-size: 17px; font-weight: 700; }
  .subtitle { font-size: 12px; opacity: 0.7; margin-top: 3px; }
  .close-btn {
    flex-shrink: 0; width: 32px; height: 32px; border-radius: 50%;
    border: none; background: rgba(255,255,255,0.15); color: white;
    display: flex; align-items: center; justify-content: center;
  }
  .close-btn:hover { background: rgba(255,255,255,0.25); }

  .body { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 0; }

  .center { display: flex; justify-content: center; padding: 40px; }
  .spinner {
    width: 28px; height: 28px;
    border: 2.5px solid var(--border);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .field-list { list-style: none; border: 1px solid var(--border); border-radius: 10px; overflow: hidden; margin-bottom: 12px; }
  .field-item { display: flex; align-items: center; justify-content: space-between; padding: 12px 14px; border-bottom: 1px solid var(--border); gap: 10px; }
  .field-item:last-child { border-bottom: none; }
  .empty-hint { padding: 20px; text-align: center; font-size: 13px; color: var(--text-muted); }

  .field-info { flex: 1; min-width: 0; }
  .field-labels { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 3px; }
  .label-de { font-size: 14px; font-weight: 600; color: var(--text); }
  .label-en { font-size: 13px; color: var(--text-muted); }
  .type-tag {
    font-size: 11px; background: rgba(72,15,37,0.08); color: var(--primary);
    padding: 1px 6px; border-radius: 8px; font-weight: 500;
  }
  .field-key { font-size: 11px; color: var(--text-muted); }

  .row-actions { display: flex; gap: 4px; flex-shrink: 0; }
  .icon-btn {
    width: 28px; height: 28px; border-radius: 6px; border: 1px solid var(--border);
    background: var(--surface-2); color: var(--text-muted);
    display: flex; align-items: center; justify-content: center; transition: all 0.12s;
  }
  .icon-btn:hover { border-color: var(--primary); color: var(--primary); }
  .icon-btn.danger:hover { border-color: #c0392b; color: #c0392b; }

  .edit-form, .create-form {
    background: var(--surface-2); border: 1px solid var(--border);
    border-radius: 10px; padding: 14px; display: flex; flex-direction: column; gap: 10px;
    width: 100%;
  }
  .edit-form { border-color: var(--primary); }
  .create-form { margin-top: 4px; }
  .edit-key { font-size: 12px; color: var(--text-muted); }
  .edit-key code { background: var(--surface); padding: 1px 5px; border-radius: 4px; font-size: 12px; }

  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .form-field { display: flex; flex-direction: column; gap: 4px; }
  .form-field label { font-size: 12px; font-weight: 600; color: var(--text-muted); }
  .form-field input, .form-field select {
    padding: 7px 9px; border: 1.5px solid var(--border); border-radius: 7px;
    font-size: 13px; background: var(--surface); color: var(--text); transition: border-color 0.15s;
  }
  .form-field input:focus, .form-field select:focus { outline: none; border-color: var(--primary); }

  .edit-actions, .create-actions { display: flex; gap: 8px; justify-content: flex-end; }
  .btn-cancel {
    padding: 7px 14px; border: 1.5px solid var(--border); border-radius: 8px;
    background: none; font-size: 13px; font-weight: 600; color: var(--text-muted);
  }
  .btn-cancel:hover { border-color: var(--primary); color: var(--primary); }
  .btn-save {
    padding: 7px 16px; border: none; border-radius: 8px;
    background: var(--primary); color: white; font-size: 13px; font-weight: 600;
  }
  .btn-save:hover:not(:disabled) { background: var(--primary-dark); }
  .btn-save:disabled { opacity: 0.45; cursor: default; }

  .btn-add {
    display: flex; align-items: center; gap: 6px; padding: 9px 14px;
    border: 1.5px dashed var(--border); border-radius: 8px;
    background: none; color: var(--text-muted); font-size: 13px; font-weight: 500;
    transition: border-color 0.15s, color 0.15s;
  }
  .btn-add:hover { border-color: var(--primary); color: var(--primary); }

  .err-msg { background: #fde8e8; color: #c0392b; padding: 7px 10px; border-radius: 6px; font-size: 12px; }
</style>
