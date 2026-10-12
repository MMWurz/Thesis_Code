# Visualization: Pareto front plot and supply chain network figure for the dual-objective results.
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch
from matplotlib.ticker import FuncFormatter

import params
import model

TOL = 1e-6

####################### STYLE #######################
# Structure wears the echelon colours of the thesis schematic (L grey, E green, R purple).
# Data wears one sequential grey ramp: political instability g. Light enough throughout
# that all node text stays black; its pale end needs the echelon outline to show on white.
W_TEXT = 5.79                           # [in] thesis \textwidth = 418.26 pt = 14.70 cm
INK, INK2, FAINT = '#1a1a1a', '#55534f', '#e2e2e2'
ROUTE = INK                             # chosen links + outlines of chosen nodes
ECH = {'L': '#8c8c8c', 'E': '#64b719', 'R': '#822181'}         # strokes, sampled from the schematic
ECH_TXT = {'L': '#6e6e6e', 'E': '#4b8a13', 'R': '#822181'}     # darker twins: readable as 7-8 pt text
RISK_CMAP = LinearSegmentedColormap.from_list(                  # darkest step: black text still 6:1
    'risk', ['#ececec', '#d8d8d8', '#bfbfbf', '#a4a4a4', '#898989'])
G_NORM = Normalize(0.33, 0.70)          # fixed scale spanning the data -> every figure shares one meaning
FS = {'icon': 11, 'node': 8, 'num': 7}

NAME = {'r1': 'DEMO',                   # everything else shows its set-key suffix: l_Au -> Au
        't_dispEl': 'dispChr\nelChem'}  # two routes at equal cost, merged into one set member


def _name(key):
    return NAME.get(key, key.split('_', 1)[-1])


def _num(x, dec=0):                     # 89440 -> "89 440", thesis number style
    return f"{x:,.{dec}f}".replace(",", " ")


####################### PARETO FRONT #######################

def pareto_front(pareto):
    points = sorted(set(pareto))       # pareto = [(cost, SR), ...]; drop repeated points
    costs, srs = zip(*points)

    fig, ax = plt.subplots()
    ax.set_xlabel('supply risk SR_norm [–]')
    ax.set_ylabel('total cost [M€]')
    ax.grid(True)
    ax.scatter(srs, costs)             # markers only: a MILP front may have gaps -> never interpolate
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x/1e6:.2f}"))  # €->M€, kills the 1e7 offset
    return fig, ax


####################### SUPPLY-CHAIN NETWORK #######################

def snapshot(m, eps=None):
    """One solved point as plain floats. Call INSIDE the AUGMECON loop - m is overwritten
    by the next solve. Keeps plotting independent of pyomo and of the solver."""
    L, E, T, R = list(m.L), list(m.E), list(m.T), list(m.R)
    built = {e: t for e in E for t in T if m.Y_et[e, t].value > 0.5}
    return {
        'built':   built,
        'plants':  {e: 1 + round(m.N[e].value) for e in built},            # the flexible plant + N_e full-size ones
        'flow_le': {(l, e): q for l in L for e in E                        # [kg nat. Li/yr]
                    if (q := sum(m.Q_let[l, e, t].value for t in T)) > TOL},  # aggregated over t (one t per e)
        'flow_er': {e: q for e in E                                        # [kg enr. Li/yr]
                    if (q := sum(m.Q_etr[e, t, r].value for t in T for r in R)) > TOL},
        'cost':    m.obj_cost.expr(),                                      # [€/yr] evaluated, not re-derived
        'sr':      model.supply_risk_rule(m)(),
        'sr_extr': model.supply_risk_extr_rule(m)(),
        'sr_enr':  model.supply_risk_enr_rule(m)(),
        'eps':     eps,
    }


#  Layout in INCHES: the network axes is scaled 1 data unit = 1 inch, so rounded corners stay
#  round and a point is always 1/72. Columns are (left, right) edges of the group boxes.
X = {'L': (0.10, 1.20), 'e': (2.15, 3.00), 't': (3.22, 4.07), 'R': (4.75, 5.65)}
X_E = (2.05, 4.17)                      # outer enrichment box around the e and t columns
NODE_H, NODE_GAP, PAD, NODE_INSET = 0.24, 0.08, 0.08, 0.08
R_ICON = 0.16
LAB_OFF = 0.60                          # figure top -> group-label row (icons sit above)


def _stack_h(n):
    return n * NODE_H + (n - 1) * NODE_GAP


