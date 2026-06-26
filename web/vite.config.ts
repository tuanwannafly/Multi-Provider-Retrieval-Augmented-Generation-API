import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/health': 'http://localhost:8000',
      '/readiness': 'http://localhost:8000',
      '/documents': 'http://localhost:8000',
      '/collections': 'http://localhost:8000',
      '/ask': 'http://localhost:8000',
      '/compare': 'http://localhost:8000',
      '/evaluate': 'http://localhost:8000',
    },
  },
})