# Web console

The production front end of the DRI kiln model: Next.js 16, React 19, Tailwind CSS v4 and Recharts. It calculates nothing itself. Every number comes from the model API in `../api/server.py`, which runs the Python model in `../src/`.

## Run

From `project/`:

```bash
./run_web.sh
```

That starts the model API on port 8000 and this console on http://localhost:3000. Requests to `/api/model/*` are rewritten to the API (see `next.config.ts`). Set `MODEL_API_URL` to use an API on another host.

## Layout

| Path | Contents |
|---|---|
| `app/page.tsx`, `app/layout.tsx` | The single page and the Geist fonts |
| `app/globals.css` | Theme tokens and Tailwind layers |
| `components/kiln/dashboard.tsx` | Shell: control rail, status strip, view tabs |
| `components/kiln/views.tsx` | Overview, Process, Pathways, Economics and Evidence views |
| `components/kiln/charts.tsx` | Mass flows, heat ledger, axial profile, pathways, cost, carbon and cash-flow charts |
| `components/kiln/schematic.tsx` | Kiln process schematic |
| `components/kiln/ui.tsx` | Cards, stats, status chips |
| `lib/api.ts` | Typed client for the model API |
| `lib/format.ts` | Rupee, crore, percentage and unit formatting |

Every chart has a table view beside it. Keep that pairing when adding a chart.
