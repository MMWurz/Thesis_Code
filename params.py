from conversions import compound_to_Li_price, w_Li_LIOH_H2O
# All model parameters, bounds, and configuration constants (costs, emission factors, capacities, solver settings).

# Flow unit/ commodity: kg - either natural or enriched

# INDEX-SETS
L = ['l_A',          'l_Ci',       'l_Ch']       # [Location] Extraction & Processing site 
#    Australia,      Chile,        China

E = ['e1','e2']                         # [Location] Enrichment site 
T = ['t1','t2']                         # [Technology] Enrichment site
R = ['r1']                              # [Location] Rector

# PARAMETERS

# Costs
FC_et = {('e1','t1'):500,               #[€] FixedCost (Building): enrichment site e with technology t 
         ('e1','t2'):700,
         ('e2','t1'):800,
         ('e2','t2'):1000}

TC_let = {('l_A','e1','t1'):5,           #[€/kg nat. Li] TransportCost (Flow): from extraxtion&processing site l to enrichment site e with technology t 
          ('l_A','e1','t2'):7,
          ('l_A','e2','t1'):15,
          ('l_A','e2','t2'):17,
          ('l_Ci','e1','t1'):40,
          ('l_Ci','e1','t2'):14,
          ('l_Ci','e2','t1'):5,
          ('l_Ci','e2','t2'):34,  
          ('l_Ch','e1','t1'):50,
          ('l_Ch','e1','t2'):15,
          ('l_Ch','e2','t1'):8,
          ('l_Ch','e2','t2'):38}                            

TC_etr = {('e1','t1','r1'):50,          #[€/kg enr. Li] TransportCost (Flow): from enrichment site e with technology t to reactor r
          ('e1','t2','r1'):70,
          ('e2','t1','r1'):60,
          ('e2','t2','r1'):170}     

PC_l  = {('l_A'):compound_to_Li_price(9900, w_Li_LIOH_H2O),      #[€/kg nat. Li] Production costs : from extraxtion&processing site l 
         ('l_Ci'):compound_to_Li_price(9900, w_Li_LIOH_H2O),
         ('l_Ch'):compound_to_Li_price(9900, w_Li_LIOH_H2O)}     # [€/kg nat. Li]; ca. 55.4 €/kg; USGS MCS 2025 p.110: LiOH·H2O spot, China, Nov 2024
           

EC_et = {('e1','t1'):25,                #[€/kg nat. Li] Enrichment costs: enrichment site e with technology t 
         ('e1','t2'):35,
         ('e2','t1'):27,
         ('e2','t2'):35}

# Capacities
#[kg nat. Li] extraction&processing capacity ceiling (max. amount handable)
# Per-country extraction/processing capacity ceiling (upper bound on total outflow from l).
# Proxy: 2024 mine production, lithium content. USGS MCS 2025 p.111.
Cap_l = {'l_A':  88_000_000,   # Australia
         'l_Ci': 49_000_000,   # Chile
         'l_Ch': 41_000_000}   # China
                           

Cap_et = {('e1','t1'):20,               #[kg nat. Li] enrichment capacity ceiling (max. amount handable by one site)              
          ('e1','t2'):20,
          ('e2','t1'):20,
          ('e2','t2'):20}
                            

Cap_et_min = {('e1','t1'):1,            #[kg nat. Li] enrichment bottom ceiling (min. amount handable by one site)               
              ('e1','t2'):1,
              ('e2','t1'):1,
              ('e2','t2'):1}

# Missc.
D_r1 = 10                               #[kg enr. Li] Demand of reactor for enriched Li

f_ne = 2                                #[kg nat. Li/ kg enr. Li] 50% enrichment 


#f_ne_t = {'t1':2.2,                     #[kg nat. Li/ kg enriched Li] 50% enrichment TODO: make conversion rate t-depndant
#          't2':2.5}

Q_max_enr = 10                          #[kg enr. Li] upper flow bound
Q_max_nat = f_ne * D_r1                 #[kg nat. Li] upper flow bound

# Supply risk
s_extr_k = {("k1"): 0.25,                      #[-] supply share of all countries k in global production of commodity 
       ("k2"): 0.25,                      # Australia, China; Chile, Argentinia ...
       ("k3"): 0.25,                      # 
       ("k4"): 0.25}

s_enr_k = {("enr_k1"): 0.25,              #[-] supply share of all countries in enrichment
           ("enr_k2"): 0.25,              # as above
           ("enr_k3"): 0.25,
           ("enr_k4"): 0.25}

g_extr =  {("l_A"): 0.7,                  #[-] political instability indicater (derived from WGI)
          ("l_Ci"): 0.2,                  # for each l country my model may get natural Li from
          ("l_Ch"): 0.1}                  # TODO rescale!!!
                                          # high = risky

g_enr = {("e1"): 0.8,                     # [-]
         ("e2"): 0.2}                     # as above 
                                          # TODO rescale!!!
                                            