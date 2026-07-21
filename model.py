# Dual-objective optimization model: defines decision variables, objective functions (cost & supply risk), and solver setup.

# I write in python -> pyomo (translates into math) -> solver
import params
import constraints  
import supply_risk

from pyomo.environ import (ConcreteModel, Set, Var, Param, Constraint, Binary, NonNegativeReals, Objective, minimize)
    # model container	m = ConcreteModel()
    # index collections	m.E, m.T, m.L, m.R

# Functions
def cost_rule(m):
    return (sum(params.FC_et[e,t] * m.Y_et[e,t] for e in m.E for t in m.T) +                    # fix building C
           sum(params.TC_let[l,e,t] * m.Q_let[l,e,t] for l in m.L for e in m.E for t in m.T) +  # fix transport C
           sum(params.TC_etr[e,t,r] * m.Q_etr[e,t,r] for e in m.E for t in m.T for r in m.R )+  # fix transport C
           sum(params.PC_l[l] * m.Q_let[l,e,t] for l in m.L for e in m.E for t in m.T)+         # fix enrichment&processing C
           sum(params.EC_et[e,t] * m.Q_let[l,e,t] for l in m.L for e in m.E for t in m.T))      # fix enrichment C TODO: this needs to be sophisticated f_ne driven/output driven etc..

def supply_risk_rule(m):
    return (supply_risk.HHI / supply_risk.D_nat *
        sum(params.g[l] * m.Q_let[l,e,t] for l in m.L for e in m.E for t in m.T))    

def build_model(p, delta=1e-3, r_SR=1.0):                   # build_model = function name (input of function = params)           
        # Safety-Catches
    if r_SR == 0:
        raise ValueError(
            "r_SR = 0: cost and supply risk do not conflict "
            "(SR_max == SR_min) — no trade-off exists, AUGMECON is not applicable."
        )

    m = ConcreteModel()                                     # m = empty box to be filled
        # Parameter
    m.L = Set(initialize=p.L)
    m.E = Set(initialize=p.E)
    m.T = Set(initialize=p.T)
    m.R = Set(initialize=p.R) 
        # Binary Var
    m.Y_et = Var(m.E, m.T, domain=Binary)                   # build or not build            # 9x
        # Conti Var 
    m.Q_let = Var(m.L,m.E,m.T, domain=NonNegativeReals)     # [kg nat. Li] transport flow    l > et
    m.Q_etr = Var(m.E,m.T,m.R, domain=NonNegativeReals)     # [kg enr. Li] transport flow    et > r
        # obj. Fkt
    m.obj_cost = Objective(rule=cost_rule, sense=minimize)
    m.obj_SR   = Objective(rule=supply_risk_rule, sense=minimize)
    m.obj_SR.deactivate()                                    # standard: costs active
        # Constraints
    m.c_techsite    = Constraint(m.E,               rule=constraints.one_tech_per_site)
    m.c_flow1       = Constraint(m.L, m.E, m.T,     rule=constraints.flow_active_rule_1)
    m.c_flow2       = Constraint(m.E, m.T, m.R,     rule=constraints.flow_activation_rule_2)
    m.c_demand      = Constraint(m.R,               rule=constraints.demand_satisfaction)
    m.c_balance     = Constraint(m.E, m.T,          rule=constraints.material_balance)
    m.c_ex_ceiling  = Constraint(m.L,               rule=constraints.extraction_ceiling)
    m.c_en_ceiling  = Constraint(m.E, m.T,          rule=constraints.enrichment_ceiling)
    m.c_en_bottom   = Constraint(m.E, m.T,          rule=constraints.enrichment_bottom)
        # AUGMECON (SR -> con)
    m.eps           = Param(initialize=0.0, mutable=True)
    m.s             = Var(within=NonNegativeReals)                      # [] slack-variable
    m.c_eps          = Constraint(expr = supply_risk_rule(m) + m.s == m.eps)
    m.c_eps.deactivate()
    m.obj_augmecon  = Objective(expr = cost_rule(m) - delta*(m.s/r_SR), sense=minimize)
    m.obj_augmecon.deactivate()
    return m 





### NOTES ####
# Parameter vs. Variable
# a parameter is something you tell the model; a variable is something the model tells you