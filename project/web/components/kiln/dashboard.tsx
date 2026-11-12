"use client"

import { Activity, CircleAlert, CircleCheck, Factory, Flame, Gauge, Layers, Menu, RotateCcw, ShieldCheck, X } from "lucide-react"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { DEFAULT_CONTROLS, getJSON, postJSON, type Controls, type Meta, type ParamsResp, type Pathways, type Scenario } from "@/lib/api"
import { num } from "@/lib/format"
import { cn } from "@/lib/utils"
import { Pill, RailRange, RailSwitch, Segmented } from "./ui"
import { Economics, Evidence, Overview, PathwaysView, Process } from "./views"

const TABS = [
  { id: "overview", label: "Overview", icon: Gauge },
  { id: "process", label: "Process", icon: Flame },
  { id: "pathways", label: "Pathways", icon: Activity },
  { id: "economics", label: "Economics", icon: Layers },
  { id: "evidence", label: "Evidence", icon: ShieldCheck },
] as const
type TabId = (typeof TABS)[number]["id"]

function RailSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border-t border-steel-3 px-3 py-4 first:border-t-0">
      <div className="mb-2 px-2 text-[10.5px] font-semibold uppercase tracking-[0.16em] text-steel-mute">{title}</div>
      <div className="space-y-1">{children}</div>
    </div>
  )
}

