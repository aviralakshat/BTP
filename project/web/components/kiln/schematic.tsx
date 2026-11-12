import type { Scenario } from "@/lib/api"
import { num } from "@/lib/format"

/** The kiln as an illustration. Each label carries the live per-tonne rate. */
export function KilnSchematic({ flows, co2 }: { flows: Scenario["flows"]; co2: number }) {
  const feeds = [
    ["Iron ore", `${num(flows.ore_t, 2)} t`],
    ["Coal", `${num(flows.coal_t, 2)} t`],
    ["Air", `${num(flows.air_t, 2)} t`],
    ["Dolomite", `${num(flows.dolomite_t, 3)} t`],
  ]
  const products = [
    ["Sponge iron", "1.00 t"],
    ["Waste gas", `${num(flows.waste_gas_t, 2)} t`],
    ["Char", `${num(flows.char_t, 3)} t`],
    ["CO₂ reported", `${num(co2, 2)} t`],
  ]
  return (
    <svg viewBox="0 0 960 300" className="h-auto w-full" role="img" aria-label="Rotary kiln with live feed and product rates per tonne of sponge iron">
      <defs>
        <linearGradient id="shell" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#3a4452" />
          <stop offset="0.45" stopColor="#5b6878" />
          <stop offset="1" stopColor="#262d36" />
        </linearGradient>
        <linearGradient id="heat" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#2a78d6" stopOpacity="0.0" />
          <stop offset="0.55" stopColor="#eda100" stopOpacity="0.35" />
          <stop offset="1" stopColor="#eb6834" stopOpacity="0.7" />
        </linearGradient>
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="#c3c2b7" />
        </marker>
      </defs>

      {feeds.map(([name, v], i) => {
        const y = 52 + i * 62
        return (
          <g key={name}>
            <text x="8" y={y} fontSize="10.5" letterSpacing="1.2" fill="#898781">{name.toUpperCase()}</text>
            <text x="8" y={y + 21} fontSize="17" fontWeight="600" fill="#0b0b0b" style={{ fontVariantNumeric: "tabular-nums" }}>{v}</text>
            <path d={`M120,${y + 8} C170,${y + 8} 180,${150 + i * 6} 222,${150 + i * 6}`} fill="none" stroke="#c3c2b7" strokeWidth="1.2" markerEnd="url(#arrow)" />
          </g>
        )
      })}

      <g transform="rotate(-6 480 150)">
        <rect x="232" y="108" width="500" height="84" rx="10" fill="url(#shell)" />
        <rect x="232" y="108" width="500" height="84" rx="10" fill="url(#heat)" />
        {[300, 440, 580, 690].map((x) => (
          <rect key={x} x={x} y="100" width="14" height="100" rx="3" fill="#1b2027" />
        ))}
        <rect x="216" y="114" width="20" height="72" rx="4" fill="#1b2027" />
        <rect x="728" y="114" width="22" height="72" rx="4" fill="#1b2027" />
        <text x="482" y="146" textAnchor="middle" fontSize="15" fontWeight="600" fill="#ffffff">Rotary kiln</text>
        <text x="482" y="166" textAnchor="middle" fontSize="11" fill="#cfd5dc">Pre-heating zone → reduction zone</text>
      </g>

      {products.map(([name, v], i) => {
        const y = 52 + i * 62
        return (
          <g key={name}>
            <path d={`M752,${142 + i * 6} C800,${142 + i * 6} 790,${y + 8} 836,${y + 8}`} fill="none" stroke="#c3c2b7" strokeWidth="1.2" markerEnd="url(#arrow)" />
            <text x="952" y={y} textAnchor="end" fontSize="10.5" letterSpacing="1.2" fill="#898781">{name.toUpperCase()}</text>
            <text x="952" y={y + 21} textAnchor="end" fontSize="17" fontWeight="600" fill="#0b0b0b" style={{ fontVariantNumeric: "tabular-nums" }}>{v}</text>
          </g>
        )
      })}
    </svg>
  )
}
