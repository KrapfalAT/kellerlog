<script>
  import { createEventDispatcher } from 'svelte';
  import { t } from '$lib/stores/i18n.js';

  export let wine;
  export let readonly = false;
  export let inventoryMode = false;

  const dispatch = createEventDispatcher();

  let localQty = wine.quantity;
  $: localQty = wine.quantity;

  $: typeLabel = {
    red: $t('type_red'), white: $t('type_white'), rosé: $t('type_rose'),
    sparkling: $t('type_sparkling'), dessert: $t('type_dessert'), other: $t('type_other')
  };

  function stars(rating) {
    if (!rating) return '';
    return '★'.repeat(rating) + '☆'.repeat(5 - rating);
  }


  $: bodyMap = { 'Light-bodied': $t('body_light'), 'Medium-bodied': $t('body_medium'), 'Full-bodied': $t('body_full') };
  $: acidMap = { 'Low': $t('acidity_low'), 'Medium': $t('acidity_medium'), 'High': $t('acidity_high') };

  function handleIncrement(e) {
    e.stopPropagation();
    localQty++;
    dispatch('quantityChange', { id: wine.id, quantity: localQty });
  }

  function handleDecrement(e) {
    e.stopPropagation();
    if (localQty <= 0) return;
    localQty--;
    dispatch('quantityChange', { id: wine.id, quantity: localQty });
  }
</script>

