# 03 Mass balance

**Code:** `project/src/models/mass_balance.py` (`MassBalance`)
**Question:** does every kilogram, and every element, that enters the kiln leave it?

## Purpose

The mass balance does not size anything. The baseline plant has already built the stream table. This model audits it, the way Dey et al. (2015) present their own balance with "other losses by difference": total mass in against total mass out, then element by element.

## Method

1. **Total.** Sum every input stream and every output stream. The residual is in minus out, as a percentage of mass in.
2. **Elements.** Recount the same streams atom by atom for Fe, C, O, H, N, S and inert solids (ash plus gangue).
3. **Acceptance.** Each closure is compared with a fixed tolerance and printed with its residual. Nothing is redistributed to make the residual smaller.

| Check | Tolerance | Why |
|---|---:|---|
| Total mass | 5% | The usual engineering acceptance for a plant-scale solids balance built from proximate and ultimate analyses |
| Each element | 2% | Element balances come from atom accounting and should be tighter |

## Result on the reference plant

| Balance | Residual | Status |
|---|---:|---|
| Total mass (solved coal rate) | 1.20% | Closed |
| Total mass (configured coal rate, running the module directly) | 1.31% | Closed |
| Fe, C, H, N, S, inerts | 0.000% | Exact |
| O | 0.48% | Closed |

The oxygen balance counts reacting oxygen only. Oxygen locked in unreduced Fe₂O₃, in gangue and in the CaO and MgO that survive calcination passes straight through, so it appears on neither side. The total residual is the stream-mass sum and is reported as it comes out.

## Running it

```bash
cd project
./venv/bin/python src/models/mass_balance.py
```

## Tests

`tests/test_model.py` checks that the total closes, that every element closes within tolerance, and that the conserved elements close exactly. The golden test freezes the residuals for the reference plant.
