import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { quasar, transformAssetUrls } from '@quasar/vite-plugin'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue({
      template: { transformAssetUrls }
    }),
    // @quasar/plugin-vite options list:
    // https://github.com/quasarframework/quasar/blob/dev/vite-plugin/index.d.ts
    quasar({
      sassVariables: 'src/quasar-variables.sass'
    })
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    proxy: {
      '^/api/.*': {
        target: 'http://localhost:5000'
        // changeOrigin: true,
        // rewrite: (path) => path.replace(/^\/api/, ''),
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
  },
})