<article class="card" class:clickable={readonly && !inventoryMode} class:inv-mode={inventoryMode} on:click={() => readonly && !inventoryMode && dispatch('select', wine)}>
  <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
  <div class="card-image" class:img-clickable={!inventoryMode} on:click|stopPropagation={() => !inventoryMode && dispatch('select', wine)}>
    {#if wine.image_url}
      <img src={wine.image_url} alt={wine.name} loading="lazy" />
    {:else}
      <div class="placeholder">
        <svg viewBox="0 0 64 100" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M24 4h16v20c0 8-4 14-4 22v44H28V46c0-8-4-14-4-22V4z" fill="currentColor" opacity=".15"/>
          <path d="M26 4h12v18c0 9-5 15-5 24v44H31V46c0-9-5-15-5-24V4z" fill="currentColor" opacity=".3"/>
          <rect x="22" y="2" width="20" height="6" rx="2" fill="currentColor" opacity=".4"/>
        </svg>
      </div>
    {/if}
    <span class="badge type-{wine.type}">{typeLabel[wine.type] || wine.type}</span>
  </div>

  <div class="card-body">
    <h3 class="wine-name" title={wine.name}>{wine.name}</h3>
    {#if wine.producer}
      <p class="producer">{wine.producer}</p>
    {/if}

    <div class="meta-row">
      {#if wine.vintage}
        <span class="meta-chip">{wine.vintage}</span>
      {/if}
      {#if wine.region}
        <span class="meta-chip">{wine.region}</span>
      {:else if wine.country}
        <span class="meta-chip">{wine.country}</span>
      {/if}
      {#if wine.grape}
        <span class="meta-chip">{wine.grape}</span>
      {/if}
    </div>

    {#if wine.rating}
      <div class="rating" title="{wine.rating}/5 Sterne">{stars(wine.rating)}</div>
    {/if}

    {#if wine.body || wine.acidity}
      <div class="wine-props">
        {#if wine.body}<span class="prop">{bodyMap[wine.body] || wine.body}</span>{/if}
        {#if wine.acidity}<span class="prop">{acidMap[wine.acidity] || wine.acidity}</span>{/if}
      </div>
    {/if}

    {#if wine.pairings}
      <div class="pairings" title="Speisenempfehlung">🍽 {wine.pairings}</div>
    {/if}

    {#if inventoryMode}
      <div class="inv-strip">
        <button class="inv-btn inv-minus" on:click={handleDecrement}>−</button>
        <span class="inv-qty" class:zero={localQty === 0}>{localQty}</span>
        <button class="inv-btn inv-plus" on:click={handleIncrement}>+</button>
      </div>
    {:else}
      <div class="card-footer">
        {#if !readonly}
          <span class="quantity">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 2h6v3.5c2 1.2 3 3.2 3 5V19a2 2 0 01-2 2H8a2 2 0 01-2-2v-8.5c0-1.8 1-3.8 3-5V2z"/>
              <line x1="6" y1="12" x2="18" y2="12"/>
            </svg>
            {wine.quantity}×
          </span>
        {/if}
        {#if wine.price}
          <span class="price">{wine.price.toFixed(2)} €</span>
        {/if}
        {#if wine.alcohol}
          <span class="alcohol">{wine.alcohol}%</span>
        {/if}
      </div>
    {/if}
  </div>

  {#if !readonly}
  <div class="card-actions">
    <button class="btn-icon" title="Bearbeiten" on:click={() => dispatch('edit', wine)}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
        <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
      </svg>
    </button>
    <button class="btn-icon danger" title="Löschen" on:click={() => dispatch('delete', wine.id)}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="3 6 5 6 21 6"/>
        <path d="M19 6l-1 14H6L5 6"/>
        <path d="M10 11v6M14 11v6"/>
        <path d="M9 6V4h6v2"/>
      </svg>
    </button>
  </div>
  {/if}
</article>

<style>
  .card {
    background: var(--surface);
    border-radius: 12px;
    box-shadow: var(--shadow);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    transition: transform 0.2s, box-shadow 0.2s;
    position: relative;
  }
  .card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-lg);
  }
  .card.clickable {
    cursor: pointer;
  }
  .card.clickable:hover {
    transform: translateY(-4px);
  }
  .card:hover .card-actions {
    opacity: 1;
  }

  .card-image {
    height: 180px;
    background: var(--surface-2);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
  }
  .card-image.img-clickable { cursor: pointer; }
  .card-image.img-clickable:hover img,
  .card-image.img-clickable:hover .placeholder { opacity: 0.85; }
  .card-image img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    padding: 8px;
  }
  .placeholder {
    color: var(--primary);
    width: 60px;
    height: 60px;
    opacity: 0.4;
  }

  .badge {
    position: absolute;
    top: 8px;
    right: 8px;
    padding: 3px 8px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    color: white;
    letter-spacing: 0.3px;
  }
  .type-red    { background: var(--red); }
  .type-white  { background: var(--white-wine); }
  .type-rosé   { background: var(--rose); }
  .type-sparkling { background: var(--sparkling); }
  .type-dessert { background: var(--dessert); }
  .type-other  { background: var(--other); }

  .card-body {
    padding: 14px;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .wine-name {
    font-size: 15px;
    font-weight: 700;
    color: var(--text);
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    line-height: 1.3;
  }
  .producer {
    font-size: 13px;
    color: var(--text-muted);
  }
  .meta-row {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-top: 2px;
  }
  .meta-chip {
    font-size: 11px;
    background: var(--surface-2);
    color: var(--text-muted);
    padding: 2px 7px;
    border-radius: 10px;
    border: 1px solid var(--border);
  }
  .rating {
    font-size: 14px;
    color: var(--accent);
    letter-spacing: 1px;
  }
  .wine-props {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }
  .prop {
    font-size: 10px;
    background: rgba(123, 29, 63, 0.08);
    color: var(--primary);
    padding: 2px 6px;
    border-radius: 8px;
    font-weight: 500;
  }
  .pairings {
    font-size: 11px;
    color: var(--text-muted);
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }
  .card-footer {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: auto;
    padding-top: 8px;
    border-top: 1px solid var(--border);
  }
  .quantity {
    display: flex;
    align-items: center;
    gap: 3px;
    font-size: 13px;
    font-weight: 600;
    color: var(--primary);
  }
  .price, .alcohol {
    font-size: 12px;
    color: var(--text-muted);
  }

  .card-actions {
    position: absolute;
    top: 8px;
    left: 8px;
    display: flex;
    gap: 4px;
    opacity: 0;
    transition: opacity 0.2s;
  }
  .btn-icon {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    border: none;
    background: rgba(255,255,255,0.95);
    color: var(--text-muted);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.15);
    transition: color 0.15s, background 0.15s;
  }
  .btn-icon:hover { color: var(--primary); background: white; }
  .btn-icon.danger:hover { color: #c0392b; }

  .card.inv-mode { cursor: default; }
  .card.inv-mode:hover { transform: none; box-shadow: var(--shadow); }

  .inv-strip {
    display: flex;
    align-items: stretch;
    border-top: 2px solid var(--primary);
    margin-top: auto;
  }
  .inv-btn {
    flex: 1;
    font-size: 30px;
    font-weight: 300;
    line-height: 1;
    border: none;
    background: none;
    padding: 10px 0;
    transition: background 0.12s, color 0.12s;
    cursor: pointer;
  }
  .inv-minus { color: #c0392b; }
  .inv-minus:hover { background: rgba(192, 57, 43, 0.08); }
  .inv-plus { color: var(--primary); }
  .inv-plus:hover { background: rgba(123, 29, 63, 0.08); }
  .inv-qty {
    min-width: 56px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 26px;
    font-weight: 800;
    color: var(--text);
    border-left: 1px solid var(--border);
    border-right: 1px solid var(--border);
    padding: 0 8px;
  }
  .inv-qty.zero { color: var(--text-muted); }
</style>
