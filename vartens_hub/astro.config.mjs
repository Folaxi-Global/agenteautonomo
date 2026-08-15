import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import react from '@astrojs/react';
import vercel from '@astrojs/vercel'; // <-- Asegúrate de que diga '@astrojs/vercel'

export default defineConfig({
  output: 'server',
  adapter: vercel(),
  integrations: [tailwind(), react()],
  trailingSlash: 'never',
  build: {
    outDir: 'dist'
  }
});
