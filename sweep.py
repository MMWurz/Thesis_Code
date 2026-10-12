# %% Commercial scenario: solves the model at every fusion fleet size and reports both payoff-table corners.
# Run: "Run Cell" above this line (about 30 s). Tables and figures appear below the cell, CSV and PDF go to runs/.
# Edits no other file: a fleet size is a temporary patch of params.D_r1, made through sensitivities.run_case.
import os

import matplotlib.pyplot as plt
import pandas as pd
from IPython.display import display
from matplotlib.backends.backend_pdf import PdfPages

import params
import plots
import sensitivities as sens

####################### INPUT #######################

# Fusion electricity generation [TWh/yr] of the 24 scenarios, Mantilla 2026 Tab. 4.1: (low, reference, high) fusion cost.
# Scenario code: Y/N = variable renewables capped/uncapped, E/L = early/late availability, F/S = fast/slow deployment.
GEN_TWH = {
    2050: {'YEF': (  756,   756,   756), 'NEF': (  582,   582,   573),
           'YES': (  134,   134,   134), 'NES': (  134,   134,   134),
           'YLF': (    0,     0,     0), 'NLF': (    0,     0,     0),
           'YLS': (    0,     0,     0), 'NLS': (    0,     0,     0)},
    2070: {'YEF': ( 7372,  7372,  7372), 'NEF': ( 7372,  5214,  4697),
           'YES': ( 1232,  1232,  1232), 'NES': ( 1232,  1232,  1232),
           'YLF': (  504,   504,   504), 'NLF': (  504,   504,   439),
           'YLS': (   89,    89,    89), 'NLS': (   89,    89,    89)},
    2100: {'YEF': (28954, 28954, 28962), 'NEF': (28142, 25415, 20656),
           'YES': ( 4841,  4841,  4841), 'NES': ( 4841,  4841,  4841),
           'YLF': (13758, 13758, 13758), 'NLF': (13219,  5940,  5253),
           'YLS': ( 2298,  2298,  2298), 'NLS': ( 2298,  2298,  2298)},
}
CF = 0.8                                # [-] capacity factor, Mantilla 2026 Tab. 3.1

# Fleet size -> annual demand. FIRST FILL ONLY: every plant gets one breeder inventory, bought over T_FILL years.
INV_PER_GWFUS = 26_000                  # [kg enr. Li/GW_fus] Giegerich 2019, the figure behind params.D_r1 (52 t for 2 GW_fus)
GWFUS_PER_GWE = 3.0                     # [GW_fus/GW_e] OPEN: no source yet
T_FILL        = 10                      # [yr] OPEN: time frame of the first fills. 10 yr is the DEMO value, a placeholder

N_GRID  = 25                            # grid points between the smallest and the largest scenario fleet, even on a log axis
Q_FRONT = 20                            # intervals of one Pareto front
LEX_TOL = 1e-9                          # [-] relative tolerance of the corner solves: with the exact freeze of sensitivities.corner
                                        #     GLPK finds no solution for single fleet sizes (cost ~1e10 EUR). Moves a corner < 3e-8


####################### FLEET SIZES #######################

def scenario_fleets():
    """Distinct fleet sizes of the 24 scenarios x 3 years: {fleet [GW_e]: {year: [scenario codes]}}, without the zeros."""
    out = {}
    for year, rows in GEN_TWH.items():
        for code, gens in rows.items():
            for cost, twh in zip('LRH', gens):
                if twh:
                    fleet = twh * 1000 / (8760 * CF)                                    # TWh/yr -> GW_e, equ_4_fleet_size
                    fleet = next((f for f in out if abs(f - fleet) < 1e-3 * f), fleet)  # 28 954 and 28 962 TWh are one fleet
                    out.setdefault(fleet, {}).setdefault(year, []).append(f"{code}-{cost}")
    return dict(sorted(out.items()))


def grid(lo, hi, n=N_GRID):                             # n fleet sizes from lo to hi, evenly spaced on a log axis
    return [lo * (hi / lo) ** (i / (n - 1)) for i in range(n)]


def demand(fleet):                                      # [GW_e] -> [kg enr. Li/yr]
    return fleet * GWFUS_PER_GWE * INV_PER_GWFUS / T_FILL


def lithium_limit():                                    # [kg enr. Li/yr] the most all extraction sites together can feed
    return sum(params.Cap_l.values()) / params.f_ne     # enrichment has no limit: a site holds as many plants as needed


####################### ONE FLEET SIZE #######################

