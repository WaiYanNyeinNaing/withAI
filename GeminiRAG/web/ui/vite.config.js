import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      '/add': 'http://localhost:6001',
      '/upload': 'http://localhost:6001',
      '/search': 'http://localhost:6001',
      '/ask': 'http://localhost:6001',
      '/ask_stream': 'http://localhost:6001',
      '/stats': 'http://localhost:6001',
      '/clear': 'http://localhost:6001',
    }
  },
  optimizeDeps: {
    include: ['react-syntax-highlighter', 'react-syntax-highlighter/dist/esm/styles/prism']
  }
})
