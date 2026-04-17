/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,jsx,ts,tsx}", "./components/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        app_orange_color: '#C67C4E',
        terracotta: '#C67C4E',
        'terracotta-light': '#D4896A',
        'terracotta-subtle': '#F5EBE4',
        cream: '#FAF7F4',
        'cream-surface': '#FFFDF9',
        espresso: '#1C1410',
        'espresso-mid': '#6B5344',
        roast: '#1A1210',
        'roast-surface': '#231A17',
      },
    },
  },
  plugins: [],
};
