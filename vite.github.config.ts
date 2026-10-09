import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  base: "/council-school-atlas/",
  plugins: [react()],
  build: {
    outDir: "dist-pages",
    emptyOutDir: true,
  },
});
