# All model parameters, bounds, and configuration constants (costs, emission factors, capacities, solver settings).

# Flow unit/ commodity: kg - either natural or enriched

# INDEX-SETS
E = ['e1','e2']                         # [Location] Enrichment site 
T = ['t1','t2']                         # [Technology] Enrichment site
L = ['l1','l2']                         # [Location] Extraction & Processing site 
R = ['r1']                              # [Location] Rector

# PARAMETERS

# Costs
FC_et = {('e1','t1'):500,               #[€] FixedCost (Building): enrichment site e with technology t 
         ('e1','t2'):700,
         ('e2','t1'):800,
         ('e2','t2'):1000}

TC_let = {('l1','e1','t1'):5,           #[€/kg nat. Li] TransportCost (Flow): from extraxtion&processing site l to enrichment site e with technology t 
          ('l1','e1','t2'):7,
          ('l1','e2','t1'):15,
          ('l1','e2','t2'):17,
          ('l2','e1','t1'):40,
          ('l2','e1','t2'):14,
          ('l2','e2','t1'):5,
          ('l2','e2','t2'):34}                             

TC_etr = {('e1','t1','r1'):50,          #[€/kg enr. Li] TransportCost (Flow): from enrichment site e with technology t to reactor r
          ('e1','t2','r1'):70,
          ('e2','t1','r1'):60,
          ('e2','t2','r1'):170}     

PC_l  = {('l1'):5,                    #[€/kg nat. Li] Production costs : from extraxtion&processing site l 
         ('l2'):10}                       

EC_et = {('e1','t1'):25,                #[€/kg nat. Li] Enrichment costs: enrichment site e with technology t 
         ('e1','t2'):35,
         ('e2','t1'):27,
         ('e2','t2'):35}

# Capacities
Cap_l = {'l1':20,                       #[kg nat. Li] extraction&processing capacity ceiling (max. amount handable)
         'l2':20}
                           

Cap_et = {('e1','t1'):20,               #[kg nat. Li] enrichment capacity ceiling (max. amount handable by one site)              
          ('e1','t2'):20,
          ('e2','t1'):20,
          ('e2','t2'):20}
                            

Cap_et_min = {('e1','t1'):1,            #[kg nat. Li] enrichment bottom ceiling (min. amount handable by one site)               
              ('e1','t2'):1,
              ('e2','t1'):1,
              ('e2','t2'):1}

# Missc.
D_r1 = 10                               #[kg enr. Li] Demand of reactor 1

f_ne = 2                                #[kg nat. Li/ kg enriched Li] 50% enrichment 


#f_ne_t = {'t1':2.2,                     #[kg nat. Li/ kg enriched Li] 50% enrichment TODO: make conversion rate t-depndant
#          't2':2.5}

Q_max_enr = 10                          #[kg enr. Li] upper flow bound
Q_max_nat = f_ne * D_r1                 #[kg nat. Li] upper flow bound

# Supply risk
s_k = {("k1"): 0.25,                      #[-] supply share of country k in global production of commodity 
       ("k2"): 0.25,                      # Australia, China; Chile, Argentinia ...
       ("k3"): 0.25,                      # 
       ("k4"): 0.25}

g = {("l1"): 0.8,                           # political instability indicater (derived from WGI)
     ("l2"): 0.2}                           # for each l country my model may get natural Li from
                                          # TODO rescale!!!
                                          # high = risky