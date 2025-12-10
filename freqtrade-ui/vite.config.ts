import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5176,
    proxy: {
      // Management Server (8002) - основной API
      '/api/v1': {
        target: 'http://127.0.0.1:8002',
        changeOrigin: true,
      },
      // Backtesting Server (8003) - бэктестирование
      '/api/backtesting': {
        target: 'http://127.0.0.1:8003',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/backtesting/, ''),
      },
      // FreqAI Server (8004) - ML модели
      '/api/freqai': {
        target: 'http://127.0.0.1:8004',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/freqai/, ''),
      },
      // Trading Gateway (8001) - управление ботами
      '/api/trading': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/trading/, '/api/v1'),
      },
    },
    fs: {
      strict: false,
    },
    historyApiFallback: true,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: undefined,
      },
    },
  },
})
