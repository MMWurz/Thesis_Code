import conversions
# All model parameters, bounds, and configuration constants (costs, emission factors, capacities, solver settings).

# Flow unit/ commodity: kg - either natural or enriched

# INDEX-SETS
L = ['l_Au',    'l_Ci',         'l_Ch',         'l_Ar',     'l_Fr']    # [Location] Extraction & Processing site 
#    Australia,   Chile,        China           Argentinia  France

E = ['e_US',      'e_EU',      'e_Ch',      'e_Ru']     # [Location] Enrichment site
#    USA,           EU,          China,       Russia

T = ['t_chemEx', 't_dispEl', 't_amalgam']               # [Technology] Enrichment site
#    chem.Exch.,  Disp.Ch & el.chem.Exch,  COLEX/ICOMAX
#    t_dispEl MERGES displacement chromatography and electrochemical exchange: no public data
#    separates them, so they shared EC = 1250 and were IDENTICAL in every model parameter
#    (EC_et, Cap_et, Cap_et_min, TC_let, TC_etr all equal) -> two identical columns, which made
#    the solver's pick between them arbitrary. Merged into one cost tier; tab_3_EC_ladder.

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
# Per-country extraction/processing capacity ceiling (upper bound on total annual outflow from l).
# Basis: CONTAINED elemental lithium of the 2024 mid-stream output, Li-content column of
# tab_3_Li_coutry_capacity (BGS 2026). Same basis as Q_let and PC_l, so the ceiling is unit-consistent.
# Never binding at the current demand: the tightest is l_Au at ~31x the 89_440 kg nat. Li/yr feed.
Cap_l = {'l_Au':  2_793_000,                       #[kg nat. Li/yr] Australia, LiOH*H2O 16_929 * w 0.165
         'l_Ci': 50_639_000,                       #[kg nat. Li/yr] Chile, LiOH*H2O 3_525 + Li2CO3 47_114
         'l_Ch': 41_000_000,                       #[kg nat. Li/yr] China, BGS contained-Li row
         'l_Ar': 15_228_000,                       #[kg nat. Li/yr] Argentina, Li2CO3 81_000 * w 0.188 (BGS estimate)
         'l_Fr':  5_600_000}                       #[kg nat. Li/yr] France, BGS-reported Li content (own w gives 5_610)

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
         ('l_Ci','e_EU'): 1.537,
         ('l_Ci','e_Ch'): 1.899,
         ('l_Ci','e_Ru'): 1.724,
         ('l_Ch','e_US'): 1.101,
         ('l_Ch','e_EU'): 2.066,
         ('l_Ch','e_Ch'): 0.000,
         ('l_Ch','e_Ru'): 0.291,
         ('l_Ch','e_Ru'): 0.291,
         ('l_Ar','e_US'): 1.321,      # CERDI 
         ('l_Ar','e_EU'): 1.439,      
         ('l_Ar','e_Ch'): 2.092,      
         ('l_Ar','e_Ru'): 1.673,
         ('l_Fr','e_US'): 1.036,      # CERDI V1.1, tab_3_d_le: d = 9_980 km
         ('l_Fr','e_EU'): 0.405,      #   3_904 km - the French port is Fos/Marseille (5.29E, 43.35N),
         ('l_Fr','e_Ch'): 1.676,      #   so the lane to Rotterdam runs via Gibraltar, not short-sea
         ('l_Fr','e_Ru'): 0.371}      #   3_576 km - Med -> Black Sea, the shortest Russian lane of all l
TC_let = {(l, e, t): TC_le[(l,e)] for l in L for e in E for t in T}   #[€/kg nat. Li] broadcast across technologies (transport is tech-independent)

