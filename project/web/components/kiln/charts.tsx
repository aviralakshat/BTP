"use client"

import {
  Bar, BarChart, CartesianGrid, Cell, ComposedChart, LabelList, Legend, Line, LineChart, ReferenceLine,
  ResponsiveContainer, Sankey, Scatter, ScatterChart, Tooltip, XAxis, YAxis,
} from "recharts"
import type { Finance, PathwayRow, Scenario } from "@/lib/api"
import { BLUE, INK, SERIES, inr, num, sentence } from "@/lib/format"

const AXIS = { stroke: INK.base, tick: { fill: INK.muted, fontSize: 11 }, tickLine: false }
const TIP = {
  contentStyle: {
    background: "#fcfcfb", border: "1px solid #e1e0d9", borderRadius: 8, fontSize: 12,
    boxShadow: "0 8px 24px rgba(11,11,11,0.08)", padding: "8px 10px",
  },
  labelStyle: { color: INK.primary, fontWeight: 600, marginBottom: 2 },
  itemStyle: { color: INK.secondary, padding: 0 },
  cursor: { fill: "rgba(42,120,214,0.06)" },
}

// ---------------------------------------------------------------- mass flow
type NodeProps = { x?: number; y?: number; width?: number; height?: number; index?: number; payload?: { name: string; value: number }; containerWidth?: number }

function FlowNode({ x = 0, y = 0, width = 0, height = 0, payload, containerWidth = 0 }: NodeProps) {
  const right = x > containerWidth / 2
  const hub = payload?.name === "Rotary kiln"
  return (
    <g>
      <rect x={x} y={y} width={width} height={Math.max(height, 1)} fill={hub ? BLUE[650] : right ? BLUE[300] : BLUE[450]} />
      {!hub && (
        <text x={right ? x - 8 : x + width + 8} y={y + height / 2} textAnchor={right ? "end" : "start"} dominantBaseline="middle" fontSize={11.5} fill={INK.primary}>
          {payload?.name}
          <tspan fill={INK.muted} dx={6}>{num(payload?.value ?? 0, 0)} kg</tspan>
        </text>
      )}
      {hub && (
        <text x={x + width / 2} y={y - 8} textAnchor="middle" fontSize={11.5} fontWeight={600} fill={INK.primary}>Rotary kiln</text>
      )}
    </g>
  )
}

export function MassSankey({ streams }: { streams: Scenario["streams"] }) {
  const ins = streams.filter((s) => s.direction === "in" && s.kg > 0.5)
  const outs = streams.filter((s) => s.direction === "out" && s.kg > 0.5)
  const nodes = [...ins.map((s) => ({ name: s.name })), { name: "Rotary kiln" }, ...outs.map((s) => ({ name: s.name }))]
  const hub = ins.length
  const links = [
    ...ins.map((s, i) => ({ source: i, target: hub, value: s.kg })),
    ...outs.map((s, i) => ({ source: hub, target: hub + 1 + i, value: s.kg })),
  ]
  return (
    <ResponsiveContainer width="100%" height={420}>
      <Sankey
        data={{ nodes, links }}
        node={<FlowNode />}
        nodePadding={22}
        nodeWidth={10}
        margin={{ top: 24, right: 180, bottom: 16, left: 180 }}
        link={{ stroke: "rgba(109,167,236,0.38)" }}
      >
        <Tooltip {...TIP} formatter={(v) => `${num(Number(v), 0)} kg per t DRI`} />
      </Sankey>
    </ResponsiveContainer>
  )
}

