<script>
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();

  let videoEl;
  let stream = null;
  let animFrame = null;
  let detector = null;
  let errorMsg = '';
  let detected = false;

  onMount(async () => {
    if (!('BarcodeDetector' in window)) {
      errorMsg = 'Barcode-Scanner wird von diesem Browser nicht unterstützt. Bitte Barcode manuell eingeben.';
      return;
    }
    try {
      detector = new window.BarcodeDetector({
        formats: ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'code_39', 'qr_code'],
      });
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
      });
      videoEl.srcObject = stream;
      await videoEl.play();
      scan();
    } catch (e) {
      errorMsg = 'Kamera konnte nicht gestartet werden. Bitte Kamerazugriff erlauben.';
    }
  });

  async function scan() {
    if (detected) return;
    if (!videoEl || videoEl.readyState < 2) {
      animFrame = requestAnimationFrame(scan);
      return;
    }
    try {
      const barcodes = await detector.detect(videoEl);
      if (barcodes.length > 0 && !detected) {
        detected = true;
        stopCamera();
        dispatch('scan', barcodes[0].rawValue);
        return;
      }
    } catch {}
    animFrame = requestAnimationFrame(scan);
  }

  function stopCamera() {
    if (animFrame) cancelAnimationFrame(animFrame);
    if (stream) stream.getTracks().forEach(t => t.stop());
  }

  onDestroy(stopCamera);

  function close() {
    stopCamera();
    dispatch('close');
  }
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
<div class="scanner-overlay" on:click|self={close}>
  <div class="scanner-box">
    <header class="scanner-header">
      <span>Barcode scannen</span>
      <button class="close-btn" on:click={close} aria-label="Schließen">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </header>

    {#if errorMsg}
      <div class="error-msg">{errorMsg}</div>
    {:else}
      <div class="video-wrap">
        <!-- svelte-ignore a11y-media-has-caption -->
        <video bind:this={videoEl} class="video" playsinline muted></video>
        <div class="scan-frame">
          <div class="corner tl"></div>
          <div class="corner tr"></div>
          <div class="corner bl"></div>
          <div class="corner br"></div>
          <div class="scan-line"></div>
        </div>
      </div>
      <p class="hint">Barcode in den Rahmen halten</p>
    {/if}
  </div>
</div>

<style>
  .scanner-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.85);
    z-index: 300;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
  }

  .scanner-box {
    background: #111;
    border-radius: 16px;
    overflow: hidden;
    width: 100%;
    max-width: 420px;
    display: flex;
    flex-direction: column;
  }

  .scanner-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 16px;
    background: #1a1a1a;
    color: white;
    font-size: 15px;
    font-weight: 600;
  }

  .close-btn {
    background: none;
    border: none;
    color: rgba(255,255,255,0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4px;
    border-radius: 6px;
    transition: color 0.15s;
  }
  .close-btn:hover { color: white; }

  .video-wrap {
    position: relative;
    background: #000;
    aspect-ratio: 4/3;
  }

  .video {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .scan-frame {
    position: absolute;
    inset: 0;
  }

  .corner {
    position: absolute;
    width: 32px;
    height: 32px;
    border-color: #C8A96E;
    border-style: solid;
  }
  .tl { top: 20%; left: 15%; border-width: 3px 0 0 3px; border-radius: 4px 0 0 0; }
  .tr { top: 20%; right: 15%; border-width: 3px 3px 0 0; border-radius: 0 4px 0 0; }
  .bl { bottom: 20%; left: 15%; border-width: 0 0 3px 3px; border-radius: 0 0 0 4px; }
  .br { bottom: 20%; right: 15%; border-width: 0 3px 3px 0; border-radius: 0 0 4px 0; }

  .scan-line {
    position: absolute;
    left: 15%;
    right: 15%;
    height: 2px;
    background: linear-gradient(to right, transparent, #C8A96E, transparent);
    animation: scanMove 2s ease-in-out infinite;
    top: 20%;
  }

  @keyframes scanMove {
    0% { top: 20%; }
    50% { top: 80%; }
    100% { top: 20%; }
  }

  .hint {
    text-align: center;
    color: rgba(255,255,255,0.6);
    font-size: 13px;
    padding: 12px;
  }

  .error-msg {
    color: #ff7070;
    text-align: center;
    padding: 32px 20px;
    font-size: 14px;
  }
</style>
