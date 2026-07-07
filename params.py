# All model parameters, bounds, and configuration constants (costs, emission factors, capacities, solver settings).

# Flow unit: kg - either natural or enriched

# INDEX-SETS
E = ['e1','e2']                         # [Location] Enrichment site 
T = ['t1','t2']                         # [Technology] Enrichment site
L = ['l1','l2']                         # [Location] Extraction & Processing site 
R = ['r1']                              # [Location] Rector

# PARAMETERS

# Costs
FC_et = {('e1','t1'):500,               #[€] FixedCost (Building): enrichment site e with technology t 
         ('e1','t2'):700,
         ('e2','t1'):1500,
         ('e2','t2'):1700,}

TC_let = {('l1','e1','t1'):5,           #[€/kg nat. Li] TransportCost (Flow): from extraxtion&processing site l to enrichment site e with technology t 
          ('l1','e1','t2'):7,
          ('l1','e2','t1'):15,
          ('l1','e2','t2'):17,
          ('l2','e1','t1'):10,
          ('l2','e1','t2'):14,
          ('l2','e2','t1'):30,
          ('l2','e2','t2'):34}                             

TC_etr = {('e1','t1','r1'):50,          #[€/kg enr. Li] TransportCost (Flow): from enrichment site e with technology t to reactor r
          ('e1','t2','r1'):70,
          ('e2','t1','r1'):150,
          ('e2','t2','r1'):170,}                            

# Capacities
Cap_l = {'l1':10,                       #[kg nat. Li] extraction&processing capacity ceiling (max. amount handable)
         'l2':10}
                           

Cap_et = {('e1','t1'):10,               #[kg nat. Li] enrichment capacity ceiling (max. amount handable by one site)              
          ('e1','t2'):10,
          ('e2','t1'):10,
          ('e2','t2'):10,}
                            

Cap_et_min = {('e1','t1'):1,            #[kg nat. Li] enrichment bottom ceiling (min. amount handable by one site)               
              ('e1','t2'):1,
              ('e2','t1'):1,
              ('e2','t2'):1,}

# Missc.
D_r1 = 10                               #[kg enr. Li] Demand of reactor 1

Q_max_enr = 10                          #[kg enr. Li] upper flow bound
Q_max_nat = 10                          #[kg nat. Li] upper flow bound

f = 2                                   #[kg nat. Li/ kg enriched Li] 50% enrichment 

# Supply risk
g_c = {'l1':1,                                 # [] Generic governance indicator of country c
       'l2':2}

S_c = {'l1':1,                                 # [] market share of country c
       'l2':2}