// ---------------------------------------------------------------- energy
export function EnergyBars({ energy }: { energy: Scenario["energy"] }) {
  const groups = Array.from(new Set(energy.filter((e) => !e.is_input).map((e) => e.group)))
  const color = (g: string) => SERIES[Math.max(0, groups.indexOf(g)) % 4]
  const data = energy
    .filter((e) => !e.is_input && e.gcal > 0.0005)
    .sort((a, b) => b.gcal - a.gcal)
    .map((e) => ({ ...e, label: e.item }))
  return (
    <>
      <div className="mb-3 flex flex-wrap gap-x-4 gap-y-1">
        {groups.map((g) => (
          <span key={g} className="inline-flex items-center gap-1.5 text-[11.5px] text-ink-2">
            <span className="size-2.5 rounded-[2px]" style={{ background: color(g) }} />
            {g}
          </span>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={Math.max(220, data.length * 30 + 30)}>
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 64, bottom: 0, left: 0 }} barCategoryGap={7}>
          <CartesianGrid horizontal={false} stroke={INK.grid} />
          <XAxis type="number" {...AXIS} tickFormatter={(v) => num(v, 1)} />
          <YAxis type="category" dataKey="label" width={210} {...AXIS} tick={{ fill: INK.secondary, fontSize: 11.5 }} axisLine={false} />
          <Tooltip {...TIP} formatter={(v, _n, p) => [`${num(Number(v), 3)} Gcal/t (${num((p.payload as { pct: number }).pct, 1)}% of coal heat)`, (p.payload as { group: string }).group]} />
          <Bar dataKey="gcal" isAnimationActive={false}>
            {data.map((d, i) => <Cell key={i} fill={color(d.group)} />)}
            <LabelList dataKey="gcal" position="right" formatter={(v: unknown) => num(Number(v), 3)} style={{ fill: INK.secondary, fontSize: 11 }} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </>
  )
}

// ---------------------------------------------------------------- kiln axis
export function AxialChart({ cells }: { cells: Scenario["kiln"]["cells"] }) {
  const data = cells.map((c) => ({ z: Number(c.z.toFixed(1)), gas: c.gas, solid: c.solid }))
  const split = cells.find((c) => c.zone !== "preheat")?.z
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 16, right: 24, bottom: 4, left: 0 }}>
        <CartesianGrid stroke={INK.grid} vertical={false} />
        <XAxis dataKey="z" type="number" domain={[0, "dataMax"]} {...AXIS} tickFormatter={(v) => `${v} m`} />
        <YAxis {...AXIS} axisLine={false} tickFormatter={(v) => `${v}°`} width={48} />
        {split != null && <ReferenceLine x={split} stroke={INK.base} strokeDasharray="4 4" label={{ value: "Reduction zone →", position: "insideTopLeft", fill: INK.muted, fontSize: 11 }} />}
        <Tooltip {...TIP} labelFormatter={(v) => `${v} m from feed end`} formatter={(v, n) => [`${num(Number(v), 0)} °C`, n === "gas" ? "Gas" : "Bed"]} />
        <Legend iconType="plainline" formatter={(v) => (v === "gas" ? "Gas" : "Bed (solids)")} wrapperStyle={{ fontSize: 12, color: INK.secondary }} />
        <Line dataKey="gas" stroke={SERIES[0]} strokeWidth={2.5} dot={false} isAnimationActive={false} />
        <Line dataKey="solid" stroke={SERIES[1]} strokeWidth={2.5} dot={false} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}

// ---------------------------------------------------------------- pathways
export function PathwayScatter({ rows, selected }: { rows: PathwayRow[]; selected?: string | null }) {
  const pt = (r: PathwayRow) => ({ x: r.co2_cut * 100, y: r.cost_delta, label: sentence(r.label) })
  const ok = rows.filter((r) => r.feasible && !r.frontier).map(pt)
  const bad = rows.filter((r) => !r.feasible).map(pt)
  const front = rows.filter((r) => r.frontier).sort((a, b) => a.co2_cut - b.co2_cut).map(pt)
  const pick = rows.filter((r) => r.label === selected).map(pt)
  return (
    <ResponsiveContainer width="100%" height={400}>
      <ScatterChart margin={{ top: 16, right: 24, bottom: 8, left: 8 }}>
        <CartesianGrid stroke={INK.grid} />
        <XAxis type="number" dataKey="x" name="CO2 cut" {...AXIS} tickFormatter={(v) => `${v}%`} domain={[0, "dataMax"]}
          label={{ value: "CO₂ removed", position: "insideBottomRight", offset: -2, fill: INK.muted, fontSize: 11 }} />
        <YAxis type="number" dataKey="y" name="Cost change" {...AXIS} width={64} tickFormatter={(v) => inr(v)} axisLine={false} />
        <ReferenceLine y={0} stroke={INK.base} />
        <Tooltip {...TIP} cursor={{ strokeDasharray: "3 3" }}
          content={({ payload }) => {
            const p = payload?.[0]?.payload as { x: number; y: number; label: string } | undefined
            if (!p) return null
            return (
              <div style={TIP.contentStyle}>
                <div style={{ fontWeight: 600, color: INK.primary }}>{p.label}</div>
                <div style={{ color: INK.secondary }}>CO₂ removed {num(p.x, 1)}%</div>
                <div style={{ color: INK.secondary }}>Cost change {inr(p.y)} per tonne</div>
              </div>
            )
          }} />
        <Legend wrapperStyle={{ fontSize: 12, color: INK.secondary }} />
        <Scatter name="Workable mix" data={ok} fill={BLUE[250]} isAnimationActive={false} />
        <Scatter name="Not enough carbon to reduce ore" data={bad} shape="square" fill="none" stroke={INK.muted} isAnimationActive={false} />
        <Scatter name="Cheapest at each cut" data={front} fill={BLUE[650]} line={{ stroke: BLUE[650], strokeWidth: 2 }} lineType="joint" isAnimationActive={false} />
        {pick.length > 0 && <Scatter name="Selected" data={pick} fill={SERIES[1]} shape="diamond" legendType="diamond" isAnimationActive={false} />}
      </ScatterChart>
    </ResponsiveContainer>
  )
}

