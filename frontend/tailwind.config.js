/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sepia: {
          50: '#faf7f2',
          100: '#f4ede1',
          200: '#ebd9c2',
          300: '#dfbe9d',
          600: '#a36d42',
          800: '#5c3e27',
          900: '#382518',
        },
        legado: {
          amber: '#d97706',
          warm: '#fffbeb',
          dark: '#1c1917',
          emerald: '#059669',
        }
      },
      fontFamily: {
        serif: ['Georgia', 'Cambria', '"Times New Roman"', 'Times', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}

