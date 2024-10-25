import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // proxy /api to localhost:8000/api
      '/api': 'http://localhost:8000/',
    }
  }
})
