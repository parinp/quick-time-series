/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          main: '#00B3FF',
          light: '#33C9FF',
          dark: '#0091CC',
        },
        secondary: {
          main: '#FF9500',
          light: '#FFAA33',
          dark: '#CC7700',
        },
        success: {
          main: '#00E396',
          light: '#33E9AB',
          dark: '#00B578',
        },
        error: {
          main: '#FF4560',
          light: '#FF6B7D',
          dark: '#CC374D',
        },
        background: {
          default: '#0A0E17',
          paper: '#111827',
        },
        text: {
          primary: '#FFFFFF',
          secondary: '#B0B7C3',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
      },
      boxShadow: {
        card: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'card-hover': '0 10px 15px -3px rgba(0, 0, 0, 0.3)',
      },
      borderRadius: {
        card: '12px',
      },
    },
  },
  plugins: [],
  // Important to prevent conflicts with Material UI
  corePlugins: {
    preflight: false,
  },
} 