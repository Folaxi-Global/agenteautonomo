import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import react from '@astrojs/react';

// https://astro.build/config
export default defineConfig({
  integrations: [tailwind(), react()],
  // Importante: Esto asegura que las rutas funcionen bien en Vercel
  trailingSlash: 'never',
  build: {
    // Vercel espera la salida en la carpeta 'dist'
    outDir: 'dist'
  }
});
