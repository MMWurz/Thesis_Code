import conversions
# All model parameters, bounds, and configuration constants (costs, emission factors, capacities, solver settings).

# Flow unit/ commodity: kg - either natural or enriched

# INDEX-SETS
L = ['l_Au',          'l_Ci',       'l_Ch']       # [Location] Extraction & Processing site 
#    Australia,      Chile,        China

E = ['e_US',      'e_EU',      'e_Ch',      'e_Ru']      # [Location] Enrichment site
#    USA,           EU,          China,       Russia
T = ['t1','t2']                         # [Technology] Enrichment site
R = ['r1']                              # [Location] Rector

# PARAMETERS

# Costs
FC_et = {('e_US','t1'):500,             #[€] FixedCost (Building): enrichment site e with technology t
         ('e_US','t2'):700,
         ('e_EU','t1'):800,
         ('e_EU','t2'):1000,
         ('e_Ch','t1'):400,
         ('e_Ch','t2'):600,
         ('e_Ru','t1'):450,
         ('e_Ru','t2'):650}

TC_let = {('l_Au','e_US','t1'):15,        #[€/kg nat. Li] TransportCost (Flow): from extraxtion&processing site l to enrichment site e with technology t
          ('l_Au','e_US','t2'):17,
          ('l_Au','e_EU','t1'):20,
          ('l_Au','e_EU','t2'):22,
          ('l_Au','e_Ch','t1'):8,
          ('l_Au','e_Ch','t2'):10,
          ('l_Au','e_Ru','t1'):18,
          ('l_Au','e_Ru','t2'):20,
          ('l_Ci','e_US','t1'):10,
          ('l_Ci','e_US','t2'):12,
          ('l_Ci','e_EU','t1'):18,
          ('l_Ci','e_EU','t2'):20,
          ('l_Ci','e_Ch','t1'):22,
          ('l_Ci','e_Ch','t2'):24,
          ('l_Ci','e_Ru','t1'):25,
          ('l_Ci','e_Ru','t2'):27,
          ('l_Ch','e_US','t1'):30,
          ('l_Ch','e_US','t2'):32,
          ('l_Ch','e_EU','t1'):28,
          ('l_Ch','e_EU','t2'):30,
          ('l_Ch','e_Ch','t1'):5,
          ('l_Ch','e_Ch','t2'):7,
          ('l_Ch','e_Ru','t1'):12,
          ('l_Ch','e_Ru','t2'):14}

TC_etr = {('e_US','t1','r1'):60,        #[€/kg enr. Li] TransportCost (Flow): from enrichment site e with technology t to reactor r
          ('e_US','t2','r1'):80,
          ('e_EU','t1','r1'):30,
          ('e_EU','t2','r1'):45,
          ('e_Ch','t1','r1'):90,
          ('e_Ch','t2','r1'):110,
          ('e_Ru','t1','r1'):85,
          ('e_Ru','t2','r1'):100}

PC_l  = {('l_Au'):conversions.compound_to_Li_price(9900, conversions.w_Li_LIOH_H2O),      #[€/kg nat. Li] Production costs : from extraxtion&processing site l 
         ('l_Ci'):conversions.compound_to_Li_price(9900, conversions.w_Li_LIOH_H2O),
         ('l_Ch'):conversions.compound_to_Li_price(9900, conversions.w_Li_LIOH_H2O)}     # [€/kg nat. Li]; ca. 55.4 €/kg; USGS MCS 2025 p.110: LiOH·H2O spot, China, Nov 2024
           

EC_et = {('e_US','t1'):30,              #[€/kg nat. Li] Enrichment costs: enrichment site e with technology t
         ('e_US','t2'):35,
         ('e_EU','t1'):32,
         ('e_EU','t2'):38,
         ('e_Ch','t1'):25,
         ('e_Ch','t2'):28,
         ('e_Ru','t1'):27,
         ('e_Ru','t2'):30}

# Capacities
#[kg nat. Li] extraction&processing capacity ceiling (max. amount handable)
# Per-country extraction/processing capacity ceiling (upper bound on total outflow from l).
# Proxy: 2024 mine production, lithium content. USGS MCS 2025 p.111.
Cap_l = {'l_Au':  88000000,   #[kg nat. Li] Australia
         'l_Ci': 49000000,   #[kg nat. Li] Chile
         'l_Ch': 41000000}   #[kg nat. Li] China
                           

Cap_et = {('e_US','t1'):200000,        #[kg nat. Li] enrichment capacity ceiling (max. amount handable by one site)
          ('e_US','t2'):200000,        # TODO Day 9: replace smoke-run placeholder (>f_ne*D_r1=115_556) with cascade-economics value
          ('e_EU','t1'):200000,
          ('e_EU','t2'):200000,
          ('e_Ch','t1'):200000,
          ('e_Ch','t2'):200000,
          ('e_Ru','t1'):200000,
          ('e_Ru','t2'):200000}
                            

