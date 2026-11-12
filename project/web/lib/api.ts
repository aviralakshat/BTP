export type Controls = {
  preset: "imported" | "domestic"
  capacity: number
  utilization: number
  coal_mode: "solve" | "specified"
  coal_rate: number | null
  whr: boolean
  biomass: number
  h2: number
  oxygen: boolean
  kiln_control: boolean
  producer_gas: boolean
  char_recycle: boolean
  vfd: boolean
  biogenic_zero: boolean
  h2_source: "green" | "grey"
}

export const DEFAULT_CONTROLS: Controls = {
  preset: "imported",
  capacity: 100,
  utilization: 0.9,
  coal_mode: "solve",
  coal_rate: null,
  whr: false,
  biomass: 0,
  h2: 0,
  oxygen: false,
  kiln_control: false,
  producer_gas: false,
  char_recycle: false,
  vfd: false,
  biogenic_zero: true,
  h2_source: "green",
}

export type Meta = {
  version: string
  fingerprint: string
  capacities: number[]
  utilization: number
  biomass_max: number
  h2_max: number
  coal_rate: { default: number; min: number; max: number }
  targets: number[]
  calibration: string
}

export type Verdict = "PASS" | "WARN" | "FAIL" | "INFO"

export type Scenario = {
  status: {
    checks_pass: number
    checks_scored: number
    checks_fail: number
    mass_closure: number
    mass_ok: boolean
    mass_tolerance: number
    energy_closure: number
    energy_ok: boolean
    feasible: boolean
    reductant_ratio: number
    coal_solved: boolean
  }
  kpi: {
    cost: number
    cash_cost: number
    capex_charge: number
    annual_output: number
    output_tpd: number
    co2_total: number
    co2_direct: number
    co2_scope2: number
    co2_biogenic: number
    coal_ef: number
    coal_rate: number
    sec_gcal: number
    capex: number
    grid_kwh: number
    export_kwh: number
    ore_rate: number
  }
  base: {
    cost: number
    co2_total: number
    co2_direct: number
    co2_scope2: number
    co2_biogenic: number
    coal_rate: number
    grid_kwh: number
  }
  flows: { ore_t: number; coal_t: number; air_t: number; dolomite_t: number; waste_gas_t: number; char_t: number }
  streams: { name: string; direction: "in" | "out"; kg: number; tpd: number }[]
  energy: { group: string; item: string; gcal: number; pct: number; is_input: boolean }[]
  elements: { element: string; in: number; out: number; error: number; ok: boolean }[]
  waste_gas: { species: string; kg: number }[]
  kiln: {
    length_m: number
    diameter_m: number
    incline_deg: number
    cells: { z: number; zone: string; gas: number; solid: number; met: number }[]
  }
  cost_lines: { item: string; inr: number }[]
  retrofits: { name: string; metrics: { label: string; value: number | boolean | null }[] }[]
  finance: Finance | null
  basis: string[]
  checks: {
    key: string
    label: string
    unit: string
    model: number
    min: number | null
    max: number | null
    verdict: Verdict
    deviation: number | null
    source: string
  }[]
  open_citations: string[]
  out_of_range: { parameter: string; value: number; min: number; max: number }[]
}

export type IrrStatus = "unique" | "none" | "multiple" | "no_investment"

export type Finance = {
  capex: number
  annual_opex: number
  annual_saving: number
  equity: number
  debt: number
  npv: number
  irr: number | null
  irr_status: IrrStatus
  project_npv: number
  project_irr: number | null
  project_irr_status: IrrStatus
  payback: number | null
  discounted_payback: number | null
  years: { year: number; equity_cf: number; cumulative: number; project_cf: number; ebitda: number; interest: number; principal: number; tax: number }[]
  terms: { debt_fraction: number; interest: number; tenor: number; tax: number; escalation: number; discount: number; life: number }
  stress: { case: string; npv: number; irr: number | null; irr_status: IrrStatus; payback: number | null }[]
  levelised: { annuity: number | null; financed: number | null }
}

export type PathwayRow = {
  label: string
  feasible: boolean
  co2: number
  co2_cut: number
  cost: number
  cost_delta: number
  abatement: number | null
  capex: number
  payback: number | null
  whr: boolean
  biomass: number
  h2: number
  frontier: boolean
}

export type Pathways = {
  rows: PathwayRow[]
  roadmap: ({ target: number } & Partial<Omit<PathwayRow, "label" | "feasible" | "frontier">> & { label: string | null })[]
  max_cut: number
  h2_breakeven: number
  h2_price: number
}

export type ParamRow = {
  name: string
  key: string
  value: number | string | null
  unit: string
  min: number | null
  max: number | null
  status: string
  source: string
}

export type ParamsResp = { summary: Record<string, number>; rows: ParamRow[] }

const BASE = "/api/model"

export async function getJSON<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { signal, cache: "no-store" })
  if (!res.ok) throw new Error(`${res.status}`)
  return res.json() as Promise<T>
}

export async function postJSON<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
    signal,
    cache: "no-store",
  })
  if (!res.ok) throw new Error(`${res.status}`)
  return res.json() as Promise<T>
}
