import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const hmrConfig = process.env.VITE_HMR_HOST
    ? {
          protocol: 'wss',
          host: process.env.VITE_HMR_HOST,
          port: parseInt(process.env.VITE_HMR_PORT || '443'),
      }
    : undefined; // Let Vite auto-detect HMR settings

export default defineConfig({
    plugins: [react()],
    server: {
        host: true,
        port: 5173,
        ...(hmrConfig && { hmr: hmrConfig }),
        proxy: {
            '/api': {
                target: 'http://backend:8000',
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api/, ''),
            },
        },
    },
});
