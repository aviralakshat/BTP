"use client"

import NumberFlow from "@number-flow/react"
import { ArrowDownRight, ArrowUpRight, BarChart3, ChevronDown, Table2 } from "lucide-react"
import { useState, type ReactNode } from "react"
import { cn } from "@/lib/utils"

export function Card({
  title, subtitle, actions, children, className, bodyClassName,
}: {
  title?: ReactNode
  subtitle?: ReactNode
  actions?: ReactNode
  children: ReactNode
  className?: string
  bodyClassName?: string
}) {
  return (
    <section className={cn("rounded-xl border border-line bg-panel shadow-[0_1px_0_rgba(11,11,11,0.03)]", className)}>
      {(title || actions) && (
        <header className="flex items-start justify-between gap-4 border-b border-line px-5 py-3.5">
          <div className="min-w-0">
            {title && <h3 className="text-[13px] font-semibold tracking-[-0.005em] text-ink">{title}</h3>}
            {subtitle && <p className="mt-0.5 text-[12px] leading-snug text-ink-3">{subtitle}</p>}
          </div>
          {actions && <div className="shrink-0">{actions}</div>}
        </header>
      )}
      <div className={cn("p-5", bodyClassName)}>{children}</div>
    </section>
  )
}

export function Kpi({
  label, value, decimals = 0, prefix, unit, delta, deltaText, lowerIsBetter = true, hint,
}: {
  label: string
  value: number
  decimals?: number
  prefix?: string
  unit?: string
  delta?: number
  deltaText?: string
  lowerIsBetter?: boolean
  hint?: string
}) {
  const moved = delta != null && Math.abs(delta) > 1e-9
  const good = moved && (lowerIsBetter ? delta! < 0 : delta! > 0)
  return (
    <div className="flex min-w-0 flex-col rounded-xl border border-line bg-panel px-4 py-3.5">
      <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-ink-3">{label}</span>
      <div className="mt-1.5 flex items-baseline gap-1.5">
        <NumberFlow
          value={value}
          prefix={prefix}
          format={{ minimumFractionDigits: decimals, maximumFractionDigits: decimals }}
          locales="en-IN"
          className="tnum text-[26px] font-semibold leading-none tracking-[-0.03em] text-ink"
        />
        {unit && <span className="text-[12px] font-medium text-ink-3">{unit}</span>}
      </div>
      <div className="mt-2 min-h-[18px] text-[12px]">
        {moved ? (
          <span className={cn("inline-flex items-center gap-1 font-medium", good ? "text-[#0a7d0a]" : "text-bad")}>
            {delta! < 0 ? <ArrowDownRight className="size-3.5" /> : <ArrowUpRight className="size-3.5" />}
            {deltaText}
          </span>
        ) : (
          <span className="text-ink-3">{hint ?? ""}</span>
        )}
      </div>
    </div>
  )
}

export function Stat({ label, value, unit, hint, tone }: { label: string; value: string; unit?: string; hint?: string; tone?: "good" | "bad" }) {
  return (
    <div className="flex min-w-0 flex-col rounded-xl border border-line bg-panel px-4 py-3.5">
      <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-ink-3">{label}</span>
      <div className="mt-1.5 flex items-baseline gap-1.5">
        <span className={cn("tnum text-[26px] font-semibold leading-none tracking-[-0.03em]",
          tone === "good" ? "text-[#0a6b0a]" : tone === "bad" ? "text-bad" : "text-ink")}>{value}</span>
        {unit && <span className="text-[12px] font-medium text-ink-3">{unit}</span>}
      </div>
      <div className="mt-2 min-h-[18px] text-[12px] text-ink-3">{hint ?? ""}</div>
    </div>
  )
}

type Tone = "good" | "warn" | "bad" | "neutral" | "accent"
const TONE: Record<Tone, string> = {
  good: "bg-[#e8f5e8] text-[#0a6b0a] ring-[#0ca30c]/25",
  warn: "bg-[#fff5dc] text-[#8a5a00] ring-[#fab219]/40",
  bad: "bg-[#fbe9e9] text-[#a42a2a] ring-[#d03b3b]/30",
  neutral: "bg-[#efeee9] text-ink-2 ring-line-strong/50",
  accent: "bg-accent-soft text-accent-deep ring-accent/25",
}

export function Pill({ tone = "neutral", icon, children, className }: { tone?: Tone; icon?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-[11.5px] font-medium ring-1 ring-inset", TONE[tone], className)}>
      {icon}
      {children}
    </span>
  )
}

export function Segmented<T extends string | number>({
  options, value, onChange, size = "md", dark = false, ariaLabel,
}: {
  options: { value: T; label: ReactNode }[]
  value: T
  onChange: (v: T) => void
  size?: "sm" | "md"
  dark?: boolean
  ariaLabel?: string
}) {
  return (
    <div
      role="radiogroup"
      aria-label={ariaLabel}
      className={cn(
        "inline-flex w-full rounded-lg p-0.5",
        dark ? "bg-steel-3/70" : "bg-[#ecebe6]",
      )}
    >
      {options.map((o) => {
        const on = o.value === value
        return (
          <button
            key={String(o.value)}
            role="radio"
            aria-checked={on}
            onClick={() => onChange(o.value)}
            className={cn(
              "flex-1 rounded-md font-medium transition-colors focus-visible:outline-2 focus-visible:outline-accent",
              size === "sm" ? "px-2 py-1 text-[11.5px]" : "px-3 py-1.5 text-[12.5px]",
              dark
                ? on ? "bg-steel-ink text-steel shadow-sm" : "text-steel-mute hover:text-steel-ink"
                : on ? "bg-panel text-ink shadow-sm" : "text-ink-2 hover:text-ink",
            )}
          >
            {o.label}
          </button>
        )
      })}
    </div>
  )
}

