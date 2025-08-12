/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Custom colors for card rotation as specified in PRP
        'card-pink': '#EAB2AB',
        'card-blue': '#93C4D8', 
        'card-yellow': '#FCE3AB',
      },
      fontFamily: {
        'sans': ['Inter', 'ui-sans-serif', 'system-ui'],
      },
      screens: {
        'xs': '475px',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [
    // Custom plugin for masonry layout
    function({ addUtilities }) {
      const newUtilities = {
        '.masonry': {
          'column-count': '2',
          'column-gap': '1rem',
          'column-fill': 'balance',
        },
        '.masonry-sm': {
          'column-count': '1',
        },
        '.masonry-md': {
          'column-count': '3',
        },
        '.masonry-lg': {
          'column-count': '4',
        },
        '.masonry-item': {
          'break-inside': 'avoid',
          'margin-bottom': '1rem',
          'display': 'inline-block',
          'width': '100%',
        },
      }
      
      addUtilities(newUtilities, ['responsive'])
    }
  ],
}