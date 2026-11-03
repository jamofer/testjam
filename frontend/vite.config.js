import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Third-party code changes far less often than the app: separate chunks keep
// it cached across deploys. Lazy-loaded heavy libraries (editor, PDF) keep
// their own automatic chunks.
const VENDOR_CHUNKS = {
  'vendor-react': ['react', 'react-dom', 'react-router', 'react-router-dom', 'scheduler'],
  'vendor-ui': ['@radix-ui', '@floating-ui', 'lucide-react', 'sonner', '@dnd-kit'],
  'vendor-data': ['@tanstack', 'axios', 'i18next', 'react-i18next'],
}

function vendorChunk(id) {
  if (!id.includes('/node_modules/')) return undefined
  const modulePath = id.split('/node_modules/').pop()
  return Object.keys(VENDOR_CHUNKS).find(chunk =>
    VENDOR_CHUNKS[chunk].some(name => modulePath === name || modulePath.startsWith(`${name}/`)),
  )
}

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: { manualChunks: vendorChunk },
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: ['localhost', 'frontend'],
    proxy: {
      '/api': { target: 'http://api:8000', changeOrigin: true, ws: true },
      '/files': { target: 'http://api:8000', changeOrigin: true },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/__tests__/setup.js'],
  },
})