Cap_et_min = {('e_US','t1'):1,          #[kg nat. Li] enrichment bottom ceiling (min. amount handable by one site)
              ('e_US','t2'):1,
              ('e_EU','t1'):1,
              ('e_EU','t2'):1,
              ('e_Ch','t1'):1,
              ('e_Ch','t2'):1,
              ('e_Ru','t1'):1,
              ('e_Ru','t2'):1}

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
prod_extr = { ("Argentina"): 18_000_000,    #[kg nat. Li] Li-content, USGS MCS 2025 (2024e)
              ("Australia"): 88_000_000, 
              ("Brazil"):   10_000_000,   
              ("Canada"):   4_300_000,
              ("Chile"):    49_000_000,
              ("China"):    41_000_000,
              ("Namibia"):  2_700_000,
              ("Portugal"): 380_000,
              ("Zimbabwe"): 22_000_000,
              ("Other countries"): 4_620_000
}

s_extr_k = conversions.s_k_shares(prod_extr) # [-] production share of each country - sum = 1

s_enr_k = {("e_US"): 1/3,                 #[-] assumed enrichment-market shares; equal over states with demonstrated/probable capability
           ("e_Ru"): 1/3,                 #    EU = non-supplier (ICOMAX only developing). HHI_enr = 3*(1/3)^2 = 0.333
           ("e_Ch"): 1/3,                 #    stated assumption, NO capacity data. Giegerich2019 / US_LithiumProcessing_2021 / Dackombe2026
           ("e_EU"): 0}


WGI_PV_EU = {("Austria"):     {'y_24': 0.5, 'av_3': 0.6},     # [-] WGI-PV per EU country {'y_24': 2024, 'av_3': 3-yr avg 2022-24} high = stable.  [WGI2025]
             ("Belgium"):     {'y_24': 0.1, 'av_3': 0.2},
             ("Bulgaria"):    {'y_24': 0.0, 'av_3': 0.2},
             ("Croatia"):     {'y_24': 0.6, 'av_3': 0.7},
             ("Cyprus"):      {'y_24': 0.4, 'av_3': 0.4},
             ("Czechia"):     {'y_24': 1.0, 'av_3': 1.0},
             ("Denmark"):     {'y_24': 0.8, 'av_3': 0.8},
             ("Estonia"):     {'y_24': 0.7, 'av_3': 0.8},
             ("Finland"):     {'y_24': 0.8, 'av_3': 0.9},
             ("France"):      {'y_24': -0.2, 'av_3': -0.1},
             ("Germany"):     {'y_24': 0.1, 'av_3': 0.4},
             ("Greece"):      {'y_24': 0.1, 'av_3': 0.3},
             ("Hungary"):     {'y_24': 0.4, 'av_3': 0.6},
             ("Ireland"):     {'y_24': 0.7, 'av_3': 0.8},
             ("Italy"):       {'y_24': 0.3, 'av_3': 0.4},
             ("Latvia"):      {'y_24': 0.6, 'av_3': 0.7},
             ("Lithuania"):   {'y_24': 0.9, 'av_3': 1.0},
             ("Luxembourg"):  {'y_24': 1.1, 'av_3': 1.0},
             ("Malta"):       {'y_24': 0.8, 'av_3': 0.9},
             ("Netherlands"): {'y_24': 0.4, 'av_3': 0.6},
             ("Poland"):      {'y_24': 0.5, 'av_3': 0.5},
             ("Portugal"):    {'y_24': 0.5, 'av_3': 0.7},
             ("Romania"):     {'y_24': 0.2, 'av_3': 0.4},
             ("Slovakia"):    {'y_24': 0.6, 'av_3': 0.6},
             ("Slovenia"):    {'y_24': 0.7, 'av_3': 0.8},
             ("Spain"):       {'y_24': 0.0, 'av_3': 0.1},
             ("Sweden"):      {'y_24': 0.6, 'av_3': 0.8}}

WGI_PV = {("Australia"): {'y_24': 0.8,  'av_3': 0.9},         # [-] WGI-PV per model country. high = stable.  [WGI2025]
          ("Chile"):     {'y_24': 0.1,  'av_3': 0.1},
          ("China"):     {'y_24': -0.2, 'av_3': -0.2},
          ("US"):        {'y_24': -0.1, 'av_3': -0.2},
          ("Russia"):    {'y_24': -0.9, 'av_3': -0.8}}

WGI_PV['EU'] = {'y_24': conversions.WGI_PV_average({c: v['y_24'] for c, v in WGI_PV_EU.items()}),   # EU = mean over members, added as one more country
                'av_3': conversions.WGI_PV_average({c: v['av_3'] for c, v in WGI_PV_EU.items()})}

                                                                            # political instability indicator g = (2.5 - PV)/5, high = risky
g_24 = {c: conversions.WGI_PV_to_g(v['y_24']) for c, v in WGI_PV.items()}   # [-] year 2024
g_3  = {c: conversions.WGI_PV_to_g(v['av_3']) for c, v in WGI_PV.items()}   # [-] 3-yr avg 2022-24

g_extr = {("l_Au"): g_24["Australia"],   # [-] political instability, extraction sites (2024)
          ("l_Ci"): g_24["Chile"],
          ("l_Ch"): g_24["China"]}

g_enr  = {("e_US"): g_24["US"],           # [-] political instability, enrichment sites (2024)
          ("e_EU"): g_24["EU"],
          ("e_Ch"): g_24["China"],        # same China PV as l_Ch
          ("e_Ru"): g_24["Russia"]}