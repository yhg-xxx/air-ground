import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  // 跨域代理（解决你 5173 CORS 报错）
  server: {
    proxy: {
      '/api': {
        target: 'http://fcs.botzooo.com:30080',
        changeOrigin: true,
        rewrite: (path) => path
      },
      '/ws': {
        target: 'ws://fcs.botzooo.com:30081',
        ws: true,
        changeOrigin: true,
        rewrite: (path) => path
      }
    }
  }
})