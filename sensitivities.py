# %% Sensitivity analysis: solves the DEMO model with ONE input changed per run and reports both payoff-table corners.
# Run: "Run Cell" above this line (about 1 min). Tables and figures appear below the cell, CSV and PDF go to runs/.
# Edits no other file: a case is a temporary patch of the loaded params / supply_risk modules, undone by reset().
import importlib
import os
import sys

os.environ["PATH"] = os.path.join(sys.prefix, "Library", "bin") + os.pathsep + os.environ["PATH"]   # glpsol, as in main.ipynb

import matplotlib.pyplot as plt
import pandas as pd
from IPython import get_ipython
from IPython.display import display
from pyomo.environ import SolverFactory, Constraint, TerminationCondition, value

import params
import supply_risk
import conversions
import model
import plots

if get_ipython():                                       # as main.ipynb: an edited .py file is reloaded before the next run
    get_ipython().extension_manager.load_extension('autoreload')
    get_ipython().run_line_magic('autoreload', '2')
pd.set_option('display.max_rows', None, 'display.max_colwidth', None)       # tables are shown in full

####################### INPUT #######################

PCT = 0.10                              # [-] one-at-a-time change of every continuous input, see tornado_cases

solver = SolverFactory('glpk')
OUT = os.path.join(os.path.dirname(params.__file__), 'runs')
os.makedirs(OUT, exist_ok=True)
TOL = 1e-6

# what params.py / supply_risk.py compute from other parameters -> never patch these, patch their source
DERIVED = ('Q_max_enr', 'Q_max_nat', 'Cap_et_min', 'Cap_et', 'N_max', 'CRF_e', 'M_e', 'Qbar', 'CCbar',
           'seg_width', 'seg_slope', 'TC_let', 'TC_etr', 'EC_et')
SR_SCALARS = ('HHI_extr', 'D_nat', 'HHI_enr', 'D_enr')

COUNTRY_L = {'l_Au': 'Australia', 'l_Ci': 'Chile', 'l_Ch': 'China', 'l_Ar': 'Argentina', 'l_Fr': 'France'}  # as params.g_extr
COUNTRY_E = {'e_US': 'US', 'e_EU': 'EU', 'e_Ch': 'China', 'e_Ru': 'Russia'}                                 # as params.g_enr


####################### PATCHING #######################

def reset():                                            # back to the values written in params.py
    importlib.reload(params)
    importlib.reload(supply_risk)


