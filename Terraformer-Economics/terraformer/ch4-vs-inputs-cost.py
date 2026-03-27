"""
Terraformer Cost Estimation  —  Synthetic CH4 Production Cost
Sabatier methanation  +  green hydrogen  +  DAC-derived CO2

Chart: CH4 cost ($/MMBtu, HHV) heatmap over CO2 price and H2 price
       Feedstock costs only — no capex, no auxiliary electricity
       CO2 range: $0 – $1/kg    H2 range: $0 – $5/kg
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

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
CH4_HHV_MJ_PER_KG = 55.5                              # Higher Heating Value of CH4 (MJ/kg)
MMBTU_IN_MJ        = 1055.06                           # 1 MMBtu = 1055.06 MJ
KG_CH4_PER_MMBTU   = MMBTU_IN_MJ / CH4_HHV_MJ_PER_KG  # = 19.01 kg CH4 / MMBtu
# Conversion:  $/MMBtu = ($/kg CH4) × KG_CH4_PER_MMBTU


# ============================================================
# PROCESS PARAMETERS
# ============================================================
SABATIER_EFFICIENCY = 0.95
# Fraction of feedstock that converts to CH4.  Unreacted fraction lost.
# actual feed = stoichiometric / SABATIER_EFFICIENCY  (+5.3% vs perfect stoich.)


# ============================================================
# COST FUNCTION  (feedstock only, $/MMBtu HHV)
# ============================================================
def ch4_feedstock_cost_mmbtu(co2_price_kg, h2_price_kg):
    """
    CH4 production cost from feedstocks only  ($/MMBtu, HHV).

    H2 term:   (H2_STOICH / eff) × h2_price      [$/kg CH4]
    CO2 term:  (CO2_STOICH / eff) × co2_price     [$/kg CH4]
    Sum multiplied by KG_CH4_PER_MMBTU to convert to $/MMBtu.

    No capex, no auxiliary electricity — pure feedstock sensitivity.
    """
    h2_cost_kg  = h2_price_kg  * (H2_STOICH_KG_PER_KG_CH4  / SABATIER_EFFICIENCY)
    co2_cost_kg = co2_price_kg * (CO2_STOICH_KG_PER_KG_CH4 / SABATIER_EFFICIENCY)
    return (h2_cost_kg + co2_cost_kg) * KG_CH4_PER_MMBTU


# ============================================================
# GRIDS
# ============================================================
# Log-spaced grids — start above zero so log scale is valid
co2_grid = np.logspace(-2, 0,          400)   # $0.01 – $1/kg CO2
h2_grid  = np.logspace(np.log10(0.05), np.log10(5), 400)  # $0.05 – $5/kg H2

CO2, H2 = np.meshgrid(co2_grid, h2_grid)
Z = ch4_feedstock_cost_mmbtu(CO2, H2)

# Terraform reference point
TERRAFORM_CO2 = 0.1   # $/kg CO2
TERRAFORM_H2  = 1.0   # $/kg H2

# Contour levels: nat gas benchmarks ($/MMBtu)
# $5    ≈ Henry Hub / cheap domestic gas
# $10   ≈ moderate LNG export-parity price
# $20   ≈ elevated European winter gas
# $50   ≈ 2022 EU gas crisis peak
# ($1 line omitted — it falls entirely in the bottom-left corner of the log grid)
CONTOUR_LEVELS = [3, 5, 10, 20, 50]
CONTOUR_FMT    = {v: f'${v:g}' for v in CONTOUR_LEVELS}

# Manual label positions (data coords, one per level in the same order).
# Computed to lie on each contour:  h2 = (Z/KG_CH4_PER_MMBTU - co2*CO2_FACTOR) / H2_FACTOR
# Placing mid-chart so each line has enough room for the label.
CONTOUR_LABEL_POS = [(0.028, 0.35), (0.04, 0.78), (0.06, 1.67), (0.20, 3.90)]


# ============================================================
# FIGURE
# ============================================================
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
cbar.set_label('CH₄ Cost  ($/MMBtu,  HHV)', fontsize=9)

# Contour lines — drawn after log scale is set so label placement uses log coords
cs = ax.contour(CO2, H2, Z, levels=CONTOUR_LEVELS,
                colors='#222222', linewidths=0.9, alpha=0.5, zorder=2)
ax.clabel(cs, fmt=CONTOUR_FMT, fontsize=8, inline=True, inline_spacing=2)
# Terraform reference point
terraform_cost = ch4_feedstock_cost_mmbtu(TERRAFORM_CO2, TERRAFORM_H2)
ax.scatter(TERRAFORM_CO2, TERRAFORM_H2, color='white', s=55, zorder=6,
           edgecolors='#222222', linewidths=0.8)
ax.annotate(f'Terraform  ${terraform_cost:.0f}/MMBtu',
            xy=(TERRAFORM_CO2, TERRAFORM_H2), xycoords='data',
            xytext=(8, 4), textcoords='offset points',
            fontsize=8, color='#222222', ha='left',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#111111',
                      alpha=0.0, edgecolor='none'))

ax.set_xlabel('CO₂ Price  ($/kg)')
ax.set_ylabel('H₂ Price  ($/kg)')
ax.set_title('Synthetic CH₄ Cost vs CO₂ Price & H₂ Price')
ax.grid(True, which='both', linestyle='--', alpha=0.3, zorder=1)

# Watermark — white text over the coloured background
ax.text(0.5, 0.95, 'Christopher Kalitin 2026',
        transform=ax.transAxes, fontsize=12, color='white',
        ha='center', va='top')

# Notes — small, bottom-left, separate from the title
ax.text(0.01, 0.01,
        f'Feedstock costs only, no capex, no auxiliary electricity ·  Sabatier efficiency {SABATIER_EFFICIENCY*100:.0f}% ·  ~$3/MMBtu required for cost parity',
        transform=ax.transAxes, fontsize=8, color='#444444',
        ha='left', va='bottom')

plt.tight_layout()

out = os.path.join(RESULTS_DIR, 'ch4_cost_vs_inputs.png')
fig.savefig(out, dpi=150)
plt.show()
print(f'Saved: {out}')
