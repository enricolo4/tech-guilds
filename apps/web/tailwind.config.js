/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'o2-green': '#6BF169',
        'o2-gray': '#494949',
        'retro-dark': '#0b0e14',
        'retro-card': '#121824',
        'retro-border': '#232d3f',
        'retro-cyan': '#00e5ff',
        'retro-gold': '#ffbe33',
        'retro-red': '#ff3864',
        'retro-purple': '#9d4edd',
      },
      fontFamily: {
        pixel: ['"Press Start 2P"', 'monospace'],
        terminal: ['VT323', 'monospace'],
      },
    },
  },
  plugins: [],
};
