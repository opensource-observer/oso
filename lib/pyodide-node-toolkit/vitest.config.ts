import { defineConfig } from "vitest/config";
import path from "path";
import { fileURLToPath } from "url";

// __dirname is not available in ESM
const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      // Force using the CJS entry point to avoid issues with ESM import paths in pyodide 0.29.0
      pyodide: "pyodide/pyodide.js",
    },
  },
  test: {
    globals: true,
  },
});
