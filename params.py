# All model parameters, bounds, and configuration constants (costs, emission factors, capacities, solver settings).

# Flow unit: 1 unit i = 1 kg of Li6

# Index-sets
E = ['e1','e2']                         # [Location] Enrichment site 
T = ['t1','t2']                         # [Technology] Enrichment site
L = ['l1','l2']                         # [Location] Extraction & Processing site 
R = ['r1']                              # [Location] Rector

# Parameters
FC_et = {('e1','t1'):500,               #[€] FixedCost (Building): enrichment site e with technology t 
         ('e1','t2'):700,
         ('e2','t1'):1500,
         ('e2','t2'):1700,}

TC_let = {('l1','e1','t1'):5,           #[€] TransportCost (Flow): from extraxtion&processing site l to enrichment site e with technology t 
          ('l1','e1','t2'):7,
          ('l1','e2','t1'):15,
          ('l1','e2','t2'):17,
          ('l2','e1','t1'):10,
          ('l2','e1','t2'):14,
          ('l2','e2','t1'):30,
          ('l2','e2','t2'):34}                             

TC_etr = {('e1','t1','r1'):50,          #[€] TransportCost (Flow): from enrichment site e with technology t to reactor r
          ('e1','t2','r1'):70,
          ('e2','t1','r1'):150,
          ('e2','t2','r1'):170,}                            

D_r1 = 10                               #[Stk. i] Demand of reactor 1

Q_max = 10                              #[Stk. i] upper flow bound

#TODO make cap like costs site and tec specific
Cap_l = 10                              # [Stk. i] extraction&processing capacity ceiling (max. amount handable)
Cap_et = 10                             # [Stk. i] enrichment capacity ceiling (max. amount handable by one site)
Cap_et_min = 1                          # [Stk. i] enrichment bottom ceiling (min. amount handable by one site)