// ---------------------------------------------------------------- cost
export function CostBars({ lines }: { lines: Scenario["cost_lines"] }) {
  const data = [...lines].sort((a, b) => b.inr - a.inr)
  return (
    <ResponsiveContainer width="100%" height={Math.max(200, data.length * 32 + 30)}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 72, bottom: 0, left: 0 }} barCategoryGap={8}>
        <CartesianGrid horizontal={false} stroke={INK.grid} />
        <XAxis type="number" {...AXIS} tickFormatter={(v) => inr(v)} />
        <YAxis type="category" dataKey="item" width={190} {...AXIS} tick={{ fill: INK.secondary, fontSize: 11.5 }} axisLine={false} />
        <ReferenceLine x={0} stroke={INK.base} />
        <Tooltip {...TIP} formatter={(v) => [`${inr(Number(v))} per tonne`, Number(v) < 0 ? "Credit" : "Cost"]} />
        <Bar dataKey="inr" isAnimationActive={false}>
          {data.map((d, i) => <Cell key={i} fill={d.inr >= 0 ? SERIES[0] : SERIES[1]} />)}
          <LabelList dataKey="inr" position="right" formatter={(v: unknown) => inr(Number(v))} style={{ fill: INK.secondary, fontSize: 11 }} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// ---------------------------------------------------------------- cash flow
export function CashFlowChart({ years }: { years: Finance["years"] }) {
  const data = years.map((y) => ({ year: y.year, cash: y.equity_cf, cumulative: y.cumulative }))
  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={data} margin={{ top: 16, right: 24, bottom: 4, left: 8 }}>
        <CartesianGrid stroke={INK.grid} vertical={false} />
        <XAxis dataKey="year" {...AXIS} tickFormatter={(v) => (v === 0 ? "Build" : `Y${v}`)} />
        <YAxis {...AXIS} axisLine={false} width={72} tickFormatter={(v) => inr(v, true)} />
        <ReferenceLine y={0} stroke={INK.base} />
        <Tooltip {...TIP} labelFormatter={(v) => (Number(v) === 0 ? "Year 0, equity invested" : `Year ${v}`)}
          formatter={(v, n) => [inr(Number(v), true), n === "cash" ? "Equity cash flow" : "Cumulative"]} />
        <Legend formatter={(v) => (v === "cash" ? "Equity cash flow in the year" : "Cumulative position")} wrapperStyle={{ fontSize: 12, color: INK.secondary }} />
        <Bar dataKey="cash" isAnimationActive={false}>
          {data.map((d, i) => <Cell key={i} fill={d.cash >= 0 ? SERIES[0] : SERIES[1]} />)}
        </Bar>
        <Line dataKey="cumulative" stroke={BLUE[650]} strokeWidth={2.5} dot={false} isAnimationActive={false} />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

// ---------------------------------------------------------------- carbon
export function CarbonStack({ rows }: { rows: { name: string; stack: number; power: number; biogenic: number }[] }) {
  const parts = [
    { key: "stack", label: "Stack (kiln + after-burner)", color: SERIES[0] },
    { key: "power", label: "Purchased power", color: SERIES[1] },
    { key: "biogenic", label: "Biogenic, reported separately", color: SERIES[2] },
  ].filter((p) => rows.some((r) => Math.abs(r[p.key as "stack"]) > 5e-4))
  return (
    <ResponsiveContainer width="100%" height={rows.length * 64 + 70}>
      <BarChart data={rows} layout="vertical" margin={{ top: 0, right: 24, bottom: 0, left: 0 }} barCategoryGap={18}>
        <CartesianGrid horizontal={false} stroke={INK.grid} />
        <XAxis type="number" {...AXIS} tickFormatter={(v) => num(v, 1)} />
        <YAxis type="category" dataKey="name" width={130} {...AXIS} tick={{ fill: INK.secondary, fontSize: 12 }} axisLine={false} />
        <Tooltip {...TIP} formatter={(v, n) => [`${num(Number(v), 3)} t CO₂/t`, parts.find((p) => p.key === n)?.label ?? String(n)]} />
        <Legend formatter={(v) => parts.find((p) => p.key === v)?.label ?? v} wrapperStyle={{ fontSize: 12, color: INK.secondary }} />
        {parts.map((p) => (
          <Bar key={p.key} dataKey={p.key} stackId="a" fill={p.color} stroke="#fcfcfb" strokeWidth={2} isAnimationActive={false}>
            <LabelList dataKey={p.key} position="center" formatter={(v: unknown) => (Number(v) > 0.12 ? num(Number(v), 2) : "")} style={{ fill: "#fff", fontSize: 11, fontWeight: 600 }} />
          </Bar>
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}
