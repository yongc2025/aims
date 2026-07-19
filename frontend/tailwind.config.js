/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        aims: {
          bg: '#050816',
          card: 'rgba(255,255,255,0.03)',
          border: 'rgba(255,255,255,0.06)',
          primary: '#00D4FF',
          up: '#00E676',
          down: '#FF5252',
          warn: '#FFC107',
          amber: '#FFB454',
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'SF Mono', 'ui-monospace', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
