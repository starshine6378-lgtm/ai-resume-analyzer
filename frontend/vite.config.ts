import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Relative assets work both locally and under /<repository>/ on GitHub Pages.
  base: "./",
});
