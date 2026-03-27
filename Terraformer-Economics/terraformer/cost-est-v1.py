"""
Terraformer Cost Estimation v1  —  Synthetic CH4 Production Cost
Sabatier methanation  +  green hydrogen  +  DAC-derived CO2

Chart 1: CH4 cost vs electricity price ($/kWh)
         Fixed:  H2 = $1/kg  |  Capex = $100k
"""

import matplotlib.pyplot as plt
import numpy as np
import os

# ============================================================
# OUTPUT
# ============================================================
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)


# ============================================================
# PHYSICAL CONSTANTS  —  Sabatier: CO2 + 4 H2 → CH4 + 2 H2O
# ============================================================
MW_CH4 = 16.0   # g/mol
MW_CO2 = 44.0   # g/mol
MW_H2  =  2.0   # g/mol

# Stoichiometric feedstock per kg CH4 produced (from molar ratios)
H2_STOICH_KG_PER_KG_CH4  = (4 * MW_H2) / MW_CH4   # = 0.500 kg H2  / kg CH4
CO2_STOICH_KG_PER_KG_CH4 = MW_CO2      / MW_CH4   # = 2.750 kg CO2 / kg CH4

# Energy unit conversion: $/kg CH4  →  $/MMBtu
CH4_HHV_MJ_PER_KG    = 55.5                              # Higher Heating Value of CH4 (MJ/kg)
CH4_HHV_KWH_PER_KG   = CH4_HHV_MJ_PER_KG / 3.6          # = 15.42 kWh/kg
MMBTU_IN_MJ           = 1055.06                           # 1 MMBtu = 1055.06 MJ
KG_CH4_PER_MMBTU      = MMBTU_IN_MJ / CH4_HHV_MJ_PER_KG  # = 19.01 kg CH4 / MMBtu
# Conversion:  $/MMBtu = ($/kg CH4) × KG_CH4_PER_MMBTU


# ============================================================
# PROCESS PARAMETERS
# ============================================================

SABATIER_EFFICIENCY = 0.95
# Fraction of H2 (and CO2) feedstock that actually converts to CH4.
# The remaining 5 % passes through unreacted (assumed lost — conservative).
#
# Impact on feedstock consumption:
#   actual feed = stoichiometric / SABATIER_EFFICIENCY
#   At 95 % efficiency the feed penalty vs perfect stoichiometry is +5.3 %.

SABATIER_ELEC_KWH_PER_KG_CH4 = 1.0
# Auxiliary electricity consumed per kg CH4 — gas compression, pumps,
# cooling loops, and instrumentation.
#
# The Sabatier reaction itself is strongly exothermic (−165 kJ/mol CH4),
# so no electric heating is required.  This term is balance-of-plant only.


# ============================================================
# ECONOMIC PARAMETERS  (Chart 1 fixed values)
# ============================================================

CO2_PRICE_PER_TONNE = 100.0                        # $/t CO2  (DAC assumed)
CO2_PRICE_PER_KG    = CO2_PRICE_PER_TONNE / 1000   # $/kg CO2

H2_PRICE_FIXED  = 1.0        # $/kg H2  (green H2, fixed for Chart 1)
CAPEX_FIXED     = 100_000    # $ total installed Sabatier capex

AMORT_YEARS = 5
# Capital amortisation period (years).
# Capex is spread uniformly over AMORT_YEARS × PLANT_ANNUAL_CAPACITY_KG.

PLANT_POWER_MW   = 1.0    # Nameplate CH4 output power (MW, HHV basis)
CAPACITY_FACTOR  = 1.0    # Fraction of 8760 h/yr the plant operates at full output
HOURS_PER_YEAR   = 8760

# Annual CH4 output derived from plant power rating:
#   rate (kg/h)  =  power (kW) / CH4_HHV_KWH_PER_KG
#   annual (kg)  =  rate × hours × capacity factor
CH4_RATE_KG_PER_HR    = (PLANT_POWER_MW * 1000) / CH4_HHV_KWH_PER_KG
PLANT_ANNUAL_CAPACITY_KG = CH4_RATE_KG_PER_HR * HOURS_PER_YEAR * CAPACITY_FACTOR


# ============================================================
# COST TRANSLATION FUNCTIONS  (all return $/kg CH4)
# ============================================================