def run_fleet(fleet, scenarios=''):
    """Both corners of one fleet size, for a scenario fleet also its Pareto front: -> table row, front rows.
    A fleet the model cannot supply comes back as 'no solution': under today's capacities that is the bottleneck."""
    d = demand(fleet)
    row = {'fleet_GWe': fleet, 'scenarios': scenarios, 'demand_kg_yr': d, 'status': 'optimal'}
    try:
        cheap, safe = sens.run_case(leaves={'D_r1': d}, lex_tol=LEX_TOL)
    except RuntimeError:                                                    # sens.solve found no optimum
        row['status'] = f"no solution: demand {plots._num(d / 1e3)} t/yr" + (
            f" > lithium supply {plots._num(lithium_limit() / 1e3)} t/yr" if d > lithium_limit() else "")
        return row, []
    row.update(sens.result(cheap, safe), cost_kg_cheap=cheap['cost'] / d, cost_kg_safe=safe['cost'] / d)
    if not scenarios:                                                       # a grid point: corners only
        return row, []
    return row, [{'fleet_GWe': fleet, 'scenarios': scenarios, **p} for p in sens.front(cheap, safe, Q_FRONT)]


####################### OUTPUT #######################

def sweep_table(table):
    """Both corners of EVERY fleet size, grid points included. Costs and premium in M EUR/yr."""
    df = pd.DataFrame(table)
    df['fleet [GWe]'] = df.fleet_GWe.round().astype(int)
    df['demand [t/yr]'] = (df.demand_kg_yr / 1e3).round().astype(int)
    return sens.corner_table(df, ['fleet [GWe]', 'demand [t/yr]', 'scenarios', 'status'])


def front_page(row, front):
    """One figure: scenario codes, year and fleet size on top, the Pareto front, both corners written out below.
    front = the front rows of this fleet size."""
    head = (f"{row['scenarios']}\nfleet size {plots._num(row['fleet_GWe'])} GWe  →  "
            f"demand {plots._num(row['demand_kg_yr'] / 1e3)} t enr. Li/yr")
    corners = {'cheap': ('Min cost', -9, 'right'), 'safe': ('Min risk', 9, 'left')}     # name, label offset [pt], side
    points = [(p['cost'], p['sr']) for p in front] + [(row[f'cost_{c}'], row[f'sr_{c}']) for c in corners]
    fig, ax = plots.pareto_front(points)                                    # same look as the DEMO front
    fig.set_size_inches(plots.W_TEXT, 5.0)
    fig.subplots_adjust(left=0.17, right=0.95, top=0.89, bottom=0.37)
    ax.set_title(head, loc='left', fontsize=plots.FS['node'] + 1, color=plots.INK)
    lines = []
    for c, (name, dx, side) in corners.items():
        xy = (row[f'sr_{c}'], row[f'cost_{c}'])
        ax.scatter(*xy, s=110, facecolors='none', edgecolors=plots.INK, linewidths=1.0, zorder=3)   # ring around the corner
        ax.annotate(name.lower(), xy, xytext=(dx, 0), textcoords='offset points', ha=side, va='center',
                    fontsize=plots.FS['node'], color=plots.INK)
        lines += [f"{name}:  {row[f'cost_{c}'] / 1e6:.2f} M€/yr  ·  {plots._num(row[f'cost_kg_{c}'])} €/kg enr. Li"
                  f"  ·  SR {row[f'sr_{c}']:.4f}",
                  f"      {row[f'chain_{c}']}"]
    lines.append(f"Premium of the min-risk chain:  {row['premium'] / 1e6:.2f} M€/yr  (+{row['premium_pct']:.0f} %)")
    fig.text(0.17, 0.26, "\n".join(lines), va='top', linespacing=1.5, fontsize=plots.FS['node'], color=plots.INK)
    return fig


def front_pages(table, fronts):
    """One front_page per scenario fleet that has a solution, all of them the pages of runs/sweep_fronts.pdf."""
    figs = []
    with PdfPages(os.path.join(sens.OUT, 'sweep_fronts.pdf')) as pdf:
        for row in table:
            if row['scenarios'] and row['status'] == 'optimal':
                figs.append(front_page(row, [p for p in fronts if p['fleet_GWe'] == row['fleet_GWe']]))
                pdf.savefig(figs[-1])
                plt.close(figs[-1])                                         # closed for pyplot only, as sens.save
    return figs


####################### RUN #######################

def run_sweep():
    """Every scenario fleet and the grid points between them: -> table rows, front rows."""
    marks = scenario_fleets()
    table, fronts = [], []
    for fleet in sorted(set(marks) | set(grid(min(marks), max(marks))[1:-1])):          # the two grid ends ARE scenario fleets
        head = "; ".join(f"{year}: {', '.join(codes)}" for year, codes in marks.get(fleet, {}).items())
        print(f"{fleet:.0f} GWe", end=' | ', flush=True)                                # sign of life: the fleet being solved
        row, points = run_fleet(fleet, scenarios=head)
        table.append(row)
        fronts += points
    print()
    sens.write_csv('sweep_corners.csv', table)
    sens.write_csv('sweep_fronts.csv', fronts)
    sens.reset()
    return table, fronts


if __name__ == '__main__':                              # true in a cell and in "python sweep.py", not on import
    sens.self_test()
    table, fronts = run_sweep()
    display(sweep_table(table), *front_pages(table, fronts))
    print(f"saved in {sens.OUT}: sweep_corners.csv, sweep_fronts.csv, sweep_fronts.pdf")

# %%
