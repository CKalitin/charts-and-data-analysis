"""
Terraformer Cost Estimation  —  Synthetic Methanol Production Cost
Direct CO2 hydrogenation  +  green hydrogen  +  DAC-derived CO2

Chart: Methanol cost ($/MT) heatmap over CO2 price and H2 price
       Feedstock costs only — no capex, no auxiliary electricity
       CO2 range: $0.01 – $1/kg    H2 range: $0.05 – $5/kg
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)


# ============================================================
# PHYSICAL CONSTANTS  —  CO2 + 3 H2 → CH3OH + H2O
# ============================================================
MW_CH3OH = 32.0   # g/mol  (12 + 4 + 16)
MW_CO2   = 44.0   # g/mol
MW_H2    =  2.0   # g/mol

# Stoichiometric feedstock per kg methanol produced (from molar ratios)
H2_STOICH_KG_PER_KG_MEOH  = (3 * MW_H2) / MW_CH3OH   # = 0.1875 kg H2  / kg MeOH
CO2_STOICH_KG_PER_KG_MEOH = MW_CO2      / MW_CH3OH   # = 1.3750 kg CO2 / kg MeOH

KG_PER_MT = 1000.0   # 1 metric tonne = 1000 kg


# ============================================================
# PROCESS PARAMETERS
# ============================================================
METHANOL_EFFICIENCY = 0.95
# Fraction of feedstock that converts to methanol.  Unreacted fraction lost.
# This is the methanol synthesis reactor step only (electrolysis not included).
# actual feed = stoichiometric / METHANOL_EFFICIENCY  (+5.3% vs perfect stoich.)


# ============================================================
# COST FUNCTION  (feedstock only, $/MT methanol)
# ============================================================
def meoh_feedstock_cost_per_mt(co2_price_kg, h2_price_kg):
    """
    Methanol production cost from feedstocks only  ($/MT methanol).

    H2 term:   (H2_STOICH / eff) × h2_price      [$/kg MeOH]
    CO2 term:  (CO2_STOICH / eff) × co2_price     [$/kg MeOH]
    Sum multiplied by KG_PER_MT to convert to $/MT.

    No capex, no auxiliary electricity — pure feedstock sensitivity.
    """
    h2_cost_kg  = h2_price_kg  * (H2_STOICH_KG_PER_KG_MEOH  / METHANOL_EFFICIENCY)
    co2_cost_kg = co2_price_kg * (CO2_STOICH_KG_PER_KG_MEOH / METHANOL_EFFICIENCY)
    return (h2_cost_kg + co2_cost_kg) * KG_PER_MT


# ============================================================
# GRIDS
# ============================================================
# Log-spaced grids — start above zero so log scale is valid
co2_grid = np.logspace(-2, 0,          400)   # $0.01 – $1/kg CO2
h2_grid  = np.logspace(np.log10(0.05), np.log10(5), 400)  # $0.05 – $5/kg H2

CO2, H2 = np.meshgrid(co2_grid, h2_grid)

# Terraform reference point
TERRAFORM_CO2 = 0.1   # $/kg CO2
TERRAFORM_H2  = 1.0   # $/kg H2

# Contour levels: methanol market benchmarks ($/MT)
# $300  ≈ conventional (coal-based, China)
# $400  ≈ typical international spot price
# $600  ≈ moderate green methanol premium
# $1000 ≈ high-cost green methanol
# $2000 ≈ extreme cost scenario
exports = [
    ('methanol_cost_vs_inputs.png',     0.0, [200, 400, 600, 1000]),   # no credit
    ('methanol_cost_vs_inputs_45V.png', 3.0, [-500, -400, -200, 0, 200, 400, 600]),      # IRA 45V
]


# ============================================================
# FIGURE
# ============================================================
def build_chart(h2_credit, filename, contour_levels):
    H2_EFF      = H2 - h2_credit
    Z           = meoh_feedstock_cost_per_mt(CO2, H2_EFF)
    contour_fmt = {v: f'${v:g}' for v in contour_levels}

    fig, ax = plt.subplots(figsize=(10, 6))

    # Set scales first — contour label placement is calculated in the current axis
    # transform, so log scale must be active before contour/clabel are called.
    ax.set_xscale('log')
    ax.set_yscale('log')
    # Plain decimal tick labels — no scientific notation
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:g}'))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:g}'))

    pcm  = ax.pcolormesh(CO2, H2, Z, cmap='plasma_r', shading='auto', zorder=0)
    cbar = fig.colorbar(pcm, ax=ax, pad=0.02)
    cbar.set_label('Methanol Cost  ($/MT)', fontsize=9)

    # Contour lines — drawn after log scale is set so label placement uses log coords
    cs = ax.contour(CO2, H2, Z, levels=contour_levels,
                    colors='#222222', linewidths=0.9, alpha=0.5, zorder=2)
    ax.clabel(cs, fmt=contour_fmt, fontsize=8, inline=True, inline_spacing=2)

    # Terraform reference point — cost uses effective H2 price after credit
    terraform_h2_eff = TERRAFORM_H2 - h2_credit
    terraform_cost   = meoh_feedstock_cost_per_mt(TERRAFORM_CO2, terraform_h2_eff)
    ax.scatter(TERRAFORM_CO2, TERRAFORM_H2, color='white', s=55, zorder=6,
               edgecolors='#222222', linewidths=0.8)
    ax.annotate(f'Terraform  ${terraform_cost:.0f}/MT',
                xy=(TERRAFORM_CO2, TERRAFORM_H2), xycoords='data',
                xytext=(8, 4), textcoords='offset points',
                fontsize=8, color='white', ha='left')

    ax.set_xlabel('CO₂ Price  ($/kg)')
    ax.set_ylabel('H₂ Market Price  ($/kg)')
    ax.set_title('Synthetic Methanol Cost vs CO₂ Price & H₂ Price')
    ax.grid(True, which='both', linestyle='--', alpha=0.3, zorder=1)

    # Watermark
    ax.text(0.5, 0.95, 'Christopher Kalitin 2026',
            transform=ax.transAxes, fontsize=12, color='white',
            ha='center', va='top')

    # Notes
    note = (f'Feedstock costs only  ·  Methanol synthesis efficiency {METHANOL_EFFICIENCY*100:.0f}%')
    if h2_credit > 0:
        note += f'\n45V H₂ tax credit applied: ${h2_credit:g}/kg'
    ax.text(0.01, 0.01, note,
            transform=ax.transAxes, fontsize=8, color='#444444',
            ha='left', va='bottom')

    plt.tight_layout()
    out = os.path.join(RESULTS_DIR, filename)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f'Saved: {out}')


for filename, h2_credit, contour_levels in exports:
    build_chart(h2_credit, filename, contour_levels)
plt.show()
