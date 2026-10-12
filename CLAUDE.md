# Li-6 supply chain model

Bi-criterion MILP of the lithium-6 supply chain for fusion: minimize total cost and EU supply risk.
Thesis context: `../CLAUDE.md`. State of this file: 2026-10-12.

## Method

- Base model: multi-echelon supply chain MILP of Tsiakis et al. 2001 (`../Literature_Dipl/MILPmultiEchelonSupplyChain_Tsiakis_2001.pdf`)
- Supply risk: GeoPolRisk of Gemechu et al. 2016, SR = HHI · Σ g_k · f_ik, carried inside the MILP per supplier country and per echelon
- The import share f = Q / ΣQ is nonlinear. The flow sum is therefore replaced by the fixed echelon demand ("fixed-demand linearization"): SR = HHI / D · Σ g_k · Q_k
- Solution: lexicographic payoff table for the two corners, then AUGMECON (Mavrotas 2009, `../Literature_Dipl/AUGMECONepsilon-con_Mavrotas_2009.pdf`) with supply risk as the ε-constraint
- No environmental objective: the LCA inventory data for the novel enrichment routes does not exist. Documented as a limitation
- The hard part is the data, not the math

## Model

Chain: extraction and processing site `l` → `Q_let` [kg nat. Li/yr] → enrichment site `e` with technology `t` → `Q_etr` [kg enr. Li/yr] → reactor `r`

| Set | Members |
|-----|---------|
| L | `l_Au`, `l_Ci`, `l_Ch`, `l_Ar`, `l_Fr` |
| E | `e_US`, `e_EU`, `e_Ch`, `e_Ru` |
| T | `t_chemEx`, `t_dispEl`, `t_amalgam` |
| R | `r1` (DEMO) |

`t_dispEl` merges displacement chromatography and electrochemical exchange: no public data separates them.

| Variable | Type | Meaning |
|----------|------|---------|
| `Y_et` | binary | site e is built with technology t |
| `Q_let`, `Q_etr` | ≥ 0 | flows |
| `z_ej`, `q_ej`, `CC_e` | binary, ≥ 0, ≥ 0 | piecewise-linear capital cost: active segment, increment inside it, capital cost [€] |
| `N_e` | integer ≥ 0 | further full-size plants at site e (0 at DEMO demand) |
| `s` | ≥ 0 | AUGMECON slack |

There are no link binaries X. Sourcing is continuous, so several countries can supply at once.

Objectives (`model.py`):
- Cost [€/yr] = Σ M_e · CC_e + Σ (TC_let + PC_l) · Q_let + Σ (TC_etr + EC_et) · Q_etr, with M_e = (CRF_e + fom) · f_e
- Supply risk [–] = HHI_extr / D_nat · Σ g_l · Q_let + HHI_enr / D_enr · Σ g_e · Q_etr (both echelons, weights 1 and 1)

Constraints (`constraints.py`):
- At most one technology per site
- Flow only into and out of a built site (big-M `Q_max_nat`, `Q_max_enr`)
- Demand: D_r1 ≤ Σ Q_etr (binds in every run)
- Material balance per (e, t): Σ_l Q_let = f_ne · Σ_r Q_etr
- Extraction ceiling `Cap_l`; enrichment ceiling `Cap_et · (Y_et + N_e)` and floor `Cap_et_min · Y_et`
- Capital cost segments: one segment if built, segment width, capital cost
- Several plants per site: full-size plants only at a built site, flexible plant ≤ output ≤ all plants
- AUGMECON: SR + s = ε, objective cost − δ · s / r_SR

Rules:
- `build_model(p, delta, r_SR)` takes only the sets and `Qbar` from `p`. All other values are read from the `params` and `supply_risk` modules directly
- `params.py` and `supply_risk.py` compute their derived values once, at import
- `Q_max_nat` and `Q_max_enr` are switches, not capacities: they must never bind
- `build_model` raises if `r_SR == 0` (the objectives do not conflict)
- A point of the front is `obj_cost` and `obj_SR`, never `obj_augmecon` (it contains the slack term)

## Files