def rederive():
    """Recompute everything params.py and supply_risk.py derive from other parameters - same formulas.
    Both files do this ONCE at import, so changing f_ne alone would leave Cap_et, Q_max_nat and D_nat old."""
    p = params
    p.Q_max_enr  = p.D_r1
    p.Q_max_nat  = p.f_ne * p.D_r1
    p.Cap_et_min = {(e, t): p.f_ne * p.Cap_e_min_prod for e in p.E for t in p.T}
    p.Cap_et     = {(e, t): p.f_ne * p.Cap_e_prod     for e in p.E for t in p.T}
    p.N_max      = int(p.D_r1 // p.Cap_e_prod)
    p.CRF_e = {e: conversions.capital_recovery_factor(p.i_e[e], p.n_life) for e in p.E}
    p.M_e   = {e: (p.CRF_e[e] + p.fom) * p.f_e[e] for e in p.E}
    p.Qbar  = conversions.geometric_breakpoints(p.Cap_e_min_prod, p.Cap_e_prod, n_seg=4)
    p.CCbar = [conversions.capex_power_law(q, p.CC_ref, p.Q_ref, p.b_scale) for q in p.Qbar]
    p.seg_width, p.seg_slope = conversions.pwl_segments(p.Qbar, p.CCbar)
    p.TC_let = {(l, e, t): p.TC_le[(l, e)] for l in p.L for e in p.E for t in p.T}
    p.TC_etr = {(e, t, r): p.TC_er[(e, r)] for e in p.E for t in p.T for r in p.R}
    p.EC_et  = {(e, t): p.EC_e[t] for e in p.E for t in p.T}
    supply_risk.HHI_extr = supply_risk.hhi(p.s_extr_k)
    supply_risk.D_nat    = p.f_ne * p.D_r1
    supply_risk.HHI_enr  = supply_risk.hhi(p.s_enr_k)
    supply_risk.D_enr    = p.D_r1


def self_test():
    """rederive() must reproduce params.py: with nothing patched, no derived value may move."""
    reset()
    before = {a: getattr(params, a) for a in DERIVED} | {a: getattr(supply_risk, a) for a in SR_SCALARS}
    rederive()
    after = {a: getattr(params, a) for a in DERIVED} | {a: getattr(supply_risk, a) for a in SR_SCALARS}
    moved = [a for a in before if before[a] != after[a]]
    assert not moved, f"rederive() disagrees with params.py for {moved}"
    assert {l: params.g_25[c] for l, c in COUNTRY_L.items()} == params.g_extr, "COUNTRY_L differs from params.g_extr"
    assert {e: params.g_25[c] for e, c in COUNTRY_E.items()} == params.g_enr,  "COUNTRY_E differs from params.g_enr"
    print("self-test OK: rederive() reproduces params.py")


####################### SOLVING #######################

def solve(m):
    res = solver.solve(m)
    if res.solver.termination_condition != TerminationCondition.optimal:
        raise RuntimeError(f"solve not optimal: {res.solver.termination_condition}")


def corner(first, second, tol=0.0):
    """Lexicographic optimum (main.ipynb m2 / m3): best `first`, then the best `second` that keeps it.
    tol > 0 keeps it only within that relative tolerance: at commercial demand (cost ~1e10 EUR) GLPK calls
    the exact freeze infeasible for some demands, sweep.py therefore passes 1e-9."""
    m = model.build_model(params)
    obj = {'cost': m.obj_cost, 'SR': m.obj_SR}
    obj['cost'].deactivate()
    obj['SR'].deactivate()
    obj[first].activate()
    solve(m)                                                            # round 1
    best = value(obj[first])
    m.c_lex = (Constraint(expr=obj[first].expr == best) if tol == 0     # freeze it at its optimum
               else Constraint(expr=obj[first].expr <= best * (1 + tol)))
    obj[first].deactivate()
    obj[second].activate()
    solve(m)                                                            # round 2
    return plots.snapshot(m)


def front(cheap, safe, q=20):
    """AUGMECON loop (main.ipynb m4) between the two corners of the case that is patched right now:
    one row per feasible grid point, safest first."""
    SR_min, SR_max = round(safe['sr'], 6), round(cheap['sr'], 6)        # rounded as in main.ipynb
    if SR_max <= SR_min:                                                # no trade-off left: the front is one point
        return []
    r_SR = SR_max - SR_min
    m = model.build_model(params, delta=1e-3, r_SR=r_SR)
    m.obj_cost.deactivate()
    m.obj_SR.deactivate()
    m.c_eps.activate()
    m.obj_augmecon.activate()
    rows = []
    for k in range(q + 1):
        m.eps = SR_min + k * (r_SR / q)
        if solver.solve(m).solver.termination_condition == TerminationCondition.optimal:   # eps = SR_min is often infeasible
            s = plots.snapshot(m)
            rows.append({'eps': value(m.eps), 'sr': s['sr'], 'cost': s['cost'], 'chain': label(s)})
    return rows


def check(s):
    """Invariants of main.ipynb test_solution, on a snapshot."""
    feed, prod = sum(s['flow_le'].values()), sum(s['flow_er'].values())
    assert abs(feed - supply_risk.D_nat) < TOL * supply_risk.D_nat, f"sum Q_let {feed} != D_nat {supply_risk.D_nat}"
    assert abs(prod - supply_risk.D_enr) < TOL * supply_risk.D_enr, f"sum Q_etr {prod} != D_enr {supply_risk.D_enr}"
    ge, gn = params.g_extr.values(), params.g_enr.values()
    assert supply_risk.HHI_extr * min(ge) - TOL <= s['sr_extr'] <= supply_risk.HHI_extr * max(ge) + TOL, "SR_extr out of bounds"
    assert supply_risk.HHI_enr  * min(gn) - TOL <= s['sr_enr']  <= supply_risk.HHI_enr  * max(gn) + TOL, "SR_enr out of bounds"


def label(s):                                           # "l_Ar 100% | e_Ch | t_dispEl", as printed in main.ipynb
    feed, src = sum(s['flow_le'].values()), {}          # a site with several plants reads "e_Ch x3"
    for (l, e), q in s['flow_le'].items():
        src[l] = src.get(l, 0) + q
    return (" + ".join(f"{l} {q / feed:.0%}" for l, q in src.items())
            + " | " + "/".join(e if n == 1 else f"{e} x{n}" for e, n in s['plants'].items())
            + " | " + "/".join(s['built'].values()))


####################### ONE CASE #######################

def run_case(leaves=None, hhi=None, lex_tol=0.0):
    """Patches the parameters and solves both corners: -> cheap, safe. The patch stays until the next reset().
    leaves  = {params attribute: new value}, set BEFORE rederive().
    hhi     = {'HHI_extr' / 'HHI_enr': number}, set AFTER it (rederive rebuilds both from the shares).
    lex_tol = relative tolerance of the two corner solves, see corner()."""
    reset()
    for a, v in (leaves or {}).items():
        assert hasattr(params, a) and a not in DERIVED, f"'{a}' is not a source parameter of params.py"
        setattr(params, a, v)
    rederive()
    for a, v in (hhi or {}).items():
        assert a in ('HHI_extr', 'HHI_enr'), f"'{a}' is not an HHI"
        setattr(supply_risk, a, v)
    safe, cheap = corner('SR', 'cost', lex_tol), corner('cost', 'SR', lex_tol)
    check(safe)
    check(cheap)
    return cheap, safe


def result(cheap, safe):                                # the result columns of every table and CSV
    return {'cost_cheap': cheap['cost'], 'sr_cheap': cheap['sr'], 'chain_cheap': label(cheap),
            'cost_safe':  safe['cost'],  'sr_safe':  safe['sr'],  'chain_safe':  label(safe),
            'premium':     safe['cost'] - cheap['cost'],                    # [EUR/yr] what the safest chain costs extra
            'premium_pct': 100 * (safe['cost'] / cheap['cost'] - 1)}


####################### CASES #######################

def scenario_cases():
    """The alternative values the thesis names (6_results.tex, tab_5_sensitivity_scenarios): {name: run_case arguments}."""
    reset()
    p, g3 = params, params.g_3
    return {
        'S0 baseline':                {},
        'S1 HHI_extr reserves 0.193': dict(hhi={'HHI_extr': 0.193}),                                # tab_4_HHI_reserves_check
        'S2 g 3-yr average':          dict(leaves={'g_extr': {l: g3[c] for l, c in COUNTRY_L.items()},
                                                   'g_enr':  {e: g3[c] for e, c in COUNTRY_E.items()}}),    # tab_4_WGI_PV
        'S3 EU port France':          dict(leaves={'TC_le': {**p.TC_le,                             # App. B: only the lanes into e_EU
                                                             ('l_Au', 'e_EU'): 1.750, ('l_Ci', 'e_EU'): 1.574,
                                                             ('l_Ch', 'e_EU'): 1.676, ('l_Ar', 'e_EU'): 1.372,
                                                             ('l_Fr', 'e_EU'): 0.0}}),              # l_Fr is the same port
        'S4a f_ne 13.5':              dict(leaves={'f_ne': 13.5}),                                  # x_w = 1 %
        'S4b f_ne 23.9':              dict(leaves={'f_ne': 23.9}),                                  # x_w = 4 %
        'S5 b 0.73':                  dict(leaves={'b_scale': 0.73}),                               # Rothwell, centrifuge plants
        'S6 f_Ru 0.57':               dict(leaves={'f_e': {**p.f_e, 'e_Ru': 0.57}}),                # nuclear overnight-cost ratio
        'S7 EC_amalgam 1000':         dict(leaves={'EC_e': {**p.EC_e, 't_amalgam': 1000}}),         # 1982 COLEX figure
        'S8a HHI_enr 0.25':           dict(hhi={'HHI_enr': 0.25}),                                  # four equal suppliers
        'S8b HHI_enr 1.0':            dict(hhi={'HHI_enr': 1.0}),                                   # a single supplier
    }


def tornado_cases():
    """Every continuous input at -PCT and +PCT, one at a time: {(input, '-' or '+'): run_case arguments}.
    The capacities are in although none binds at DEMO demand: a bar of zero is a result too.
    Left out: Q_ref (pairs with CC_ref), g (covered by S2)."""
    reset()
    p, out = params, {}
    for sign, f in (('-', 1 - PCT), ('+', 1 + PCT)):
        for a in ('f_ne', 'D_r1', 'CC_ref', 'b_scale', 'fom', 'n_life', 'Cap_e_prod', 'Cap_e_min_prod'):    # scalars
            out[a, sign] = dict(leaves={a: getattr(p, a) * f})
        for a in ('PC_l', 'EC_e', 'f_e', 'i_e', 'Cap_l'):                               # one country / technology at a time
            for k, v in getattr(p, a).items():
                out[f"{a} {k.split('_', 1)[-1]}", sign] = dict(leaves={a: {**getattr(p, a), k: v * f}})
        for a in ('TC_le', 'TC_er'):                                                    # all lanes together = the freight rate
            out[f"{a} (all lanes)", sign] = dict(leaves={a: {k: v * f for k, v in getattr(p, a).items()}})
        for a in ('HHI_extr', 'HHI_enr'):
            out[a, sign] = dict(hhi={a: getattr(supply_risk, a) * f})
    return out


####################### OUTPUT #######################

def write_csv(fname, rows):
    pd.DataFrame(rows).to_csv(os.path.join(OUT, fname), index=False)


def save(fig, fname):                                   # closed for pyplot only: the figure can still be displayed
    fig.savefig(os.path.join(OUT, fname))
    plt.close(fig)
    return fig


def corner_table(rows, lead):
    """Result rows as a table, columns as tab_5_sensitivity_scenarios. Costs and premium in M EUR/yr.
    lead = the column(s) of `rows` that name a row."""
    df = pd.DataFrame(rows).set_index(lead)
    return pd.DataFrame({('cost-optimal', 'cost'): (df.cost_cheap / 1e6).round(2), ('cost-optimal', 'SR'): df.sr_cheap.round(4),
                         ('risk-optimal', 'cost'): (df.cost_safe / 1e6).round(2),  ('risk-optimal', 'SR'): df.sr_safe.round(4),
                         ('premium', 'abs.'):      (df.premium / 1e6).round(2),    ('premium', '[%]'):     df.premium_pct.round(1),
                         ('chain', 'cost-optimal'): df.chain_cheap,                ('chain', 'risk-optimal'): df.chain_safe})


def tornado(base, rows):
    """Change against the baseline [M EUR/yr] of the cost-optimal cost and of the cost premium at -PCT and +PCT,
    one line per input in run order. * = a corner decision changed."""
    keys = list(dict.fromkeys(k for k, _ in rows))
    star = {k: ' *' if any(rows[k, s][c] != base[c] for s in '-+' for c in ('chain_cheap', 'chain_safe')) else ''
            for k in keys}
    return pd.DataFrame({(head, f"{s}{PCT:.0%}"): [(rows[k, s][metric] - base[metric]) / 1e6 for k in keys]
                         for metric, head in (('cost_cheap', 'cost-optimal cost'), ('premium', 'cost premium'))
                         for s in '-+'}, index=[k + star[k] for k in keys])


def tornado_table(d):
    """tornado() with the rows of tab_5_sensitivity_oat: largest effect on the cost premium on top."""
    t = d.round(2) + 0.0                                                                # + 0.0: "-0.00" becomes "0.00"

    def size(k):
        return t.loc[k, 'cost premium'].abs().max(), t.loc[k, 'cost-optimal cost'].abs().max()

    return t.loc[sorted(t.index, key=size, reverse=True)]                               # ties keep their run order


def tornado_plot(d, head, xlabel, fname):
    """One column pair of tornado() as bars, EVERY input, largest effect on top."""
    bars = d[head]
    bars = bars.loc[sorted(bars.index, key=lambda k: d.loc[k, head].abs().max())]       # ties keep their run order
    y = range(len(bars))
    fig, ax = plt.subplots(figsize=(plots.W_TEXT, 0.2 * len(bars) + 0.95))
    for sign, colour in zip(bars.columns, ('#bfbfbf', plots.INK2)):                     # two greys: survives a b/w print
        ax.barh(y, bars[sign], height=0.62, color=colour, label=sign)
    ax.axvline(0, color=plots.INK, linewidth=0.8)
    ax.set_yticks(y, list(bars.index), fontsize=plots.FS['node'], color=plots.INK)
    ax.set_xlabel(xlabel, fontsize=plots.FS['node'], color=plots.INK)
    ax.tick_params(axis='x', labelsize=plots.FS['num'], colors=plots.INK2)
    ax.tick_params(axis='y', length=0)
    ax.grid(axis='x', color=plots.FAINT, linewidth=0.5)
    ax.set_axisbelow(True)
    for side in ('top', 'right', 'left'):
        ax.spines[side].set_visible(False)
    ax.legend(title='parameter changed by', fontsize=plots.FS['num'], title_fontsize=plots.FS['num'],
              frameon=False, loc='lower right')
    fig.tight_layout()
    return save(fig, fname)


####################### RUN #######################

def run_scenarios():
    """Part 1, the alternative values: -> table rows, front rows, {caption: figure of a corner chain}."""
    table, fronts, chains = [], [], {}
    for name, case in scenario_cases().items():
        print(name, end=' | ', flush=True)                                  # sign of life: the case being solved
        cheap, safe = run_case(**case)
        table.append({'case': name, **result(cheap, safe)})
        fronts += [{'case': name, **p} for p in front(cheap, safe)]
        for c, s in (('cheap', cheap), ('safe', safe)):                     # drawn now: the figure reads the patched g
            fname = f"chain_{name.split()[0]}_{c}.pdf"
            chains[f"{name}: {fname}"] = save(plots.supply_chain_network(s)[0], fname)
    print()
    write_csv('scenarios.csv', table)
    write_csv('fronts.csv', fronts)
    reset()
    return table, fronts, chains


def run_tornado():
    """Part 2, one input at a time: -> baseline row, {(input, '-' or '+'): row}."""
    base = result(*run_case())
    rows = {}
    for (k, sign), case in tornado_cases().items():
        print(f"{k} {sign}{PCT:.0%}", end=' | ', flush=True)                # sign of life: the case being solved
        rows[k, sign] = result(*run_case(**case))
    print()
    write_csv('tornado.csv', [{'case': 'baseline', **base}]
              + [{'case': f"{k} {sign}{PCT:.0%}", **row} for (k, sign), row in rows.items()])
    reset()
    return base, rows


if __name__ == '__main__':                              # true in a cell and in "python sensitivities.py", not on import
    self_test()
    table, fronts, chains = run_scenarios()
    display(corner_table(table, 'case'))
    base, rows = run_tornado()
    d = tornado(base, rows)
    display(tornado_table(d),
            tornado_plot(d, 'cost-optimal cost', 'change of the cost-optimal total cost [M€/yr]', 'tornado_cost.pdf'),
            tornado_plot(d, 'cost premium', 'change of the cost premium, safest minus cheapest chain [M€/yr]',
                         'tornado_premium.pdf'))
    for caption, fig in chains.items():
        print(caption)
        display(fig)
    print(f"saved in {OUT}: scenarios.csv, fronts.csv, tornado.csv, tornado_*.pdf, chain_*.pdf")

# %%
