<script>
  import '../app.css';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { isLoggedIn } from '$lib/stores/auth.js';

  const PUBLIC_PATHS = ['/login', '/kiosk'];

  onMount(() => {
    const path = $page.url.pathname;
    const isPublic = PUBLIC_PATHS.some(p => path === p || path.startsWith(p + '/'));
    if (!isPublic && !$isLoggedIn) {
      goto('/login');
    }
  });
</script>

<slot />
