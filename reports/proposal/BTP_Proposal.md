# B.Tech Project: Techno-Economic Assessment of Retrofit Pathways for Low-Carbon Coal-Based Rotary-Kiln DRI

## 1. Project Objective

Develop a computational **techno-economic model of an existing coal-based rotary-kiln Direct Reduced Iron (DRI) plant** to determine whether carbon emissions can be reduced through retrofit technologies without making DRI production economically unattractive.

The immediate objective is **not to design a new hydrogen-based DRI plant**. Instead, the project should answer:

> **How much CO₂ reduction can be achieved by retrofitting an existing coal-based rotary kiln, and what is the corresponding change in ₹/tonne DRI?**

The ultimate target is to investigate pathways toward **20%, 40%, and 60% CO₂ reduction**.

## 2. Scope of Work

Develop a Python/Excel-based model representing a typical coal-based rotary-kiln DRI plant.

The model should calculate, for each retrofit scenario:

- DRI production rate
- Coal consumption
- Iron-ore consumption
- Electricity consumption
- Thermal energy consumption
- Reducing-gas consumption
- H₂ consumption, where applicable
- Biomass/biocarbon consumption
- Waste-heat recovery
- Total energy consumption
- CO₂ emissions
- CO₂ emissions per tonne DRI
- Operating cost (₹/t DRI)
- Retrofit CAPEX
- Annual operating savings/cost increase
- Payback period
- CO₂ abatement cost

The model should allow the user to change plant capacity and key economic parameters.

## 3. Establish the Baseline Plant

Start with a representative coal-based rotary kiln.

Consider at least three plant capacities:

- 100 TPD
- 200 TPD
- 350 TPD

If sufficient data are available, a 500 TPD case can also be considered.

Initially, use literature values and clearly state all assumptions.

The baseline model should include:

### Raw materials

- Iron ore
- Non-coking coal
- Dolomite/limestone
- Any other relevant additives

### Energy

- Coal
- Electricity
- Auxiliary fuel, if applicable

### Outputs

- DRI
- Char/coal ash
- Waste gas
- Waste heat

The student should construct a simplified **mass balance and energy balance** around the kiln.

## 4. Baseline Performance Indicators

Calculate:

[ SEC= ]

[ C_{}= ]

[ E_{}= ]

and

[ C_{}=  {} ]

The baseline should provide:

[  ]

and

[  ]

These two numbers will be the reference against which all retrofit scenarios are compared.

## 5. Retrofit Case Studies

The student should progressively introduce different retrofit options.

### Case 0 — Existing Coal-Based Kiln

No retrofit.

This is the reference case.

### Case 1 — Process Optimization

Investigate improvements such as:

- Air/fuel ratio optimization
- Reduced excess air
- Improved coal distribution
- Improved temperature control
- Improved residence-time control
- Improved ore/coal ratio
- Reduction of unnecessary heat losses
- Improved kiln operating efficiency

Estimate the potential reduction in coal consumption and CO₂ emissions.

The student should investigate the literature for realistic ranges rather than assuming an arbitrary improvement.

### Case 2 — Waste-Heat Recovery

Investigate recovery of heat from:

- kiln off-gas
- cooler exhaust
- hot DRI

Possible uses:

- combustion-air preheating
- feed preheating
- water/steam generation
- electricity generation

For small plants, do **not automatically assume electricity-generation WHR is optimal**. Compare process-heat recovery with power generation.

Calculate:

[      ]

Then calculate:

- WHR CAPEX
- annual savings
- payback
- CO₂ reduction

## 6. Case 3 — Biomass/Biocarbon Substitution

Investigate partial replacement of coal with biomass-derived carbon/biocarbon.

Study:

[ 5%,10%,15%,20% ]

substitution levels, subject to realistic process constraints from literature.

Calculate:

- coal reduction
- biomass consumption
- change in energy input
- change in CO₂ emissions
- change in operating cost