def h2_feedstock_cost(h2_price_per_kg):
    """
    H2 feedstock cost per kg of CH4 produced.

    Stoichiometry  (CO2 + 4 H2 → CH4 + 2 H2O):
        4 mol H2 × 2 g/mol  per  1 mol CH4 × 16 g/mol  →  0.500 kg H2 / kg CH4

    Efficiency term:
        The reactor is fed 1/SABATIER_EFFICIENCY times the stoichiometric
        H2 so that the reacted fraction (= SABATIER_EFFICIENCY) yields
        exactly 1 kg CH4.  The unreacted remainder is lost.

        actual H2 input  =  H2_STOICH_KG_PER_KG_CH4 / SABATIER_EFFICIENCY
    """
    h2_input_kg = H2_STOICH_KG_PER_KG_CH4 / SABATIER_EFFICIENCY   # kg H2 / kg CH4
    return h2_price_per_kg * h2_input_kg


def co2_feedstock_cost():
    """
    CO2 feedstock cost per kg of CH4 produced.  Uses global CO2_PRICE_PER_TONNE.

    Stoichiometry  (CO2 + 4 H2 → CH4 + 2 H2O):
        1 mol CO2 × 44 g/mol  per  1 mol CH4 × 16 g/mol  →  2.750 kg CO2 / kg CH4

    Efficiency term:
        Identical logic to H2 — more CO2 is fed than stoichiometrically
        needed to compensate for the unconverted fraction.

        actual CO2 input  =  CO2_STOICH_KG_PER_KG_CH4 / SABATIER_EFFICIENCY
    """
    co2_input_kg = CO2_STOICH_KG_PER_KG_CH4 / SABATIER_EFFICIENCY  # kg CO2 / kg CH4
    return CO2_PRICE_PER_KG * co2_input_kg


def capex_cost(total_capex_dollars,
               amort_years=AMORT_YEARS,
               annual_capacity_kg=PLANT_ANNUAL_CAPACITY_KG):
    """
    Amortised capital cost per kg of CH4 produced.

    Assumes the plant runs continuously at full annual_capacity_kg for
    amort_years years.  Total lifetime CH4 = amort_years × annual_capacity_kg.
    Capex is then divided evenly across every kg of CH4 ever produced.

        capex per kg  =  total_capex_dollars / (amort_years × annual_capacity_kg)
    """
    lifetime_production_kg = amort_years * annual_capacity_kg
    return total_capex_dollars / lifetime_production_kg


def electricity_cost(elec_price_per_kwh):
    """
    Auxiliary electricity cost per kg of CH4 produced.

    Sabatier is strongly exothermic — no external heating required.
    SABATIER_ELEC_KWH_PER_KG_CH4 covers only compressors, pumps, and controls.
    Cost is strictly linear in electricity price.

        elec cost per kg  =  elec_price_per_kwh × SABATIER_ELEC_KWH_PER_KG_CH4
    """
    return elec_price_per_kwh * SABATIER_ELEC_KWH_PER_KG_CH4


def total_ch4_cost(h2_price, total_capex, elec_price):
    """Total CH4 production cost — sum of all four contributors ($/kg CH4)."""
    return (h2_feedstock_cost(h2_price)
          + co2_feedstock_cost()
          + capex_cost(total_capex)
          + electricity_cost(elec_price))


# ============================================================
# CHART 1  —  CH4 Cost vs Electricity Price
# Fixed: H2 = $1/kg, Capex = $100 000
# ============================================================

ELEC_RANGE = np.linspace(0.0, 0.05, 600)   # $/kWh x-axis sweep  (0 – 5 cents)


