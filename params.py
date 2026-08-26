from conversions import compound_to_Li_price, w_Li_LIOH_H2O
# All model parameters, bounds, and configuration constants (costs, emission factors, capacities, solver settings).

# Flow unit/ commodity: kg - either natural or enriched

# INDEX-SETS
L = ['l_A',          'l_Ci',       'l_Ch']       # [Location] Extraction & Processing site 
#    Australia,      Chile,        China

E = ['e_US',      'e_EU',      'e_CN',      'e_RU']      # [Location] Enrichment site
#    USA,         EU,          China,       Russia
T = ['t1','t2']                         # [Technology] Enrichment site
R = ['r1']                              # [Location] Rector

# PARAMETERS

# Costs
FC_et = {('e_US','t1'):500,             #[€] FixedCost (Building): enrichment site e with technology t
         ('e_US','t2'):700,
         ('e_EU','t1'):800,
         ('e_EU','t2'):1000,
         ('e_CN','t1'):400,
         ('e_CN','t2'):600,
         ('e_RU','t1'):450,
         ('e_RU','t2'):650}

TC_let = {('l_A','e_US','t1'):15,        #[€/kg nat. Li] TransportCost (Flow): from extraxtion&processing site l to enrichment site e with technology t
          ('l_A','e_US','t2'):17,
          ('l_A','e_EU','t1'):20,
          ('l_A','e_EU','t2'):22,
          ('l_A','e_CN','t1'):8,
          ('l_A','e_CN','t2'):10,
          ('l_A','e_RU','t1'):18,
          ('l_A','e_RU','t2'):20,
          ('l_Ci','e_US','t1'):10,
          ('l_Ci','e_US','t2'):12,
          ('l_Ci','e_EU','t1'):18,
          ('l_Ci','e_EU','t2'):20,
          ('l_Ci','e_CN','t1'):22,
          ('l_Ci','e_CN','t2'):24,
          ('l_Ci','e_RU','t1'):25,
          ('l_Ci','e_RU','t2'):27,
          ('l_Ch','e_US','t1'):30,
          ('l_Ch','e_US','t2'):32,
          ('l_Ch','e_EU','t1'):28,
          ('l_Ch','e_EU','t2'):30,
          ('l_Ch','e_CN','t1'):5,
          ('l_Ch','e_CN','t2'):7,
          ('l_Ch','e_RU','t1'):12,
          ('l_Ch','e_RU','t2'):14}

TC_etr = {('e_US','t1','r1'):60,        #[€/kg enr. Li] TransportCost (Flow): from enrichment site e with technology t to reactor r
          ('e_US','t2','r1'):80,
          ('e_EU','t1','r1'):30,
          ('e_EU','t2','r1'):45,
          ('e_CN','t1','r1'):90,
          ('e_CN','t2','r1'):110,
          ('e_RU','t1','r1'):85,
          ('e_RU','t2','r1'):100}

PC_l  = {('l_A'):compound_to_Li_price(9900, w_Li_LIOH_H2O),      #[€/kg nat. Li] Production costs : from extraxtion&processing site l 
         ('l_Ci'):compound_to_Li_price(9900, w_Li_LIOH_H2O),
         ('l_Ch'):compound_to_Li_price(9900, w_Li_LIOH_H2O)}     # [€/kg nat. Li]; ca. 55.4 €/kg; USGS MCS 2025 p.110: LiOH·H2O spot, China, Nov 2024
           

EC_et = {('e_US','t1'):30,              #[€/kg nat. Li] Enrichment costs: enrichment site e with technology t
         ('e_US','t2'):35,
         ('e_EU','t1'):32,
         ('e_EU','t2'):38,
         ('e_CN','t1'):25,
         ('e_CN','t2'):28,
         ('e_RU','t1'):27,
         ('e_RU','t2'):30}

# Capacities
#[kg nat. Li] extraction&processing capacity ceiling (max. amount handable)
# Per-country extraction/processing capacity ceiling (upper bound on total outflow from l).
# Proxy: 2024 mine production, lithium content. USGS MCS 2025 p.111.
Cap_l = {'l_A':  88000000,   #[kg nat. Li] Australia
         'l_Ci': 49000000,   #[kg nat. Li] Chile
         'l_Ch': 41000000}   #[kg nat. Li] China
                           

Cap_et = {('e_US','t1'):200000,        #[kg nat. Li] enrichment capacity ceiling (max. amount handable by one site)
          ('e_US','t2'):200000,        # TODO Day 9: replace smoke-run placeholder (>f_ne*D_r1=115_556) with cascade-economics value
          ('e_EU','t1'):200000,
          ('e_EU','t2'):200000,
          ('e_CN','t1'):200000,
          ('e_CN','t2'):200000,
          ('e_RU','t1'):200000,
          ('e_RU','t2'):200000}
                            

Cap_et_min = {('e_US','t1'):1,          #[kg nat. Li] enrichment bottom ceiling (min. amount handable by one site)
              ('e_US','t2'):1,
              ('e_EU','t1'):1,
              ('e_EU','t2'):1,
              ('e_CN','t1'):1,
              ('e_CN','t2'):1,
              ('e_RU','t1'):1,
              ('e_RU','t2'):1}

# Missc.
D_r1 = 52000                              #[kg enr. Li] Demand of reactor for enriched Li
                                          #   = 52 t of 90%-enriched lithium (WCLL breeder inventory, 2 GWfus DEMO), Giegerich 2019.
                                          #   NO /alpha: Giegerich's "52 t pure 6Li" == his "26 t/GWfus 90%-enriched Li" == the enriched PRODUCT, not the bare isotope (~47 t 6Li).

f_ne = 2                                #[kg nat. Li/ kg enr. Li] 50% enrichment


#f_ne_t = {'t1':2.2,                     #[kg nat. Li/ kg enriched Li] 50% enrichment TODO: make conversion rate t-depndant
#          't2':2.5}

Q_max_enr = D_r1                        #[kg enr. Li] upper flow bound (one link must carry full demand)
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

g_enr = {("e_US"): 0.3,                   # [-] political instability indicator (placeholder)
         ("e_EU"): 0.15,                  # for each enrichment country e
         ("e_CN"): 0.6,                   # high = risky
         ("e_RU"): 0.8}                   # TODO rescale!!!
                                            