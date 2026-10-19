import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function getLocalToken(): string {
  if (process.env.SPECBRIDGE_TOKEN) return process.env.SPECBRIDGE_TOKEN;
  try {
    const tokenPath = path.resolve(__dirname, "../../.data/session-token");
    if (fs.existsSync(tokenPath)) {
      return fs.readFileSync(tokenPath, "utf-8").trim();
    }
  } catch {
    // ignore
  }
  return "";
}

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        target: process.env.VITE_API_TARGET || "http://127.0.0.1:8000",
        configure: (proxy) => {
          proxy.on("proxyReq", (proxyReq) => {
            if (!proxyReq.getHeader("Authorization")) {
              const token = getLocalToken();
              if (token) {
                proxyReq.setHeader("Authorization", `Bearer ${token}`);
              }
            }
          });
        },
      },
    },
  },
});
