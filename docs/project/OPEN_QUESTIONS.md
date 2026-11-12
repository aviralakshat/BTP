# Open questions

Unanswered as of 10 November 2026. Phase 0 does not decide any of them.

1. Is the one-dimensional kiln model (Phase 5) in scope, or is the product a planning twin only? Decided on 10 November 2026: the axial reconstruction is in scope. A kinetic prediction is not, until Figure 4 is digitised and a rotation speed and a rate constant are sourced. The product remains a planning twin for metallisation, cost and CO2.
2. Is any real plant data obtainable, even one anonymised operating month?
3. Which model provider and budget should the analyst use, and should the chat run on a public deployment or only locally? The tab shipped on 10 November 2026 quotes the plant tools and does not call an API. A provider is still not chosen. `docs/software/agent_design.md` is the hook.
4. Which carbon-price and CBAM cases are the official ones? The model now has two, and neither is marked official. "No carbon charge" is the plant gate: the GST compensation cess of Rs 400/t coal was removed by the 56th GST Council (Ministry of Coal, 11 September 2025). "CBAM certificate, Q3 2026" is the European Commission's published price, EUR 82.32/t, converted at the ECB reference rate of 6 November 2026 (104.8645 INR per EUR). Say if the report should treat that published price as the case.
5. Should the hydrogen price follow a cited trajectory, or stay a single assumption of INR 305/kg? Hall et al. (2025) quote about $3.5/kg from Indian green-ammonia tenders, for a full hydrogen kiln rather than a partial injection retrofit.
6. Is the written report for examiners only, or also for an industry reader?
7. Can the untracked virtualenv at `project/tests/venv` be deleted?
8. Is the GitHub repository public or private? The literature PDFs are in `papers/`. The IITD webmail PDF is still at the repository root.

9. **Excess-air reduction as a lever.** Excess air is now Dey's measured 11.35%. No source gives an achievable lower value for a coal rotary kiln. Kumar (2012) and Gaurav (2017) cite "10–12% energy" from controlled axial and radial air injection, but that overlaps the existing kiln-control case (CSE 2026, 3–5% coal). Is a plant figure obtainable, or should excess air stay a sensitivity parameter only?
10. **Dust-loss reduction.** Dey's 4.96% of ore iron to dust is measured. BEE 2019 prescribes ore sizing (5–18 mm) but gives no dust figure for it, and Bhardwaj (2024) assume a 14.7% ore loss. No source links a measure to a lower loss, so no case was added.
11. **Kiln shell painting or insulation.** BEE 2019 Table 6.16 sets a skin-temperature standard of 90 °C and a target of 70 °C; Bhardwaj (2024) model 300 °C and Eq. (9)–(10). Turning that into a coal saving needs the shell emissivity, convection coefficient and kiln dimensions, none of which are stated for Dey's kiln.
12. **Import tariff.** The model buys power at INR 3.5/kWh (Kamal 2026, Gaurav 2017). Bhardwaj (2024) use 8.4 ¢/kWh, about INR 8.0. The tariff drives every power-saving case, VFD and WHR included. Which is right for a 2026 Chhattisgarh or Odisha plant?
13. **Does the hydrogen tender price include compression?** The model now adds Kamal's compressor capital on top of Hall's $3.5/kg. If the tender price is for delivered, compressed gas, this double counts.

A checked data sheet is in `docs/project/research/CHECKED_DATA.md`. It is not in the model yet. Prices, a kiln-suitable biomass analysis, a producer-gas capital cost and a waste-heat boiler efficiency are still missing from that sheet.
