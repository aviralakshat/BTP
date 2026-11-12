# TASK: Materials-science literature expansion and a robust v2 plan for the DRI digital twin

You are working in the repo https://github.com/aviralakshat/BTP (branch main). Before anything else, read docs/project/PROJECT_MASTER_PLAN.md in the repo root, then project/config/parameters.json, project/config/validation_targets.json, project/data/literature_gaps.csv, and skim project/src and project/app.py. The 13 literature PDFs at the repo root have text extracts in data/text/. Grep those before saying anything about what they contain.

THIS STEP IS RESEARCH AND PLANNING ONLY. Do not edit any file under project/src, project/config, project/app.py or project/tests. You may create new files only under docs/project/research/.

## 1. Who I am and what the project must be

I am a B.Tech student in Materials Science and Engineering at IIT Delhi. The project is a digital twin of an Indian coal-based rotary-kiln DRI (sponge iron) plant. At present it is a steady-state mass and energy balance with retrofit economics (waste-heat recovery, biomass substitution, partial hydrogen injection). It is judged by a materials science department, so the project must be defensible as materials science and metallurgy, not only as a process-engineering spreadsheet.

Proposed central thesis, which you should test, sharpen or reject with evidence:
"How far can a coal-based rotary-kiln DRI plant be decarbonised by retrofit before the materials constraints bind: iron-oxide reduction thermodynamics and kinetics, ore reducibility, coal and biomass char reactivity, ash and slag chemistry (sticking and accretion), desulphurisation chemistry, refractory and shell limits, and the quality of the DRI delivered to the steel furnace?"

The current model already has one materials-style constraint, a reductant-carbon adequacy ratio. The aim is to find out which further materials constraints are defensible, quantifiable from published data, and feasible to implement.

## 2. Non-negotiable rules (inherited from the project)

1. No magic numbers. Every numeric input will end up in parameters.json with value, unit, min, max, source and status.
2. Validation targets are never inputs. Do not propose copying a literature band into a parameter.
3. Derive rather than assume. Do not propose hard-coding quantities the model can solve.
4. Report residuals; never fudge a balance.
5. Keep the KILN and STACK system boundaries distinct.
6. Known failures (WHR overshoot against Nduagu et al., domestic coal over-sensitivity, 38 uncited parameters) are documented, not hidden.
7. Metallisation, DRI carbon and accretion risk are currently inputs or unmodelled. Making them predictions is a new model and must be proposed as such.
8. Never fabricate a citation, DOI, page, table number, figure or value. If you cannot verify it, say so.

## 3. Research protocol (follow exactly)

Use web search and web fetch extensively. For each topic below, run multiple searches with varied terms. Prefer peer-reviewed papers, standards, government and institutional reports. For each source you use, record: full citation, DOI or URL, year, access level (full text read / abstract only / could not access), and the exact location (table, figure, page) of every number you extract. Do not rely on memory for numbers. Do not quote more than a short phrase; paraphrase and give the location.

Rate each extracted number: A = measured in an Indian or comparable coal-based rotary-kiln plant; B = peer-reviewed lab or pilot data on relevant materials; C = review or secondary source; D = vendor, grey literature, or unverifiable. Say plainly when a source is weak.

Topics to cover (these are search seeds; verify every claim yourself):

A. Reduction thermodynamics and kinetics of iron oxides
 - Fe-O-C-H phase stability: Baur-Glaessner and Ellingham-type treatment, CO/CO2 and H2/H2O equilibrium for hematite, magnetite, wustite, iron; Boudouard equilibrium; water-gas shift.
 - Reduction kinetics of iron ore and pellets by CO, H2, solid carbon and coal char: shrinking-core and unreacted-core models, rate-controlling steps, activation energies, effect of temperature 900-1100 C, particle size, porosity.
 - Comparative H2 vs CO reduction rates and the endothermic nature of H2 reduction; sticking and low-temperature behaviour; the thermodynamic limit on H2 utilisation.
 - Kinetics specific to rotary-kiln conditions: solids bed behaviour, gas-solid contact, residence time, bed depth and fill level, freeboard.

