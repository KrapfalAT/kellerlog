<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import { getUsers, createUser, updateUser, deleteUser } from '$lib/api.js';
  import { auth } from '$lib/stores/auth.js';
  import { t } from '$lib/stores/i18n.js';
  import Modal from './Modal.svelte';

  const dispatch = createEventDispatcher();

  let users = [];
  let loading = true;
  let error = '';

  let showCreate = false;
  let newUsername = '';
  let newPassword = '';
  let newRole = 'viewer';
  let creating = false;
  let createError = '';

  let editingId = null;
  let editPassword = '';
  let editRole = '';
  let saving = false;

  onMount(async () => {
    await load();
  });

  async function load() {
    loading = true;
    try {
      users = await getUsers();
    } catch {
      error = $t('users_error_load');
    } finally {
      loading = false;
    }
  }

  async function handleCreate() {
    if (!newUsername.trim() || !newPassword) return;
    creating = true;
    createError = '';
    try {
      await createUser({ username: newUsername.trim(), password: newPassword, role: newRole });
      newUsername = '';
      newPassword = '';
      newRole = 'viewer';
      showCreate = false;
      await load();
    } catch (err) {
      createError = err.message;
    } finally {
      creating = false;
    }
  }

  function startEdit(user) {
    editingId = user.id;
    editPassword = '';
    editRole = user.role;
  }

  async function saveEdit(user) {
    saving = true;
    try {
      const data = {};
      if (editPassword) data.password = editPassword;
      if (editRole !== user.role) data.role = editRole;
      if (Object.keys(data).length > 0) {
        await updateUser(user.id, data);
        await load();
      }
      editingId = null;
    } catch (err) {
      error = err.message;
    } finally {
      saving = false;
    }
  }

  async function handleDelete(user) {
    if (!confirm(`${$t('users_title')}: „${user.username}" löschen?`)) return;
    try {
      await deleteUser(user.id);
      await load();
    } catch (err) {
      error = err.message;
    }
  }

  $: roleLabel = { admin: 'Admin', viewer: 'Viewer' };
</script>

