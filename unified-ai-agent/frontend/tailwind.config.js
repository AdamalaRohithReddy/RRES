/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        govblue: {
          50: '#f0f5fa',
          100: '#dce8f4',
          500: '#1b4d89',
          600: '#143c6d',
          700: '#0e2b52',
          800: '#091c36',
          900: '#040d1b',
        },
        govgold: {
          500: '#f59e0b',
          600: '#d97706',
        }
      }
    },
  },
  plugins: [],
}