def _net_height():
    """Grows with the largest set, so adding a country or site in params.py resizes the
    figure instead of overflowing it."""
    n_max = max(len(params.L), len(params.E), len(params.T), len(params.R))
    return LAB_OFF + 0.24 + _stack_h(n_max) + 2 * PAD


def _box(ax, x0, y0, x1, y1, edge, lw, face='none', r=0.08, z=1):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle=f'round,pad=0,rounding_size={r}',
                                facecolor=face, edgecolor=edge, linewidth=lw, zorder=z))


def _column(keys, col, y_mid):         # node rectangles, first key on top, centred on y_mid
    x0, x1 = X[col][0] + NODE_INSET, X[col][1] - NODE_INSET
    top = y_mid + _stack_h(len(keys)) / 2
    return {k: (x0, top - i * (NODE_H + NODE_GAP) - NODE_H, x1, top - i * (NODE_H + NODE_GAP))
            for i, k in enumerate(keys)}


def _node(ax, rect, label, chosen, edge, g=None):
    """g given -> filled on the risk ramp, g printed right; no g -> white.
    Unchosen nodes keep a thin echelon outline - the ramp's pale end would vanish on white."""
    x0, y0, x1, y1 = rect
    face = RISK_CMAP(G_NORM(g)) if g is not None else 'white'
    ec, lw = (ROUTE, 1.6) if chosen else (edge, 0.8)
    _box(ax, x0, y0, x1, y1, ec, lw, face=face, r=0.04, z=4)
    ink = INK if (chosen or g is not None) else INK2
    yc = (y0 + y1) / 2
    weight = 'bold' if chosen else 'normal'
    if g is None:
        ax.text((x0 + x1) / 2, yc, label, ha='center', va='center', linespacing=1.0,
                fontsize=FS['num'] if '\n' in label else FS['node'],    # two names -> smaller, 2 lines
                color=ink, fontweight=weight, zorder=6)
        return
    ax.text(x0 + 0.06, yc, label, ha='left', va='center', fontsize=FS['node'],
            color=ink, fontweight=weight, zorder=6)
    ax.text(x1 - 0.06, yc, f"{g:.3f}", ha='right', va='center', fontsize=FS['num'], color=ink, zorder=6)


def _link(ax, p0, p1, width=None, head=True):
    """Hairline for an option, thick route line (width in pt) for what was chosen."""
    if width is None:
        ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle='-', color=FAINT, linewidth=0.45, zorder=2))
        return
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle='-|>' if head else '-', color=ROUTE,
                                 linewidth=width, mutation_scale=8, shrinkA=0, shrinkB=0.5,
                                 joinstyle='miter', capstyle='butt', zorder=5))


def _header(ax, H):
    """Echelon icons with their letter, centred over each group - as in the schematic."""
    cy = H - 0.06 - R_ICON
    for k, cx in {'L': sum(X['L']) / 2, 'E': sum(X_E) / 2, 'R': sum(X['R']) / 2}.items():
        ax.add_patch(Circle((cx, cy), R_ICON, facecolor='white', edgecolor=ECH[k], linewidth=1.2, zorder=3))
        ax.text(cx, cy, k, ha='center', va='center', fontsize=FS['icon'], color=ECH_TXT[k], zorder=4)


