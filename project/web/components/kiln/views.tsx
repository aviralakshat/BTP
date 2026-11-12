"use client"

import { ArrowRight, CheckCircle2, CircleAlert, Download, Search } from "lucide-react"
import { useMemo, useState } from "react"
import type { Controls, Finance, IrrStatus, Meta, ParamsResp, Pathways, Scenario } from "@/lib/api"
import { PROVENANCE, VERDICT, inr, num, pct, sentence, signed } from "@/lib/format"
import { cn } from "@/lib/utils"
import { AxialChart, CarbonStack, CashFlowChart, CostBars, EnergyBars, MassSankey, PathwayScatter } from "./charts"
import { KilnSchematic } from "./schematic"
import { Card, ChartCard, DataTable, Disclosure, Kpi, Pill, SectionHead, Segmented, Stat } from "./ui"

type Common = { sc: Scenario; hasRetrofit: boolean }

function KpiRow({ sc, hasRetrofit }: Common) {
  const k = sc.kpi
  const b = sc.base
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
      <Kpi label="Cost per tonne" value={k.cost} prefix="₹" delta={hasRetrofit ? k.cost - b.cost : undefined}
        deltaText={`${inr(Math.abs(k.cost - b.cost))} vs kiln alone`} hint="Plant-gate, incl. annualised capital" />
      <Kpi label="CO₂ intensity" value={k.co2_total} decimals={2} unit="t / t DRI" delta={hasRetrofit ? k.co2_total - b.co2_total : undefined}
        deltaText={`${num(Math.abs(k.co2_total - b.co2_total), 2)} t vs kiln alone`} hint="Stack plus purchased power" />
      <Kpi label="Coal rate" value={k.coal_rate} decimals={3} unit="t / t DRI" delta={hasRetrofit ? k.coal_rate - b.coal_rate : undefined}
        deltaText={`${num(Math.abs(k.coal_rate - b.coal_rate), 3)} t vs kiln alone`} hint={sc.status.coal_solved ? "Solved from the heat balance" : "Specified input"} />
      <Kpi label="Specific energy" value={k.sec_gcal} decimals={2} unit="Gcal / t" hint="Coal heating value in" />
      <Kpi label="Output" value={k.output_tpd} decimals={0} unit="t / day" lowerIsBetter={false} hint={`${num(k.annual_output / 1000, 1)} kt per year`} />
    </div>
  )
}

function CheckStrip({ checks }: { checks: Scenario["checks"] }) {
  return (
    <div>
      <div className="flex gap-1" role="list" aria-label="Literature checks">
        {checks.map((c) => {
          const v = VERDICT[c.verdict]
          return (
            <div key={c.key} role="listitem" className="group relative flex-1">
              <div className="h-8 rounded-[3px] transition-opacity group-hover:opacity-80" style={{ background: v.color, opacity: c.verdict === "INFO" ? 0.35 : 1 }}
                aria-label={`${c.label}: ${v.label}`} />
              <div className="pointer-events-none absolute bottom-10 left-1/2 z-20 hidden w-56 -translate-x-1/2 rounded-lg border border-line bg-panel p-2.5 text-[11.5px] shadow-lg group-hover:block">
                <div className="font-semibold text-ink">{c.label}</div>
                <div className="mt-0.5 text-ink-2"><span style={{ color: v.color }}>{v.glyph}</span> {v.label}</div>
                <div className="text-ink-2">Plant value {num(c.model, 3)} {c.unit}</div>
                {c.min != null && c.max != null && <div className="text-ink-3">Published range {num(c.min, 3)} to {num(c.max, 3)}</div>}
              </div>
            </div>
          )
        })}
      </div>
      <div className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1 text-[11.5px] text-ink-3">
        {(["PASS", "WARN", "FAIL", "INFO"] as const).map((k) => (
          <span key={k} className="inline-flex items-center gap-1.5">
            <span style={{ color: VERDICT[k].color }}>{VERDICT[k].glyph}</span>{VERDICT[k].label}
            <span className="tnum font-semibold text-ink-2">{checks.filter((c) => c.verdict === k).length}</span>
          </span>
        ))}
      </div>
    </div>
  )
}