<Modal variant="drawer" labelledby="users-title" on:close={() => dispatch('close')}>
  <div class="panel">
    <div class="panel-header">
      <div>
        <h2 id="users-title">{$t('users_title')}</h2>
        <p class="subtitle">{$t('users_subtitle')}</p>
      </div>
      <button class="close-btn" on:click={() => dispatch('close')} aria-label={$t('users_cancel')}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <div class="body">
      {#if error}
        <div class="err-banner">{error}</div>
      {/if}

      {#if loading}
        <div class="center"><div class="loader"></div></div>
      {:else}
        <ul class="user-list">
          {#each users as user (user.id)}
            <li class="user-row">
              {#if editingId === user.id}
                <div class="edit-form">
                  <div class="edit-top">
                    <span class="username">{user.username}</span>
                    <span class="self-badge" class:visible={user.id === $auth?.id}>{$t('users_you')}</span>
                  </div>
                  <div class="edit-fields">
                    <div class="edit-field">
                      <label for="edit-password-{user.id}">{$t('users_new_password')}</label>
                      <input id="edit-password-{user.id}" type="password" bind:value={editPassword} placeholder={$t('users_password_hint')} />
                    </div>
                    <div class="edit-field">
                      <label for="edit-role-{user.id}">{$t('users_role')}</label>
                      <select id="edit-role-{user.id}" bind:value={editRole}>
                        <option value="admin">Admin</option>
                        <option value="viewer">Viewer</option>
                      </select>
                    </div>
                  </div>
                  <div class="edit-actions">
                    <button class="btn-secondary" on:click={() => editingId = null}>{$t('users_cancel')}</button>
                    <button class="btn-primary" on:click={() => saveEdit(user)} disabled={saving}>
                      {saving ? $t('users_saving') : $t('users_save')}
                    </button>
                  </div>
                </div>
              {:else}
                <div class="user-info">
                  <div class="user-top">
                    <span class="username">{user.username}</span>
                    {#if user.id === $auth?.id}
                      <span class="self-badge visible">{$t('users_you')}</span>
                    {/if}
                  </div>
                  <span class="role-badge role-{user.role}">{roleLabel[user.role]}</span>
                </div>
                <div class="row-actions">
                  <button class="icon-btn" title="Bearbeiten" aria-label="Bearbeiten" on:click={() => startEdit(user)}>
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>
                  {#if user.id !== $auth?.id}
                    <button class="icon-btn danger" title="Löschen" aria-label="Löschen" on:click={() => handleDelete(user)}>
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6l-1 14H6L5 6"/>
                        <path d="M10 11v6M14 11v6M9 6V4h6v2"/>
                      </svg>
                    </button>
                  {/if}
                </div>
              {/if}
            </li>
          {/each}
        </ul>

        {#if showCreate}
          <div class="create-form">
            <h3>{$t('users_new_title')}</h3>
            {#if createError}<div class="err-inline">{createError}</div>{/if}
            <div class="create-fields">
              <div class="edit-field">
                <label for="new-username">{$t('users_username')}</label>
                <input id="new-username" type="text" bind:value={newUsername} placeholder="username" />
              </div>
              <div class="edit-field">
                <label for="new-user-password">{$t('users_password')}</label>
                <input id="new-user-password" type="password" bind:value={newPassword} placeholder="••••••••" />
              </div>
              <div class="edit-field">
                <label for="new-user-role">{$t('users_role')}</label>
                <select id="new-user-role" bind:value={newRole}>
                  <option value="viewer">Viewer</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
            </div>
            <div class="edit-actions">
              <button class="btn-secondary" on:click={() => { showCreate = false; createError = ''; }}>{$t('users_cancel')}</button>
              <button class="btn-primary" on:click={handleCreate} disabled={creating || !newUsername || !newPassword}>
                {creating ? $t('users_creating') : $t('users_create')}
              </button>
            </div>
          </div>
        {:else}
          <button class="btn-add-user" on:click={() => showCreate = true}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            {$t('users_add_btn')}
          </button>
        {/if}
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
    padding: 8px 0 16px;
  }

  .err-banner {
    margin: 12px 16px;
    padding: 10px 14px;
    background: rgba(192,57,43,0.1);
    border: 1px solid rgba(192,57,43,0.3);
    border-radius: 10px;
    font-size: 13px;
    color: var(--danger);
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

  .user-list { list-style: none; }

  .user-row {
    border-bottom: 1px solid var(--border);
    padding: 12px 16px;
  }

  .user-info {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .user-top { display: flex; align-items: center; gap: 6px; }
  .username { font-size: 14px; font-weight: 600; color: var(--text); }

  .self-badge {
    font-size: 10px;
    font-weight: 700;
    background: var(--primary);
    color: white;
    padding: 1px 6px;
    border-radius: 8px;
    display: none;
  }
  .self-badge.visible { display: inline; }

  .role-badge {
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 8px;
  }
  .role-admin { background: rgba(123,29,63,0.12); color: var(--primary); border: 1px solid rgba(123,29,63,0.25); }
  .role-viewer { background: var(--surface-2); color: var(--text-muted); border: 1px solid var(--border); }

  .row-actions { display: flex; gap: 4px; }

  .icon-btn {
    width: 30px; height: 30px;
    border-radius: 50%; border: none;
    background: none; color: var(--text-muted);
    display: flex; align-items: center; justify-content: center;
    transition: color 0.15s, background 0.15s;
  }
  .icon-btn:hover { color: var(--primary); background: rgba(123,29,63,0.08); }
  .icon-btn.danger:hover { color: var(--danger); background: rgba(192,57,43,0.08); }

  .edit-form, .create-form {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .create-form {
    margin: 12px 16px;
    padding: 16px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 12px;
  }

  .create-form h3 { font-size: 13px; font-weight: 700; color: var(--text); }

  .edit-top { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }

  .edit-fields, .create-fields {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .edit-field { display: flex; flex-direction: column; gap: 4px; }
  .edit-field label {
    font-size: 10px; font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.4px;
  }
  .edit-field input, .edit-field select {
    padding: 7px 9px;
    border: 1.5px solid var(--border);
    border-radius: 8px;
    background: var(--surface);
    color: var(--text);
    font-size: 13px;
  }
  .edit-field input:focus, .edit-field select:focus {
    outline: none; border-color: var(--primary);
  }

  .edit-actions {
    display: flex; gap: 8px;
  }
  .edit-actions .btn-secondary { flex: 1; }
  .edit-actions .btn-primary { flex: 2; }

  .err-inline {
    font-size: 12px; color: var(--danger);
    background: rgba(192,57,43,0.08);
    border-radius: 6px; padding: 6px 10px;
  }

  .btn-add-user {
    margin: 12px 16px 0;
    padding: 10px 16px;
    border: 1.5px dashed var(--border);
    border-radius: 10px;
    background: none;
    color: var(--text-muted);
    font-size: 13px; font-weight: 600;
    display: flex; align-items: center; gap: 8px;
    width: calc(100% - 32px);
    transition: border-color 0.15s, color 0.15s;
  }
  .btn-add-user:hover { border-color: var(--primary); color: var(--primary); }
</style>