The student must distinguish between **biogenic CO₂ and fossil CO₂** and clearly state the accounting methodology.

## 7. Case 4 — Syngas Substitution

Investigate partial substitution of coal-derived reducing energy with syngas.

Study several substitution levels.

Determine:

- required syngas flow rate
- coal displacement
- thermal effect
- effect on reducing potential
- CO₂ reduction
- syngas cost
- total DRI production cost

The model should identify the economically optimal syngas substitution level.

## 8. Case 5 — Hydrogen-Assisted Rotary Kiln

Investigate partial H₂ injection/replacement.

Do **not assume complete replacement of coal**.

Study scenarios such as:

[ 5%,10%,15%,20%,30% ]

hydrogen substitution, with the exact definition of “substitution” clearly specified.

The student should calculate:

- H₂ requirement
- coal displacement
- energy balance
- reduction potential
- CO₂ reduction
- H₂ cost
- electricity requirement for green H₂, if applicable
- effect on ₹/t DRI

Most importantly, determine the **break-even hydrogen price**.

For example:

[ P_{H_2}^{break-even} =  ]

This should be calculated for different substitution levels.

## 9. Case 6 — Combined Retrofit

Combine the most promising technologies.

For example:

[  ]

Do not simply add the individual percentage reductions.

The combined system must be recalculated using the mass and energy balance.

Determine whether:

- 20% reduction is achievable
- 40% reduction is achievable
- 60% reduction is achievable

while maintaining acceptable DRI productivity and metallization.

## 10. Techno-Economic Model

For every case calculate:

[ C_{} = C_{} +C_{} +C_{H_2} +C_{} +C_{} +C_{} +C_{} +C_{} +C_{} ]

and include the economic benefit from recovered heat/electricity.

Calculate:

[ C = C_{}-C_{} ]

and:

[  =  {} ]

Also calculate:

[  ]

in:

[ ₹/ ]

## 11. Most Important Analysis: Cost vs CO₂ Reduction

Generate a curve showing:

[  ]

For example, identify:

- lowest-cost 10% reduction
- lowest-cost 20% reduction
- lowest-cost 30% reduction
- lowest-cost 40% reduction
- lowest-cost 50% reduction
- lowest-cost 60% reduction

This will provide a **decarbonization cost curve** for the rotary kiln.

## 12. Sensitivity Analysis

Perform sensitivity analysis for the parameters that are likely to dominate the economics.

At minimum investigate:

### Fuel/electricity

- Coal price
- Electricity price
- Biomass price
- Syngas price
- H₂ price

### Plant

- Plant capacity
- Capacity utilization
- Coal consumption
- Thermal efficiency
- WHR efficiency

### Retrofit

- H₂ substitution percentage
- Biomass substitution percentage
- WHR CAPEX
- H₂-system CAPEX
- Retrofit lifetime

### Economic

- Discount rate
- Plant operating days
- Carbon price, if applicable

## 13. Hydrogen Price Sensitivity

This should be one of the major outputs.

Plot:

[     ]

for different H₂ substitution levels.

Identify the H₂ price at which hydrogen-assisted operation becomes economically attractive.

This will help determine whether hydrogen retrofit is currently viable or requires future reductions in green-H₂ cost.

## 14. Plant-Scale Sensitivity

Repeat the analysis for:

- 100 TPD
- 200 TPD
- 350 TPD
- 500 TPD

Determine whether the economically optimal retrofit changes with plant size.

For example:

> A 100 TPD plant may favor process optimization and direct heat recovery, whereas a 350 TPD plant may justify WHR electricity generation and more extensive reducing-gas integration.

This is particularly important for MSME-scale DRI plants.

## 15. Optimization

After developing the individual case studies, develop a simple optimization routine in Python.

The objective can be:

[  ]

subject to:

[ CO_2 reduction X% ]

where:

[ X=20,;40,;60 ]

Run the optimization separately for each target.

The final output should answer:

### For 20% CO₂ reduction:

