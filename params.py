import conversions
# All model parameters, bounds, and configuration constants (costs, emission factors, capacities, solver settings).

# Flow unit/ commodity: kg - either natural or enriched

# INDEX-SETS
L = ['l_Au',          'l_Ci',       'l_Ch']             # [Location] Extraction & Processing site 
#    Australia,      Chile,        China

E = ['e_US',      'e_EU',      'e_Ch',      'e_Ru']     # [Location] Enrichment site
#    USA,           EU,          China,       Russia

T = ['t_chemEx', 't_dispChr', 't_elChem', 't_amalgam']  # [Technology] Enrichment site

R = ['r1']                                              # [Location] Rector

####################### COSTS #######################

# Missc.
D_r1 = 5_200                                        #[kg enr. Li/yr] TARGET-YEAR SNAPSHOT: ANNUAL demand of reactor for enriched Li
                                                    #   = 52 t 90%-enr. Li (WCLL breeder inventory, 2 GWfus DEMO, Giegerich 2019) / 10 yr build-up (2040-49 procurement window).
                                                    #   BUILD-UP ONLY: the 224 kg/yr burn-up replacement (Giegerich 2019) is NOT added - a plant sized for 5.2 t/yr covers it easily.
                                                    #   NO /alpha: Giegerich's "52 t pure 6Li" == his "26 t/GWfus 90%-enriched Li" == the enriched PRODUCT, not the bare isotope (~47 t 6Li).

f_ne = 17.2                            #[kg nat. Li/ kg enr. Li] 90% enrichment


Q_max_enr = D_r1                    #[kg enr. Li/yr] upper flow bound (one link must carry full demand)
Q_max_nat = f_ne * D_r1             #[kg nat. Li/yr] upper flow bound
                                    # TODO: have a look at big M - bounds are now 10x tighter after the D_r1 rescale (52_000 -> 5_200)

# Capacities
#[kg nat. Li/yr] extraction&processing capacity ceiling (max. amount handable per year)
# Per-country extraction/processing capacity ceiling (upper bound on total annual outflow from l).
# Proxy: 2024 mine production (an ANNUAL rate), lithium content. USGS MCS 2025 p.111.
Cap_l = {'l_Au': 88_000_000,                        #[kg nat. Li/yr] Australia
         'l_Ci': 49_000_000,                        #[kg nat. Li/yr] Chile
         'l_Ch': 41_000_000}                        #[kg nat. Li/yr] China
                           

Cap_e_min_prod  = 1_000    #[kg/yr enr. product] = ICOMAX FOAK target
Cap_e_prod      = 40_000   #[kg/yr enr. product] = Y-12 historical avg

Cap_et_min = {(e,t): f_ne * Cap_e_min_prod for e in E for t in T}   #[kg nat. Li/yr]
Cap_et     = {(e,t): f_ne * Cap_e_prod     for e in E for t in T}   #[kg nat. Li/yr]

# Costs
#[€] CAPEX FixedCost (Building) per enrichment site; tech-independent placeholder (Day 9)
      
K_ref   = 508e6                                     #[€2024] eq:capex_escalation
Q_ref   = 200_000                                   #[kg/yr enr. product] Ault large plant
b_scale = 0.57                                      #[-]  eq:capex_exponent
n_life  = 30                                        #[yr] plant lifetime
fom     = 0.07                                      #[1/yr] Towler&Sinnott p.324
i_e = {'e_US':0.050, 'e_EU':0.050,                  #[-] real cost of capital, Rothwell 2009
       'e_Ch':0.025, 'e_Ru':0.025}                  #    state-financed (China assumed)
f_e = {'e_US':1.00, 'e_EU':1.13,                    #[-] location factor, Towler&Sinnott Tab.7.7
       'e_Ch':0.61, 'e_Ru':1.53}                    #    Ru sensitivity: 0.57

# Fixed cost FC_e - derived
CRF_e = {e: conversions.capital_recovery_factor(i_e[e], n_life) for e in E}
M_e   = {e: (CRF_e[e] + fom) * f_e[e] for e in E}   #[1/yr] tab:FC_multipliers
Qbar  = conversions.geometric_breakpoints(Cap_e_min_prod, Cap_e_prod, n_seg=4)
Kbar  = [conversions.capex_power_law(q, K_ref, Q_ref, b_scale) for q in Qbar]
seg_width, seg_slope = conversions.pwl_segments(Qbar, Kbar)

# Transport Costs TC - with TC = c_TC * distance (c_TC = 0.1038 €/(kg nat. Li * 10^3 km))
TC_le = {('l_Au','e_US'): 1.329,                    #[€/kg nat. Li] tab:TC_let_values
         ('l_Au','e_EU'): 2.205,
         ('l_Au','e_Ch'): 1.067,
         ('l_Au','e_Ru'): 1.216,
         ('l_Ci','e_US'): 0.889,
         ('l_Ci','e_EU'): 1.536,
         ('l_Ci','e_Ch'): 1.899,
         ('l_Ci','e_Ru'): 1.724,
         ('l_Ch','e_US'): 1.101,
         ('l_Ch','e_EU'): 2.065,
         ('l_Ch','e_Ch'): 0.000,
         ('l_Ch','e_Ru'): 0.291}
TC_let = {(l, e, t): TC_le[(l,e)] for l in L for e in E for t in T}   #[€/kg nat. Li] broadcast across technologies (transport is tech-independent)

# Transport Costs TC - basically made up (TODO)
TC_er = {('e_US','r1'): 90,   #[€/kg enr. Li] allied, moderate export control
         ('e_EU','r1'): 50,   #               domestic, no border/export friction
         ('e_Ch','r1'): 130,  #               export controls and re-export licensing
         ('e_Ru','r1'): 150}  #               export-controlled, sanctions-adjacent
TC_etr = {(e, t, r): TC_er[(e,r)] for e in E for t in T for r in R}                 #[€/kg enr. Li] broadcast across technologies

         
PC_l  = {('l_Au'):89.96,      #[€/kg Li] = Trade-based feed prices =Production costs : from extraxtion&processing site l 
        ('l_Ci'):52.14,
        ('l_Ch'):103.04} 


EC_e = {'t_chemEx':  2500,                          #[€/kg enr. Li6 product] chemical exchange (liquid)  -- Badea "very high"
        't_dispChr': 1250,                          #[€/kg enr. Li6 product] displacement chromatography -- Badea "moderate"
        't_elChem':  1250,                          #[€/kg enr. Li6 product] electrochemical exchange    -- Acosta 0.77 k$/kg floor -> moderate
        't_amalgam': 1000}                          #[€/kg enr. Li6 product] COLEX/ICOMAX (amalgam)       -- Giegerich; high scen. 2000 (Ward Hg financing)
EC_et = {(e, t): EC_e[t] for e in E for t in T}     #[€/kg enr. Li6 product] per technology, broadcast across sites; charged on Q_etr (OUTPUT)
EC_amalgam_high = 2000                              #[€/kg enr. Li6 product] RUN C: COLEX/ICOMAX high scenario (Ward Hg financing)


####################### SR #######################

prod_extr = { ("Argentina"): 18_000_000,    #[kg nat. Li/yr] Li-content, USGS MCS 2025 (2024e). Annual production; only the SHARES matter for HHI, so the /yr basis cancels.
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

WGI_PV['EU'] = {'y_24': conversions.WGI_PV_average({c: v['y_24'] for c, v in WGI_PV_EU.items()}),   # [-] EU = mean over members, added as one more country
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