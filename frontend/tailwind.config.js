/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0284c7',
          600: '#0284c7',
          700: '#0369a1',
          900: '#0c4a6e',
        },
        damage: {
          none: '#10b981',
          minor: '#f59e0b',
          major: '#f97316',
          destroyed: '#ef4444'
        }
      }
    },
  },
  plugins: [],
}
