import type { Config } from "tailwindcss";

export default {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#0b0e11",
        panel: "#161a1e",
        panelAlt: "#1e2329",
        accent: "#fcd535",
        success: "#2ebd85",
        warning: "#f0b90b",
        danger: "#f6465d",
        textSoft: "#b7bdc6",
      },
      boxShadow: {
        neon: "0 8px 30px rgba(0, 0, 0, 0.35)",
        glow: "0 0 20px rgba(252, 213, 53, 0.2)",
      },
    },
  },
  plugins: [],
} satisfies Config;
