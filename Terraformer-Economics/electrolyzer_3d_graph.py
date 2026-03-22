import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

# --- Assumptions ---
electricity_price = 0.01   # $/kWh
capacity_factor   = 0.25   # 90%
lifetime_years    = 10
hours_per_year    = 8760

# H2 cost ($/kgH2):
#   electricity:  efficiency * electricity_price
#   capital:      capex * efficiency / (lifetime * hours/yr * CF)
#                 (amortizes $/kW over lifetime kgH2 produced per kW)

eff  = np.linspace(40, 80, 200)     # kWh/kgH2
cost = np.linspace(40, 900, 200)   # $/kW
EFF, COST = np.meshgrid(eff, cost)

def h2_cost(e, c):
    return e * electricity_price + c * e / (lifetime_years * hours_per_year * capacity_factor)

H2_COST = h2_cost(EFF, COST)

# Points from electrolyzer_cost_vs_eff (eff 40-80, capex <= 1000)
# (efficiency kWh/kgH2, capex $/kW, label)
stack_points = [
    (48.9, 353, 'US DOE Alkaline (stack)'),
    (46,   200, 'Verdagy AEM Goal (stack)'),
    (80,   100, 'Terraform 100 $/kW (stack)'),
    (80,   50, 'Terraform 50 $/kW (stack)'),
    (60, 100, "60 kWh/kgH₂ @ 100 $/kW (stack)"),
]
plant_points = [
    (53.7, 610, 'US DOE Alkaline (plant)'),
    (50,   775, 'Verdagy Alkaline (plant)'),
    (54.5, 850, 'EH2 PEM (plant)'),
]

fig = plt.figure(figsize=(8, 7))
ax = fig.add_subplot(111, projection='3d')

surf = ax.plot_surface(EFF, COST, H2_COST, cmap='viridis_r', 
                       alpha=0.6,    # Keep this under 0.7
                       rcount=100,   # High rcount/ccount helps the 
                       ccount=100,   # renderer sort points better
                       antialiased=True,
                       zorder=1)
#fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label='H₂ Cost ($/kgH₂)')

# 1. Increase the nudge to 0.15 or 0.2 (approx 5% of the Z-range)
# 2. Add 'clip_on=False' to the scatter call
# 3. Lower surface alpha to 0.6 to let the points "bleed through" if needed

for e, c, label in stack_points:
    z_base = h2_cost(e, c)
    ax.scatter(e, c, z_base + 0, color='orange', edgecolors='black', 
               linewidth=1, marker='o', s=80, zorder=10, clip_on=False)
    ax.text(e, c, z_base - 0.1, f'  {label}\n  Cost: ${z_base:.2f}/kg', fontsize=7, zorder=11)

for e, c, label in plant_points:
    z_base = h2_cost(e, c)
    ax.scatter(e, c, z_base + 0, color='blue', edgecolors='black', 
               linewidth=1, marker='^', s=80, zorder=10, clip_on=False)
    ax.text(e, c, z_base - 0.1, f'  {label}\n  Cost: ${z_base:.2f}/kg', fontsize=7, zorder=11)
    
ax.set_xlabel('Efficiency (kWh/kgH₂)', labelpad=10)
ax.set_ylabel('Capex ($/kW)', labelpad=10)
ax.set_zlabel('H₂ Cost ($/kgH₂)', labelpad=10)
ax.set_title('Electrolyzer H₂ Cost vs Efficiency & Capex\n'
             f'($0.01/kWh electricity, {int(capacity_factor*100)}% CF, {lifetime_years}yr lifetime)')

fig.text(0.5, 0.87, 'Christopher Kalitin 2026', ha='center', fontsize=10, color='black', alpha=1.0)

plt.tight_layout()
plt.savefig('electrolyzer_3d_graph.png', dpi=150)
plt.show()
