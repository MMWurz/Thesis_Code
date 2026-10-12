####################### UNIT CONVERSION #######################

# Li mass fractions (natural isotopic abundance)
USD_TO_EUR = 1 / 1.0824          # ECB 2024 annual avg EUR/USD = 1.0824

w_Li_LI2CO3      = 0.188      # [kg Li / kg Li2CO3
w_Li_LIOH_H2O    = 0.165      # [kg Li / kg LiOH·H2O
w_Li_SPODUMENE_6 = 0.028      # [kg Li / kg spodumene (6% Li2O)


####################### FUNCTION FOR SR #######################

def s_k_shares(production):
    prod_tot = sum(production.values())     #[kg nat. Li] total worldwide produced Li 2024 - 240k tons
    return {k: v/prod_tot for k, v in production.items()}

def WGI_PV_average(countries):
    return  sum(countries.values()) / len(countries) 

def WGI_PV_to_g(country):
    return (2.5 - country)/5

####################### FIXED COSTS #######################

def capex_power_law(Q, CC_ref, Q_ref, b):           # [€] Capacity-factored capital cost (six-tenths rule). Towler&Sinnott p.243
    return CC_ref * (Q / Q_ref) ** b

def capital_recovery_factor(i, n):                  # [1/yr] Share of investment repaid per year. Towler&Sinnott Eq. 9.26.
    return i * (1 + i) ** n / ((1 + i) ** n - 1)

def geometric_breakpoints(Q_min, Q_max, n_seg):     # [kg/yr] n_seg+1 geometrically spaced capacities -> constant relative PWL error.
    ratio = (Q_max / Q_min) ** (1 / n_seg)
    return [Q_min * ratio ** k for k in range(n_seg + 1)]

def pwl_segments(Qbar, CCbar):                      # Segment widths [kg/yr] and slopes [€ per kg/yr] of the PWL curve.                                                
    widths = [Qbar[j] - Qbar[j-1] for j in range(1, len(Qbar))]
    slopes = [(CCbar[j] - CCbar[j-1]) / widths[j-1] for j in range(1, len(CCbar))]
    return widths, slopes
