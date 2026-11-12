# Oxygen enrichment

**Code:** `project/src/retrofits/oxygen.py` (`Oxygen.calculate_impact`)

## What it does

Oxygen is added to the kiln air. The model applies one measured industrial trial: Rajesh, Nandi and Pabi (2016), Table 8, on a 100 t/day kiln. It does not rebuild the air stream.

## Method

```
hourly coal remaining   = 4.15 / 4.29 t/h                = 96.7%
specific coal remaining = 96.7% / (1 + 6% more output)   = 91.3%
coal cut per tonne      = 8.7%
oxygen cost             = 8 Nm³/t × ₹20/Nm³              = ₹160/t
```

Hourly solid coal falls from 4.29 to 4.15 t/h while output rises 6%, so coal per tonne falls by more than the authors' stated 6%. Both numbers are returned, and the 8.7% from the table is the one applied. The trial's air figures (2,600 falling to 2,150 Nm³/t) are reported for comparison with the solved air rate and are not used. The 6% output gain is carried into cost and finance.

## Result on the reference plant

| Quantity | Value |
|---|---:|
| Coal cut per tonne | 8.7% |
| Output | +6% |
| Oxygen cost | ₹160/t |
| CO₂ change | −8.5% |
| Cost change | −₹86/t |
| Capital | none charged |
| Equity NPV | ₹1.75 crore |

## Limits

The trial reports no oxygen price, so ₹20/Nm³ is an indicative supplier quote. No capital is charged for oxygen supply, because the trial does not give one. The trial ran for 100 days against a 50-day baseline campaign, and one trial on one kiln is the whole evidence.