export function RailSwitch({ label, hint, checked, onChange }: { label: string; hint?: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className="group flex w-full items-start justify-between gap-3 rounded-lg px-2 py-2 text-left transition-colors hover:bg-steel-2 focus-visible:outline-2 focus-visible:outline-accent"
    >
      <span className="min-w-0">
        <span className={cn("block text-[13px] font-medium", checked ? "text-white" : "text-steel-ink")}>{label}</span>
        {hint && <span className="mt-0.5 block text-[11.5px] leading-snug text-steel-mute">{hint}</span>}
      </span>
      <span className={cn("relative mt-0.5 h-[18px] w-8 shrink-0 rounded-full transition-colors", checked ? "bg-accent" : "bg-[#343b45]")}>
        <span className={cn("absolute top-[2px] size-[14px] rounded-full bg-white shadow transition-transform", checked ? "translate-x-[16px]" : "translate-x-[2px]")} />
      </span>
    </button>
  )
}

export function RailRange({
  label, value, min, max, step, onChange, display,
}: {
  label: string
  value: number
  min: number
  max: number
  step: number
  onChange: (v: number) => void
  display: string
}) {
  const fill = max > min ? ((value - min) / (max - min)) * 100 : 0
  return (
    <label className="block px-2 py-2">
      <span className="mb-2 flex items-center justify-between text-[13px]">
        <span className={cn("font-medium", value > min ? "text-white" : "text-steel-ink")}>{label}</span>
        <span className="tnum font-mono text-[12px] text-steel-ink">{display}</span>
      </span>
      <input
        type="range"
        className="rail-range"
        min={min}
        max={max}
        step={step}
        value={value}
        style={{ ["--fill" as string]: `${fill}%` }}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </label>
  )
}

export type Column<R> = {
  key: string
  label: string
  align?: "left" | "right"
  render?: (row: R) => ReactNode
  className?: string
}

export function DataTable<R extends Record<string, unknown>>({
  columns, rows, dense = false, maxHeight,
}: {
  columns: Column<R>[]
  rows: R[]
  dense?: boolean
  maxHeight?: number
}) {
  return (
    <div className="overflow-auto rounded-lg border border-line" style={maxHeight ? { maxHeight } : undefined}>
      <table className="w-full border-collapse text-[12.5px]">
        <thead className="sticky top-0 z-10 bg-[#f6f5f1]">
          <tr>
            {columns.map((c) => (
              <th
                key={c.key}
                className={cn(
                  "whitespace-nowrap border-b border-line px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-ink-3",
                  c.align === "right" ? "text-right" : "text-left",
                )}
              >
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-b border-line/70 last:border-0 hover:bg-[#f8f7f3]">
              {columns.map((c) => (
                <td
                  key={c.key}
                  className={cn(
                    dense ? "px-3 py-1.5" : "px-3 py-2",
                    c.align === "right" ? "tnum text-right font-mono text-[12px]" : "text-left",
                    "text-ink",
                    c.className,
                  )}
                >
                  {c.render ? c.render(r) : String(r[c.key] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/** Every chart ships a table twin: the palette's contrast note requires it. */
export function ChartCard<R extends Record<string, unknown>>({
  title, subtitle, children, columns, rows, className, footer,
}: {
  title: string
  subtitle?: string
  children: ReactNode
  columns: Column<R>[]
  rows: R[]
  className?: string
  footer?: ReactNode
}) {
  const [view, setView] = useState<"chart" | "table">("chart")
  return (
    <Card
      title={title}
      subtitle={subtitle}
      className={className}
      actions={
        <div className="flex rounded-md border border-line bg-[#f6f5f1] p-0.5" role="radiogroup" aria-label="View">
          {(["chart", "table"] as const).map((v) => (
            <button
              key={v}
              role="radio"
              aria-checked={view === v}
              aria-label={v === "chart" ? "Chart view" : "Table view"}
              onClick={() => setView(v)}
              className={cn("rounded px-1.5 py-1", view === v ? "bg-panel text-ink shadow-sm" : "text-ink-3 hover:text-ink")}
            >
              {v === "chart" ? <BarChart3 className="size-3.5" /> : <Table2 className="size-3.5" />}
            </button>
          ))}
        </div>
      }
    >
      {view === "chart" ? children : <DataTable columns={columns} rows={rows} dense maxHeight={420} />}
      {footer && <div className="mt-3 text-[12px] leading-relaxed text-ink-3">{footer}</div>}
    </Card>
  )
}

export function Disclosure({ title, children, defaultOpen = false }: { title: ReactNode; children: ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="rounded-lg border border-line">
      <button
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="flex w-full items-center justify-between px-3 py-2 text-left text-[12.5px] font-medium text-ink-2 hover:text-ink"
      >
        {title}
        <ChevronDown className={cn("size-4 transition-transform", open && "rotate-180")} />
      </button>
      {open && <div className="border-t border-line px-3 py-2.5 text-[12.5px] leading-relaxed text-ink-2">{children}</div>}
    </div>
  )
}

export function SectionHead({ eyebrow, title, description, actions }: { eyebrow: string; title: string; description?: string; actions?: ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
      <div className="max-w-3xl">
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-accent">{eyebrow}</p>
        <h2 className="mt-1 text-[22px] font-semibold tracking-[-0.02em] text-ink">{title}</h2>
        {description && <p className="mt-1.5 text-[13.5px] leading-relaxed text-ink-2">{description}</p>}
      </div>
      {actions}
    </div>
  )
}