B. Ore and burden materials
 - Indian iron ore mineralogy relevant to sponge iron (hematite, goethite, magnetite; lump vs pellet), gangue (SiO2, Al2O3), LOI, porosity, reducibility index, thermal decrepitation, reduction degradation index (RDI), cold and hot strength, size distribution.
 - How ore properties change coal rate, metallisation, fines generation and accretion.

C. Reductant materials: coal, char, biomass
 - Coal properties for sponge iron: reactivity (CO2 gasification), volatile matter and its release profile, fixed carbon, ash content and ash fusion temperature, sulphur, caking behaviour; Indian non-coking coal quality (high ash) and its effect on specific coal consumption.
 - Biomass and biochar as reductants and fuels: char reactivity with CO2, ash chemistry (K, Na, Ca, P, Si), alkali effects on gasification and on accretion, torrefaction and pyrolysis products, calorific values, bulk density and handling, particle size, volatile release.
 - Substitution limits found in experiments or pilot work.

D. Ash, slag and accretion chemistry
 - Ring and accretion formation in rotary kilns: mechanisms, low-melting phases in FeO-SiO2-Al2O3-CaO systems (fayalite, hercynite and others), alkali roles, temperature windows, operating practices that suppress them.
 - Effect of coal ash, dolomite and ore gangue on accretion; effect of biomass ash and hydrogen-rich atmosphere on it.
 - Any published quantitative criteria or indices that could become a model-based accretion-risk indicator.

E. Desulphurisation chemistry
 - Role of dolomite or limestone in absorbing sulphur, CaS formation, sulphur partition between gas, DRI and char; temperature and gas-composition dependence; effect of biomass (low sulphur) and hydrogen on sulphur in DRI.

F. DRI as a material and what the steel furnace needs
 - Metallisation, carbon content, gangue (SiO2 plus Al2O3), sulphur and phosphorus, porosity, apparent density, strength, reoxidation and pyrophoricity, fines, magnetic separation of char.
 - How DRI quality affects induction furnace and EAF yield, slag volume, energy use and steel quality in the Indian secondary steel sector.
 - Quality consequences of biomass or hydrogen substitution (carbon content, metallisation, reoxidation).

G. Refractories, kiln shell and heat loss materials
 - Refractory lining materials in rotary kilns (alumina-silica, high alumina, alkali and slag attack), wear mechanisms, shell temperature limits, heat-loss through shell and effect of lining on thermal efficiency and on WHR.
 - Whether the retrofits (hydrogen-rich gas, biomass ash, higher flame temperature, after-burner post-combustion, WHR boiler fouling) create materials risks (corrosion, fouling, hydrogen attack, high-temperature oxidation of heat-exchanger steels).

H. Waste-heat recovery
 - Measured gross and net generation per tonne DRI at Indian sponge iron plants; boiler (WHRB) and steam-cycle efficiencies; auxiliary load; waste-gas temperature and dust load; stack temperature limits (acid dew point, sulphur). Mine Gaurav et al. and Nduagu et al. fully for these.

I. Hydrogen and biomass techno-economics for Indian conditions
 - Green hydrogen cost projections for India and their sources; transport, storage and injection into a rotary kiln; safety and materials compatibility; biomass price, availability, logistics for sponge iron regions (Odisha, Chhattisgarh, Jharkhand, West Bengal).

J. Indian sponge iron sector facts
 - Production share by route (coal-based rotary kiln vs gas-based), kiln size distribution, specific energy and CO2 intensity surveys (CEEW, TERI, BEE, JPC, Ministry of Steel, SIMA), grid emission factor (CEA), policy context (carbon market, CBAM exposure of steel exports). Verify current status of any policy item with a search, and give the date of each source.

K. Modelling literature
 - Rotary kiln direct reduction process models (mass-energy balances, 1-D axial models, CFD) for sponge iron and for related kilns, including their calibration and validation approach, and what plant data they used. Identify any open-source or published equation sets that could be adapted legitimately with citation.
 - Hydrogen-based direct reduction modelling (shaft furnace, fluidised bed) only where it informs partial H2 injection.

Also find at least 15 additional highly relevant review articles or key primary papers that I do not yet have, and say why each matters.

## 4. Deliverables (create these under docs/project/research/)