def make_chart1():
    # --- Compute cost components ($/kg CH4), then convert to $/MMBtu ---
    h2_arr    = np.full_like(ELEC_RANGE, h2_feedstock_cost(H2_PRICE_FIXED))
    co2_arr   = np.full_like(ELEC_RANGE, co2_feedstock_cost())
    cap_arr   = np.full_like(ELEC_RANGE, capex_cost(CAPEX_FIXED))
    elec_arr  = electricity_cost(ELEC_RANGE)
    total_arr = h2_arr + co2_arr + cap_arr + elec_arr

    # Convert all cost arrays from $/kg CH4 to $/MMBtu
    # $/MMBtu = $/kg × KG_CH4_PER_MMBTU  (more kg needed per MMBtu → higher $ per MMBtu)
    h2_arr    *= KG_CH4_PER_MMBTU
    co2_arr   *= KG_CH4_PER_MMBTU
    cap_arr   *= KG_CH4_PER_MMBTU
    elec_arr  *= KG_CH4_PER_MMBTU
    total_arr *= KG_CH4_PER_MMBTU

    fig, ax = plt.subplots(figsize=(9, 6))

    # --- Stacked area: H2 (bottom) → CO2 → capex → electricity (top) ---
    ax.stackplot(
        ELEC_RANGE,
        h2_arr, co2_arr, cap_arr, elec_arr,
        labels=[
            f'H₂ feedstock  (${H2_PRICE_FIXED}/kg)',
            f'CO₂ feedstock  (${CO2_PRICE_PER_TONNE:.0f}/t)',
            f'Capex  (${CAPEX_FIXED/1e3:.0f}k, {AMORT_YEARS} yr)',
            f'Auxiliary electricity  ({SABATIER_ELEC_KWH_PER_KG_CH4} kWh/kg CH₄)',
        ],
        colors=['#2980b9', '#27ae60', '#e67e22', '#c0392b'],
        alpha=0.75,
    )

    # --- Total cost line ---
    ax.plot(ELEC_RANGE, total_arr,
            color='black', linewidth=2.2, label='Total CH₄ cost', zorder=5)

    # --- Reference marker at $0.01/kWh ---
    ref_elec = 0.01
    ref_cost = total_ch4_cost(H2_PRICE_FIXED, CAPEX_FIXED, ref_elec) * KG_CH4_PER_MMBTU
    ax.axvline(ref_elec, color='dimgray', linestyle=':', linewidth=1.2, alpha=0.7)
    ax.text(ref_elec + 0.003, total_arr.max() * 1.25,
            f'${ref_elec}/kWh\n-> ${ref_cost:.1f}/MMBtu',
            fontsize=8, color='dimgray', ha='left', va='top')

    # --- Axes ---
    ax.set_xlabel('Electricity Price  ($/kWh)', fontsize=12)
    ax.set_ylabel('CH₄ Production Cost  ($/MMBtu,  HHV)', fontsize=12)
    ax.set_title(
        'Synthetic CH₄ Cost vs Electricity Price\n'
        'Sabatier Methanation  ·  Green H₂  ·  DAC-derived CO₂',
        fontsize=13,
    )
    ax.set_xlim(ELEC_RANGE[0], ELEC_RANGE[-1])
    ax.set_ylim(0, total_arr.max() * 1.45)   # headroom for assumptions box
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.legend(fontsize=9, loc='upper left')

    # --- Assumptions text box (upper-right, above data band) ---
    h2_actual  = H2_STOICH_KG_PER_KG_CH4  / SABATIER_EFFICIENCY
    co2_actual = CO2_STOICH_KG_PER_KG_CH4 / SABATIER_EFFICIENCY
    assumptions = (
        'Assumptions\n'
        f'  CO₂ price:            ${CO2_PRICE_PER_TONNE:.0f}/t  (DAC)\n'
        f'  H₂ price:              ${H2_PRICE_FIXED}/kg  (fixed)\n'
        f'  Sabatier efficiency:  {SABATIER_EFFICIENCY*100:.0f}%\n'
        f'  Capex:                 ${CAPEX_FIXED/1e3:.0f}k total\n'
        f'  Amortisation:         {AMORT_YEARS} yr\n'
        f'  Plant power:          {PLANT_POWER_MW} MW CH₄ out (HHV)\n'
        f'  Plant capacity:       {PLANT_ANNUAL_CAPACITY_KG/1e3:.0f} t CH₄/yr  (CF={CAPACITY_FACTOR:.0%})\n'
        f'  H₂ feed (actual):     {h2_actual:.3f} kg H₂/kg CH₄\n'
        f'  CO₂ feed (actual):    {co2_actual:.3f} kg CO₂/kg CH₄\n'
        f'  Aux electricity:      {SABATIER_ELEC_KWH_PER_KG_CH4} kWh/kg CH₄\n'
        f'  CH₄ HHV:              {CH4_HHV_MJ_PER_KG} MJ/kg  ({KG_CH4_PER_MMBTU:.2f} kg/MMBtu)'
    )
    ax.text(
        0.975, 0.975, assumptions,
        transform=ax.transAxes,
        fontsize=8, family='monospace',
        verticalalignment='top', horizontalalignment='right',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                  edgecolor='lightgray', alpha=0.92),
    )

    # --- Watermark: 50 % x, near top of figure, 50 % alpha ---
    fig.text(0.50, 0.965, 'Christopher Kalitin 2026',
             fontsize=10, color='gray', alpha=0.50,
             ha='center', va='top')

    plt.tight_layout(rect=[0, 0, 1, 0.94])

    out = os.path.join(RESULTS_DIR, 'ch4_cost_vs_elec_price.png')
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.show()
    print(f'Saved: {out}')


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == '__main__':
    make_chart1()
