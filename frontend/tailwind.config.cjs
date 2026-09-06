/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Brand. Chosen to sit clear of the status hues below so an accent can
        // never be mistaken for a score.
        brand: {
          50: "#f2f0fb",
          100: "#e6e2f7",
          200: "#cec7ef",
          300: "#aa9ee2",
          400: "#8474d1",
          500: "#6553bd",
          600: "#4a3aa7", // primary — 8.56:1 on white
          700: "#3d2f8c",
          800: "#332771",
          900: "#2b215d",
        },
        ink: {
          DEFAULT: "#0b0b0b",
          soft: "#52514e",
          muted: "#898781",
        },
        line: "#e6e5e0",
        canvas: "#f9f9f7",
        // Status palette. Fixed, never themed, never reused as decoration.
        // warning is sub-3:1 on white by design, so it is always paired with an
        // icon and a text label rather than carrying meaning alone.
        score: {
          strong: "#0ca30c",
          mid: "#fab219",
          weak: "#d03b3b",
          "strong-ink": "#046604",
          "mid-ink": "#8a5a00",
          "weak-ink": "#a52121",
        },
      },
      fontFamily: {
        sans: [
          // Inter is loaded in index.html; the rest is a graceful fallback.
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
      fontSize: {
        "display": ["clamp(2.5rem, 5vw, 4rem)", { lineHeight: "1.05", letterSpacing: "-0.03em" }],
        "title": ["clamp(1.75rem, 3vw, 2.5rem)", { lineHeight: "1.15", letterSpacing: "-0.02em" }],
      },
      boxShadow: {
        card: "0 1px 2px rgba(11,11,11,0.04), 0 1px 3px rgba(11,11,11,0.06)",
        lift: "0 4px 12px rgba(11,11,11,0.06), 0 12px 32px rgba(11,11,11,0.08)",
        brand: "0 8px 24px rgba(74,58,167,0.24)",
      },
      borderRadius: { xl2: "1rem" },
      keyframes: {
        "fade-up": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: { "100%": { transform: "translateX(100%)" } },
      },
      animation: {
        "fade-up": "fade-up 0.35s ease-out both",
        shimmer: "shimmer 1.6s infinite",
      },
    },
  },
  plugins: [],
};
