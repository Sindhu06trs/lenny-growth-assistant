/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#EEF2FF',
          100: '#E0E7FF',
          200: '#C7D2FE',
          300: '#A5B4FC',
          400: '#818CF8',
          500: '#6366F1', // Primary Electric Indigo
          600: '#4F46E5',
          700: '#4338CA',
          800: '#3730A3',
          900: '#312E81',
        },
        dark: {
          bg: '#0B0F19',        // Deep Obsidian Slate
          surface: '#131B2E',   // Midnight Slate Panel
          card: '#182238',      // Card surface
          border: '#232F4D',    // Border divider
          hover: '#1F2C4A',     // Hover state
          muted: '#2A3B60',     // Subtle element
        },
        growth: {
          emerald: '#10B981',   // Growth Emerald for Citations & Success
          gold: '#F59E0B',      // Podcast Gold for Highlights & Badges
          rose: '#F43F5E',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        serif: ['Merriweather', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
}