What is the cheapest retrofit combination?

### For 40% CO₂ reduction:

What is the cheapest retrofit combination?

### For 60% CO₂ reduction:

What is the cheapest technically feasible retrofit combination?

## 16. Final Output

The student should produce a **Retrofit Decarbonization Roadmap**.

For example:

| Target | Retrofit combination | CAPEX | Change in ₹/t DRI | CO₂ reduction | Payback |
| --- | --- | --- | --- | --- | --- |
| Baseline | Existing kiln | — | — | 0% | — |
| Low-carbon | Optimization + heat recovery | ₹X | −₹X | 10–20% | X yr |
| Medium | + biomass/syngas | ₹X | +₹X | 30–40% | X yr |
| Deep | + H₂ | ₹X | +₹X | 40–60% | X yr |

The numbers should be generated by the model and **not assumed beforehand**.

## 17. Data Sources

Initially, the student should use:

1. Peer-reviewed research papers on Indian coal-based DRI rotary kilns.
2. Government/industry reports.
3. Bureau of Energy Efficiency documents.
4. TERI reports.
5. Ministry of Steel reports.
6. Industrial energy-efficiency studies.
7. Published techno-economic studies.
8. Published data on hydrogen, biomass, syngas and WHR costs.

Create a database containing:

- source
- plant capacity
- coal consumption
- ore consumption
- energy consumption
- DRI production
- metallization
- temperature
- gas composition
- emissions
- CAPEX
- OPEX
- fuel prices
- retrofit performance

Every assumed parameter in the model must have a literature reference or a clearly documented engineering assumption.

## 18. Software

The student can initially implement the model using:

**Python + Excel**

Python should be used for:

- mass/energy balance
- scenario generation
- sensitivity analysis
- optimization
- plotting

Recommended Python packages:

- NumPy
- Pandas
- Matplotlib
- SciPy

A simple Excel interface can subsequently be developed so that an industrial user can enter plant data and obtain the retrofit recommendation.

## 19. Expected Research Outcome

The project should ultimately answer five questions:

1. **What is the baseline cost and carbon intensity of a typical coal-based rotary-kiln DRI plant?**
2. **Which retrofit measures provide the largest CO₂ reduction per rupee invested?**
3. **At what H₂/syngas/biomass prices do low-carbon retrofits become economically viable?**
4. **Can an existing rotary kiln achieve 40% and 60% CO₂ reduction without replacing the kiln?**
5. **What is the least-cost retrofit pathway for an MSME-scale DRI plant?**

The project should **not assume that 60% reduction is achievable**. The purpose of the model is to determine whether it is technically and economically feasible and, if not, identify the limiting factor.

## 20. Longer-Term Development

The B.Tech project should be designed as the first stage of a larger project.

### B.Tech Stage

**Literature → mass/energy balance → techno-economic model → retrofit scenarios → optimization**

↓

### Next Stage

**Real plant data → plant-specific calibration → digital twin**

↓

### Advanced Stage

**AI-based real-time optimization**

The eventual system could accept real-time kiln data such as:

- temperature profile
- coal flow
- air flow
- ore feed
- kiln speed
- gas composition
- pressure
- DRI metallization
- production rate

and recommend:

> **Optimal coal/H₂/syngas/air/feed conditions for minimum ₹/t DRI subject to a specified CO₂ target.**

This would provide the foundation for an **AI-driven retrofit decision-support platform for existing Indian coal-based rotary-kiln DRI plants**.

### Immediate Deliverable for the B.Tech Student

The first version should **not attempt AI or machine learning**.

The student should first build a reliable:

[  ]

Once this model is validated, AI can be added later to predict kiln behavior and optimize the retrofit in real time.

**The most important final figure should be a Pareto/abatement curve showing:**

[  ]

for different retrofit pathways.

That figure will be the starting point for discussions with MSME DRI plant owners and for the subsequent NCLCI/Karetic industrial deployment.
