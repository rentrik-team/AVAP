import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    globals: false,
    css: false,
    env: {
      // config/env.ts validates this at module load time (it's a required
      // public runtime config, not a secret) — every module that imports
      // lib/api/client.ts transitively needs it defined, even in tests
      // that never actually issue a request.
      NEXT_PUBLIC_API_BASE_URL: "http://localhost:8000",
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
});
