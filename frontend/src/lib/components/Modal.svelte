<script>
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';

  export let variant = 'drawer'; // 'drawer' | 'center' | 'sheet'
  export let labelledby = undefined;
  export let closeOnBackdrop = true;
  export let closeOnEscape = true;
  export let maxWidth = undefined;

  const dispatch = createEventDispatcher();
  let panelEl;
  let previouslyFocused;

  function close() {
    dispatch('close');
  }

  function handleBackdropClick(e) {
    if (closeOnBackdrop && e.target === e.currentTarget) close();
  }

  function focusableIn(root) {
    return Array.from(root.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )).filter(el => !el.disabled && el.offsetParent !== null);
  }

  function handleKeydown(e) {
    if (closeOnEscape && e.key === 'Escape') {
      e.stopPropagation();
      close();
      return;
    }
    if (e.key === 'Tab') {
      const list = focusableIn(panelEl);
      if (!list.length) return;
      const first = list[0];
      const last = list[list.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  }

  onMount(() => {
    previouslyFocused = document.activeElement;
    document.body.style.overflow = 'hidden';
    const [first] = focusableIn(panelEl);
    (first || panelEl).focus();
  });

  onDestroy(() => {
    document.body.style.overflow = '';
    if (previouslyFocused?.focus) previouslyFocused.focus();
  });
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
<div
  class="kl-overlay"
  class:kl-overlay-center={variant === 'center'}
  class:kl-overlay-sheet={variant === 'sheet'}
  on:click={handleBackdropClick}
  on:keydown={handleKeydown}
>
  <div
    class="kl-panel kl-panel-{variant}"
    role="dialog"
    aria-modal="true"
    aria-labelledby={labelledby}
    tabindex="-1"
    style={maxWidth ? `max-width: ${maxWidth}` : undefined}
    bind:this={panelEl}
  >
    <slot />
  </div>
</div>

<style>
  .kl-overlay {
    position: fixed;
    inset: 0;
    background: rgba(26, 13, 17, 0.65);
    backdrop-filter: blur(5px);
    z-index: 150;
    display: flex;
    align-items: stretch;
    justify-content: flex-end;
  }
  .kl-overlay-center {
    align-items: center;
    justify-content: center;
    padding: 20px;
  }
  .kl-overlay-sheet {
    align-items: flex-end;
    justify-content: center;
  }
  .kl-panel {
    outline: none;
  }
  .kl-panel-drawer {
    background: var(--surface);
    width: 100%;
    max-width: 440px;
    display: flex;
    flex-direction: column;
    box-shadow: -8px 0 40px rgba(0, 0, 0, 0.25);
    animation: kl-slide-in 0.25s ease;
  }
  .kl-panel-center {
    background: var(--surface);
    border-radius: 16px;
    max-width: 560px;
    width: 100%;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    animation: kl-pop-in 0.2s ease;
    overflow: hidden;
  }
  @keyframes kl-slide-in {
    from { transform: translateX(40px); opacity: 0; }
    to   { transform: translateX(0); opacity: 1; }
  }
  @keyframes kl-pop-in {
    from { transform: scale(0.96); opacity: 0; }
    to   { transform: scale(1); opacity: 1; }
  }
  .kl-panel-sheet {
    background: var(--surface);
    border-radius: 20px 20px 0 0;
    width: 100%;
    max-width: 480px;
    box-shadow: 0 -8px 40px rgba(0, 0, 0, 0.3);
    animation: kl-slide-up 0.22s cubic-bezier(0.34, 1.4, 0.64, 1);
    padding-bottom: env(safe-area-inset-bottom, 0px);
  }
  @keyframes kl-slide-up {
    from { transform: translateY(40px); opacity: 0; }
    to   { transform: translateY(0);    opacity: 1; }
  }

  @media (max-width: 600px) {
    .kl-panel-center { max-height: 100vh; border-radius: 12px; }
  }
</style>
