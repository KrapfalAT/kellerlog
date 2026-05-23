<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { auth, isLoggedIn } from '$lib/stores/auth.js';
  import { login } from '$lib/api.js';

  let username = '';
  let password = '';
  let loading = false;
  let error = '';

  onMount(() => {
    if ($isLoggedIn) goto('/');
  });

  async function handleSubmit(e) {
    e.preventDefault();
    if (!username.trim() || !password) return;
    loading = true;
    error = '';
    try {
      const data = await login(username.trim(), password);
      auth.login(data);
      goto('/');
    } catch (err) {
      error = err.message === 'INVALID_CREDENTIALS'
        ? 'Benutzername oder Passwort falsch'
        : 'Anmeldung fehlgeschlagen';
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head><title>Anmelden — KellerLog</title></svelte:head>

<div class="page">
  <div class="card">
    <div class="logo-area">
      <img src="/logo/kellerlog-icon-192.png" alt="KellerLog" class="logo" />
      <h1>KellerLog</h1>
    </div>

    <form on:submit={handleSubmit} class="form">
      {#if error}
        <div class="error-msg">{error}</div>
      {/if}

      <div class="field">
        <label for="username">Benutzername</label>
        <input
          id="username"
          type="text"
          bind:value={username}
          autocomplete="username"
          autofocus
          disabled={loading}
        />
      </div>

      <div class="field">
        <label for="password">Passwort</label>
        <input
          id="password"
          type="password"
          bind:value={password}
          autocomplete="current-password"
          disabled={loading}
        />
      </div>

      <button type="submit" class="btn-login" disabled={loading || !username || !password}>
        {#if loading}
          <span class="spinner"></span>
          Anmelden…
        {:else}
          Anmelden
        {/if}
      </button>
    </form>
  </div>
</div>

<style>
  .page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg);
    padding: 16px;
  }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 40px 32px 32px;
    width: 100%;
    max-width: 360px;
    box-shadow: var(--shadow-lg);
  }

  .logo-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    margin-bottom: 32px;
  }

  .logo {
    width: 64px;
    height: 64px;
    border-radius: 16px;
  }

  h1 {
    font-size: 22px;
    font-weight: 800;
    color: var(--text);
    letter-spacing: -0.5px;
  }

  .form {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .field label {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .field input {
    padding: 10px 12px;
    border: 1.5px solid var(--border);
    border-radius: 10px;
    background: var(--surface-2);
    color: var(--text);
    font-size: 15px;
    transition: border-color 0.15s;
  }

  .field input:focus {
    outline: none;
    border-color: var(--primary);
  }

  .field input:disabled {
    opacity: 0.6;
  }

  .error-msg {
    background: rgba(192, 57, 43, 0.1);
    border: 1px solid rgba(192, 57, 43, 0.3);
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 13px;
    color: #c0392b;
  }

  .btn-login {
    margin-top: 4px;
    padding: 12px;
    background: var(--primary);
    color: white;
    border: none;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 700;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    transition: background 0.15s;
  }

  .btn-login:hover:not(:disabled) { background: var(--primary-dark); }
  .btn-login:disabled { opacity: 0.55; cursor: default; }

  .spinner {
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
