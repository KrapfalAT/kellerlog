<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import { getLibrary, deleteLibraryEntry } from '$lib/api.js';

  const dispatch = createEventDispatcher();

  let entries = [];
  let loading = true;
  let filterText = '';

  const typeLabel = {
    red: 'Rotwein', white: 'Weißwein', rosé: 'Rosé',
    sparkling: 'Sekt', dessert: 'Dessertwein', other: 'Sonstiger'
  };

  $: filtered = entries.filter(e => {
    if (!filterText.trim()) return true;
    const q = filterText.toLowerCase();
    return (
      e.name.toLowerCase().includes(q) ||
      (e.producer || '').toLowerCase().includes(q) ||
      (e.country || '').toLowerCase().includes(q) ||
      (e.region || '').toLowerCase().includes(q)
    );
  });

  onMount(async () => {
    try {
      entries = await getLibrary();
    } finally {
      loading = false;
    }
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  });

  async function handleDelete(id) {
    if (!confirm('Eintrag aus Weinbibliothek entfernen?')) return;
    await deleteLibraryEntry(id);
    entries = entries.filter(e => e.id !== id);
  }

  function handleBackdrop(e) {
    if (e.target === e.currentTarget) dispatch('close');
  }

  function stars(r) {
    if (!r) return '';
    return '★'.repeat(r) + '☆'.repeat(5 - r);
  }
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
<div class="overlay" on:click={handleBackdrop}>
  <div class="panel">
    <div class="panel-header">
      <div>
        <h2>Weinbibliothek</h2>
        <p class="subtitle">Gespeicherte Weindaten — beim Suchen bevorzugt angezeigt</p>
      </div>
      <button class="close-btn" on:click={() => dispatch('close')} aria-label="Schließen">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <div class="search-bar">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input
        type="search"
        placeholder="In Bibliothek suchen..."
        bind:value={filterText}
        class="search-input"
      />
    </div>

    <div class="list-area">
      {#if loading}
        <div class="center"><div class="loader"></div></div>
      {:else if filtered.length === 0}
        <div class="empty">
          {#if entries.length === 0}
            <p>Noch keine Weine in der Bibliothek.</p>
            <p class="hint">Weindaten werden automatisch gespeichert, wenn du einen Wein hinzufügst oder bearbeitest.</p>
          {:else}
            <p>Kein Treffer für „{filterText}"</p>
          {/if}
        </div>
      {:else}
        <p class="count">{filtered.length} Eintra{filtered.length !== 1 ? 'ge' : 'g'}</p>
        <ul class="entries">
          {#each filtered as entry (entry.id)}
            <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
            <li class="entry">
              <div class="entry-thumb">
                {#if entry.image_url}
                  <img src={entry.image_url} alt={entry.name} />
                {:else}
                  <div class="thumb-placeholder">🍷</div>
                {/if}
              </div>
              <div class="entry-info">
                <div class="entry-top">
                  <span class="entry-name">{entry.name}</span>
                  <span class="type-badge type-{entry.type}">{typeLabel[entry.type] || entry.type}</span>
                  {#if entry.quantity > 0}
                    <span class="qty-badge">{entry.quantity}×</span>
                  {/if}
                </div>
                {#if entry.producer}
                  <span class="entry-producer">{entry.producer}</span>
                {/if}
                <div class="entry-meta">
                  {#if entry.vintage}<span class="meta-chip year">{entry.vintage}</span>{/if}
                  {#if entry.region}<span class="meta-chip">{entry.region}</span>{/if}
                  {#if entry.country}<span class="meta-chip">{entry.country}</span>{/if}
                  {#if entry.rating}<span class="meta-stars">{stars(entry.rating)}</span>{/if}
                </div>
              </div>
              <button
                class="add-btn"
                title="Zum Keller hinzufügen"
                on:click|stopPropagation={() => dispatch('addToInventory', entry)}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
              </button>
              <button
                class="icon-action-btn"
                title="Duplizieren"
                on:click|stopPropagation={() => dispatch('duplicateEntry', entry)}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
                </svg>
              </button>
              <button
                class="icon-action-btn"
                title="Bearbeiten"
                on:click|stopPropagation={() => dispatch('editEntry', entry)}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </button>
              <button
                class="delete-btn"
                title="Aus Bibliothek entfernen"
                on:click|stopPropagation={() => handleDelete(entry.id)}
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6l-1 14H6L5 6"/>
                  <path d="M10 11v6M14 11v6"/>
                  <path d="M9 6V4h6v2"/>
                </svg>
              </button>
            </li>
          {/each}
        </ul>
      {/if}
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
    max-width: 520px;
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
  }

  .panel-header h2 {
    font-size: 18px;
    font-weight: 700;
  }

  .subtitle {
    font-size: 12px;
    opacity: 0.7;
    margin-top: 3px;
    line-height: 1.4;
  }

  .close-btn {
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: none;
    background: rgba(255,255,255,0.15);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s;
  }
  .close-btn:hover { background: rgba(255,255,255,0.25); }

  .search-bar {
    padding: 10px 16px;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 1px solid var(--border);
    background: var(--surface-2);
  }
  .search-bar svg { color: var(--text-muted); flex-shrink: 0; }
  .search-input {
    flex: 1;
    border: none;
    background: none;
    font-size: 14px;
    outline: none;
    color: var(--text);
  }
  .search-input::placeholder { color: var(--text-muted); }

  .list-area {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;
  }

  .count {
    font-size: 11px;
    color: var(--text-muted);
    padding: 4px 16px 8px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .center {
    display: flex;
    justify-content: center;
    padding: 60px 20px;
  }
  .loader {
    width: 36px;
    height: 36px;
    border: 3px solid var(--border);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .empty {
    padding: 60px 24px;
    text-align: center;
    color: var(--text-muted);
    font-size: 14px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    align-items: center;
  }
  .hint {
    font-size: 12px;
    line-height: 1.5;
    max-width: 320px;
  }

  .entries { list-style: none; }

  .entry {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 16px;
    border-bottom: 1px solid var(--border);
  }
  .entry:last-child { border-bottom: none; }

  .entry-thumb {
    width: 44px;
    height: 52px;
    border-radius: 6px;
    overflow: hidden;
    background: var(--surface-2);
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid var(--border);
  }
  .entry-thumb img { width: 100%; height: 100%; object-fit: contain; }
  .thumb-placeholder { font-size: 22px; }

  .entry-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }
  .entry-top {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
  }
  .entry-name {
    font-size: 14px;
    font-weight: 600;
    color: var(--text);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .entry-producer { font-size: 12px; color: var(--text-muted); }

  .type-badge {
    font-size: 10px;
    font-weight: 600;
    color: white;
    padding: 2px 7px;
    border-radius: 10px;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .type-red      { background: var(--red); }
  .type-white    { background: var(--white-wine); }
  .type-rosé     { background: var(--rose); }
  .type-sparkling{ background: var(--sparkling); }
  .type-dessert  { background: var(--dessert); }
  .type-other    { background: var(--other); }

  .entry-meta {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
    align-items: center;
  }
  .meta-chip {
    font-size: 11px;
    background: var(--surface-2);
    color: var(--text-muted);
    padding: 1px 6px;
    border-radius: 8px;
    border: 1px solid var(--border);
  }
  .meta-chip.year {
    background: rgba(123, 29, 63, 0.07);
    color: var(--primary);
    border-color: rgba(123, 29, 63, 0.15);
    font-weight: 600;
  }
  .meta-stars { font-size: 11px; color: var(--accent); }

  .qty-badge {
    font-size: 10px;
    font-weight: 700;
    background: rgba(44, 122, 75, 0.12);
    color: #2c7a4b;
    border: 1px solid rgba(44, 122, 75, 0.3);
    padding: 1px 6px;
    border-radius: 10px;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .add-btn {
    flex-shrink: 0;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    border: 1.5px solid rgba(44, 122, 75, 0.35);
    background: rgba(44, 122, 75, 0.07);
    color: #2c7a4b;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s, border-color 0.15s;
  }
  .add-btn:hover {
    background: rgba(44, 122, 75, 0.16);
    border-color: rgba(44, 122, 75, 0.6);
  }

  .icon-action-btn {
    flex-shrink: 0;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    border: none;
    background: none;
    color: var(--text-muted);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: color 0.15s, background 0.15s;
  }
  .icon-action-btn:hover {
    color: var(--primary);
    background: rgba(123, 29, 63, 0.08);
  }

  .delete-btn {
    flex-shrink: 0;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    border: none;
    background: none;
    color: var(--text-muted);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: color 0.15s, background 0.15s;
  }
  .delete-btn:hover {
    color: #c0392b;
    background: rgba(192, 57, 43, 0.08);
  }
</style>