// ======================================================================== Overview
export function Overview({
  sc, hasRetrofit, pw, target, setTarget, onApply, meta,
}: Common & { pw: Pathways | null; target: number; setTarget: (t: number) => void; onApply: (whr: boolean, biomass: number, h2: number) => void; meta: Meta }) {
  const rec = pw?.roadmap.find((r) => Math.abs(r.target - target) < 1e-9)
  const st = sc.status
  return (
    <div className="space-y-5">
      <SectionHead eyebrow="Overview" title="Plant performance and least-cost decarbonisation"
        description="Operating cost, carbon intensity and fuel use, solved from the plant's mass and heat balances and updated as you change the controls." />
      <KpiRow sc={sc} hasRetrofit={hasRetrofit} />

      <div className="grid gap-5 xl:grid-cols-[1.25fr_1fr]">
        <Card title="Decarbonisation planner" subtitle="Waste-heat power, rice husk and hydrogen are optimised as one system. The recommendation is the lowest-cost mix that meets the target."
          actions={<span className="text-[11.5px] text-ink-3">Maximum achievable cut {pct(pw?.max_cut ?? 0)}</span>}>
          <div className="mb-4">
            <div className="mb-2 text-[12px] font-medium text-ink-2">CO₂ reduction target</div>
            <Segmented ariaLabel="CO2 reduction target" value={target} onChange={setTarget}
              options={meta.targets.map((t) => ({ value: t, label: `${Math.round(t * 100)}%` }))} />
          </div>
          {!pw && <div className="h-40 animate-pulse rounded-lg bg-[#efeee9]" />}
          {pw && rec && rec.label ? (
            <div className="rounded-lg border border-line bg-gradient-to-br from-accent-soft/70 to-transparent p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="text-[11px] font-semibold uppercase tracking-[0.12em] text-accent-deep">Recommended mix</div>
                  <div className="mt-1 text-[19px] font-semibold tracking-[-0.015em] text-ink">{sentence(rec.label)}</div>
                </div>
                <button onClick={() => onApply(!!rec.whr, rec.biomass ?? 0, rec.h2 ?? 0)}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-accent-deep px-3.5 py-2 text-[12.5px] font-medium text-white shadow-sm transition-colors hover:bg-[#0d366b] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent">
                  Apply to plant <ArrowRight className="size-3.5" />
                </button>
              </div>
              <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
                {[
                  ["Cost per tonne", inr(rec.cost)],
                  ["Change vs kiln alone", `${signed(rec.cost_delta ?? 0)} ₹/t`],
                  ["CO₂ removed", pct(rec.co2_cut ?? 0, 1)],
                  ["Simple payback", rec.payback != null && rec.payback < 50 ? `${num(rec.payback, 1)} yr` : "—"],
                ].map(([k, v]) => (
                  <div key={k}>
                    <dt className="text-[11px] uppercase tracking-[0.06em] text-ink-3">{k}</dt>
                    <dd className="tnum mt-1 text-[16px] font-semibold text-ink">{v}</dd>
                  </div>
                ))}
              </dl>
              <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-[12px] text-ink-3">
                <span>Capital required <span className="tnum font-medium text-ink-2">{inr(rec.capex ?? 0, true)}</span></span>
                <span>Abatement cost <span className="tnum font-medium text-ink-2">{rec.abatement != null ? `${inr(rec.abatement)} per t CO₂` : "—"}</span></span>
              </div>
            </div>
          ) : pw ? (
            <div className="rounded-lg border border-line p-4 text-[13px] text-ink-2">
              A {Math.round(target * 100)}% reduction is not achievable with these levers at this plant. Beyond their substitution limits the kiln has too little carbon to reduce the ore. The maximum achievable cut is {pct(pw.max_cut)}.
            </div>
          ) : null}
        </Card>

        <Card title="Model health" subtitle="Mass and heat balances are checked on every run. Outputs are benchmarked against independent published plant data.">
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "Mass balance", value: `${num(st.mass_closure, 2)}%`, ok: st.mass_ok, note: `Residual, limit ${num(st.mass_tolerance, 0)}%` },
              { label: "Heat balance", value: `${num(st.energy_closure, 2)}%`, ok: st.energy_ok, note: "Residual" },
              { label: "Reductant carbon", value: `${num(st.reductant_ratio, 2)}×`, ok: st.feasible, note: "Of the minimum needed to reduce the ore" },
              { label: "Benchmarks", value: `${st.checks_pass}/${st.checks_scored}`, ok: st.checks_fail === 0, note: "Within published ranges" },
            ].map((m) => (
              <div key={m.label} className="rounded-lg border border-line px-3 py-2.5">
                <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.06em] text-ink-3">
                  {m.label}
                  {m.ok ? <CheckCircle2 className="size-3.5 text-good" aria-label="Within limits" /> : <CircleAlert className="size-3.5 text-bad" aria-label="Outside limits" />}
                </div>
                <div className="tnum mt-1 text-[18px] font-semibold text-ink">{m.value}</div>
                <div className="text-[11.5px] text-ink-3">{m.note}</div>
              </div>
            ))}
          </div>
          <div className="mt-4">
            <div className="mb-2 text-[12px] font-medium text-ink-2">Benchmark results</div>
            <CheckStrip checks={sc.checks} />
          </div>
        </Card>
      </div>

      <Card title="Process at a glance" subtitle="Per tonne of sponge iron. Ore, air, coal and waste gas are calculated from the balances.">
        <KilnSchematic flows={sc.flows} co2={sc.kpi.co2_total} />
      </Card>
    </div>
  )
}