export function Dashboard() {
  const [meta, setMeta] = useState<Meta | null>(null)
  const [controls, setControls] = useState<Controls>(DEFAULT_CONTROLS)
  const [sc, setSc] = useState<Scenario | null>(null)
  const [pw, setPw] = useState<Pathways | null>(null)
  const [params, setParams] = useState<ParamsResp | null>(null)
  const [tab, setTab] = useState<TabId>("overview")
  const [target, setTarget] = useState(0.2)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [railOpen, setRailOpen] = useState(false)
  const scAbort = useRef<AbortController | null>(null)
  const pwAbort = useRef<AbortController | null>(null)

  const set = useCallback(<K extends keyof Controls>(k: K, v: Controls[K]) => setControls((c) => ({ ...c, [k]: v })), [])

  useEffect(() => {
    getJSON<Meta>("/meta")
      .then((m) => {
        setMeta(m)
        setControls((c) => ({ ...c, utilization: m.utilization }))
      })
      .catch(() => setError("offline"))
    getJSON<ParamsResp>("/parameters").then(setParams).catch(() => undefined)
  }, [])

  useEffect(() => {
    if (!meta) return
    const t = setTimeout(() => {
      scAbort.current?.abort()
      const ac = new AbortController()
      scAbort.current = ac
      setBusy(true)
      postJSON<Scenario>("/scenario", controls, ac.signal)
        .then((s) => { setSc(s); setError(null) })
        .catch((e) => { if (e.name !== "AbortError") setError("offline") })
        .finally(() => { if (scAbort.current === ac) setBusy(false) })
    }, 180)
    return () => clearTimeout(t)
  }, [controls, meta])

  const baseKey = useMemo(
    () => JSON.stringify([controls.preset, controls.capacity, controls.utilization, controls.coal_mode, controls.coal_rate, controls.biogenic_zero, controls.h2_source]),
    [controls],
  )
  useEffect(() => {
    if (!meta) return
    const t = setTimeout(() => {
      pwAbort.current?.abort()
      const ac = new AbortController()
      pwAbort.current = ac
      postJSON<Pathways>("/pathways", { ...controls, whr: false, biomass: 0, h2: 0 }, ac.signal)
        .then(setPw)
        .catch(() => undefined)
    }, 250)
    return () => clearTimeout(t)
    // Pathways depend only on the base plant, not on the retrofit switches.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [baseKey, meta])

  const apply = useCallback((whr: boolean, biomass: number, h2: number) => {
    setControls((c) => ({ ...c, whr, biomass, h2, oxygen: false, kiln_control: false, producer_gas: false, char_recycle: false, vfd: false }))
    setTab("overview")
  }, [])

  const reset = () => setControls({ ...DEFAULT_CONTROLS, utilization: meta?.utilization ?? DEFAULT_CONTROLS.utilization })

  const active = [
    controls.whr && "Waste-heat power",
    controls.biomass > 0 && `Rice husk ${Math.round(controls.biomass * 100)}%`,
    controls.h2 > 0 && `Hydrogen ${Math.round(controls.h2 * 100)}%`,
    controls.oxygen && "Oxygen enrichment",
    controls.kiln_control && "Advanced kiln control",
    controls.producer_gas && "Producer gas",
    controls.char_recycle && "Char recycling",
    controls.vfd && "Variable-speed drives",
  ].filter(Boolean) as string[]
  const hasRetrofit = (sc?.retrofits.length ?? 0) > 0

  const rail = meta && (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2.5 px-5 pb-4 pt-5">
        <div className="grid size-8 place-items-center rounded-lg bg-accent text-white"><Factory className="size-4.5" /></div>
        <div>
          <div className="text-[14px] font-semibold tracking-[-0.01em] text-white">Kiln Planner</div>
          <div className="text-[11px] text-steel-mute">Coal-based DRI operations</div>
        </div>
        <button className="ml-auto rounded-md p-1 text-steel-mute hover:text-white lg:hidden" onClick={() => setRailOpen(false)} aria-label="Close controls"><X className="size-5" /></button>
      </div>
      <div className="flex-1 overflow-y-auto pb-4">
        <RailSection title="Plant">
          <div className="px-2 pb-2">
            <div className="mb-1.5 text-[12px] text-steel-mute">Coal supply</div>
            <Segmented dark size="sm" ariaLabel="Coal supply" value={controls.preset} onChange={(v) => set("preset", v)}
              options={[{ value: "imported", label: "Imported" }, { value: "domestic", label: "Domestic (high ash)" }]} />
          </div>
          <div className="px-2 pb-1">
            <div className="mb-1.5 text-[12px] text-steel-mute">Nameplate capacity</div>
            <div className="grid grid-cols-4 gap-1">
              {meta.capacities.map((c) => (
                <button key={c} onClick={() => set("capacity", c)} aria-pressed={controls.capacity === c}
                  className={cn("rounded-md py-1.5 text-[12px] font-medium tnum transition-colors",
                    controls.capacity === c ? "bg-steel-ink text-steel" : "bg-steel-3/60 text-steel-mute hover:text-steel-ink")}>{c}</button>
              ))}
              <span className="col-span-1 self-center text-center text-[11px] text-steel-mute">t / day</span>
            </div>
          </div>
          <RailRange label="Utilisation" value={Math.round(controls.utilization * 100)} min={50} max={95} step={5}
            onChange={(v) => set("utilization", v / 100)} display={`${Math.round(controls.utilization * 100)}%`} />
          <div className="px-2 pb-1">
            <div className="mb-1.5 text-[12px] text-steel-mute">Coal rate</div>
            <Segmented dark size="sm" ariaLabel="Coal rate mode" value={controls.coal_mode} onChange={(v) => set("coal_mode", v)}
              options={[{ value: "solve", label: "Solve from heat balance" }, { value: "specified", label: "Specify" }]} />
          </div>
          {controls.coal_mode === "specified" && (
            <RailRange label="Coal per tonne DRI" value={controls.coal_rate ?? meta.coal_rate.default} min={meta.coal_rate.min} max={meta.coal_rate.max} step={0.01}
              onChange={(v) => set("coal_rate", v)} display={`${num(controls.coal_rate ?? meta.coal_rate.default, 2)} t`} />
          )}
        </RailSection>

        <RailSection title="Decarbonisation levers">
          <RailSwitch label="Waste-heat power" hint="After-burner gas to a boiler and turbine" checked={controls.whr} onChange={(v) => set("whr", v)} />
          <RailRange label="Rice husk" value={Math.round(controls.biomass * 100)} min={0} max={Math.round(meta.biomass_max * 100)} step={5}
            onChange={(v) => set("biomass", v / 100)} display={`${Math.round(controls.biomass * 100)}%`} />
          <RailRange label="Hydrogen" value={Math.round(controls.h2 * 100)} min={0} max={Math.round(meta.h2_max * 100)} step={5}
            onChange={(v) => set("h2", v / 100)} display={`${Math.round(controls.h2 * 100)}%`} />
        </RailSection>

        <RailSection title="Efficiency measures">
          <RailSwitch label="Oxygen enrichment" hint="Enriched combustion air" checked={controls.oxygen} onChange={(v) => set("oxygen", v)} />
          <RailSwitch label="Advanced kiln control" hint="Tighter air and temperature control" checked={controls.kiln_control} onChange={(v) => set("kiln_control", v)} />
          <RailSwitch label="Producer gas firing" hint="Gasifier fuel at the discharge end" checked={controls.producer_gas} onChange={(v) => set("producer_gas", v)} />
          <RailSwitch label="Char recycling" hint="Dolochar returned to the feed" checked={controls.char_recycle} onChange={(v) => set("char_recycle", v)} />
          <RailSwitch label="Variable-speed drives" hint="Fans and kiln drive" checked={controls.vfd} onChange={(v) => set("vfd", v)} />
        </RailSection>

        <RailSection title="Carbon accounting">
          <RailSwitch label="Biogenic CO₂ zero-rated" hint="Standard reporting convention" checked={controls.biogenic_zero} onChange={(v) => set("biogenic_zero", v)} />
          <div className="px-2 pt-1">
            <div className="mb-1.5 text-[12px] text-steel-mute">Hydrogen supply</div>
            <Segmented dark size="sm" ariaLabel="Hydrogen supply" value={controls.h2_source} onChange={(v) => set("h2_source", v)}
              options={[{ value: "green", label: "Renewable" }, { value: "grey", label: "Natural gas" }]} />
          </div>
        </RailSection>
      </div>
      <div className="border-t border-steel-3 p-3">
        <button onClick={reset} className="flex w-full items-center justify-center gap-2 rounded-lg border border-steel-3 py-2 text-[12.5px] font-medium text-steel-ink hover:bg-steel-2">
          <RotateCcw className="size-3.5" /> Reset to baseline
        </button>
        <div className="mt-2.5 flex justify-center gap-3 text-[10.5px] text-steel-mute">
          <span>Model {meta.version}</span>
          <span className="font-mono" title="Parameter set fingerprint">{meta.fingerprint}</span>
        </div>
      </div>
    </div>
  )

  if (error === "offline" && !sc) {
    return (
      <div className="grid min-h-screen place-items-center bg-canvas p-6">
        <div className="max-w-md rounded-xl border border-line bg-panel p-6">
          <div className="flex items-center gap-2 text-[15px] font-semibold text-ink"><CircleAlert className="size-5 text-bad" /> Model service unavailable</div>
          <p className="mt-2 text-[13px] leading-relaxed text-ink-2">The console could not reach the plant model. Start both services from the project folder:</p>
          <pre className="mt-3 rounded-lg bg-steel p-3 font-mono text-[12px] text-steel-ink">./run_web.sh</pre>
          <button onClick={() => location.reload()} className="mt-4 rounded-lg bg-accent-deep px-3.5 py-2 text-[12.5px] font-medium text-white">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen bg-canvas">
      <aside className="sticky top-0 hidden h-screen w-[300px] shrink-0 bg-steel lg:block">{rail}</aside>
      {railOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setRailOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-[300px] bg-steel shadow-2xl">{rail}</aside>
        </div>
      )}

      <div className="min-w-0 flex-1">
        <div className="relative h-0.5 overflow-hidden">
          {busy && <div className="loadbar absolute inset-y-0 w-1/3 bg-accent" />}
        </div>
        <header className="sticky top-0 z-30 border-b border-line bg-canvas/90 backdrop-blur">
          <div className="mx-auto flex max-w-[1320px] flex-wrap items-center gap-x-6 gap-y-3 px-6 pt-4">
            <button className="rounded-md border border-line p-1.5 text-ink-2 lg:hidden" onClick={() => setRailOpen(true)} aria-label="Open controls"><Menu className="size-5" /></button>
            <div className="min-w-0">
              <h1 className="text-[17px] font-semibold tracking-[-0.015em] text-ink">Rotary kiln sponge iron plant</h1>
              <ul className="mt-0.5 flex flex-wrap items-center gap-y-1 text-[12.5px] text-ink-3 [&>li+li]:ml-2.5 [&>li+li]:border-l [&>li+li]:border-line-strong [&>li+li]:pl-2.5">
                <li>{controls.preset === "imported" ? "Imported coal" : "Domestic high-ash coal"}</li>
                <li className="tnum">{controls.capacity} t/day</li>
                <li className="tnum">{Math.round(controls.utilization * 100)}% utilisation</li>
                <li className={active.length ? "text-accent-deep" : undefined}>{active.length > 0 ? active.join(", ") : "Baseline configuration"}</li>
              </ul>
            </div>
            {sc && (
              <div className="ml-auto flex flex-wrap items-center gap-2">
                <Pill tone={sc.status.feasible ? "good" : "bad"} icon={sc.status.feasible ? <CircleCheck className="size-3.5" /> : <CircleAlert className="size-3.5" />}>
                  {sc.status.feasible ? "Ore fully reduced" : "Insufficient reductant"}
                </Pill>
                <Pill tone={sc.status.mass_ok && sc.status.energy_ok ? "good" : "bad"} icon={<span aria-hidden>●</span>}>
                  {sc.status.mass_ok && sc.status.energy_ok ? "Balances closed" : "Balance outside tolerance"}
                </Pill>
                <Pill tone={sc.status.checks_fail === 0 ? "good" : "warn"} icon={<span aria-hidden>{sc.status.checks_fail === 0 ? "●" : "▲"}</span>}>
                  {sc.status.checks_pass}/{sc.status.checks_scored} benchmarks in range
                </Pill>
              </div>
            )}
          </div>
          <nav className="mx-auto mt-3 flex max-w-[1320px] gap-1 overflow-x-auto px-5" aria-label="Sections">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button key={id} onClick={() => setTab(id)} aria-current={tab === id ? "page" : undefined}
                className={cn("relative flex items-center gap-1.5 whitespace-nowrap px-3 pb-3 pt-1.5 text-[13px] font-medium transition-colors",
                  tab === id ? "text-ink" : "text-ink-3 hover:text-ink-2")}>
                <Icon className="size-4" />
                {label}
                {tab === id && <span className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-accent-deep" />}
              </button>
            ))}
          </nav>
        </header>

        <main className="mx-auto max-w-[1320px] px-6 py-6">
          {!sc || !meta ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3 xl:grid-cols-5">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-28 animate-pulse rounded-xl bg-[#ebeae5]" />)}</div>
              <div className="h-80 animate-pulse rounded-xl bg-[#ebeae5]" />
            </div>
          ) : (
            <div className={cn("transition-opacity", busy && "opacity-[0.88]")}>
              {tab === "overview" && <Overview sc={sc} hasRetrofit={hasRetrofit} pw={pw} target={target} setTarget={setTarget} onApply={apply} meta={meta} />}
              {tab === "process" && <Process sc={sc} hasRetrofit={hasRetrofit} />}
              {tab === "pathways" && <PathwaysView pw={pw} onApply={apply} />}
              {tab === "economics" && <Economics sc={sc} hasRetrofit={hasRetrofit} />}
              {tab === "evidence" && <Evidence sc={sc} params={params} meta={meta} />}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
