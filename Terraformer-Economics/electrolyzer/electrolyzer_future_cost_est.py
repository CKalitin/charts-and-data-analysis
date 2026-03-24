import matplotlib.pyplot as plt
import numpy as np
import os
from electrolyzer_data import handmer_x, handmer_y

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

HOURS_OPERATING_PER_YEAR = 0.25 * 8760  # 2190 hrs/year at 25% capacity factor
OPEX_PER_KWH   = 0.01          # $/kWh

def cost_per_kg(efficiency, capex_per_kw, amortization_years):
    # Dimensional Analysis:
    # It's a downward opening parabola in the 2030 case (quadratic in efficiency) because:
    # opex + capex is linear wrt efficiency
    # My 2030 fit is capex = -9 * efficiency + 760, so capex is linear in efficiency
    # Therefore capex * efficiency is quadratic in efficiency
    
    opex = efficiency * OPEX_PER_KWH # kWh/kgH2 * $/kWh = $/kgH2
    capex = capex_per_kw * (1 / (HOURS_OPERATING_PER_YEAR * amortization_years)) * efficiency # $/kW * 1/(hours per year * years) * kWh/kgH2 = $/kgH2
    return opex + capex

def capex_2026(efficiency):
    return np.interp(efficiency, handmer_x, handmer_y)

def capex_2030(efficiency):
    return -9 * np.asarray(efficiency, dtype=float) + 760

eff_2026 = np.linspace(min(handmer_x), max(handmer_x), 500)
eff_2030 = np.linspace(40, 80, 500)

models = [
    ('2026 Model - Electrolyzer Stack Only (Not Plant)', capex_2026, eff_2026, True),
    ('2030 Model - Electrolyzer Stack Only (Not Plant)', capex_2030, eff_2030, False),
]

def plot_model(ax, title, capex_fn, eff, ylim_zero=False):
    for amort, color in [(5, 'blue'), (10, 'orange')]:
        cost = cost_per_kg(eff, capex_fn(eff), amort)
        ax.plot(eff, cost, color=color, linewidth=2, label=f'{amort}-Year Amortization')

    if ylim_zero:
        ax.set_ylim(bottom=0)
    ax.set_xlim(right=80)
    ax.set_xlabel('Efficiency (kWh/kgH\u2082)')
    ax.set_ylabel('Cost ($/kgH\u2082)')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.text(0.99, 0.01,
            f'Electricity: ${OPEX_PER_KWH}/kWh  |  Capacity factor: {int(HOURS_OPERATING_PER_YEAR/8760*100)}%',
            transform=ax.transAxes, fontsize=7, color='gray', ha='right', va='bottom')

    # Secondary x-axis: capex $/kW
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    tick_effs = np.linspace(eff.min(), eff.max(), 6)
    ax2.set_xticks(tick_effs)
    ax2.set_xticklabels([f'${capex_fn(e):.0f}' for e in tick_effs])
    ax2.set_xlabel('Capex ($/kW)')

# --- Combined figure (1x2) ---
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('Electrolyzer H\u2082 Cost vs Efficiency / Capex\nChristopher Kalitin 2026', fontsize=13)

for ax, (title, capex_fn, eff, ylim_zero) in zip(axes, models):
    plot_model(ax, title, capex_fn, eff, ylim_zero)

plt.tight_layout()
plt.savefig(os.path.join(RESULTS_DIR, 'electrolyzer_future_cost_est.png'), dpi=150)

# --- Individual figures ---
for title, capex_fn, eff, ylim_zero in models:
    fig, ax = plt.subplots(figsize=(7, 5))
    plot_model(ax, title, capex_fn, eff, ylim_zero)
    fig.suptitle('Electrolyzer H\u2082 Cost vs Efficiency / Capex\nChristopher Kalitin 2026', fontsize=11)
    plt.tight_layout()
    filename = os.path.join(RESULTS_DIR, 'electrolyzer_future_cost_est_' + title.lower().replace(' ', '_') + '.png')
    plt.savefig(filename, dpi=150)

#plt.show()
