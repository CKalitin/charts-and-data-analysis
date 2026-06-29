import matplotlib.pyplot as plt
import numpy as np
import os

output_dir = os.path.join(os.path.dirname(__file__), 'outputs')
os.makedirs(output_dir, exist_ok=True)

AUTHOR = 'Christopher Kalitin 2026'

# ─── Data: same categories + colours as solar/solar_opex.py ──────────────────
OPEX = [
    ('Cleaning',         15.20, '#3498db'),
    ('Inspection',        8.65, '#1abc9c'),
    ('New BOS',           7.67, '#8e44ad'),
    ('New Modules',       1.81, '#f1c40f'),
    ('New Inverters',    13.95, '#e74c3c'),
    ('Land Lease',       12.83, '#27ae60'),
    ('Property Tax',     11.72, '#95a5a6'),
    ('Insurance',        17.71, '#e67e22'),
    ('Asset Management', 10.46, '#2c3e50'),
]

labels = [row[0] for row in OPEX]
values = [row[1] for row in OPEX]
colors = [row[2] for row in OPEX]

# ─── Figure ───────────────────────────────────────────────────────────────────
# ─── OPEX totals (from solar/solar_lcoe.py) ──────────────────────────────────
OPEX_UTILITY_PER_KW  = 18.25   # $/kW/yr — standard utility rate
SOLAR_RESOURCE       = 2000    # kWh/kW/yr specific yield
opex_per_kwh         = OPEX_UTILITY_PER_KW / SOLAR_RESOURCE   # $/kWh

fig, ax = plt.subplots(figsize=(7.5, 7.0), dpi=150)

wedges, _ = ax.pie(
    values,
    colors=colors,
    startangle=90,
    counterclock=False,
    wedgeprops=dict(width=0.52, edgecolor='white', linewidth=1.5),  # donut
)

# ─── Centre text ──────────────────────────────────────────────────────────────
ax.text(0,  0.12, 'Annual opex', ha='center', va='center',
        fontsize=10, color='#222222', fontweight='bold')
ax.text(0, 0, f'${OPEX_UTILITY_PER_KW:.2f} / kW / yr', ha='center', va='center',
        fontsize=10, color='#222222')
ax.text(0, -0.1, f'${opex_per_kwh:.4f} / kWh', ha='center', va='center',
        fontsize=10, color='#222222')

# ─── Slice labels (no legend) ─────────────────────────────────────────────────
# For tiny slices (<4%) use a leader line and push further out so they
# don't get sandwiched between their neighbours.
for wedge, label, val in zip(wedges, labels, values):
    angle   = (wedge.theta1 + wedge.theta2) / 2
    cos_a   = np.cos(np.radians(angle))
    sin_a   = np.sin(np.radians(angle))
    is_tiny = val < 4.0
    r_label = 1.48 if is_tiny else 1.22
    ha      = 'left' if cos_a >= 0 else 'right'
    txt     = f'{label}\n{val:.1f}%'
    kw      = dict(ha=ha, va='center', fontsize=8.5, color='#333333')

    if is_tiny:
        ax.annotate(
            txt,
            xy=(1.02 * cos_a, 1.02 * sin_a),
            xytext=(r_label * cos_a, r_label * sin_a),
            arrowprops=dict(arrowstyle='-', color='#aaaaaa', lw=0.8),
            **kw,
        )
    else:
        ax.text(r_label * cos_a, r_label * sin_a, txt, **kw)

# Tight limits: labels reach at most ~±1.35 vertically and ~±1.55 horizontally
ax.set_xlim(-1.5, 1.5)
ax.set_ylim(-1.3, 1.3)

# ─── Title & footnotes ────────────────────────────────────────────────────────
ax.set_title('Solar Array OPEX Breakdown', fontsize=12, fontweight='bold', pad=6)
fig.text(0.99, 0.01, AUTHOR, ha='right', va='bottom', fontsize=8, color='#888888')
fig.text(0.01, 0.01,
         'Source: NREL ATB 2023; Lazard LCOE v17.0; Wood Mackenzie Solar O&M 2023',
         ha='left', va='bottom', fontsize=7.5, color='#666666', style='italic')

plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.savefig(os.path.join(output_dir, 'solar_opex_donut.png'),
            dpi=150, bbox_inches='tight')
plt.close(fig)
print('Saved: solar_opex_donut.png')
