import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

function liveWipePlugin() {
  let state = {
    connected: false,
    is_wiping: false,
    status: "IDLE",
    target: "\\\\.\\PhysicalDrive1 (15.2 GB Pendrive)",
    method: "NIST_800_88_PURGE",
    progress: 0,
    speed_mb_s: 0,
    bytes_written: 0,
    total_bytes: 0,
    sectors_done: 0,
    sectors_total: 19380,
    pass_number: 1,
    total_passes: 1,
    pass_label: "",
    eta_seconds: 0,
    bad_sectors: 0,
    logs: [
      "[SYS] ZeroTrace Forensic Workstation initialized.",
      "[SYS] Ready and listening for desktop application hardware sanitization..."
    ],
    last_update: 0,
    certificate: null
  };

  return {
    name: 'live-wipe-bridge',
    configureServer(server) {
      server.middlewares.use('/api/live-wipe', (req, res) => {
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

        if (req.method === 'OPTIONS') {
          res.statusCode = 204;
          return res.end();
        }

        if (req.method === 'POST') {
          let body = '';
          req.on('data', chunk => { body += chunk; });
          req.on('end', () => {
            try {
              const data = JSON.parse(body);
              state = {
                ...state,
                ...data,
                connected: true,
                last_update: Date.now()
              };
              if (data.new_log) {
                state.logs = [...state.logs.slice(-60), data.new_log];
              }
              res.setHeader('Content-Type', 'application/json');
              res.end(JSON.stringify({ success: true, message: 'Telemetry received' }));
            } catch (err) {
              res.statusCode = 400;
              res.end(JSON.stringify({ error: err.message }));
            }
          });
        } else {
          const isFresh = (Date.now() - state.last_update) < 15000;
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ ...state, workstation_online: isFresh }));
        }
      });
    }
  };
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss(), liveWipePlugin()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})


