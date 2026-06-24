import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        buy: '#22c55e',
        sell: '#ef4444',
        hold: '#eab308',
      },
    },
  },
  plugins: [],
}

export default config