| File | Role |
|------|------|
| `params.py` | sets and all input data with units and sources |
| `conversions.py` | formulas behind the derived parameters (CRF, capex power law, breakpoints, shares, g) |
| `supply_risk.py` | HHI and demand scalars of the risk objective; ex-post GeoPolRisk for the tests |
| `constraints.py` | constraint rules |
| `model.py` | `build_model`: variables, both objectives, AUGMECON block |
| `plots.py` | `snapshot`, `pareto_front`, `supply_chain_network` |
| `main.ipynb` | DEMO scenario: cost-only run, payoff table, AUGMECON front, tests |
| `sensitivities.py` | sensitivity analysis of the DEMO scenario |
| `sweep.py` | Commercial scenario: fleet-size sweep |
| `runs/` | outputs of `sensitivities.py` and `sweep.py` (CSV, PDF) |

## Running

- Environment: conda env `thesis` (Pyomo, GLPK, pandas, matplotlib, ipykernel)
- `main.ipynb`: run all cells. Writes `pareto_front.pdf`, `chain_cheap.pdf`, `chain_mid.pdf`, `chain_safe.pdf` into this folder. `Presentation/X_presentation.tex` links the front and the cheap and safe chain
- `sensitivities.py` (about 1 min) and `sweep.py` (about 30 s): each file is one `# %%` cell. "Run Cell" shows the tables and figures inline and saves them in `runs/`
- Both files reload edited `.py` files before a run (autoreload, as the first cell of `main.ipynb`)

## DEMO base case (2026-10-12)

| Corner | Cost [M€/yr] | SR | Chain |
|--------|--------------|----|-------|
| Cost-optimal | 14.92 | 0.2689 | 100 % Argentina → China, `t_dispEl` |
| Risk-optimal | 24.23 | 0.2022 | 100 % Australia → EU, `t_dispEl` |

The front has two branches (`e_Ch` and `e_EU`) and a gap between them.

## Enrichment cost data

- No industrial cost figure for Li-6 enrichment is public
- One base value per technology block (`EC_e`): chemEx 2500, dispEl 1250, amalgam 2000 €/kg product
- The uncertainty goes through the sensitivity analysis, not through low/medium/high scenarios: amalgam at 1000 €/kg as the sourced alternative, every block at ±10 %
- Result: enrichment cost shifts the cost level of the whole front, not the cost premium of the safe chain, because both corners build the same block

## Sensitivity analysis: `sensitivities.py`

- One input changes per run. Reported are both payoff-table corners and the cost premium between them
- `scenario_cases()`: the alternative values named in the thesis (S0–S8). `tornado_cases()`: all 33 continuous inputs at ±`PCT` (10 %)
- A case patches the loaded modules: `run_case(leaves, hhi, lex_tol)` resets, sets the values, calls `rederive()`, solves both corners and returns the two snapshots. `result()` makes the table row, `front()` traces the Pareto front
- **Rule:** every value that `params.py` computes from other parameters must also be in `rederive()` and in `DERIVED`. `self_test()` proves that the listed formulas agree; it cannot notice a missing one
- Never patch a derived value (`TC_let`, `Cap_et`, `M_e`, ...): patch its source (`TC_le`, `f_ne`, `f_e`, ...). `run_case` asserts this
- The patch stays in the kernel until the next `reset()`
- Corners come from the lexicographic payoff solves, not from the ε loop (the grid point ε = SR_min is often infeasible)
- `Cap_e_prod` and `Cap_e_min_prod` also anchor the capex breakpoints `Qbar`: changing them moves the linearized CC(Q) slightly although neither capacity binds
- Outputs: `scenarios.csv`, `fronts.csv`, `tornado.csv`, `chain_S*_cheap.pdf` / `chain_S*_safe.pdf`, `tornado_cost.pdf`, `tornado_premium.pdf`

## Commercial scenario: `sweep.py`

- Sweeps the fusion fleet size; the scenarios of Mantilla 2026 (Tab. 4.1) are markers on that axis: fleet [GWe] = TWh / (8760 h · 0.8)
- 21 scenario fleets (corners and Pareto front) plus 23 log-spaced grid points (corners only)
- Demand = fleet · `GWFUS_PER_GWE` · 26 000 kg / `T_FILL`, first fill only
- **Placeholders, no source yet:** `GWFUS_PER_GWE = 3.0` and `T_FILL = 10` yr
- `Cap_l` stays at the 2024 values. A fleet the model cannot supply comes back as "no solution"
- With the placeholders 31 of 44 fleet sizes solve; the lithium limit of 6 701 t enr. Li/yr sits at about 860 GWe
- `LEX_TOL = 1e-9`: at costs near 1e10 € GLPK calls the exact corner freeze infeasible for single fleet sizes
- Outputs: `sweep_corners.csv`, `sweep_fronts.csv`, `sweep_fronts.pdf` (one page per solved scenario fleet)
