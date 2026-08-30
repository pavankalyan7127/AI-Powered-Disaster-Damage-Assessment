import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [
    react({
      fastRefresh: true,
    })
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/outputs': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/backend_uploads': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/inference': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
});
