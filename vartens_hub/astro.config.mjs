import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import react from '@astrojs/react';
import vercel from '@vercel/astro';

// https://astro.build/config
export default defineConfig({
  output: 'server', // <-- Vital para que funcionen las rutas dinámicas por subdominio
  adapter: vercel(),
  integrations: [tailwind(), react()],
  trailingSlash: 'never',
  build: {
    outDir: 'dist'
  }
});
