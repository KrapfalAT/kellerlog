<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import { t, lang } from '$lib/stores/i18n.js';

  export let wine;
  export let editable = false;
  export let customFields = [];

  const dispatch = createEventDispatcher();

  $: typeLabel = {
    red: $t('type_red'), white: $t('type_white'), rosé: $t('type_rose'),
    sparkling: $t('type_sparkling'), dessert: $t('type_dessert'), other: $t('type_other')
  };
  $: bodyMap = { 'Light-bodied': $t('body_light'), 'Medium-bodied': $t('body_medium'), 'Full-bodied': $t('body_full') };
  $: acidMap = { 'Low': $t('acidity_low'), 'Medium': $t('acidity_medium'), 'High': $t('acidity_high') };

  function stars(r) {
    if (!r) return '';
    return '★'.repeat(r) + '☆'.repeat(5 - r);
  }

  function handleBackdrop(e) {
    if (e.target === e.currentTarget) dispatch('close');
  }

  onMount(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  });
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
<div class="overlay" on:click={handleBackdrop}>
  <div class="panel" role="dialog" aria-modal="true">

    <!-- Image -->
    <div class="image-side">
      {#if wine.image_url}
        <img src={wine.image_url} alt={wine.name} class="wine-img" />
      {:else}
        <div class="img-placeholder">
          <svg viewBox="0 0 64 100" fill="none">
            <path d="M24 4h16v20c0 8-4 14-4 22v44H28V46c0-8-4-14-4-22V4z" fill="currentColor" opacity=".15"/>
            <path d="M26 4h12v18c0 9-5 15-5 24v44H31V46c0-9-5-15-5-24V4z" fill="currentColor" opacity=".3"/>
            <rect x="22" y="2" width="20" height="6" rx="2" fill="currentColor" opacity=".4"/>
          </svg>
        </div>
      {/if}
      <span class="type-badge type-{wine.type}">{typeLabel[wine.type] || wine.type}</span>
      {#if wine.by_glass}
        <span class="glass-badge">{$t('kiosk_by_glass')}</span>
      {/if}
    </div>

    <!-- Details -->
    <div class="detail-side">
      <div class="detail-header-btns">
        {#if editable}
          <button class="edit-btn" on:click={() => dispatch('edit', wine)} title="Bearbeiten">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </button>
        {/if}
        <button class="close-btn" on:click={() => dispatch('close')} aria-label="Schließen">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <div class="detail-scroll">
        <h2 class="wine-name">{wine.name}</h2>

        {#if wine.producer}
          <p class="producer">{wine.producer}</p>
        {/if}

        {#if wine.rating}
          <div class="stars">{stars(wine.rating)}</div>
        {/if}

        <div class="chips">
          {#if wine.vintage}
            <span class="chip chip-year">{wine.vintage}</span>
          {/if}
          {#if wine.region}
            <span class="chip">{wine.region}</span>
          {/if}
          {#if wine.country}
            <span class="chip">{wine.country}</span>
          {/if}
          {#if wine.grape}
            <span class="chip">{wine.grape}</span>
          {/if}
        </div>

        {#if wine.body || wine.acidity || wine.alcohol}
          <div class="props">
            {#if wine.body}
              <div class="prop-item">
                <span class="prop-label">{$t('detail_body')}</span>
                <span class="prop-val">{bodyMap[wine.body] || wine.body}</span>
              </div>
            {/if}
            {#if wine.acidity}
              <div class="prop-item">
                <span class="prop-label">{$t('detail_acidity')}</span>
                <span class="prop-val">{acidMap[wine.acidity] || wine.acidity}</span>
              </div>
            {/if}
            {#if wine.alcohol}
              <div class="prop-item">
                <span class="prop-label">{$t('detail_alcohol')}</span>
                <span class="prop-val">{wine.alcohol}%</span>
              </div>
            {/if}
          </div>
        {/if}

        {#if wine.description}
          <p class="description">{wine.description}</p>
        {/if}

        {#if wine.pairings}
          <div class="pairings">
            <span class="prop-label">{$t('detail_pairings')}</span>
            <p>{wine.pairings}</p>
          </div>
        {/if}

        {#if wine.notes}
          <div class="notes">
            <span class="prop-label">{$t('detail_notes')}</span>
            <p>{wine.notes}</p>
          </div>
        {/if}

        {#if customFields.length > 0 && wine.custom_values}
          {@const visibleFields = customFields.filter(cf => wine.custom_values[cf.key])}
          {#if visibleFields.length > 0}
            <div class="custom-fields">
              <span class="prop-label">{$t('custom_fields_section')}</span>
              <div class="custom-grid">
                {#each visibleFields as cf (cf.key)}
                  <div class="custom-item">
                    <span class="custom-label">{$lang === 'de' ? cf.label_de : (cf.label_en || cf.label_de)}</span>
                    <span class="custom-val">{wine.custom_values[cf.key]}</span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}
        {/if}

        <div class="footer-row">
          {#if wine.price}
            <span class="price">{wine.price.toFixed(2)} € <span class="price-label">{$t('detail_per_bottle')}</span></span>
          {/if}
          {#if wine.by_glass && wine.price_per_glass}
            <span class="price glass-price">
              {wine.price_per_glass.toFixed(2)} € <span class="price-label">{$t('detail_per_glass')}</span>
            </span>
          {/if}
        </div>
      </div>
    </div>

  </div>
</div>

<style>
  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(26, 13, 17, 0.7);
    backdrop-filter: blur(6px);
    z-index: 200;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
  }

  .panel {
    background: var(--surface);
    border-radius: 20px;
    width: 100%;
    max-width: 780px;
    max-height: 92vh;
    display: flex;
    box-shadow: 0 24px 64px rgba(0,0,0,0.35);
    overflow: hidden;
    animation: popIn 0.22s cubic-bezier(0.34, 1.4, 0.64, 1);
  }

  @keyframes popIn {
    from { transform: scale(0.92); opacity: 0; }
    to   { transform: scale(1);    opacity: 1; }
  }

  /* ── Image side ── */
  .image-side {
    width: 42%;
    flex-shrink: 0;
    background: var(--surface-2);
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .wine-img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    padding: 24px;
  }

  .img-placeholder {
    color: var(--primary);
    width: 100px;
    height: 100px;
    opacity: 0.25;
  }

  .type-badge {
    position: absolute;
    bottom: 16px;
    left: 16px;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    color: white;
    letter-spacing: 0.3px;
  }
  .type-red      { background: var(--red); }
  .type-white    { background: var(--white-wine); }
  .type-rosé     { background: var(--rose); }
  .type-sparkling{ background: var(--sparkling); }
  .type-dessert  { background: var(--dessert); }
  .type-other    { background: var(--other); }

  .glass-badge {
    position: absolute;
    bottom: 16px;
    right: 16px;
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    color: white;
    background: rgba(20, 20, 20, 0.65);
    backdrop-filter: blur(4px);
  }

  /* ── Detail side ── */
  .detail-side {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    position: relative;
  }

  .detail-header-btns {
    position: absolute;
    top: 14px;
    right: 14px;
    display: flex;
    gap: 6px;
    z-index: 1;
  }
  .close-btn, .edit-btn {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: none;
    background: var(--surface-2);
    color: var(--text-muted);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s, color 0.15s;
  }
  .close-btn:hover { background: var(--border); color: var(--text); }
  .edit-btn:hover { background: var(--primary); color: white; }

  .detail-scroll {
    padding: 28px 28px 24px;
    overflow-y: auto;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .wine-name {
    font-size: 22px;
    font-weight: 800;
    color: var(--text);
    line-height: 1.25;
    padding-right: 36px;
  }

  .producer {
    font-size: 14px;
    color: var(--text-muted);
    margin-top: -8px;
  }

  .stars {
    font-size: 20px;
    color: var(--accent);
    letter-spacing: 2px;
  }

  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }
  .chip {
    font-size: 12px;
    background: var(--surface-2);
    color: var(--text-muted);
    padding: 3px 10px;
    border-radius: 12px;
    border: 1px solid var(--border);
  }
  .chip-year {
    background: rgba(123, 29, 63, 0.08);
    color: var(--primary);
    border-color: rgba(123, 29, 63, 0.2);
    font-weight: 600;
  }

  .props {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
  }
  .prop-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .prop-label {
    font-size: 11px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .prop-val {
    font-size: 14px;
    font-weight: 600;
    color: var(--text);
  }

  .description {
    font-size: 14px;
    color: var(--text-muted);
    line-height: 1.6;
    border-left: 3px solid var(--border);
    padding-left: 12px;
  }

  .pairings, .notes {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .pairings p, .notes p {
    font-size: 13px;
    color: var(--text-muted);
    line-height: 1.5;
  }

  .custom-fields { display: flex; flex-direction: column; gap: 8px; }
  .custom-grid { display: flex; flex-direction: column; gap: 6px; }
  .custom-item { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
  .custom-label { font-size: 13px; color: var(--text-muted); }
  .custom-val { font-size: 13px; font-weight: 600; color: var(--text); text-align: right; }

  .footer-row {
    display: flex;
    align-items: center;
    gap: 16px;
    padding-top: 8px;
    border-top: 1px solid var(--border);
    margin-top: auto;
  }
  .price {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 20px;
    font-weight: 700;
    color: var(--primary);
  }
  .price-label {
    font-size: 12px;
    font-weight: 500;
    opacity: 0.7;
  }
  .glass-price {
    font-size: 18px;
  }
  .qty {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 13px;
    color: var(--text-muted);
  }

  /* Mobile: stack vertically */
  @media (max-width: 600px) {
    .panel {
      flex-direction: column;
      max-height: 95vh;
    }
    .image-side {
      width: 100%;
      height: 240px;
    }
    .detail-scroll {
      padding: 20px;
    }
  }
</style>
