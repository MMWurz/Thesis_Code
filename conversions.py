# UNIT CONVERSION

# Li mass fractions (natural isotopic abundance)
USD_TO_EUR = 1 / 1.082            # ECB 2024 annual avg EUR/USD = 1.082

w_Li_LI2CO3      = 0.188      # kg Li / kg Li2CO3
w_Li_LIOH_H2O    = 0.165      # kg Li / kg LiOH·H2O
w_Li_SPODUMENE_6 = 0.028      # kg Li / kg spodumene (6% Li2O)

def compound_to_Li_price(price_usd_t, w_li):                # [$/t compound -> €/kg contained natural Li]
    return price_usd_t / w_li / 1000 * USD_TO_EUR



