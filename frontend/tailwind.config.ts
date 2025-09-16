import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui"],
      },
      colors: {
        brand: {
          DEFAULT: "#4f46e5",
          foreground: "#eef2ff"
        }
      },
      animation: {
        "fade-in": "fade-in 0.3s ease-in-out"
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" }
        }
      }
    }
  },
  plugins: [require("tailwindcss-animate")]
};

export default config;
