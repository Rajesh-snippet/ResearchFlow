import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev server proxies /api/* to the FastAPI backend so the frontend never
// hardcodes a port. In production (Docker/Railway), set VITE_API_BASE_URL
// instead — see src/api.js.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