# --- SUPERSEDED 2026-10-05, kept for the record: flat freight-only TC_etr, uniform across sites ---
# # Transport Costs TC - enrichment site e to reactor r: freight only, UNIFORM across sites.
# #   (3600 $/TEU SCFI comprehensive spot + 250 $/container IMDG hazardous cargo surcharge,
# #    Crowley Tariff 002 Rule 8) / 1.0824 $/EUR / 5200 kg/yr = one surcharged container-equivalent per year.
# #   No distance term (DEMO site undecided). NO country differentiation: export-licensing and sanctions
# #   exposure are country-level institutional differences, already priced on the RISK axis via g_enr -
# #   charging them here too would double-count. A uniform TC_etr is decision-neutral anyway (sum Q_etr = D_r1
# #   is fixed, so it only adds a constant to C_tot). The country-differentiated premium (EU 50 / US 90 /
# #   CN 130 / RU 150 EUR/kg) had no published rate behind it and is kept as a SCENARIO, not a base parameter.
# TC_er_freight = 0.68          #[€/kg enr. Li] (3600 + 250) / 1.0824 / 5200
# TC_er = {(e, r): TC_er_freight for e in E for r in R}
# ---------------------------------------------------------------------------------------------------

# Transport Costs TC - enrichment site e to reactor r (Rotterdam): TC_etr = c_TC * d_er * w * phi_haz,
#   equ_3_TC_etr / tab_3_TC_etr. The product ships as lithium METAL, so the 1/w carried by c_TC drops
#   out (c_TC * w = 0.0171 €/(kg * 10^3 km)) and phi_haz = (3600+250)/3600 = 1.069 is the IMDG
#   hazardous-cargo mark-up (Crowley Tariff 002 Rule 8). Distances d_er from CERDI, as in TC_le.
#   Licensing and sanctions exposure is NOT priced here: it sits on the RISK axis via g_enr, charging
#   it twice would double-count. The old country-differentiated premium (EU 50 / US 90 / CN 130 /
#   RU 150 €/kg) has no published rate behind it and is kept as a SCENARIO only.
TC_er = {('e_US','r1'): 0.18,   #[€/kg enr. Li] d_er =  9_623 km
         ('e_EU','r1'): 0.00,   #               d_er =      0 km (reactor node = EU port)
         ('e_Ch','r1'): 0.36,   #               d_er = 19_901 km
         ('e_Ru','r1'): 0.12}   #               d_er =  6_828 km
TC_etr = {(e, t, r): TC_er[(e,r)] for e in E for t in T for r in R}                 #[€/kg enr. Li] broadcast across technologies

         
PC_l  = {('l_Au'): 89.56,    #[€/kg contained nat. Li] blended trade-based feed price, tab_3_Li_prices_trade
        ('l_Ci'):  49.14,    #   = (TV_LiOH + TV_Li2CO3) / (m_LiOH*0.165 + m_Li2CO3*0.188) / 1.0824,
        ('l_Ch'): 102.17,    #   equ_3_blended_price, WITS / UN Comtrade 2024 export values.
        ('l_Ar'):  41.91,    #   NO carbonate->hydroxide adder any more: pooling both compounds already
        ('l_Fr'): 100.30}    #   puts every country on one contained-Li basis.


EC_e = {'t_chemEx':  2500,                          #[€/kg enr. Li6 product] chemical exchange (liquid)  -- Badea "very high"
        't_dispEl':  1250,                          #[€/kg enr. Li6 product] Disp.Ch & el.chem.Exch      -- Badea "moderate" for both;
                                                    #                        Acosta 0.77 k$/kg is an electricity-only FLOOR for the
                                                    #                        electrochemical half and does not separate the two
        't_amalgam': 2000}                          #[€/kg enr. Li6 product] COLEX/ICOMAX (amalgam)       -- Giegerich; high scen. 2000 (Ward Hg financing)
EC_et = {(e, t): EC_e[t] for e in E for t in T}     #[€/kg enr. Li6 product] per technology, broadcast across sites; charged on Q_etr (OUTPUT)


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