def _draw_network(ax, snap, H):
    ax.set_xlim(0, W_TEXT), ax.set_ylim(0, H)
    ax.set_axis_off()
    _header(ax, H)

    # group boxes - one row of labels, all inner boxes share top and bottom
    lab_y = H - LAB_OFF                                              # label row, inside the outer E box
    top = lab_y - 0.10
    bot = top - _stack_h(max(len(params.L), len(params.E), len(params.T))) - 2 * PAD
    y_mid = (top + bot) / 2
    _box(ax, X_E[0], bot - 0.06, X_E[1], lab_y + 0.13, ECH['E'], 1.0)            # outer enrichment box
    for col, ech, lab in [('L', 'L', 'Location $l$'), ('e', 'E', 'Location $e$'),
                          ('t', 'E', 'Technology $t$')]:
        _box(ax, X[col][0], bot, X[col][1], top, ECH[ech], 1.0)
        ax.text(sum(X[col]) / 2, lab_y, lab, ha='center', va='center', fontsize=FS['num'],
                color=ECH_TXT[ech])
    r_half = _stack_h(len(params.R)) / 2 + PAD                       # reactor box hugs its node(s)
    _box(ax, X['R'][0], y_mid - r_half, X['R'][1], y_mid + r_half, ECH['R'], 1.0)

    # nodes - every option is drawn, sorted safest on top, so the figure shows the risk landscape
    n_l = _column(sorted(params.L, key=lambda k: params.g_extr[k]), 'L', y_mid)
    n_e = _column(sorted(params.E, key=lambda k: params.g_enr[k]), 'e', y_mid)
    n_t = _column(list(params.T), 't', y_mid)
    n_r = _column(list(params.R), 'R', y_mid)
    built = snap['built']                                            # {e: t}
    sourcing = {l for l, _ in snap['flow_le']}
    for l, rc in n_l.items():
        _node(ax, rc, _name(l), l in sourcing, ECH['L'], g=params.g_extr[l])
    for e, rc in n_e.items():
        _node(ax, rc, _name(e), e in built, ECH['E'], g=params.g_enr[e])
    for t, rc in n_t.items():
        _node(ax, rc, _name(t), t in built.values(), ECH['E'])
    for r, rc in n_r.items():
        _node(ax, rc, _name(r), True, ECH['R'])

    right = lambda rc: (rc[2], (rc[1] + rc[3]) / 2)                 # noqa: E731 - edge midpoints
    left = lambda rc: (rc[0], (rc[1] + rc[3]) / 2)                  # noqa: E731

    # L -> e : all options as hairlines, the chosen ones scaled by share of the feed
    feed = sum(snap['flow_le'].values())
    for l in n_l:
        for e in n_e:
            q = snap['flow_le'].get((l, e))
            p0, p1 = right(n_l[l]), left(n_e[e])
            _link(ax, p0, p1, None if q is None else 0.8 + 2.2 * q / feed)
            if q:
                mx, my = p0[0] + 0.45 * (p1[0] - p0[0]), p0[1] + 0.45 * (p1[1] - p0[1])
                ax.text(mx, my, f"{100 * q / feed:.0f} %", ha='center', va='center', fontsize=FS['num'],
                        color=INK, zorder=7,
                        bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor='none'))

    # e - t : which technology the built site runs (a pairing, not a transport link -> no head)
    d_tot = sum(snap['flow_er'].values())
    for e, t in built.items():
        _link(ax, right(n_e[e]), left(n_t[t]), 0.8 + 2.2 * snap['flow_er'].get(e, 0) / d_tot, head=False)

    # t -> R : hairline per technology, the used one(s) as route
    for t in n_t:
        q = sum(snap['flow_er'].get(e, 0) for e, tt in built.items() if tt == t)
        for r in n_r:
            _link(ax, right(n_t[t]), left(n_r[r]), 0.8 + 2.2 * q / d_tot if q else None)


#  legend block under the network: cost and SR, nothing else

def _draw_legend(ax, snap, h):
    ax.set_xlim(0, W_TEXT), ax.set_ylim(0, h)
    ax.set_axis_off()
    y = h / 2                                                        # one line: cost left, SR right
    ax.text(0.12, y, f"cost   {snap['cost'] / 1e6:.2f} M€/yr", ha='left', va='center',
            fontsize=FS['node'], color=INK, fontweight='bold')
    ax.text(W_TEXT - 0.12, y, rf"$\mathbf{{SR_{{norm}}\ \ {snap['sr']:.3f}}}$   (SR$_L$ = {snap['sr_extr']:.3f},  "
            f"SR$_E$ = {snap['sr_enr']:.3f})", ha='right', va='center', fontsize=FS['node'], color=INK)


def _risk_colourbar(fig, cax):
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=G_NORM, cmap=RISK_CMAP), cax=cax, orientation='horizontal')
    cb.set_label('political instability $g$ [–]        safe  →  risky', fontsize=FS['num'], color=INK2, labelpad=2)
    cb.ax.tick_params(labelsize=FS['num'], length=2, pad=1.5, colors=INK2)
    cb.outline.set_visible(False)


def supply_chain_network(snap, figsize=None):
    """Chosen route through the full option network for ONE Pareto point, legend underneath."""
    net_h, leg_h, cb_h = _net_height(), 0.22, 0.09
    total = net_h + 0.08 + leg_h + 0.10 + cb_h + 0.34
    fig = plt.figure(figsize=figsize or (W_TEXT, total))

    def place(top, h, x0=0.0, w=W_TEXT):                            # inches from the top -> axes
        return fig.add_axes([x0 / W_TEXT, 1 - (top + h) / total, w / W_TEXT, h / total])

    _draw_network(place(0, net_h), snap, net_h)
    _draw_legend(place(net_h + 0.08, leg_h), snap, leg_h)
    _risk_colourbar(fig, place(net_h + 0.08 + leg_h + 0.10, cb_h, x0=0.12, w=W_TEXT - 0.24))
    return fig, fig.axes