1. LITERATURE_REVIEW.md: organised by topics A-K. For each topic: what is established, what is contested, what numbers can be used and at what quality grade, and how it connects to a model feature. End each topic with a short "so what for this project".
2. EVIDENCE_TABLE.csv: one row per extracted fact. Columns: topic, quantity, value, unit, conditions, source citation, DOI or URL, location in source, access level, quality grade, candidate parameter name, parameter min, parameter max, suggested status, notes.
3. SOURCE_LIBRARY.csv: every source considered, including ones rejected, with the reason.
4. GAP_RESOLUTION.md: for each of the 38 needs_citation parameters (read parameters.json for the list), state what you found, the proposed value and range, the source and location, or state that nothing defensible was found.
5. MATERIALS_MODEL_OPTIONS.md: a menu of materials-science model upgrades, each with:
 - the physical or chemical basis and governing equations (with citations),
 - the input parameters needed and whether published values exist,
 - what output it would turn from an input into a prediction (for example metallisation, DRI carbon, accretion risk, reductant-carbon feasibility, sulphur in DRI, DRI quality index),
 - how it would be validated, using which dataset, and which data would be held out,
 - effort estimate in days, risk, and whether it is defensible at B.Tech level,
 - how it respects the rules in section 2.
 Include at least these candidates: (a) thermodynamic feasibility limits from Fe-O-C-H equilibrium on gas composition and H2/biomass substitution; (b) shrinking-core reduction kinetics giving residence-time-limited metallisation; (c) char and biomass reactivity driven carbon-gasification model; (d) ash fusion and slag-phase accretion risk indicator; (e) dolomite desulphurisation and sulphur-in-DRI estimate; (f) DRI quality index for the downstream furnace; (g) refractory and heat-exchanger materials risk flags for each retrofit; (h) a 1-D axial kiln model as the integrating framework. Rank them by defensibility, data availability and value to the thesis.
6. MASTER_PLAN_V2.md: a revised version of docs/project/PROJECT_MASTER_PLAN.md that integrates your findings. Keep the structure and rules, but add: the materials-science thesis statement; the chosen materials model upgrades and their phase order; updated parameter register plan; new validation approach (fit set versus holdout set); updated agent tools (materials constraint tools and a literature-evidence lookup tool that returns citation and location for any parameter); updated UI pages (for example a "Materials constraints" page showing which constraint binds first at each CO2 target); updated tests; updated timeline with explicit cut lines (what to drop if time runs short). Mark every claim about the literature with its evidence row.
7. THESIS_OUTLINE.md: a chapter-by-chapter thesis outline from the materials science angle, mapping each chapter to code modules, figures and evidence rows.
8. VIVA_QUESTIONS.md: the 30 hardest questions a materials science examiner could ask about this project (thermodynamics, kinetics, ore, ash, refractories, DRI quality, validation, honesty of the model), each with a repo-grounded answer and the weakness you would admit.
9. OPEN_QUESTIONS.md: anything I must decide or any data I must obtain (for example a plant visit, ore or coal analyses, access to a paper behind a paywall).

## 5. Quality bar

- Every number in the deliverables has a source and a location, or is explicitly marked as unverified.
- Never present a source you could only read the abstract of as if you read it fully.
- Where sources disagree, show both values and explain the likely reason (conditions, ore type, definitions, boundaries).
- Flag any place where my current model's boundary, definition or assumption conflicts with the literature.
- Be explicit about what a B.Tech project can credibly claim. Prefer fewer, better-validated materials models over many shallow ones. Tell me which upgrades to cut.
- Keep language plain. No filler.

## 6. How to work

1. First reply: after reading the repo, give me a short summary of (a) what you found in the repo that differs from the plan, (b) your search plan per topic, (c) any questions that block you. Then proceed without waiting unless truly blocked.
2. Work topic by topic. After each topic, append to EVIDENCE_TABLE.csv and SOURCE_LIBRARY.csv so progress is saved.
3. At the end, give me a summary: what you delivered, the five strongest findings, the five biggest remaining gaps, which numbers in the current model your research contradicts or supports, and your recommended top three materials model upgrades with reasons.
