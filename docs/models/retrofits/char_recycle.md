# Char recycling

**Code:** `project/src/retrofits/char_recycle.py` (`CharRecycle.calculate_impact`)

## What it does

The char in the dolochar is separated and fed back to the kiln with the ore, replacing feed coal on equal fixed carbon. The method is Bhardwaj et al. (2024), Section 4.6.

## Method

```
char recycled       = dolochar × 90% separation
carbon returned     = char carbon × 90%
feed coal replaced  = carbon returned / feed-coal fixed carbon (40.95%)
coal cut            = feed coal replaced / total coal
lost char sales     = char recycled × ₹1,500/t
```

The coal it displaces is a coal cut like the other levers. What differs is that the recycled char carbon now leaves as gas instead of with the solids, and the plant stops selling that char.

The method is single-pass, as in the source. The char that the recycled char would itself leave behind is not iterated.

## Result on the reference plant

| Quantity | Value |
|---|---:|
| Char recycled | 123 kg/t |
| Carbon returned | 35.1 kg/t |
| Feed coal replaced | 85.7 kg/t (8.4% of coal) |
| Lost dolochar sales | ₹185/t |
| CO₂ change | −2.1% |
| Cost change | −₹30/t |
| Equity NPV | ₹0.57 crore |

The coal saved is worth more than the char sales given up, but only just.

## Limits

The separation power is not reported in the source and is excluded. Bhardwaj et al. treat char recycling as exclusive with gaseous reductants. This model has no such exclusion; the reductant-carbon ratio is the constraint it enforces.
