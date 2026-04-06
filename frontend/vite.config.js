import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    
    // HMR через Docker — указываем WebSocket на localhost
    hmr: {
      host: 'localhost',
      port: 5173,
    },
    
    // ВАЖНО: Polling нужен потому что Docker volumes
    // не триггерят нативные filesystem events
    watch: {
      usePolling: true,
      interval: 1000,
    },
    
    // Proxy API запросов на бэкенд
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})