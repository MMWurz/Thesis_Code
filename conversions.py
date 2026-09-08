####################### UNIT CONVERSION #######################

# Li mass fractions (natural isotopic abundance)
USD_TO_EUR = 1 / 1.082            # ECB 2024 annual avg EUR/USD = 1.082

w_Li_LI2CO3      = 0.188      # [kg Li / kg Li2CO3
w_Li_LIOH_H2O    = 0.165      # [kg Li / kg LiOH·H2O
w_Li_SPODUMENE_6 = 0.028      # [kg Li / kg spodumene (6% Li2O)

def compound_to_Li_price(price_usd_t, w_li):                # [$/t compound -> €/kg contained natural Li]
    return price_usd_t / w_li / 1000 * USD_TO_EUR


####################### FUNCTION FOR SR #######################
#prod_tot = sum(params.prod_extr.values())   #[kg nat. Li] total worldwide produced Li 2024 - 240k tons 

#s_extr_k = {k: v/prod_tot for k, v in prod_extr.items()}    # production share of each country - sum = 1

def s_k_shares(production):
    prod_tot = sum(production.values())     #[kg nat. Li] total worldwide produced Li 2024 - 240k tons
    return {k: v/prod_tot for k, v in production.items()}

def WGI_PV_average(countries):
    return  sum(countries.values()) / len(countries) 

def WGI_PV_to_g(country):
    return (2.5 - country)/5

####################### FIXED COSTS #######################

def capex_power_law(Q, K_ref, Q_ref, b):            # [€] Capacity-factored capital cost (six-tenths rule). Towler&Sinnott p.243
    return K_ref * (Q / Q_ref) ** b

def capital_recovery_factor(i, n):                  # [1/yr] Share of investment repaid per year. Towler&Sinnott Eq. 9.26.
    return i * (1 + i) ** n / ((1 + i) ** n - 1)

def geometric_breakpoints(Q_min, Q_max, n_seg):     # [kg/yr] n_seg+1 geometrically spaced capacities -> constant relative PWL error.
    ratio = (Q_max / Q_min) ** (1 / n_seg)
    return [Q_min * ratio ** k for k in range(n_seg + 1)]

def pwl_segments(Qbar, Kbar):                       # Segment widths [kg/yr] and slopes [€ per kg/yr] of the PWL curve.                                                
    widths = [Qbar[j] - Qbar[j-1] for j in range(1, len(Qbar))]
    slopes = [(Kbar[j] - Kbar[j-1]) / widths[j-1] for j in range(1, len(Kbar))]
    return widths, slopes
