# Visualization: Pareto front plots, supply chain flow diagrams, and sensitivity analysis charts for dual-objective results.
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Rectangle, FancyArrowPatch
from matplotlib.ticker import FuncFormatter

import params
import supply_risk
import model

TOL = 1e-6

####################### STYLE #######################
# One sequential blue ramp carries political instability g; one warm accent carries the chosen route.
# Ramp starts at step 250 - anything lighter drops below 2:1 contrast on white and reads as an empty box.
W_TEXT = 5.79                           # [in] thesis \textwidth = 418.26 pt = 14.70 cm
INK, INK2, FAINT = '#0b0b0b', '#52514e', '#dcdcd8'
ACCENT = '#eb6834'                      # active route only - never used on a node
RISK_CMAP = LinearSegmentedColormap.from_list(
    'risk', ['#86b6ef', '#5598e7', '#2a78d6', '#1c5cab', '#104281'])
G_LIM = (0.30, 0.70)                    # fixed scale: every panel must share one colour meaning
FS = {'node': 8, 'num': 7, 'slot': 7, 'box': 8, 'tick': 7}

# SR bar reference scale: what the two echelons could attain at their safest / riskiest extreme
SR_FLOOR = (supply_risk.HHI_extr * min(params.g_extr.values())
            + supply_risk.HHI_enr * min(params.g_enr.values()))
SR_CEIL = (supply_risk.HHI_extr * max(params.g_extr.values())
           + supply_risk.HHI_enr * max(params.g_enr.values()))

#  display names; anything missing falls back to the bare set key, so adding or
#  renaming a site/technology in params.py can never break the figure
NAME = {'l_Au': 'Australia', 'l_Ci': 'Chile', 'l_Ch': 'China',
        'l_Ar': 'Argentina', 'l_Fr': 'France',
        'e_US': 'USA', 'e_EU': 'EU', 'e_Ch': 'China', 'e_Ru': 'Russia',
        'r1': 'DEMO',
        't_chemEx': 'chem. exchange', 't_dispEl': 'displ./electrochem.',
        't_amalgam': 'amalgam (COLEX)'}


def _name(key):
    return NAME.get(key, key.split('_', 1)[-1])


def _num(x, dec=0):                     # 89440 -> "89 440", thesis number style
    return f"{x:,.{dec}f}".replace(",", " ")


