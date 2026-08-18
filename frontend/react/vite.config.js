import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Dev-time passthrough to the FastAPI retrieval service (or run the Node
      // gateway on 8000 and point these at http://localhost:8000 instead)
      '/ingest': 'http://localhost:8001',
      '/search': 'http://localhost:8001',
      '/chat': 'http://localhost:8001',
      '/documents': 'http://localhost:8001',
      '/title': 'http://localhost:8001',
      '/space': 'http://localhost:8001',
    },
  },
})
