# 08 Project finance and the annuity cost

**Code:** `project/src/economics/financial.py` (`finance_project`, `retrofit_project`, `reconciliation`)
**Question:** does a retrofit pay back once it carries a loan, tax and escalation?

Model 0.6.0. The mass balance, the energy balance and the cost per tonne are the 0.5.0 results. What changed is that a retrofit can now be read as a cash flow as well as an annuity.

## What is being financed

The cash flow is the retrofit, not the kiln. No source in the model gives the capital cost of the kiln itself, so a net present value of the whole plant would need a sponge-iron selling price and a kiln cost that are not in the parameter file. Neither is invented. The benefit of a retrofit is the operating cash it saves.

That saving is the cash cost per tonne before the retrofit minus the cash cost per tonne after it, times the tonnes produced after it. Total spend at two different outputs is not compared. With no selling price, a retrofit that raises output (oxygen enrichment raises it 6%) would otherwise be charged for its extra tonnes as if they were a cost overrun. Before 0.7.1 the totals were compared, and oxygen enrichment showed a negative NPV despite cutting cost per tonne. It now shows about ₹1.75 crore.

## The annuity

Capital on the Economics tab is

```
CRF × capex / annual tonnes
```

with the capital recovery factor at 8% for 20 years. The 8% is the weighted average cost of capital in Hall, Bhaskar and Görnerup (TERI 2025). The 20 years are Kamal et al. (2026), Table 3. This charge is pre-tax and all-equity. It does not depend on the tax rate or the loan.

Kamal's own table uses a 10% real post-tax discount rate, and their sensitivity finds the hydrogen-plant NPV crossing zero near 11%. Those are results for a different plant. They are not the rate used here.

## The cash flow

The terms are one case, the Bureau of Energy Efficiency detailed project report (2011) for a waste-heat power plant on a 100 TPD sponge-iron kiln, Annexure 4 and Section 4.2.

| Term | Value | Where it is stated |
|---|---|---|
| Term loan | 75% of capital | Section 4.2 |
| Equity | 25% | Section 4.2 |
| Interest | 10% | Section 4.2.3, SIDBI energy-efficiency rate |
| Tenor | 5 years, equal principal | Annexure 4, marked assumed |
| Book depreciation | 5.28% straight line | Annexure 4, Companies Act |
| Tax depreciation | 7.84% of the written-down value | Annexure 4, Income Tax Rules |
| Tax | 33.99% of taxable profit | Annexure 4 |
| Escalation | 5% a year on operating cost only | Annexure 4 |

Taxable profit is operating profit after interest, with book depreciation added back and tax depreciation deducted. That is the report's own tax computation: on its year-1 figures, 902.47 − 84.05 − 75.32 = 743.10, and 33.99% of that is 252.58. A loss is not refunded. Since 0.7.1 it is carried forward and set off against later taxable profit with no expiry. The losses in these projects come from tax depreciation, and unabsorbed depreciation carries forward without limit under s.32(2) of the Income Tax Act, 1961. The BEE waste-heat project has no loss year, so its figures are unchanged. The six-month moratorium is not applied. The report marks it as assumed.

An IRR is quoted only when the cash flow has exactly one. The solver scans every sign change of the net present value from -90% upwards with no fixed ceiling, so a small equity cheque against a large saving still gets its IRR. When there is no root, `irr_status` is `none` (the outlay is never recovered). When there are several, it is `multiple`, and the net present value is the decision measure. When there is no outlay at all (producer gas, char recycling and variable-speed drives carry no capital cost), it is `no_investment`. A rate of return is undefined there, and the console shows the payback as immediate when the NPV is positive.

The assumptions table in the extract prints 240.19 in the interest-rate cell. That is the equity amount in lakh, copied into the wrong row. The prose says 10%, and 10% is what the model uses.

Working capital is zero. The report's balance sheet accumulates cash. It does not tie up a separate stock of working capital.

The equity cash flow is discounted at the same 8% as the annuity, so the two can be compared. Payback on this cash flow is the equity cheque, after debt service. The payback on the pathway tab is still the whole capital divided by the operating saving. They are different questions.

## Reconciliation

Take the waste-heat case at 100 TPD. Switch tax, debt and escalation off, and the cash-flow levelised cost equals the annuity cost: ₹6,367 per tonne. Switch them back on and the levelised cost is ₹6,417 per tonne, ₹50 higher. The loan costs 10% while the annuity discounts the whole outlay at 8%, and a cost-only account has no taxable profit, so the depreciation does not reduce the tax.

On the incremental project the saving is income, so tax does bite. For waste heat recovery the equity net present value is about ₹14.6 crore, the equity IRR is about 48%, and the equity payback is about 2.7 years (about 3.1 years discounted). Most of the capital is borrowed, which is why the equity return is high. That is not a claim that the project returns 48% on the whole ₹8.8 crore. The unlevered project IRR on the full capital, with no debt, is about 27%.

The web console also stresses the equity case. With capital 30% higher, the saving 20% lower and interest 2 points higher all at once, waste heat recovery keeps an equity NPV of about ₹7.3 crore and an equity IRR of about 21%. The shocks are in `config/analysis.json` under `finance_stress`. The saving shock reduces the benefit by 20% of its magnitude, so a retrofit that already loses money gets worse, not better.

## Prices

`project/data/price_series/commodity_prices.json` names the series. The numbers are read from `parameters.json`, so a price cannot be updated in one file and forgotten in the other. Coal and iron ore have a single cited price. Power, the export tariff, dolomite and hydrogen have a cited low and high. Carbon is not in the plant cost. Its base is no charge, and its high case is the Q3 2026 CBAM certificate price.

A named scenario, saved through `src/analysis/scenario_store.py`, stores the overrides, the model version and the hash of `parameters.json`.