def _ink_on(rgba):                      # label ink that stays readable on the node fill
    lum = 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]
    return INK if lum > 0.55 else 'white'


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
    return {
        'built':   {e: t for e in E for t in T if m.Y_et[e, t].value > 0.5},
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


#  Box heights are given in POINTS and converted to axes fractions per figure, so the same
#  layout holds whether the network gets a full page or one row of a small multiple.
PT = {'full':    dict(node=31, gap=9, head=14, slot=11, pad=4, reac=38),
      'compact': dict(node=22, gap=7, head=13, body=12,         reac=34)}
COL = {'full':    {'L': (0.02, 0.17), 'E': (0.40, 0.35), 'R': (0.84, 0.15)},   # (x, width)
       'compact': {'L': (0.02, 0.20), 'E': (0.40, 0.35), 'R': (0.84, 0.14)}}
BAND = (0.02, 0.88)                     # drawing band; the header line sits above it
LOCATOR = {'full': [0.825, 0.045, 0.175, 0.27], 'compact': [0.80, 0.02, 0.20, 0.36]}


def _unit(ax):                          # axes fraction per typographic point
    return 1.0 / (72.0 * ax.get_position().height * ax.figure.get_size_inches()[1])


def _layout(ax, compact):
    """Node boxes in axes coordinates. Both columns sorted by g, safest on top, so that
    'the route moves up' means 'safer' - and so panels stay comparable."""
    u, pt, col = _unit(ax), PT['compact' if compact else 'full'], COL['compact' if compact else 'full']
    h_src = pt['node'] * u
    h_pl = (pt['head'] + (pt['body'] if compact else len(params.T) * pt['slot'] + pt['pad'])) * u

    box = {}
    x, w = col['L']
    for l, y in _stack(sorted(params.L, key=lambda k: params.g_extr[k]), h_src, pt['gap'] * u).items():
        box[l] = (x, y, w, h_src)
    x, w = col['E']
    for e, y in _stack(sorted(params.E, key=lambda k: params.g_enr[k]), h_pl, pt['gap'] * u).items():
        box[e] = (x, y, w, h_pl)
    x, w = col['R']
    cy = 0.64 if compact else 0.5                                # compact: lift it clear of the inset
    box['r1'] = (x, cy - pt['reac'] * u / 2, w, pt['reac'] * u)
    return box, Normalize(*G_LIM), u, pt


def _stack(keys, h, gap):                # vertical stack, first key on top; returns bottom-y per key
    n = len(keys)
    y0 = BAND[0] + ((BAND[1] - BAND[0]) - (n * h + (n - 1) * gap)) / 2
    return {k: y0 + (n - 1 - i) * (h + gap) for i, k in enumerate(keys)}


def _source_node(ax, rect, u, g, norm, name, lines, active, unused_alpha):
    x, y, w, h = rect
    rgba = RISK_CMAP(norm(g))
    ax.add_patch(Rectangle((x, y), w, h, facecolor=rgba, edgecolor=INK if active else FAINT,
                           linewidth=1.4 if active else 0.5,
                           alpha=1.0 if active else unused_alpha, zorder=3))
    ink = _ink_on(rgba)
    ax.text(x + w / 2, y + h - 3 * u, name, ha='center', va='top', zorder=5,
            fontsize=FS['node'], color=ink, fontweight='bold' if active else 'normal')
    for i, ln in enumerate(lines):
        ax.text(x + w / 2, y + h - (13 + 9.5 * i) * u, ln, ha='center', va='top',
                fontsize=FS['num'], color=ink, zorder=5)


def _plant_card(ax, rect, u, pt, e, norm, snap, compact, unused_alpha):
    """Coloured header band carries g; the white body carries the technology slots -
    the choice sits INSIDE the site, it is not an echelon of its own."""
    x, y, w, h = rect
    built = e in snap['built']
    chosen = snap['built'].get(e)
    rgba = RISK_CMAP(norm(params.g_enr[e]))
    a = 1.0 if built else unused_alpha
    hd = pt['head'] * u
    yh = y + h - hd                                                  # header bottom edge

    ax.add_patch(Rectangle((x, y), w, h - hd, facecolor='white', edgecolor='none', alpha=a, zorder=2))
    ax.add_patch(Rectangle((x, yh), w, hd, facecolor=rgba, edgecolor='none', alpha=a, zorder=3))
    ax.add_patch(Rectangle((x, y), w, h, facecolor='none', zorder=4,
                           edgecolor=INK if built else FAINT, linewidth=1.4 if built else 0.5))
    ink = _ink_on(rgba)
    ax.text(x + 0.012, yh + hd / 2, f"{_name(e)}  ({e})", ha='left', va='center', zorder=5,
            fontsize=FS['node'], color=ink, fontweight='bold' if built else 'normal')
    ax.text(x + w - 0.012, yh + hd / 2, f"g {params.g_enr[e]:.3f}  ·  $f_e$ {params.f_e[e]:.2f}",
            ha='right', va='center', fontsize=FS['num'], color=ink, zorder=5)

    if compact:
        ax.text(x + w / 2, y + (h - hd) / 2, _name(chosen) if built else '– not built –',
                ha='center', va='center', fontsize=FS['slot'], zorder=5,
                color=INK if built else INK2, fontweight='bold' if built else 'normal')
        return

    tied = [t for t in params.T                                      # equal cost -> solver picks freely
            if chosen and t != chosen and params.EC_e[t] == params.EC_e[chosen]]
    for i, t in enumerate(params.T):
        sy = yh - (i + 1) * pt['slot'] * u                           # slot bottom
        cy = sy + pt['slot'] * u / 2
        on = (t == chosen)
        ax.add_patch(Rectangle((x + 0.012, sy + 1 * u), w - 0.024, (pt['slot'] - 2) * u, zorder=4,
                               facecolor='#fdece4' if on else 'none',
                               edgecolor=ACCENT if on else FAINT, linewidth=0.9 if on else 0.4))
        mark = '✓' if on else ('=' if t in tied else '')             # '=' : cost-tied, choice arbitrary
        ax.text(x + 0.022, cy, mark, ha='left', va='center', zorder=5,
                fontsize=FS['slot'], color=ACCENT if on else INK2, fontweight='bold')
        ax.text(x + 0.042, cy, _name(t), ha='left', va='center', zorder=5,     # no bold: keeps the
                fontsize=FS['slot'], color=INK if on else INK2,                # two columns clear
                alpha=1.0 if on else 0.7)
        ax.text(x + w - 0.018, cy, _num(params.EC_e[t]) + ' €/kg', ha='right', va='center',
                fontsize=FS['num'], color=INK if on else INK2,
                alpha=1.0 if on else 0.7, zorder=5)


def _edge(ax, p0, p1, share=None):
    """Grey hairline for an unused link, accent arrow scaled by flow for a used one."""
    if share is None:
        ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle='-', color=FAINT, linewidth=0.5,
                                     connectionstyle='arc3,rad=0.04', zorder=1))
    else:
        ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle='-|>', color=ACCENT,
                                     linewidth=0.9 + 2.4 * share, mutation_scale=9,
                                     connectionstyle='arc3,rad=0.04', shrinkA=0, shrinkB=1,
                                     zorder=6))


