/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'vartens-blue': '#2563eb', // Un azul vibrante
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'], // Usaremos Inter por defecto (más fácil de cargar)
      },
    },
  },
  plugins: [],
};
