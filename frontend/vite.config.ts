import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: {
      '/recipes': 'http://backend:8000',
      '/api': 'http://backend:8000',
      '/login': 'http://backend:8000',
      '/logout': 'http://backend:8000',
      '/authorize': 'http://backend:8000'
    }
  }
});
