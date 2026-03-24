import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

# --- Model ---
HOURS_OPERATING = 8760 * 0.25   # 25% capacity factor

def capex_2030(e):
    return np.maximum(-9 * np.asarray(e, dtype=float) + 760, 0)

def pct_capex(eff, elec_price, amort_years):
    """Capex share of total H2 cost (0–100%) using 2030 capex model."""
    opex          = eff * elec_price
    capex_contrib = capex_2030(eff) * eff / (HOURS_OPERATING * amort_years)
    return capex_contrib / (opex + capex_contrib) * 100

# --- Grid (log-spaced prices for smooth heatmap on log axis) ---
EFF_ARR   = np.linspace(35, 80, 200)
PRICE_ARR = np.logspace(np.log10(0.005), np.log10(0.10), 200)
EFF_GRID, PRICE_GRID = np.meshgrid(EFF_ARR, PRICE_ARR)

# --- Amortization series ---
amort_series = [1, 3, 5, 10, 20]
colors       = ['tomato', 'darkorange', 'goldenrod', 'steelblue', 'seagreen']

# --- Figure ---
fig, ax = plt.subplots(figsize=(10, 7))

# Iso-lines: price = capex_2030(eff) / (HOURS * amort)  (50% capex/opex boundary)
# Below a line → capex dominated for that amortization period
# Above a line → opex dominated for that amortization period
for amort, color in zip(amort_series, colors):
    price_50 = capex_2030(EFF_ARR) / (HOURS_OPERATING * amort)
    mask = (price_50 >= 0.005) & (price_50 <= 0.10)
    if mask.any():
        ax.plot(EFF_ARR[mask], price_50[mask],
                color=color, linewidth=2.0, label=f'{amort} yr')

ax.grid(True, linestyle='--', alpha=0.4)

# Region labels
ax.text(0.02, 0.04, 'Capex dominated', transform=ax.transAxes,
        ha='left', va='bottom', fontsize=9, color='gray')
ax.text(0.98, 0.96, 'Opex dominated', transform=ax.transAxes,
        ha='right', va='top', fontsize=9, color='gray')

# --- Primary axes ---
ax.set_yscale('log')
ax.set_xlim(35, 80)
ax.set_ylim(0.005, 0.10)
ax.set_yticks([0.005, 0.01, 0.02, 0.05, 0.10])
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:.3g}'))
ax.set_xlabel('Efficiency (kWh/kgH\u2082)', fontsize=11)
ax.set_ylabel('Electricity Price ($/kWh)', fontsize=11)

# --- Secondary capex axis (top) ---
ax2 = ax.twiny()
ax2.set_xlim(ax.get_xlim())
eff_ticks = np.linspace(35, 80, 6)
ax2.set_xticks(eff_ticks)
ax2.set_xticklabels([f'${capex_2030(e):.0f}' for e in eff_ticks])
ax2.set_xlabel('Capex ($/kW)', fontsize=11)

# --- Title, legend, footer ---
ax.set_title(
    'H\u2082 Cost: Capex/Opex Boundary vs Efficiency & Electricity Price\n'
    '2030 Capex Model  |  25% CF  |  Each line = electricity price where capex share = 50%',
    fontsize=11, pad=12
)

ax.legend(title='Amortization\nPeriod', loc='lower right', fontsize=9, title_fontsize=8)

fig.text(0.5, 0.01, 'Christopher Kalitin 2026',
         ha='center', fontsize=10, color='gray')

fig.tight_layout(rect=[0, 0.03, 1, 1])
fig.savefig(os.path.join(RESULTS_DIR, 'electrolyzer_contribution_heatmap.png'), dpi=150)
plt.close(fig)
print('Saved electrolyzer_contribution_heatmap.png')

# ============================================================
# 3D wireframe chart with 50% iso-lines
# ============================================================

# Linear-spaced grid for the 3D surface (log spacing not needed in 3D)
EFF_ARR_3D   = np.linspace(35, 80, 80)
PRICE_ARR_3D = np.linspace(0.005, 0.10, 80)
EFF_3D, PRICE_3D = np.meshgrid(EFF_ARR_3D, PRICE_ARR_3D)

fig3d = plt.figure(figsize=(14, 9))
ax3d  = fig3d.add_subplot(111, projection='3d')

for amort, color in zip(amort_series, colors):
    Z = pct_capex(EFF_3D, PRICE_3D, amort)
    ax3d.plot_wireframe(EFF_3D, PRICE_3D, Z,
                        color=color, linewidth=0.5, alpha=0.5,
                        rstride=4, cstride=4)

ax3d.set_xlabel('Efficiency (kWh/kgH\u2082)', labelpad=12)
ax3d.set_ylabel('Electricity Price ($/kWh)', labelpad=12)
ax3d.set_zlabel('Capex Share (%)', labelpad=10)
ax3d.zaxis.set_rotate_label(False)
ax3d.set_zlim(0, 100)

ax3d.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:.3g}'))

ax3d.set_title(
    'H\u2082 Cost: Capex Share vs Efficiency & Electricity Price\n'
    '2030 Capex Model  |  25% CF  |  Bold lines = 50% boundary per amortization period',
    fontsize=14
)

ax3d.view_init(elev=25, azim=-55)

legend_elements_3d = [
    Patch(facecolor=c, alpha=0.75, label=f'{a} yr amortization')
    for a, c in zip(amort_series, colors)
]
ax3d.legend(handles=legend_elements_3d, title='Amortization Period',
            loc='upper right', fontsize=9, title_fontsize=9)

fig3d.text(0.5, 0.01, 'Christopher Kalitin 2026',
           ha='center', fontsize=10, color='gray')

fig3d.tight_layout()
fig3d.savefig(os.path.join(RESULTS_DIR, 'electrolyzer_contribution_3d.png'), dpi=150)
plt.close(fig3d)
print('Saved electrolyzer_contribution_3d.png')