// ======================================================================== Process
export function Process({ sc }: Common) {
  const ledger = sc.energy.filter((e) => !e.is_input)
  return (
    <div className="space-y-5">
      <SectionHead eyebrow="Process" title="Material and heat flows through the kiln"
        description={`Kiln boundary, per tonne of sponge iron. Mass balance residual ${num(sc.status.mass_closure, 2)}%, heat balance residual ${num(sc.status.energy_closure, 2)}%. Residuals are shown as calculated, with no adjustment.`} />
      <ChartCard title="Material flow" subtitle="kg per tonne of sponge iron. Combustion air and waste gas are the largest streams, as on an operating kiln."
        columns={[
          { key: "name", label: "Stream" },
          { key: "direction", label: "Direction", render: (r) => (r.direction === "in" ? "Input" : "Output") },
          { key: "kg", label: "kg / t DRI", align: "right", render: (r) => num(r.kg, 1) },
          { key: "tpd", label: "t / day", align: "right", render: (r) => num(r.tpd, 2) },
        ]}
        rows={sc.streams}>
        <MassSankey streams={sc.streams} />
      </ChartCard>

      <div className="grid gap-5 xl:grid-cols-2">
        <ChartCard title="Where the coal's heat goes" subtitle={`Distribution of ${num(sc.kpi.sec_gcal, 2)} Gcal/t of coal heat input. Volatiles burnt in the after-burner chamber are recoverable as waste-heat power.`}
          columns={[
            { key: "group", label: "Group" },
            { key: "item", label: "Item" },
            { key: "gcal", label: "Gcal / t", align: "right", render: (r) => num(r.gcal, 3) },
            { key: "pct", label: "% of coal heat", align: "right", render: (r) => num(r.pct, 1) },
          ]}
          rows={ledger}>
          <EnergyBars energy={sc.energy} />
        </ChartCard>

        <ChartCard title="Temperature along the kiln" subtitle={`${num(sc.kiln.length_m, 0)} m kiln, ${num(sc.kiln.diameter_m, 2)} m internal diameter, ${num(sc.kiln.incline_deg, 1)}° incline. Profile anchored to measured end temperatures.`}
          columns={[
            { key: "z", label: "Distance (m)", align: "right", render: (r) => num(r.z, 1) },
            { key: "zone", label: "Zone", render: (r) => (r.zone === "preheat" ? "Pre-heating" : "Reduction") },
            { key: "gas", label: "Gas °C", align: "right", render: (r) => num(r.gas, 0) },
            { key: "solid", label: "Bed °C", align: "right", render: (r) => num(r.solid, 0) },
            { key: "met", label: "Metallisation %", align: "right", render: (r) => num(r.met, 1) },
          ]}
          rows={sc.kiln.cells}>
          <AxialChart cells={sc.kiln.cells} />
        </ChartCard>
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.2fr_1fr]">
        <Card title="Element balance" subtitle="Inputs and outputs of each element, checked against the closure tolerance.">
          <DataTable dense rows={sc.elements} columns={[
            { key: "element", label: "Element" },
            { key: "in", label: "In kg/t", align: "right", render: (r) => num(r.in, 2) },
            { key: "out", label: "Out kg/t", align: "right", render: (r) => num(r.out, 2) },
            { key: "error", label: "Error %", align: "right", render: (r) => num(r.error, 3) },
            { key: "ok", label: "Status", render: (r) => (r.ok ? <Pill tone="good">● Closed</Pill> : <Pill tone="bad">■ Open</Pill>) },
          ]} />
        </Card>
        <Card title="Waste-gas composition" subtitle="At the kiln outlet, upstream of the after-burner chamber.">
          <DataTable dense rows={sc.waste_gas} columns={[
            { key: "species", label: "Species" },
            { key: "kg", label: "kg / t DRI", align: "right", render: (r) => num(r.kg, 1) },
          ]} />
        </Card>
      </div>
    </div>
  )
}

