import matplotlib.pyplot as plt
import numpy as np
import os

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

# --- 2030 model (capex = -9·eff + 760, same as future_cost_est) ---
HOURS_OPERATING = 8760 * 0.25   # 25% capacity factor

eff = np.linspace(40, 80, 500)

def capex_2030(e):
    return np.maximum(-9 * np.asarray(e, dtype=float) + 760, 0)

capex_kw = capex_2030(eff)

def pct_capex(electricity_price, amort_years):
    """Fraction of total H2 cost that comes from amortised capex (0–100)."""
    opex         = eff * electricity_price
    capex_contrib = capex_kw * eff / (HOURS_OPERATING * amort_years)
    return capex_contrib / (opex + capex_contrib) * 100

# --- Shared axis styling ---
def _secondary_capex_axis(ax):
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    ticks = np.linspace(eff.min(), eff.max(), 6)
    ax2.set_xticks(ticks)
    ax2.set_xticklabels([f'${capex_2030(e):.0f}' for e in ticks])
    ax2.set_xlabel('Capex ($/kW)')

def _style_ax(ax, title, footnote):
    ax.set_xlim(eff.min(), eff.max())
    ax.set_ylim(0, 100)

    # Shaded regions
    ax.axhspan(50, 100, alpha=0.07, color='tomato',    zorder=0)
    ax.axhspan(0,  50,  alpha=0.07, color='steelblue', zorder=0)
    ax.axhline(50, color='gray', linestyle=':', linewidth=1.2, zorder=1)

    # Region labels (axes coords so they never overlap the data)
    ax.text(0.01, 0.97, 'Capex dominated',  transform=ax.transAxes,
            ha='left', va='top',    fontsize=8, color='tomato',    alpha=0.8)
    ax.text(0.01, 0.03, 'Opex dominated',   transform=ax.transAxes,
            ha='left', va='bottom', fontsize=8, color='steelblue', alpha=0.8)

    ax.set_xlabel('Efficiency (kWh/kgH\u2082)')
    ax.set_ylabel('Capex share of total H\u2082 cost (%)')
    ax.set_title(title, fontsize=10)
    ax.legend(fontsize=8, loc='center right')
    ax.grid(True, linestyle='--', alpha=0.4, zorder=0)
    ax.text(0.99, 0.01, footnote, transform=ax.transAxes,
            fontsize=7, color='gray', ha='right', va='bottom')
    _secondary_capex_axis(ax)

# -----------------------------------------------------------------------
# Graph 1 — Vary amortisation period (fixed electricity = $0.01/kWh)
# -----------------------------------------------------------------------
# As capex falls (right side of curve), the gap between amortisation lines
# narrows → the period matters less and less (Dennard-scaling analogy).
AMORT_SERIES = [
    (3,  '#c0392b', '3-year'),
    (5,  '#e67e22', '5-year'),
    (10, '#2980b9', '10-year'),
    (20, '#27ae60', '20-year'),
]
E_PRICE_FIXED = 0.01

# Graph 2 — Vary electricity price (fixed amortisation = 10 years)
# -----------------------------------------------------------------------
# Cheaper solar shifts the balance toward capex → capex share rises, making
# further capex reductions more valuable.
ELEC_SERIES = [
    (0.005, '#27ae60', '$0.005/kWh'),
    (0.010, '#2980b9', '$0.010/kWh'),
    (0.020, '#e67e22', '$0.020/kWh'),
    (0.050, '#c0392b', '$0.050/kWh'),
]
AMORT_FIXED = 10

# --- Combined figure (1 x 2) ---
fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle(
    '2030 Electrolyzer: Capex Share of H\u2082 Cost Along Efficiency / Capex Curve\n'
    'Christopher Kalitin 2026',
    fontsize=12)

for amort, color, lbl in AMORT_SERIES:
    ax_l.plot(eff, pct_capex(E_PRICE_FIXED, amort), linewidth=2, color=color, label=lbl, zorder=3)
_style_ax(ax_l,
          f'Varying Amortisation Period\n(electricity ${E_PRICE_FIXED}/kWh, {int(HOURS_OPERATING/8760*100)}% CF)',
          f'Electricity: ${E_PRICE_FIXED}/kWh  |  CF: {int(HOURS_OPERATING/8760*100)}%')

for e_price, color, lbl in ELEC_SERIES:
    ax_r.plot(eff, pct_capex(e_price, AMORT_FIXED), linewidth=2, color=color, label=lbl, zorder=3)
_style_ax(ax_r,
          f'Varying Electricity Price\n({AMORT_FIXED}-year amortisation, {int(HOURS_OPERATING/8760*100)}% CF)',
          f'Amortisation: {AMORT_FIXED} years  |  CF: {int(HOURS_OPERATING/8760*100)}%')

plt.tight_layout()
fig.savefig(os.path.join(RESULTS_DIR, 'electrolyzer_cost_contribution.png'), dpi=150)
plt.close(fig)

# --- Individual figures ---
fig, ax = plt.subplots(figsize=(8, 5))
for amort, color, lbl in AMORT_SERIES:
    ax.plot(eff, pct_capex(E_PRICE_FIXED, amort), linewidth=2, color=color, label=lbl, zorder=3)
_style_ax(ax,
          f'2030 Electrolyzer: Capex Share — Varying Amortisation\n(electricity ${E_PRICE_FIXED}/kWh, {int(HOURS_OPERATING/8760*100)}% CF)',
          f'Electricity: ${E_PRICE_FIXED}/kWh  |  CF: {int(HOURS_OPERATING/8760*100)}%')
fig.suptitle('Christopher Kalitin 2026', fontsize=9, color='gray')
plt.tight_layout()
fig.savefig(os.path.join(RESULTS_DIR, 'electrolyzer_cost_contribution_amort.png'), dpi=150)
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 5))
for e_price, color, lbl in ELEC_SERIES:
    ax.plot(eff, pct_capex(e_price, AMORT_FIXED), linewidth=2, color=color, label=lbl, zorder=3)
_style_ax(ax,
          f'2030 Electrolyzer: Capex Share — Varying Electricity Price\n({AMORT_FIXED}-year amortisation, {int(HOURS_OPERATING/8760*100)}% CF)',
          f'Amortisation: {AMORT_FIXED} years  |  CF: {int(HOURS_OPERATING/8760*100)}%')
fig.suptitle('Christopher Kalitin 2026', fontsize=9, color='gray')
plt.tight_layout()
fig.savefig(os.path.join(RESULTS_DIR, 'electrolyzer_cost_contribution_elec.png'), dpi=150)
plt.close(fig)