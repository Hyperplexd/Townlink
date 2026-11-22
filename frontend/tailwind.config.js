/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Manrope', 'system-ui', 'sans-serif'],
        serif: ['"Source Serif 4"', 'Georgia', 'serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        ink: {
          950: '#070b12',
          900: '#0c1220',
          800: '#141c2e',
          700: '#1c2740',
        },
        brass: {
          200: '#f3e2b0',
          300: '#e4c36a',
          500: '#b8892d',
        },
        city: {
          800: '#003865',
          700: '#0a4d82',
          500: '#1d6fbf',
        },
        paper: '#f4efe6',
      },
      boxShadow: {
        phone: '0 36px 70px -28px rgba(0,0,0,.75)',
      },
    },
  },
  plugins: [],
};
