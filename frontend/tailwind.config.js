/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // SensorPulse brand colors
        'sp-charcoal': '#3C4650',
        'sp-cyan': '#00A8E8',
        'sp-lime': '#92D13F',
      },
    },
  },
  plugins: [],
}
