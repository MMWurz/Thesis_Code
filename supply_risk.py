import params

# FLOW L --> E

# CENTRAL EQUATION Function
def hhi(shares):                                            # first bracket: Σ s_k²
    return sum(s**2 for s in shares.values())               # .values ???

def import_risk(g, f):                                      # second bracket: Σ g_k · f_{i,k}
    return sum(g[k] * f[k] for k in f)                      # f: dict supplier -> import share for one importer

def geopolrisk(shares, g, f):                               # full Eq. (1): SR_{c,i}
    return hhi(shares) * import_risk(g, f)

# FIXED OBJECTIVE SCALARS
HHI_extr = hhi(params.s_extr_k)                                         # 0.25, fix (globale Produktion)
D_nat = params.f_ne * params.D_r1                                       # 20 kg, Demand an nat. Li (fester Nenner)

HHI_enr = hhi(params.s_enr_k)
D_enr = params.D_r1

# IMPORT SHARE Function
# "for enrichment site e, what fraction of its lithium comes from each source l?"
def import_share_L(m, e):                                           # import share f_{e,·} for one enrichment site e
    total = sum(m.Q_let[l,e,t].value for l in m.L for t in m.T)     # all nat. Lithium flowing into e
    if total == 0:                                                  # if nothing flows to e
        return {l: 0.0 for l in m.L}
    return {l: sum(m.Q_let[l,e,t].value for t in m.T) / total for l in m.L} # share of flow from l to total e

def import_share_ET(m,r):
    total = sum(m.Q_etr[e,t,r].value for e in m.E for t in m.T) 
    if total == 0:
        return {e: 0.0 for e in m.E}
    return {e: sum(m.Q_etr[e,t,r].value for t in m.T) / total for e in m.E}

# VALIDATION Function                           # not needed for model to run                                                 
def calculate_SR_L(m):                          # SR_{Li,e} for each enrichment site
    SR_L = {}
    for e in m.E:
        f_e = import_share_L(m, e)
        SR_L[e] = geopolrisk(params.s_extr_k, params.g_extr, f_e)
    return SR_L

def calculate_SR_ET(m):                        # SR_{Li,e} for each enrichment site
    SR_ET = {}
    for r in m.R:
        f_r = import_share_ET(m, r)
        SR_ET[r] = geopolrisk(params.s_enr_k, params.g_enr, f_r)
    return SR_ET