// ======================================================================== Pathways
export function PathwaysView({ pw, onApply }: { pw: Pathways | null; onApply: (whr: boolean, biomass: number, h2: number) => void }) {
  const [selected, setSelected] = useState<string | null>(null)
  if (!pw) return <div className="h-96 animate-pulse rounded-xl bg-[#efeee9]" />
  const feasible = pw.rows.filter((r) => r.feasible).length
  return (
    <div className="space-y-5">
      <SectionHead eyebrow="Pathways" title="Retrofit combinations, costed as one plant"
        description="Every combination of waste-heat power, rice husk and hydrogen is solved as a single plant, so interactions between levers are captured. Combinations that leave too little carbon to reduce the ore are excluded." />
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Kpi label="Combinations solved" value={pw.rows.length} />
        <Kpi label="Technically feasible" value={feasible} hint="Enough carbon to reduce the ore" lowerIsBetter={false} />
        <Kpi label="Maximum CO₂ cut" value={pw.max_cut * 100} decimals={0} unit="%" lowerIsBetter={false} />
        <Kpi label="Hydrogen break-even" value={pw.h2_breakeven} prefix="₹" unit="/ kg" hint={`Current price ${inr(pw.h2_price)}/kg`} />
      </div>

      <ChartCard title="Cost against CO₂ removed" subtitle="Each point is one combination. The dark line traces the lowest cost at each level of reduction."
        columns={[
          { key: "label", label: "Mix", render: (r) => sentence(String(r.label)) },
          { key: "feasible", label: "Workable", render: (r) => (r.feasible ? "Yes" : "No") },
          { key: "co2_cut", label: "CO₂ cut", align: "right", render: (r) => pct(Number(r.co2_cut), 1) },
          { key: "cost", label: "₹ / t", align: "right", render: (r) => inr(Number(r.cost)) },
          { key: "cost_delta", label: "Δ ₹ / t", align: "right", render: (r) => signed(Number(r.cost_delta)) },
          { key: "capex", label: "Capital", align: "right", render: (r) => inr(Number(r.capex), true) },
        ]}
        rows={[...pw.rows].sort((a, b) => a.co2_cut - b.co2_cut)}>
        <PathwayScatter rows={pw.rows} selected={selected} />
      </ChartCard>

      <Card title="Decarbonisation roadmap" subtitle="Lowest-cost feasible mix for each reduction target. Select a row to locate it on the chart, or apply it to the plant." bodyClassName="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-[12.5px]">
            <thead className="bg-[#f6f5f1]">
              <tr className="text-[11px] uppercase tracking-[0.06em] text-ink-3">
                {["Target", "Mix", "Cut", "Δ ₹ / t", "₹ / t CO₂", "Capital", "Payback", ""].map((h, i) => (
                  <th key={h + i} className={cn("border-b border-line px-4 py-2 font-semibold", i >= 2 && i <= 6 ? "text-right" : "text-left")}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pw.roadmap.map((r) => (
                <tr key={r.target} onClick={() => r.label && setSelected(r.label)}
                  className={cn("cursor-pointer border-b border-line/70 last:border-0 hover:bg-[#f8f7f3]", selected === r.label && r.label && "bg-accent-soft/60")}>
                  <td className="px-4 py-2.5 font-semibold text-ink">{Math.round(r.target * 100)}%</td>
                  {r.label ? (
                    <>
                      <td className="px-4 py-2.5 text-ink">{sentence(r.label)}</td>
                      <td className="tnum px-4 py-2.5 text-right font-mono text-[12px]">{pct(r.co2_cut ?? 0, 1)}</td>
                      <td className="tnum px-4 py-2.5 text-right font-mono text-[12px]">{signed(r.cost_delta ?? 0)}</td>
                      <td className="tnum px-4 py-2.5 text-right font-mono text-[12px]">{r.abatement != null ? signed(r.abatement) : "—"}</td>
                      <td className="tnum px-4 py-2.5 text-right font-mono text-[12px]">{r.capex ? inr(r.capex, true) : "—"}</td>
                      <td className="tnum px-4 py-2.5 text-right font-mono text-[12px]">{r.payback != null && r.payback < 50 ? `${num(r.payback, 1)} yr` : "—"}</td>
                      <td className="px-4 py-2.5 text-right">
                        <button onClick={(e) => { e.stopPropagation(); onApply(!!r.whr, r.biomass ?? 0, r.h2 ?? 0) }}
                          className="rounded-md border border-line px-2.5 py-1 text-[12px] font-medium text-accent-deep hover:border-accent hover:bg-accent-soft">Apply</button>
                      </td>
                    </>
                  ) : (
                    <td colSpan={7} className="px-4 py-2.5 text-ink-3">Not achievable with these levers</td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}

// ======================================================================== Economics
function irrText(irr: number | null, status: IrrStatus) {
  if (irr != null) return pct(irr, 1)
  return status === "multiple" ? "Multiple" : status === "no_investment" ? "n/a" : "None"
}

const IRR_NOTE: Record<IrrStatus, string> = {
  unique: "",
  none: "Cash flow does not recover the investment",
  multiple: "Cash flow changes sign more than once; use NPV",
  no_investment: "No capital outlay",
}

const years = (v: number | null, status?: IrrStatus) =>
  v != null ? num(v, 1) : status === "no_investment" ? "Immediate" : "Beyond life"

function FinancePanel({ f }: { f: Finance }) {
  const t = f.terms
  const gap = f.levelised.financed != null && f.levelised.annuity != null ? f.levelised.financed - f.levelised.annuity : null
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3 pt-2">
        <div>
          <h3 className="text-[16px] font-semibold tracking-[-0.01em] text-ink">Retrofit financing</h3>
          <p className="mt-1 max-w-3xl text-[13px] leading-relaxed text-ink-2">
            Investment case for the active retrofits, valued on the operating saving against the baseline plant. {pct(t.debt_fraction)} debt at {pct(t.interest, 1)} over {t.tenor} years, corporate tax {pct(t.tax, 2)}, operating cost escalating {pct(t.escalation)} a year, discounted at {pct(t.discount)} over {t.life} years.
          </p>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <Stat label="Equity NPV" value={inr(f.npv, true)} tone={f.npv >= 0 ? "good" : "bad"} hint={`On ${inr(f.equity, true)} equity`} />
        <Stat label="Equity IRR" value={irrText(f.irr, f.irr_status)} hint={IRR_NOTE[f.irr_status] || "After debt service and tax"} />
        <Stat label="Project IRR" value={irrText(f.project_irr, f.project_irr_status)} hint={IRR_NOTE[f.project_irr_status] || `Unlevered, on ${inr(f.capex, true)}`} />
        <Stat label="Payback" value={years(f.payback, f.npv > 0 ? f.irr_status : undefined)} unit={f.payback != null ? "yr" : undefined} hint="Equity, undiscounted" />
        <Stat label="Discounted payback" value={years(f.discounted_payback, f.npv > 0 ? f.irr_status : undefined)} unit={f.discounted_payback != null ? "yr" : undefined} hint={`At ${pct(t.discount)}`} />
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.4fr_1fr]">
        <ChartCard title="Equity cash flow" subtitle={`Annual saving ${inr(f.annual_saving, true)} against ${inr(f.annual_opex, true)} added operating cost in year one. Debt service ends after year ${t.tenor}.`}
          columns={[
            { key: "year", label: "Year", render: (r) => (r.year === 0 ? "0" : String(r.year)) },
            { key: "ebitda", label: "EBITDA", align: "right", render: (r) => inr(r.ebitda, true) },
            { key: "interest", label: "Interest", align: "right", render: (r) => inr(r.interest, true) },
            { key: "principal", label: "Principal", align: "right", render: (r) => inr(r.principal, true) },
            { key: "tax", label: "Tax", align: "right", render: (r) => inr(r.tax, true) },
            { key: "equity_cf", label: "Equity cash", align: "right", render: (r) => inr(r.equity_cf, true) },
            { key: "cumulative", label: "Cumulative", align: "right", render: (r) => inr(r.cumulative, true) },
          ]}
          rows={f.years}>
          <CashFlowChart years={f.years} />
        </ChartCard>

        <Card title="Downside stress test" subtitle="Equity returns under adverse capital, saving and interest outcomes." bodyClassName="p-0">
          <table className="w-full text-[12.5px]">
            <thead className="bg-[#f6f5f1]">
              <tr className="text-[11px] uppercase tracking-[0.06em] text-ink-3">
                {["Case", "Equity NPV", "IRR", "Payback"].map((h, i) => (
                  <th key={h} className={cn("border-b border-line px-4 py-2 font-semibold", i ? "text-right" : "text-left")}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {f.stress.map((s, i) => (
                <tr key={s.case} className={cn("border-b border-line/70 last:border-0", i === 0 && "bg-accent-soft/40")}>
                  <td className="px-4 py-2.5 text-ink">{s.case}</td>
                  <td className="tnum px-4 py-2.5 text-right font-mono text-[12px]">
                    <span className={s.npv >= 0 ? "text-[#0a6b0a]" : "text-bad"}>{s.npv >= 0 ? "▲" : "▼"}</span> {inr(s.npv, true)}
                  </td>
                  <td className="tnum px-4 py-2.5 text-right font-mono text-[12px]">{irrText(s.irr, s.irr_status)}</td>
                  <td className="tnum px-4 py-2.5 text-right font-mono text-[12px]">{s.payback != null ? `${num(s.payback, 1)} yr` : years(null, s.npv > 0 ? s.irr_status : undefined)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <dl className="grid grid-cols-2 gap-4 border-t border-line px-4 py-3.5 text-[12px]">
            <div>
              <dt className="text-ink-3">Capital charge, annuity basis</dt>
              <dd className="tnum mt-0.5 text-[14px] font-semibold text-ink">{f.levelised.annuity != null ? `${inr(f.levelised.annuity)} / t` : "—"}</dd>
            </div>
            <div>
              <dt className="text-ink-3">Levelised cost, financed</dt>
              <dd className="tnum mt-0.5 text-[14px] font-semibold text-ink">
                {f.levelised.financed != null ? `${inr(f.levelised.financed)} / t` : "—"}
                {gap != null && <span className="ml-1.5 text-[11.5px] font-normal text-ink-3">({signed(gap)})</span>}
              </dd>
            </div>
          </dl>
        </Card>
      </div>
    </div>
  )
}

export function Economics({ sc, hasRetrofit }: Common) {
  const k = sc.kpi
  const rows = [
    ...(hasRetrofit
      ? [{ name: "Kiln alone", stack: sc.base.co2_direct, power: sc.base.co2_scope2, biogenic: sc.base.co2_biogenic }]
      : []),
    { name: hasRetrofit ? "With retrofits" : "Current plant", stack: k.co2_direct, power: k.co2_scope2, biogenic: k.co2_biogenic },
  ]
  return (
    <div className="space-y-5">
      <SectionHead eyebrow="Economics & carbon" title="Cost per tonne, project returns and carbon sources"
        description="Retrofit capital is annualised into the cost per tonne so it can be compared directly with coal and power. Project returns are modelled separately, with debt, tax and cost escalation. CO₂ is taken from the plant's carbon balance." />
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Kpi label="Cash cost" value={k.cash_cost} prefix="₹" unit="/ t" hint="Operating cost, excluding capital" />
        <Kpi label="Capital charge" value={k.capex_charge} prefix="₹" unit="/ t" hint="Retrofit capital, annualised" />
        <Kpi label="Stack CO₂" value={k.co2_direct} decimals={3} unit="t / t" hint="Kiln and after-burner" />
        <Kpi label="Grid power" value={k.grid_kwh} decimals={0} unit="kWh / t" hint={k.export_kwh > 0 ? `${num(k.export_kwh, 0)} kWh/t exported` : "Net import"} />
      </div>
      <div className="grid gap-5 xl:grid-cols-2">
        <ChartCard title="Cost build-up per tonne" subtitle="Costs in blue. Credits, such as exported power, in orange."
          columns={[{ key: "item", label: "Line item" }, { key: "inr", label: "₹ / t", align: "right", render: (r) => inr(r.inr) }]}
          rows={sc.cost_lines}>
          <CostBars lines={sc.cost_lines} />
        </ChartCard>
        <ChartCard title="CO₂ intensity by source" subtitle="Tonnes of CO₂ per tonne of sponge iron."
          columns={[
            { key: "name", label: "Case" },
            { key: "stack", label: "Stack", align: "right", render: (r) => num(r.stack, 3) },
            { key: "power", label: "Power", align: "right", render: (r) => num(r.power, 3) },
            { key: "biogenic", label: "Biogenic", align: "right", render: (r) => num(r.biogenic, 3) },
          ]}
          rows={rows}>
          <CarbonStack rows={rows} />
        </ChartCard>
      </div>

      {sc.finance && <FinancePanel f={sc.finance} />}

      <Card title="Active retrofits" subtitle={hasRetrofit ? "Performance of each lever on this plant." : "No retrofit is active. Enable one in the control rail, or apply a recommended mix from the Overview."}>
        {hasRetrofit ? (
          <div className="grid gap-4 lg:grid-cols-2">
            {sc.retrofits.map((r) => (
              <div key={r.name} className="rounded-lg border border-line p-4">
                <div className="mb-2 text-[13px] font-semibold text-ink">{r.name}</div>
                <dl className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[12px]">
                  {r.metrics.slice(0, 8).map((m) => (
                    <div key={m.label} className="flex justify-between gap-2 border-b border-line/60 pb-1">
                      <dt className="truncate text-ink-3" title={m.label}>{m.label}</dt>
                      <dd className="tnum font-mono text-ink">{typeof m.value === "boolean" ? (m.value ? "Yes" : "No") : num(Number(m.value), Math.abs(Number(m.value)) >= 100 ? 0 : 3)}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-[13px] text-ink-3">The plant is running at baseline.</div>
        )}
        {sc.basis.length > 0 && (
          <div className="mt-4">
            <Disclosure title={`Basis of estimate (${sc.basis.length})`}>
              <ul className="list-disc space-y-1.5 pl-4">
                {sc.basis.map((b) => <li key={b}>{b}</li>)}
              </ul>
            </Disclosure>
          </div>
        )}
      </Card>
    </div>
  )
}

// ======================================================================== Evidence
export function Evidence({ sc, params, meta }: { sc: Scenario; params: ParamsResp | null; meta: Meta }) {
  const [q, setQ] = useState("")
  const [status, setStatus] = useState<string>("all")
  const rows = useMemo(() => {
    if (!params) return []
    const s = q.trim().toLowerCase()
    return params.rows.filter((r) =>
      (status === "all" || r.status === status) &&
      (!s || r.name.toLowerCase().includes(s) || r.key.toLowerCase().includes(s) || r.source.toLowerCase().includes(s)))
  }, [params, q, status])
  const download = () => {
    if (!params) return
    const head = ["parameter", "key", "value", "unit", "min", "max", "status", "source"]
    const esc = (v: unknown) => `"${String(v ?? "").replace(/"/g, '""')}"`
    const csv = [head.join(","), ...params.rows.map((r) => [r.name, r.key, r.value, r.unit, r.min, r.max, r.status, r.source].map(esc).join(","))].join("\n")
    const a = document.createElement("a")
    a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }))
    a.download = "parameter_register.csv"
    a.click()
  }
  return (
    <div className="space-y-5">
      <SectionHead eyebrow="Evidence" title="Validation and data provenance"
        description={`Model ${meta.version}. Each output is benchmarked against an independent published range. No benchmark is used as a model input, so a result in range is genuine evidence.`} />
      <Card title="Benchmark results" subtitle="Position of each plant output within its published operating range." bodyClassName="p-0">
        <div className="divide-y divide-line">
          {sc.checks.map((c) => {
            const v = VERDICT[c.verdict]
            const span = c.min != null && c.max != null ? c.max - c.min || 1 : null
            const pos = span != null ? Math.min(1.25, Math.max(-0.25, (c.model - (c.min as number)) / span)) : null
            return (
              <div key={c.key} className="grid items-center gap-3 px-5 py-3 md:grid-cols-[1.6fr_1.3fr_0.9fr]">
                <div className="min-w-0">
                  <div className="text-[13px] font-medium text-ink">{c.label}</div>
                  <div className="truncate text-[11.5px] text-ink-3" title={c.source}>{c.source}</div>
                </div>
                <div className="relative h-6" aria-hidden>
                  <div className="absolute inset-y-2 left-[16.6%] right-[16.6%] rounded-full bg-accent-soft ring-1 ring-inset ring-accent/20" />
                  {pos != null && (
                    <div className="absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full ring-2 ring-panel"
                      style={{ left: `${16.6 + pos * 66.8}%`, background: v.color }} />
                  )}
                </div>
                <div className="flex items-center justify-end gap-3 text-right">
                  <span className="tnum font-mono text-[12px] text-ink">{num(c.model, 3)} <span className="text-ink-3">{c.unit}</span></span>
                  <Pill tone={c.verdict === "PASS" ? "good" : c.verdict === "WARN" ? "warn" : c.verdict === "FAIL" ? "bad" : "neutral"}>
                    {v.glyph} {v.label}
                  </Pill>
                </div>
              </div>
            )
          })}
        </div>
      </Card>

      <Card title="Parameter register"
        subtitle={params ? `${params.summary.total} parameters, ${params.summary.verified ?? 0} verified against a published source and ${params.summary.needs_citation ?? 0} awaiting a source.` : "Loading"}
        actions={
          <button onClick={download} className="inline-flex items-center gap-1.5 rounded-md border border-line px-2.5 py-1.5 text-[12px] font-medium text-ink-2 hover:text-ink">
            <Download className="size-3.5" /> CSV
          </button>
        }>
        <div className="mb-3 flex flex-wrap gap-3">
          <label className="relative min-w-[240px] flex-1">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-ink-3" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search coal, hydrogen, waste heat, a source…"
              className="w-full rounded-lg border border-line bg-panel py-2 pl-8 pr-3 text-[13px] outline-none placeholder:text-ink-3 focus:border-accent focus:ring-2 focus:ring-accent/20" />
          </label>
          <select value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Filter by status"
            className="rounded-lg border border-line bg-panel px-3 py-2 text-[13px] outline-none focus:border-accent">
            <option value="all">All statuses</option>
            {Object.entries(PROVENANCE).map(([k, v]) => <option key={k} value={k}>{v.glyph} {v.label}</option>)}
          </select>
        </div>
        <DataTable dense maxHeight={520} rows={rows} columns={[
          { key: "name", label: "Parameter", render: (r) => <span title={r.key}>{r.name}</span> },
          { key: "value", label: "Value", align: "right", render: (r) => (typeof r.value === "number" ? num(r.value, Math.abs(r.value) >= 100 ? 0 : 4) : String(r.value ?? "")) },
          { key: "unit", label: "Unit", className: "text-ink-3" },
          { key: "range", label: "Range", align: "right", render: (r) => (r.min != null && r.max != null ? `${num(r.min, 3)} – ${num(r.max, 3)}` : "—") },
          { key: "status", label: "Status", render: (r) => <span className="whitespace-nowrap text-ink-2">{PROVENANCE[r.status]?.glyph} {PROVENANCE[r.status]?.label ?? r.status}</span> },
          { key: "source", label: "Source", render: (r) => <span className="line-clamp-2 max-w-[420px] text-ink-2" title={r.source}>{r.source}</span> },
        ]} />
        <div className="mt-2 text-[11.5px] text-ink-3">Showing {rows.length} of {params?.rows.length ?? 0}</div>
      </Card>
    </div>
  )
}

export type { Controls }
