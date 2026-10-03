import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  css: {
    postcss: false
  },
  server: {
    proxy: {
      "/api": "http://localhost:8000"
    }
  }
});