def _draw_network(ax, snap, compact=False, unused_alpha=1.0, split_in_header=False):
    box, norm, u, pt = _layout(ax, compact)
    ax.set_xlim(0, 1), ax.set_ylim(0, 1)
    ax.set_axis_off()
    feed_tot = sum(snap['flow_le'].values())
    sourcing = {l for l, _ in snap['flow_le']}

    # every option is drawn: the figure shows the risk landscape, not only the winner
    for l in params.L:
        lines = ([f"g {params.g_extr[l]:.3f}  ·  {params.PC_l[l]:.2f} €/kg"] if compact else
                 [f"g {params.g_extr[l]:.3f}", f"{params.PC_l[l]:.2f} €/kg"])
        _source_node(ax, box[l], u, params.g_extr[l], norm, _name(l), lines,
                     l in sourcing, unused_alpha)
    for e in params.E:
        _plant_card(ax, box[e], u, pt, e, norm, snap, compact, unused_alpha)

    rx, ry, rw, rh = box['r1']                                       # reactor carries no g -> uncoloured
    ax.add_patch(Rectangle((rx, ry), rw, rh, facecolor='white', edgecolor=INK,
                           linewidth=1.4, zorder=3))
    ax.text(rx + rw / 2, ry + rh - 4 * u, _name('r1'), ha='center', va='top', zorder=5,
            fontsize=FS['node'], color=INK, fontweight='bold')
    ax.text(rx + rw / 2, ry + rh - 15 * u,
            f"{_num(params.D_r1)} kg/yr\nenr. Li" if compact else f"{_num(params.D_r1)}\nkg enr. Li/yr",
            ha='center', va='top', fontsize=FS['num'], color=INK2, zorder=5, linespacing=1.25)

    # links L -> E : all |L|x|E| possible, the used ones scaled by flow share
    for l in params.L:
        lx, ly, lw_, lh = box[l]
        for e in params.E:
            ex, ey, ew, eh = box[e]
            p0, p1 = (lx + lw_, ly + lh / 2), (ex, ey + eh / 2)
            q = snap['flow_le'].get((l, e))
            _edge(ax, p0, p1, None if q is None else q / feed_tot)
            if q:
                mx, my = p0[0] + 0.58 * (p1[0] - p0[0]), p0[1] + 0.58 * (p1[1] - p0[1])
                ax.text(mx, my, f"{q / feed_tot:.0%}\n{_num(q)} kg/yr", ha='center', va='center',
                        fontsize=FS['num'], color=INK, linespacing=1.25, zorder=7,
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none'))

    # links E -> R : leave from the chosen technology slot, so the route stays traceable
    for e in params.E:
        ex, ey, ew, eh = box[e]
        q = snap['flow_er'].get(e)
        y_out = ey + eh / 2
        if q and not compact:
            i = list(params.T).index(snap['built'][e])
            y_out = ey + eh - pt['head'] * u - (i + 0.5) * pt['slot'] * u
        _edge(ax, (ex + ew, y_out), (rx, ry + rh / 2), None if q is None else 1.0)

    # header - what trade-off point this is
    eps = snap.get('eps')
    head = (f"$\\varepsilon$ = {eps:.4f}      " if eps is not None else "")
    head += f"cost = {snap['cost']/1e6:.2f} M€/yr      SR$_{{norm}}$ = {snap['sr']:.4f}"
    head += (f" = {snap['sr_extr']:.3f} extr. + {snap['sr_enr']:.3f} enr."
             if split_in_header else "      $w_L = w_{ET}$ = 1")
    ax.text(0.0, 1.0, head, ha='left', va='top', fontsize=FS['box'], color=INK, zorder=8)
    return norm


def _draw_sr_bar(ax, snap):
    """Where the risk sits: the two echelons stacked against what they could attain."""
    ax.set_xlim(0, SR_CEIL * 1.02), ax.set_ylim(0, 1)
    ax.add_patch(Rectangle((0, 0.25), SR_CEIL, 0.5, facecolor='#f2f1ee', edgecolor='none', zorder=1))
    gap = SR_CEIL * 0.004                                            # 2px surface gap, no borders
    for x0, wd, col, lab in [(0, snap['sr_extr'], '#5598e7', 'extraction'),
                             (snap['sr_extr'] + gap, snap['sr_enr'] - gap, '#104281', 'enrichment')]:
        ax.add_patch(Rectangle((x0, 0.25), wd, 0.5, facecolor=col, edgecolor='none', zorder=2))
        ax.text(x0 + wd / 2, 0.5, f"{lab} {wd + (gap if x0 else 0):.3f}", ha='center', va='center',
                fontsize=FS['tick'], color='white', zorder=3)
    if snap.get('eps') is not None:                                  # SR lands below eps: the slack
        ax.plot([snap['eps']] * 2, [0.12, 0.88], color=INK, lw=0.9, zorder=4)
        ax.text(snap['eps'], 0.95, '$\\varepsilon$', ha='center', va='bottom',
                fontsize=FS['tick'], color=INK)
    ax.set_yticks([])
    ax.set_xticks([0, SR_FLOOR, snap['sr'], SR_CEIL])
    ax.set_xticklabels(['0', f"floor\n{SR_FLOOR:.3f}", f"SR\n{snap['sr']:.3f}",
                        f"ceiling\n{SR_CEIL:.3f}"], fontsize=FS['tick'], color=INK2)
    ax.tick_params(length=2, pad=1.5, colors=INK2)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_linewidth(0.5), ax.spines['bottom'].set_color(FAINT)


def _draw_locator(ax, front, snap, bare=False):
    """Mini front in the corner: which trade-off point is on display."""
    pts = sorted(set(front))
    ax.set_facecolor('white'), ax.set_zorder(9), ax.patch.set_alpha(1.0)  # sits above the grey links
    ax.scatter([s for _, s in pts], [c / 1e6 for c, _ in pts], s=9, facecolor='none',
               edgecolor=INK2, linewidth=0.6, zorder=2)
    ax.scatter([snap['sr']], [snap['cost'] / 1e6], s=22, color=ACCENT, zorder=3)
    ax.margins(0.12)                                                 # keep corner points off the spines
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('bottom', 'left'):
        ax.spines[s].set_linewidth(0.5), ax.spines[s].set_color(FAINT)
    if bare:                                                         # too small for numbers
        ax.set_xticks([]), ax.set_yticks([])
        ax.set_xlabel('SR$_{norm}$ →', fontsize=FS['tick'], color=INK2, labelpad=1)
        ax.set_ylabel('cost →', fontsize=FS['tick'], color=INK2, labelpad=1)
        return
    ax.set_xlabel('SR$_{norm}$ [–]', fontsize=FS['tick'], labelpad=1)
    ax.set_ylabel('cost [M€/yr]', fontsize=FS['tick'], labelpad=1)
    ax.tick_params(labelsize=FS['tick'], length=2, pad=1, colors=INK2)
    ax.locator_params(nbins=3)                                       # a locator, not a readable chart


def _risk_colourbar(fig, cax, norm):
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=RISK_CMAP), cax=cax,
                      orientation='horizontal')
    cb.set_label('political instability  g = (2.5 − WGI-PV)/5   [–]      safe → risky',
                 fontsize=FS['tick'], color=INK2, labelpad=2)
    cb.ax.tick_params(labelsize=FS['tick'], length=2, pad=1.5, colors=INK2)
    cb.outline.set_visible(False)


