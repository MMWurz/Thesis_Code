## NOTES
	- Hardest part: **data** (supplier locations, costs, isotope separation capacity), not the math
	- Node-structure needs backing up (maybe Giegerich)
	- Not yet all constraints implemented (check Tsiakis)

## Thesis novelty framing

	"We extend @Thesis/Literature/MILPmultiEchelonSupplyChain_Tsiakis_2001.pdf to Li-6 by and applying it as a bi-criterion MOO for the first time, trading off cost against EU supply risk.
	Therby we provide the modelling-background to the following policy papers:
	@Thesis/Literature/Li6SupplyDEMOFusion_Giegerich_2019.pdf
	@Thesis/Literature/LiEnrichmentUK_Dackombe-Rodrigues_2026.pdf
	@Thesis/Literature/LiSupplyFusion_Ward_2025.pdf "

# MOO Model Research — Li-6 Supply Chain

	- Decided to adopt an existing MILP supply chain model rather than build from scratch, extending it for Li-6 with two objectives: cost and EU supply risk.

	- Environmental impact was dropped as a third objective. A rigorous ecological assessment requires data that is not yet available for the Li-6 enrichment routes relevant to this thesis. 
	- Including it without adequate data would compromise scientific validity. The omission is treated as a limitation and future work direction in the thesis.

## Base model (adopt this)

	@Thesis/Literature/MILPmultiEchelonSupplyChain_Tsiakis_2001.pdf

## Solution method (implement this)
	
	@Thesis/Literature/AUGMECONepsilon-con_Mavrotas_2009.pdf
	- the augmented epsilon-constraint method. Correct and efficient for bi-criterion MILP; avoids weakly Pareto-optimal solutions via slack variable augmentation; generates a clean 2D Pareto curve.
	- AUGMECON solves the MILP repeatedly with different epsilon bounds to trace the Pareto front.

## Objective 2 — EU Supply Autonomy methodology

	- Use EU JRC CRM supply risk methodology: HHI x WGI per supplier country -> weighted supply risk score
	- Reference: EU EEA supply risk metrics — https://www.eea.europa.eu/en/circularity/thematic-metrics/materialsandwaste/evolution-of-eu-raw-materials-supply-risk

## Enrichment cost data

	Public techno-economic data for novel Li-6 enrichment routes is sparse; no industrial cost figures are publicly available.
	- Enrichment technology cost is a **scenario variable**: low / medium / high cost assumption per technology
	- Model is solved for each scenario; Pareto fronts are compared across scenarios
	- Shows policy-relevant insight: how sensitive the cost-risk trade-off is to enrichment cost uncertainty
	- Academically defensible: framework and trade-off structure are the contribution, not a single cost estimate

## Model type: MILP

	Two kinds of variables (decision-layers):
		1. binary: Is something done (yes = 1) or (no = 0) 	- build-decisions called Y and supply decisions called X   
		2. continuous: all values allowed 			- flows called Q

	Node structure:

	[Extraction & Processing] -> [Enrichment facility] -> [Consumer]

	- arrow = flow variable (continuous)
	- node = facility-open decision (binary)
	- multi-echelon MILP
	- Both objectives (cost, supply risk) are linear functions of those variables
	

to build (1) / not build (0) a facility

# MILP Formulation 
	
	- Adapted from Tsiakis et al. (2001), Ind. Eng. Chem. Res., 40, 3585-3604.

	# Sets & Indices

	| Symbol | Description 			| Size |
	|--------|-------------			|------|
	| e in E | enrichment sites 		| 3 |
	| t in T | enrichment technologies 	| 3 |
	| l in L | extraction & processing sites| 3 |
	| r in R | Reactors (customers) 	| 1 |

	# Decision Variables

	- Binary

	| Variable 		| Definition |
	|----------		|------------|
	| Y_et in {0,1} 	| 1 if enrichment site e with technology t is built |
	| X_let in {0,1} 	| 1 if extraction & processing site l supplies enrichment site e with technology t |
	| X_etr in {0,1} 	| 1 if enrichment site e with technology t supplies reactor r |

	# Continuous

	| Variable 		| Definition |
	|----------		|------------|
	| Q_let >= 0 		| Flow rate extraction & processing site l to enrichment site e with tecnology t |
	| Q_etr >= 0 		| Flow rate from enrichment site e with technology t to to reactor r |


## Constraints

	# Network Structure — link only if facility exists

		- A supply link can only be active if enrichment facility e is built.
		- Analogous to Tsiakis eq. (1): X_mk <= Y_m.

		- 9-equation formulation (technology aggregated): X_le <= Y_e for all e, l
		- 27-equation formulation (technology explicit): X_let <= Y_et for all e, t, l

	# Flow Activation — flow only if facility exists

		- Flow on a link is zero unless the upstream enrichment facility is built.
		- Analogous to Tsiakis eq. (6).

		- 9-equation: Q_el <= Q_el_max * Y_e for all e, l
		- 27-equation: Q_etl <= Q_etl_max * Y_et for all e, t, l

## Status

| Constraint group 			| Formulated 	| Coded |
|-----------------			|------------	|-------|
| 1. Network structure 		| done 		| no |
| 2. Minimum flow 			| done 		| no |
| 3. Flow activation 		| done 		| no |
| Material balance 			| no 		| no |
| Capacity bounds 			| no 		| no |
| Objective function 		| no 		| no |