WGI_PV_EU = {("Austria"):     {'y_25':  0.531158, 'av_3':  0.616873},   # [-] WGI-PV per EU country {'y_25': 2025, 'av_3': 3-yr avg 2023-25} high = stable.  [WGI2026]
             ("Belgium"):     {'y_25':  0.172754, 'av_3':  0.183750},   #     Governance estimate, sheet "pv" of the 2026 release (Data/wgidataset_with_sourcedata-2026.xlsx).
             ("Bulgaria"):    {'y_25':  0.245054, 'av_3':  0.239837},   #     Full precision on purpose: the EU mean below is formed from unrounded members.
             ("Croatia"):     {'y_25':  0.684057, 'av_3':  0.694695},
             ("Cyprus"):      {'y_25':  0.440780, 'av_3':  0.409945},
             ("Czechia"):     {'y_25':  1.020596, 'av_3':  1.060902},
             ("Denmark"):     {'y_25':  0.791270, 'av_3':  0.839565},
             ("Estonia"):     {'y_25':  0.887544, 'av_3':  0.852241},
             ("Finland"):     {'y_25':  0.955030, 'av_3':  0.870956},
             ("France"):      {'y_25': -0.092230, 'av_3': -0.082656},
             ("Germany"):     {'y_25':  0.208281, 'av_3':  0.312588},
             ("Greece"):      {'y_25':  0.276693, 'av_3':  0.309057},
             ("Hungary"):     {'y_25':  0.509335, 'av_3':  0.565445},
             ("Ireland"):     {'y_25':  0.747951, 'av_3':  0.802160},
             ("Italy"):       {'y_25':  0.456738, 'av_3':  0.454672},
             ("Latvia"):      {'y_25':  0.809011, 'av_3':  0.827202},
             ("Lithuania"):   {'y_25':  0.932903, 'av_3':  0.962785},
             ("Luxembourg"):  {'y_25':  1.192860, 'av_3':  1.104956},
             ("Malta"):       {'y_25':  1.036044, 'av_3':  0.964499},
             ("Netherlands"): {'y_25':  0.534518, 'av_3':  0.578149},
             ("Poland"):      {'y_25':  0.693775, 'av_3':  0.623891},
             ("Portugal"):    {'y_25':  0.702010, 'av_3':  0.716473},
             ("Romania"):     {'y_25':  0.206785, 'av_3':  0.336770},
             ("Slovakia"):    {'y_25':  0.666500, 'av_3':  0.629187},   # WGI name: "Slovak Republic"
             ("Slovenia"):    {'y_25':  0.877008, 'av_3':  0.869785},
             ("Spain"):       {'y_25':  0.178328, 'av_3':  0.163813},
             ("Sweden"):      {'y_25':  0.852460, 'av_3':  0.772306}}

WGI_PV = {("Australia"): {'y_25':  0.780585, 'av_3':  0.853335},       # [-] WGI-PV per model country. high = stable.  [WGI2026]
          ("Chile"):     {'y_25':  0.170603, 'av_3':  0.188075},
          ("China"):     {'y_25':  0.022475, 'av_3': -0.077793},
          ("US"):        {'y_25': -0.302082, 'av_3': -0.186962},
          ("Russia"):    {'y_25': -0.944959, 'av_3': -0.904771},
          ("Argentina"): {'y_25':  0.162060, 'av_3':  0.050308},
          ("France"):    {'y_25': -0.092230, 'av_3': -0.082656}}   # == WGI_PV_EU["France"]

WGI_PV['EU'] = {'y_25': conversions.WGI_PV_average({c: v['y_25'] for c, v in WGI_PV_EU.items()}),   # [-] EU = mean over members, added as one more country
                'av_3': conversions.WGI_PV_average({c: v['av_3'] for c, v in WGI_PV_EU.items()})}

                                                                            # political instability indicator g = (2.5 - PV)/5, high = risky
g_25 = {c: conversions.WGI_PV_to_g(v['y_25']) for c, v in WGI_PV.items()}   # [-] year 2025
g_3  = {c: conversions.WGI_PV_to_g(v['av_3']) for c, v in WGI_PV.items()}   # [-] 3-yr avg 2023-25

g_extr = {("l_Au"): g_25["Australia"],   # [-] political instability, extraction sites (2025)
          ("l_Ci"): g_25["Chile"],
          ("l_Ch"): g_25["China"],
          ("l_Ar"): g_25["Argentina"],
          ("l_Fr"): g_25["France"]}       # NOTE g_Fr = 0.52 > g_Ch = 0.50: on WGI-PV 2025 France is the
                                          #      riskiest source, while e_EU carries the EU MEAN (0.38)

g_enr  = {("e_US"): g_25["US"],           # [-] political instability, enrichment sites (2025)
          ("e_EU"): g_25["EU"],
          ("e_Ch"): g_25["China"],        # same China PV as l_Ch
          ("e_Ru"): g_25["Russia"]}