import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
        secure: false,
        // Silenciar el spam de ECONNREFUSED en la terminal cuando el backend no está iniciado
        configure: (proxy) => {
          proxy.on('error', (err, req, res) => {
            if (!res.headersSent) {
              res.writeHead(503, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ 
                status: 'offline',
                message: 'Backend FastAPI no detectado en puerto 8080. El frontend está usando almacenamiento local.' 
              }));
            }
          });
        }
      }
    }
  }
})
