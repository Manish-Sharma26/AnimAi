import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Forward /api requests to Express server
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
      // Forward Socket.io to Express server
      '/socket.io': {
        target: 'http://localhost:3001',
        changeOrigin: true,
        ws: true,  // WebSocket proxy
      },
    },
  },
})
