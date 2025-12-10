import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
<<<<<<<< HEAD:dashboard-ui/vite.config.js
    host: '0.0.0.0',
    port: 5173,
========
>>>>>>>> origin/refactor/full-system-rewrite:dashboard-ui/vite.config.ts
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
