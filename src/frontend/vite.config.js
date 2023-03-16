import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
      proxy: {
        '^/api/.*': {
          target: 'http://localhost:5000',
          changeOrigin: true,
        },
        '^/api-docs/.*': {
          target: 'http://localhost:5000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api-docs/, ''),
        },
        '^/swagger.json': {
          target: 'http://localhost:5000',
          changeOrigin: true,
        },
        '^/swaggerui/.*': {
          target: 'http://localhost:5000',
          changeOrigin: true,
        },
        '^/health/?': {
          target: 'http://localhost:5000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/health\/$/, '\/health'),
        },
      }
  }
})