#  figure assembly - rows are placed in inches, top down, so nothing depends on gridspec guessing
H = {'bar': 0.40, 'cb': 0.22, 'gap': 0.20, 'labels': 0.42, 'top': 0.12}


def _net_height(compact):
    """Network height [in] that makes the tallest column fit the band exactly - so adding a
    country, a site or a technology in params.py resizes the figure instead of overflowing it."""
    pt = PT['compact' if compact else 'full']
    card = pt['head'] + (pt['body'] if compact else len(params.T) * pt['slot'] + pt['pad'])
    tallest = max(len(params.L) * pt['node'] + (len(params.L) - 1) * pt['gap'],
                  len(params.E) * card + (len(params.E) - 1) * pt['gap'], pt['reac'])
    return tallest / (BAND[1] - BAND[0]) / 72
X0, XW = 0.02, 0.96


def _row(fig, y_top_in, h_in):           # inches from the top -> axes rectangle
    fig_h = fig.get_size_inches()[1]
    return fig.add_axes([X0, 1 - (y_top_in + h_in) / fig_h, XW, h_in / fig_h])


def supply_chain_network(snap, front=None, show_split=True, compact=False,
                         unused_alpha=1.0, figsize=None):
    """Chosen route through the full option network for ONE Pareto point.
    front: the whole front -> adds the locator inset. unused_alpha < 1 dims unchosen nodes."""
    net = _net_height(compact)
    total = H['top'] + net + (H['gap'] + H['bar'] + H['labels'] if show_split else 0) \
        + H['gap'] + H['cb'] + H['labels']
    fig = plt.figure(figsize=figsize or (W_TEXT, total))
    y = H['top']
    ax = _row(fig, y, net)
    norm = _draw_network(ax, snap, compact, unused_alpha)
    if front:
        _draw_locator(ax.inset_axes(LOCATOR['compact' if compact else 'full']), front, snap, compact)
    y += net
    if show_split:
        _draw_sr_bar(_row(fig, y + H['gap'], H['bar']), snap)
        y += H['gap'] + H['bar'] + H['labels']
    _risk_colourbar(fig, _row(fig, y + H['gap'], H['cb']), norm)
    return fig, fig.axes


def supply_chain_panels(snaps, front=None, figsize=None):
    """Same layout, several ε in one figure - the structural shifts along the front.
    snaps: list of snapshot dicts, cheapest first (or whatever order tells the story).
    The SR split moves into each header; a bar per panel would not fit on one page."""
    n = len(snaps)
    block = _net_height(True) + H['gap']
    total = H['top'] + n * block + H['gap'] + H['cb'] + H['labels']
    fig = plt.figure(figsize=figsize or (W_TEXT, total))
    for k, snap in enumerate(snaps):
        ax = _row(fig, H['top'] + k * block, block - H['gap'])
        norm = _draw_network(ax, snap, compact=True, split_in_header=True)
        if front:
            _draw_locator(ax.inset_axes(LOCATOR['compact']), front, snap, bare=True)
    _risk_colourbar(fig, _row(fig, H['top'] + n * block + H['gap'], H['cb']), norm)
    return fig, fig.axes
