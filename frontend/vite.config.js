import react from "@vitejs/plugin-react";
import { resolve } from "node:path";
import { defineConfig, loadEnv } from "vite";

const envDir = resolve(__dirname, "..");

export default defineConfig(({ mode }) => {

  // Only DEV_* is read here. Vite does not
  // put .env values on process.env.
  const env = loadEnv(mode, envDir, "DEV_");

  return {
    plugins: [react()],

    envDir,

    server: {
      proxy: {
        "/api": {
          target: (
            env.DEV_API_PROXY_TARGET ||
            "http://127.0.0.1:8000"
          ),
          changeOrigin: true
        }
      }
    }
  };
});
