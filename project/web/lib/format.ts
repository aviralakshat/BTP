/** Validated categorical slots, in fixed order. Never cycled. */
export const SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]

export const BLUE = {
  100: "#cde2fb", 200: "#9ec5f4", 250: "#86b6ef", 300: "#6da7ec", 450: "#2a78d6",
  550: "#1c5cab", 650: "#104281", 700: "#0d366b",
} as const

export const INK = { primary: "#0b0b0b", secondary: "#52514e", muted: "#898781", grid: "#e1e0d9", base: "#c3c2b7" }

/** Reserved for status. Always paired with an icon or a word. */
export const STATUS = { good: "#0ca30c", warn: "#fab219", bad: "#d03b3b" }

export const VERDICT = {
  PASS: { label: "In range", glyph: "●", color: STATUS.good },
  WARN: { label: "Near limit", glyph: "▲", color: STATUS.warn },
  FAIL: { label: "Out of range", glyph: "■", color: STATUS.bad },
  INFO: { label: "Reference", glyph: "○", color: INK.muted },
} as const

export const PROVENANCE: Record<string, { label: string; glyph: string }> = {
  verified: { label: "Verified", glyph: "●" },
  derived: { label: "Derived", glyph: "○" },
  indicative: { label: "Indicative", glyph: "◐" },
  scenario_choice: { label: "Scenario choice", glyph: "◇" },
  physical_constant: { label: "Physical constant", glyph: "○" },
  needs_citation: { label: "Pending source", glyph: "▲" },
}

const nf = (d: number) => new Intl.NumberFormat("en-IN", { minimumFractionDigits: d, maximumFractionDigits: d })

export const num = (v: number | null | undefined, d = 2) => (v == null || Number.isNaN(v) ? "—" : nf(d).format(v))

export function inr(v: number | null | undefined, compact = false) {
  if (v == null || Number.isNaN(v)) return "—"
  const sign = v < 0 ? "-" : ""
  const a = Math.abs(v)
  if (compact && a >= 1e7) return `${sign}₹${nf(2).format(a / 1e7)} Cr`
  if (compact && a >= 1e5) return `${sign}₹${nf(2).format(a / 1e5)} L`
  return `${sign}₹${nf(0).format(a)}`
}

export const pct = (v: number | null | undefined, d = 0) => (v == null ? "—" : `${nf(d).format(v * 100)}%`)

export const signed = (v: number, d = 0) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${nf(d).format(Math.abs(v))}`

export function sentence(s: string) {
  return s ? s[0].toUpperCase() + s.slice(1) : s
}
