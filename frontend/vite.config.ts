import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
  base: "/landing/",
  plugins: [react(), tailwindcss()],
  build: {
    // 产物输出到 FastAPI 的 static/landing，可通过 /landing/ 直接访问
    outDir: "../static/landing",
    emptyOutDir: true,
  },
});
