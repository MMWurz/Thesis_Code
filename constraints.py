# Supply chain constraints: capacity limits, flow balance, demand satisfaction, and material-specific feasibility conditions.
import params

# LOGICAL - con 
def one_tech_per_site(m,e):                             # only max. 1 technology t per site e 
    return sum(m.Y_et[e,t] for t in m.T) <= 1

# FLOW - con (Eq. 6)
def flow_active_rule_1(m,l,e,t):                        # only flow between l and et if et is built
    return m.Q_let[l,e,t] <= params.Q_max_nat * m.Y_et[e,t]
     
def flow_activation_rule_2(m,e,t,r):                    # only flow between et and r if et is built
    return m.Q_etr[e,t,r] <= params.Q_max_enr * m.Y_et[e,t]
    
# DEMAND - con (Eq. 14)
def demand_satisfaction(m,r):                           # the demand of the reactor r1 must be met
    return params.D_r1 <= sum(m.Q_etr[e,t,r] for e in m.E for t in m.T)
    
# MATERIAL-BALANCE - con (Eq. 12 & 13)
def material_balance(m,e,t):                            # all that flows into et must flow out of et
    return (sum(m.Q_let[l,e,t] for l in m.L) 
            == params.f_ne * sum(m.Q_etr[e,t,r] for r in m.R))

# PRODUCTION RATE - con (Eq. 15)
def extraction_ceiling(m,l):                         
    return sum(m.Q_let[l,e,t] for e in m.E for t in m.T) <= params.Cap_l[l] 

def enrichment_ceiling(m,e,t):                          # Y_et = the plant of flexible size, N_e = further full-size plants
    return sum(m.Q_let[l,e,t] for l in m.L) <= params.Cap_et[e,t] * (m.Y_et[e,t] + m.N[e])

def enrichment_bottom(m,e,t):
    return sum(m.Q_let[l,e,t] for l in m.L) >= params.Cap_et_min[e,t] * m.Y_et[e,t]

# FC 
def one_segment_if_built(m, e):                     # exactly one segment iff a plant is built
    return sum(m.z[e,j] for j in m.J) == sum(m.Y_et[e,t] for t in m.T)

def segment_width(m, e, j):                         # increment cannot exceed its segment
    return m.q[e,j] <= params.seg_width[j-1] * m.z[e,j]

# SEVERAL PLANTS PER SITE: one plant of flexible size (z, q) + N_e further plants of the largest size Qbar[-1].
# With N_e = 0 the two capacity rules below are one equality again: build exactly the capacity you use.
def full_plants_if_built(m, e):                     # full-size plants only at a built site
    return m.N[e] <= params.N_max * sum(m.Y_et[e,t] for t in m.T)

def flex_plant_within_throughput(m, e):             # the flexible plant is never bigger than the output of its site
    return (sum(params.Qbar[j-1]*m.z[e,j] + m.q[e,j] for j in m.J)
            <= sum(m.Q_etr[e,t,r] for t in m.T for r in m.R))

def capacity_covers_throughput(m, e):               # all plants of the site together cover its output
    return (sum(params.Qbar[j-1]*m.z[e,j] + m.q[e,j] for j in m.J) + params.Qbar[-1]*m.N[e]
            >= sum(m.Q_etr[e,t,r] for t in m.T for r in m.R))

def capital_cost(m, e):                             # PWL evaluation of CC(Q) + N_e plants at the last support point
    return m.CC[e] == (sum(params.CCbar[j-1]*m.z[e,j] + params.seg_slope[j-1]*m.q[e,j] for j in m.J)
                       + params.CCbar[-1]*m.N[e])


### NOTES ###

## syntax explenation:
# constraint is a function/ rule

# Indices are in SIGNATUR (m, Index1, Index2)
# = Indices der Regel
# Pyomo makes loop out of this and runs it for every index-combination
# = pro Index eine Ungleichung                                                      -> loop ganze Ungl
# = darüber wird ganze Ungl gelaufen

# Indices in SUM (m.A_bc[bc] for b in m.B) 
# = summiert über diesen Index innerhalb der Ungleichung auf                        -> loop innerhalb Ungl
# for ... in ... über diese Indizes wird summiert (was kein for hat bleibt fix)