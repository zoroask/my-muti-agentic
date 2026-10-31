import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0f172a',
        surface: '#1e293b',
        'surface-raised': '#334155',
        text: '#f8fafc',
        muted: '#94a3b8',
        accent: '#3b82f6',
        'accent-hover': '#2563eb',
        success: '#22c55e',
        warning: '#f59e0b',
        danger: '#ef4444',
        border: '#334155',
      },
      borderRadius: {
        card: '6px',
        btn: '8px',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config
