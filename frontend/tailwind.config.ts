import type { Config } from "tailwindcss";

/**
 * Offshore design tokens.
 *
 * Visual identity: dark, cool, oceanic. Deep navy base + glacial teal accent,
 * reserved for Antarctica / Southern Ocean thematic alignment.
 *
 * Every later surface (risk panel, route sidebar, iceberg inspector, etc.) must
 * consume these tokens rather than introducing raw colors.
 *
 * See: src/styles/tokens.css for the CSS-variable source of truth.
 */
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Primitive → semantic mapping. Keep this flat on purpose; we
        // re-export semantic names via CSS variables for portability.
        offshore: {
          abyss: "#050a14",      // deepest background (page)
          deep: "#0a1424",       // surface
          hull: "#0f1b2e",       // panel / card
          steel: "#1b2a44",      // border, divider
          fog: "#3a506b",        // muted border / disabled
          mist: "#a7b8cc",       // secondary text
          ice: "#e8f1f8",        // primary text on dark
          glacial: "#7fd1d3",    // primary accent (teal)
          lagoon: "#3aa9b3",     // accent hover
          signal: "#5eead4",     // success / "go" cue
          hazard: "#f87171",     // danger / iceberg
          alert: "#fbbf24",      // warning
        },
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      boxShadow: {
        panel: "0 1px 0 rgba(255,255,255,0.04) inset, 0 8px 24px rgba(0,0,0,0.35)",
      },
    },
  },
  plugins: [],
};

export default config;